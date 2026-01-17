"""
RapidAPI TikTok Integration
Reliable TikTok analytics fetching using RapidAPI instead of web scraping
"""

import requests
import os
import re
from typing import Dict, Optional

# Available RapidAPI TikTok APIs (choose one based on your subscription):
# 1. "TikTok API" by DataFanatic - Most popular, reliable
# 2. "TikTok video downloader" - Good for video data
# 3. "TikTok Data API" - Comprehensive data

class RapidAPITikTok:
    """TikTok analytics fetcher using RapidAPI"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize RapidAPI TikTok client
        
        Args:
            api_key: RapidAPI key (or set RAPIDAPI_KEY env var)
        """
        self.api_key = api_key or os.getenv('RAPIDAPI_KEY')
        
        # Try multiple API hosts in order of preference
        self.api_hosts = [
            'tiktok-api23.p.rapidapi.com',  # TikTok API by DataFanatic
            'tiktok-video-no-watermark2.p.rapidapi.com',  # TikTok Video Downloader
            'tiktok-scraper7.p.rapidapi.com',  # TikTok Scraper
        ]
        
        self.current_host = self.api_hosts[0]
        self.base_headers = {
            'X-RapidAPI-Key': self.api_key,
            'X-RapidAPI-Host': self.current_host
        }
    
    def extract_video_id(self, video_url: str) -> Optional[str]:
        """
        Extract video ID from TikTok URL
        
        Args:
            video_url: TikTok video URL
            
        Returns:
            Video ID or None if not found
        """
        # Pattern: /video/1234567890123456789
        match = re.search(r'/video/(\d+)', video_url)
        if match:
            return match.group(1)
        
        # Pattern: /v/1234567890123456789
        match = re.search(r'/v/(\d+)', video_url)
        if match:
            return match.group(1)
        
        return None
    
    def fetch_video_analytics(self, video_url: str) -> Dict[str, int]:
        """
        Fetch video analytics using RapidAPI
        
        Args:
            video_url: TikTok video URL (any format)
            
        Returns:
            Dict with keys: views, likes, comments, shares
        """
        analytics = {'views': 0, 'likes': 0, 'comments': 0, 'shares': 0}
        
        if not self.api_key:
            print("[RapidAPI] ⚠️ No API key found. Set RAPIDAPI_KEY environment variable.")
            return analytics
        
        video_id = self.extract_video_id(video_url)
        if not video_id:
            print(f"[RapidAPI] ❌ Could not extract video ID from: {video_url[:60]}...")
            return analytics
        
        print(f"[RapidAPI] 🔍 Fetching analytics for video ID: {video_id}")
        
        # Try each API host
        for host in self.api_hosts:
            try:
                self.current_host = host
                self.base_headers['X-RapidAPI-Host'] = host
                
                # API endpoint varies by service
                if 'tiktok-api23' in host:
                    # DataFanatic API
                    url = f"https://{host}/api/video/info"
                    params = {'video_id': video_id}
                    
                elif 'tiktok-video-no-watermark2' in host:
                    # Video Downloader API
                    url = f"https://{host}/"
                    params = {'url': video_url, 'hd': '1'}
                    
                elif 'tiktok-scraper7' in host:
                    # Scraper API
                    url = f"https://{host}/video/info"
                    params = {'video_url': video_url}
                
                else:
                    continue
                
                print(f"[RapidAPI] 🌐 Trying {host}...")
                response = requests.get(url, headers=self.base_headers, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Parse response based on API format
                    analytics = self._parse_response(data, host)
                    
                    if analytics['views'] > 0:
                        print(f"[RapidAPI] ✅ Success with {host}: {analytics['views']} views")
                        return analytics
                    else:
                        print(f"[RapidAPI] ⚠️ {host} returned 0 views")
                        
                else:
                    print(f"[RapidAPI] ⚠️ {host} returned status {response.status_code}")
                    
            except Exception as e:
                print(f"[RapidAPI] ❌ Error with {host}: {e}")
                continue
        
        print(f"[RapidAPI] ⚠️ All API hosts failed for {video_url[:60]}...")
        return analytics
    
    def _parse_response(self, data: dict, host: str) -> Dict[str, int]:
        """
        Parse API response based on host format
        
        Args:
            data: JSON response from API
            host: API host that returned the data
            
        Returns:
            Parsed analytics dict
        """
        analytics = {'views': 0, 'likes': 0, 'comments': 0, 'shares': 0}
        
        try:
            if 'tiktok-api23' in host:
                # DataFanatic format
                stats = data.get('data', {}).get('stats', {})
                analytics['views'] = int(stats.get('playCount', 0))
                analytics['likes'] = int(stats.get('diggCount', 0))
                analytics['comments'] = int(stats.get('commentCount', 0))
                analytics['shares'] = int(stats.get('shareCount', 0))
                
            elif 'tiktok-video-no-watermark2' in host:
                # Video Downloader format
                stats = data.get('data', {})
                analytics['views'] = int(stats.get('play_count', 0))
                analytics['likes'] = int(stats.get('digg_count', 0))
                analytics['comments'] = int(stats.get('comment_count', 0))
                analytics['shares'] = int(stats.get('share_count', 0))
                
            elif 'tiktok-scraper7' in host:
                # Scraper format
                video_data = data.get('data', {}).get('video', {})
                analytics['views'] = int(video_data.get('playCount', 0))
                analytics['likes'] = int(video_data.get('diggCount', 0))
                analytics['comments'] = int(video_data.get('commentCount', 0))
                analytics['shares'] = int(video_data.get('shareCount', 0))
            
            print(f"[RapidAPI] 📊 Parsed: {analytics}")
            
        except Exception as e:
            print(f"[RapidAPI] ❌ Parse error: {e}")
        
        return analytics
    
    def is_available(self) -> bool:
        """Check if RapidAPI is configured and available"""
        return bool(self.api_key)


# Convenience function for easy import
def fetch_tiktok_analytics_rapidapi(video_url: str, api_key: Optional[str] = None) -> Dict[str, int]:
    """
    Quick function to fetch TikTok analytics via RapidAPI
    
    Args:
        video_url: TikTok video URL
        api_key: Optional RapidAPI key (uses env var if not provided)
        
    Returns:
        Dict with views, likes, comments, shares
    """
    client = RapidAPITikTok(api_key)
    return client.fetch_video_analytics(video_url)


if __name__ == '__main__':
    # Test the integration
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python rapidapi_tiktok.py <video_url>")
        print("Example: python rapidapi_tiktok.py https://www.tiktok.com/@user/video/1234567890")
        sys.exit(1)
    
    test_url = sys.argv[1]
    print(f"\n🧪 Testing RapidAPI TikTok Integration")
    print(f"URL: {test_url}\n")
    
    result = fetch_tiktok_analytics_rapidapi(test_url)
    
    print(f"\n📊 Results:")
    print(f"   Views: {result['views']:,}")
    print(f"   Likes: {result['likes']:,}")
    print(f"   Comments: {result['comments']:,}")
    print(f"   Shares: {result['shares']:,}")
