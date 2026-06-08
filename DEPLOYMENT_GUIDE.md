# Domain Extractor System — Deployment Guide

---

## ⚡ One-Click Push (Everyday Use)

Once you have completed the First-Time Setup below, deploying any future changes is as simple as:

1. Open **PowerShell** in the `h:\Domain Extract` folder.
2. Run the push script:
   ```powershell
   .\push.ps1
   ```
3. Enter a brief commit message (or press **Enter** to use a timestamp).
4. Done! The script will:
   - Stage all your changes.
   - Commit with your message.
   - Push to GitHub.
   - Vercel will auto-detect the push and rebuild & redeploy your dashboard in ~1 minute.
   - If you modified any file in `supabase/migrations/`, GitHub Actions will automatically apply the new SQL to your live Supabase database.

> **Tip:** You can also double-click `push.ps1` in File Explorer and choose *"Run with PowerShell"* for a zero-terminal workflow.

---

## 📋 First-Time Setup

You only need to complete these steps **once**.

### Step 1 — Create a GitHub Repository

1. Go to [github.com](https://github.com) and sign in.
2. Click the **+** icon at the top right → **New repository**.
3. Fill in:
   - **Repository name**: e.g. `domain-extractor`
   - **Visibility**: Private (recommended)
   - ❌ Do **NOT** check "Add a README file" or any other option.
4. Click **Create repository**.
5. Copy the repository URL shown (e.g. `https://github.com/USERNAME/domain-extractor.git`).

---

### Step 2 — Push Code to GitHub (First Time)

Open **PowerShell** inside `h:\Domain Extract` and run:

```powershell
# The script handles first-time setup automatically
.\push.ps1
```

When prompted, paste your GitHub repository URL (from Step 1). The script will initialize Git, stage all files, commit, and push automatically.

---

### Step 3 — Set Up Supabase Database

1. Go to [supabase.com](https://supabase.com) and sign in.
2. Click **New Project**, choose an organization, and fill in:
   - **Project Name**: e.g. `domain-extractor`
   - **Database Password**: Choose a strong password and **save it securely** (you will need it later).
   - **Region**: Choose the region closest to you.
3. Click **Create new project** and wait ~2 minutes for provisioning.
4. Once ready, in the left sidebar click **SQL Editor** → **New Query**.
5. Open the file [`supabase/migrations/20260608000000_init_schema.sql`](./supabase/migrations/20260608000000_init_schema.sql) from your project folder, copy all its contents, paste into the SQL Editor, and click **Run**.
6. Go to **Project Settings** → **API** and copy:
   - **Project URL** — looks like `https://xxxxxxxxxxxx.supabase.co`
   - **service_role** secret key — click *Reveal* and copy it carefully.

---

### Step 4 — Deploy to Vercel

1. Go to [vercel.com](https://vercel.com) and sign in with your GitHub account.
2. Click **Add New** → **Project**.
3. Find and import your `domain-extractor` GitHub repository.
4. Configure the build settings:
   - **Framework Preset**: `Astro` (auto-detected)
   - **Root Directory**: Click *Edit* and type `minor-meteor` → click **Continue**.
   - **Environment Variables**: Add the following two variables:

   | Variable Name | Value |
   |---|---|
   | `SUPABASE_URL` | Your Supabase Project URL (from Step 3) |
   | `SUPABASE_SERVICE_ROLE_KEY` | Your Supabase service_role key (from Step 3) |

5. Click **Deploy**. Wait ~1 minute. Once finished, copy your live dashboard URL (e.g. `https://domain-extractor.vercel.app`).

---

### Step 5 — Configure GitHub Secrets

These secrets allow GitHub Actions to run the Python scraper and auto-deploy database migrations:

1. In your GitHub repository page, go to **Settings** → **Secrets and variables** → **Actions**.
2. Click **New repository secret** and add all four secrets below:

   | Secret Name | Where to find it |
   |---|---|
   | `SUPABASE_URL` | Your Supabase Project URL |
   | `SUPABASE_SERVICE_ROLE_KEY` | Your Supabase service_role key |
   | `SUPABASE_PROJECT_ID` | The `xxxx` part of `https://supabase.com/dashboard/project/xxxx` |
   | `SUPABASE_DB_PASSWORD` | The database password you set in Step 3 |

---

### Step 6 — Set Up 5-Minute Cron Job

This sends a request to your Vercel serverless function every 5 minutes to check if tracked domains have become available:

1. Go to [cron-jobs.org](https://cron-jobs.org) and register a free account.
2. Click **Create Cron Job** and fill in:
   - **Title**: `Domain Availability Checker`
   - **URL**: `https://YOUR-VERCEL-URL.vercel.app/api/cron`
   - **Schedule**: Click **Every** → select `5 Minutes`
   - **Request method**: `GET`
3. Click **Create**. The cron is now active 24/7.

---

### Step 7 — Configure Dashboard Settings (Final Step)

Open your live Vercel URL in your browser:

#### A. Telegram Bot Setup
1. Go to the **Settings** page in the dashboard.
2. Under **Telegram Bot Setup**, fill in your Bot Token and Chat ID.
3. Click **Save Telegram Config**.
4. Click **Test Notification** — you should receive a Telegram message instantly.

> **Don't have a Telegram bot yet?** Open Telegram → search `@BotFather` → type `/newbot` → follow the instructions to get your token. For Chat ID, forward any message to `@userinfobot`.

#### B. ExpiredDomains.net Cookies
1. Open [expireddomains.net](https://expireddomains.net) in Chrome and log in.
2. Press `F12` → **Application** → **Cookies** → `https://www.expireddomains.net`.
3. Find and copy the values for:
   - `sessionid`
   - `expireddomains_session`
4. Paste them in the Dashboard → **Settings** → **ExpiredDomains Cookies** → **Update Session Cookies**.

#### C. GitHub Scraper Trigger
1. Go to [github.com/settings/tokens](https://github.com/settings/tokens).
2. Click **Generate new token (classic)**.
3. Give it a name, set expiry, and check the `workflow` scope.
4. Copy the token (starts with `ghp_`).
5. Paste it in Dashboard → **Settings** → **GitHub Scraper Trigger** along with your GitHub username and repository name → click **Update Repository Link**.

#### D. Add Your First Search Target
1. Go to [expireddomains.net](https://expireddomains.net) and apply your desired filters.
2. Copy the full URL from the browser address bar.
3. In your Dashboard, go to **Search Targets** → paste the URL and give it a name → **Add Target**.
4. Return to **Dashboard** → click **⚡ Run Scraper Now** to start your first extraction!

---

## 🔄 Future Updates: Everyday Workflow

Whenever you make any code changes in the future:

```powershell
.\push.ps1
```

That's it. Everything else is automatic.

| What changed | What happens automatically |
|---|---|
| Dashboard code (`minor-meteor/`) | Vercel rebuilds and redeploys |
| Scraper code (`scraper/`) | GitHub Actions syncs on next scheduled run |
| SQL schema (`supabase/migrations/*.sql`) | GitHub Actions applies migration to live DB |
