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
- **IMPORTANT**: Configure persistent disk to prevent data loss on redeploy (see below)
- API keys are in code (consider using environment variables for production)

## Preventing Data Loss on Redeploy

**CRITICAL**: By default, Render does NOT persist the `data/` directory across deployments. To prevent videos from disappearing from campaigns when you redeploy:

### Configure Persistent Disk

1. Go to your Render dashboard: https://dashboard.render.com
2. Click on your `smmfollows-dashboard` service  
3. Go to **Settings** tab
4. Scroll down to **Disks**
5. Click **Add Disk**
6. Configure:
   - **Name**: `smmfollows-data`
   - **Mount Path**: `/opt/render/project/src/data`
   - **Size**: 1 GB (free)
7. Click **Save**
8. Service will automatically redeploy with persistent storage

### What This Does

- Your `campaigns.json` and `progress.json` files persist across deployments
- Videos added to campaigns won't disappear when you redeploy
- The app also includes automatic rebuild logic on startup as a fallback

### Verification

After configuring the disk and redeploying, check the startup logs:

```
🚀 Starting SMM Follows Dashboard and Bot...
🔄 Rebuilding campaigns from progress.json...
✅ Campaigns already in sync with progress.json
```

If you see videos being restored, that's normal for the first deploy after adding the disk.
