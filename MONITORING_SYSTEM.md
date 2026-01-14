# Monitoring System for Multiple Videos (24+ Hours)

## Overview

The monitoring system tracks multiple videos simultaneously over 24+ hours, ensuring orders are placed correctly and delivery is progressing.

## Components

### 1. **Progress Tracking** (`progress.json`)
Stores state for each video:
- Orders placed (views, likes, comments, comment likes)
- Order history with timestamps
- Next scheduled orders
- Start time and targets
- Real analytics snapshots

### 2. **Order History** (`orders.json`)
Complete log of all orders:
- Order ID
- Service type
- Quantity
- Timestamp
- Status

### 3. **Real-Time Monitoring** (`monitor_progress.py`)
- Checks real TikTok analytics
- Compares ordered vs delivered
- Shows progress for all videos
- Identifies issues

### 4. **Continuous Monitor** (`continuous_monitor.py`)
- Runs in background
- Checks every 5 minutes
- Updates status automatically
- Alerts on issues

## Usage

### Check Status Once
```bash
python monitor_progress.py
```

### Continuous Monitoring (Background)
```bash
python continuous_monitor.py
```

### Check Order Statuses
```bash
python monitor_progress.py --check-orders "VIDEO_URL"
```

## What Gets Monitored

### For Each Video:
1. **Orders Placed**
   - Views ordered vs target
   - Likes ordered vs target
   - Comments ordered
   - Comment likes ordered

2. **Real Analytics**
   - Actual TikTok views
   - Actual TikTok likes
   - Actual TikTok comments
   - Delivery rate (delivered/ordered)

3. **Timeline Progress**
   - Elapsed time vs 24 hours
   - Next scheduled orders
   - Orders behind schedule

4. **Issues Detection**
   - Orders not being placed
   - Delivery not happening
   - API errors
   - Balance issues

## Monitoring Features

### ✅ **Multi-Video Support**
- Track unlimited videos simultaneously
- Each video has independent progress
- Summary shows totals across all videos

### ✅ **Real Analytics Integration**
- Fetches actual TikTok stats
- Compares ordered vs delivered
- Shows delivery rate percentage

### ✅ **Order Status Checking**
- Verifies orders are processing
- Tracks completion status
- Identifies failed orders

### ✅ **Automatic Issue Detection**
- Alerts if orders are behind schedule
- Warns if delivery rate is low
- Notifies of API errors

### ✅ **Progress Persistence**
- Saves progress after each order
- Can resume if interrupted
- Complete audit trail

## Example Output

```
╔══════════════════════════════════════════════╗
║   Monitoring 3 Active Video(s)        ║
╚══════════════════════════════════════════════╝

============================================================
Video: https://www.tiktok.com/@user/video/123...
============================================================
Started: 2024-01-09 10:00:00
Elapsed: 5.2 hours / 24 hours
Progress: 21.7% of timeline

Orders Placed:
  Views: 2,100/4,000 (52.5%)
  Likes: 65/125 (52.0%)
  Comments: 10 (target: 7)
  Comment Likes: 50 (target: 15)

Real TikTok Analytics:
  Views: 1,850 / 4,000 (46.3%)
  Likes: 58 / 125 (46.4%)
  Comments: 8

Delivery Status:
  Views Delivery: 88.1% (1,850/2,100 delivered)

Next Orders Scheduled:
  Views: 50 at 15:18:00 (in 18 min)
  Likes: 10 at 15:50:00 (in 50 min)

============================================================
SUMMARY
============================================================

Active Videos: 3
Total Views Ordered: 6,300
Total Likes Ordered: 195
Total Cost: $0.6834
```

## Integration with Bot

The bot automatically:
1. Saves progress after each order
2. Updates order history
3. Schedules next orders
4. Records timestamps

Monitor can run independently to check status anytime.

## Alerts & Notifications

Future enhancements:
- Email alerts on issues
- SMS notifications
- Webhook integration
- Dashboard UI

## Files

- `monitor_progress.py` - Main monitoring script
- `continuous_monitor.py` - Background monitor
- `~/.smmfollows_bot/progress.json` - Progress data
- `~/.smmfollows_bot/orders.json` - Order history
- `~/.smmfollows_bot/monitor.log` - Monitor logs


