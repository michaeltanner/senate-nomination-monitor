import os
import sys
import json
import argparse
import requests

CONFIG_FILE = "config.json"

def load_config():
    if not os.path.exists(CONFIG_FILE):
        print(f"Error: Configuration file '{CONFIG_FILE}' not found.", file=sys.stderr)
        sys.exit(1)
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error reading configuration file '{CONFIG_FILE}': {e}", file=sys.stderr)
        sys.exit(1)

def check_nomination(congress, nomination, label, api_key):
    url = f"https://api.congress.gov/v3/nomination/{congress}/{nomination}/actions"
    print(f"\n--- Checking: {label} (PN{nomination}, {congress}th Congress) ---")
    try:
        response = requests.get(url, params={"api_key": api_key, "format": "json"}, timeout=15)
        if response.status_code == 403:
            print("Error: API request forbidden (403). Your API key might be invalid, or rate limits were exceeded.", file=sys.stderr)
            return False
        response.raise_for_status()
        data = response.json()
        actions = data.get("actions", [])
        
        if not actions:
            print("No actions found for this nomination.")
            return True
            
        print(f"Success! Found {len(actions)} actions (shown oldest to newest):")
        # Reverse list to show chronologically
        for i, action in enumerate(reversed(actions)):
            print(f"  [{i+1}] {action.get('actionDate')}: {action.get('text')}")
        return True
    except Exception as e:
        print(f"Error querying Congress.gov API: {e}", file=sys.stderr)
        return False

def test_notification(topic):
    url = f"https://ntfy.sh/{topic}"
    print(f"\n--- Sending Test Notification to topic: {topic} ---")
    headers = {
        "Title": "Nomination Monitor Test",
        "Priority": "default",
        "Tags": "test_tube,checkered_flag"
    }
    message = "Your local validation script verified that ntfy.sh is working correctly!"
    try:
        response = requests.post(url, data=message.encode("utf-8"), headers=headers, timeout=15)
        response.raise_for_status()
        print("Success! Test notification sent to ntfy.sh. Check your phone.")
        return True
    except Exception as e:
        print(f"Error sending test notification: {e}", file=sys.stderr)
        return False

def main():
    parser = argparse.ArgumentParser(description="Validate Senate Nomination Monitor API and notification setup.")
    parser.add_argument("--test-notify", action="store_true", help="Send a test notification using NTFY_TOPIC.")
    args = parser.parse_args()

    # Load configuration
    config = load_config()
    nominations = config.get("nominations", [])
    if not nominations:
        print("Error: No nominations configured in config.json.", file=sys.stderr)
        sys.exit(1)

    # Resolve API Key
    api_key = os.environ.get("CONGRESS_API_KEY")
    if not api_key:
        print("WARNING: CONGRESS_API_KEY environment variable is not set.", file=sys.stderr)
        print("If you run this locally, you can set it with: $env:CONGRESS_API_KEY='your_key' (PowerShell)", file=sys.stderr)
        print("or run with a temporary key. Trying 'DEMO_KEY' fallback...", file=sys.stderr)
        api_key = "DEMO_KEY"
    else:
        print("Loaded CONGRESS_API_KEY from environment.")

    # Validate each nomination
    all_success = True
    for nom in nominations:
        congress = nom.get("congress")
        nomination = nom.get("nomination")
        label = nom.get("label", f"PN{nomination}")
        if not congress or not nomination:
            print("Error: Missing congress or nomination number in config entry.", file=sys.stderr)
            all_success = False
            continue
        success = check_nomination(congress, nomination, label, api_key)
        if not success:
            all_success = False

    # Check notification settings
    if args.test_notify:
        topic = os.environ.get("NTFY_TOPIC")
        if not topic:
            print("\nError: NTFY_TOPIC environment variable is not set. Cannot run test notification.", file=sys.stderr)
            print("Set it using: $env:NTFY_TOPIC='your_topic' (PowerShell)", file=sys.stderr)
            all_success = False
        else:
            success = test_notification(topic)
            if not success:
                all_success = False

    print("\n--- Validation Summary ---")
    if all_success:
        print("PASS: Configuration and API access are fully functional!")
    else:
        print("FAIL: One or more validation checks failed. Please check the logs above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
