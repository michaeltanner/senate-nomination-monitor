# Senate Nomination Monitor

An automated, serverless monitor that tracks the confirmation status of Presidential Nominations (PNs) on Congress.gov and sends push notifications to your mobile phone (Android/iOS) for free via **ntfy.sh**.

---

## Features

* **Configurable Tracking**: Declare which nominations to track in `config.json`.
* **Chronological Playback**: On first subscription, the script automatically sends a push notification for **every** historical action in chronological order (oldest to newest).
* **Smart Alerting**: Subsequent scheduled runs check for updates and only alert you when new actions occur.
* **Local Validation**: Includes a command-line script (`validate.py`) to test your setup and verify API connectivity and actions history before deploying.

---

## How to Configure the Automatic Schedule (Cron)

You can control how often the monitor runs automatically by editing the schedule in the `.github/workflows/monitor.yml` file. 

The schedule uses the standard **cron syntax** (written in UTC time):

### Scheduling Examples:

#### 1. Turn Off Automatic Runs (Never Run Automatically)
To disable automatic monitoring and only run the script when you manually click the "Run workflow" button, edit the workflow file so that `on:` only contains `workflow_dispatch`:
```yaml
on:
  workflow_dispatch: # Allows manual runs from the GitHub UI
```

#### 2. Run Every X Minutes
* **Every 15 minutes**:
  ```yaml
  on:
    schedule:
      - cron: '*/15 * * * *'
  ```
  *(Note: GitHub Actions has a minimum limit of 5 minutes, and high-frequency runs may experience queue delays).*

#### 3. Run Every X Hours
* **Every 3 hours** (at minute 0):
  ```yaml
  on:
    schedule:
      - cron: '0 */3 * * *'
  ```
* **Every 3 hours with an offset** (at minutes 13 and 43 of the hour, to avoid server congestion):
  ```yaml
  on:
    schedule:
      - cron: '13,43 * * * *'
  ```

#### 4. Run Every X Days
* **Once a day at midnight UTC**:
  ```yaml
  on:
    schedule:
      - cron: '0 0 * * *'
  ```
* **Every 2 days at noon UTC**:
  ```yaml
  on:
    schedule:
      - cron: '0 12 */2 * *'
  ```

---

## Local Setup & Validation

Before pushing to GitHub, you should verify your configuration and API key locally:

1. **Verify `config.json`**:
   Ensure `config.json` contains the correct Congress and nomination number you wish to track:
   ```json
   {
     "nominations": [
       {
         "congress": "119",
         "nomination": "1048",
         "label": "Brig Gen Jason Voorheis"
       }
     ]
   }
   ```

2. **Run Validation**:
   Open a terminal in this folder, set your API key environment variable, and run the validation script:
   
   **PowerShell (Windows)**:
   ```powershell
   $env:CONGRESS_API_KEY="your_actual_api_key"
   python validate.py
   ```
   
   **Bash (Mac/Linux)**:
   ```bash
   export CONGRESS_API_KEY="your_actual_api_key"
   python validate.py
   ```

   The script will print out the full history of Senate actions for your configured nominations.

3. **Optional: Test Phone Notifications**:
   If you set your `NTFY_TOPIC` environment variable as well, you can run:
   ```bash
   python validate.py --test-notify
   ```
   This will send a test alert directly to your phone.

---

## Deployment to GitHub Actions

To run the monitor on a regular schedule for free:

### Step 1: Push to GitHub
1. Create a **private** repository on GitHub (e.g. `senate-nomination-monitor`).
2. Run these commands in your local folder:
   ```bash
   git init
   git add .
   git commit -m "Initial commit of monitor"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/senate-nomination-monitor.git
   git push -u origin main
   ```

### Step 2: Configure Actions Secrets
Navigate to your GitHub repository: **Settings** > **Secrets and variables** > **Actions** and add two **Repository Secrets**:
* **`CONGRESS_API_KEY`** (Required): Your personal API key from [api.data.gov](https://api.data.gov/). (A dedicated key is required because GitHub Action's shared IPs are heavily rate-limited).
* **`NTFY_TOPIC`** (Required): The unique topic name you subscribed to in the ntfy mobile app (e.g., `senate-nomination-alerts-xyz789`).

### Step 3: Enable Write Permissions
1. Go to **Settings** > **Actions** > **General**.
2. Scroll to the bottom to **Workflow permissions**.
3. Select **Read and write permissions** and click **Save** (this allows the action to commit and save the updated status file back to the repository).

---

## How It Works

* **Trigger**: Configured via the `schedule` setting in your workflow.
* **Logs**: The execution history is written to `history_log.txt` inside your repository on every run.
* **State Preservation**: The notified history for each nomination is saved in `status_{congress}_{nomination}.json`.
