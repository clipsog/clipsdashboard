#!/usr/bin/env python3
"""
Debug script to test analytics fetching for videos showing 0 views
"""
import json
from pathlib import Path
from run_delivery_bot import DeliveryBot

# Load progress
progress_file = Path.home() / '.smmfollows_bot' / 'progress.json'
if not progress_file.exists():
    print("No progress.json found")
    exit(1)

with open(progress_file, 'r') as f:
    progress = json.load(f)

# Find videos with 0 views
zero_view_videos = []
for url, data in progress.items():
    if data.get('real_views', 0) == 0:
        zero_view_videos.append(url)

print(f"Found {len(zero_view_videos)} videos with 0 views\n")

# Test fetching analytics for first 3
test_count = min(3, len(zero_view_videos))
print(f"Testing analytics fetch for {test_count} videos:\n")

for i, url in enumerate(zero_view_videos[:test_count], 1):
    print(f"\n{'='*60}")
    print(f"TEST {i}/{test_count}: {url}")
    print('='*60)
    
    bot = DeliveryBot(url)
    analytics = bot.fetch_all_analytics()
    
    print(f"\nRESULT:")
    print(f"  Views: {analytics['views']}")
    print(f"  Likes: {analytics['likes']}")
    print(f"  Comments: {analytics['comments']}")
    
    if analytics['views'] > 0:
        print(f"  ✓ SUCCESS - Analytics fetched!")
    else:
        print(f"  ✗ FAILED - Still showing 0 views")
        print(f"\n  URL TYPE: {'vt.tiktok.com' if 'vt.tiktok.com' in url else 'direct TikTok URL'}")

print(f"\n{'='*60}")
print("RECOMMENDATION:")
print("If all URLs show 0 views:")
print("  - TikTok may be blocking requests (rate limit/IP block)")
print("  - Try using a VPN or proxy")
print("  - Wait 30-60 minutes and try again")
print("="*60)
