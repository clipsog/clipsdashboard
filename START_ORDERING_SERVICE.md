# Start Continuous Ordering Service

## What It Does
The Continuous Ordering Service monitors ALL videos 24/7 and automatically:
- Places orders when they're due (based on schedule)
- Continues ordering in OVERTIME mode until goals are reached
- Checks every 30 seconds for due orders
- Works across all campaigns automatically

## How to Start

### 1. Start the Service
```bash
cd /Users/duboisca/Desktop/LitoStream/kick/smmfollows-bot
python3 continuous_ordering_service.py
```

### 2. Run in Background (Recommended for 24/7)
```bash
# Option A: Using nohup
nohup python3 continuous_ordering_service.py > ordering_service.log 2>&1 &

# Option B: Using screen (recommended)
screen -S ordering
python3 continuous_ordering_service.py
# Press Ctrl+A then D to detach
# To reattach: screen -r ordering
```

### 3. Stop the Service
```bash
# If running in foreground: Press Ctrl+C

# If running in background:
ps aux | grep continuous_ordering_service
kill <PID>
```

## What You'll See
```
╔══════════════════════════════════════════════════╗
║   Continuous Ordering Service (24/7)            ║
║   Monitors all videos and places orders         ║
║   Automatically until goals are reached          ║
╚══════════════════════════════════════════════════╝

✓ Checks every 30 seconds
✓ Places orders when due
✓ Continues in OVERTIME mode until goals reached
✓ Press Ctrl+C to stop

============================================================
Cycle #1 - 2024-01-15 14:30:00
============================================================
✓ Orders placed for: https://www.tiktok.com/@user/video/123...
[OVERTIME] Orders placed for: https://www.tiktok.com/@user/video/456...

✓ Placed orders for 2 video(s)
Next check in 30 seconds...
```

## Key Features

1. **Automatic OVERTIME Mode**
   - Detects when deadline has passed
   - Continues placing orders every 30 seconds
   - Stops only when goals are reached OR manually stopped

2. **Smart Ordering**
   - Respects schedule timing
   - Places orders immediately when due
   - Checks actual delivered counts vs targets

3. **24/7 Operation**
   - Runs continuously in background
   - No manual intervention needed
   - Survives server restarts (if using screen/tmux)

## Troubleshooting

**Service not placing orders?**
- Check if videos have `target_completion_time` set
- Verify goals haven't been reached already
- Check `overtime_stopped` flag isn't set

**Want to check status?**
```bash
python3 monitor_progress.py
```

**Want to stop OVERTIME for a specific video?**
- Click "End Overtime" button on dashboard
- Or set `overtime_stopped: true` in progress.json

## For Render Deployment

Add this to your render.yaml:
```yaml
services:
  - type: worker
    name: ordering-service
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "python continuous_ordering_service.py"
    autoDeploy: true
```
