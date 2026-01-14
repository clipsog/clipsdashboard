# HTML Dashboard & Time-Based Scheduling

## Overview

The dashboard provides a modern web interface to monitor videos and set target completion times. The bot automatically adjusts delivery pace to meet objectives by the specified time.

## Features

### HTML Dashboard
- **Modern Web Interface** - Beautiful, responsive design
- **Real-time Updates** - Auto-refreshes every 30 seconds
- **Progress Visualization** - Progress bars and status indicators
- **Target Time Setting** - Set completion date/time for each video
- **Multi-video Support** - Monitor all videos in one place

### Time-Based Scheduling
- **Automatic Pace Adjustment** - Bot calculates delivery pace based on target time
- **Dynamic Scheduling** - Orders are spaced to complete by target time
- **Time Compression** - Faster delivery if target is sooner than default 24h

## Usage

### Starting the Dashboard Server

```bash
python dashboard_server.py
```

The server will:
- Start on `http://localhost:8080`
- Automatically open your browser
- Run until you press Ctrl+C

### Setting Target Completion Time

1. Open the dashboard in your browser
2. For each video, use the datetime picker
3. Select your target date and time
4. Click "Set Target"
5. The bot will automatically adjust delivery pace

### How Time-Based Scheduling Works

**Example:**
- Default schedule: 24 hours
- Target completion: 12 hours from now
- Bot calculates: 2x compression factor
- All orders are spaced 2x faster

**Formula:**
```
time_factor = target_time_remaining / original_schedule_time
adjusted_order_time = original_order_time * time_factor
```

## Dashboard Features

### Video Cards
Each video shows:
- **Status Badge** - ✅ Complete, 🟢 Good, 🟡 Moderate, 🔴 Early
- **Progress Bars** - Visual progress for views, likes, comments, comment likes
- **Metrics** - Current values vs targets
- **Time Info** - Elapsed time, time remaining
- **Cost Tracking** - Total spent per video

### Target Time Section
- **DateTime Picker** - Select target completion date/time
- **Set Target Button** - Save target time
- **Time Remaining** - Shows countdown to target
- **Auto-adjustment** - Bot automatically adjusts pace

## API Endpoints

### GET `/api/progress`
Returns all video progress as JSON

### POST `/api/update-target`
Updates target completion time for a video

**Parameters:**
- `video_url` - Video URL
- `target_datetime` - ISO format datetime string

## Integration

The dashboard reads from `~/.smmfollows_bot/progress.json`, which is updated by:
- `run_delivery_bot.py` - Main bot script
- `dashboard_server.py` - Dashboard server (for target time updates)

## Examples

### Set Target for 6 Hours
1. Open dashboard
2. Select video
3. Set datetime to 6 hours from now
4. Click "Set Target"
5. Bot adjusts all orders to complete in 6 hours

### Set Target for Tomorrow
1. Open dashboard
2. Select video
3. Set datetime to tomorrow at specific time
4. Click "Set Target"
5. Bot spreads orders over longer period

## Technical Details

### Schedule Adjustment Algorithm

```python
def calculate_adjusted_schedule(purchases, target_time, start_time):
    total_time_available = (target_time - start_time).total_seconds()
    original_total_time = max([p.time_seconds for p in purchases])
    time_factor = total_time_available / original_total_time
    
    for purchase in purchases:
        purchase.time_seconds *= time_factor
```

### Time Compression Limits

- **Minimum**: Orders can't be faster than API rate limits
- **Maximum**: Orders can't be slower than delivery guarantees
- **Safety**: Bot validates time ranges before applying

## Troubleshooting

**Dashboard won't start?**
- Check if port 8080 is available
- Try: `python dashboard_server.py 8081` (different port)

**Target time not working?**
- Ensure datetime is in the future
- Check that bot is running and reading progress.json
- Verify time format is ISO: `YYYY-MM-DDTHH:MM:SS`

**Schedule not adjusting?**
- Check that target time is set in dashboard
- Verify bot is reading target_completion_time from progress.json
- Check console output for adjustment messages

## Best Practices

1. **Set realistic targets** - Don't compress too much (API limits)
2. **Monitor progress** - Check dashboard regularly
3. **Adjust as needed** - Update target time if circumstances change
4. **Keep bot running** - Bot must be active to place orders

## Future Enhancements

- [ ] Real-time WebSocket updates
- [ ] Historical progress charts
- [ ] Email/SMS notifications
- [ ] Batch target time setting
- [ ] Export progress reports


