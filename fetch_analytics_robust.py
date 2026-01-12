#!/usr/bin/env python3
"""
Robust TikTok analytics fetcher with multiple methods
"""

import requests
import json
import re
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

def method1_trollishly(video_url):
    """Method 1: trollishly.com API"""
    try:
        video_id_match = re.search(r'tiktok\.com/@[^/]+/video/(\d+)', video_url)
        if not video_id_match:
            return None
        
        video_id = video_id_match.group(1)
        ua = UserAgent()
        
        csrf_url = "https://www.trollishly.com/tiktok-counter/"
        response = requests.get(csrf_url, headers={'User-Agent': ua.random}, timeout=10)
        if response.status_code != 200:
            return None
        
        soup = BeautifulSoup(response.text, 'html.parser')
        csrf_token = soup.find('meta', {'name': 'csrf-token'})
        if not csrf_token:
            return None
        
        csrf_token = csrf_token.get('content')
        api_url = "https://www.trollishly.com/nocache/search_tiktok_user_counter_val/"
        payload = {'username': video_id}
        headers = {
            'User-Agent': ua.random,
            'Accept': 'application/json',
            'Content-Type': 'application/x-www-form-urlencoded',
            'Referer': 'https://www.trollishly.com/tiktok-counter/',
            'X-CSRF-Token': csrf_token,
            'X-Requested-With': 'XMLHttpRequest'
        }
        
        response = requests.post(api_url, data=payload, headers=headers, cookies=response.cookies, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'error' not in data and 'video_views_count' in data:
                return {
                    'views': int(data.get('video_views_count', 0)) if data.get('video_views_count') else 0,
                    'likes': int(data.get('video_likes_count', 0)) if data.get('video_likes_count') else 0
                }
    except:
        pass
    return None

def method2_direct_scraping(video_url):
    """Method 2: Direct TikTok page scraping"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        response = requests.get(video_url, headers=headers, timeout=15, allow_redirects=True)
        if response.status_code == 200:
            html = response.text
            
            # Look for JSON data in script tags
            # TikTok embeds video data in <script id="__UNIVERSAL_DATA_FOR_REHYDRATION__">
            script_match = re.search(r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>', html, re.DOTALL)
            if script_match:
                try:
                    data = json.loads(script_match.group(1))
                    # Navigate through TikTok's data structure
                    # This structure can vary, so we try multiple paths
                    if 'defaultScope' in data:
                        default = data['defaultScope']
                        if 'webapp.video-detail' in default:
                            video_data = default['webapp.video-detail']
                            if 'itemInfo' in video_data and 'itemStruct' in video_data['itemInfo']:
                                item = video_data['itemInfo']['itemStruct']
                                views = item.get('playCount', 0) or item.get('viewCount', 0) or 0
                                likes = item.get('diggCount', 0) or item.get('likeCount', 0) or 0
                                if views > 0 or likes > 0:
                                    return {'views': int(views), 'likes': int(likes)}
                except:
                    pass
            
            # Alternative: Look for meta tags
            soup = BeautifulSoup(html, 'html.parser')
            meta_desc = soup.find('meta', {'property': 'og:description'})
            if meta_desc:
                desc = meta_desc.get('content', '')
                # Try to extract numbers from description like "1.2M views, 50K likes"
                views_match = re.search(r'([\d.]+[KMB]?)\s*views?', desc, re.I)
                likes_match = re.search(r'([\d.]+[KMB]?)\s*likes?', desc, re.I)
                # This is less reliable but sometimes works
    except:
        pass
    return None

def method3_tiktok_api(video_url):
    """Method 3: TikTok API endpoints (if available)"""
    try:
        video_id_match = re.search(r'tiktok\.com/@[^/]+/video/(\d+)', video_url)
        if not video_id_match:
            return None
        
        video_id = video_id_match.group(1)
        
        # Try TikTok's web API
        api_url = f"https://www.tiktok.com/api/post/item_list/?aid=1988&app_name=tiktok_web&device_platform=web&device_id=&region=US&count=1&itemID={video_id}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': video_url
        }
        
        response = requests.get(api_url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if 'itemList' in data and len(data['itemList']) > 0:
                item = data['itemList'][0]
                stats = item.get('stats', {})
                views = stats.get('playCount', 0) or stats.get('viewCount', 0) or 0
                likes = stats.get('diggCount', 0) or stats.get('likeCount', 0) or 0
                if views > 0 or likes > 0:
                    return {'views': int(views), 'likes': int(likes)}
    except:
        pass
    return None

def fetch_analytics(video_url):
    """Try all methods to fetch analytics"""
    print(f"Trying Method 1: trollishly.com...")
    result = method1_trollishly(video_url)
    if result:
        print(f"  ✓ Success: {result['views']:,} views, {result['likes']} likes")
        return result
    print(f"  ✗ Failed")
    
    print(f"Trying Method 2: Direct scraping...")
    result = method2_direct_scraping(video_url)
    if result:
        print(f"  ✓ Success: {result['views']:,} views, {result['likes']} likes")
        return result
    print(f"  ✗ Failed")
    
    print(f"Trying Method 3: TikTok API...")
    result = method3_tiktok_api(video_url)
    if result:
        print(f"  ✓ Success: {result['views']:,} views, {result['likes']} likes")
        return result
    print(f"  ✗ Failed")
    
    return None

if __name__ == "__main__":
    video_url = "https://www.tiktok.com/@the.clips.origins/video/7593452575140187410"
    print(f"Fetching analytics for: {video_url}\n")
    result = fetch_analytics(video_url)
    
    if result:
        print(f"\n✓ Final result: {result['views']:,} views, {result['likes']} likes")
    else:
        print(f"\n✗ All methods failed")


