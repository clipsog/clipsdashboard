# Deploying to Render

This guide will help you deploy the SMM Follows Dashboard to Render's free tier.

## Prerequisites

1. A GitHub account
2. A Render account (sign up at https://render.com)

## Deployment Steps

### 1. Push to GitHub

First, push your code to a GitHub repository:

```bash
cd smmfollows-bot
git init
git add .
git commit -m "Initial commit"
git remote add origin <your-github-repo-url>
git push -u origin main
```

### 2. Create Render Web Service

1. Go to https://dashboard.render.com
2. Click "New +" → "Web Service"
3. Connect your GitHub repository
4. Configure the service:
   - **Name**: `smmfollows-dashboard` (or your preferred name)
   - **Environment**: `Python 3`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python app.py`
   - **Health Check Path**: `/health`

### 3. Environment Variables (Optional)

Render will automatically set the `PORT` environment variable. You can add custom environment variables if needed:
- `RENDER`: Set to `true` (automatically set by Render)
- `RENDER_EXTERNAL_URL`: Your service URL (automatically set by Render)

### 4. Deploy

Click "Create Web Service" and Render will:
- Build your application
- Start the server
- Keep it running with automatic health checks

## Features

- **Always Running**: The service includes a health check endpoint that Render pings automatically
- **Continuous Bot**: The delivery bot runs continuously in the background, checking for orders every 5 minutes
- **Mobile Responsive**: The dashboard is optimized for mobile devices
- **Health Pings**: Internal health pinger keeps the instance alive (pings every 5 minutes)

## Accessing the Dashboard

Once deployed, you'll get a URL like: `https://smmfollows-dashboard.onrender.com`

You can access this from:
- Desktop browsers
- Mobile browsers
- Any device with internet access

## Monitoring

- Check the Render dashboard for logs
- Health check endpoint: `https://your-service.onrender.com/health`
- The bot will automatically process videos and place orders

## Notes

- Free tier may spin down after 15 min inactivity, but health checks keep it alive
- **Data Persistence (Free Tier Solution)**: Since persistent disks are a premium feature, the app uses automatic rebuild on startup
  - On every startup, campaigns are automatically rebuilt from `progress.json`
  - Videos with `campaign_id` set are restored to their campaigns
  - **Important**: The `progress.json` file is the source of truth for all video-campaign relationships
  - As long as `progress.json` persists (it's in git), campaigns can be rebuilt
- **Backup Strategy**: Periodically commit your `data/*.json` files to git to preserve state across redeployments
- API keys are in code (consider using environment variables for production)

## Free Tier Data Persistence Strategy

Since Render's free tier doesn't include persistent disks, use this approach:

### Automatic Rebuild (Already Configured)

The app automatically rebuilds campaigns from `progress.json` on every startup. This means:
- If `campaigns.json` is outdated after redeploy → automatically fixed on startup
- As long as videos have `campaign_id` in `progress.json`, they'll be restored
- No manual intervention needed after redeployment

### Optional: Commit Data Files

To preserve the exact state across redeployments, you can periodically commit data files:

```bash
# Commit current state
git add data/campaigns.json data/progress.json
git commit -m "Update campaign data"
git push
```

Then redeploy on Render - it will pull the latest data files.

### How It Works

1. **During Runtime**: Videos added to campaigns update both `campaigns.json` and `progress.json` (with `campaign_id`)
2. **On Redeploy**: Render pulls code from git (may have old `campaigns.json`)
3. **On Startup**: App automatically runs rebuild logic:
   - Reads `progress.json` 
   - Finds all videos with `campaign_id`
   - Restores them to campaigns
   - Saves updated `campaigns.json`
4. **Result**: All videos back in their campaigns, even with free tier!
