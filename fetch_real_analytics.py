#!/usr/bin/env python3
"""
Standalone script to fetch real-time analytics for all videos
Can be called by dashboard or bot to update progress.json with latest analytics
"""

import json
import requests
import re
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime

PROGRESS_FILE = Path.home() / '.smmfollows_bot' / 'progress.json'

def fetch_tiktok_analytics(video_url):
    """Fetch real-time analytics from TikTok"""
    analytics = {'views': 0, 'likes': 0, 'comments': 0}
    
    # Method 1: Try direct TikTok scraping
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        response = requests.get(video_url, headers=headers, timeout=20, allow_redirects=True)
        if response.status_code == 200:
            html = response.text
            
            # Look for JSON data in script tags
            patterns = [
                r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>',
                r'<script[^>]*>window\.__UNIVERSAL_DATA_FOR_REHYDRATION__\s*=\s*({.*?});</script>',
            ]
            
            for pattern in patterns:
                script_match = re.search(pattern, html, re.DOTALL)
                if script_match:
                    try:
                        json_str = script_match.group(1)
                        if json_str.startswith('{'):
                            data = json.loads(json_str)
                            
                            # Try multiple navigation paths - TikTok uses __DEFAULT_SCOPE__ with underscores
                            paths = [
                                ['__DEFAULT_SCOPE__', 'webapp.video-detail', 'itemInfo', 'itemStruct'],
                                ['defaultScope', 'webapp.video-detail', 'itemInfo', 'itemStruct'],
                                ['defaultScope', 'webapp.video-detail', 'videoData', 'itemInfo', 'itemStruct'],
                                ['webapp.video-detail', 'itemInfo', 'itemStruct'],
                            ]
                            
                            for path in paths:
                                try:
                                    item = data
                                    for key in path:
                                        if isinstance(item, dict) and key in item:
                                            item = item[key]
                                        else:
                                            break
                                    else:
                                        # Get stats from item.stats (TikTok stores stats in a separate object)
                                        stats = item.get('stats', {})
                                        views = int(stats.get('playCount', 0) or stats.get('viewCount', 0) or item.get('playCount', 0) or 0)
                                        likes = int(stats.get('diggCount', 0) or stats.get('likeCount', 0) or item.get('diggCount', 0) or 0)
                                        comments = int(stats.get('commentCount', 0) or stats.get('comment_count', 0) or item.get('commentCount', 0) or 0)
                                        
                                        if views > 0 or likes > 0:
                                            analytics['views'] = views
                                            analytics['likes'] = likes
                                            analytics['comments'] = comments
                                            return analytics
                                except:
                                    continue
                    except:
                        continue
    except:
        pass
    
    # Method 2: Try TikTok API endpoint
    try:
        video_id_match = re.search(r'tiktok\.com/@[^/]+/video/(\d+)', video_url)
        if video_id_match:
            video_id = video_id_match.group(1)
            api_url = f"https://www.tiktok.com/api/post/item_list/?aid=1988&app_name=tiktok_web&device_platform=web&device_id=&region=US&count=1&itemID={video_id}"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': video_url,
                'Accept': 'application/json',
            }
            
            response = requests.get(api_url, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                if 'itemList' in data and len(data['itemList']) > 0:
                    item = data['itemList'][0]
                    stats = item.get('stats', {})
                    views = stats.get('playCount', 0) or stats.get('viewCount', 0) or 0
                    likes = stats.get('diggCount', 0) or stats.get('likeCount', 0) or 0
                    comments = stats.get('commentCount', 0) or 0
                    
                    if views > 0 or likes > 0:
                        analytics['views'] = int(views)
                        analytics['likes'] = int(likes)
                        analytics['comments'] = int(comments)
                        return analytics
    except:
        pass
    
    return analytics

def update_all_videos_analytics():
    """Update analytics for all videos in progress.json"""
    if not PROGRESS_FILE.exists():
        print("No progress file found")
        return
    
    try:
        with open(PROGRESS_FILE, 'r') as f:
            progress = json.load(f)
    except:
        print("Error reading progress file")
        return
    
    updated_count = 0
    for video_url, video_data in progress.items():
        print(f"Fetching analytics for {video_url}...")
        analytics = fetch_tiktok_analytics(video_url)
        
        if analytics['views'] > 0 or analytics['likes'] > 0:
            # Update with real analytics
            progress[video_url]['real_views'] = analytics['views']
            progress[video_url]['real_likes'] = analytics['likes']
            progress[video_url]['real_comments'] = analytics['comments']
            
            # Also update initial values if they're outdated
            current_real = analytics['views']
            current_initial = progress[video_url].get('initial_views', 0)
            
            # If real views are significantly higher than initial, update initial
            if current_real > current_initial * 1.1:  # 10% threshold
                print(f"  Updating initial_views: {current_initial} -> {current_real}")
                progress[video_url]['initial_views'] = current_real
                progress[video_url]['initial_likes'] = analytics['likes']
                progress[video_url]['initial_comments'] = analytics['comments']
            
            updated_count += 1
            print(f"  ✓ {analytics['views']:,} views, {analytics['likes']:,} likes, {analytics['comments']} comments")
        else:
            print(f"  ⚠ Could not fetch analytics")
    
    # Save updated progress
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)
    
    print(f"\n✓ Updated analytics for {updated_count} video(s)")

if __name__ == '__main__':
    update_all_videos_analytics()

