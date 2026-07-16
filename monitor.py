import os
import sys
import json
import requests

# Configuration
CONGRESS_NUMBER = "119"
NOMINATION_NUMBER = "1048"
STATUS_FILE = "status.json"

# API URL
API_URL = f"https://api.congress.gov/v3/nomination/{CONGRESS_NUMBER}/{NOMINATION_NUMBER}"

# Fetch API Key from env, fallback to DEMO_KEY
API_KEY = os.environ.get("CONGRESS_API_KEY", "DEMO_KEY")
# Fetch ntfy topic from env
NTFY_TOPIC = os.environ.get("NTFY_TOPIC")

def get_current_status():
    try:
        response = requests.get(API_URL, params={"api_key": API_KEY, "format": "json"}, timeout=15)
        response.raise_for_status()
        data = response.json()
        nomination = data.get("nomination", {})
        latest_action = nomination.get("latestAction", {})
        return {
            "date": latest_action.get("actionDate", "Unknown Date"),
            "text": latest_action.get("text", "No action text available.")
        }
    except Exception as e:
        print(f"Error fetching status from Congress.gov API: {e}", file=sys.stderr)
        sys.exit(1)

def load_last_status():
    if os.path.exists(STATUS_FILE):
        try:
            with open(STATUS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not read status file, resetting. Error: {e}", file=sys.stderr)
    return {"date": "", "text": ""}

def save_status(status):
    try:
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(status, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error writing status file: {e}", file=sys.stderr)

def send_notification(new_status):
    if not NTFY_TOPIC:
        print("NTFY_TOPIC environment variable not set. Skipping notification.")
        print(f"Notification would have been: {new_status['text']}")
        return

    url = f"https://ntfy.sh/{NTFY_TOPIC}"
    title = f"Lt Gen Promotion Update: Brig Gen Voorheis"
    message = f"Status updated on {new_status['date']}:\n{new_status['text']}"
    
    headers = {
        "Title": title,
        "Priority": "high",
        "Tags": "loudspeaker,star"
    }
    
    try:
        response = requests.post(url, data=message.encode("utf-8"), headers=headers, timeout=15)
        response.raise_for_status()
        print("Notification successfully sent via ntfy.sh!")
    except Exception as e:
        print(f"Error sending notification to ntfy: {e}", file=sys.stderr)

def main():
    print("Checking promotion confirmation status...")
    current = get_current_status()
    last = load_last_status()

    print(f"Current Status ({current['date']}): {current['text']}")
    print(f"Previous Status ({last['date']}): {last['text']}")

    if current["date"] != last["date"] or current["text"] != last["text"]:
        print("Status change detected! Sending notification and updating saved state...")
        send_notification(current)
        save_status(current)
        # Write outputs for GitHub actions if needed
        if "GITHUB_OUTPUT" in os.environ:
            with open(os.environ["GITHUB_OUTPUT"], "a") as f:
                f.write("changed=true\n")
    else:
        print("No change detected.")
        if "GITHUB_OUTPUT" in os.environ:
            with open(os.environ["GITHUB_OUTPUT"], "a") as f:
                f.write("changed=false\n")

if __name__ == "__main__":
    main()
