# Promotion Status Monitor Setup Instructions

This repository contains a simple Python script and GitHub Actions workflow designed to monitor the Senate confirmation status of Brigadier General Jason D. Voorheis's promotion to Lieutenant General (**PN1048**).

Whenever the status changes on Congress.gov, you will receive a push notification on your Android phone for free.

---

## Step 1: Set up the **ntfy** App on Your Android Phone

1. Download the free, open-source **ntfy** app:
   - [Google Play Store](https://play.google.com/store/apps/details?id=io.heckel.ntfy)
   - [F-Droid](https://f-droid.org/en/packages/io.heckel.ntfy/)
2. Open the app and click the **+ (Plus)** button to subscribe to a new topic.
3. Choose a unique, random name for your topic (e.g., `voorheis-promotion-alerts-xyz789`) so others do not accidentally receive your notifications.
4. Subscribe to the topic. Keep the app open or running in the background.

---

## Step 2: Push this Repository to GitHub

If you haven't initialized git in this folder yet, run these commands in your terminal:

```bash
git init
git add .
git commit -m "Initial commit of monitor script and action"
```

Then, create a **private** repository on GitHub (it's completely free) and run:

```bash
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
git push -u origin main
```

---

## Step 3: Configure GitHub Actions Secrets

For security, the script looks for your private topic name and optional API keys in GitHub Secrets:

1. Go to your GitHub repository in your browser.
2. Navigate to **Settings** > **Secrets and variables** > **Actions**.
3. Click **New repository secret**.
4. Add the following secrets:
   - **`NTFY_TOPIC`**: The unique topic name you subscribed to in Step 1 (e.g., `voorheis-promotion-alerts-xyz789`).
   - **`CONGRESS_API_KEY`** *(Optional)*: You can register a free API key at [api.data.gov](https://api.data.gov/) and add it here. If omitted, the script will use `DEMO_KEY` (which works but has lower hourly rate limits).

---

## Step 4: Enable Workflow Writing Permissions

Because the action commits the updated status back to the repository (`status.json`), you must give GitHub Actions write permissions:

1. In your GitHub repository, go to **Settings** > **Actions** > **General**.
2. Scroll down to **Workflow permissions**.
3. Select **Read and write permissions**.
4. Click **Save**.

---

## How It Works

* **Automatic Schedule**: The workflow runs automatically twice a day (at 00:00 and 12:00 UTC).
* **Manual Check**: You can manually trigger a check at any time by going to the **Actions** tab in your GitHub repository, clicking **Monitor Senate Confirmation**, and clicking **Run workflow**.
