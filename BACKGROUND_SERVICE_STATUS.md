# Background Ordering Service - Status & Verification

## What It Does
The `continuous_ordering_service.py` runs 24/7 in the background on Render, placing orders automatically even when you're not on the platform. This ensures timers continue and orders are placed on schedule.

## How to Verify It's Running

### On Render Dashboard:
1. Go to https://dashboard.render.com
2. Find your service
3. Look for **TWO services**:
   - `web` - The dashboard (dashboard_server.py)
   - `worker` - The background ordering service (continuous_ordering_service.py)
4. Check the worker service status - should show "Live" with a green dot

### Check Logs:
```bash
# On Render, click the worker service → Logs tab
# You should see:
[Continuous Ordering] Starting service...
[Continuous Ordering] Loaded 35 videos from database
[Continuous Ordering] Checking video: https://...
[Continuous Ordering] Placed order for: https://... (50 views)
```

### If Worker Service Doesn't Exist:
The `render.yaml` should have BOTH services defined. If you only see the web service, the worker wasn't deployed.

## Manual Verification
Run this locally to test if ordering logic works:
```bash
cd smmfollows-bot
python3 continuous_ordering_service.py
```

You should see it checking videos and placing orders.

## Common Issues

### Issue 1: Worker Not Deployed
**Symptom**: Only see "web" service on Render, not "worker"
**Solution**: Check `render.yaml` has both services, redeploy

### Issue 2: Orders Not Placing
**Symptom**: Timers reach 0 but no orders placed
**Solution**: 
1. Check worker logs for errors
2. Verify API keys are set in environment variables
3. Check database connection

### Issue 3: Timers Reset on Refresh
**Symptom**: Refresh page and timer goes back to higher value
**Solution**: This is FIXED now - timers are calculated from server data, not client-side

## Why Timers Don't Reset Anymore

### OLD (Broken):
- Client calculates: "5 minutes until next order"
- You refresh: Client recalculates: "6 minutes until next order" (WRONG!)
- Timer resets because calculation changes

### NEW (Fixed):
- Server stores: `next_purchase_time = "2024-01-16 15:30:00"`
- Client displays: Time until that fixed timestamp
- You refresh: Still shows time until same timestamp (CORRECT!)
- Timer continues counting down

## How Orders Are Placed When You're Offline

1. **Background Service** runs every 30 seconds
2. For each video, it:
   - Checks if `next_purchase_time` has passed
   - If yes: Places order automatically
   - Updates `next_purchase_time` for next order
   - Saves to database
3. **Dashboard** reads from database
   - Shows time until the server-set `next_purchase_time`
   - Updates every 5 seconds while orders processing
   - You see real-time progress even if orders were placed offline

## Testing

### Test 1: Orders While Offline
1. Set a video with a short timer (5 minutes)
2. Close the browser
3. Wait for timer to reach 0
4. Open browser again
5. **Expected**: Order was placed, count updated

### Test 2: Timer Persistence
1. Note the "TIME NEXT" value
2. Refresh the page
3. **Expected**: Timer shows same or slightly lower value, not reset

### Test 3: Background Service
1. Check Render worker logs
2. **Expected**: See "[Continuous Ordering] Checking video..." every 30s

## Environment Variables Required

Make sure these are set in Render:
- `DATABASE_URL` - PostgreSQL connection
- `API_KEY` - SMM API key (already set)
- `RENDER` - Set to "true" (auto-set by Render)

## Force Restart Service

If you need to restart the background service:
1. Go to Render dashboard
2. Click the worker service
3. Click "Manual Deploy" → "Clear build cache & deploy"
