# Deploy to Render with Automatic Ordering

## What You Need

To ensure posts keep ordering until goals are reached, you need TWO services running:

1. **Web Service** (Dashboard) - Already running ✓
2. **Worker Service** (Ordering) - THIS IS WHAT KEEPS ORDERING ✓

## Option 1: Add Worker Service on Render Dashboard

1. Go to your Render dashboard: https://dashboard.render.com
2. Click "New +"
3. Select "Background Worker"
4. Connect to your GitHub repo: `clipsog/clipsdashboard`
5. Fill in:
   - **Name**: `ordering-service`
   - **Runtime**: `Python 3`
   - **Root Directory**: `smmfollows-bot`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python continuous_ordering_service.py`
6. Add Environment Variable:
   - **Key**: `DATABASE_URL`
   - **Value**: (same as your web service)
7. Click "Create Background Worker"

## Option 2: Use render.yaml (Easier)

Create `render.yaml` in your repo root:

```yaml
services:
  # Dashboard Web Service
  - type: web
    name: clipsdashboard
    runtime: python
    rootDir: ./smmfollows-bot
    buildCommand: pip install -r requirements.txt
    startCommand: python dashboard_server.py
    envVars:
      - key: DATABASE_URL
        sync: false
    autoDeploy: true
  
  # Continuous Ordering Worker Service (THIS KEEPS ORDERING!)
  - type: worker
    name: ordering-service
    runtime: python
    rootDir: ./smmfollows-bot
    buildCommand: pip install -r requirements.txt
    startCommand: python continuous_ordering_service.py
    envVars:
      - key: DATABASE_URL
        sync: false
    autoDeploy: true
```

Then:
1. Commit and push
2. Render will automatically detect and deploy both services

## What the Worker Does

The **ordering-service** worker:
- ✓ Runs 24/7 in the background
- ✓ Checks ALL videos every 30 seconds
- ✓ Places orders when they're due
- ✓ **Continues ordering in OVERTIME mode until goals are reached**
- ✓ Works across all campaigns automatically
- ✓ Never stops unless you manually stop it

## How to Verify It's Working

### Check Render Logs
1. Go to Render Dashboard
2. Click on "ordering-service"
3. Check logs - you should see:
   ```
   ╔══════════════════════════════════════════════════╗
   ║   Continuous Ordering Service (24/7)            ║
   ║   Monitors all videos and places orders         ║
   ║   Automatically until goals are reached          ║
   ╚══════════════════════════════════════════════════╝
   
   Cycle #1 - 2024-01-15 14:30:00
   ✓ Orders placed for...
   ```

### Check Dashboard
- Videos in OVERTIME should show countdown to next order
- Orders should be placed every 30 seconds
- Goals should eventually be reached

## Important Notes

1. **Worker is REQUIRED** - Without it, orders won't be placed automatically
2. **24/7 Operation** - Worker runs continuously, even when dashboard is idle
3. **Automatic Restarts** - If worker crashes, Render restarts it automatically
4. **Same Database** - Worker and web service share the same PostgreSQL database

## Pricing

- **Web Service**: Free tier (750 hours/month)
- **Worker Service**: $7/month (always running)

**Total**: $7/month for automatic ordering 24/7

## If You Don't Want to Pay

Run locally:
```bash
cd /Users/duboisca/Desktop/LitoStream/kick/smmfollows-bot
python3 continuous_ordering_service.py
```

Keep your terminal open 24/7 or use `screen`:
```bash
screen -S ordering
python3 continuous_ordering_service.py
# Press Ctrl+A then D to detach
```

## Troubleshooting

**Worker not showing up?**
- Make sure render.yaml is in repo root
- Push to GitHub
- Check Render dashboard for errors

**Orders not being placed?**
- Check worker logs
- Verify DATABASE_URL is set
- Check progress.json has videos

**Want to stop all ordering?**
- Suspend the worker service on Render
- Or delete it entirely
