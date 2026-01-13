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

- Render's free tier may spin down after 15 minutes of inactivity, but the health checks keep it alive
- The service will automatically restart if it crashes
- **Data persistence**: The `data/` directory is mounted to a persistent disk that survives across deploys
  - Your campaigns, videos, and progress data will NOT be lost when you redeploy
  - The disk is configured in `render.yaml` with 1GB storage
  - **Important**: If you delete and recreate the service, you'll need to configure the disk again
- **First deployment**: The disk will be created automatically with any existing data from your repository
