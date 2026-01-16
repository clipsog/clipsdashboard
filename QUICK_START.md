# Quick Start - Get Orders Placing

## Problem: "Timers never reach 0" / "Orders never placed"

This happens when the **Continuous Ordering Service is not running**.

## Solution: Start the Ordering Service

### Option 1: Run Locally (Quick Test)

```bash
cd /Users/duboisca/Desktop/LitoStream/kick/smmfollows-bot
python3 continuous_ordering_service.py
```

You should see:
```
╔══════════════════════════════════════════════════╗
║   Continuous Ordering Service (24/7)            ║
╚══════════════════════════════════════════════════╝

Cycle #1 - 2024-01-15 14:30:00
============================================================
🔍 Checking 10 scheduled order(s)...
   Start time: 2024-01-15 10:00:00
   Current time: 2024-01-15 14:30:00
   Completed: 3 order(s)
   [Views] 50 @ 4h 30m (scheduled: 14:30:00, diff: 0.0min)
      ✓ DUE - Will place order
📦 Placing 1 due order(s)...
✓ Order placed! ID: 12345
```

If you see "No orders due", the timers are working but nothing is scheduled yet.

### Option 2: Run in Background (24/7)

```bash
# Using screen (recommended)
screen -S ordering
python3 continuous_ordering_service.py
# Press Ctrl+A then D to detach

# To check if it's running
screen -ls

# To reattach
screen -r ordering
```

### Option 3: Deploy to Render (Automatic)

Already configured! After pushing to GitHub, Render will:
1. Deploy `clipsdashboard` (web service)
2. Deploy `ordering-service` (worker service) **← This places orders**

Check Render dashboard - you should see **2 services running**.

## Diagnostic Tools

### 1. Check Timer Status
```bash
python3 check_timers.py
```

Shows:
- Which videos have orders due
- Time until next order
- OVERTIME status
- Start times and elapsed time

### 2. Check if Service is Running
```bash
# Check locally
ps aux | grep continuous_ordering_service

# Check on Render
# Go to dashboard.render.com > ordering-service > Logs
```

### 3. Manual Test (Single Video)
```bash
# Test ordering logic for one video
python3 -c "from run_delivery_bot import DeliveryBot; bot = DeliveryBot('YOUR_VIDEO_URL'); bot.check_and_place_due_orders()"
```

## Common Issues

### Issue: "No orders due" but timer shows 0:00
**Cause**: Orders already completed or goals reached
**Check**: Run `python3 check_timers.py` to see completed orders

### Issue: "No start_time found"
**Cause**: Video missing start_time in progress.json
**Fix**: Run the delivery bot for that video:
```bash
python3 run_delivery_bot.py YOUR_VIDEO_URL
```

### Issue: Service stops after a while
**Cause**: Terminal closed or server restarted
**Fix**: Use `screen` or deploy to Render for 24/7 operation

### Issue: Timer shows time remaining but never decreases
**Cause**: Ordering service not running
**Fix**: Start `continuous_ordering_service.py`

## What Each Service Does

### Dashboard (`dashboard_server.py`)
- Shows UI with timers
- Displays countdowns
- **Does NOT place orders**

### Ordering Service (`continuous_ordering_service.py`)
- Monitors all videos every 30 seconds
- Places orders when timers reach 0
- Handles OVERTIME mode
- **THIS IS REQUIRED FOR AUTOMATIC ORDERING**

## Verification Checklist

Run through this checklist:

- [ ] Ordering service is running (check with `ps aux | grep continuous` or Render dashboard)
- [ ] Videos have start_time set (check with `check_timers.py`)
- [ ] purchase_schedule.json exists in smmfollows-bot folder
- [ ] Videos are not ended (status != 'ended')
- [ ] Goals not already reached

If all checked, orders will be placed automatically!

## Quick Command Reference

```bash
# Start ordering service
python3 continuous_ordering_service.py

# Check timer status
python3 check_timers.py

# Check if running
ps aux | grep continuous_ordering_service

# Kill if stuck
pkill -f continuous_ordering_service

# Restart
python3 continuous_ordering_service.py
```

## Still Not Working?

1. **Check logs** - Run `python3 check_timers.py` for detailed status
2. **Verify database** - Make sure DATABASE_URL is set (for Render)
3. **Check local files** - Verify `~/.smmfollows_bot/progress.json` exists
4. **Test manually** - Try placing one order manually to verify API key works

Need more help? Check the logs from `continuous_ordering_service.py` - they show exactly what's happening.
