# Dashboard Guide

## Overview

The dashboard provides a real-time view of all videos currently being processed by the bot, showing progress, statistics, and status.

## Usage

### Summary Dashboard (Quick View)

```bash
python dashboard.py
```

Shows a compact table with all videos:
- Video identifier (username/video ID)
- Views progress (current/target)
- Likes progress (current/target)
- Comments (ordered/target)
- Comment Likes (ordered/target)
- Overall progress percentage
- Time elapsed since start
- Status indicator (✅ 🟢 🟡 🟠 🔴)

### Detailed Dashboard

```bash
python dashboard.py --detailed
```

Shows detailed information for all videos including:
- Progress bars for each metric
- Breakdown of existing vs ordered counts
- Time information
- Total cost
- Order count

### Single Video Detail

```bash
python dashboard.py --detailed <video_url>
```

Shows detailed information for a specific video.

## Features

### Status Indicators

- ✅ **Complete** - 100% progress
- 🟢 **75%+** - Good progress
- 🟡 **50%+** - Moderate progress
- 🟠 **25%+** - Early stage
- 🔴 **<25%** - Just started

### Progress Tracking

The dashboard tracks:
- **Views**: Existing views + ordered views = total
- **Likes**: Existing likes + ordered likes = total
- **Comments**: Ordered comments (minimum 10)
- **Comment Likes**: Ordered comment likes (minimum 50)

### Time Tracking

Shows:
- Time elapsed since bot started
- Start timestamp
- Estimated completion (based on delivery schedule)

## Examples

### View all videos summary
```bash
python dashboard.py
```

### View detailed progress for all videos
```bash
python dashboard.py --detailed
```

### View specific video details
```bash
python dashboard.py --detailed "https://www.tiktok.com/@user/video/1234567890"
```

## Integration with Bot

The dashboard reads from `~/.smmfollows_bot/progress.json`, which is automatically updated by:
- `run_delivery_bot.py` - Main bot script
- `manage_videos.py` - Video management system

## Tips

1. **Run dashboard in separate terminal** - Keep it open to monitor progress
2. **Use `--detailed` for troubleshooting** - See exact numbers and breakdowns
3. **Check status indicators** - Quick visual feedback on progress
4. **Monitor cost** - Track spending across all videos

## Output Format

### Summary View
```
Video                          Views          Likes        Comments    C.Likes     Progress   Time       Status
────────────────────────────────────────────────────────────────────────────────────────────────────────────
@username                      1,234/4,000    45/125       5/7         10/15       30.9%      2h 15m     🟡
video_id...
```

### Detailed View
```
Video: @username - video_id
────────────────────────────────────────────────────────────────────────────────────────────────────────────

Views:
  ████████████░░░░░░░░░░░░░░░░░░░░░░
  1,234 / 4,000 (30.9%)
    Existing: 1,000 | Ordered: 234

Likes:
  ██████████████████████████████████
  45 / 125 (36.0%)
    Existing: 20 | Ordered: 25
```

## Troubleshooting

**No videos shown?**
- Make sure you've run `run_delivery_bot.py` at least once
- Check that `~/.smmfollows_bot/progress.json` exists

**Progress not updating?**
- The bot updates progress after each order
- Refresh the dashboard to see latest updates

**Wrong numbers?**
- The dashboard shows "existing + ordered = total"
- Existing counts come from real analytics fetching
- Ordered counts come from placed orders


