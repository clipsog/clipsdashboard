# 🚨 DATA KEEPS COMING BACK - HERE'S WHY

## The Problem

Data reappears after deletion because:

1. **Continuous Ordering Service** is still running in the background
2. It has videos in **memory/cache** from before
3. It keeps **writing them back** to the database
4. Even if you delete, it recreates them!

## The Solution (3 Steps)

### Step 1: Suspend Background Worker (CRITICAL!)

1. Go to **Render Dashboard**: https://dashboard.render.com/
2. Find: **`continuous-ordering-service`** (worker)
3. Click **"Suspend"**
4. **CONFIRM** - this stops all ordering immediately

**Without this step, data will keep coming back!**

---

### Step 2: Run Nuclear Wipe

Go to your main dashboard service → **Shell** tab, then run:

```bash
cd /opt/render/project/src
python nuclear_wipe.py
```

This will:
- Delete ALL videos from database (TRUNCATE)
- Delete ALL campaigns from database (TRUNCATE)
- Reset auto-increment IDs
- Avoid deadlocks (using TRUNCATE instead of DELETE)

You should see:
```
🚨 NUCLEAR RESET - WIPING EVERYTHING
✓ Connected to database
📊 Current data:
   Videos: 47
   Campaigns: 5
🗑️  Truncating tables...
   ✓ Deleted 47 videos
   ✓ Deleted 5 campaigns
   ✓ Reset ID sequences
✅ WIPE COMPLETE!
   Videos remaining: 0
   Campaigns remaining: 0
```

---

### Step 3: Verify Clean State

1. Refresh your dashboard (Cmd+Shift+R)
2. You should see: **"No campaigns yet. Create your first campaign..."**
3. No videos in the table

---

## Why Data Comes Back

### The Continuous Ordering Service:

```python
# continuous_ordering_service.py runs in a loop:
while True:
    progress = load_progress()  # Loads videos from memory/database
    
    for video_url in progress:
        # Check if order needed
        # Place orders
        save_progress(progress)  # Writes back to database!
    
    time.sleep(60)  # Wait 1 minute, repeat
```

**If this service is running, it will keep recreating data!**

---

## Complete Reset Checklist

- [ ] **Suspend `continuous-ordering-service`** on Render
- [ ] **Run `nuclear_wipe.py`** in Shell
- [ ] **Verify dashboard is empty**
- [ ] (Optional) **Resume worker** when ready to use again

---

## Alternative: Direct SQL (If Shell Doesn't Work)

If you can't access the Shell, run this SQL directly on Railway/Supabase:

```sql
-- Wipe everything
TRUNCATE TABLE videos CASCADE;
TRUNCATE TABLE campaigns CASCADE;

-- Reset IDs
ALTER SEQUENCE IF EXISTS videos_id_seq RESTART WITH 1;
ALTER SEQUENCE IF EXISTS campaigns_id_seq RESTART WITH 1;

-- Verify
SELECT COUNT(*) FROM videos;
SELECT COUNT(*) FROM campaigns;
```

---

## Summary

**THE WORKER IS THE CULPRIT!**

1. Suspend `continuous-ordering-service` first
2. Then run `nuclear_wipe.py`
3. Data won't come back

**The DELETE ALL button fails because the worker is actively writing while you're deleting (deadlock).**

Stop the worker first! 🛑
