# Quick Deploy Guide

## Step 1: Initialize Git Repository

```bash
cd smmfollows-bot
git init
git add .
git commit -m "Initial commit - Ready for Render deployment"
```

## Step 2: Create GitHub Repository

1. Go to https://github.com/new
2. Create a new repository (make it **private** if you want to keep your API keys secure)
3. **Don't** initialize with README, .gitignore, or license
4. Copy the repository URL

## Step 3: Push to GitHub

```bash
git remote add origin <your-github-repo-url>
git branch -M main
git push -u origin main
```

## Step 4: Deploy on Render

1. Go to https://dashboard.render.com
2. Sign up/login (free account works)
3. Click **"New +"** → **"Web Service"**
4. Connect your GitHub account (if not already connected)
5. Select your repository
6. Render will auto-detect the `render.yaml` file
7. Verify settings:
   - **Name**: `smmfollows-dashboard` (or your choice)
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`
   - **Health Check Path**: `/health`
8. Click **"Create Web Service"**

## Step 5: Wait for Deployment

- Render will build and deploy (takes 2-5 minutes)
- Watch the logs for any errors
- Once deployed, you'll get a URL like: `https://smmfollows-dashboard.onrender.com`

## Step 6: Access Your Dashboard

- Open the URL on any device (desktop, phone, tablet)
- The dashboard is mobile-responsive
- The bot will automatically start processing orders

## Troubleshooting

- **Build fails**: Check logs in Render dashboard
- **Service crashes**: Check logs for Python errors
- **Health check fails**: Ensure `/health` endpoint is working
- **Bot not running**: Check logs for bot thread errors

## Notes

- Free tier may spin down after 15 min inactivity, but health checks keep it alive
- **Data Persistence**: The app uses automatic rebuild on startup (free tier compatible)
- API keys are in code (consider using environment variables for production)

## Data Persistence on Free Tier

Since Render's persistent disks require a paid plan, this app uses an automatic rebuild strategy:

### How It Works

1. **Automatic Rebuild on Startup** (`app.py`):
   - Every time the app starts, it automatically rebuilds campaigns from `progress.json`
   - Videos with `campaign_id` are restored to their campaigns
   - Uses atomic file writes to prevent corruption

2. **Source of Truth**:
   - `progress.json` stores each video's `campaign_id`
   - This file is tracked in git and survives redeployments
   - As long as progress.json has the data, campaigns can be rebuilt

### What Happens on Redeploy

1. Render pulls latest code from git (may include old `campaigns.json`)
2. App starts and runs rebuild logic
3. Reads `progress.json` to find videos with `campaign_id`
4. Restores all videos to their campaigns
5. Saves updated `campaigns.json`

**Result**: No data loss, even on free tier!

### Verification

Check the startup logs after deployment:

```
🚀 Starting SMM Follows Dashboard and Bot...
🔄 Rebuilding campaigns from progress.json...
  ✓ Restored video to campaign_1_xxx: https://...
✅ Rebuilt 10 video(s) to campaigns
```

### Optional: Preserve Exact State

To preserve the exact state of `campaigns.json` across redeployments (optional):

```bash
# Periodically commit data files
git add data/campaigns.json data/progress.json
git commit -m "Update campaign data"
git push
```

Then trigger a redeploy on Render - it will pull the latest versions.

### Troubleshooting

**Videos still missing after redeploy?**
1. Check startup logs for rebuild messages
2. Verify videos in `progress.json` have `campaign_id` field set
3. Try restarting the service to trigger rebuild

**Want to force a rebuild?**
Restart the service from Render dashboard - rebuild runs on every startup.
