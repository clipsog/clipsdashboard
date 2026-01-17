# 🆓 FREE TikTok Analytics - PyTok Setup

## Why PyTok?

**100% FREE** - No API keys, no paid subscriptions!

- ✅ **Open source** (GitHub: networkdynamics/pytok)
- ✅ **Browser automation** (more reliable than basic scraping)
- ✅ **Handles CAPTCHAs** automatically
- ✅ **Works with all URL formats**
- ✅ **Active maintenance** in 2025/2026
- ✅ **No rate limits** (built-in delays)

## Quick Setup

### 1. Install PyTok

```bash
pip install pytok playwright
python -m playwright install chromium
```

This installs:
- `pytok` - The TikTok scraper library
- `playwright` - Browser automation framework
- Chromium browser (for automation)

### 2. Test It Works

```bash
cd smmfollows-bot
python free_tiktok_scraper.py "https://www.tiktok.com/@user/video/123"
```

You should see:
```
[PyTok] ✅ Free TikTok scraper initialized
[PyTok] 🔍 Fetching analytics for video ID: 123
[PyTok] ✅ Success: 5,000 views, 200 likes

📊 Results:
   Views: 5,000
   Likes: 200
   Comments: 50
   Shares: 30
```

### 3. Deploy to Render

Add to your Render **Build Command**:

```bash
pip install -r requirements.txt && python -m playwright install chromium
```

That's it! No environment variables needed.

## How It Works

### Fetch Priority (Automatic):

1. **PyTok** (if installed) - Free browser automation
2. **Web Scraping** (fallback) - BeautifulSoup

### Integration Code:

The dashboard will automatically detect PyTok and use it:

```python
from free_tiktok_scraper import fetch_tiktok_analytics_free

# Fetch analytics for any TikTok URL
result = fetch_tiktok_analytics_free('https://www.tiktok.com/@user/video/123')

print(result)
# {'views': 5000, 'likes': 200, 'comments': 50, 'shares': 30}
```

## Comparison: Free vs Paid

| Feature | PyTok (FREE) | RapidAPI (PAID) | Web Scraping |
|---------|--------------|-----------------|--------------|
| **Cost** | 🆓 FREE | 💰 $10-200/mo | 🆓 FREE |
| **Reliability** | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| **Speed** | Medium | Fast | Slow |
| **Rate Limits** | None | Yes (quota) | None |
| **Maintenance** | Active | Official | Breaks often |
| **Setup** | Easy | Need API key | Already done |

**Recommendation**: Use **PyTok** (FREE) - it's the best free option!

## Benefits Over Web Scraping

### Before (Web Scraping):
```
[FETCH DEBUG] https://vt.tiktok.com/ZS5K7tfH5/... status_code=200
[FETCH DEBUG] found 12 script tags total
⚠️ ZERO VIEWS returned - TikTok HTML changed
```

### After (PyTok):
```
[PyTok] 🔍 Fetching analytics for video ID: 7234567890
[PyTok] ✅ Success: 3,271 views, 85 likes
```

## Troubleshooting

### "PyTok not installed"

```bash
pip install pytok playwright
python -m playwright install chromium
```

### "Playwright browser not found"

```bash
python -m playwright install chromium
```

### Still getting "0 views"?

PyTok uses browser automation, so it's much more reliable than basic scraping. If it fails, check:
- Internet connection
- TikTok might be temporarily blocking your IP
- Try again in a few minutes

### On Render deployment fails?

Make sure your **Build Command** includes:

```bash
pip install -r requirements.txt && python -m playwright install chromium
```

## Performance Notes

- **First request**: ~3-5 seconds (browser startup)
- **Subsequent requests**: ~1-2 seconds
- **Memory usage**: ~150MB (browser overhead)

This is acceptable for dashboard analytics (not real-time, but accurate).

## Alternative Free Options

If PyTok doesn't work, here are other free GitHub scrapers:

1. **TikTok-Content-Scraper** by Q-Bukold
   - More features (downloads videos)
   - Heavier dependencies
   - GitHub: github.com/Q-Bukold/TikTok-Content-Scraper

2. **TikTok Simple Scraper** (PyPI)
   - Lightweight
   - Requires manual token
   - Install: `pip install tiktok-simple-scraper`

## Need Help?

Test the integration:
```bash
python free_tiktok_scraper.py <video_url>
```

Check logs for `[PyTok]` messages to see what's happening.

---

**100% FREE! No API keys needed!** 🎉

Just install PyTok and you're done. The dashboard will automatically use it.
