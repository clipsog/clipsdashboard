# 🚀 RapidAPI Integration Setup

## Overview

The dashboard now supports **RapidAPI** for fetching TikTok analytics instead of web scraping. This provides:

- ✅ **More reliable data** (no more "0 views" issues)
- ✅ **Better performance** (faster API calls)
- ✅ **Handles all URL formats** (including vt.tiktok.com)
- ✅ **Automatic fallback** to web scraping if API fails

## Setup Instructions

### 1. Get RapidAPI Key

1. Go to [RapidAPI Hub](https://rapidapi.com/hub)
2. **Sign up** for a free account
3. Subscribe to one of these TikTok APIs:

#### Recommended APIs (Choose One):

**Option A: TikTok API by DataFanatic** (Most Popular)
- URL: https://rapidapi.com/DataFanatic/api/tiktok-api23
- Free tier: 500 requests/month
- Best for: General video analytics

**Option B: TikTok Video Downloader**
- URL: https://rapidapi.com/yi005/api/tiktok-video-no-watermark2
- Free tier: 100 requests/month
- Best for: Video data + analytics

**Option C: TikTok Scraper**
- URL: https://rapidapi.com/logicbuilder/api/tiktok-scraper7
- Free tier: 500 requests/month
- Best for: Comprehensive scraping

### 2. Get Your API Key

1. After subscribing, go to **your app** in RapidAPI
2. Find your **X-RapidAPI-Key** in the **Code Snippets** section
3. Copy the key (looks like: `abc123xyz456...`)

### 3. Add API Key to Environment

#### On Render (Production):

1. Go to your Render Dashboard
2. Click on your **clipsdashboard** service
3. Go to **Environment** tab
4. Click **Add Environment Variable**
5. Set:
   - **Key**: `RAPIDAPI_KEY`
   - **Value**: `your_api_key_here`
6. Click **Save Changes**
7. Service will auto-redeploy

#### Locally (Development):

Add to your shell profile or `.env`:

```bash
export RAPIDAPI_KEY="your_api_key_here"
```

Or run the dashboard with:

```bash
RAPIDAPI_KEY="your_api_key_here" python dashboard_server.py
```

### 4. Verify It's Working

Check the logs when the dashboard starts:

```
[INIT] ✅ RapidAPI TikTok integration loaded
```

And when fetching analytics:

```
[RapidAPI] 🚀 Attempting RapidAPI fetch for https://www.tiktok.com/...
[RapidAPI] ✅ SUCCESS: 5000 views, 200 likes
```

If RapidAPI isn't configured, you'll see:

```
[RapidAPI] ⚠️ No RAPIDAPI_KEY found in environment, skipping RapidAPI (using web scraping)
[WEB SCRAPE] 🕷️ Using web scraping for https://www.tiktok.com/...
```

## How It Works

### Fetch Priority:

1. **RapidAPI** (if configured) - tries 3 different API hosts
2. **Web Scraping** (fallback) - BeautifulSoup HTML parsing

### Code Example:

```python
from rapidapi_tiktok import fetch_tiktok_analytics_rapidapi

# Fetch analytics for any TikTok URL
result = fetch_tiktok_analytics_rapidapi('https://www.tiktok.com/@user/video/123')

print(result)
# {'views': 5000, 'likes': 200, 'comments': 50, 'shares': 30}
```

### Testing the Integration:

```bash
cd smmfollows-bot
python rapidapi_tiktok.py "https://www.tiktok.com/@user/video/123"
```

## API Limits & Costs

### Free Tiers:
- **DataFanatic**: 500 requests/month
- **Video Downloader**: 100 requests/month
- **Scraper**: 500 requests/month

### Paid Plans (if you exceed free tier):
- **Basic**: ~$10-20/month (5,000-10,000 requests)
- **Pro**: ~$50/month (50,000 requests)
- **Ultra**: ~$200/month (500,000 requests)

### How Many Requests Do You Need?

If you have:
- **10 videos** refreshing every **5 minutes** = ~2,880 requests/day = ~86,400/month
- **50 videos** refreshing every **5 minutes** = ~14,400 requests/day = ~432,000/month

**Recommendation**: Start with the **free tier** to test. Upgrade if you exceed limits.

## Troubleshooting

### "No API key found"
- Check environment variable is set: `echo $RAPIDAPI_KEY`
- On Render, verify the env var is in the dashboard
- Restart the service after adding the key

### "All API hosts failed"
- Check your RapidAPI subscription is active
- Verify you haven't exceeded your request quota
- Check the API key is correct (no extra spaces)

### Still getting "0 views"
- RapidAPI fallback to web scraping means the API failed
- Check logs to see which method succeeded
- Try a different RapidAPI provider

## Benefits of RapidAPI

### Before (Web Scraping):
```
[FETCH DEBUG] https://vt.tiktok.com/ZS5K7tfH5/... status_code=200
[FETCH DEBUG] found 12 script tags total
⚠️ ZERO VIEWS returned for https://vt.tiktok.com/ZS5K7tfH5/...
```

### After (RapidAPI):
```
[RapidAPI] 🚀 Attempting RapidAPI fetch for https://vt.tiktok.com/ZS5K7tfH5/...
[RapidAPI] ✅ SUCCESS: 3,271 views, 85 likes
```

## Need Help?

- Check the logs for `[RapidAPI]` messages
- Test the integration: `python rapidapi_tiktok.py <video_url>`
- If issues persist, the system will automatically fall back to web scraping

---

**Ready to go!** 🎉 Just add your `RAPIDAPI_KEY` to the environment and restart the service.
