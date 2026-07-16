import os
import sys
import json
import datetime
import time
import requests

CONFIG_FILE = "config.json"
LOG_FILE = "history_log.txt"

# Fetch API Key from env
API_KEY = os.environ.get("CONGRESS_API_KEY")
# Fetch ntfy topic from env
NTFY_TOPIC = os.environ.get("NTFY_TOPIC")

def append_to_log(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}\n"
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(log_entry)
    except Exception as e:
        print(f"Error writing to history log: {e}", file=sys.stderr)

def load_config():
    if not os.path.exists(CONFIG_FILE):
        error_msg = f"Error: Configuration file '{CONFIG_FILE}' not found."
        print(error_msg, file=sys.stderr)
        append_to_log(error_msg)
        sys.exit(1)
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        error_msg = f"Error reading configuration file '{CONFIG_FILE}': {e}"
        print(error_msg, file=sys.stderr)
        append_to_log(error_msg)
        sys.exit(1)

def get_nomination_actions(congress, nomination):
    url = f"https://api.congress.gov/v3/nomination/{congress}/{nomination}/actions"
    try:
        response = requests.get(url, params={"api_key": API_KEY, "format": "json"}, timeout=15)
        response.raise_for_status()
        data = response.json()
        return data.get("actions", [])
    except Exception as e:
        error_msg = f"Error fetching actions from API for PN{nomination} ({congress}th Congress): {e}"
        print(error_msg, file=sys.stderr)
        append_to_log(error_msg)
        return None

def load_state(state_file):
    if os.path.exists(state_file):
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not read state file '{state_file}', resetting. Error: {e}", file=sys.stderr)
    return {"notified_actions": []}

def save_state(state_file, state):
    try:
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error writing state file '{state_file}': {e}", file=sys.stderr)

def send_notification(label, nomination, action):
    if not NTFY_TOPIC:
        msg = f"NTFY_TOPIC not set. Skipped alert for PN{nomination}: {action['text']}"
        print(msg)
        append_to_log(msg)
        return

    url = f"https://ntfy.sh/{NTFY_TOPIC}"
    title = f"Nomination Update: {label}"
    message = f"Status updated on {action['actionDate']}:\n{action['text']}"
    
    headers = {
        "Title": title,
        "Priority": "high",
        "Tags": "loudspeaker,star"
    }
    
    try:
        response = requests.post(url, data=message.encode("utf-8"), headers=headers, timeout=15)
        response.raise_for_status()
        print(f"Alert sent: {action['text']}")
        append_to_log(f"Alert successfully sent for PN{nomination} to topic: {NTFY_TOPIC}")
    except Exception as e:
        err_msg = f"Error sending alert to ntfy: {e}"
        print(err_msg, file=sys.stderr)
        append_to_log(err_msg)

def process_nomination(nom):
    congress = nom.get("congress")
    nomination = nom.get("nomination")
    label = nom.get("label", f"PN{nomination}")
    
    if not congress or not nomination:
        print("Warning: Skipping invalid config entry (missing congress/nomination).", file=sys.stderr)
        return False

    state_file = f"status_{congress}_{nomination}.json"
    actions = get_nomination_actions(congress, nomination)
    if actions is None:
        return False # Error occurred during fetch

    state = load_state(state_file)
    notified_list = state.get("notified_actions", [])
    
    # We identify new actions by comparing actionDate and text
    # Convert notified list to helper set of tuples for quick lookups
    notified_set = {(a.get("actionDate"), a.get("text")) for a in notified_list}
    
    new_actions = []
    for action in actions:
        key = (action.get("actionDate"), action.get("text"))
        if key not in notified_set:
            new_actions.append(action)
            
    if not new_actions:
        print(f"No new actions for {label} (PN{nomination}).")
        append_to_log(f"Checked {label} (PN{nomination}). No new actions.")
        return False

    # Sort new actions chronologically (oldest first) so they arrive in order on the phone
    new_actions.reverse()
    
    is_first_run = len(notified_list) == 0
    if is_first_run:
        print(f"First run for {label}. Sending all {len(new_actions)} historical actions...")
        append_to_log(f"First run for {label}. Initializing timeline with {len(new_actions)} actions.")
    else:
        print(f"Found {len(new_actions)} new actions for {label}.")
        append_to_log(f"New activity detected for {label} (PN{nomination}): {len(new_actions)} new actions.")

    # Send notifications and build updated state
    for action in new_actions:
        send_notification(label, nomination, action)
        notified_list.append({
            "actionDate": action.get("actionDate"),
            "text": action.get("text")
        })
        # Add a tiny delay if sending multiple to prevent rate limits or out-of-order delivery
        if len(new_actions) > 1:
            time.sleep(1)

    state["notified_actions"] = notified_list
    save_state(state_file, state)
    return True

def main():
    if not API_KEY:
        error_msg = "Error: CONGRESS_API_KEY environment variable is missing. It is required for reliable GitHub Actions execution."
        print(error_msg, file=sys.stderr)
        append_to_log(error_msg)
        sys.exit(1)

    print("Checking Senate nomination statuses...")
    config = load_config()
    nominations = config.get("nominations", [])
    
    any_changed = False
    for nom in nominations:
        changed = process_nomination(nom)
        if changed:
            any_changed = True

    # Output variable for GitHub Actions workflow
    if "GITHUB_OUTPUT" in os.environ:
        with open(os.environ["GITHUB_OUTPUT"], "a") as f:
            f.write(f"changed={'true' if any_changed else 'false'}\n")

if __name__ == "__main__":
    main()
