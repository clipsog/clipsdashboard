#!/usr/bin/env python3
"""
HTML Dashboard Server for TikTok Bot
Provides web interface to monitor videos and set target completion times
"""

import json
import sys
import re
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import webbrowser
import threading
import time
import requests
from bs4 import BeautifulSoup
from colorama import Fore, Style, init

init(autoreset=True)

# Use environment variable for PORT (Render provides this), fallback to 8080
import os
PORT = int(os.environ.get('PORT', 8080))

# For Render, use absolute paths in the project directory instead of home directory
if os.environ.get('RENDER'):
    # Running on Render - use project directory
    DATA_DIR = Path(__file__).parent / 'data'
    DATA_DIR.mkdir(exist_ok=True)
    PROGRESS_FILE = DATA_DIR / 'progress.json'
    CAMPAIGNS_FILE = DATA_DIR / 'campaigns.json'
else:
    # Running locally - use home directory
    PROGRESS_FILE = Path.home() / '.smmfollows_bot' / 'progress.json'
    CAMPAIGNS_FILE = Path.home() / '.smmfollows_bot' / 'campaigns.json'

# SMM API Configuration (same as run_delivery_bot.py)
API_KEY = "3327db2d9f02b8c241b200a40fe3d12d"
BASE_URL = "https://smmfollows.com/api/v2"

SERVICES = {
    'views': '1321',
    'likes': '250',
    'comments': '1384',
    'comment_likes': '14718'
}

MINIMUMS = {
    'views': 50,
    'likes': 10,
    'comments': 10,
    'comment_likes': 50
}

class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        if path == '/' or path == '/index.html':
            self.send_dashboard()
        elif path == '/api/progress':
            self.send_progress_json()
        elif path == '/api/update-target':
            self.handle_update_target()
        elif path == '/api/update-comments':
            self.handle_update_comments()
        elif path == '/api/remove-video':
            self.handle_remove_video()
        elif path == '/api/add-video':
            self.handle_add_video()
        elif path == '/api/order-comments':
            self.handle_order_comments()
        elif path == '/api/fetch-comments':
            self.handle_fetch_comments()
        elif path == '/api/order-comment-likes':
            self.handle_order_comment_likes()
        elif path == '/api/campaigns':
            self.handle_get_campaigns()
        elif path == '/api/create-campaign':
            self.handle_create_campaign()
        elif path == '/api/update-campaign':
            self.handle_update_campaign()
        elif path == '/api/end-campaign':
            self.handle_end_campaign()
        elif path == '/api/assign-videos':
            self.handle_assign_videos()
        elif path == '/api/save-next-purchase-time':
            self.handle_save_next_purchase_time()
        elif path == '/api/catch-up':
            self.handle_catch_up()
        elif path == '/api/manual-order':
            self.handle_manual_order()
        elif path == '/health' or path == '/api/health':
            self.handle_health()
        else:
            self.send_error(404)
    
    def do_POST(self):
        """Handle POST requests"""
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        
        if path == '/api/update-target':
            self.handle_update_target()
        elif path == '/api/update-comments':
            self.handle_update_comments()
        elif path == '/api/remove-video':
            self.handle_remove_video()
        elif path == '/api/add-video':
            self.handle_add_video()
        elif path == '/api/order-comments':
            self.handle_order_comments()
        elif path == '/api/fetch-comments':
            self.handle_fetch_comments()
        elif path == '/api/order-comment-likes':
            self.handle_order_comment_likes()
        elif path == '/api/campaigns':
            self.handle_get_campaigns()
        elif path == '/api/create-campaign':
            self.handle_create_campaign()
        elif path == '/api/update-campaign':
            self.handle_update_campaign()
        elif path == '/api/end-campaign':
            self.handle_end_campaign()
        elif path == '/api/assign-videos':
            self.handle_assign_videos()
        elif path == '/api/save-next-purchase-time':
            self.handle_save_next_purchase_time()
        elif path == '/api/catch-up':
            self.handle_catch_up()
        elif path == '/api/manual-order':
            self.handle_manual_order()
        elif path == '/health' or path == '/api/health':
            self.handle_health()
        else:
            self.send_error(404)
    
    def send_dashboard(self):
        """Send the HTML dashboard"""
        html = self.get_dashboard_html()
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        try:
            self.wfile.write(html.encode())
        except BrokenPipeError:
            # Client disconnected, ignore
            pass
    
    def fetch_real_analytics_for_video(self, video_url):
        """Fetch real-time analytics for a single video"""
        analytics = {'views': 0, 'likes': 0, 'comments': 0}
        
        # Method 1: Try direct TikTok scraping with BeautifulSoup
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
                soup = BeautifulSoup(html, 'html.parser')
                
                # Try multiple script tag patterns
                script_patterns = [
                    r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>',
                    r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',
                    r'<script[^>]*>window\.__UNIVERSAL_DATA_FOR_REHYDRATION__\s*=\s*({.*?});</script>',
                ]
                
                # First try regex patterns
                for pattern in script_patterns:
                    script_match = re.search(pattern, html, re.DOTALL)
                    if script_match:
                        try:
                            script_content = script_match.group(1)
                            # Clean up the content - remove any leading/trailing whitespace
                            script_content = script_content.strip()
                            if script_content.startswith('{'):
                                data = json.loads(script_content)
                                
                                # Try multiple data paths - TikTok uses __DEFAULT_SCOPE__ with underscores
                                paths_to_try = [
                                    (['__DEFAULT_SCOPE__', 'webapp.video-detail', 'itemInfo', 'itemStruct']),
                                    (['defaultScope', 'webapp.video-detail', 'itemInfo', 'itemStruct']),
                                    (['props', 'pageProps', 'itemInfo', 'itemStruct']),
                                    (['__DEFAULT_SCOPE__', 'webapp.video-detail', 'videoData', 'itemInfo', 'itemStruct']),
                                    (['defaultScope', 'webapp.video-detail', 'videoData', 'itemInfo', 'itemStruct']),
                                ]
                                
                                for path in paths_to_try:
                                    try:
                                        item = data
                                        for key in path:
                                            if isinstance(item, dict) and key in item:
                                                item = item[key]
                                            else:
                                                break
                                        else:
                                            # Successfully navigated the path
                                            if isinstance(item, dict):
                                                # Get stats from item.stats (TikTok stores stats in a separate object)
                                                stats = item.get('stats', {})
                                                
                                                # Try stats first, then fall back to item directly
                                                views = (stats.get('playCount') or stats.get('viewCount') or 
                                                        item.get('playCount') or item.get('viewCount') or 0)
                                                likes = (stats.get('diggCount') or stats.get('likeCount') or 
                                                       item.get('diggCount') or item.get('likeCount') or 0)
                                                comments = (stats.get('commentCount') or stats.get('comment_count') or 
                                                          item.get('commentCount') or item.get('comment_count') or 0)
                                                
                                                if views or likes or comments:
                                                    analytics['views'] = int(views) if views else 0
                                                    analytics['likes'] = int(likes) if likes else 0
                                                    analytics['comments'] = int(comments) if comments else 0
                                                    
                                                    # Return if we got any data
                                                    if analytics['views'] > 0 or analytics['likes'] > 0:
                                                        print(f"DEBUG: Method 1 success via path {path}: views={analytics['views']}, likes={analytics['likes']}, comments={analytics['comments']}")
                                                        return analytics
                                    except Exception as e:
                                        continue
                        except json.JSONDecodeError as e:
                            continue
                        except Exception as e:
                            continue
                
                # Method 1b: Try BeautifulSoup to find script tags
                script_tags = soup.find_all('script', id=re.compile(r'__UNIVERSAL_DATA|__NEXT_DATA'))
                for script_tag in script_tags:
                    try:
                        script_content = script_tag.string
                        if script_content and script_content.strip().startswith('{'):
                            data = json.loads(script_content)
                            # Try the same paths as above
                            paths_to_try = [
                                (['defaultScope', 'webapp.video-detail', 'itemInfo', 'itemStruct']),
                                (['props', 'pageProps', 'itemInfo', 'itemStruct']),
                            ]
                            for path in paths_to_try:
                                try:
                                    item = data
                                    for key in path:
                                        if isinstance(item, dict) and key in item:
                                            item = item[key]
                                        else:
                                            break
                                    else:
                                        if isinstance(item, dict):
                                            stats = item.get('stats', item)
                                            views = stats.get('playCount') or stats.get('viewCount') or item.get('playCount') or 0
                                            likes = stats.get('diggCount') or stats.get('likeCount') or item.get('diggCount') or 0
                                            comments = stats.get('commentCount') or item.get('commentCount') or 0
                                            if views or likes or comments:
                                                analytics['views'] = int(views) if views else 0
                                                analytics['likes'] = int(likes) if likes else 0
                                                analytics['comments'] = int(comments) if comments else 0
                                                if analytics['views'] > 0 or analytics['likes'] > 0:
                                                    print(f"DEBUG: Method 1b success: {analytics}")
                                                    return analytics
                                except:
                                    continue
                    except:
                        continue
                
                # Method 1c: Try to extract from meta tags or visible text
                # Look for stats in meta description
                meta_desc = soup.find('meta', {'property': 'og:description'})
                if meta_desc:
                    desc = meta_desc.get('content', '')
                    # Try to parse "X views, Y likes" format
                    views_match = re.search(r'([\d,]+)\s*views?', desc, re.I)
                    likes_match = re.search(r'([\d,]+)\s*likes?', desc, re.I)
                    if views_match:
                        views_str = views_match.group(1).replace(',', '')
                        try:
                            analytics['views'] = int(views_str)
                        except:
                            pass
                    if likes_match:
                        likes_str = likes_match.group(1).replace(',', '')
                        try:
                            analytics['likes'] = int(likes_str)
                        except:
                            pass
                    if analytics['views'] > 0 or analytics['likes'] > 0:
                        print(f"DEBUG: Method 1c (meta tags) success: {analytics}")
                        return analytics
                        
        except Exception as e:
            print(f"DEBUG: Error in Method 1: {e}")
            pass
        
        # Method 2: Try TikTok API (skip if Method 1 got data)
        if analytics['views'] == 0 and analytics['likes'] == 0:
            try:
                video_id_match = re.search(r'tiktok\.com/@[^/]+/video/(\d+)', video_url)
                if video_id_match:
                    video_id = video_id_match.group(1)
                    api_url = f"https://www.tiktok.com/api/post/item_list/?aid=1988&app_name=tiktok_web&device_platform=web&device_id=&region=US&count=1&itemID={video_id}"
                    headers = {
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                        'Referer': video_url,
                        'Accept': 'application/json',
                    }
                    response = requests.get(api_url, headers=headers, timeout=10)
                    if response.status_code == 200:
                        try:
                            data = response.json()
                            if 'itemList' in data and len(data['itemList']) > 0:
                                item = data['itemList'][0]
                                stats = item.get('stats', {})
                                
                                views = stats.get('playCount') or stats.get('viewCount') or item.get('playCount') or 0
                                likes = stats.get('diggCount') or stats.get('likeCount') or item.get('diggCount') or 0
                                comments = stats.get('commentCount') or item.get('commentCount') or 0
                                
                                analytics['views'] = int(views) if views else 0
                                analytics['likes'] = int(likes) if likes else 0
                                analytics['comments'] = int(comments) if comments else 0
                                
                                if analytics['views'] > 0 or analytics['likes'] > 0:
                                    print(f"DEBUG: Method 2 success: {analytics}")
                                    return analytics
                        except json.JSONDecodeError:
                            # Response is not JSON - TikTok might be blocking
                            pass
            except Exception as e:
                # Don't print error for Method 2 as it's expected to fail often
                pass
        
        # Method 3: Try alternative API endpoint
        try:
            video_id_match = re.search(r'tiktok\.com/@[^/]+/video/(\d+)', video_url)
            if video_id_match:
                video_id = video_id_match.group(1)
                api_url = f"https://www.tiktok.com/api/video/detail/?itemId={video_id}"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Referer': video_url,
                    'Accept': 'application/json',
                }
                response = requests.get(api_url, headers=headers, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    if 'itemInfo' in data and 'itemStruct' in data['itemInfo']:
                        item = data['itemInfo']['itemStruct']
                        stats = item.get('stats', {})
                        
                        views = stats.get('playCount') or stats.get('viewCount') or item.get('playCount') or 0
                        likes = stats.get('diggCount') or stats.get('likeCount') or item.get('diggCount') or 0
                        comments = stats.get('commentCount') or item.get('commentCount') or 0
                        
                        analytics['views'] = int(views) if views else 0
                        analytics['likes'] = int(likes) if likes else 0
                        analytics['comments'] = int(comments) if comments else 0
                        
                        if analytics['views'] > 0 or analytics['likes'] > 0:
                            print(f"DEBUG: Fetched analytics via Method 3: {analytics}")
                            return analytics
        except Exception as e:
            print(f"DEBUG: Error in Method 3: {e}")
            pass
        
        # Method 4: Fallback to standalone script if all else fails
        if analytics['views'] == 0 and analytics['likes'] == 0:
            try:
                script_path = Path(__file__).parent / 'fetch_real_analytics.py'
                if script_path.exists():
                    result = subprocess.run(
                        [sys.executable, str(script_path)],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    # The script updates progress.json, so reload it
                    progress = self.load_progress()
                    if video_url in progress:
                        video_data = progress[video_url]
                        if 'real_views' in video_data or 'real_likes' in video_data:
                            analytics['views'] = video_data.get('real_views', 0)
                            analytics['likes'] = video_data.get('real_likes', 0)
                            analytics['comments'] = video_data.get('real_comments', 0)
                            if analytics['views'] > 0 or analytics['likes'] > 0:
                                print(f"DEBUG: Method 4 (standalone script) success: {analytics}")
                                return analytics
            except Exception as e:
                print(f"DEBUG: Method 4 failed: {e}")
                pass
        
        print(f"DEBUG: Could not fetch analytics for {video_url}, returning defaults: {analytics}")
        return analytics
    
    def send_progress_json(self):
        """Send progress as JSON with real-time analytics"""
        progress = self.load_progress()
        
        # Always fetch real-time analytics for all videos
        for video_url in list(progress.keys()):
            try:
                analytics = self.fetch_real_analytics_for_video(video_url)
                # Always update real analytics (even if 0, to ensure we're always fetching)
                # Initialize historical data if not exists
                if 'growth_history' not in progress[video_url]:
                    progress[video_url]['growth_history'] = []
                
                # Add current data point to history (always, to track changes)
                current_time = datetime.now().isoformat()
                history_entry = {
                    'timestamp': current_time,
                    'views': analytics['views'],
                    'likes': analytics['likes'],
                    'comments': analytics['comments']
                }
                
                # Only add if data changed (avoid duplicates)
                history = progress[video_url]['growth_history']
                if not history or (history[-1]['views'] != analytics['views'] or 
                                  history[-1]['likes'] != analytics['likes'] or 
                                  history[-1]['comments'] != analytics['comments']):
                    history.append(history_entry)
                    # Keep only last 100 data points to avoid file bloat
                    if len(history) > 100:
                        history.pop(0)
                
                # Always update real analytics (even if 0)
                progress[video_url]['real_views'] = analytics['views']
                progress[video_url]['real_likes'] = analytics['likes']
                progress[video_url]['real_comments'] = analytics['comments']
                print(f"Updated analytics for {video_url}: views={analytics['views']}, likes={analytics['likes']}, comments={analytics['comments']}")
            except Exception as e:
                print(f"Error fetching analytics for {video_url}: {e}")
                import traceback
                traceback.print_exc()
        
        # Save updated progress
        try:
            PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
            with open(PROGRESS_FILE, 'w') as f:
                json.dump(progress, f, indent=2)
        except:
            pass
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        try:
            self.wfile.write(json.dumps(progress).encode())
        except BrokenPipeError:
            # Client disconnected, ignore
            pass
    
    def handle_update_target(self):
        """Handle target date/time update"""
        try:
            # Parse URL to get path and query string
            parsed_path = urllib.parse.urlparse(self.path)
            query_string = parsed_path.query
            
            if self.command == 'GET':
                # Parse query string
                params = urllib.parse.parse_qs(query_string)
            else:
                # Parse POST body
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length > 0:
                    post_data = self.rfile.read(content_length)
                    params = urllib.parse.parse_qs(post_data.decode())
                else:
                    params = {}
            
            video_url = params.get('video_url', [None])[0]
            campaign_id = params.get('campaign_id', [None])[0]
            target_datetime = params.get('target_datetime', [None])[0]
            
            # URL decode the video_url if needed
            if video_url:
                video_url = urllib.parse.unquote(video_url)
            
            # Debug logging
            print(f"DEBUG: video_url={video_url}, target_datetime={target_datetime}")
            
            if not video_url:
                response_data = json.dumps({'success': False, 'error': 'Missing video_url'})
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
                return
            
            if not target_datetime:
                response_data = json.dumps({'success': False, 'error': 'Missing target_datetime'})
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
                return
            
            progress = self.load_progress()
            if video_url not in progress:
                response_data = json.dumps({'success': False, 'error': 'Video not found in progress'})
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
                return
            
            try:
                # Convert datetime-local format (YYYY-MM-DDTHH:MM) to ISO format
                if 'T' in target_datetime and len(target_datetime) == 16:
                    # Add seconds if missing
                    target_datetime = target_datetime + ':00'
                
                target_dt = datetime.fromisoformat(target_datetime)
                progress[video_url]['target_completion_time'] = target_dt.isoformat()
                progress[video_url]['target_completion_datetime'] = target_dt.isoformat()
                self.save_progress(progress)
                
                print(f"SUCCESS: Updated target time for {video_url} to {target_dt.isoformat()}")
                
                response_data = json.dumps({'success': True, 'message': 'Target time updated successfully'})
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
                return
            except Exception as e:
                print(f"ERROR: {str(e)}")
                import traceback
                traceback.print_exc()
                response_data = json.dumps({'success': False, 'error': str(e)})
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
                return
        except Exception as e:
            print(f"EXCEPTION in handle_update_target: {str(e)}")
            import traceback
            traceback.print_exc()
            response_data = json.dumps({'success': False, 'error': str(e)})
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(response_data)))
            self.end_headers()
            self.wfile.write(response_data.encode())
    
    def handle_remove_video(self):
        """Handle video removal"""
        try:
            # Parse URL to get path and query string
            parsed_path = urllib.parse.urlparse(self.path)
            query_string = parsed_path.query
            
            if self.command == 'GET':
                # Parse query string
                params = urllib.parse.parse_qs(query_string)
            else:
                # Parse POST body
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length > 0:
                    post_data = self.rfile.read(content_length)
                    params = urllib.parse.parse_qs(post_data.decode())
                else:
                    params = {}
            
            video_url = params.get('video_url', [None])[0]
            campaign_id = params.get('campaign_id', [None])[0]
            
            # URL decode the video_url if needed
            if video_url:
                video_url = urllib.parse.unquote(video_url)
            if campaign_id:
                campaign_id = urllib.parse.unquote(campaign_id)
            
            # Debug logging
            print(f"DEBUG: Removing video: {video_url}")
            
            if not video_url:
                response_data = json.dumps({'success': False, 'error': 'Missing video_url'})
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
                return
            
            progress = self.load_progress()
            if video_url not in progress:
                response_data = json.dumps({'success': False, 'error': 'Video not found in progress'})
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
                return
            
            # Remove video from progress
            del progress[video_url]
            self.save_progress(progress)
            
            # Also remove video from all campaigns
            campaigns = self.load_campaigns()
            campaigns_changed = False
            for campaign_id, campaign_data in campaigns.items():
                if 'videos' in campaign_data and video_url in campaign_data['videos']:
                    campaign_data['videos'].remove(video_url)
                    campaigns_changed = True
                    print(f"Removed video from campaign {campaign_id}")
            
            if campaigns_changed:
                self.save_campaigns(campaigns)
            
            print(f"SUCCESS: Removed video {video_url} from progress and campaigns")
            
            response_data = json.dumps({'success': True, 'message': 'Video removed successfully'})
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(response_data)))
            self.end_headers()
            self.wfile.write(response_data.encode())
            return
        except Exception as e:
            print(f"EXCEPTION in handle_remove_video: {str(e)}")
            import traceback
            traceback.print_exc()
            response_data = json.dumps({'success': False, 'error': str(e)})
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(response_data)))
            self.end_headers()
            self.wfile.write(response_data.encode())
    
    def handle_add_video(self):
        """Handle adding a new video to the campaign"""
        try:
            # Parse URL to get path and query string
            parsed_path = urllib.parse.urlparse(self.path)
            query_string = parsed_path.query
            
            if self.command == 'GET':
                # Parse query string
                params = urllib.parse.parse_qs(query_string)
            else:
                # Parse POST body
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length > 0:
                    post_data = self.rfile.read(content_length)
                    params = urllib.parse.parse_qs(post_data.decode())
                else:
                    params = {}
            
            video_url = params.get('video_url', [None])[0]
            campaign_id = params.get('campaign_id', [None])[0]
            
            # URL decode the video_url if needed
            if video_url:
                video_url = urllib.parse.unquote(video_url)
            if campaign_id:
                campaign_id = urllib.parse.unquote(campaign_id)
            
            # Validate TikTok URL
            if not video_url:
                response_data = json.dumps({'success': False, 'error': 'Missing video_url'})
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
                return
            
            # Validate it's a TikTok URL
            if 'tiktok.com' not in video_url.lower():
                response_data = json.dumps({'success': False, 'error': 'Invalid URL. Please provide a TikTok video URL.'})
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
                return
            
            # Normalize URL (remove query params, fragments, etc.)
            video_url = video_url.split('?')[0].split('#')[0]
            if not video_url.endswith('/'):
                video_url = video_url.rstrip('/')
            
            # Check if video already exists
            progress = self.load_progress()
            if video_url in progress:
                response_data = json.dumps({'success': False, 'error': 'Video already exists in campaign'})
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
                return
            
            # Fetch initial analytics
            print(f"Fetching analytics for new video: {video_url}")
            analytics = self.fetch_real_analytics_for_video(video_url)
            initial_views = analytics.get('views', 0)
            initial_likes = analytics.get('likes', 0)
            initial_comments = analytics.get('comments', 0)
            
            # Initialize video in progress
            from datetime import datetime
            progress[video_url] = {
                'start_time': datetime.now().isoformat(),
                'target_views': 4000,
                'target_likes': 125,
                'target_comments': 7,
                'target_comment_likes': 15,
                'initial_views': initial_views,
                'initial_likes': initial_likes,
                'initial_comments': initial_comments,
                'real_views': initial_views,
                'real_likes': initial_likes,
                'real_comments': initial_comments,
                'orders_placed': {'views': 0, 'likes': 0, 'comments': 0, 'comment_likes': 0},
                'order_history': [],
                'next_orders': [],
                'total_cost': 0,
                'activity_log': [{
                    'timestamp': datetime.now().isoformat(),
                    'message': 'Video added to campaign',
                    'level': 'info'
                }],
                'growth_history': [{
                    'timestamp': datetime.now().isoformat(),
                    'views': initial_views,
                    'likes': initial_likes,
                    'comments': initial_comments
                }]
            }

            # If campaign_id is provided, assign immediately (and apply campaign goals/speed)
            if campaign_id:
                campaigns = self.load_campaigns()
                if campaign_id in campaigns:
                    campaign = campaigns.get(campaign_id, {})
                    # CRITICAL: Set campaign_id FIRST before adding to campaign
                    # This ensures rebuild logic can restore the video if needed
                    progress[video_url]['campaign_id'] = campaign_id
                    # Add to campaign's video list
                    if 'videos' not in campaign:
                        campaign['videos'] = []
                    if video_url not in campaign['videos']:
                        campaign['videos'].append(video_url)
                        print(f"[ADD VIDEO] Added {video_url[:50]}... to campaign {campaign_id}")

                    # Apply goals
                    progress[video_url]['target_views'] = int(campaign.get('target_views', 4000) or 4000)
                    progress[video_url]['target_likes'] = int(campaign.get('target_likes', 125) or 125)
                    progress[video_url]['target_comments'] = int(campaign.get('target_comments', 7) or 7)
                    progress[video_url]['target_comment_likes'] = int(campaign.get('target_comment_likes', 15) or 15)

                    # Apply speed as target completion datetime from now
                    try:
                        hours = int(campaign.get('target_duration_hours', 0) or 0)
                        minutes = int(campaign.get('target_duration_minutes', 0) or 0)
                        if hours > 0 or minutes > 0:
                            target_dt = datetime.now() + timedelta(hours=hours, minutes=minutes)
                            progress[video_url]['target_completion_time'] = target_dt.isoformat()
                            progress[video_url]['target_completion_datetime'] = target_dt.isoformat()
                    except:
                        pass

                    campaigns[campaign_id] = campaign
                    self.save_campaigns(campaigns)
                else:
                    # Invalid campaign_id passed; ignore assignment
                    pass
            
            self.save_progress(progress)
            
            print(f"SUCCESS: Added video {video_url} to campaign")
            
            response_data = json.dumps({
                'success': True,
                'message': 'Video added successfully',
                'video_url': video_url,
                'analytics': {
                    'views': initial_views,
                    'likes': initial_likes,
                    'comments': initial_comments
                }
            })
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(response_data)))
            self.end_headers()
            self.wfile.write(response_data.encode())
            return
        except Exception as e:
            print(f"EXCEPTION in handle_add_video: {str(e)}")
            import traceback
            traceback.print_exc()
            response_data = json.dumps({'success': False, 'error': str(e)})
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(response_data)))
            self.end_headers()
            self.wfile.write(response_data.encode())
    
    def handle_order_comments(self):
        """Handle ordering comments when milestone is reached"""
        try:
            # Parse URL to get path and query string
            parsed_path = urllib.parse.urlparse(self.path)
            query_string = parsed_path.query
            
            if self.command == 'GET':
                # Parse query string
                params = urllib.parse.parse_qs(query_string)
            else:
                # Parse POST body
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length > 0:
                    post_data = self.rfile.read(content_length)
                    params = urllib.parse.parse_qs(post_data.decode())
                else:
                    params = {}
            
            video_url = params.get('video_url', [None])[0]
            
            # URL decode the video_url if needed
            if video_url:
                video_url = urllib.parse.unquote(video_url)
            
            if not video_url:
                response_data = json.dumps({'success': False, 'error': 'Missing video_url'})
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
                return
            
            progress = self.load_progress()
            if video_url not in progress:
                response_data = json.dumps({'success': False, 'error': 'Video not found in progress'})
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
                return
            
            video_data = progress[video_url]
            orders_placed = video_data.get('orders_placed', {})
            
            # Check if comments already ordered
            if orders_placed.get('comments', 0) > 0:
                response_data = json.dumps({'success': False, 'error': 'Comments already ordered'})
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
                return
            
            # Check if we have saved comments
            saved_comments = video_data.get('saved_comments', [])
            if len(saved_comments) < MINIMUMS['comments']:
                response_data = json.dumps({
                    'success': False, 
                    'error': f'Need {MINIMUMS["comments"]} saved comments. Please add comments in the dashboard first.'
                })
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
                return
            
            # Prepare comments text (one per line)
            comments_text = '\n'.join(saved_comments[:MINIMUMS['comments']])
            
            # Create order via API
            order_data = {
                'key': API_KEY,
                'action': 'add',
                'service': SERVICES['comments'],
                'link': video_url,
                'quantity': MINIMUMS['comments'],
                'comments': comments_text
            }
            
            print(f"Ordering comments for video: {video_url}")
            response = requests.post(BASE_URL, data=order_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                order_id = data.get('order', 0)
                
                if order_id and order_id != 0:
                    # Update progress
                    from datetime import datetime
                    if 'orders_placed' not in video_data:
                        video_data['orders_placed'] = {'views': 0, 'likes': 0, 'comments': 0, 'comment_likes': 0}
                    video_data['orders_placed']['comments'] = MINIMUMS['comments']
                    
                    if 'order_history' not in video_data:
                        video_data['order_history'] = []
                    video_data['order_history'].append({
                        'timestamp': datetime.now().isoformat(),
                        'service': 'comments',
                        'quantity': MINIMUMS['comments'],
                        'order_id': order_id
                    })
                    
                    # Update activity log
                    if 'activity_log' not in video_data:
                        video_data['activity_log'] = []
                    video_data['activity_log'].append({
                        'timestamp': datetime.now().isoformat(),
                        'message': f'Ordered {MINIMUMS["comments"]} comments via dashboard',
                        'level': 'success'
                    })
                    
                    # Update current activity
                    video_data['current_activity'] = {
                        'status': 'ordering',
                        'action': f'Ordering {MINIMUMS["comments"]} comments',
                        'service': 'Comments',
                        'quantity': MINIMUMS['comments'],
                        'last_updated': datetime.now().isoformat()
                    }
                    
                    self.save_progress(progress)
                    
                    print(f"SUCCESS: Ordered comments for {video_url}, order ID: {order_id}")
                    
                    response_data = json.dumps({
                        'success': True,
                        'message': f'Comments ordered successfully! Order ID: {order_id}',
                        'order_id': order_id
                    })
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Content-Length', str(len(response_data)))
                    self.end_headers()
                    self.wfile.write(response_data.encode())
                    return
                else:
                    error = data.get('error', 'Unknown error')
                    print(f"ERROR: Failed to order comments: {error}")
                    response_data = json.dumps({'success': False, 'error': f'API Error: {error}'})
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Content-Length', str(len(response_data)))
                    self.end_headers()
                    self.wfile.write(response_data.encode())
                    return
            else:
                error_text = response.text[:200] if response.text else 'Unknown error'
                print(f"ERROR: HTTP {response.status_code}: {error_text}")
                response_data = json.dumps({'success': False, 'error': f'HTTP {response.status_code}: {error_text}'})
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
                return
        except Exception as e:
            print(f"EXCEPTION in handle_order_comments: {str(e)}")
            import traceback
            traceback.print_exc()
            response_data = json.dumps({'success': False, 'error': str(e)})
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(response_data)))
            self.end_headers()
            self.wfile.write(response_data.encode())
    
    def handle_fetch_comments(self):
        """Fetch comments from TikTok video"""
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            query_string = parsed_path.query
            params = urllib.parse.parse_qs(query_string)
            video_url = params.get('video_url', [None])[0]
            
            if video_url:
                video_url = urllib.parse.unquote(video_url)
            
            if not video_url:
                response_data = json.dumps({'success': False, 'error': 'Missing video_url'})
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
                return
            
            # Fetch comments from TikTok
            comments = self.fetch_comments_from_tiktok(video_url)
            
            if comments is None:
                response_data = json.dumps({
                    'success': False,
                    'error': 'Failed to fetch comments. Please check the video URL.'
                })
                self.send_response(500)
            else:
                response_data = json.dumps({
                    'success': True,
                    'comments': comments
                })
                self.send_response(200)
            
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(response_data)))
            self.end_headers()
            self.wfile.write(response_data.encode())
        except Exception as e:
            print(f"EXCEPTION in handle_fetch_comments: {str(e)}")
            import traceback
            traceback.print_exc()
            response_data = json.dumps({'success': False, 'error': str(e)})
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(response_data)))
            self.end_headers()
            self.wfile.write(response_data.encode())
    
    def fetch_comments_from_tiktok(self, video_url):
        """Fetch comments from TikTok video page"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': 'https://www.tiktok.com/',
            }
            response = requests.get(video_url, headers=headers, timeout=20, allow_redirects=True)
            if response.status_code == 200:
                html = response.text
                
                # Try to find comments in the page data with more comprehensive patterns
                script_patterns = [
                    r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>',
                    r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',
                    r'<script[^>]*>window\.__UNIVERSAL_DATA_FOR_REHYDRATION__\s*=\s*({.*?});</script>',
                ]
                
                comments_list = []
                for pattern in script_patterns:
                    script_match = re.search(pattern, html, re.DOTALL)
                    if script_match:
                        try:
                            script_content = script_match.group(1).strip()
                            if script_content.startswith('{'):
                                data = json.loads(script_content)
                                
                                # Try to find comments in various paths - more comprehensive search
                                def find_comments_recursive(obj, path=[]):
                                    """Recursively search for comment-like structures"""
                                    if isinstance(obj, dict):
                                        # Check if this looks like a comment object
                                        if 'text' in obj or 'commentText' in obj or 'content' in obj:
                                            user = obj.get('user', {}) or obj.get('author', {}) or {}
                                            username = (user.get('uniqueId') or 
                                                       user.get('nickname') or 
                                                       user.get('username') or
                                                       obj.get('uniqueId') or
                                                       obj.get('nickname') or
                                                       'Unknown')
                                            text = (obj.get('text') or 
                                                   obj.get('commentText') or 
                                                   obj.get('content') or
                                                   obj.get('textDisplay') or '')
                                            comment_id = (obj.get('cid') or 
                                                         obj.get('commentId') or 
                                                         obj.get('id') or '')
                                            if text and username:
                                                return [{
                                                    'username': str(username),
                                                    'text': str(text),
                                                    'id': str(comment_id),
                                                    'url': video_url
                                                }]
                                        
                                        # Check for comment list structures
                                        for key, value in obj.items():
                                            if isinstance(key, str) and ('comment' in key.lower() or 'reply' in key.lower()):
                                                if isinstance(value, list):
                                                    found = []
                                                    for item in value:
                                                        result = find_comments_recursive(item, path + [key])
                                                        if result:
                                                            found.extend(result)
                                                    if found:
                                                        return found
                                            
                                            # Recursively search nested objects
                                            result = find_comments_recursive(value, path + [key])
                                            if result:
                                                return result
                                    
                                    elif isinstance(obj, list):
                                        found = []
                                        for item in obj:
                                            result = find_comments_recursive(item, path)
                                            if result:
                                                found.extend(result)
                                        if found:
                                            return found
                                    
                                    return []
                                
                                # Try recursive search first
                                comments_list = find_comments_recursive(data)
                                if comments_list:
                                    # Remove duplicates based on text+username
                                    seen = set()
                                    unique_comments = []
                                    for comment in comments_list:
                                        key = (comment['username'], comment['text'][:50])  # Use first 50 chars for dedup
                                        if key not in seen:
                                            seen.add(key)
                                            unique_comments.append(comment)
                                    return unique_comments[:50]  # Limit to 50 comments
                                
                                # Fallback: Try specific known paths
                                paths_to_try = [
                                    (['__DEFAULT_SCOPE__', 'webapp.video-detail', 'commentList', 'comments']),
                                    (['__DEFAULT_SCOPE__', 'webapp.video-detail', 'commentList']),
                                    (['defaultScope', 'webapp.video-detail', 'commentList', 'comments']),
                                    (['defaultScope', 'webapp.video-detail', 'commentList']),
                                    (['props', 'pageProps', 'commentList', 'comments']),
                                    (['props', 'pageProps', 'commentList']),
                                    (['__DEFAULT_SCOPE__', 'webapp.video-detail', 'itemInfo', 'itemStruct', 'commentList']),
                                    (['__DEFAULT_SCOPE__', 'webapp.video-detail', 'itemInfo', 'itemStruct', 'stats', 'commentCount']),
                                ]
                                
                                for path in paths_to_try:
                                    try:
                                        item = data
                                        for key in path:
                                            if isinstance(item, dict):
                                                item = item.get(key)
                                            elif isinstance(item, list) and isinstance(key, int):
                                                if key < len(item):
                                                    item = item[key]
                                                else:
                                                    item = None
                                            else:
                                                item = None
                                            if item is None:
                                                break
                                        
                                        if isinstance(item, list):
                                            for comment in item:
                                                if isinstance(comment, dict):
                                                    user = comment.get('user', {}) or comment.get('author', {}) or {}
                                                    username = (user.get('uniqueId') or 
                                                               user.get('nickname') or 
                                                               user.get('username') or
                                                               comment.get('uniqueId') or
                                                               comment.get('nickname') or
                                                               'Unknown')
                                                    text = (comment.get('text') or 
                                                           comment.get('commentText') or 
                                                           comment.get('content') or
                                                           comment.get('textDisplay') or '')
                                                    comment_id = (comment.get('cid') or 
                                                                 comment.get('commentId') or 
                                                                 comment.get('id') or '')
                                                    if text:
                                                        comments_list.append({
                                                            'username': str(username),
                                                            'text': str(text),
                                                            'id': str(comment_id),
                                                            'url': video_url
                                                        })
                                            if comments_list:
                                                # Remove duplicates
                                                seen = set()
                                                unique_comments = []
                                                for comment in comments_list:
                                                    key = (comment['username'], comment['text'][:50])
                                                    if key not in seen:
                                                        seen.add(key)
                                                        unique_comments.append(comment)
                                                return unique_comments[:50]
                                    except (KeyError, TypeError, AttributeError):
                                        continue
                                
                                if comments_list:
                                    return comments_list[:50]
                        except (json.JSONDecodeError, KeyError, TypeError) as e:
                            print(f"Error parsing JSON: {e}")
                            continue
                
                # If no comments found, return empty list (not None)
                print("No comments found in page data")
                return []
            return None
        except Exception as e:
            print(f"Error fetching comments: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def handle_order_comment_likes(self):
        """Handle ordering likes for selected comments"""
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            query_string = parsed_path.query
            
            if self.command == 'GET':
                params = urllib.parse.parse_qs(query_string)
            else:
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length > 0:
                    post_data = self.rfile.read(content_length)
                    params = urllib.parse.parse_qs(post_data.decode())
                else:
                    params = {}
            
            video_url = params.get('video_url', [None])[0]
            selected_comments_json = params.get('selected_comments', [None])[0]
            
            if video_url:
                video_url = urllib.parse.unquote(video_url)
            
            if not video_url or not selected_comments_json:
                response_data = json.dumps({'success': False, 'error': 'Missing video_url or selected_comments'})
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
                return
            
            try:
                selected_comments = json.loads(selected_comments_json)
            except:
                response_data = json.dumps({'success': False, 'error': 'Invalid selected_comments format'})
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
                return
            
            if len(selected_comments) < 1:
                response_data = json.dumps({'success': False, 'error': 'Please select at least one comment'})
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
                return
            
            progress = self.load_progress()
            if video_url not in progress:
                response_data = json.dumps({'success': False, 'error': 'Video not found in progress'})
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
                return
            
            # Format comments for API: URL|username (one per line)
            comments_text = '\n'.join([f"{comment['url']}|{comment['username']}" for comment in selected_comments])
            
            # Calculate total quantity needed (minimum 50)
            quantity = max(MINIMUMS['comment_likes'], len(selected_comments) * 10)
            
            # Create order via API
            order_url = f"{BASE_URL}/?key={API_KEY}&action=add"
            order_data = {
                'service': SERVICES['comment_likes'],
                'link': video_url,
                'quantity': quantity,
                'comments': comments_text
            }
            
            response = requests.post(order_url, data=order_data, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('order'):
                    order_id = data['order']
                    
                    # Update progress
                    video_data = progress[video_url]
                    video_data['orders_placed']['comment_likes'] = video_data['orders_placed'].get('comment_likes', 0) + quantity
                    
                    from datetime import datetime
                    video_data['order_history'].append({
                        'timestamp': datetime.now().isoformat(),
                        'service': 'comment_likes',
                        'quantity': quantity,
                        'order_id': order_id
                    })
                    
                    # Save selected comments for reference
                    video_data['selected_comment_likes'] = selected_comments
                    
                    self.save_progress(progress)
                    
                    print(f"SUCCESS: Ordered comment likes for {video_url}, order ID: {order_id}")
                    
                    response_data = json.dumps({
                        'success': True,
                        'message': f'Comment likes ordered successfully! Order ID: {order_id}',
                        'order_id': order_id
                    })
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Content-Length', str(len(response_data)))
                    self.end_headers()
                    self.wfile.write(response_data.encode())
                    return
                else:
                    error = data.get('error', 'Unknown error')
                    print(f"ERROR: Failed to order comment likes: {error}")
                    response_data = json.dumps({'success': False, 'error': f'API Error: {error}'})
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Content-Length', str(len(response_data)))
                    self.end_headers()
                    self.wfile.write(response_data.encode())
                    return
            else:
                error_text = response.text[:200] if response.text else 'Unknown error'
                print(f"ERROR: HTTP {response.status_code}: {error_text}")
                response_data = json.dumps({'success': False, 'error': f'HTTP {response.status_code}: {error_text}'})
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
                return
        except Exception as e:
            print(f"EXCEPTION in handle_order_comment_likes: {str(e)}")
            import traceback
            traceback.print_exc()
            response_data = json.dumps({'success': False, 'error': str(e)})
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(response_data)))
            self.end_headers()
            self.wfile.write(response_data.encode())
    
    def handle_get_campaigns(self):
        """Get all campaigns with financial data"""
        try:
            campaigns = self.load_campaigns()
            progress = self.load_progress()
            campaigns_changed = False
            
            # Rebuild campaign videos from progress.json (ensure persistence after restarts)
            # This ensures videos with campaign_id in progress.json are added to campaigns
            # This is critical for persistence - if server restarts, videos are restored
            # This runs EVERY TIME campaigns are loaded to ensure videos never disappear
            for video_url, video_data in progress.items():
                campaign_id = video_data.get('campaign_id')
                if campaign_id and campaign_id in campaigns:
                    # Initialize videos list if it doesn't exist
                    if 'videos' not in campaigns[campaign_id]:
                        campaigns[campaign_id]['videos'] = []
                    # Add video if not already in list (prevents duplicates)
                    if video_url not in campaigns[campaign_id]['videos']:
                        campaigns[campaign_id]['videos'].append(video_url)
                        campaigns_changed = True
                        print(f"[REBUILD] Added video {video_url[:50]}... to campaign {campaign_id}")
            
            # Ensure all campaigns have a videos list (even if empty)
            for campaign_id, campaign_data in campaigns.items():
                if 'videos' not in campaign_data:
                    campaign_data['videos'] = []
                    campaigns_changed = True
            
            # Calculate financial data for each campaign
            for campaign_id, campaign_data in campaigns.items():
                # Backfill defaults for older campaigns (goals + speed)
                if 'target_views' not in campaign_data:
                    campaign_data['target_views'] = 4000
                    campaigns_changed = True
                if 'target_likes' not in campaign_data:
                    campaign_data['target_likes'] = 125
                    campaigns_changed = True
                if 'target_comments' not in campaign_data:
                    campaign_data['target_comments'] = 7
                    campaigns_changed = True
                if 'target_comment_likes' not in campaign_data:
                    campaign_data['target_comment_likes'] = 15
                    campaigns_changed = True
                if 'target_duration_hours' not in campaign_data:
                    campaign_data['target_duration_hours'] = 24
                    campaigns_changed = True
                if 'target_duration_minutes' not in campaign_data:
                    campaign_data['target_duration_minutes'] = 0
                    campaigns_changed = True

                video_urls = campaign_data.get('videos', [])
                cpm = campaign_data.get('cpm', 0)  # Cost per mille (per 1000 views)
                
                total_spent = 0
                total_views = 0
                total_earned = 0
                
                for video_url in video_urls:
                    if video_url in progress:
                        video_data = progress[video_url]
                        # Calculate spent from order history
                        order_history = video_data.get('order_history', [])
                        for order in order_history:
                            # Use stored cost if available, otherwise calculate
                            if 'cost' in order:
                                total_spent += float(order.get('cost', 0))
                            else:
                                quantity = order.get('quantity', 0)
                                service = order.get('service', '')
                                # Pricing rates (per 1000 units) - approximate rates
                                rates = {'views': 0.0140, 'likes': 0.2100, 'comments': 13.5000, 'comment_likes': 0.2100}
                                rate = rates.get(service, 0)
                                cost = (quantity / 1000.0) * rate
                                total_spent += cost
                        
                        # Calculate earned from views
                        real_views = video_data.get('real_views', 0) or video_data.get('initial_views', 0)
                        total_views += real_views
                
                # Calculate earned (CPM * views / 1000)
                total_earned = (total_views / 1000.0) * cpm if cpm > 0 else 0
                profit = total_earned - total_spent
                roi = (profit / total_spent * 100) if total_spent > 0 else 0
                
                # IMPORTANT: Do NOT remove videos from campaigns here!
                # The rebuild logic above already handles adding videos back.
                # Removing videos here causes them to disappear if there's any timing issue
                # or if progress.json is temporarily incomplete.
                # Videos should only be removed when explicitly deleted via /api/remove-video
                # or when reassigned to a different campaign.
                # 
                # Note: We keep all videos in the campaign's list, even if temporarily not in progress.
                # The rebuild logic will add them back if they have campaign_id set.
                # 
                # DO NOT DO THIS: campaign_data['videos'] = [v for v in video_urls if v in progress]
                # This was causing videos to disappear!
                
                campaign_data['financial'] = {
                    'total_spent': round(total_spent, 2),
                    'total_views': total_views,
                    'total_earned': round(total_earned, 2),
                    'profit': round(profit, 2),
                    'roi': round(roi, 2)
                }

            if campaigns_changed:
                self.save_campaigns(campaigns)
            
            response_data = json.dumps({'success': True, 'campaigns': campaigns})
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(response_data)))
            self.end_headers()
            self.wfile.write(response_data.encode())
        except Exception as e:
            print(f"EXCEPTION in handle_get_campaigns: {str(e)}")
            import traceback
            traceback.print_exc()
            response_data = json.dumps({'success': False, 'error': str(e)})
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(response_data)))
            self.end_headers()
            self.wfile.write(response_data.encode())
    
    def handle_create_campaign(self):
        """Create a new campaign"""
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            query_string = parsed_path.query
            
            if self.command == 'GET':
                params = urllib.parse.parse_qs(query_string)
            else:
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length > 0:
                    post_data = self.rfile.read(content_length)
                    params = urllib.parse.parse_qs(post_data.decode())
                else:
                    params = {}
            
            campaign_name = params.get('campaign_name', [None])[0]
            cpm_str = params.get('cpm', [None])[0]
            target_views_str = params.get('target_views', [None])[0]
            target_likes_str = params.get('target_likes', [None])[0]
            target_comments_str = params.get('target_comments', [None])[0]
            target_comment_likes_str = params.get('target_comment_likes', [None])[0]
            target_duration_hours_str = params.get('target_duration_hours', [None])[0]
            target_duration_minutes_str = params.get('target_duration_minutes', [None])[0]
            
            if not campaign_name:
                response_data = json.dumps({'success': False, 'error': 'Missing campaign_name'})
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
                return
            
            try:
                cpm = float(cpm_str) if cpm_str else 0
            except:
                cpm = 0

            def _parse_int(value, default):
                try:
                    if value is None or value == '':
                        return default
                    return int(float(value))
                except:
                    return default

            # Defaults match per-video defaults used by the tracker
            target_views = _parse_int(target_views_str, 4000)
            target_likes = _parse_int(target_likes_str, 125)
            target_comments = _parse_int(target_comments_str, 7)
            target_comment_likes = _parse_int(target_comment_likes_str, 15)
            target_duration_hours = _parse_int(target_duration_hours_str, 24)
            target_duration_minutes = _parse_int(target_duration_minutes_str, 0)
            
            campaigns = self.load_campaigns()
            campaign_id = f"campaign_{len(campaigns) + 1}_{int(datetime.now().timestamp())}"
            
            campaigns[campaign_id] = {
                'name': campaign_name,
                'cpm': cpm,
                'target_views': target_views,
                'target_likes': target_likes,
                'target_comments': target_comments,
                'target_comment_likes': target_comment_likes,
                'target_duration_hours': target_duration_hours,
                'target_duration_minutes': target_duration_minutes,
                'videos': [],
                'created_at': datetime.now().isoformat()
            }
            
            self.save_campaigns(campaigns)
            
            response_data = json.dumps({
                'success': True,
                'message': 'Campaign created successfully',
                'campaign_id': campaign_id
            })
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(response_data)))
            self.end_headers()
            self.wfile.write(response_data.encode())
        except Exception as e:
            print(f"EXCEPTION in handle_create_campaign: {str(e)}")
            import traceback
            traceback.print_exc()
            response_data = json.dumps({'success': False, 'error': str(e)})
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(response_data)))
            self.end_headers()
            self.wfile.write(response_data.encode())
    
    def handle_update_campaign(self):
        """Update campaign (e.g., change CPM / goals)"""
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            query_string = parsed_path.query
            
            if self.command == 'GET':
                params = urllib.parse.parse_qs(query_string)
            else:
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length > 0:
                    post_data = self.rfile.read(content_length)
                    params = urllib.parse.parse_qs(post_data.decode())
                else:
                    params = {}
            
            campaign_id = params.get('campaign_id', [None])[0]
            cpm_str = params.get('cpm', [None])[0]
            campaign_name = params.get('campaign_name', [None])[0]
            target_views_str = params.get('target_views', [None])[0]
            target_likes_str = params.get('target_likes', [None])[0]
            target_comments_str = params.get('target_comments', [None])[0]
            target_comment_likes_str = params.get('target_comment_likes', [None])[0]
            target_duration_hours_str = params.get('target_duration_hours', [None])[0]
            target_duration_minutes_str = params.get('target_duration_minutes', [None])[0]
            
            if not campaign_id:
                response_data = json.dumps({'success': False, 'error': 'Missing campaign_id'})
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
                return
            
            campaigns = self.load_campaigns()
            if campaign_id not in campaigns:
                response_data = json.dumps({'success': False, 'error': 'Campaign not found'})
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
                return
            
            if cpm_str:
                try:
                    campaigns[campaign_id]['cpm'] = float(cpm_str)
                except:
                    pass
            
            if campaign_name:
                campaigns[campaign_id]['name'] = campaign_name

            def _maybe_set_int(key, value):
                if value is None or value == '':
                    return
                try:
                    campaigns[campaign_id][key] = int(float(value))
                except:
                    return

            _maybe_set_int('target_views', target_views_str)
            _maybe_set_int('target_likes', target_likes_str)
            _maybe_set_int('target_comments', target_comments_str)
            _maybe_set_int('target_comment_likes', target_comment_likes_str)
            _maybe_set_int('target_duration_hours', target_duration_hours_str)
            _maybe_set_int('target_duration_minutes', target_duration_minutes_str)
            
            self.save_campaigns(campaigns)
            
            response_data = json.dumps({'success': True, 'message': 'Campaign updated successfully'})
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(response_data)))
            self.end_headers()
            self.wfile.write(response_data.encode())
        except Exception as e:
            print(f"EXCEPTION in handle_update_campaign: {str(e)}")
            import traceback
            traceback.print_exc()
            response_data = json.dumps({'success': False, 'error': str(e)})
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(response_data)))
            self.end_headers()
            self.wfile.write(response_data.encode())
    
    def handle_save_next_purchase_time(self):
        """Save next purchase time for a video"""
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            query_string = parsed_path.query
            
            if self.command == 'GET':
                params = urllib.parse.parse_qs(query_string)
            else:
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length > 0:
                    post_data = self.rfile.read(content_length)
                    params = urllib.parse.parse_qs(post_data.decode())
                else:
                    params = {}
            
            video_url = params.get('video_url', [None])[0]
            metric = params.get('metric', [None])[0]  # 'views', 'likes', 'comments', 'comment_likes'
            purchase_time = params.get('purchase_time', [None])[0]  # ISO format timestamp
            
            if not video_url or not metric or not purchase_time:
                response_data = json.dumps({'success': False, 'error': 'Missing required parameters'})
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
                return
            
            progress = self.load_progress()
            if video_url not in progress:
                response_data = json.dumps({'success': False, 'error': 'Video not found'})
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
                return
            
            # Save the next purchase time
            key_map = {
                'views': 'next_views_purchase_time',
                'likes': 'next_likes_purchase_time',
                'comments': 'next_comments_purchase_time',
                'comment_likes': 'next_comment_likes_purchase_time'
            }
            
            if metric in key_map:
                progress[video_url][key_map[metric]] = purchase_time
                self.save_progress(progress)
                
                response_data = json.dumps({'success': True, 'message': 'Next purchase time saved'})
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
            else:
                response_data = json.dumps({'success': False, 'error': 'Invalid metric'})
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
        except Exception as e:
            print(f"EXCEPTION in handle_save_next_purchase_time: {str(e)}")
            import traceback
            traceback.print_exc()
            response_data = json.dumps({'success': False, 'error': str(e)})
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(response_data)))
            self.end_headers()
            self.wfile.write(response_data.encode())
    
    def handle_catch_up(self):
        """Handle catch-up order request"""
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            query_string = parsed_path.query
            
            if self.command == 'GET':
                params = urllib.parse.parse_qs(query_string)
            else:
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length > 0:
                    post_data = self.rfile.read(content_length)
                    params = urllib.parse.parse_qs(post_data.decode())
                else:
                    params = {}
            
            video_url = params.get('video_url', [None])[0]
            metric = params.get('metric', [None])[0]  # 'views', 'likes', 'comments', 'comment_likes'
            amount = params.get('amount', [None])[0]  # Amount to order
            
            if not video_url or not metric or not amount:
                response_data = json.dumps({'success': False, 'error': 'Missing required parameters'})
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
                return
            
            try:
                amount = int(amount)
            except:
                response_data = json.dumps({'success': False, 'error': 'Invalid amount'})
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
                return
            
            if amount <= 0:
                response_data = json.dumps({'success': False, 'error': 'Amount must be greater than 0'})
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
                return
            
            # Service IDs and minimums (matching run_delivery_bot.py)
            SERVICES = {
                'views': '1321',
                'likes': '250',
                'comments': '1384',
                'comment_likes': '14718'
            }
            
            MINIMUMS = {
                'views': 50,
                'likes': 10,
                'comments': 10,
                'comment_likes': 50
            }
            
            API_KEY = "3327db2d9f02b8c241b200a40fe3d12d"
            BASE_URL = "https://smmfollows.com/api/v2"
            
            if metric not in SERVICES:
                response_data = json.dumps({'success': False, 'error': 'Invalid metric'})
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
                return
            
            # Ensure amount meets minimum
            minimum = MINIMUMS[metric]
            if amount < minimum:
                amount = minimum
            
            service_id = SERVICES[metric]
            
            # Place order
            import requests
            order_data = {
                'key': API_KEY,
                'action': 'add',
                'service': service_id,
                'link': video_url,
                'quantity': amount
            }
            
            # Add comments if needed
            if metric == 'comments':
                progress = self.load_progress()
                if video_url in progress:
                    comments_text = progress[video_url].get('comments_text', '')
                    if comments_text:
                        order_data['comments'] = comments_text
            
            response = requests.post(BASE_URL, data=order_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                order_id = data.get('order', 0)
                if order_id and order_id != 0:
                    # Update progress
                    progress = self.load_progress()
                    if video_url not in progress:
                        progress[video_url] = {}
                    
                    # Update orders placed
                    if 'orders_placed' not in progress[video_url]:
                        progress[video_url]['orders_placed'] = {'views': 0, 'likes': 0, 'comments': 0, 'comment_likes': 0}
                    
                    orders_placed = progress[video_url]['orders_placed']
                    orders_placed[metric] = orders_placed.get(metric, 0) + amount
                    
                    # Update order history
                    if 'order_history' not in progress[video_url]:
                        progress[video_url]['order_history'] = []
                    
                    progress[video_url]['order_history'].append({
                        'service': metric,
                        'quantity': amount,
                        'order_id': str(order_id),
                        'timestamp': datetime.now().isoformat(),
                        'type': 'catch_up'
                    })
                    
                    # Update total cost
                    rates = {
                        'views': 0.0140,
                        'likes': 0.2100,
                        'comments': 13.5000,
                        'comment_likes': 0.2100
                    }
                    cost = (amount / 1000.0) * rates[metric]
                    progress[video_url]['total_cost'] = progress[video_url].get('total_cost', 0) + cost
                    
                    self.save_progress(progress)
                    
                    response_data = json.dumps({
                        'success': True,
                        'message': f'Catch-up order placed: {amount} {metric}',
                        'order_id': order_id,
                        'amount': amount
                    })
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Content-Length', str(len(response_data)))
                    self.end_headers()
                    self.wfile.write(response_data.encode())
                else:
                    error_msg = data.get('error', 'Unknown error')
                    response_data = json.dumps({'success': False, 'error': f'Order failed: {error_msg}'})
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Content-Length', str(len(response_data)))
                    self.end_headers()
                    self.wfile.write(response_data.encode())
            else:
                response_data = json.dumps({'success': False, 'error': f'API request failed: {response.status_code}'})
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
        except Exception as e:
            print(f"EXCEPTION in handle_catch_up: {str(e)}")
            import traceback
            traceback.print_exc()
            response_data = json.dumps({'success': False, 'error': str(e)})
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(response_data)))
            self.end_headers()
            self.wfile.write(response_data.encode())
    
    def handle_manual_order(self):
        """Handle manual order request"""
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            query_string = parsed_path.query
            
            if self.command == 'GET':
                params = urllib.parse.parse_qs(query_string)
            else:
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length > 0:
                    post_data = self.rfile.read(content_length)
                    params = urllib.parse.parse_qs(post_data.decode())
                else:
                    params = {}
            
            video_url = params.get('video_url', [None])[0]
            metric = params.get('metric', [None])[0]  # 'views', 'likes', 'comments', 'comment_likes'
            amount = params.get('amount', [None])[0]  # Amount to order
            
            if not video_url or not metric or not amount:
                response_data = json.dumps({'success': False, 'error': 'Missing required parameters'})
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
                return
            
            try:
                amount = int(amount)
            except:
                response_data = json.dumps({'success': False, 'error': 'Invalid amount'})
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
                return
            
            if amount <= 0:
                response_data = json.dumps({'success': False, 'error': 'Amount must be greater than 0'})
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
                return
            
            # Service IDs and minimums (matching run_delivery_bot.py)
            SERVICES = {
                'views': '1321',
                'likes': '250',
                'comments': '1384',
                'comment_likes': '14718'
            }
            
            MINIMUMS = {
                'views': 50,
                'likes': 10,
                'comments': 10,
                'comment_likes': 50
            }
            
            API_KEY = "3327db2d9f02b8c241b200a40fe3d12d"
            BASE_URL = "https://smmfollows.com/api/v2"
            
            if metric not in SERVICES:
                response_data = json.dumps({'success': False, 'error': 'Invalid metric'})
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
                return
            
            # Ensure amount meets minimum
            minimum = MINIMUMS[metric]
            if amount < minimum:
                response_data = json.dumps({'success': False, 'error': f'Amount must be at least {minimum} for {metric}'})
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
                return
            
            service_id = SERVICES[metric]
            
            # Place order
            import requests
            order_data = {
                'key': API_KEY,
                'action': 'add',
                'service': service_id,
                'link': video_url,
                'quantity': amount
            }
            
            # Add comments if needed
            if metric == 'comments':
                progress = self.load_progress()
                if video_url in progress:
                    comments_text = progress[video_url].get('comments_text', '')
                    if comments_text:
                        order_data['comments'] = comments_text
            
            response = requests.post(BASE_URL, data=order_data, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                order_id = data.get('order', 0)
                if order_id and order_id != 0:
                    # Update progress
                    progress = self.load_progress()
                    if video_url not in progress:
                        progress[video_url] = {}
                    
                    # Update orders placed
                    if 'orders_placed' not in progress[video_url]:
                        progress[video_url]['orders_placed'] = {'views': 0, 'likes': 0, 'comments': 0, 'comment_likes': 0}
                    
                    orders_placed = progress[video_url]['orders_placed']
                    orders_placed[metric] = orders_placed.get(metric, 0) + amount
                    
                    # Update order history
                    if 'order_history' not in progress[video_url]:
                        progress[video_url]['order_history'] = []
                    
                    progress[video_url]['order_history'].append({
                        'service': metric,
                        'quantity': amount,
                        'order_id': str(order_id),
                        'timestamp': datetime.now().isoformat(),
                        'type': 'manual'
                    })
                    
                    # Update total cost
                    rates = {
                        'views': 0.0140,
                        'likes': 0.2100,
                        'comments': 13.5000,
                        'comment_likes': 0.2100
                    }
                    cost = (amount / 1000.0) * rates[metric]
                    progress[video_url]['total_cost'] = progress[video_url].get('total_cost', 0) + cost
                    
                    self.save_progress(progress)
                    
                    response_data = json.dumps({
                        'success': True,
                        'message': f'Manual order placed: {amount} {metric}',
                        'order_id': order_id,
                        'amount': amount
                    })
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Content-Length', str(len(response_data)))
                    self.end_headers()
                    self.wfile.write(response_data.encode())
                else:
                    error_msg = data.get('error', 'Unknown error')
                    response_data = json.dumps({'success': False, 'error': f'Order failed: {error_msg}'})
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Content-Length', str(len(response_data)))
                    self.end_headers()
                    self.wfile.write(response_data.encode())
            else:
                response_data = json.dumps({'success': False, 'error': f'API request failed: {response.status_code}'})
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
        except Exception as e:
            print(f"EXCEPTION in handle_manual_order: {str(e)}")
            import traceback
            traceback.print_exc()
            response_data = json.dumps({'success': False, 'error': str(e)})
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(response_data)))
            self.end_headers()
            self.wfile.write(response_data.encode())
    
    def handle_health(self):
        """Health check endpoint for Render"""
        response_data = json.dumps({
            'status': 'ok',
            'timestamp': datetime.now().isoformat(),
            'service': 'dashboard'
        })
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Content-Length', str(len(response_data)))
        self.end_headers()
        self.wfile.write(response_data.encode())
    
    def handle_end_campaign(self):
        """End a campaign (mark as ended but keep for stats)"""
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            query_string = parsed_path.query
            
            if self.command == 'GET':
                params = urllib.parse.parse_qs(query_string)
            else:
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length > 0:
                    post_data = self.rfile.read(content_length)
                    params = urllib.parse.parse_qs(post_data.decode())
                else:
                    params = {}
            
            campaign_id = params.get('campaign_id', [None])[0]
            
            if not campaign_id:
                response_data = json.dumps({'success': False, 'error': 'Missing campaign_id'})
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
                return
            
            campaigns = self.load_campaigns()
            
            if campaign_id not in campaigns:
                response_data = json.dumps({'success': False, 'error': 'Campaign not found'})
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
                return
            
            # Mark campaign as ended
            campaigns[campaign_id]['status'] = 'ended'
            campaigns[campaign_id]['ended_at'] = datetime.now().isoformat()
            
            self.save_campaigns(campaigns)
            
            response_data = json.dumps({
                'success': True,
                'message': 'Campaign ended successfully'
            })
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(response_data)))
            self.end_headers()
            self.wfile.write(response_data.encode())
            
        except Exception as e:
            print(f"EXCEPTION in handle_end_campaign: {str(e)}")
            import traceback
            traceback.print_exc()
            response_data = json.dumps({'success': False, 'error': str(e)})
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(response_data)))
            self.end_headers()
            self.wfile.write(response_data.encode())
    
    def handle_assign_videos(self):
        """Assign videos to a campaign"""
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            query_string = parsed_path.query
            
            if self.command == 'GET':
                params = urllib.parse.parse_qs(query_string)
            else:
                content_length = int(self.headers.get('Content-Length', 0))
                if content_length > 0:
                    post_data = self.rfile.read(content_length)
                    params = urllib.parse.parse_qs(post_data.decode())
                else:
                    params = {}
            
            campaign_id = params.get('campaign_id', [None])[0]
            video_urls_json = params.get('video_urls', [None])[0]
            
            if not campaign_id or not video_urls_json:
                response_data = json.dumps({'success': False, 'error': 'Missing campaign_id or video_urls'})
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
                return
            
            try:
                video_urls = json.loads(video_urls_json)
            except:
                response_data = json.dumps({'success': False, 'error': 'Invalid video_urls format'})
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
                return
            
            campaigns = self.load_campaigns()
            progress = self.load_progress()
            
            if campaign_id not in campaigns:
                response_data = json.dumps({'success': False, 'error': 'Campaign not found'})
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
                return
            
            # Remove videos from other campaigns first
            for cid, camp_data in campaigns.items():
                if cid != campaign_id:
                    camp_data['videos'] = [v for v in camp_data.get('videos', []) if v not in video_urls]
            
            # Add videos to selected campaign
            # Ensure all videos in video_urls that exist in progress are added
            existing_videos = set(campaigns[campaign_id].get('videos', []))
            # Add all videos that exist in progress to the campaign
            for video_url in video_urls:
                if video_url in progress:
                    existing_videos.add(video_url)
            campaigns[campaign_id]['videos'] = list(existing_videos)
            
            # Update video campaign assignments in progress (and apply campaign goals)
            campaign = campaigns.get(campaign_id, {})
            for video_url in video_urls:
                if video_url in progress:
                    # Always set campaign_id to ensure persistence
                    progress[video_url]['campaign_id'] = campaign_id

                    # Apply campaign goals to each post (per-video)
                    if 'target_views' in campaign:
                        progress[video_url]['target_views'] = campaign.get('target_views', 4000)
                    if 'target_likes' in campaign:
                        progress[video_url]['target_likes'] = campaign.get('target_likes', 125)
                    if 'target_comments' in campaign:
                        progress[video_url]['target_comments'] = campaign.get('target_comments', 7)
                    if 'target_comment_likes' in campaign:
                        progress[video_url]['target_comment_likes'] = campaign.get('target_comment_likes', 15)

                    # Apply campaign "speed" as a target completion datetime from now
                    try:
                        hours = int(campaign.get('target_duration_hours', 0) or 0)
                        minutes = int(campaign.get('target_duration_minutes', 0) or 0)
                        if hours > 0 or minutes > 0:
                            target_dt = datetime.now() + timedelta(hours=hours, minutes=minutes)
                            progress[video_url]['target_completion_time'] = target_dt.isoformat()
                            progress[video_url]['target_completion_datetime'] = target_dt.isoformat()
                    except:
                        pass
            
            self.save_campaigns(campaigns)
            self.save_progress(progress)
            
            response_data = json.dumps({
                'success': True,
                'message': f'Assigned {len(new_videos)} video(s) to campaign'
            })
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(response_data)))
            self.end_headers()
            self.wfile.write(response_data.encode())
        except Exception as e:
            print(f"EXCEPTION in handle_assign_videos: {str(e)}")
            import traceback
            traceback.print_exc()
            response_data = json.dumps({'success': False, 'error': str(e)})
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(response_data)))
            self.end_headers()
            self.wfile.write(response_data.encode())
    
    def load_progress(self):
        """Load progress from file"""
        if not PROGRESS_FILE.exists():
            return {}
        try:
            with open(PROGRESS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def save_progress(self, progress):
        """Save progress to file"""
        PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(PROGRESS_FILE, 'w') as f:
            json.dump(progress, f, indent=2)
    
    def load_campaigns(self):
        """Load campaigns from file"""
        if not CAMPAIGNS_FILE.exists():
            return {}
        try:
            with open(CAMPAIGNS_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def save_campaigns(self, campaigns):
        """Save campaigns to file"""
        CAMPAIGNS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(CAMPAIGNS_FILE, 'w') as f:
            json.dump(campaigns, f, indent=2)
    
    def get_dashboard_html(self):
        """Generate HTML dashboard"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <title>Campaign Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: #0f0f0f;
            min-height: 100vh;
            padding: 20px;
            color: #e0e0e0;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .header {
            background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
            border-radius: 16px;
            padding: 40px;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.4);
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        .header h1 {
            color: #ffffff;
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 700;
        }
        
        .header p {
            color: #b0b0b0;
            font-size: 1.1em;
        }
        
        .video-card {
            background: linear-gradient(135deg, #1a1a1a 0%, #252525 100%);
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 25px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.1);
            transition: all 0.3s ease;
        }
        
        .video-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 12px 40px rgba(0,0,0,0.5);
            border-color: rgba(102, 126, 234, 0.3);
        }
        
        .video-embed-container {
            width: 100%;
            max-width: 400px;
            margin: 20px 0;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        
        .video-embed-container iframe {
            width: 100%;
            height: 700px;
            border: none;
        }
        
        .video-link-container {
            margin-top: 10px;
        }
        
        .video-link-container a {
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
        }
        
        .video-link-container a:hover {
            text-decoration: underline;
        }
        
        .video-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        
        .video-title {
            font-size: 1.5em;
            color: #ffffff;
            font-weight: 600;
        }
        
        .video-id {
            color: #888;
            font-size: 0.9em;
            margin-top: 5px;
        }
        
        .remove-video-btn {
            padding: 8px 16px;
            background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 0.9em;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            margin-left: 10px;
            box-shadow: 0 4px 12px rgba(220, 38, 38, 0.3);
        }
        
        .remove-video-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(220, 38, 38, 0.4);
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        }
        
        .remove-video-btn:active {
            transform: translateY(0);
        }
        
        .status-badge {
            padding: 8px 16px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.9em;
        }
        
        .status-complete { background: #10b981; color: white; }
        .status-good { background: #3b82f6; color: white; }
        .status-moderate { background: #f59e0b; color: white; }
        .status-early { background: #ef4444; color: white; }
        
        .target-time-section {
            background: linear-gradient(135deg, #1e1e1e 0%, #2a2a2a 100%);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 25px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        .target-time-section h3 {
            color: #ffffff;
            margin-bottom: 15px;
            font-size: 1.2em;
            font-weight: 600;
        }
        
        .target-input-group {
            display: flex;
            gap: 10px;
            align-items: center;
            flex-wrap: wrap;
        }
        
        .target-input-group input[type="datetime-local"] {
            padding: 12px 16px;
            border: 2px solid rgba(255,255,255,0.2);
            border-radius: 8px;
            font-size: 1em;
            flex: 1;
            min-width: 200px;
            background: #1a1a1a;
            color: #e0e0e0;
            transition: all 0.2s;
        }
        
        .target-input-group input[type="datetime-local"]:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
        }
        
        .target-input-group button {
            padding: 12px 24px;
            background: linear-gradient(135deg, #667eea 0%, #5568d3 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 1em;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.2s;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }
        
        .target-input-group button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
        }
        
        .target-input-group button:active {
            transform: translateY(0);
        }
        
        .target-display {
            margin-top: 15px;
            padding: 15px;
            background: rgba(0,0,0,0.3);
            border-radius: 8px;
            color: #e0e0e0;
            border-left: 4px solid #667eea;
        }
        
        .target-display strong {
            color: #667eea;
        }
        
        .metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .metric {
            background: linear-gradient(135deg, #1e1e1e 0%, #2a2a2a 100%);
            border-radius: 12px;
            padding: 25px;
            border: 1px solid rgba(255,255,255,0.1);
            transition: all 0.2s;
        }
        
        .metric:hover {
            border-color: rgba(102, 126, 234, 0.3);
            transform: translateY(-2px);
        }
        
        .metric-label {
            color: #b0b0b0;
            font-size: 0.9em;
            margin-bottom: 10px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .metric-value {
            font-size: 2.2em;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 5px;
        }
        
        .metric-target {
            color: #888;
            font-size: 0.9em;
        }
        
        .progress-bar-container {
            background: rgba(0,0,0,0.3);
            border-radius: 10px;
            height: 24px;
            overflow: hidden;
            margin-top: 12px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        .progress-bar {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
            transition: width 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-size: 0.75em;
            font-weight: 600;
        }
        
        .growth-chart-section {
            margin-top: 30px;
            padding: 25px;
            background: linear-gradient(135deg, #1e1e1e 0%, #2a2a2a 100%);
            border-radius: 12px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        .growth-chart-section h3 {
            margin: 0 0 20px 0;
            color: #ffffff;
            font-size: 1.2em;
            font-weight: 600;
        }
        
        .chart-container {
            position: relative;
            height: 400px;
            margin: 20px 0;
        }
        
        .chart-legend {
            display: flex;
            gap: 20px;
            justify-content: center;
            margin-top: 15px;
            flex-wrap: wrap;
        }
        
        .chart-legend-item {
            display: flex;
            align-items: center;
            gap: 8px;
            color: #e0e0e0;
            font-size: 0.9em;
        }
        
        .chart-legend-color {
            width: 20px;
            height: 20px;
            border-radius: 4px;
        }
        
        .milestones-section {
            margin-top: 30px;
            padding: 25px;
            background: linear-gradient(135deg, #1e1e1e 0%, #2a2a2a 100%);
            border-radius: 12px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        .milestones-section h3 {
            margin: 0 0 20px 0;
            color: #ffffff;
            font-size: 1.2em;
            font-weight: 600;
        }
        
        .milestone-card {
            background: rgba(0,0,0,0.3);
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 15px;
            border-left: 4px solid #555;
            transition: all 0.2s;
        }
        
        .milestone-card:hover {
            background: rgba(0,0,0,0.4);
        }
        
        .milestone-card.milestone-pending {
            border-left-color: #ffc107;
        }
        
        .milestone-card.milestone-ready {
            border-left-color: #ff9800;
        }
        
        .milestone-card.milestone-completed {
            border-left-color: #4caf50;
        }
        
        .milestone-header {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 10px;
        }
        
        .milestone-icon {
            font-size: 20px;
        }
        
        .milestone-title {
            font-weight: bold;
            flex: 1;
        }
        
        .milestone-status {
            font-size: 12px;
            padding: 6px 12px;
            border-radius: 6px;
            background: rgba(255,255,255,0.1);
            color: #e0e0e0;
            font-weight: 600;
        }
        
        .milestone-details {
            margin-left: 30px;
        }
        
        .milestone-info {
            margin-bottom: 10px;
            line-height: 1.6;
            color: #d0d0d0;
        }
        
        .milestone-info strong {
            color: #ffffff;
        }
        
        .milestone-comments {
            margin-top: 10px;
        }
        
        .milestone-comments strong {
            color: #ffffff;
        }
        
        .comments-list {
            margin: 10px 0 0 20px;
            padding: 0;
        }
        
        .comments-list li {
            margin: 5px 0;
            padding: 8px;
            background: rgba(0,0,0,0.3);
            border-radius: 6px;
            color: #d0d0d0;
            border-left: 2px solid rgba(102, 126, 234, 0.5);
        }
        
        .milestone-username {
            margin-top: 10px;
            padding: 12px;
            background: rgba(102, 126, 234, 0.2);
            border-radius: 6px;
            color: #e0e0e0;
            border-left: 3px solid #667eea;
        }
        
        .milestone-username strong {
            color: #ffffff;
        }
        
        .comments-editor-section {
            margin-top: 30px;
            padding: 25px;
            background: linear-gradient(135deg, #1e1e1e 0%, #2a2a2a 100%);
            border-radius: 12px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        .comments-editor-section h3 {
            margin: 0 0 15px 0;
            color: #ffffff;
            font-size: 1.2em;
            font-weight: 600;
        }
        
        .comments-editor-disabled {
            opacity: 0.6;
            pointer-events: none;
        }
        
        .comments-editor-disabled::after {
            content: ' (Comments already ordered - cannot edit)';
            color: #ff9800;
            font-weight: bold;
            margin-left: 10px;
        }
        
        .comments-textarea {
            width: 100%;
            min-height: 200px;
            padding: 15px;
            border: 2px solid rgba(255,255,255,0.2);
            border-radius: 10px;
            font-family: inherit;
            font-size: 14px;
            line-height: 1.6;
            resize: vertical;
            box-sizing: border-box;
            background: #1a1a1a;
            color: #e0e0e0;
            transition: all 0.2s;
        }
        
        .comments-textarea:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
        }
        
        .comments-textarea:disabled {
            background: #151515;
            cursor: not-allowed;
            opacity: 0.5;
        }
        
        .comments-help {
            margin-top: 10px;
            font-size: 12px;
            color: #888;
        }
        
        .comments-save-btn {
            margin-top: 15px;
            padding: 12px 24px;
            background: linear-gradient(135deg, #667eea 0%, #5568d3 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }
        
        .comments-save-btn:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
        }
        
        .comments-save-btn:disabled {
            background: #444;
            cursor: not-allowed;
            box-shadow: none;
        }
        
        .add-campaign-btn {
            padding: 10px 20px;
            background: #2a2a2a;
            color: #fff;
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .add-campaign-btn:hover {
            background: #333;
        }
        
        .comments-save-status {
            margin-top: 12px;
            padding: 12px;
            border-radius: 8px;
            font-size: 13px;
            display: none;
        }
        
        .comments-save-status.success {
            background: rgba(16, 185, 129, 0.2);
            color: #10b981;
            display: block;
            border-left: 4px solid #10b981;
        }
        
        .comments-save-status.error {
            background: rgba(239, 68, 68, 0.2);
            color: #ef4444;
            display: block;
            border-left: 4px solid #ef4444;
        }
        
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        
        .info-item {
            background: linear-gradient(135deg, #1e1e1e 0%, #2a2a2a 100%);
            border-radius: 10px;
            padding: 18px;
            border: 1px solid rgba(255,255,255,0.1);
            transition: all 0.2s;
        }
        
        .info-item:hover {
            border-color: rgba(102, 126, 234, 0.3);
            transform: translateY(-2px);
        }
        
        .info-label {
            color: #b0b0b0;
            font-size: 0.85em;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .info-value {
            color: #ffffff;
            font-size: 1.3em;
            font-weight: 600;
        }
        
        .refresh-btn {
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: #2a2a2a;
            color: #b0b0b0;
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 8px;
            width: 48px;
            height: 48px;
            cursor: pointer;
            box-shadow: 0 2px 8px rgba(0,0,0,0.3);
            transition: all 0.2s;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 0;
        }
        
        .refresh-btn:hover {
            background: #333;
            color: #fff;
            border-color: rgba(255,255,255,0.2);
            transform: rotate(90deg);
        }
        
        .refresh-btn svg {
            width: 18px;
            height: 18px;
        }
        
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #b0b0b0;
        }
        
        .empty-state h2 {
            font-size: 2em;
            margin-bottom: 10px;
            color: #ffffff;
        }
        
        .loading {
            text-align: center;
            padding: 40px;
            color: #b0b0b0;
            font-size: 1.2em;
        }
        
        /* Homepage Grid Styles */
        .videos-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
            gap: 25px;
            margin-top: 20px;
        }
        
        .video-card-mini {
            background: linear-gradient(135deg, #1a1a1a 0%, #252525 100%);
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            border: 1px solid rgba(255,255,255,0.1);
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .video-card-mini:hover {
            transform: translateY(-4px);
            box-shadow: 0 12px 40px rgba(0,0,0,0.5);
            border-color: rgba(102, 126, 234, 0.5);
        }
        
        .video-card-mini-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .video-card-mini-title {
            font-size: 1.2em;
            color: #ffffff;
            font-weight: 600;
        }
        
        .video-card-mini-stats {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin-top: 15px;
        }
        
        .mini-stat {
            text-align: center;
        }
        
        .mini-stat-label {
            color: #b0b0b0;
            font-size: 0.75em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 5px;
        }
        
        .mini-stat-value {
            color: #ffffff;
            font-size: 1.3em;
            font-weight: 700;
        }
        
        .mini-stat-progress {
            margin-top: 8px;
            height: 4px;
            background: rgba(0,0,0,0.3);
            border-radius: 2px;
            overflow: hidden;
        }
        
        .mini-stat-progress-bar {
            height: 100%;
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            border-radius: 2px;
        }
        
        .back-button {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 10px 20px;
            background: linear-gradient(135deg, #1e1e1e 0%, #2a2a2a 100%);
            color: #ffffff;
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            margin-bottom: 20px;
            transition: all 0.2s;
            cursor: pointer;
        }
        
        .back-button:hover {
            border-color: rgba(102, 126, 234, 0.5);
            transform: translateX(-4px);
        }
        
        .show-analytics-btn:hover {
            transform: scale(1.02);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        
        .show-analytics-btn:active {
            transform: scale(0.98);
        }
        
        .video-embed-mini {
            width: 100%;
            height: 400px;
            border-radius: 12px;
            overflow: hidden;
            margin-bottom: 15px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        .video-embed-mini iframe {
            width: 100%;
            height: 100%;
            border: none;
        }
        
        /* Summary Statistics */
        .summary-stats {
            display: flex;
            gap: 24px;
            margin-bottom: 20px;
            padding: 12px 16px;
            background: #1a1a1a;
            border-radius: 8px;
            border: 1px solid rgba(255,255,255,0.08);
            flex-wrap: wrap;
            align-items: center;
        }
        
        .summary-stat-card {
            display: flex;
            align-items: baseline;
            gap: 8px;
            flex: 0 1 auto;
        }
        
        .summary-stat-label {
            color: #888;
            font-size: 0.75em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-weight: 500;
        }
        
        .summary-stat-value {
            color: #ffffff;
            font-size: 1.1em;
            font-weight: 600;
        }
        
        .summary-stat-change {
            display: none;
        }
        
        /* Search and Filter Bar */
        .controls-bar {
            background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 25px;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            align-items: center;
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        .search-box {
            flex: 1;
            min-width: 200px;
            padding: 12px 16px;
            border: 2px solid rgba(255,255,255,0.2);
            border-radius: 8px;
            background: #1a1a1a;
            color: #e0e0e0;
            font-size: 14px;
            transition: all 0.2s;
        }
        
        .search-box:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
        }
        
        .filter-select {
            padding: 12px 16px;
            border: 2px solid rgba(255,255,255,0.2);
            border-radius: 8px;
            background: #1a1a1a;
            color: #e0e0e0;
            font-size: 14px;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .filter-select:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
        }
        
        .export-btn {
            padding: 12px 24px;
            background: #2a2a2a;
            color: #fff;
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .export-btn:hover {
            background: #333;
        }
        
        .clear-filters-btn {
            padding: 12px 20px;
            background: #2a2a2a;
            color: #fff;
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .clear-filters-btn:hover {
            background: #333;
        }
        
        .add-video-btn {
            padding: 10px 20px;
            background: #2a2a2a;
            color: #fff;
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .add-video-btn:hover {
            background: #333;
        }
        
        /* Mobile Responsive Styles */
        @media (max-width: 768px) {
            body {
                padding: 10px;
            }
            
            .header {
                padding: 20px;
            }
            
            .header h1 {
                font-size: 1.8em;
            }
            
            .video-card {
                padding: 15px;
            }
            
            .video-header {
                flex-direction: column;
                align-items: flex-start;
                gap: 10px;
            }
            
            .video-title {
                font-size: 1.2em;
            }
            
            .video-embed-container {
                max-width: 100%;
            }
            
            .video-embed-container iframe {
                height: 500px;
            }
            
            .metrics {
                grid-template-columns: 1fr;
            }
            
            .metric {
                margin-bottom: 15px;
            }
            
            .target-input-group {
                flex-direction: column;
                gap: 10px;
            }
            
            .target-input-group input,
            .target-input-group button {
                width: 100%;
            }
            
            .campaign-card-clickable {
                padding: 12px !important;
            }
            
            .container {
                padding: 0 10px;
            }
            
            button {
                padding: 8px 16px;
                font-size: 14px;
            }
            
            .summary-stats {
                flex-direction: column;
                align-items: flex-start;
                gap: 8px;
            }
            
            .summary-stat-card {
                width: 100%;
            }
        }
        
        }
        
        @media (max-width: 480px) {
            .header h1 {
                font-size: 1.5em;
            }
            
            .video-embed-container iframe {
                height: 400px;
            }
            
            button {
                padding: 6px 12px;
                font-size: 12px;
            }
        }
            .controls-bar {
                flex-direction: column;
            }
            
            .search-box, .filter-select, .export-btn, .clear-filters-btn {
                width: 100%;
            }
            
            .summary-stats {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Campaign Dashboard</h1>
            <p>Monitor your videos and set target completion times</p>
        </div>
        
        <div id="summary-stats-container"></div>
        
        <div class="controls-bar">
            <input type="text" id="search-box" class="search-box" placeholder="🔍 Search videos by username or URL..." oninput="filterVideos()">
            <select id="status-filter" class="filter-select" onchange="filterVideos()">
                <option value="all">All Status</option>
                <option value="complete">✅ Complete</option>
                <option value="good">🟢 Good Progress</option>
                <option value="moderate">🟡 Moderate</option>
                <option value="early">🔴 Early Stage</option>
            </select>
            <select id="sort-by" class="filter-select" onchange="filterVideos()">
                <option value="progress-desc">Progress: High to Low</option>
                <option value="progress-asc">Progress: Low to High</option>
                <option value="views-desc">Views: High to Low</option>
                <option value="views-asc">Views: Low to High</option>
                <option value="recent">Most Recent</option>
                <option value="oldest">Oldest</option>
            </select>
            <button class="export-btn" onclick="exportData()">Export Data</button>
            <button class="add-video-btn" onclick="showAddVideoModal()">Add Video</button>
            <button class="clear-filters-btn" onclick="clearFilters()">Clear Filters</button>
        </div>
        
        <!-- Campaign Management Bar -->
        <div id="campaign-bar" style="display: none; background: #2a2a2a; padding: 15px; border-radius: 8px; margin-bottom: 20px; border: 1px solid rgba(255,255,255,0.1);">
            <div style="display: flex; align-items: center; gap: 15px; flex-wrap: wrap;">
                <div style="flex: 1; min-width: 200px;">
                    <div style="color: #b0b0b0; font-size: 0.85em; margin-bottom: 5px;">Selected: <span id="selected-count">0</span> video(s)</div>
                    <div style="display: flex; gap: 10px;">
                        <select id="campaign-selector" style="flex: 1; padding: 8px 12px; background: #1a1a1a; border: 1px solid rgba(255,255,255,0.2); border-radius: 6px; color: #fff; font-size: 14px;">
                            <option value="">Select Campaign...</option>
                        </select>
                        <button id="new-campaign-btn-bar" style="background: #10b981; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 14px;">➕ New Campaign</button>
                        <button onclick="assignToCampaign()" id="assign-campaign-btn" style="background: #667eea; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 14px;" disabled>Assign</button>
                        <button onclick="clearSelection()" style="background: #444; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 14px;">Clear</button>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Campaigns Summary -->
        <div id="campaigns-summary" style="margin-bottom: 25px;"></div>
        
        <!-- Add Video Modal -->
        <div id="add-video-modal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 10000; align-items: center; justify-content: center;">
            <div style="background: #1a1a1a; border-radius: 16px; padding: 30px; max-width: 500px; width: 90%; border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 8px 32px rgba(0,0,0,0.5);">
                <h2 style="margin: 0 0 20px 0; color: #fff; font-size: 24px;">➕ Add Video to Campaign</h2>
                <p style="color: #b0b0b0; margin-bottom: 20px; font-size: 14px;">Enter a TikTok video URL to start tracking it in your campaign.</p>
                <div style="margin-bottom: 12px;">
                    <label style="display: block; color: #fff; margin-bottom: 8px; font-weight: 600;">Assign to Campaign (optional)</label>
                    <div style="display: flex; gap: 10px;">
                        <select id="add-video-campaign-selector" style="flex: 1; padding: 10px 12px; background: #252525; border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; color: #fff; font-size: 14px;">
                            <option value="">No campaign</option>
                        </select>
                        <button id="add-video-new-campaign-btn" style="background: #10b981; color: white; border: none; padding: 10px 14px; border-radius: 8px; cursor: pointer; font-weight: 700; font-size: 13px;">➕ New</button>
                    </div>
                    <div style="color: #888; font-size: 12px; margin-top: 6px;">If you choose a campaign, we’ll apply that campaign’s goals & speed to this post.</div>
                </div>
                <textarea id="new-video-url" placeholder="Enter one or more TikTok URLs (one per line)&#10;https://www.tiktok.com/@username/video/1234567890&#10;https://www.tiktok.com/@username/video/0987654321" style="width: 100%; padding: 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.2); background: #252525; color: #fff; font-size: 14px; margin-bottom: 12px; box-sizing: border-box; min-height: 120px; resize: vertical; font-family: monospace;"></textarea>
                <div style="color: #888; font-size: 12px; margin-bottom: 12px;">💡 Tip: Paste multiple URLs, one per line</div>
                <div id="add-video-progress" style="display: none; margin-bottom: 15px;">
                    <div style="color: #667eea; font-size: 13px; margin-bottom: 8px;">Adding videos...</div>
                    <div style="background: #252525; border-radius: 8px; padding: 12px; max-height: 200px; overflow-y: auto;">
                        <div id="add-video-progress-list" style="color: #b0b0b0; font-size: 12px; font-family: monospace;"></div>
                    </div>
                    <div style="background: #252525; height: 4px; border-radius: 2px; margin-top: 8px; overflow: hidden;">
                        <div id="add-video-progress-bar" style="background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); height: 100%; width: 0%; transition: width 0.3s;"></div>
                    </div>
                </div>
                <div id="add-video-error" style="color: #ff4444; font-size: 13px; margin-bottom: 15px; display: none;"></div>
                <div id="add-video-success" style="color: #10b981; font-size: 13px; margin-bottom: 15px; display: none;"></div>
                <div style="display: flex; gap: 10px; justify-content: flex-end;">
                    <button onclick="hideAddVideoModal()" id="add-video-cancel-btn" style="padding: 10px 20px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.2); background: transparent; color: #fff; cursor: pointer; font-size: 14px;">Cancel</button>
                    <button onclick="addVideo()" id="add-video-submit-btn" style="padding: 10px 20px; border-radius: 8px; border: none; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; cursor: pointer; font-weight: 600; font-size: 14px;">Add Video(s)</button>
                </div>
            </div>
        </div>

        <!-- Create Campaign Modal -->
        <div id="create-campaign-modal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 10002; align-items: center; justify-content: center;">
            <div style="background: #1a1a1a; border-radius: 16px; padding: 30px; max-width: 500px; width: 90%; border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 8px 32px rgba(0,0,0,0.5);">
                <h2 style="margin: 0 0 20px 0; color: #fff; font-size: 24px;">📊 Create New Campaign</h2>
                <p style="color: #b0b0b0; margin-bottom: 20px; font-size: 14px;">Create a new campaign to group videos and track financial performance.</p>
                <div style="margin-bottom: 20px;">
                    <label style="display: block; color: #fff; margin-bottom: 8px; font-weight: 600;">Campaign Name</label>
                    <input type="text" id="new-campaign-name" placeholder="e.g., Q1 2026 Campaign" style="width: 100%; padding: 12px; background: #2a2a2a; border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; color: #fff; font-size: 14px; box-sizing: border-box;">
                </div>
                <div style="margin-bottom: 20px;">
                    <label style="display: block; color: #fff; margin-bottom: 8px; font-weight: 600;">CPM (Cost Per Mille)</label>
                    <p style="color: #b0b0b0; font-size: 12px; margin-bottom: 8px;">How much you get paid per 1,000 views (e.g., 2.50 = $2.50 per 1000 views)</p>
                    <input type="number" id="new-campaign-cpm" placeholder="0.00" step="0.01" min="0" style="width: 100%; padding: 12px; background: #2a2a2a; border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; color: #fff; font-size: 14px; box-sizing: border-box;">
                </div>
                <div style="margin-bottom: 20px;">
                    <label style="display: block; color: #fff; margin-bottom: 8px; font-weight: 600;">Goals per Post</label>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                        <div>
                            <div style="color: #b0b0b0; font-size: 12px; margin-bottom: 6px;">Views goal</div>
                            <input type="number" id="new-campaign-target-views" placeholder="4000" min="0" step="1" style="width: 100%; padding: 10px; background: #2a2a2a; border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; color: #fff; font-size: 14px; box-sizing: border-box;">
                        </div>
                        <div>
                            <div style="color: #b0b0b0; font-size: 12px; margin-bottom: 6px;">Likes goal</div>
                            <input type="number" id="new-campaign-target-likes" placeholder="125" min="0" step="1" style="width: 100%; padding: 10px; background: #2a2a2a; border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; color: #fff; font-size: 14px; box-sizing: border-box;">
                        </div>
                        <div>
                            <div style="color: #b0b0b0; font-size: 12px; margin-bottom: 6px;">Comments goal</div>
                            <input type="number" id="new-campaign-target-comments" placeholder="7" min="0" step="1" style="width: 100%; padding: 10px; background: #2a2a2a; border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; color: #fff; font-size: 14px; box-sizing: border-box;">
                        </div>
                        <div>
                            <div style="color: #b0b0b0; font-size: 12px; margin-bottom: 6px;">Comment likes goal</div>
                            <input type="number" id="new-campaign-target-comment-likes" placeholder="15" min="0" step="1" style="width: 100%; padding: 10px; background: #2a2a2a; border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; color: #fff; font-size: 14px; box-sizing: border-box;">
                        </div>
                    </div>
                </div>
                <div style="margin-bottom: 20px;">
                    <label style="display: block; color: #fff; margin-bottom: 8px; font-weight: 600;">Growth Speed</label>
                    <p style="color: #b0b0b0; font-size: 12px; margin-bottom: 8px;">How long each post should take to reach the goal (used to set the target completion time).</p>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                        <div>
                            <div style="color: #b0b0b0; font-size: 12px; margin-bottom: 6px;">Hours</div>
                            <input type="number" id="new-campaign-duration-hours" placeholder="24" min="0" step="1" style="width: 100%; padding: 10px; background: #2a2a2a; border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; color: #fff; font-size: 14px; box-sizing: border-box;">
                        </div>
                        <div>
                            <div style="color: #b0b0b0; font-size: 12px; margin-bottom: 6px;">Minutes</div>
                            <input type="number" id="new-campaign-duration-minutes" placeholder="0" min="0" step="1" style="width: 100%; padding: 10px; background: #2a2a2a; border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; color: #fff; font-size: 14px; box-sizing: border-box;">
                        </div>
                    </div>
                </div>
                <div id="create-campaign-error" style="color: #ef4444; margin-bottom: 15px; font-size: 14px; display: none;"></div>
                <div style="display: flex; gap: 10px; justify-content: flex-end;">
                    <button onclick="hideCreateCampaignModal()" style="background: #444; color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer;">Cancel</button>
                    <button onclick="createCampaign()" style="background: #10b981; color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; font-weight: 600;">Create Campaign</button>
                </div>
            </div>
        </div>
        
        <!-- Edit Campaign Modal -->
        <div id="edit-campaign-modal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 10003; align-items: center; justify-content: center;">
            <div style="background: #1a1a1a; border-radius: 16px; padding: 30px; max-width: 500px; width: 90%; border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 8px 32px rgba(0,0,0,0.5);">
                <h2 style="margin: 0 0 20px 0; color: #fff; font-size: 24px;">Edit Campaign</h2>
                <p style="color: #b0b0b0; margin-bottom: 20px; font-size: 14px;">Update campaign CPM and goals.</p>
                <div style="margin-bottom: 20px;">
                    <label style="display: block; color: #fff; margin-bottom: 8px; font-weight: 600;">Campaign Name</label>
                    <input type="text" id="edit-campaign-name" placeholder="e.g., Q1 2026 Campaign" style="width: 100%; padding: 12px; background: #2a2a2a; border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; color: #fff; font-size: 14px; box-sizing: border-box;">
                </div>
                <div style="margin-bottom: 20px;">
                    <label style="display: block; color: #fff; margin-bottom: 8px; font-weight: 600;">CPM (Cost Per Mille)</label>
                    <p style="color: #b0b0b0; font-size: 12px; margin-bottom: 8px;">How much you get paid per 1,000 views (e.g., 2.50 = $2.50 per 1000 views)</p>
                    <input type="number" id="edit-campaign-cpm" placeholder="0.00" step="0.01" min="0" style="width: 100%; padding: 12px; background: #2a2a2a; border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; color: #fff; font-size: 14px; box-sizing: border-box;">
                </div>
                <div style="margin-bottom: 20px;">
                    <label style="display: block; color: #fff; margin-bottom: 8px; font-weight: 600;">Goals per Post</label>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                        <div>
                            <div style="color: #b0b0b0; font-size: 12px; margin-bottom: 6px;">Views goal</div>
                            <input type="number" id="edit-campaign-target-views" placeholder="4000" min="0" step="1" style="width: 100%; padding: 10px; background: #2a2a2a; border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; color: #fff; font-size: 14px; box-sizing: border-box;">
                        </div>
                        <div>
                            <div style="color: #b0b0b0; font-size: 12px; margin-bottom: 6px;">Likes goal</div>
                            <input type="number" id="edit-campaign-target-likes" placeholder="125" min="0" step="1" style="width: 100%; padding: 10px; background: #2a2a2a; border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; color: #fff; font-size: 14px; box-sizing: border-box;">
                        </div>
                        <div>
                            <div style="color: #b0b0b0; font-size: 12px; margin-bottom: 6px;">Comments goal</div>
                            <input type="number" id="edit-campaign-target-comments" placeholder="7" min="0" step="1" style="width: 100%; padding: 10px; background: #2a2a2a; border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; color: #fff; font-size: 14px; box-sizing: border-box;">
                        </div>
                        <div>
                            <div style="color: #b0b0b0; font-size: 12px; margin-bottom: 6px;">Comment likes goal</div>
                            <input type="number" id="edit-campaign-target-comment-likes" placeholder="15" min="0" step="1" style="width: 100%; padding: 10px; background: #2a2a2a; border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; color: #fff; font-size: 14px; box-sizing: border-box;">
                        </div>
                    </div>
                </div>
                <div style="margin-bottom: 20px;">
                    <label style="display: block; color: #fff; margin-bottom: 8px; font-weight: 600;">Growth Speed</label>
                    <p style="color: #b0b0b0; font-size: 12px; margin-bottom: 8px;">How long each post should take to reach the goal (used to set the target completion time).</p>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                        <div>
                            <div style="color: #b0b0b0; font-size: 12px; margin-bottom: 6px;">Hours</div>
                            <input type="number" id="edit-campaign-duration-hours" placeholder="24" min="0" step="1" style="width: 100%; padding: 10px; background: #2a2a2a; border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; color: #fff; font-size: 14px; box-sizing: border-box;">
                        </div>
                        <div>
                            <div style="color: #b0b0b0; font-size: 12px; margin-bottom: 6px;">Minutes</div>
                            <input type="number" id="edit-campaign-duration-minutes" placeholder="0" min="0" step="1" style="width: 100%; padding: 10px; background: #2a2a2a; border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; color: #fff; font-size: 14px; box-sizing: border-box;">
                        </div>
                    </div>
                </div>
                <div id="edit-campaign-error" style="color: #ef4444; margin-bottom: 15px; font-size: 14px; display: none;"></div>
                <div style="display: flex; gap: 10px; justify-content: flex-end;">
                    <button onclick="hideEditCampaignModal()" style="background: #444; color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer;">Cancel</button>
                    <button onclick="updateCampaign()" style="background: #10b981; color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; font-weight: 600;">Update Campaign</button>
                </div>
            </div>
        </div>
        
        <div id="dashboard-content">
            <div class="loading">Loading...</div>
        </div>
    </div>
    
    <button class="refresh-btn" onclick="loadDashboard(true)" title="Refresh">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8"></path>
            <path d="M21 3v5h-5"></path>
            <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16"></path>
            <path d="M3 21v-5h5"></path>
        </svg>
    </button>
    
    <script>
        function formatNumber(num) {
            return new Intl.NumberFormat().format(Math.floor(num));
        }
        
        function formatPercentage(current, target) {
            if (target === 0) return '0%';
            return ((current / target) * 100).toFixed(1) + '%';
        }
        
        function getStatusClass(progress) {
            if (progress >= 100) return 'status-complete';
            if (progress >= 75) return 'status-good';
            if (progress >= 50) return 'status-moderate';
            return 'status-early';
        }
        
        function getStatusText(progress) {
            if (progress >= 100) return '✅ Complete';
            if (progress >= 75) return '🟢 Good Progress';
            if (progress >= 50) return '🟡 Moderate';
            return '🔴 Early Stage';
        }
        
        function formatTimeElapsed(startTime) {
            if (!startTime) return 'N/A';
            try {
                const start = new Date(startTime);
                const now = new Date();
                const diff = now - start;
                const hours = Math.floor(diff / (1000 * 60 * 60));
                const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
                if (hours > 0) return `${hours}h ${minutes}m`;
                return `${minutes}m`;
            } catch {
                return 'N/A';
            }
        }
        
        function calculateTimeRemaining(targetTime) {
            if (!targetTime) return null;
            try {
                const target = new Date(targetTime);
                const now = new Date();
                const diff = target - now;
                if (diff < 0) return 'Past due';
                const hours = Math.floor(diff / (1000 * 60 * 60));
                const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
                if (hours > 0) return `${hours}h ${minutes}m remaining`;
                return `${minutes}m remaining`;
            } catch {
                return null;
            }
        }
        
        function extractVideoInfo(url) {
            try {
                const parts = url.split('/');
                let username = null;
                let videoId = null;
                for (let i = 0; i < parts.length; i++) {
                    if (parts[i].startsWith('@')) {
                        username = parts[i].substring(1);
                    }
                    if (parts[i] === 'video' && i + 1 < parts.length) {
                        videoId = parts[i + 1].split('?')[0];
                    }
                }
                return { username, videoId };
            } catch {
                return { username: null, videoId: null };
            }
        }
        
        function getTikTokEmbedUrl(videoUrl) {
            // Convert TikTok URL to embed format
            // Format: https://www.tiktok.com/embed/v2/{videoId}
            const { videoId } = extractVideoInfo(videoUrl);
            if (videoId) {
                return `https://www.tiktok.com/embed/v2/${videoId}`;
            }
            return null;
        }
        
        async function removeVideo(videoUrl) {
            // Escape template literal special characters for display
            function escapeForTemplate(str) {
                if (!str) return '';
                return String(str).replace(/\\\\/g, '\\\\\\\\').replace(/`/g, '\\\\`').replace(/\\$/g, '\\\\$');
            }
            if (!confirm(`Are you sure you want to remove this video from the process?\\n\\nVideo: ${escapeForTemplate(videoUrl)}\\n\\nThis will stop tracking but won't cancel existing orders.`)) {
                return;
            }
            
            try {
                const params = new URLSearchParams({
                    video_url: videoUrl
                });
                
                const response = await fetch(`/api/remove-video?${params.toString()}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: params.toString()
                });
                
                const data = await response.json();
                
                if (data.success) {
                    alert('✅ Video removed successfully!');
                    // Navigate to home if we're on detail page
                    const route = getCurrentRoute();
                    if (route.type === 'detail') {
                        navigateToHome();
                    } else {
                        loadDashboard(false);
                    }
                } else {
                    alert('❌ Error: ' + (data.error || 'Failed to remove video'));
                }
            } catch (error) {
                console.error('Error:', error);
                alert('❌ Error removing video: ' + error.message);
            }
        }
        
        async function saveNextPurchaseTime(videoUrl, metric, purchaseTime) {
            try {
                const params = new URLSearchParams({
                    video_url: videoUrl,
                    metric: metric,
                    purchase_time: purchaseTime
                });
                
                const response = await fetch('/api/save-next-purchase-time?' + params.toString(), {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: params.toString()
                });
                
                const data = await response.json();
                if (!data.success) {
                    console.warn('Failed to save next purchase time:', data.error);
                }
            } catch (error) {
                console.warn('Error saving next purchase time:', error);
                // Don't show error to user, this is background operation
            }
        }
        
        async function catchUp(videoUrl, metric, amount, buttonElement) {
            if (!confirm(`Place catch-up order for ${amount.toLocaleString()} ${metric}?`)) {
                return;
            }
            
            const button = buttonElement || event.target;
            const originalText = button.textContent;
            button.disabled = true;
            button.textContent = 'Placing order...';
            
            try {
                const params = new URLSearchParams({
                    video_url: videoUrl,
                    metric: metric,
                    amount: amount.toString()
                });
                
                const response = await fetch('/api/catch-up?' + params.toString(), {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: params.toString()
                });
                
                const data = await response.json();
                if (data.success) {
                    alert(`✓ Catch-up order placed! Order ID: ${data.order_id}\nAmount: ${data.amount.toLocaleString()} ${metric}`);
                    // Reload dashboard to show updated stats
                    await loadDashboard(true);
                } else {
                    alert('❌ Error: ' + (data.error || 'Failed to place catch-up order'));
                    button.disabled = false;
                    button.textContent = originalText;
                }
            } catch (error) {
                console.error('Error:', error);
                alert('❌ Error placing catch-up order: ' + error.message);
                button.disabled = false;
                button.textContent = originalText;
            }
        }
        
        async function manualOrder(videoUrl, metric, minimum, buttonElement) {
            const button = buttonElement || event.target;
            const amountStr = prompt(`Enter amount of ${metric} to order (minimum: ${minimum}):`, minimum);
            
            if (!amountStr) {
                return; // User cancelled
            }
            
            const amount = parseInt(amountStr);
            if (isNaN(amount) || amount < minimum) {
                alert(`Amount must be at least ${minimum} for ${metric}`);
                return;
            }
            
            if (!confirm(`Place manual order for ${amount.toLocaleString()} ${metric}?`)) {
                return;
            }
            
            const originalText = button.textContent;
            button.disabled = true;
            button.textContent = 'Placing order...';
            
            try {
                const params = new URLSearchParams({
                    video_url: videoUrl,
                    metric: metric,
                    amount: amount
                });
                
                const response = await fetch('/api/manual-order?' + params.toString(), {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: params.toString()
                });
                
                const data = await response.json();
                if (data.success) {
                    alert(`✓ Manual order placed! Order ID: ${data.order_id}\nAmount: ${data.amount.toLocaleString()} ${metric}`);
                    // Reload dashboard to show updated stats
                    await loadDashboard(true);
                } else {
                    alert('❌ Error: ' + (data.error || 'Failed to place manual order'));
                    button.disabled = false;
                    button.textContent = originalText;
                }
            } catch (error) {
                console.error('Error:', error);
                alert('❌ Error placing manual order: ' + error.message);
                button.disabled = false;
                button.textContent = originalText;
            }
        }
        
        async function saveComments(videoUrl, textareaId) {
            const textarea = document.getElementById(textareaId);
            const comments = textarea.value.trim();
            const statusDiv = document.getElementById('comments-status-' + textareaId.replace('comments-', ''));
            
            if (!comments) {
                statusDiv.className = 'comments-save-status error';
                statusDiv.textContent = 'Please enter at least 10 comments';
                return;
            }
            
            const commentsList = comments.split('\\n').filter(c => c.trim());
            if (commentsList.length < 10) {
                statusDiv.className = 'comments-save-status error';
                statusDiv.textContent = `Need at least 10 comments. You provided ${commentsList.length}.`;
                return;
            }
            
            try {
                const params = new URLSearchParams({
                    video_url: videoUrl,
                    comments: comments
                });
                
                const response = await fetch(`/api/update-comments?${params.toString()}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: params.toString()
                });
                
                const data = await response.json();
                
                if (data.success) {
                    statusDiv.className = 'comments-save-status success';
                    statusDiv.textContent = `✅ ${data.message || 'Comments saved successfully!'}`;
                    // Refresh dashboard after a short delay
                    setTimeout(() => {
                        loadDashboard(false);
                        statusDiv.className = 'comments-save-status';
                    }, 2000);
                } else {
                    statusDiv.className = 'comments-save-status error';
                    statusDiv.textContent = `❌ Error: ${data.error || 'Failed to save comments'}`;
                }
            } catch (error) {
                console.error('Error:', error);
                statusDiv.className = 'comments-save-status error';
                statusDiv.textContent = `❌ Error: ${error.message}`;
            }
        }
        
        async function orderComments(videoUrl, button) {
            if (!confirm('Are you sure you want to order comments now? This will place an order for 10 comments using your saved comments.')) {
                return;
            }
            
            const originalText = button.textContent;
            button.disabled = true;
            button.textContent = 'Ordering...';
            
            try {
                const params = new URLSearchParams({
                    video_url: videoUrl
                });
                
                const response = await fetch('/api/order-comments?' + params.toString(), {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: params.toString()
                });
                
                const data = await response.json();
                
                if (data.success) {
                    alert('✅ ' + data.message);
                    // Refresh dashboard to show updated status
                    await loadDashboard(false);
                } else {
                    alert('❌ Error: ' + (data.error || 'Failed to order comments'));
                    button.disabled = false;
                    button.textContent = originalText;
                }
            } catch (error) {
                console.error('Error:', error);
                alert('❌ Error ordering comments: ' + error.message);
                button.disabled = false;
                button.textContent = originalText;
            }
        }
        
        async function showCommentSelectionModal(videoUrl) {
            let modal = document.getElementById('comment-selection-modal');
            if (!modal) {
                // Create modal if it doesn't exist
                const modalHtml = `
                    <div id="comment-selection-modal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 10001; align-items: center; justify-content: center; overflow-y: auto;">
                        <div style="background: #1a1a1a; border-radius: 16px; padding: 30px; max-width: 700px; width: 90%; margin: 20px auto; border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 8px 32px rgba(0,0,0,0.5); max-height: 90vh; overflow-y: auto;">
                            <h2 style="margin: 0 0 20px 0; color: #fff; font-size: 24px;">📝 Select Comments to Boost</h2>
                            <div id="comment-selection-loading" style="color: #b0b0b0; text-align: center; padding: 20px;">Loading comments...</div>
                            <div id="comment-selection-list" style="display: none; margin-bottom: 20px;"></div>
                            <div id="comment-selection-error" style="display: none; color: #ef4444; margin-bottom: 20px;"></div>
                            <div style="display: flex; gap: 10px; justify-content: flex-end;">
                                <button onclick="hideCommentSelectionModal()" style="background: #444; color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer;">Cancel</button>
                                <button id="order-comment-likes-btn" onclick="orderSelectedCommentLikes()" style="background: #667eea; color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; display: none;">🚀 Order Likes for Selected</button>
                            </div>
                        </div>
                    </div>
                `;
                document.body.insertAdjacentHTML('beforeend', modalHtml);
                modal = document.getElementById('comment-selection-modal');
            }
            const loadingDiv = document.getElementById('comment-selection-loading');
            const listDiv = document.getElementById('comment-selection-list');
            const errorDiv = document.getElementById('comment-selection-error');
            const orderBtn = document.getElementById('order-comment-likes-btn');
            
            modal.style.display = 'flex';
            loadingDiv.style.display = 'block';
            listDiv.style.display = 'none';
            errorDiv.style.display = 'none';
            orderBtn.style.display = 'none';
            
            // Store video URL in modal for later use
            modal.setAttribute('data-video-url', videoUrl);
            
            try {
                const params = new URLSearchParams({ video_url: videoUrl });
                const response = await fetch('/api/fetch-comments?' + params.toString());
                const data = await response.json();
                
                loadingDiv.style.display = 'none';
                
                if (data.success && data.comments && data.comments.length > 0) {
                    listDiv.innerHTML = '';
                    data.comments.forEach((comment, index) => {
                        const commentHtml = `
                            <div style="background: #2a2a2a; border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; padding: 15px; margin-bottom: 10px;">
                                <label style="display: flex; align-items: flex-start; cursor: pointer; gap: 10px;">
                                    <input type="checkbox" class="comment-checkbox" data-comment-index="${index}" style="margin-top: 3px; cursor: pointer;">
                                    <div style="flex: 1;">
                                        <div style="color: #667eea; font-weight: 600; margin-bottom: 5px;">@${comment.username}</div>
                                        <div style="color: #b0b0b0; font-size: 0.9em;">${comment.text}</div>
                                    </div>
                                </label>
                            </div>
                        `;
                        listDiv.insertAdjacentHTML('beforeend', commentHtml);
                    });
                    
                    // Store comments data
                    modal.setAttribute('data-comments', JSON.stringify(data.comments));
                    
                    listDiv.style.display = 'block';
                    orderBtn.style.display = 'block';
                    
                    // Add change listener to checkboxes
                    document.querySelectorAll('.comment-checkbox').forEach(checkbox => {
                        checkbox.addEventListener('change', updateOrderButton);
                    });
                } else {
                    errorDiv.textContent = data.error || 'No comments found. Make sure the video has comments.';
                    errorDiv.style.display = 'block';
                }
            } catch (error) {
                loadingDiv.style.display = 'none';
                errorDiv.textContent = 'Error fetching comments: ' + error.message;
                errorDiv.style.display = 'block';
            }
        }
        
        function hideCommentSelectionModal() {
            const modal = document.getElementById('comment-selection-modal');
            if (modal) {
                modal.style.display = 'none';
            }
        }
        
        function updateOrderButton() {
            const checked = document.querySelectorAll('.comment-checkbox:checked').length;
            const orderBtn = document.getElementById('order-comment-likes-btn');
            if (orderBtn) {
                if (checked > 0) {
                    orderBtn.textContent = `🚀 Order Likes for ${checked} Selected`;
                    orderBtn.disabled = false;
                } else {
                    orderBtn.textContent = '🚀 Order Likes for Selected';
                    orderBtn.disabled = true;
                }
            }
        }
        
        async function orderSelectedCommentLikes() {
            const modal = document.getElementById('comment-selection-modal');
            if (!modal) return;
            
            const videoUrl = modal.getAttribute('data-video-url');
            const commentsJson = modal.getAttribute('data-comments');
            
            if (!videoUrl || !commentsJson) {
                alert('Error: Missing video URL or comments data');
                return;
            }
            
            const allComments = JSON.parse(commentsJson);
            const checkedBoxes = document.querySelectorAll('.comment-checkbox:checked');
            const selectedComments = Array.from(checkedBoxes).map(checkbox => {
                const index = parseInt(checkbox.getAttribute('data-comment-index'));
                return allComments[index];
            });
            
            if (selectedComments.length === 0) {
                alert('Please select at least one comment');
                return;
            }
            
            const orderBtn = document.getElementById('order-comment-likes-btn');
            const originalText = orderBtn.textContent;
            orderBtn.disabled = true;
            orderBtn.textContent = 'Ordering...';
            
            try {
                const params = new URLSearchParams({
                    video_url: videoUrl,
                    selected_comments: JSON.stringify(selectedComments)
                });
                
                const response = await fetch('/api/order-comment-likes?' + params.toString(), {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: params.toString()
                });
                
                const data = await response.json();
                
                if (data.success) {
                    alert('✅ ' + data.message);
                    hideCommentSelectionModal();
                    await loadDashboard(false);
                } else {
                    alert('❌ Error: ' + (data.error || 'Failed to order comment likes'));
                    orderBtn.disabled = false;
                    orderBtn.textContent = originalText;
                }
            } catch (error) {
                console.error('Error:', error);
                alert('❌ Error ordering comment likes: ' + error.message);
                orderBtn.disabled = false;
                orderBtn.textContent = originalText;
            }
        }
        
        function quickSetTargetTime(videoUrl, hoursId, minutesId) {
            const hoursInput = document.getElementById(hoursId);
            const minutesInput = document.getElementById(minutesId);
            
            const hours = parseInt(hoursInput.value) || 0;
            const minutes = parseInt(minutesInput.value) || 0;
            
            if (hours === 0 && minutes === 0) {
                alert('Please enter at least 1 hour or 1 minute');
                return;
            }
            
            // Calculate exact datetime from now
            const now = new Date();
            const targetTime = new Date(now.getTime() + (hours * 60 + minutes) * 60 * 1000);
            
            // Format as datetime-local (YYYY-MM-DDTHH:MM)
            const year = targetTime.getFullYear();
            const month = String(targetTime.getMonth() + 1).padStart(2, '0');
            const day = String(targetTime.getDate()).padStart(2, '0');
            const hour = String(targetTime.getHours()).padStart(2, '0');
            const minute = String(targetTime.getMinutes()).padStart(2, '0');
            const targetDateTime = `${year}-${month}-${day}T${hour}:${minute}`;
            
            // Show confirmation with exact time
            const exactTimeStr = targetTime.toLocaleString();
            if (confirm(`Set target completion time to:\n${exactTimeStr}\n\n(${hours}h ${minutes}m from now)`)) {
                updateTargetTime(videoUrl, targetDateTime);
            }
        }
        
        async function updateTargetTime(videoUrl, targetDateTime) {
            if (!targetDateTime) {
                alert('Please select a date and time');
                return;
            }
            
            try {
                console.log('Updating target time:', videoUrl, targetDateTime);
                
                const params = new URLSearchParams({
                    video_url: videoUrl,
                    target_datetime: targetDateTime
                });
                
                const response = await fetch(`/api/update-target?${params.toString()}`, {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                const data = await response.json();
                console.log('Response:', data);
                
                if (data.success) {
                    alert('✅ Target time updated successfully!');
                    loadDashboard(false); // Silent refresh after update
                } else {
                    alert('❌ Error: ' + (data.error || 'Failed to update'));
                }
            } catch (error) {
                console.error('Error:', error);
                alert('❌ Error updating target time: ' + error.message);
            }
        }
        
        // Campaign Management Functions
        let campaignsData = {};
        
        async function loadCampaigns() {
            try {
                const response = await fetch('/api/campaigns');
                const data = await response.json();
                if (data.success) {
                    campaignsData = data.campaigns || {};
                    updateCampaignSelector();
                    renderCampaignsSummary();
                    updateCampaignNames();
                }
            } catch (error) {
                console.error('Error loading campaigns:', error);
            }
        }
        
        function updateCampaignSelector() {
            const selector = document.getElementById('campaign-selector');
            if (!selector) return;
            
            selector.innerHTML = '<option value="">Select Campaign...</option>';
            for (const [campaignId, campaign] of Object.entries(campaignsData)) {
                const option = document.createElement('option');
                option.value = campaignId;
                option.textContent = `${campaign.name}${campaign.cpm > 0 ? ` (CPM: $${campaign.cpm.toFixed(2)})` : ''}`;
                selector.appendChild(option);
            }
        }
        
        function updateCampaignBar() {
            const checkboxes = document.querySelectorAll('.video-select-checkbox:checked');
            const count = checkboxes.length;
            const campaignBar = document.getElementById('campaign-bar');
            const selectedCount = document.getElementById('selected-count');
            const assignBtn = document.getElementById('assign-campaign-btn');
            
            if (selectedCount) selectedCount.textContent = count;
            if (assignBtn) assignBtn.disabled = count === 0;
            if (campaignBar) campaignBar.style.display = count > 0 ? 'block' : 'none';
        }
        
        function clearSelection() {
            document.querySelectorAll('.video-select-checkbox').forEach(cb => cb.checked = false);
            updateCampaignBar();
        }
        
        function showCreateCampaignModal() {
            const modal = document.getElementById('create-campaign-modal');
            if (modal) {
                modal.style.display = 'flex';
                document.getElementById('new-campaign-name').value = '';
                document.getElementById('new-campaign-cpm').value = '';
                const tv = document.getElementById('new-campaign-target-views');
                const tl = document.getElementById('new-campaign-target-likes');
                const tc = document.getElementById('new-campaign-target-comments');
                const tcl = document.getElementById('new-campaign-target-comment-likes');
                const dh = document.getElementById('new-campaign-duration-hours');
                const dm = document.getElementById('new-campaign-duration-minutes');
                if (tv) tv.value = '4000';
                if (tl) tl.value = '125';
                if (tc) tc.value = '7';
                if (tcl) tcl.value = '15';
                if (dh) dh.value = '24';
                if (dm) dm.value = '0';
                document.getElementById('create-campaign-error').style.display = 'none';
            }
        }
        
        function hideCreateCampaignModal() {
            const modal = document.getElementById('create-campaign-modal');
            if (modal) modal.style.display = 'none';
        }
        
        async function createCampaign() {
            const nameInput = document.getElementById('new-campaign-name');
            const cpmInput = document.getElementById('new-campaign-cpm');
            const targetViewsInput = document.getElementById('new-campaign-target-views');
            const targetLikesInput = document.getElementById('new-campaign-target-likes');
            const targetCommentsInput = document.getElementById('new-campaign-target-comments');
            const targetCommentLikesInput = document.getElementById('new-campaign-target-comment-likes');
            const durationHoursInput = document.getElementById('new-campaign-duration-hours');
            const durationMinutesInput = document.getElementById('new-campaign-duration-minutes');
            const errorDiv = document.getElementById('create-campaign-error');
            const name = nameInput.value.trim();
            const cpm = parseFloat(cpmInput.value) || 0;
            const targetViews = parseInt(targetViewsInput ? targetViewsInput.value : '4000') || 4000;
            const targetLikes = parseInt(targetLikesInput ? targetLikesInput.value : '125') || 125;
            const targetComments = parseInt(targetCommentsInput ? targetCommentsInput.value : '7') || 7;
            const targetCommentLikes = parseInt(targetCommentLikesInput ? targetCommentLikesInput.value : '15') || 15;
            const targetDurationHours = parseInt(durationHoursInput ? durationHoursInput.value : '24') || 0;
            const targetDurationMinutes = parseInt(durationMinutesInput ? durationMinutesInput.value : '0') || 0;
            
            if (!name) {
                errorDiv.textContent = 'Please enter a campaign name';
                errorDiv.style.display = 'block';
                return;
            }
            
            try {
                const params = new URLSearchParams({
                    campaign_name: name,
                    cpm: cpm.toString(),
                    target_views: targetViews.toString(),
                    target_likes: targetLikes.toString(),
                    target_comments: targetComments.toString(),
                    target_comment_likes: targetCommentLikes.toString(),
                    target_duration_hours: targetDurationHours.toString(),
                    target_duration_minutes: targetDurationMinutes.toString()
                });
                
                const response = await fetch('/api/create-campaign?' + params.toString(), {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: params.toString()
                });
                
                const data = await response.json();
                
                if (data.success) {
                    hideCreateCampaignModal();
                    await loadCampaigns();
                    // Auto-select the new campaign
                    const selector = document.getElementById('campaign-selector');
                    if (selector && data.campaign_id) {
                        selector.value = data.campaign_id;
                    }
                } else {
                    errorDiv.textContent = data.error || 'Failed to create campaign';
                    errorDiv.style.display = 'block';
                }
            } catch (error) {
                errorDiv.textContent = 'Error: ' + error.message;
                errorDiv.style.display = 'block';
            }
        }
        
        async function endCampaign(campaignId) {
            if (!confirm('Are you sure you want to end this campaign? The campaign will remain visible for stats tracking, but no new orders will be placed.')) {
                return;
            }
            
            try {
                const params = new URLSearchParams({
                    campaign_id: campaignId
                });
                
                const response = await fetch('/api/end-campaign?' + params.toString(), {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: params.toString()
                });
                
                const data = await response.json();
                
                if (data.success) {
                    showNotification('✓ Campaign ended successfully', 'success');
                    await loadCampaigns();
                    await loadDashboard(false);
                } else {
                    alert('❌ Error: ' + (data.error || 'Failed to end campaign'));
                }
            } catch (error) {
                alert('❌ Error: ' + error.message);
            }
        }
        
        function showEditCampaignModal(campaignId) {
            const campaign = campaignsData[campaignId];
            if (!campaign) return;
            
            document.getElementById('edit-campaign-name').value = campaign.name || '';
            document.getElementById('edit-campaign-cpm').value = campaign.cpm || 0;
            document.getElementById('edit-campaign-target-views').value = campaign.target_views || 4000;
            document.getElementById('edit-campaign-target-likes').value = campaign.target_likes || 125;
            document.getElementById('edit-campaign-target-comments').value = campaign.target_comments || 7;
            document.getElementById('edit-campaign-target-comment-likes').value = campaign.target_comment_likes || 15;
            document.getElementById('edit-campaign-duration-hours').value = campaign.target_duration_hours || 24;
            document.getElementById('edit-campaign-duration-minutes').value = campaign.target_duration_minutes || 0;
            
            const modal = document.getElementById('edit-campaign-modal');
            modal.setAttribute('data-campaign-id', campaignId);
            modal.style.display = 'flex';
            document.getElementById('edit-campaign-error').style.display = 'none';
        }
        
        function hideEditCampaignModal() {
            const modal = document.getElementById('edit-campaign-modal');
            modal.style.display = 'none';
            modal.removeAttribute('data-campaign-id');
        }
        
        async function updateCampaign() {
            const modal = document.getElementById('edit-campaign-modal');
            const campaignId = modal.getAttribute('data-campaign-id');
            if (!campaignId) return;
            
            const nameInput = document.getElementById('edit-campaign-name');
            const cpmInput = document.getElementById('edit-campaign-cpm');
            const targetViewsInput = document.getElementById('edit-campaign-target-views');
            const targetLikesInput = document.getElementById('edit-campaign-target-likes');
            const targetCommentsInput = document.getElementById('edit-campaign-target-comments');
            const targetCommentLikesInput = document.getElementById('edit-campaign-target-comment-likes');
            const durationHoursInput = document.getElementById('edit-campaign-duration-hours');
            const durationMinutesInput = document.getElementById('edit-campaign-duration-minutes');
            const errorDiv = document.getElementById('edit-campaign-error');
            
            const name = nameInput.value.trim();
            const cpm = parseFloat(cpmInput.value) || 0;
            const targetViews = parseInt(targetViewsInput ? targetViewsInput.value : '4000') || 4000;
            const targetLikes = parseInt(targetLikesInput ? targetLikesInput.value : '125') || 125;
            const targetComments = parseInt(targetCommentsInput ? targetCommentsInput.value : '7') || 7;
            const targetCommentLikes = parseInt(targetCommentLikesInput ? targetCommentLikesInput.value : '15') || 15;
            const targetDurationHours = parseInt(durationHoursInput ? durationHoursInput.value : '24') || 0;
            const targetDurationMinutes = parseInt(durationMinutesInput ? durationMinutesInput.value : '0') || 0;
            
            if (!name) {
                errorDiv.textContent = 'Please enter a campaign name';
                errorDiv.style.display = 'block';
                return;
            }
            
            try {
                const params = new URLSearchParams({
                    campaign_id: campaignId,
                    campaign_name: name,
                    cpm: cpm.toString(),
                    target_views: targetViews.toString(),
                    target_likes: targetLikes.toString(),
                    target_comments: targetComments.toString(),
                    target_comment_likes: targetCommentLikes.toString(),
                    target_duration_hours: targetDurationHours.toString(),
                    target_duration_minutes: targetDurationMinutes.toString()
                });
                
                const response = await fetch('/api/update-campaign?' + params.toString(), {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: params.toString()
                });
                
                const data = await response.json();
                
                if (data.success) {
                    hideEditCampaignModal();
                    await loadCampaigns();
                    await loadDashboard(false);
                } else {
                    errorDiv.textContent = data.error || 'Failed to update campaign';
                    errorDiv.style.display = 'block';
                }
            } catch (error) {
                errorDiv.textContent = 'Error: ' + error.message;
                errorDiv.style.display = 'block';
            }
        }
        
        async function assignToCampaign() {
            const selector = document.getElementById('campaign-selector');
            const campaignId = selector ? selector.value : '';
            
            if (!campaignId) {
                alert('Please select a campaign');
                return;
            }
            
            const checkboxes = document.querySelectorAll('.video-select-checkbox:checked');
            const videoUrls = Array.from(checkboxes).map(cb => {
                const url = cb.getAttribute('data-video-url');
                return url.replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&amp;/g, '&');
            });
            
            if (videoUrls.length === 0) {
                alert('Please select at least one video');
                return;
            }
            
            try {
                const params = new URLSearchParams({
                    campaign_id: campaignId,
                    video_urls: JSON.stringify(videoUrls)
                });
                
                const response = await fetch('/api/assign-videos?' + params.toString(), {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: params.toString()
                });
                
                const data = await response.json();
                
                if (data.success) {
                    alert('✅ ' + data.message);
                    clearSelection();
                    await loadCampaigns();
                    await loadDashboard(false);
                } else {
                    alert('❌ Error: ' + (data.error || 'Failed to assign videos'));
                }
            } catch (error) {
                alert('❌ Error: ' + error.message);
            }
        }
        
        function renderCampaignsSummary() {
            const container = document.getElementById('campaigns-summary');
            if (!container) return;
            
            const campaigns = Object.entries(campaignsData);
            
            let html = '<div style="background: linear-gradient(135deg, #1e1e1e 0%, #2a2a2a 100%); border-radius: 12px; padding: 20px; margin-bottom: 25px; border: 1px solid rgba(255,255,255,0.1);">';
            html += '<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">';
            html += '<h3 style="margin: 0; color: #fff; font-size: 1.2em; font-weight: 600;">📊 Campaigns Overview</h3>';
            html += '<button id="add-campaign-btn-header" class="add-campaign-btn">Add Campaign</button>';
            html += '</div>';

            // CPM + Goals calculator (home)
            html += '<div style="background: #252525; border-radius: 12px; padding: 16px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px;">';
            html += '<div style="display: flex; justify-content: space-between; align-items: center; gap: 10px; margin-bottom: 12px; flex-wrap: wrap;">';
            html += '<div style="color: #fff; font-weight: 700;">💰 CPM & Goals Calculator</div>';
            if (campaigns.length > 0) {
                html += '<select id="calc-campaign-select" style="padding: 8px 10px; background: #1a1a1a; border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; color: #fff; font-size: 13px;">';
                html += '<option value="">Use campaign defaults…</option>';
                for (const [campaignId, campaign] of campaigns) {
                    const name = (campaign && campaign.name) ? String(campaign.name) : 'Unnamed Campaign';
                    const safeName = name.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
                    html += `<option value="${campaignId}">${safeName}</option>`;
                }
                html += '</select>';
            }
            html += '</div>';
            html += '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px;">';
            html += '<div><div style="color:#b0b0b0; font-size:12px; margin-bottom:6px;">CPM ($ / 1000 views)</div><input id="calc-cpm" type="number" min="0" step="0.01" placeholder="2.50" style="width:100%; padding:10px; background:#1a1a1a; border:1px solid rgba(255,255,255,0.2); border-radius:8px; color:#fff;"></div>';
            html += '<div><div style="color:#b0b0b0; font-size:12px; margin-bottom:6px;"># of videos</div><input id="calc-videos" type="number" min="1" step="1" placeholder="10" style="width:100%; padding:10px; background:#1a1a1a; border:1px solid rgba(255,255,255,0.2); border-radius:8px; color:#fff;"></div>';
            html += '<div><div style="color:#b0b0b0; font-size:12px; margin-bottom:6px;">Views goal / video</div><input id="calc-views" type="number" min="0" step="1" placeholder="4000" style="width:100%; padding:10px; background:#1a1a1a; border:1px solid rgba(255,255,255,0.2); border-radius:8px; color:#fff;"></div>';
            html += '<div><div style="color:#b0b0b0; font-size:12px; margin-bottom:6px;">Likes goal / video</div><input id="calc-likes" type="number" min="0" step="1" placeholder="125" style="width:100%; padding:10px; background:#1a1a1a; border:1px solid rgba(255,255,255,0.2); border-radius:8px; color:#fff;"></div>';
            html += '<div><div style="color:#b0b0b0; font-size:12px; margin-bottom:6px;">Comments goal / video</div><input id="calc-comments" type="number" min="0" step="1" placeholder="7" style="width:100%; padding:10px; background:#1a1a1a; border:1px solid rgba(255,255,255,0.2); border-radius:8px; color:#fff;"></div>';
            html += '<div><div style="color:#b0b0b0; font-size:12px; margin-bottom:6px;">Comment likes goal / video</div><input id="calc-comment-likes" type="number" min="0" step="1" placeholder="15" style="width:100%; padding:10px; background:#1a1a1a; border:1px solid rgba(255,255,255,0.2); border-radius:8px; color:#fff;"></div>';
            html += '</div>';
            html += '<div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.08); display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px;">';
            html += '<div style="background:#1f1f1f; border:1px solid rgba(255,255,255,0.06); border-radius:10px; padding:12px;"><div style="color:#b0b0b0; font-size:12px;">Estimated Invest</div><div id="calc-invest" style="color:#ef4444; font-weight:800; font-size:18px;">$0.00</div></div>';
            html += '<div style="background:#1f1f1f; border:1px solid rgba(255,255,255,0.06); border-radius:10px; padding:12px;"><div style="color:#b0b0b0; font-size:12px;">Estimated Earn</div><div id="calc-earn" style="color:#10b981; font-weight:800; font-size:18px;">$0.00</div></div>';
            html += '<div style="background:#1f1f1f; border:1px solid rgba(255,255,255,0.06); border-radius:10px; padding:12px;"><div style="color:#b0b0b0; font-size:12px;">Profit</div><div id="calc-profit" style="color:#fff; font-weight:800; font-size:18px;">$0.00</div><div id="calc-roi" style="color:#b0b0b0; font-size:12px; margin-top:4px;">ROI: 0%</div></div>';
            html += '</div>';
            html += '<div style="margin-top: 10px; color: #888; font-size: 12px;">Uses current service rates (approx): Views $0.014 / 1k, Likes $0.21 / 1k, Comments $13.50 / 1k, Comment Likes $0.21 / 1k.</div>';
            html += '</div>';
            
            if (campaigns.length === 0) {
                html += '<div style="text-align: center; padding: 40px 20px; color: #b0b0b0;">';
                html += '<p style="margin: 0 0 10px 0; font-size: 1em;">No campaigns yet. Create your first campaign to start tracking your video performance!</p>';
                html += '</div>';
            } else {
                html += '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px;">';
                
                for (const [campaignId, campaign] of campaigns) {
                    const financial = campaign.financial || {};
                    const totalSpent = financial.total_spent || 0;
                    const totalEarned = financial.total_earned || 0;
                    const profit = financial.profit || 0;
                    const roi = financial.roi || 0;
                    const videoCount = (campaign.videos || []).length;
                    const goalViews = (campaign.target_views !== undefined) ? campaign.target_views : 4000;
                    const goalLikes = (campaign.target_likes !== undefined) ? campaign.target_likes : 125;
                    const goalComments = (campaign.target_comments !== undefined) ? campaign.target_comments : 7;
                    const goalCommentLikes = (campaign.target_comment_likes !== undefined) ? campaign.target_comment_likes : 15;
                    const durH = (campaign.target_duration_hours !== undefined) ? campaign.target_duration_hours : 24;
                    const durM = (campaign.target_duration_minutes !== undefined) ? campaign.target_duration_minutes : 0;
                    
                    html += `<div class="campaign-card-clickable" data-campaign-id="${campaignId}" style="background: #2a2a2a; border-radius: 8px; padding: 15px; border: 1px solid rgba(255,255,255,0.1); cursor: pointer; transition: all 0.2s; position: relative; display: flex; flex-direction: column;" onmouseover="this.style.borderColor='rgba(102,126,234,0.5)'; this.style.transform='translateY(-2px)';" onmouseout="this.style.borderColor='rgba(255,255,255,0.1)'; this.style.transform='translateY(0)';">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                            <h4 style="margin: 0; color: #fff; font-size: 1.1em; font-weight: 600;">${campaign.name || 'Unnamed Campaign'}</h4>
                            ${campaign.cpm > 0 ? `<span style="color: #667eea; font-size: 0.9em;">CPM: $${campaign.cpm.toFixed(2)}</span>` : '<span style="color: #888; font-size: 0.9em;">No CPM set</span>'}
                        </div>
                        <div style="color: #b0b0b0; font-size: 0.85em; margin-bottom: 10px;">
                            <div>Goals/post: ${formatNumber(goalViews)} views · ${formatNumber(goalLikes)} likes · ${formatNumber(goalComments)} comments · ${formatNumber(goalCommentLikes)} comment likes</div>
                            <div style="margin-top: 4px;">Speed: ${durH}h ${durM}m to goal</div>
                        </div>
                        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 10px;">
                            <div>
                                <div style="color: #b0b0b0; font-size: 0.85em;">Videos</div>
                                <div style="color: #fff; font-size: 1.2em; font-weight: 600;">${videoCount}</div>
                            </div>
                            <div>
                                <div style="color: #b0b0b0; font-size: 0.85em;">Total Views</div>
                                <div style="color: #fff; font-size: 1.2em; font-weight: 600;">${formatNumber(financial.total_views || 0)}</div>
                            </div>
                        </div>
                        <div style="border-top: 1px solid rgba(255,255,255,0.1); padding-top: 10px; margin-top: 10px;">
                            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                <span style="color: #b0b0b0; font-size: 0.9em;">Spent:</span>
                                <span style="color: #ef4444; font-weight: 600;">$${totalSpent.toFixed(2)}</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                                <span style="color: #b0b0b0; font-size: 0.9em;">Earned:</span>
                                <span style="color: #10b981; font-weight: 600;">$${totalEarned.toFixed(2)}</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; margin-top: 10px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.1);">
                                <span style="color: #fff; font-weight: 600;">Profit:</span>
                                <span style="color: ${profit >= 0 ? '#10b981' : '#ef4444'}; font-weight: 700; font-size: 1.1em;">$${profit.toFixed(2)}</span>
                            </div>
                            ${totalSpent > 0 ? `<div style="display: flex; justify-content: space-between; margin-top: 5px;">
                                <span style="color: #b0b0b0; font-size: 0.85em;">ROI:</span>
                                <span style="color: ${roi >= 0 ? '#10b981' : '#ef4444'}; font-weight: 600;">${roi >= 0 ? '+' : ''}${roi.toFixed(1)}%</span>
                            </div>` : ''}
                        </div>
                        <div style="border-top: 1px solid rgba(255,255,255,0.1); padding-top: 12px; margin-top: 12px; display: flex; gap: 8px; flex-wrap: wrap;">
                            <button class="edit-campaign-btn" data-campaign-id="${campaignId}" onclick="event.stopPropagation(); showEditCampaignModal('${campaignId}');" style="flex: 1; min-width: 80px; background: #2a2a2a; color: #fff; border: 1px solid rgba(255,255,255,0.2); padding: 8px 12px; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: 600; transition: all 0.2s;" onmouseover="this.style.background='#333'; this.style.borderColor='rgba(255,255,255,0.3)';" onmouseout="this.style.background='#2a2a2a'; this.style.borderColor='rgba(255,255,255,0.2)';">Edit</button>
                            <button class="add-video-to-campaign-btn" data-campaign-id="${campaignId}" onclick="event.stopPropagation(); showAddVideoToCampaignModal('${campaignId}');" style="flex: 1; min-width: 100px; background: #2a2a2a; color: #667eea; border: 1px solid rgba(102,126,234,0.3); padding: 8px 12px; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: 600; transition: all 0.2s;" onmouseover="this.style.background='#333'; this.style.borderColor='rgba(102,126,234,0.5)';" onmouseout="this.style.background='#2a2a2a'; this.style.borderColor='rgba(102,126,234,0.3)';">Add Video</button>
                            ${campaign.status !== 'ended' ? `<button class="end-campaign-btn" data-campaign-id="${campaignId}" onclick="event.stopPropagation(); endCampaign('${campaignId}');" style="flex: 1; min-width: 120px; background: #2a2a2a; color: #ef4444; border: 1px solid rgba(239,68,68,0.3); padding: 8px 12px; border-radius: 6px; cursor: pointer; font-size: 12px; font-weight: 600; transition: all 0.2s;" onmouseover="this.style.background='#333'; this.style.borderColor='rgba(239,68,68,0.5)';" onmouseout="this.style.background='#2a2a2a'; this.style.borderColor='rgba(239,68,68,0.3)';">End Campaign</button>` : '<span style="flex: 1; color: #888; font-size: 11px; padding: 8px 12px; text-align: center;">Ended</span>'}
                        </div>
                    </div>`;
                }
                
                html += '</div>';
            }
            
            html += '</div>';
            container.innerHTML = html;
            
            // Attach event listener to the button after inserting HTML
            const addCampaignBtn = document.getElementById('add-campaign-btn-header');
            if (addCampaignBtn) {
                addCampaignBtn.addEventListener('click', function(e) {
                    e.preventDefault();
                    showCreateCampaignModal();
                });
            }
            
            // Attach click listeners to campaign cards
            document.querySelectorAll('.campaign-card-clickable').forEach(card => {
                card.addEventListener('click', function(e) {
                    // Don't navigate if clicking on a button or link inside
                    if (e.target.tagName === 'BUTTON' || e.target.tagName === 'A' || e.target.closest('button') || e.target.closest('a')) {
                        return;
                    }
                    const campaignId = card.getAttribute('data-campaign-id');
                    if (campaignId) {
                        navigateToCampaign(campaignId);
                    }
                });
            });

            initCpmCalculator();
        }

        // CPM + Goals calculator helpers
        const CPM_CALC_RATES = {
            views: 0.0140,         // $ per 1000 views
            likes: 0.2100,         // $ per 1000 likes
            comments: 13.5000,     // $ per 1000 comments
            comment_likes: 0.2100  // $ per 1000 comment likes
        };

        function formatMoney(amount) {
            const n = isFinite(amount) ? amount : 0;
            return '$' + n.toFixed(2);
        }

        function fillCalculatorFromCampaign(campaignId) {
            const c = campaignsData[campaignId];
            if (!c) return;
            const elCpm = document.getElementById('calc-cpm');
            const elViews = document.getElementById('calc-views');
            const elLikes = document.getElementById('calc-likes');
            const elComments = document.getElementById('calc-comments');
            const elCommentLikes = document.getElementById('calc-comment-likes');
            if (elCpm) elCpm.value = (c.cpm !== undefined && c.cpm !== null) ? String(c.cpm) : '';
            if (elViews) elViews.value = (c.target_views !== undefined && c.target_views !== null) ? String(c.target_views) : '4000';
            if (elLikes) elLikes.value = (c.target_likes !== undefined && c.target_likes !== null) ? String(c.target_likes) : '125';
            if (elComments) elComments.value = (c.target_comments !== undefined && c.target_comments !== null) ? String(c.target_comments) : '7';
            if (elCommentLikes) elCommentLikes.value = (c.target_comment_likes !== undefined && c.target_comment_likes !== null) ? String(c.target_comment_likes) : '15';
        }

        function updateCpmCalculator() {
            const elCpm = document.getElementById('calc-cpm');
            const elVideos = document.getElementById('calc-videos');
            const elViews = document.getElementById('calc-views');
            const elLikes = document.getElementById('calc-likes');
            const elComments = document.getElementById('calc-comments');
            const elCommentLikes = document.getElementById('calc-comment-likes');

            const cpm = Math.max(0, parseFloat(elCpm ? elCpm.value : '0') || 0);
            const videos = Math.max(1, parseInt(elVideos ? elVideos.value : '1') || 1);
            const viewsGoal = Math.max(0, parseInt(elViews ? elViews.value : '0') || 0);
            const likesGoal = Math.max(0, parseInt(elLikes ? elLikes.value : '0') || 0);
            const commentsGoal = Math.max(0, parseInt(elComments ? elComments.value : '0') || 0);
            const commentLikesGoal = Math.max(0, parseInt(elCommentLikes ? elCommentLikes.value : '0') || 0);

            const totalViews = viewsGoal * videos;
            const totalLikes = likesGoal * videos;
            const totalComments = commentsGoal * videos;
            const totalCommentLikes = commentLikesGoal * videos;

            const invest =
                (totalViews / 1000.0) * CPM_CALC_RATES.views +
                (totalLikes / 1000.0) * CPM_CALC_RATES.likes +
                (totalComments / 1000.0) * CPM_CALC_RATES.comments +
                (totalCommentLikes / 1000.0) * CPM_CALC_RATES.comment_likes;

            const earn = (totalViews / 1000.0) * cpm;
            const profit = earn - invest;
            const roi = invest > 0 ? (profit / invest) * 100 : 0;

            const investEl = document.getElementById('calc-invest');
            const earnEl = document.getElementById('calc-earn');
            const profitEl = document.getElementById('calc-profit');
            const roiEl = document.getElementById('calc-roi');

            if (investEl) investEl.textContent = formatMoney(invest);
            if (earnEl) earnEl.textContent = formatMoney(earn);
            if (profitEl) {
                profitEl.textContent = formatMoney(profit);
                profitEl.style.color = profit >= 0 ? '#10b981' : '#ef4444';
            }
            if (roiEl) {
                roiEl.textContent = 'ROI: ' + (isFinite(roi) ? (roi >= 0 ? '+' : '') + roi.toFixed(1) : '0.0') + '%';
                roiEl.style.color = roi >= 0 ? '#10b981' : '#ef4444';
            }
        }

        function initCpmCalculator() {
            const elCpm = document.getElementById('calc-cpm');
            const elVideos = document.getElementById('calc-videos');
            const elViews = document.getElementById('calc-views');
            const elLikes = document.getElementById('calc-likes');
            const elComments = document.getElementById('calc-comments');
            const elCommentLikes = document.getElementById('calc-comment-likes');
            const elSelect = document.getElementById('calc-campaign-select');

            // If calculator isn't present on this route, skip
            if (!elCpm || !elVideos || !elViews || !elLikes || !elComments || !elCommentLikes) return;

            // Set defaults once if empty
            if (!elVideos.value) elVideos.value = '1';
            if (!elViews.value) elViews.value = '4000';
            if (!elLikes.value) elLikes.value = '125';
            if (!elComments.value) elComments.value = '7';
            if (!elCommentLikes.value) elCommentLikes.value = '15';

            const handler = () => updateCpmCalculator();
            elCpm.oninput = handler;
            elVideos.oninput = handler;
            elViews.oninput = handler;
            elLikes.oninput = handler;
            elComments.oninput = handler;
            elCommentLikes.oninput = handler;

            if (elSelect) {
                elSelect.onchange = () => {
                    if (elSelect.value) {
                        fillCalculatorFromCampaign(elSelect.value);
                    }
                    updateCpmCalculator();
                };
            }

            updateCpmCalculator();
        }
        
        function updateCampaignNames() {
            // Update campaign names in video cards
            for (const [campaignId, campaign] of Object.entries(campaignsData)) {
                const videos = campaign.videos || [];
                for (const videoUrl of videos) {
                    const safeUrl = videoUrl.replace(/[^a-zA-Z0-9]/g, '_');
                    const nameEl = document.getElementById('campaign-name-' + safeUrl);
                    if (nameEl) {
                        nameEl.textContent = campaign.name || 'Unnamed';
                    }
                }
            }
        }
        
        function renderVideoCard(videoUrl, videoData) {
            const { username, videoId } = extractVideoInfo(videoUrl);
            // Escape template literal special characters
            function escapeTemplateLiteral(str) {
                if (!str) return '';
                return String(str).replace(/\\\\/g, '\\\\\\\\').replace(/`/g, '\\\\`').replace(/\\$/g, '\\\\$');
            }
            
            const displayName = username ? `@${escapeTemplateLiteral(username)}` : 'Unknown';
            
            const ordersPlaced = videoData.orders_placed || {};
            
            // Use REAL-TIME analytics if available, otherwise fall back to initial + ordered
            const realViews = videoData.real_views !== undefined ? videoData.real_views : (videoData.initial_views || 0);
            const realLikes = videoData.real_likes !== undefined ? videoData.real_likes : (videoData.initial_likes || 0);
            const realComments = videoData.real_comments !== undefined ? videoData.real_comments : (videoData.initial_comments || 0);
            
            const initialViews = videoData.initial_views || 0;
            const initialLikes = videoData.initial_likes || 0;
            
            const viewsOrdered = ordersPlaced.views || 0;
            const likesOrdered = ordersPlaced.likes || 0;
            const commentsOrdered = ordersPlaced.comments || 0;
            const commentLikesOrdered = ordersPlaced.comment_likes || 0;
            
            // Count number of orders placed for each metric
            const orderHistory = videoData.order_history || [];
            const viewsOrdersCount = orderHistory.filter(o => o.service === 'views').length;
            const likesOrdersCount = orderHistory.filter(o => o.service === 'likes').length;
            const commentsOrdersCount = orderHistory.filter(o => o.service === 'comments').length;
            const commentLikesOrdersCount = orderHistory.filter(o => o.service === 'comment_likes').length;
            
            // Use real-time analytics as current actual values
            const totalViews = realViews; // Current actual views from TikTok
            const totalLikes = realLikes; // Current actual likes from TikTok
            const totalComments = realComments; // Current actual comments from TikTok
            
            // Calculate expected total (for tracking purposes)
            const expectedViews = initialViews + viewsOrdered;
            const expectedLikes = initialLikes + likesOrdered;
            
            const targetViews = videoData.target_views || 4000;
            const targetLikes = videoData.target_likes || 125;
            const targetComments = videoData.target_comments || 7;
            const targetCommentLikes = videoData.target_comment_likes || 15;
            
            // Calculate expected totals to order (target - initial)
            const expectedViewsToOrder = Math.max(0, targetViews - initialViews);
            const expectedLikesToOrder = Math.max(0, targetLikes - initialLikes);
            const expectedCommentsToOrder = Math.max(0, targetComments - 0); // Comments start at 0
            const expectedCommentLikesToOrder = Math.max(0, targetCommentLikes - 0); // Comment likes start at 0
            
            const viewsProgress = (totalViews / targetViews) * 100;
            const likesProgress = (totalLikes / targetLikes) * 100;
            const commentsProgress = (commentsOrdered / targetComments) * 100;
            const commentLikesProgress = (commentLikesOrdered / targetCommentLikes) * 100;
            
            const overallProgress = viewsProgress; // Use views as main indicator
            
            const targetCompletionTime = videoData.target_completion_time || videoData.target_completion_datetime;
            const timeRemaining = calculateTimeRemaining(targetCompletionTime);
            
            // Get current datetime-local value (default to 24 hours from now)
            const defaultTargetTime = new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString().slice(0, 16);
            const currentTargetTime = targetCompletionTime ? new Date(targetCompletionTime).toISOString().slice(0, 16) : defaultTargetTime;
            
            // Milestone information
            const commentsMilestone = 2000;
            const commentLikesMilestone = 2600;
            const savedComments = videoData.saved_comments || [];
            const commentUsername = videoData.comment_username || null;
            const hasCommentsOrdered = ordersPlaced.comments > 0;
            const hasCommentLikesOrdered = ordersPlaced.comment_likes > 0;
            const activityLog = videoData.activity_log || [];
            
            // Determine current status
            let currentStatus = 'Ready';
            if (hasCommentsOrdered && hasCommentLikesOrdered && totalViews >= targetViews) {
                currentStatus = 'Complete';
            } else if (viewsOrdered > 0) {
                currentStatus = 'Active - Delivering orders';
            } else if (totalViews >= commentsMilestone && !hasCommentsOrdered) {
                currentStatus = 'Waiting - Ready to order comments';
            } else if (totalViews >= commentLikesMilestone && !hasCommentLikesOrdered) {
                currentStatus = 'Waiting - Ready to order comment likes';
            } else if (viewsOrdered === 0) {
                currentStatus = 'Initializing';
            }
            
            // Calculate time until milestones
            const currentTotalViews = totalViews; // Real-time views
            const viewsNeededForComments = Math.max(0, commentsMilestone - currentTotalViews);
            const viewsNeededForCommentLikes = Math.max(0, commentLikesMilestone - currentTotalViews);
            
            // Estimate delivery rate (views per hour) based on schedule
            // If we have a target completion time, calculate rate
            let viewsPerHour = 0;
            if (targetCompletionTime && viewsOrdered > 0) {
                const startTime = videoData.start_time ? new Date(videoData.start_time) : new Date();
                const endTime = new Date(targetCompletionTime);
                const hoursRemaining = Math.max(1, (endTime - new Date()) / (1000 * 60 * 60));
                viewsPerHour = viewsOrdered / hoursRemaining;
            } else {
                // Default: assume 24 hours for 4000 views = ~167 views/hour
                viewsPerHour = 167;
            }
            
            const hoursUntilComments = viewsNeededForComments > 0 && viewsPerHour > 0 ? viewsNeededForComments / viewsPerHour : 0;
            const hoursUntilCommentLikes = viewsNeededForCommentLikes > 0 && viewsPerHour > 0 ? viewsNeededForCommentLikes / viewsPerHour : 0;
            
            // Calculate rates based on target completion time (if set) or use combined rates
            const now = new Date();
            const startTime = videoData.start_time ? new Date(videoData.start_time) : now;
            let hoursToTarget = 0;
            if (targetCompletionTime) {
                const targetTime = new Date(targetCompletionTime);
                hoursToTarget = Math.max(0, (targetTime - now) / (1000 * 60 * 60));
            }
            
            // Get initial values for catch-up calculation
            const initialComments = videoData.initial_comments || 0;
            
            // Calculate expected values at current time (for catch-up comparison)
            let expectedViewsNow = initialViews;
            let expectedLikesNow = initialLikes;
            let expectedCommentsNow = initialComments;
            
            if (targetCompletionTime) {
                const targetTime = new Date(targetCompletionTime);
                const totalDuration = targetTime - startTime;
                const elapsed = now - startTime;
                
                if (totalDuration > 0 && elapsed >= 0) {
                    const progress = Math.min(1, Math.max(0, elapsed / totalDuration));
                    expectedViewsNow = initialViews + (targetViews - initialViews) * progress;
                    expectedLikesNow = initialLikes + (targetLikes - initialLikes) * progress;
                    expectedCommentsNow = initialComments + (targetComments - initialComments) * progress;
                }
            }
            
            // Calculate catch-up amounts (difference between expected and actual)
            const viewsCatchUp = Math.max(0, Math.ceil(expectedViewsNow - totalViews));
            const likesCatchUp = Math.max(0, Math.ceil(expectedLikesNow - totalLikes));
            const commentsCatchUp = Math.max(0, Math.ceil(expectedCommentsNow - totalComments));
            
            // Calculate what's needed for each metric (needed before calculating rates)
            const viewsNeeded = Math.max(0, targetViews - totalViews);
            const likesNeeded = Math.max(0, targetLikes - totalLikes);
            const commentsNeeded = Math.max(0, targetComments - totalComments);
            const commentLikesNeeded = Math.max(0, targetCommentLikes - commentLikesOrdered);
            
            // Calculate combined progress rates (orders + organic growth) for each metric
            const growthHistory = videoData.growth_history || [];
            let combinedViewsPerHour = viewsPerHour;
            let combinedLikesPerHour = 0;
            let combinedCommentsPerHour = 0;
            
            // Calculate likes per hour from orders (if target time is set)
            if (targetCompletionTime && likesOrdered > 0 && hoursToTarget > 0) {
                combinedLikesPerHour = likesOrdered / hoursToTarget;
            }
            
            // Calculate comments per hour from orders (if target time is set)
            if (targetCompletionTime && commentsOrdered > 0 && hoursToTarget > 0) {
                combinedCommentsPerHour = commentsOrdered / hoursToTarget;
            }
            
            // Calculate comment likes per hour from orders (if target time is set)
            let commentLikesPerHour = 0;
            if (targetCompletionTime && commentLikesOrdered > 0 && hoursToTarget > 0) {
                commentLikesPerHour = commentLikesOrdered / hoursToTarget;
            }
            
            // Add organic growth rates if available
            if (growthHistory.length >= 2) {
                const recent = growthHistory.slice(-5);
                const oldest = recent[0];
                const newest = recent[recent.length - 1];
                const timeDiff = (new Date(newest.timestamp) - new Date(oldest.timestamp)) / (1000 * 60 * 60);
                
                if (timeDiff > 0) {
                    const viewsDiff = newest.views - oldest.views;
                    const likesDiff = newest.likes - oldest.likes;
                    const commentsDiff = newest.comments - oldest.comments;
                    
                    const organicViewsRate = viewsDiff / timeDiff;
                    const organicLikesRate = likesDiff / timeDiff;
                    const organicCommentsRate = commentsDiff / timeDiff;
                    
                    combinedViewsPerHour = viewsPerHour + organicViewsRate;
                    combinedLikesPerHour = combinedLikesPerHour + organicLikesRate;
                    combinedCommentsPerHour = combinedCommentsPerHour + organicCommentsRate;
                }
            }
            
            // If no organic growth and no orders, use default rates based on target time
            if (targetCompletionTime && hoursToTarget > 0) {
                if (combinedViewsPerHour === 0 || combinedViewsPerHour === viewsPerHour) {
                    // Recalculate based on what's needed to reach target in time
                    const viewsNeededForTarget = Math.max(0, targetViews - totalViews);
                    combinedViewsPerHour = viewsNeededForTarget / hoursToTarget;
                }
                if (combinedLikesPerHour === 0 && likesNeeded > 0) {
                    const likesNeededForTarget = Math.max(0, targetLikes - totalLikes);
                    combinedLikesPerHour = likesNeededForTarget / hoursToTarget;
                }
                if (combinedCommentsPerHour === 0 && commentsNeeded > 0) {
                    const commentsNeededForTarget = Math.max(0, targetComments - totalComments);
                    combinedCommentsPerHour = commentsNeededForTarget / hoursToTarget;
                }
                if (commentLikesPerHour === 0 && commentLikesNeeded > 0) {
                    const commentLikesNeededForTarget = Math.max(0, targetCommentLikes - commentLikesOrdered);
                    commentLikesPerHour = commentLikesNeededForTarget / hoursToTarget;
                }
            }
            
            // Check if target is overdue
            const isTargetOverdue = targetCompletionTime && hoursToTarget <= 0;
            
            // Pricing rates (per 1000 units)
            const rates = {
                'views': 0.0140,
                'likes': 0.2100,
                'comments': 13.5000,
                'comment_likes': 0.2100
            };
            
            // Minimum order sizes
            const minimums = {
                'views': 50,
                'likes': 10,
                'comments': 10,
                'comment_likes': 50
            };
            
            // Calculate next purchase info for each metric
            function calculateNextPurchase(metricName, needed, hoursRemaining, combinedPerHour, minOrder) {
                if (needed <= 0 || hoursRemaining <= 0 || isTargetOverdue) {
                    return null;
                }
                
                // Always use minimum order size
                const unitsPerPurchase = minOrder;
                
                // Calculate how many minimum orders we can fit in the remaining time
                // Aim for orders every 30 minutes to 1 hour (distribute evenly)
                const minHoursBetweenOrders = 0.5; // 30 minutes minimum between orders
                const maxHoursBetweenOrders = 1.0; // 1 hour maximum between orders
                
                // Calculate maximum number of orders we can make
                const maxOrders = Math.floor(hoursRemaining / minHoursBetweenOrders);
                const ordersNeeded = Math.ceil(needed / unitsPerPurchase);
                const totalOrders = Math.min(maxOrders, ordersNeeded);
                
                // Calculate time between orders (distribute evenly over remaining time)
                const hoursBetweenOrders = totalOrders > 1 ? hoursRemaining / totalOrders : hoursRemaining;
                
                // Time until next purchase
                const hoursUntilNext = Math.max(0.1, hoursBetweenOrders); // At least 6 minutes
                const nextPurchaseTime = new Date(now.getTime() + hoursUntilNext * 60 * 60 * 1000);
                
                // Calculate cost for one minimum order
                const cost = (unitsPerPurchase / 1000.0) * rates[metricName];
                
                // Calculate total cost for all orders needed
                const totalCost = (Math.min(needed, totalOrders * unitsPerPurchase) / 1000.0) * rates[metricName];
                
                return {
                    timeUntilNext: hoursUntilNext,
                    nextPurchaseTime: nextPurchaseTime,
                    units: unitsPerPurchase, // Always minimum
                    cost: cost, // Cost for one order
                    totalCost: totalCost, // Total cost for all orders
                    purchasesCount: totalOrders,
                    totalUnitsNeeded: needed
                };
            }
            
            // If target completion time is set, use that as the maximum time remaining
            let hoursToViewsGoal = 0;
            let hoursToLikesGoal = 0;
            let hoursToCommentsGoal = 0;
            let hoursToCommentLikesGoal = 0;
            
            if (isTargetOverdue) {
                // Target is overdue - set all to negative/zero to show "Past due"
                hoursToViewsGoal = viewsNeeded > 0 ? -1 : 0;
                hoursToLikesGoal = likesNeeded > 0 ? -1 : 0;
                hoursToCommentsGoal = commentsNeeded > 0 ? -1 : 0;
                hoursToCommentLikesGoal = commentLikesNeeded > 0 ? -1 : 0;
            } else if (targetCompletionTime && hoursToTarget > 0) {
                // Use target completion time as the limit
                hoursToViewsGoal = Math.min(hoursToTarget, combinedViewsPerHour > 0 ? viewsNeeded / combinedViewsPerHour : hoursToTarget);
                hoursToLikesGoal = Math.min(hoursToTarget, combinedLikesPerHour > 0 ? likesNeeded / combinedLikesPerHour : hoursToTarget);
                hoursToCommentsGoal = Math.min(hoursToTarget, combinedCommentsPerHour > 0 ? commentsNeeded / combinedCommentsPerHour : hoursToTarget);
                hoursToCommentLikesGoal = Math.min(hoursToTarget, commentLikesPerHour > 0 ? commentLikesNeeded / commentLikesPerHour : hoursToTarget);
            } else {
                // Fallback to rate-based calculation
                hoursToViewsGoal = combinedViewsPerHour > 0 ? viewsNeeded / combinedViewsPerHour : 0;
                hoursToLikesGoal = combinedLikesPerHour > 0 ? likesNeeded / combinedLikesPerHour : 0;
                hoursToCommentsGoal = combinedCommentsPerHour > 0 ? commentsNeeded / combinedCommentsPerHour : 0;
                hoursToCommentLikesGoal = commentLikesPerHour > 0 ? commentLikesNeeded / commentLikesPerHour : 0;
            }
            
            // Check for saved next purchase times first (persistent across refreshes)
            const savedNextViewsTime = videoData.next_views_purchase_time ? new Date(videoData.next_views_purchase_time) : null;
            const savedNextLikesTime = videoData.next_likes_purchase_time ? new Date(videoData.next_likes_purchase_time) : null;
            const savedNextCommentsTime = videoData.next_comments_purchase_time ? new Date(videoData.next_comments_purchase_time) : null;
            const savedNextCommentLikesTime = videoData.next_comment_likes_purchase_time ? new Date(videoData.next_comment_likes_purchase_time) : null;
            
            // Use saved times if they're still in the future OR recently expired (within 10 minutes)
            // This gives the bot time to place orders before recalculating
            const GRACE_PERIOD_MS = 10 * 60 * 1000; // 10 minutes
            
            const isRecentlyExpired = (savedTime) => {
                if (!savedTime) return false;
                const expiredAgo = now - savedTime;
                return expiredAgo >= 0 && expiredAgo <= GRACE_PERIOD_MS;
            };
            
            let nextViewsPurchaseTime = (savedNextViewsTime && (savedNextViewsTime > now || isRecentlyExpired(savedNextViewsTime))) ? savedNextViewsTime : null;
            let nextLikesPurchaseTime = (savedNextLikesTime && (savedNextLikesTime > now || isRecentlyExpired(savedNextLikesTime))) ? savedNextLikesTime : null;
            let nextCommentsPurchaseTime = (savedNextCommentsTime && (savedNextCommentsTime > now || isRecentlyExpired(savedNextCommentsTime))) ? savedNextCommentsTime : null;
            let nextCommentLikesPurchaseTime = (savedNextCommentLikesTime && (savedNextCommentLikesTime > now || isRecentlyExpired(savedNextCommentLikesTime))) ? savedNextCommentLikesTime : null;
            
            // Calculate next purchase info for each metric (only if we don't have saved times)
            let nextViewsPurchase = null;
            let nextLikesPurchase = null;
            let nextCommentsPurchase = null;
            let nextCommentLikesPurchase = null;
            
            // Only calculate if we need to (no saved time or saved time has passed)
            if (targetCompletionTime && hoursToTarget > 0) {
                if (!nextViewsPurchaseTime) {
                    nextViewsPurchase = calculateNextPurchase('views', viewsNeeded, hoursToTarget, combinedViewsPerHour, minimums.views);
                    if (nextViewsPurchase) {
                        nextViewsPurchaseTime = nextViewsPurchase.nextPurchaseTime;
                        // Save to progress (will be saved when video data updates via API)
                        videoData.next_views_purchase_time = nextViewsPurchaseTime.toISOString();
                        // Save immediately via API
                        saveNextPurchaseTime(videoUrl, 'views', nextViewsPurchaseTime.toISOString());
                    }
                } else {
                    // Use saved time to create purchase info for display
                    const hoursUntilNext = (nextViewsPurchaseTime - now) / (1000 * 60 * 60);
                    if (hoursUntilNext > 0 && viewsNeeded > 0) {
                        const unitsPerPurchase = minimums.views;
                        const ordersNeeded = Math.ceil(viewsNeeded / unitsPerPurchase);
                        const cost = (unitsPerPurchase / 1000.0) * rates.views;
                        const totalCost = (Math.min(viewsNeeded, ordersNeeded * unitsPerPurchase) / 1000.0) * rates.views;
                        nextViewsPurchase = {
                            timeUntilNext: hoursUntilNext,
                            nextPurchaseTime: nextViewsPurchaseTime,
                            units: unitsPerPurchase,
                            cost: cost,
                            totalCost: totalCost,
                            purchasesCount: ordersNeeded,
                            totalUnitsNeeded: viewsNeeded
                        };
                    }
                }
                
                if (!nextLikesPurchaseTime) {
                    nextLikesPurchase = calculateNextPurchase('likes', likesNeeded, hoursToTarget, combinedLikesPerHour, minimums.likes);
                    if (nextLikesPurchase) {
                        nextLikesPurchaseTime = nextLikesPurchase.nextPurchaseTime;
                        videoData.next_likes_purchase_time = nextLikesPurchaseTime.toISOString();
                        saveNextPurchaseTime(videoUrl, 'likes', nextLikesPurchaseTime.toISOString());
                    }
                } else {
                    const hoursUntilNext = (nextLikesPurchaseTime - now) / (1000 * 60 * 60);
                    if (hoursUntilNext > 0 && likesNeeded > 0) {
                        const unitsPerPurchase = minimums.likes;
                        const ordersNeeded = Math.ceil(likesNeeded / unitsPerPurchase);
                        const cost = (unitsPerPurchase / 1000.0) * rates.likes;
                        const totalCost = (Math.min(likesNeeded, ordersNeeded * unitsPerPurchase) / 1000.0) * rates.likes;
                        nextLikesPurchase = {
                            timeUntilNext: hoursUntilNext,
                            nextPurchaseTime: nextLikesPurchaseTime,
                            units: unitsPerPurchase,
                            cost: cost,
                            totalCost: totalCost,
                            purchasesCount: ordersNeeded,
                            totalUnitsNeeded: likesNeeded
                        };
                    }
                }
                
                if (!nextCommentsPurchaseTime) {
                    nextCommentsPurchase = calculateNextPurchase('comments', commentsNeeded, hoursToTarget, combinedCommentsPerHour, minimums.comments);
                    if (nextCommentsPurchase) {
                        nextCommentsPurchaseTime = nextCommentsPurchase.nextPurchaseTime;
                        videoData.next_comments_purchase_time = nextCommentsPurchaseTime.toISOString();
                        saveNextPurchaseTime(videoUrl, 'comments', nextCommentsPurchaseTime.toISOString());
                    }
                } else {
                    const hoursUntilNext = (nextCommentsPurchaseTime - now) / (1000 * 60 * 60);
                    if (hoursUntilNext > 0 && commentsNeeded > 0) {
                        const unitsPerPurchase = minimums.comments;
                        const ordersNeeded = Math.ceil(commentsNeeded / unitsPerPurchase);
                        const cost = (unitsPerPurchase / 1000.0) * rates.comments;
                        const totalCost = (Math.min(commentsNeeded, ordersNeeded * unitsPerPurchase) / 1000.0) * rates.comments;
                        nextCommentsPurchase = {
                            timeUntilNext: hoursUntilNext,
                            nextPurchaseTime: nextCommentsPurchaseTime,
                            units: unitsPerPurchase,
                            cost: cost,
                            totalCost: totalCost,
                            purchasesCount: ordersNeeded,
                            totalUnitsNeeded: commentsNeeded
                        };
                    }
                }
                
                if (!nextCommentLikesPurchaseTime) {
                    nextCommentLikesPurchase = calculateNextPurchase('comment_likes', commentLikesNeeded, hoursToTarget, commentLikesPerHour, minimums.comment_likes);
                    if (nextCommentLikesPurchase) {
                        nextCommentLikesPurchaseTime = nextCommentLikesPurchase.nextPurchaseTime;
                        videoData.next_comment_likes_purchase_time = nextCommentLikesPurchaseTime.toISOString();
                        saveNextPurchaseTime(videoUrl, 'comment_likes', nextCommentLikesPurchaseTime.toISOString());
                    }
                } else {
                    const hoursUntilNext = (nextCommentLikesPurchaseTime - now) / (1000 * 60 * 60);
                    if (hoursUntilNext > 0 && commentLikesNeeded > 0) {
                        const unitsPerPurchase = minimums.comment_likes;
                        const ordersNeeded = Math.ceil(commentLikesNeeded / unitsPerPurchase);
                        const cost = (unitsPerPurchase / 1000.0) * rates.comment_likes;
                        const totalCost = (Math.min(commentLikesNeeded, ordersNeeded * unitsPerPurchase) / 1000.0) * rates.comment_likes;
                        nextCommentLikesPurchase = {
                            timeUntilNext: hoursUntilNext,
                            nextPurchaseTime: nextCommentLikesPurchaseTime,
                            units: unitsPerPurchase,
                            cost: cost,
                            totalCost: totalCost,
                            purchasesCount: ordersNeeded,
                            totalUnitsNeeded: commentLikesNeeded
                        };
                    }
                }
            }
            
            // Fallback: Calculate next purchase times based on purchase schedule if still no times
            if (!nextViewsPurchaseTime || !nextLikesPurchaseTime || !nextCommentsPurchaseTime || !nextCommentLikesPurchaseTime) {
                const nextOrders = videoData.next_orders || [];
                
                // Find next scheduled purchases
                for (const order of nextOrders) {
                    const orderTime = order.time_seconds ? (startTime.getTime() + order.time_seconds * 1000) : null;
                    if (orderTime && orderTime > now.getTime()) {
                        if (order.service === 'views' && !nextViewsPurchaseTime) {
                            nextViewsPurchaseTime = new Date(orderTime);
                            videoData.next_views_purchase_time = nextViewsPurchaseTime.toISOString();
                            saveNextPurchaseTime(videoUrl, 'views', nextViewsPurchaseTime.toISOString());
                        } else if (order.service === 'likes' && !nextLikesPurchaseTime) {
                            nextLikesPurchaseTime = new Date(orderTime);
                            videoData.next_likes_purchase_time = nextLikesPurchaseTime.toISOString();
                            saveNextPurchaseTime(videoUrl, 'likes', nextLikesPurchaseTime.toISOString());
                        } else if (order.service === 'comments' && !nextCommentsPurchaseTime) {
                            nextCommentsPurchaseTime = new Date(orderTime);
                            videoData.next_comments_purchase_time = nextCommentsPurchaseTime.toISOString();
                            saveNextPurchaseTime(videoUrl, 'comments', nextCommentsPurchaseTime.toISOString());
                        } else if (order.service === 'comment_likes' && !nextCommentLikesPurchaseTime) {
                            nextCommentLikesPurchaseTime = new Date(orderTime);
                            videoData.next_comment_likes_purchase_time = nextCommentLikesPurchaseTime.toISOString();
                            saveNextPurchaseTime(videoUrl, 'comment_likes', nextCommentLikesPurchaseTime.toISOString());
                        }
                    }
                }
            }
            
            // Format time remaining helper with seconds
            function formatTimeRemaining(hours) {
                if (hours < 0) return 'Past due';
                if (hours <= 0 || !isFinite(hours)) return 'N/A';
                const totalSeconds = Math.floor(hours * 3600);
                const days = Math.floor(totalSeconds / (24 * 3600));
                const remainingAfterDays = totalSeconds % (24 * 3600);
                const hoursVal = Math.floor(remainingAfterDays / 3600);
                const remainingAfterHours = remainingAfterDays % 3600;
                const minutes = Math.floor(remainingAfterHours / 60);
                const seconds = remainingAfterHours % 60;
                
                if (days > 0) {
                    return days + 'd ' + hoursVal + 'h ' + minutes + 'm';
                } else if (hoursVal > 0) {
                    return hoursVal + 'h ' + minutes + 'm ' + seconds + 's';
                } else if (minutes > 0) {
                    return minutes + 'm ' + seconds + 's';
                } else {
                    return seconds + 's';
                }
            }
            
            // Format time remaining with seconds (for countdowns that need real-time updates)
            function formatTimeRemainingWithSeconds(totalSeconds) {
                if (totalSeconds < 0) return 'Past due';
                if (totalSeconds <= 0 || !isFinite(totalSeconds)) return 'N/A';
                const days = Math.floor(totalSeconds / (24 * 3600));
                const remainingAfterDays = totalSeconds % (24 * 3600);
                const hours = Math.floor(remainingAfterDays / 3600);
                const remainingAfterHours = remainingAfterDays % 3600;
                const minutes = Math.floor(remainingAfterHours / 60);
                const seconds = remainingAfterHours % 60;
                
                if (days > 0) {
                    return days + 'd ' + hours + 'h ' + minutes + 'm';
                } else if (hours > 0) {
                    return hours + 'h ' + minutes + 'm ' + seconds + 's';
                } else if (minutes > 0) {
                    return minutes + 'm ' + seconds + 's';
                } else {
                    return seconds + 's';
                }
            }
            
            const embedUrl = getTikTokEmbedUrl(videoUrl);
            const safeVideoUrl = JSON.stringify(videoUrl);
            // Escape URLs for HTML attributes - use split/join to avoid regex issues
            function escapeHtml(str) {
                if (!str) return '';
                return str.split('"').join('&quot;').split("'").join('&#39;');
            }
            const safeEmbedUrl = escapeHtml(embedUrl);
            const safeVideoUrlAttr = escapeHtml(videoUrl);
            // Sanitize for IDs - use split/join to avoid regex issues
            function sanitizeId(str) {
                if (!str) return '';
                let result = '';
                for (let i = 0; i < str.length; i++) {
                    const char = str[i];
                    if ((char >= 'a' && char <= 'z') || (char >= 'A' && char <= 'Z') || (char >= '0' && char <= '9')) {
                        result += char;
                    } else {
                        result += '_';
                    }
                }
                return result;
            }
            const safeVideoUrlId = sanitizeId(videoUrl);
            
            return `
                <div class="video-card">
                    <div class="video-header">
                        <div>
                            <div class="video-title">${displayName}</div>
                            <div class="video-id">${escapeTemplateLiteral(videoId || videoUrl)}</div>
                        </div>
                        <div style="display: flex; align-items: center; gap: 10px; flex-wrap: wrap;">
                            <div class="status-badge ${getStatusClass(overallProgress)}">
                                ${getStatusText(overallProgress)}
                            </div>
                            <button class="remove-video-btn" data-video-url="${safeVideoUrlAttr}" title="Remove video from process">
                                🗑️ Remove
                            </button>
                        </div>
                    </div>
                    
                    ${embedUrl ? `
                    <div class="video-embed-container">
                        <iframe 
                            src="${safeEmbedUrl}" 
                            allow="encrypted-media"
                            allowfullscreen
                            scrolling="no">
                        </iframe>
                    </div>
                    <div class="video-link-container">
                        <a href="${safeVideoUrlAttr}" target="_blank">Open on TikTok →</a>
                    </div>
                    ` : `
                    <div class="video-link-container">
                        <a href="${safeVideoUrlAttr}" target="_blank">View Video on TikTok →</a>
                    </div>
                    `}
                    
                    <div class="target-time-section">
                        <h3>🎯 Target Completion Time</h3>
                        <div style="margin-bottom: 15px;">
                            <div style="color: #b0b0b0; font-size: 0.9em; margin-bottom: 10px;">Quick Set (from now):</div>
                            <div class="target-input-group" style="margin-bottom: 10px;">
                                <input type="number" id="quick-hours-${safeVideoUrlId}" placeholder="Hours" min="0" max="999" style="padding: 10px 12px; background: #2a2a2a; border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; color: #fff; width: 100px; font-size: 14px;">
                                <span style="color: #b0b0b0;">:</span>
                                <input type="number" id="quick-minutes-${safeVideoUrlId}" placeholder="Minutes" min="0" max="59" style="padding: 10px 12px; background: #2a2a2a; border: 1px solid rgba(255,255,255,0.2); border-radius: 8px; color: #fff; width: 100px; font-size: 14px;">
                                <button class="quick-set-target-btn" data-video-url="${safeVideoUrlAttr}" data-hours-id="quick-hours-${safeVideoUrlId}" data-minutes-id="quick-minutes-${safeVideoUrlId}" style="background: #667eea; color: white; border: none; padding: 10px 20px; border-radius: 8px; cursor: pointer; font-weight: 600;">Quick Set</button>
                            </div>
                        </div>
                        <div style="border-top: 1px solid rgba(255,255,255,0.1); padding-top: 15px; margin-top: 15px;">
                            <div style="color: #b0b0b0; font-size: 0.9em; margin-bottom: 10px;">Or set exact date/time:</div>
                            <div class="target-input-group">
                                <input type="datetime-local" id="target-${safeVideoUrlId}" value="${currentTargetTime}">
                                <button class="set-target-btn" data-video-url="${safeVideoUrlAttr}" data-target-id="target-${safeVideoUrlId}">Set Target</button>
                            </div>
                        </div>
                        ${targetCompletionTime ? (function() {
                            try {
                                const targetStr = String(new Date(targetCompletionTime).toLocaleString()).replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
                                const remainingStr = timeRemaining ? ' | <strong>Time Remaining:</strong> ' + String(timeRemaining).replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;') : '';
                                return '<div class="target-display" style="margin-top: 15px;"><strong>Target:</strong> ' + targetStr + remainingStr + '</div>';
                            } catch(e) {
                                return '<div class="target-display" style="margin-top: 15px;"><strong>Target:</strong> Invalid Date</div>';
                            }
                        }()) : ''}
                    </div>
                    
                    <div class="metrics">
                        <div class="metric">
                            <div class="metric-label">Views</div>
                            <div class="metric-value">${formatNumber(totalViews)}</div>
                            <div class="metric-target">/ ${formatNumber(targetViews)} (${formatPercentage(totalViews, targetViews)})</div>
                            ${viewsOrdered > 0 ? `<div style="color: #667eea; font-size: 0.85em; margin-top: 3px;">📦 Orders placed: <strong>${viewsOrdersCount}</strong> (${formatNumber(viewsOrdered)} total ordered)</div>` : ''}
                            ${viewsCatchUp > 0 && targetCompletionTime ? `<div style="background: rgba(239, 68, 68, 0.1); border-radius: 6px; padding: 8px; margin-top: 8px; font-size: 0.85em; border: 1px solid rgba(239, 68, 68, 0.3);">
                                <div style="color: #ef4444; font-weight: 600; margin-bottom: 4px;">⚠️ Behind Schedule</div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Expected: <span style="color: #fff;">${formatNumber(Math.ceil(expectedViewsNow))}</span></div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Actual: <span style="color: #fff;">${formatNumber(totalViews)}</span></div>
                                <div style="color: #b0b0b0; margin-bottom: 6px;">Gap: <span style="color: #ef4444; font-weight: 600;">${formatNumber(viewsCatchUp)}</span></div>
                                <button class="catch-up-btn" data-video-url="${safeVideoUrlAttr}" data-metric="views" data-amount="${viewsCatchUp}" style="width: 100%; background: #ef4444; color: white; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 0.9em;">Catch Up (${formatNumber(viewsCatchUp)})</button>
                            </div>` : ''}
                            ${viewsNeeded > 0 && hoursToViewsGoal > 0 ? `<div style="color: #888; font-size: 0.85em; margin-top: 5px;" data-time-to-goal data-hours="${hoursToViewsGoal}" data-metric="views">⏱️ <span data-countdown-to-goal>${formatTimeRemaining(hoursToViewsGoal)}</span> to goal</div>` : viewsNeeded <= 0 ? `<div style="color: #10b981; font-size: 0.85em; margin-top: 5px;">✓ Target reached</div>` : viewsNeeded > 0 && isTargetOverdue ? `<div style="color: #ef4444; font-size: 0.85em; margin-top: 5px;">⚠️ Past due</div>` : ''}
                            ${nextViewsPurchase ? `<div style="background: rgba(102, 126, 234, 0.1); border-radius: 6px; padding: 8px; margin-top: 8px; font-size: 0.85em;">
                                <div style="color: #667eea; font-weight: 600; margin-bottom: 4px;">🛒 Next Purchase</div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Time: <span data-next-purchase data-purchase-time="${nextViewsPurchase.nextPurchaseTime.toISOString()}" data-metric="views" style="color: #fff;"><span data-countdown-display>${formatTimeRemaining(nextViewsPurchase.timeUntilNext)}</span></span></div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Units: <span style="color: #fff;">${formatNumber(nextViewsPurchase.units)}</span> (min order)</div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Orders: <span style="color: #fff;">${nextViewsPurchase.purchasesCount}x</span> (${formatNumber(nextViewsPurchase.purchasesCount * nextViewsPurchase.units)} total)</div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Expected total: <span style="color: #fff;">${formatNumber(expectedViewsToOrder)}</span></div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Already ordered: <span style="color: #10b981; font-weight: 600;">${formatNumber(viewsOrdered)}</span></div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Per order: <span style="color: #10b981; font-weight: 600;">$${nextViewsPurchase.cost.toFixed(4)}</span></div>
                                <div style="color: #b0b0b0; margin-bottom: 6px;">Total cost: <span style="color: #10b981; font-weight: 600;">$${nextViewsPurchase.totalCost.toFixed(4)}</span></div>
                                <button class="manual-order-btn" data-video-url="${safeVideoUrlAttr}" data-metric="views" data-minimum="50" style="width: 100%; background: #10b981; color: white; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 0.9em; margin-top: 4px;">📦 Manual Order</button>
                            </div>` : nextViewsPurchaseTime ? `<div style="color: #667eea; font-size: 0.85em; margin-top: 3px;" data-next-purchase data-purchase-time="${nextViewsPurchaseTime.toISOString()}" data-metric="views">🛒 Next purchase: <span data-countdown-display>${formatTimeRemaining((nextViewsPurchaseTime - now) / (1000 * 60 * 60))}</span></div>` : ''}
                            ${targetViews > 0 ? `<button class="manual-order-btn" data-video-url="${safeVideoUrlAttr}" data-metric="views" data-minimum="50" style="width: 100%; background: #10b981; color: white; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 0.85em; margin-top: 8px;">📦 Manual Order Views</button>` : ''}
                            <div class="progress-bar-container">
                                <div class="progress-bar" style="width: ${Math.min(viewsProgress, 100)}%">${formatPercentage(totalViews, targetViews)}</div>
                            </div>
                        </div>
                        
                        <div class="metric">
                            <div class="metric-label">Likes</div>
                            <div class="metric-value">${formatNumber(totalLikes)}</div>
                            <div class="metric-target">/ ${formatNumber(targetLikes)} (${formatPercentage(totalLikes, targetLikes)})</div>
                            ${likesOrdered > 0 ? `<div style="color: #667eea; font-size: 0.85em; margin-top: 3px;">📦 Orders placed: <strong>${likesOrdersCount}</strong> (${formatNumber(likesOrdered)} total ordered)</div>` : ''}
                            ${likesCatchUp > 0 && targetCompletionTime ? `<div style="background: rgba(239, 68, 68, 0.1); border-radius: 6px; padding: 8px; margin-top: 8px; font-size: 0.85em; border: 1px solid rgba(239, 68, 68, 0.3);">
                                <div style="color: #ef4444; font-weight: 600; margin-bottom: 4px;">⚠️ Behind Schedule</div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Expected: <span style="color: #fff;">${formatNumber(Math.ceil(expectedLikesNow))}</span></div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Actual: <span style="color: #fff;">${formatNumber(totalLikes)}</span></div>
                                <div style="color: #b0b0b0; margin-bottom: 6px;">Gap: <span style="color: #ef4444; font-weight: 600;">${formatNumber(likesCatchUp)}</span></div>
                                <button class="catch-up-btn" data-video-url="${safeVideoUrlAttr}" data-metric="likes" data-amount="${likesCatchUp}" style="width: 100%; background: #ef4444; color: white; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 0.9em;">Catch Up (${formatNumber(likesCatchUp)})</button>
                            </div>` : ''}
                            ${likesNeeded > 0 && hoursToLikesGoal > 0 ? `<div style="color: #888; font-size: 0.85em; margin-top: 5px;" data-time-to-goal data-hours="${hoursToLikesGoal}" data-metric="likes">⏱️ <span data-countdown-to-goal>${formatTimeRemaining(hoursToLikesGoal)}</span> to goal</div>` : likesNeeded <= 0 ? `<div style="color: #10b981; font-size: 0.85em; margin-top: 5px;">✓ Target reached</div>` : likesNeeded > 0 && isTargetOverdue ? `<div style="color: #ef4444; font-size: 0.85em; margin-top: 5px;">⚠️ Past due</div>` : likesNeeded > 0 && targetCompletionTime ? `<div style="color: #888; font-size: 0.85em; margin-top: 5px;" data-time-to-goal data-hours="${hoursToTarget}" data-metric="likes">⏱️ <span data-countdown-to-goal>${formatTimeRemaining(hoursToTarget)}</span> to goal</div>` : ''}
                            ${nextLikesPurchase ? `<div style="background: rgba(102, 126, 234, 0.1); border-radius: 6px; padding: 8px; margin-top: 8px; font-size: 0.85em;">
                                <div style="color: #667eea; font-weight: 600; margin-bottom: 4px;">🛒 Next Purchase</div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Time: <span data-next-purchase data-purchase-time="${nextLikesPurchase.nextPurchaseTime.toISOString()}" data-metric="likes" style="color: #fff;"><span data-countdown-display>${formatTimeRemaining(nextLikesPurchase.timeUntilNext)}</span></span></div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Units: <span style="color: #fff;">${formatNumber(nextLikesPurchase.units)}</span> (min order)</div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Orders: <span style="color: #fff;">${nextLikesPurchase.purchasesCount}x</span> (${formatNumber(nextLikesPurchase.purchasesCount * nextLikesPurchase.units)} total)</div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Expected total: <span style="color: #fff;">${formatNumber(expectedLikesToOrder)}</span></div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Already ordered: <span style="color: #10b981; font-weight: 600;">${formatNumber(likesOrdered)}</span></div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Per order: <span style="color: #10b981; font-weight: 600;">$${nextLikesPurchase.cost.toFixed(4)}</span></div>
                                <div style="color: #b0b0b0; margin-bottom: 6px;">Total cost: <span style="color: #10b981; font-weight: 600;">$${nextLikesPurchase.totalCost.toFixed(4)}</span></div>
                                <button class="manual-order-btn" data-video-url="${safeVideoUrlAttr}" data-metric="likes" data-minimum="10" style="width: 100%; background: #10b981; color: white; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 0.9em; margin-top: 4px;">📦 Manual Order</button>
                            </div>` : nextLikesPurchaseTime ? `<div style="color: #667eea; font-size: 0.85em; margin-top: 3px;" data-next-purchase data-purchase-time="${nextLikesPurchaseTime.toISOString()}" data-metric="likes">🛒 Next purchase: <span data-countdown-display>${formatTimeRemaining((nextLikesPurchaseTime - now) / (1000 * 60 * 60))}</span></div>` : ''}
                            ${targetLikes > 0 ? `<button class="manual-order-btn" data-video-url="${safeVideoUrlAttr}" data-metric="likes" data-minimum="10" style="width: 100%; background: #10b981; color: white; border: none; padding: 6px 12px; border-radius: 6px; cursor: pointer; font-weight: 600; font-size: 0.85em; margin-top: 8px;">📦 Manual Order Likes</button>` : ''}
                            <div class="progress-bar-container">
                                <div class="progress-bar" style="width: ${Math.min(likesProgress, 100)}%">${formatPercentage(totalLikes, targetLikes)}</div>
                            </div>
                        </div>
                        
                        <div class="metric">
                            <div class="metric-label">Comments</div>
                            <div class="metric-value">${totalComments}</div>
                            <div class="metric-target">/ ${targetComments} (${formatPercentage(totalComments, targetComments)})</div>
                            ${commentsOrdered > 0 ? `<div style="color: #667eea; font-size: 0.85em; margin-top: 3px;">📦 Orders placed: <strong>${commentsOrdersCount}</strong> (${formatNumber(commentsOrdered)} total ordered)</div>` : ''}
                            ${commentsNeeded > 0 && hoursToCommentsGoal > 0 ? `<div style="color: #888; font-size: 0.85em; margin-top: 5px;" data-time-to-goal data-hours="${hoursToCommentsGoal}" data-metric="comments">⏱️ <span data-countdown-to-goal>${formatTimeRemaining(hoursToCommentsGoal)}</span> to goal</div>` : commentsNeeded <= 0 ? `<div style="color: #10b981; font-size: 0.85em; margin-top: 5px;">✓ Target reached</div>` : commentsNeeded > 0 && isTargetOverdue ? `<div style="color: #ef4444; font-size: 0.85em; margin-top: 5px;">⚠️ Past due</div>` : commentsNeeded > 0 && targetCompletionTime ? `<div style="color: #888; font-size: 0.85em; margin-top: 5px;" data-time-to-goal data-hours="${hoursToTarget}" data-metric="comments">⏱️ <span data-countdown-to-goal>${formatTimeRemaining(hoursToTarget)}</span> to goal</div>` : ''}
                            ${nextCommentsPurchase ? `<div style="background: rgba(102, 126, 234, 0.1); border-radius: 6px; padding: 8px; margin-top: 8px; font-size: 0.85em;">
                                <div style="color: #667eea; font-weight: 600; margin-bottom: 4px;">🛒 Next Purchase</div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Time: <span data-next-purchase data-purchase-time="${nextCommentsPurchase.nextPurchaseTime.toISOString()}" data-metric="comments" style="color: #fff;"><span data-countdown-display>${formatTimeRemaining(nextCommentsPurchase.timeUntilNext)}</span></span></div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Units: <span style="color: #fff;">${formatNumber(nextCommentsPurchase.units)}</span> (min order)</div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Orders: <span style="color: #fff;">${nextCommentsPurchase.purchasesCount}x</span> (${formatNumber(nextCommentsPurchase.purchasesCount * nextCommentsPurchase.units)} total)</div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Expected total: <span style="color: #fff;">${formatNumber(expectedCommentsToOrder)}</span></div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Already ordered: <span style="color: #10b981; font-weight: 600;">${formatNumber(commentsOrdered)}</span></div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Per order: <span style="color: #10b981; font-weight: 600;">$${nextCommentsPurchase.cost.toFixed(4)}</span></div>
                                <div style="color: #b0b0b0;">Total cost: <span style="color: #10b981; font-weight: 600;">$${nextCommentsPurchase.totalCost.toFixed(4)}</span></div>
                            </div>` : nextCommentsPurchaseTime ? `<div style="color: #667eea; font-size: 0.85em; margin-top: 3px;" data-next-purchase data-purchase-time="${nextCommentsPurchaseTime.toISOString()}" data-metric="comments">🛒 Next purchase: <span data-countdown-display>${formatTimeRemaining((nextCommentsPurchaseTime - now) / (1000 * 60 * 60))}</span></div>` : ''}
                            <div class="progress-bar-container">
                                <div class="progress-bar" style="width: ${Math.min(commentsProgress, 100)}%">${formatPercentage(totalComments, targetComments)}</div>
                            </div>
                        </div>
                        
                        <div class="metric">
                            <div class="metric-label">Comment Likes</div>
                            <div class="metric-value">${commentLikesOrdered}</div>
                            <div class="metric-target">/ ${targetCommentLikes} (${formatPercentage(commentLikesOrdered, targetCommentLikes)})</div>
                            ${commentLikesOrdered > 0 ? `<div style="color: #667eea; font-size: 0.85em; margin-top: 3px;">📦 Orders placed: <strong>${commentLikesOrdersCount}</strong> (${formatNumber(commentLikesOrdered)} total ordered)</div>` : ''}
                            ${commentLikesNeeded > 0 && hoursToCommentLikesGoal > 0 ? `<div style="color: #888; font-size: 0.85em; margin-top: 5px;" data-time-to-goal data-hours="${hoursToCommentLikesGoal}" data-metric="comment_likes">⏱️ <span data-countdown-to-goal>${formatTimeRemaining(hoursToCommentLikesGoal)}</span> to goal</div>` : commentLikesNeeded <= 0 ? `<div style="color: #10b981; font-size: 0.85em; margin-top: 5px;">✓ Target reached</div>` : commentLikesNeeded > 0 && isTargetOverdue ? `<div style="color: #ef4444; font-size: 0.85em; margin-top: 5px;">⚠️ Past due</div>` : commentLikesNeeded > 0 && targetCompletionTime ? `<div style="color: #888; font-size: 0.85em; margin-top: 5px;" data-time-to-goal data-hours="${hoursToTarget}" data-metric="comment_likes">⏱️ <span data-countdown-to-goal>${formatTimeRemaining(hoursToTarget)}</span> to goal</div>` : ''}
                            ${nextCommentLikesPurchase ? `<div style="background: rgba(102, 126, 234, 0.1); border-radius: 6px; padding: 8px; margin-top: 8px; font-size: 0.85em;">
                                <div style="color: #667eea; font-weight: 600; margin-bottom: 4px;">🛒 Next Purchase</div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Time: <span data-next-purchase data-purchase-time="${nextCommentLikesPurchase.nextPurchaseTime.toISOString()}" data-metric="comment_likes" style="color: #fff;"><span data-countdown-display>${formatTimeRemaining(nextCommentLikesPurchase.timeUntilNext)}</span></span></div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Units: <span style="color: #fff;">${formatNumber(nextCommentLikesPurchase.units)}</span> (min order)</div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Orders: <span style="color: #fff;">${nextCommentLikesPurchase.purchasesCount}x</span> (${formatNumber(nextCommentLikesPurchase.purchasesCount * nextCommentLikesPurchase.units)} total)</div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Expected total: <span style="color: #fff;">${formatNumber(expectedCommentLikesToOrder)}</span></div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Already ordered: <span style="color: #10b981; font-weight: 600;">${formatNumber(commentLikesOrdered)}</span></div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Per order: <span style="color: #10b981; font-weight: 600;">$${nextCommentLikesPurchase.cost.toFixed(4)}</span></div>
                                <div style="color: #b0b0b0;">Total cost: <span style="color: #10b981; font-weight: 600;">$${nextCommentLikesPurchase.totalCost.toFixed(4)}</span></div>
                            </div>` : nextCommentLikesPurchaseTime ? `<div style="color: #667eea; font-size: 0.85em; margin-top: 3px;" data-next-purchase data-purchase-time="${nextCommentLikesPurchaseTime.toISOString()}" data-metric="comment_likes">🛒 Next purchase: <span data-countdown-display>${formatTimeRemaining((nextCommentLikesPurchaseTime - now) / (1000 * 60 * 60))}</span></div>` : ''}
                            <div class="progress-bar-container">
                                <div class="progress-bar" style="width: ${Math.min(commentLikesProgress, 100)}%">${formatPercentage(commentLikesOrdered, targetCommentLikes)}</div>
                            </div>
                            ${commentLikesNeeded > 0 && totalComments > 0 ? `<div style="margin-top: 10px;"><button class="select-comments-btn" data-video-url="${safeVideoUrlAttr}" style="background: #667eea; color: white; border: none; padding: 8px 16px; border-radius: 6px; cursor: pointer; font-size: 0.9em;">📝 Select Comments to Boost</button></div>` : commentLikesNeeded > 0 && totalComments === 0 ? `<div style="margin-top: 10px; color: #888; font-size: 0.85em;">No comments yet. Comments must be added before ordering likes.</div>` : ''}
                        </div>
                    </div>
                    
                    ${(() => {
                        const growthHistory = videoData.growth_history || [];
                        if (growthHistory.length > 0) {
                            // Sanitize for IDs - use loop to avoid regex issues
                            function sanitizeId(str) {
                                if (!str) return '';
                                let result = '';
                                for (let i = 0; i < str.length; i++) {
                                    const char = str[i];
                                    if ((char >= 'a' && char <= 'z') || (char >= 'A' && char <= 'Z') || (char >= '0' && char <= '9')) {
                                        result += char;
                                    } else {
                                        result += '_';
                                    }
                                }
                                return result;
                            }
                            const safeVideoUrlId = sanitizeId(videoUrl);
                            const chartId = 'growth-chart-' + safeVideoUrlId;
                            const chartDataId = 'chart-data-' + safeVideoUrlId;
                            const labels = growthHistory.map(h => {
                                try {
                                    const date = new Date(h.timestamp);
                                    const label = date.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
                                    // Escape any special characters that could break template literals
                                    return String(label || '').replace(/`/g, '\\`').replace(/\$/g, '\\$');
                                } catch (e) {
                                    return '';
                                }
                            });
                            const viewsData = growthHistory.map(h => h.views);
                            const likesData = growthHistory.map(h => h.likes);
                            const commentsData = growthHistory.map(h => h.comments);
                            
                            // Calculate expected growth data
                            const startTime = videoData.start_time ? new Date(videoData.start_time) : (growthHistory.length > 0 ? new Date(growthHistory[0].timestamp) : new Date());
                            const targetCompletionTime = videoData.target_completion_time || videoData.target_completion_datetime;
                            const targetViews = videoData.target_views || 4000;
                            const targetLikes = videoData.target_likes || 125;
                            const targetComments = videoData.target_comments || 7;
                            
                            // Get initial values from first growth history entry or videoData
                            const initialViews = growthHistory.length > 0 ? growthHistory[0].views : (videoData.initial_views || 0);
                            const initialLikes = growthHistory.length > 0 ? growthHistory[0].likes : (videoData.initial_likes || 0);
                            const initialComments = growthHistory.length > 0 ? growthHistory[0].comments : 0;
                            
                            // Extend labels and data to show full timeline up to target completion time
                            let extendedLabels = [...labels];
                            let extendedViewsData = [...viewsData];
                            let extendedLikesData = [...likesData];
                            let extendedCommentsData = [...commentsData];
                            
                            // Calculate expected growth for full timeline
                            const expectedViewsData = [];
                            const expectedLikesData = [];
                            const expectedCommentsData = [];
                            
                            if (targetCompletionTime) {
                                const targetTime = new Date(targetCompletionTime);
                                const totalDuration = targetTime - startTime;
                                const now = new Date();
                                
                                // Get the last timestamp from growth history, or use start time
                                const lastHistoryTime = growthHistory.length > 0 ? new Date(growthHistory[growthHistory.length - 1].timestamp) : startTime;
                                
                                // Create timeline points: from start to target, with points every 30 minutes
                                const timelinePoints = [];
                                const intervalMs = 30 * 60 * 1000; // 30 minutes
                                let currentTime = new Date(startTime);
                                
                                // Add start point
                                timelinePoints.push(new Date(currentTime));
                                
                                // Add intermediate points every 30 minutes up to target
                                while (currentTime < targetTime) {
                                    currentTime = new Date(Math.min(currentTime.getTime() + intervalMs, targetTime.getTime()));
                                    timelinePoints.push(new Date(currentTime));
                                }
                                
                                // Ensure target point is included
                                if (timelinePoints[timelinePoints.length - 1].getTime() !== targetTime.getTime()) {
                                    timelinePoints.push(new Date(targetTime));
                                }
                                
                                // Create labels for all timeline points
                                extendedLabels = timelinePoints.map(t => {
                                    try {
                                        const date = new Date(t);
                                        const label = date.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
                                        return String(label || '').replace(/`/g, '\\`').replace(/\$/g, '\\$');
                                    } catch (e) {
                                        return '';
                                    }
                                });
                                
                                // Create a map of existing data points by timestamp (for matching)
                                const dataPointMap = new Map();
                                for (let i = 0; i < growthHistory.length; i++) {
                                    const timestamp = new Date(growthHistory[i].timestamp).getTime();
                                    dataPointMap.set(timestamp, {
                                        views: viewsData[i],
                                        likes: likesData[i],
                                        comments: commentsData[i]
                                    });
                                }
                                
                                // Calculate expected values and match actual data for all timeline points
                                for (let i = 0; i < timelinePoints.length; i++) {
                                    const currentTime = timelinePoints[i];
                                    const currentTimeMs = currentTime.getTime();
                                    const elapsed = currentTime - startTime;
                                    
                                    // Calculate expected values
                                    if (totalDuration > 0 && elapsed >= 0) {
                                        // Linear interpolation: initial + (target - initial) * (elapsed / totalDuration)
                                        const progress = Math.min(1, Math.max(0, elapsed / totalDuration));
                                        expectedViewsData.push(initialViews + (targetViews - initialViews) * progress);
                                        expectedLikesData.push(initialLikes + (targetLikes - initialLikes) * progress);
                                        expectedCommentsData.push(initialComments + (targetComments - initialComments) * progress);
                                    } else {
                                        // Before start time, use initial values
                                        expectedViewsData.push(initialViews);
                                        expectedLikesData.push(initialLikes);
                                        expectedCommentsData.push(initialComments);
                                    }
                                    
                                    // Match actual data if available (within 15 minutes tolerance)
                                    let matched = false;
                                    for (const [timestamp, data] of dataPointMap.entries()) {
                                        if (Math.abs(timestamp - currentTimeMs) < 15 * 60 * 1000) {
                                            extendedViewsData.push(data.views);
                                            extendedLikesData.push(data.likes);
                                            extendedCommentsData.push(data.comments);
                                            matched = true;
                                            break;
                                        }
                                    }
                                    
                                    if (!matched) {
                                        // No matching data point - use null (Chart.js will skip null values)
                                        extendedViewsData.push(null);
                                        extendedLikesData.push(null);
                                        extendedCommentsData.push(null);
                                    }
                                }
                            } else {
                                // No target time - use existing labels and data as-is
                                // Expected = initial (flat line)
                                for (let i = 0; i < labels.length; i++) {
                                    expectedViewsData.push(initialViews);
                                    expectedLikesData.push(initialLikes);
                                    expectedCommentsData.push(initialComments);
                                }
                            }
                            
                            // Store data in JSON script tag - use JSON.stringify in a way that works
                            const chartDataStr = JSON.stringify({
                                labels: extendedLabels,
                                viewsData: extendedViewsData,
                                likesData: extendedLikesData,
                                commentsData: extendedCommentsData,
                                expectedViewsData: expectedViewsData,
                                expectedLikesData: expectedLikesData,
                                expectedCommentsData: expectedCommentsData,
                                chartId: chartId
                            });
                            
                            // Properly escape JSON for HTML attribute - escape all special characters
                            function escapeHtmlAttr(str) {
                                if (!str) return '';
                                return String(str)
                                    .replace(/&/g, '&amp;')
                                    .replace(/"/g, '&quot;')
                                    .replace(/'/g, '&#39;')
                                    .replace(/</g, '&lt;')
                                    .replace(/>/g, '&gt;')
                                    .replace(/\\n/g, '&#10;')
                                    .replace(/\\r/g, '&#13;');
                            }
                            
                            // Use a data attribute instead of script tag content to avoid parsing issues
                            return '<div class="growth-chart-section">' +
                                '<h3>📈 Growth Tracking (Actual vs Expected)</h3>' +
                                '<div class="chart-container">' +
                                '<canvas id="' + chartId + '"></canvas>' +
                                '</div>' +
                                '<div class="chart-legend">' +
                                '<div class="chart-legend-item">' +
                                '<div class="chart-legend-color" style="background: rgba(102, 126, 234, 0.8);"></div>' +
                                '<span>Views (Actual)</span>' +
                                '</div>' +
                                '<div class="chart-legend-item">' +
                                '<div class="chart-legend-color" style="background: rgba(102, 126, 234, 0.3); border: 1px dashed rgba(102, 126, 234, 0.8);"></div>' +
                                '<span>Views (Expected)</span>' +
                                '</div>' +
                                '<div class="chart-legend-item">' +
                                '<div class="chart-legend-color" style="background: rgba(16, 185, 129, 0.8);"></div>' +
                                '<span>Likes (Actual)</span>' +
                                '</div>' +
                                '<div class="chart-legend-item">' +
                                '<div class="chart-legend-color" style="background: rgba(16, 185, 129, 0.3); border: 1px dashed rgba(16, 185, 129, 0.8);"></div>' +
                                '<span>Likes (Expected)</span>' +
                                '</div>' +
                                '<div class="chart-legend-item">' +
                                '<div class="chart-legend-color" style="background: rgba(239, 68, 68, 0.8);"></div>' +
                                '<span>Comments (Actual)</span>' +
                                '</div>' +
                                '<div class="chart-legend-item">' +
                                '<div class="chart-legend-color" style="background: rgba(239, 68, 68, 0.3); border: 1px dashed rgba(239, 68, 68, 0.8);"></div>' +
                                '<span>Comments (Expected)</span>' +
                                '</div>' +
                                '</div>' +
                                '<div id="' + chartDataId + '" data-chart-data="' + escapeHtmlAttr(chartDataStr) + '" style="display:none;"></div>' +
                                '</div>';
                        }
                        return '';
                    })()}
                    
                    <div class="milestones-section">
                        <h3>📋 Milestones & Actions</h3>
                        
                        <div class="milestone-card ${currentTotalViews >= commentsMilestone ? (hasCommentsOrdered ? 'milestone-completed' : 'milestone-ready') : 'milestone-pending'}">
                            <div class="milestone-header">
                                <span class="milestone-icon">💬</span>
                                <span class="milestone-title">Comments Milestone</span>
                                <span class="milestone-status">
                                    ${currentTotalViews >= commentsMilestone ? (hasCommentsOrdered ? '✓ Ordered' : '⚠ Ready to Order') : '⏳ Pending'}
                                </span>
                            </div>
                            <div class="milestone-details">
                                <div class="milestone-info">
                                    <strong>Trigger:</strong> ${commentsMilestone.toLocaleString()} total views
                                    <br>
                                    <strong>Current:</strong> ${formatNumber(currentTotalViews)} views
                                    ${currentTotalViews < commentsMilestone ? `
                                    <br>
                                    <strong>Views Needed:</strong> ${formatNumber(viewsNeededForComments)} views
                                    ${hoursUntilComments > 0 ? (function() {
                                        const timeStr = hoursUntilComments < 1 
                                            ? Math.round(hoursUntilComments * 60) + ' minutes' 
                                            : hoursUntilComments.toFixed(1) + ' hours';
                                        return '<br><strong>Estimated Time:</strong> ' + timeStr;
                                    }()) : ''}
                                    ` : ''}
                                </div>
                                ${savedComments.length > 0 ? `
                                <div class="milestone-comments">
                                    <strong>Saved Comments (${savedComments.length}):</strong>
                                    <ol class="comments-list">
                                        ${savedComments.map(c => `<li>${String(c || '').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/&/g, '&amp;')}</li>`).join('')}
                                    </ol>
                                    ${!hasCommentsOrdered && currentTotalViews >= commentsMilestone ? `
                                    <button class="order-comments-btn" data-video-url="${safeVideoUrlAttr}" style="margin-top: 15px; padding: 10px 20px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border: none; border-radius: 8px; color: white; font-weight: 600; cursor: pointer; font-size: 14px; width: 100%;">
                                        🚀 Order Comments Now
                                    </button>
                                    ` : ''}
                                </div>
                                ` : hasCommentsOrdered ? `
                                <div class="milestone-comments">
                                    <strong>Status:</strong> Comments have been ordered
                                </div>
                                ` : currentTotalViews >= commentsMilestone ? `
                                <div class="milestone-comments">
                                    <strong>Status:</strong> ⚠️ No comments saved. Please add comments below to order.
                                </div>
                                ` : `
                                <div class="milestone-comments">
                                    <strong>Status:</strong> No comments saved yet. Bot will prompt when milestone is reached.
                                </div>
                                `}
                            </div>
                        </div>
                        
                        <div class="milestone-card ${currentTotalViews >= commentLikesMilestone ? (hasCommentLikesOrdered ? 'milestone-completed' : 'milestone-ready') : 'milestone-pending'}">
                            <div class="milestone-header">
                                <span class="milestone-icon">❤️</span>
                                <span class="milestone-title">Comment Likes Milestone</span>
                                <span class="milestone-status">
                                    ${currentTotalViews >= commentLikesMilestone ? (hasCommentLikesOrdered ? '✓ Ordered' : '⚠ Ready to Order') : '⏳ Pending'}
                                </span>
                            </div>
                            <div class="milestone-details">
                                <div class="milestone-info">
                                    <strong>Trigger:</strong> ${commentLikesMilestone.toLocaleString()} total views
                                    <br>
                                    <strong>Current:</strong> ${formatNumber(currentTotalViews)} views
                                    ${currentTotalViews < commentLikesMilestone ? `
                                    <br>
                                    <strong>Views Needed:</strong> ${formatNumber(viewsNeededForCommentLikes)} views
                                    ${hoursUntilCommentLikes > 0 ? (function() {
                                        try {
                                            const timeStr = hoursUntilCommentLikes < 1 
                                                ? Math.round(hoursUntilCommentLikes * 60) + ' minutes' 
                                                : hoursUntilCommentLikes.toFixed(1) + ' hours';
                                            return '<br><strong>Estimated Time:</strong> ' + String(timeStr).replace(/"/g, '&quot;').replace(/'/g, '&#39;');
                                        } catch(e) {
                                            return '';
                                        }
                                    }()) : ''}
                                    ` : ''}
                                </div>
                                ${commentUsername ? `
                                <div class="milestone-username">
                                    <strong>Target Username:</strong> @${commentUsername}
                                </div>
                                ` : hasCommentLikesOrdered ? `
                                <div class="milestone-username">
                                    <strong>Status:</strong> Comment likes have been ordered
                                </div>
                                ` : currentTotalViews >= commentLikesMilestone ? `
                                <div class="milestone-username">
                                    <strong>Status:</strong> Waiting for username input. Bot will prompt when ready.
                                </div>
                                ` : `
                                <div class="milestone-username">
                                    <strong>Status:</strong> Username will be requested when milestone is reached.
                                </div>
                                `}
                            </div>
                        </div>
                    </div>
                    
                    <div class="comments-editor-section ${hasCommentsOrdered ? 'comments-editor-disabled' : ''}">
                        <h3>💬 Edit Comments (${hasCommentsOrdered ? 'Locked' : 'Editable'})</h3>
                        <textarea 
                            id="comments-${safeVideoUrlId}" 
                            class="comments-textarea" 
                            placeholder="Enter 10 comments, one per line..."
                            ${hasCommentsOrdered ? 'disabled' : ''}
                        >${savedComments.length > 0 ? savedComments.map(c => String(c || '').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/&/g, '&amp;')).join(String.fromCharCode(10)) : ''}</textarea>
                        <div class="comments-help">
                            Enter exactly 10 comments, one per line. These will be used when the milestone is reached.
                        </div>
                        <button 
                            class="comments-save-btn" 
                            data-video-url="${safeVideoUrlAttr}"
                            data-textarea-id="comments-${safeVideoUrlId}"
                            ${hasCommentsOrdered ? 'disabled' : ''}
                        >
                            ${hasCommentsOrdered ? 'Comments Already Ordered' : 'Save Comments'}
                        </button>
                        <div id="comments-status-${safeVideoUrlId}" class="comments-save-status"></div>
                    </div>
                    
                    <div class="live-activity-section" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 12px; margin-bottom: 30px; color: white;">
                        <h3 style="margin: 0 0 15px 0; color: white; font-size: 18px;">⚡ Live Activity Status</h3>
                        ${(function() {
                            const currentActivity = videoData.current_activity || {};
                            const activityStatus = currentActivity.status || 'idle';
                            const lastUpdated = currentActivity.last_updated ? new Date(currentActivity.last_updated) : null;
                            const now = new Date();
                            const timeSinceUpdate = lastUpdated ? Math.floor((now - lastUpdated) / 1000) : null;
                            
                            // Calculate target completion time variables
                            const targetCompletionTimeLocal = videoData.target_completion_time || videoData.target_completion_datetime;
                            let hoursToTargetLocal = 0;
                            let isTargetOverdueLocal = false;
                            if (targetCompletionTimeLocal) {
                                const targetTime = new Date(targetCompletionTimeLocal);
                                hoursToTargetLocal = Math.max(0, (targetTime - now) / (1000 * 60 * 60));
                                isTargetOverdueLocal = hoursToTargetLocal <= 0;
                            }
                            
                            // Calculate next action time if waiting
                            let nextActionTime = null;
                            let countdownSeconds = 0;
                            if (activityStatus === 'waiting' && currentActivity.next_action_time) {
                                nextActionTime = new Date(currentActivity.next_action_time);
                                countdownSeconds = Math.max(0, Math.floor((nextActionTime - now) / 1000));
                            }
                            
                            // Calculate combined progress rate (orders + organic growth)
                            let combinedViewsPerHour = 0;
                            const growthHistory = videoData.growth_history || [];
                            if (growthHistory.length >= 2) {
                                const recent = growthHistory.slice(-5);
                                const oldest = recent[0];
                                const newest = recent[recent.length - 1];
                                const timeDiff = (new Date(newest.timestamp) - new Date(oldest.timestamp)) / (1000 * 60 * 60);
                                const viewsDiff = newest.views - oldest.views;
                                if (timeDiff > 0) {
                                    const organicRate = viewsDiff / timeDiff;
                                    combinedViewsPerHour = viewsPerHour + organicRate;
                                } else {
                                    combinedViewsPerHour = viewsPerHour;
                                }
                            } else {
                                combinedViewsPerHour = viewsPerHour;
                            }
                            
                            // Calculate time remaining to reach goals - respect target completion time
                            const viewsNeeded = Math.max(0, targetViews - totalViews);
                            let hoursToGoal = 0;
                            
                            // Use target completion time if set, otherwise calculate from rate
                            if (targetCompletionTimeLocal && hoursToTargetLocal > 0) {
                                // Use target completion time as the maximum
                                hoursToGoal = Math.min(hoursToTargetLocal, combinedViewsPerHour > 0 ? viewsNeeded / combinedViewsPerHour : hoursToTargetLocal);
                            } else {
                                // Fallback to rate-based calculation
                                hoursToGoal = combinedViewsPerHour > 0 ? viewsNeeded / combinedViewsPerHour : 0;
                            }
                            
                            // If target is overdue, show that
                            if (isTargetOverdueLocal && viewsNeeded > 0) {
                                hoursToGoal = -1; // Will show "Past due"
                            }
                            
                            let statusHtml = '';
                            
                            if (activityStatus === 'waiting') {
                                const hours = Math.floor(countdownSeconds / 3600);
                                const minutes = Math.floor((countdownSeconds % 3600) / 60);
                                const seconds = countdownSeconds % 60;
                                
                                let timeDisplay = '';
                                if (hours > 0) {
                                    timeDisplay = hours + 'h ' + minutes + 'm ' + seconds + 's';
                                } else if (minutes > 0) {
                                    timeDisplay = minutes + 'm ' + seconds + 's';
                                } else {
                                    timeDisplay = seconds + 's';
                                }
                                
                                statusHtml = '<div style="display: flex; align-items: center; gap: 15px; flex-wrap: wrap;">' +
                                    '<div style="font-size: 24px;">⏳</div>' +
                                    '<div style="flex: 1;">' +
                                    '<div style="font-weight: 600; font-size: 16px; margin-bottom: 5px;">Waiting to Order</div>' +
                                    '<div style="opacity: 0.9; font-size: 14px;">' + (currentActivity.waiting_for || 'Next order') + '</div>' +
                                    '</div>' +
                                    '<div style="text-align: right;">' +
                                    '<div style="font-size: 20px; font-weight: 700; font-family: monospace;" data-countdown-display>' + timeDisplay + '</div>' +
                                    '<div style="opacity: 0.8; font-size: 12px;">until next action</div>' +
                                    '</div>' +
                                    '</div>' +
                                    '<div data-countdown data-next-action-time="' + (currentActivity.next_action_time || '') + '" style="display:none;"></div>';
                            } else if (activityStatus === 'ordering') {
                                statusHtml = '<div style="display: flex; align-items: center; gap: 15px;">' +
                                    '<div style="font-size: 24px;">🔄</div>' +
                                    '<div style="flex: 1;">' +
                                    '<div style="font-weight: 600; font-size: 16px; margin-bottom: 5px;">Ordering Now</div>' +
                                    '<div style="opacity: 0.9; font-size: 14px;">' + (currentActivity.action || 'Placing order') + '</div>' +
                                    '</div>' +
                                    '</div>';
                            } else {
                                // Idle or delivering
                                statusHtml = '<div style="display: flex; align-items: center; gap: 15px; flex-wrap: wrap;">' +
                                    '<div style="font-size: 24px;">✅</div>' +
                                    '<div style="flex: 1;">' +
                                    '<div style="font-weight: 600; font-size: 16px; margin-bottom: 5px;">' + currentStatus + '</div>' +
                                    '<div style="opacity: 0.9; font-size: 14px;">' + (viewsOrdered > 0 ? 'Delivering orders' : 'Monitoring progress') + '</div>' +
                                    '</div>' +
                                    '</div>';
                            }
                            
                            // Add time remaining to goal
                            if (viewsNeeded > 0) {
                                let timeToGoal = '';
                                if (hoursToGoal < 0 || isTargetOverdue) {
                                    timeToGoal = 'Past due';
                                } else if (hoursToGoal > 0) {
                                    const totalSeconds = Math.floor(hoursToGoal * 3600);
                                    const days = Math.floor(totalSeconds / (24 * 3600));
                                    const remainingAfterDays = totalSeconds % (24 * 3600);
                                    const hours = Math.floor(remainingAfterDays / 3600);
                                    const remainingAfterHours = remainingAfterDays % 3600;
                                    const minutes = Math.floor(remainingAfterHours / 60);
                                    const seconds = remainingAfterHours % 60;
                                    
                                    if (days > 0) {
                                        timeToGoal = days + 'd ' + hours + 'h ' + minutes + 'm';
                                    } else if (hours > 0) {
                                        timeToGoal = hours + 'h ' + minutes + 'm ' + seconds + 's';
                                    } else if (minutes > 0) {
                                        timeToGoal = minutes + 'm ' + seconds + 's';
                                    } else {
                                        timeToGoal = seconds + 's';
                                    }
                                } else {
                                    timeToGoal = 'N/A';
                                }
                                
                                const targetTimeDisplay = targetCompletionTimeLocal && hoursToTargetLocal > 0 ? '<div style="opacity: 0.7; font-size: 11px; margin-top: 2px;">Target: ' + formatTimeRemaining(hoursToTargetLocal) + '</div>' : '';
                                statusHtml += '<div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid rgba(255,255,255,0.3); display: flex; justify-content: space-between; align-items: center;">' +
                                    '<div>' +
                                    '<div style="opacity: 0.9; font-size: 13px; margin-bottom: 3px;">Estimated Time to Goal</div>' +
                                    '<div style="font-size: 18px; font-weight: 600; color: ' + (hoursToGoal < 0 ? '#ef4444' : '#fff') + ';" data-time-to-goal-detail data-hours="' + hoursToGoal + '">' + timeToGoal + '</div>' +
                                    targetTimeDisplay +
                                    '</div>' +
                                    '<div style="text-align: right;">' +
                                    '<div style="opacity: 0.9; font-size: 13px; margin-bottom: 3px;">Progress Rate</div>' +
                                    '<div style="font-size: 18px; font-weight: 600;">' + Math.round(combinedViewsPerHour) + ' views/hr</div>' +
                                    '</div>' +
                                    '</div>';
                            }
                            
                            if (timeSinceUpdate !== null && timeSinceUpdate > 300) {
                                statusHtml += '<div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.3); opacity: 0.7; font-size: 12px;">' +
                                    'Last updated: ' + (timeSinceUpdate < 60 ? timeSinceUpdate + 's ago' : Math.floor(timeSinceUpdate / 60) + 'm ago') +
                                    '</div>';
                            }
                            
                            return statusHtml;
                        }())}
                    </div>
                    
                    <div class="activity-log-section">
                        <h3>📋 Activity Log</h3>
                        <div class="log-status">Current Status: ${currentStatus}</div>
                        <ul class="activity-log">
                            ${activityLog.length > 0 ? (function() {
                                const logs = activityLog.slice(-20).reverse();
                                let html = '';
                                for (let i = 0; i < logs.length; i++) {
                                    const log = logs[i];
                                    const level = log.level || 'info';
                                    const time = new Date(log.timestamp).toLocaleTimeString();
                                    const message = String(log.message || '').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;').replace(/'/g, '&#39;');
                                    html += '<li class="log-' + level + '"><span class="log-timestamp">' + time + '</span><span class="log-message">' + message + '</span></li>';
                                }
                                return html;
                            }()) : '<li class="log-info">No activity logged yet</li>'}
                        </ul>
                    </div>
                    
                    <div class="info-grid">
                        <div class="info-item">
                            <div class="info-label">Real-Time Views</div>
                            <div class="info-value">${formatNumber(totalViews)}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Ordered Views</div>
                            <div class="info-value">${formatNumber(viewsOrdered)}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Expected Total</div>
                            <div class="info-value">${formatNumber(expectedViews)}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Real-Time Likes</div>
                            <div class="info-value">${formatNumber(totalLikes)}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Time Elapsed</div>
                            <div class="info-value">${formatTimeElapsed(videoData.start_time)}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Total Cost</div>
                            <div class="info-value">$${(videoData.total_cost || 0).toFixed(4)}</div>
                        </div>
                        <div class="info-item">
                            <div class="info-label">Orders Placed</div>
                            <div class="info-value">${(videoData.order_history || []).length}</div>
                        </div>
                    </div>
                </div>
            `;
        }
        
        function getCurrentRoute() {
            const hash = window.location.hash;
            const fullUrl = window.location.href;
            console.log('getCurrentRoute - hash:', hash, 'full URL:', fullUrl);
            
            // Check hash first
            if (hash && hash.length > 7 && hash.startsWith('#video/')) {
                try {
                    const videoUrl = decodeURIComponent(hash.substring(7));
                    console.log('getCurrentRoute - decoded URL from hash:', videoUrl);
                    return { type: 'detail', videoUrl: videoUrl };
                } catch (e) {
                    console.error('Error decoding video URL from hash:', e, 'hash was:', hash);
                    return { type: 'home' };
                }
            }
            
            // Also check if URL contains #video/ directly (in case hash isn't set yet)
            const hashMatch = fullUrl.match(/#video\/(.+)$/);
            if (hashMatch) {
                try {
                    const videoUrl = decodeURIComponent(hashMatch[1]);
                    console.log('getCurrentRoute - decoded URL from URL match:', videoUrl);
                    return { type: 'detail', videoUrl: videoUrl };
                } catch (e) {
                    console.error('Error decoding video URL from URL match:', e);
                }
            }
            
            console.log('getCurrentRoute - returning home (no hash or hash does not start with #video/)');
            return { type: 'home' };
        }
        
        function navigateToVideo(videoUrl) {
            console.log('[navigateToVideo] Called with:', videoUrl);
            console.log('[navigateToVideo] Type:', typeof videoUrl);
            try {
                // Ensure videoUrl is a string
                let urlString = String(videoUrl);
                console.log('[navigateToVideo] String version:', urlString);
                
                // Decode HTML entities if present
                urlString = urlString.replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>');
                
                // Remove quotes if present (from JSON.stringify)
                if (urlString.startsWith('"') && urlString.endsWith('"')) {
                    urlString = urlString.slice(1, -1);
                }
                
                console.log('[navigateToVideo] Processed URL:', urlString);
                
                const hash = '#video/' + encodeURIComponent(urlString);
                console.log('[navigateToVideo] Setting hash to:', hash);
                
                // Set hash and immediately trigger loadDashboard
                window.location.hash = hash;
                console.log('[navigateToVideo] Hash set, current hash:', window.location.hash);
                
                setTimeout(() => {
                    console.log('[navigateToVideo] Timeout fired, hash:', window.location.hash);
                    loadDashboard(false);
                }, 100);
            } catch (error) {
                console.error('[navigateToVideo] ERROR:', error);
                console.error('[navigateToVideo] Stack:', error.stack);
                alert('Error navigating to video: ' + error.message);
            }
        }
        
        function navigateToHome() {
            window.location.hash = '';
            loadDashboard(false);
        }
        
        function renderHomepage(videos) {
            // Format time remaining helper
            function formatTimeRemaining(hours) {
                if (hours < 0) return 'Past due';
                if (hours <= 0 || !isFinite(hours)) return 'N/A';
                const days = Math.floor(hours / 24);
                const remainingHours = Math.floor(hours % 24);
                const minutes = Math.floor((hours % 1) * 60);
                
                if (days > 0) {
                    return days + 'd ' + remainingHours + 'h';
                } else if (remainingHours > 0) {
                    return remainingHours + 'h ' + minutes + 'm';
                } else {
                    return minutes + 'm';
                }
            }
            
            if (Object.keys(videos).length === 0) {
                return `
                    <div class="empty-state">
                        <h2>No Videos</h2>
                        <p>Add videos to start tracking campaigns</p>
                    </div>
                `;
            }
            
            let html = '<div class="videos-grid">';
            
            for (const [videoUrl, videoData] of Object.entries(videos)) {
                const { username, videoId } = extractVideoInfo(videoUrl);
                // Escape template literal special characters
                function escapeTemplateLiteral(str) {
                    if (!str) return '';
                    return String(str).replace(/\\\\/g, '\\\\\\\\').replace(/`/g, '\\\\`').replace(/\\$/g, '\\\\$');
                }
                const displayName = username ? `@${escapeTemplateLiteral(username)}` : 'Unknown';
                
                const ordersPlaced = videoData.orders_placed || {};
                const realViews = videoData.real_views !== undefined ? videoData.real_views : (videoData.initial_views || 0);
                const realLikes = videoData.real_likes !== undefined ? videoData.real_likes : (videoData.initial_likes || 0);
                const realComments = videoData.real_comments !== undefined ? videoData.real_comments : (videoData.initial_comments || 0);
                
                const targetViews = videoData.target_views || 4000;
                const targetLikes = videoData.target_likes || 125;
                const targetComments = videoData.target_comments || 7;
                
                const viewsProgress = (realViews / targetViews) * 100;
                const likesProgress = (realLikes / targetLikes) * 100;
                const commentsProgress = (realComments / targetComments) * 100;
                
                const overallProgress = viewsProgress;
                const embedUrl = getTikTokEmbedUrl(videoUrl);
                const safeVideoUrl = JSON.stringify(videoUrl);
                // Escape URLs for HTML attributes - use split/join to avoid regex issues
                function escapeHtml(str) {
                    if (!str) return '';
                    return str.split('&').join('&amp;').split('"').join('&quot;').split("'").join('&#39;').split('<').join('&lt;').split('>').join('&gt;');
                }
                const safeEmbedUrl = escapeHtml(embedUrl);
                const safeVideoUrlAttr = escapeHtml(videoUrl);
                
                // Create a safe ID for the button to avoid issues
                const buttonId = 'btn-' + Math.random().toString(36).substring(2, 9);
                
                const campaignId = videoData.campaign_id || '';
                html += `
                    <div class="video-card-mini" data-video-url="${safeVideoUrlAttr}" data-campaign-id="${campaignId || ''}">
                        <div class="video-card-mini-header" style="display: flex; align-items: center; gap: 10px;">
                            <input type="checkbox" class="video-select-checkbox" data-video-url="${safeVideoUrlAttr}" style="width: 18px; height: 18px; cursor: pointer; accent-color: #667eea;" onchange="updateCampaignBar()">
                            <div class="video-card-mini-title" style="flex: 1;">${displayName}</div>
                            <div class="status-badge ${getStatusClass(overallProgress)}">
                                ${getStatusText(overallProgress)}
                            </div>
                        </div>
                        ${campaignId ? `<div style="font-size: 0.75em; color: #667eea; margin-top: 5px; opacity: 0.8;">📊 Campaign: <span id="campaign-name-${safeVideoUrlAttr.replace(/[^a-zA-Z0-9]/g, '_')}">Loading...</span></div>` : ''}
                        ${embedUrl ? `
                        <div class="video-embed-mini" data-action="stop-propagation">
                            <iframe src="${safeEmbedUrl}" allowfullscreen></iframe>
                        </div>
                        ` : ''}
                        <div class="video-card-mini-stats">
                            <div class="mini-stat">
                                <div class="mini-stat-label">Views</div>
                                <div class="mini-stat-value">${formatNumber(realViews)}</div>
                                <div class="mini-stat-progress">
                                    <div class="mini-stat-progress-bar" style="width: ${Math.min(viewsProgress, 100)}%"></div>
                                </div>
                            </div>
                            <div class="mini-stat">
                                <div class="mini-stat-label">Likes</div>
                                <div class="mini-stat-value">${formatNumber(realLikes)}</div>
                                <div class="mini-stat-progress">
                                    <div class="mini-stat-progress-bar" style="width: ${Math.min(likesProgress, 100)}%"></div>
                                </div>
                            </div>
                            <div class="mini-stat">
                                <div class="mini-stat-label">Comments</div>
                                <div class="mini-stat-value">${formatNumber(realComments)}</div>
                                <div class="mini-stat-progress">
                                    <div class="mini-stat-progress-bar" style="width: ${Math.min(commentsProgress, 100)}%"></div>
                                </div>
                            </div>
                        </div>
                        ${(function() {
                            const currentActivity = videoData.current_activity || {};
                            const activityStatus = currentActivity.status || 'idle';
                            const lastUpdated = currentActivity.last_updated ? new Date(currentActivity.last_updated) : null;
                            const now = new Date();
                            
                            // Calculate next action time if waiting
                            let nextActionTime = null;
                            let countdownSeconds = 0;
                            if (activityStatus === 'waiting' && currentActivity.next_action_time) {
                                nextActionTime = new Date(currentActivity.next_action_time);
                                countdownSeconds = Math.max(0, Math.floor((nextActionTime - now) / 1000));
                            }
                            
                            // Calculate views per hour from orders
                            const viewsOrdered = ordersPlaced.views || 0;
                            const targetCompletionTime = videoData.target_completion_time || videoData.target_completion_datetime;
                            let viewsPerHour = 0;
                            if (targetCompletionTime && viewsOrdered > 0) {
                                const startTime = videoData.start_time ? new Date(videoData.start_time) : new Date();
                                const endTime = new Date(targetCompletionTime);
                                const hoursRemaining = Math.max(1, (endTime - new Date()) / (1000 * 60 * 60));
                                viewsPerHour = viewsOrdered / hoursRemaining;
                            } else {
                                viewsPerHour = 167; // Default rate
                            }
                            
                            // Calculate target completion time variables
                            const targetCompletionTimeLocal = videoData.target_completion_time || videoData.target_completion_datetime;
                            let hoursToTargetLocal = 0;
                            let isTargetOverdueLocal = false;
                            if (targetCompletionTimeLocal) {
                                const targetTime = new Date(targetCompletionTimeLocal);
                                hoursToTargetLocal = Math.max(0, (targetTime - now) / (1000 * 60 * 60));
                                isTargetOverdueLocal = hoursToTargetLocal <= 0;
                            }
                            
                            // Calculate combined progress rate (orders + organic growth)
                            let combinedViewsPerHour = viewsPerHour;
                            const growthHistory = videoData.growth_history || [];
                            if (growthHistory.length >= 2) {
                                const recent = growthHistory.slice(-5);
                                const oldest = recent[0];
                                const newest = recent[recent.length - 1];
                                const timeDiff = (new Date(newest.timestamp) - new Date(oldest.timestamp)) / (1000 * 60 * 60);
                                const viewsDiff = newest.views - oldest.views;
                                if (timeDiff > 0) {
                                    const organicRate = viewsDiff / timeDiff;
                                    combinedViewsPerHour = viewsPerHour + organicRate;
                                }
                            }
                            
                            // Calculate time remaining to reach goals - respect target completion time
                            const viewsNeeded = Math.max(0, targetViews - realViews);
                            let hoursToGoal = 0;
                            
                            // Use target completion time if set, otherwise calculate from rate
                            if (targetCompletionTimeLocal && hoursToTargetLocal > 0) {
                                // Use target completion time as the maximum
                                hoursToGoal = Math.min(hoursToTargetLocal, combinedViewsPerHour > 0 ? viewsNeeded / combinedViewsPerHour : hoursToTargetLocal);
                            } else {
                                // Fallback to rate-based calculation
                                hoursToGoal = combinedViewsPerHour > 0 ? viewsNeeded / combinedViewsPerHour : 0;
                            }
                            
                            // If target is overdue, show that
                            if (isTargetOverdueLocal && viewsNeeded > 0) {
                                hoursToGoal = -1; // Will show "Past due"
                            }
                            
                            let statusHtml = '';
                            
                            if (activityStatus === 'waiting') {
                                const hours = Math.floor(countdownSeconds / 3600);
                                const minutes = Math.floor((countdownSeconds % 3600) / 60);
                                const seconds = countdownSeconds % 60;
                                
                                let timeDisplay = '';
                                if (hours > 0) {
                                    timeDisplay = hours + 'h ' + minutes + 'm ' + seconds + 's';
                                } else if (minutes > 0) {
                                    timeDisplay = minutes + 'm ' + seconds + 's';
                                } else {
                                    timeDisplay = seconds + 's';
                                }
                                
                                statusHtml = '<div class="video-card-mini-activity" style="padding: 12px; margin: 12px 0; background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%); border-radius: 8px; border-left: 3px solid #667eea;">' +
                                    '<div style="display: flex; align-items: center; gap: 10px; margin-bottom: 8px;">' +
                                    '<span style="font-size: 18px;">⏳</span>' +
                                    '<div style="flex: 1;">' +
                                    '<div style="font-weight: 600; font-size: 13px; color: #fff;">Waiting to Order</div>' +
                                    '<div style="opacity: 0.8; font-size: 11px; color: #ccc;">' + (currentActivity.waiting_for || 'Next order') + '</div>' +
                                    '</div>' +
                                    '<div style="text-align: right;">' +
                                    '<div style="font-size: 16px; font-weight: 700; font-family: monospace; color: #fff;" data-countdown-display data-video-url="' + safeVideoUrlAttr + '">' + timeDisplay + '</div>' +
                                    '<div style="opacity: 0.7; font-size: 10px; color: #ccc;">until next</div>' +
                                    '</div>' +
                                    '</div>' +
                                    '<div data-countdown data-next-action-time="' + (currentActivity.next_action_time || '') + '" data-video-url="' + safeVideoUrlAttr + '" style="display:none;"></div>';
                                
                                // Add time to goal if available
                                if (viewsNeeded > 0) {
                                    let timeToGoal = '';
                                    if (hoursToGoal < 0 || isTargetOverdueLocal) {
                                        timeToGoal = 'Past due';
                                    } else if (hoursToGoal > 0) {
                                        const totalSeconds = Math.floor(hoursToGoal * 3600);
                                        const days = Math.floor(totalSeconds / (24 * 3600));
                                        const remainingAfterDays = totalSeconds % (24 * 3600);
                                        const hours = Math.floor(remainingAfterDays / 3600);
                                        const remainingAfterHours = remainingAfterDays % 3600;
                                        const minutes = Math.floor(remainingAfterHours / 60);
                                        const seconds = remainingAfterHours % 60;
                                        
                                        if (days > 0) {
                                            timeToGoal = days + 'd ' + hours + 'h ' + minutes + 'm';
                                        } else if (hours > 0) {
                                            timeToGoal = hours + 'h ' + minutes + 'm ' + seconds + 's';
                                        } else if (minutes > 0) {
                                            timeToGoal = minutes + 'm ' + seconds + 's';
                                        } else {
                                            timeToGoal = seconds + 's';
                                        }
                                    } else {
                                        timeToGoal = 'N/A';
                                    }
                                    
                                    const targetTimeDisplay = targetCompletionTimeLocal && hoursToTargetLocal > 0 ? ' (Target: ' + formatTimeRemaining(hoursToTargetLocal) + ')' : '';
                                    statusHtml += '<div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.2); display: flex; justify-content: space-between; font-size: 11px;">' +
                                        '<div style="opacity: 0.8;">Time to Goal: <strong style="color: ' + (hoursToGoal < 0 ? '#ef4444' : '#fff') + ';">' + timeToGoal + '</strong>' + targetTimeDisplay + '</div>' +
                                        '<div style="opacity: 0.8;">Rate: <strong>' + Math.round(combinedViewsPerHour) + '/hr</strong></div>' +
                                        '</div>';
                                }
                                
                                statusHtml += '</div>';
                            } else if (activityStatus === 'ordering') {
                                statusHtml = '<div class="video-card-mini-activity" style="padding: 12px; margin: 12px 0; background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%); border-radius: 8px; border-left: 3px solid #667eea;">' +
                                    '<div style="display: flex; align-items: center; gap: 10px;">' +
                                    '<span style="font-size: 18px;">🔄</span>' +
                                    '<div style="flex: 1;">' +
                                    '<div style="font-weight: 600; font-size: 13px; color: #fff;">Ordering Now</div>' +
                                    '<div style="opacity: 0.8; font-size: 11px; color: #ccc;">' + (currentActivity.action || 'Placing order') + '</div>' +
                                    '</div>' +
                                    '</div>';
                                
                                // Add time to goal if available
                                if (viewsNeeded > 0) {
                                    let timeToGoal = '';
                                    if (hoursToGoal < 0 || isTargetOverdueLocal) {
                                        timeToGoal = 'Past due';
                                    } else if (hoursToGoal > 0) {
                                        const totalSeconds = Math.floor(hoursToGoal * 3600);
                                        const days = Math.floor(totalSeconds / (24 * 3600));
                                        const remainingAfterDays = totalSeconds % (24 * 3600);
                                        const hours = Math.floor(remainingAfterDays / 3600);
                                        const remainingAfterHours = remainingAfterDays % 3600;
                                        const minutes = Math.floor(remainingAfterHours / 60);
                                        const seconds = remainingAfterHours % 60;
                                        
                                        if (days > 0) {
                                            timeToGoal = days + 'd ' + hours + 'h ' + minutes + 'm';
                                        } else if (hours > 0) {
                                            timeToGoal = hours + 'h ' + minutes + 'm ' + seconds + 's';
                                        } else if (minutes > 0) {
                                            timeToGoal = minutes + 'm ' + seconds + 's';
                                        } else {
                                            timeToGoal = seconds + 's';
                                        }
                                    } else {
                                        timeToGoal = 'N/A';
                                    }
                                    
                                    const targetTimeDisplay = targetCompletionTimeLocal && hoursToTargetLocal > 0 ? ' (Target: ' + formatTimeRemaining(hoursToTargetLocal) + ')' : '';
                                    statusHtml += '<div style="margin-top: 8px; padding-top: 8px; border-top: 1px solid rgba(255,255,255,0.2); display: flex; justify-content: space-between; font-size: 11px;">' +
                                        '<div style="opacity: 0.8;">Time to Goal: <strong style="color: ' + (hoursToGoal < 0 ? '#ef4444' : '#fff') + ';">' + timeToGoal + '</strong>' + targetTimeDisplay + '</div>' +
                                        '<div style="opacity: 0.8;">Rate: <strong>' + Math.round(combinedViewsPerHour) + '/hr</strong></div>' +
                                        '</div>';
                                }
                                
                                statusHtml += '</div>';
                            } else {
                                // Idle or delivering - show time to goal
                                if (viewsNeeded > 0) {
                                    let timeToGoal = '';
                                    if (hoursToGoal < 0 || isTargetOverdueLocal) {
                                        timeToGoal = 'Past due';
                                    } else if (hoursToGoal > 0) {
                                        const totalSeconds = Math.floor(hoursToGoal * 3600);
                                        const days = Math.floor(totalSeconds / (24 * 3600));
                                        const remainingAfterDays = totalSeconds % (24 * 3600);
                                        const hours = Math.floor(remainingAfterDays / 3600);
                                        const remainingAfterHours = remainingAfterDays % 3600;
                                        const minutes = Math.floor(remainingAfterHours / 60);
                                        const seconds = remainingAfterHours % 60;
                                        
                                        if (days > 0) {
                                            timeToGoal = days + 'd ' + hours + 'h ' + minutes + 'm';
                                        } else if (hours > 0) {
                                            timeToGoal = hours + 'h ' + minutes + 'm ' + seconds + 's';
                                        } else if (minutes > 0) {
                                            timeToGoal = minutes + 'm ' + seconds + 's';
                                        } else {
                                            timeToGoal = seconds + 's';
                                        }
                                    } else {
                                        timeToGoal = 'N/A';
                                    }
                                    
                                    const targetTimeDisplay = targetCompletionTimeLocal && hoursToTargetLocal > 0 ? ' (Target: ' + formatTimeRemaining(hoursToTargetLocal) + ')' : '';
                                    
                                    statusHtml = '<div class="video-card-mini-activity" style="padding: 12px; margin: 12px 0; background: linear-gradient(135deg, rgba(102, 126, 234, 0.2) 0%, rgba(118, 75, 162, 0.2) 100%); border-radius: 8px; border-left: 3px solid #667eea;">' +
                                        '<div style="display: flex; justify-content: space-between; align-items: center; font-size: 11px;">' +
                                        '<div style="opacity: 0.8;">Time to Goal: <strong style="color: ' + (hoursToGoal < 0 ? '#ef4444' : '#fff') + ';">' + timeToGoal + '</strong>' + targetTimeDisplay + '</div>' +
                                        '<div style="opacity: 0.8;">Rate: <strong style="color: #fff;">' + Math.round(combinedViewsPerHour) + '/hr</strong></div>' +
                                        '</div>' +
                                        '</div>';
                                }
                            }
                            
                            return statusHtml;
                        }())}
                        <div class="video-card-mini-actions" style="padding: 15px; border-top: 1px solid rgba(255,255,255,0.1);">
                            <button class="show-analytics-btn" data-video-url="${safeVideoUrlAttr}" style="width: 100%; padding: 12px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border: none; border-radius: 8px; color: white; font-weight: 600; cursor: pointer; font-size: 14px; transition: transform 0.2s, box-shadow 0.2s;">
                                📊 Show Analytics
                            </button>
                        </div>
                    </div>
                `;
            }
            
            html += '</div>';
            return html;
        }
        
        let isRefreshing = false;
        let allVideosData = {};
        
        function getCurrentRoute() {
            const hash = window.location.hash || '';
            if (hash.startsWith('#video/')) {
                const videoUrl = decodeURIComponent(hash.substring(7));
                return { type: 'detail', videoUrl: videoUrl };
            } else if (hash.startsWith('#campaign/')) {
                const campaignId = decodeURIComponent(hash.substring(10));
                return { type: 'campaign', campaignId: campaignId };
            }
            return { type: 'home' };
        }
        
        function navigateToHome() {
            window.location.hash = '';
            loadDashboard(false);
        }
        
        function navigateToCampaign(campaignId) {
            window.location.hash = '#campaign/' + encodeURIComponent(campaignId);
            loadDashboard(false);
        }
        
        function navigateToVideo(videoUrl) {
            window.location.hash = '#video/' + encodeURIComponent(videoUrl);
            loadDashboard(false);
        }
        
        function renderSummaryStats(videos) {
            if (Object.keys(videos).length === 0) {
                document.getElementById('summary-stats-container').innerHTML = '';
                return;
            }
            
            let totalVideos = 0;
            let totalViews = 0;
            let totalLikes = 0;
            let totalComments = 0;
            let totalCost = 0;
            let completedVideos = 0;
            let activeVideos = 0;
            
            for (const [videoUrl, videoData] of Object.entries(videos)) {
                totalVideos++;
                const realViews = videoData.real_views !== undefined ? videoData.real_views : (videoData.initial_views || 0);
                const realLikes = videoData.real_likes !== undefined ? videoData.real_likes : (videoData.initial_likes || 0);
                const realComments = videoData.real_comments !== undefined ? videoData.real_comments : (videoData.initial_comments || 0);
                const targetViews = videoData.target_views || 4000;
                const viewsProgress = (realViews / targetViews) * 100;
                
                totalViews += realViews;
                totalLikes += realLikes;
                totalComments += realComments;
                totalCost += videoData.total_cost || 0;
                
                if (viewsProgress >= 100) {
                    completedVideos++;
                } else if (viewsProgress > 0) {
                    activeVideos++;
                }
            }
            
            const avgProgress = totalVideos > 0 ? 
                Object.values(videos).reduce((sum, v) => {
                    const views = v.real_views !== undefined ? v.real_views : (v.initial_views || 0);
                    const target = v.target_views || 4000;
                    return sum + ((views / target) * 100);
                }, 0) / totalVideos : 0;
            
            const html = `
                <div class="summary-stats">
                    <div class="summary-stat-card">
                        <div class="summary-stat-label">Total Campaigns</div>
                        <div class="summary-stat-value">${totalVideos}</div>
                        <div class="summary-stat-change">${completedVideos} completed, ${activeVideos} active</div>
                    </div>
                    <div class="summary-stat-card">
                        <div class="summary-stat-label">Total Views</div>
                        <div class="summary-stat-value">${formatNumber(totalViews)}</div>
                        <div class="summary-stat-change">Across all campaigns</div>
                    </div>
                    <div class="summary-stat-card">
                        <div class="summary-stat-label">Total Likes</div>
                        <div class="summary-stat-value">${formatNumber(totalLikes)}</div>
                        <div class="summary-stat-change">Across all campaigns</div>
                    </div>
                    <div class="summary-stat-card">
                        <div class="summary-stat-label">Total Comments</div>
                        <div class="summary-stat-value">${formatNumber(totalComments)}</div>
                        <div class="summary-stat-change">Across all campaigns</div>
                    </div>
                    <div class="summary-stat-card">
                        <div class="summary-stat-label">Total Cost</div>
                        <div class="summary-stat-value">$${totalCost.toFixed(2)}</div>
                        <div class="summary-stat-change">Total spent</div>
                    </div>
                    <div class="summary-stat-card">
                        <div class="summary-stat-label">Avg Progress</div>
                        <div class="summary-stat-value">${avgProgress.toFixed(1)}%</div>
                        <div class="summary-stat-change">Average completion</div>
                    </div>
                </div>
            `;
            
            document.getElementById('summary-stats-container').innerHTML = html;
        }
        
        function filterVideos() {
            const searchTerm = document.getElementById('search-box').value.toLowerCase();
            const statusFilter = document.getElementById('status-filter').value;
            const sortBy = document.getElementById('sort-by').value;
            
            const route = getCurrentRoute();
            if (route.type === 'detail') {
                // Don't filter on detail page
                return;
            }
            
            const content = document.getElementById('dashboard-content');
            const videoCards = content.querySelectorAll('.video-card-mini');
            
            let visibleCount = 0;
            const videoDataArray = [];
            
            videoCards.forEach(card => {
                const videoUrl = card.getAttribute('data-video-url');
                if (!videoUrl) return;
                
                const videoData = allVideosData[videoUrl];
                if (!videoData) return;
                
                // Search filter
                const { username, videoId } = extractVideoInfo(videoUrl);
                const searchText = (username || '') + ' ' + (videoId || '') + ' ' + videoUrl;
                const matchesSearch = !searchTerm || searchText.toLowerCase().includes(searchTerm);
                
                // Status filter
                const realViews = videoData.real_views !== undefined ? videoData.real_views : (videoData.initial_views || 0);
                const targetViews = videoData.target_views || 4000;
                const viewsProgress = (realViews / targetViews) * 100;
                
                let statusMatch = true;
                if (statusFilter !== 'all') {
                    if (statusFilter === 'complete' && viewsProgress < 100) statusMatch = false;
                    else if (statusFilter === 'good' && (viewsProgress < 75 || viewsProgress >= 100)) statusMatch = false;
                    else if (statusFilter === 'moderate' && (viewsProgress < 50 || viewsProgress >= 75)) statusMatch = false;
                    else if (statusFilter === 'early' && viewsProgress >= 50) statusMatch = false;
                }
                
                if (matchesSearch && statusMatch) {
                    videoDataArray.push({
                        url: videoUrl,
                        card: card,
                        data: videoData,
                        progress: viewsProgress,
                        views: realViews,
                        startTime: videoData.start_time || ''
                    });
                }
            });
            
            // Sort
            videoDataArray.sort((a, b) => {
                switch(sortBy) {
                    case 'progress-desc':
                        return b.progress - a.progress;
                    case 'progress-asc':
                        return a.progress - b.progress;
                    case 'views-desc':
                        return b.views - a.views;
                    case 'views-asc':
                        return a.views - b.views;
                    case 'recent':
                        return new Date(b.startTime) - new Date(a.startTime);
                    case 'oldest':
                        return new Date(a.startTime) - new Date(b.startTime);
                    default:
                        return 0;
                }
            });
            
            // Hide all cards first
            videoCards.forEach(card => card.style.display = 'none');
            
            // Show and reorder filtered cards
            const grid = content.querySelector('.videos-grid');
            if (grid && videoDataArray.length > 0) {
                // Clear existing order
                const fragment = document.createDocumentFragment();
                videoDataArray.forEach(item => {
                    item.card.style.display = 'block';
                    fragment.appendChild(item.card);
                    visibleCount++;
                });
                grid.innerHTML = '';
                grid.appendChild(fragment);
            }
            
            // Show empty state if no results
            if (visibleCount === 0 && Object.keys(allVideosData).length > 0) {
                const grid = content.querySelector('.videos-grid');
                if (grid) {
                    grid.innerHTML = `
                        <div class="empty-state" style="grid-column: 1 / -1;">
                            <h2>No videos match your filters</h2>
                            <p>Try adjusting your search or filter criteria</p>
                        </div>
                    `;
                }
            } else if (visibleCount === 0 && Object.keys(allVideosData).length === 0) {
                // No videos at all
                content.innerHTML = `
                    <div class="empty-state">
                        <h2>No videos in progress</h2>
                        <p>Add a video using: python run_delivery_bot.py &lt;video_url&gt;</p>
                    </div>
                `;
            }
        }
        
        function clearFilters() {
            document.getElementById('search-box').value = '';
            document.getElementById('status-filter').value = 'all';
            document.getElementById('sort-by').value = 'progress-desc';
            filterVideos();
        }
        
        function exportData() {
            const data = {
                exportDate: new Date().toISOString(),
                videos: allVideosData
            };
            
            const jsonStr = JSON.stringify(data, null, 2);
            const blob = new Blob([jsonStr], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `campaign-dashboard-export-${new Date().toISOString().split('T')[0]}.json`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            // Also create CSV export
            let csv = 'Video URL,Username,Video ID,Views,Likes,Comments,Progress,Status,Cost,Start Time\\n';
            for (const [videoUrl, videoData] of Object.entries(allVideosData)) {
                const { username, videoId } = extractVideoInfo(videoUrl);
                const realViews = videoData.real_views !== undefined ? videoData.real_views : (videoData.initial_views || 0);
                const realLikes = videoData.real_likes !== undefined ? videoData.real_likes : (videoData.initial_likes || 0);
                const realComments = videoData.real_comments !== undefined ? videoData.real_comments : (videoData.initial_comments || 0);
                const targetViews = videoData.target_views || 4000;
                const progress = ((realViews / targetViews) * 100).toFixed(1);
                const status = getStatusText(progress);
                const cost = (videoData.total_cost || 0).toFixed(4);
                const startTime = videoData.start_time || '';
                
                csv += `"${videoUrl}","${username || ''}","${videoId || ''}",${realViews},${realLikes},${realComments},${progress}%,"${status}",$${cost},"${startTime}"\\n`;
            }
            
            const csvBlob = new Blob([csv], { type: 'text/csv' });
            const csvUrl = URL.createObjectURL(csvBlob);
            const csvA = document.createElement('a');
            csvA.href = csvUrl;
            csvA.download = `campaign-dashboard-export-${new Date().toISOString().split('T')[0]}.csv`;
            document.body.appendChild(csvA);
            csvA.click();
            document.body.removeChild(csvA);
            URL.revokeObjectURL(csvUrl);
        }
        
        function showAddVideoModal(campaignId = null) {
            const modal = document.getElementById('add-video-modal');
            const input = document.getElementById('new-video-url');
            const errorDiv = document.getElementById('add-video-error');
            const campaignSelector = document.getElementById('add-video-campaign-selector');
            
            modal.style.display = 'flex';
            input.value = '';
            errorDiv.style.display = 'none';
            errorDiv.textContent = '';
            if (campaignSelector) {
                populateAddVideoCampaignSelector();
                campaignSelector.value = campaignId || '';
            }
            
            // Focus input after modal appears
            setTimeout(() => input.focus(), 100);
        }
        
        function showAddVideoToCampaignModal(campaignId) {
            showAddVideoModal(campaignId);
        }
        
        function hideAddVideoModal() {
            const modal = document.getElementById('add-video-modal');
            const errorDiv = document.getElementById('add-video-error');
            
            modal.style.display = 'none';
            errorDiv.style.display = 'none';
            errorDiv.textContent = '';
        }
        
        async function addVideo() {
            const input = document.getElementById('new-video-url');
            const errorDiv = document.getElementById('add-video-error');
            const successDiv = document.getElementById('add-video-success');
            const progressDiv = document.getElementById('add-video-progress');
            const progressList = document.getElementById('add-video-progress-list');
            const progressBar = document.getElementById('add-video-progress-bar');
            const addButton = document.getElementById('add-video-submit-btn');
            const cancelButton = document.getElementById('add-video-cancel-btn');
            const campaignSelector = document.getElementById('add-video-campaign-selector');
            const campaignId = campaignSelector ? campaignSelector.value : '';
            
            // Get URLs from textarea (one per line)
            const urlsText = input.value.trim();
            const urls = urlsText.split('\\n')
                .map(url => url.trim())
                .filter(url => url.length > 0);
            
            // Clear previous messages
            errorDiv.style.display = 'none';
            errorDiv.textContent = '';
            successDiv.style.display = 'none';
            successDiv.textContent = '';
            
            // Validate input
            if (urls.length === 0) {
                errorDiv.textContent = 'Please enter at least one TikTok video URL';
                errorDiv.style.display = 'block';
                return;
            }
            
            // Validate all URLs
            const invalidUrls = urls.filter(url => !url.includes('tiktok.com'));
            if (invalidUrls.length > 0) {
                errorDiv.textContent = `Invalid URLs detected. All URLs must be TikTok links.`;
                errorDiv.style.display = 'block';
                return;
            }
            
            // Show progress
            progressDiv.style.display = 'block';
            progressList.innerHTML = '';
            progressBar.style.width = '0%';
            addButton.disabled = true;
            cancelButton.disabled = true;
            addButton.textContent = 'Adding...';
            
            let successCount = 0;
            let errorCount = 0;
            const results = [];
            
            // Process each URL
            for (let i = 0; i < urls.length; i++) {
                const url = urls[i];
                const progress = ((i + 1) / urls.length) * 100;
                progressBar.style.width = progress + '%';
                
                // Update progress list
                const statusLine = document.createElement('div');
                statusLine.style.marginBottom = '4px';
                statusLine.innerHTML = `[${i + 1}/${urls.length}] ${url.substring(0, 60)}... <span style="color: #667eea;">Processing...</span>`;
                progressList.appendChild(statusLine);
                
                try {
                    const params = new URLSearchParams({
                        video_url: url
                    });
                    if (campaignId) params.set('campaign_id', campaignId);

                    const response = await fetch('/api/add-video?' + params.toString(), {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/x-www-form-urlencoded',
                        },
                        body: params.toString()
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        successCount++;
                        statusLine.innerHTML = `[${i + 1}/${urls.length}] ${url.substring(0, 60)}... <span style="color: #10b981;">✓ Added</span>`;
                        results.push({ url, success: true, data });
                    } else {
                        errorCount++;
                        statusLine.innerHTML = `[${i + 1}/${urls.length}] ${url.substring(0, 60)}... <span style="color: #ef4444;">✗ ${data.error || 'Failed'}</span>`;
                        results.push({ url, success: false, error: data.error });
                    }
                } catch (error) {
                    errorCount++;
                    statusLine.innerHTML = `[${i + 1}/${urls.length}] ${url.substring(0, 60)}... <span style="color: #ef4444;">✗ Error: ${error.message}</span>`;
                    results.push({ url, success: false, error: error.message });
                }
                
                // Scroll to bottom of progress list
                progressList.scrollTop = progressList.scrollHeight;
            }
            
            // Complete
            progressBar.style.width = '100%';
            
            // Show results
            if (successCount > 0) {
                successDiv.textContent = `✓ Successfully added ${successCount} video(s)${errorCount > 0 ? ` (${errorCount} failed)` : ''}`;
                successDiv.style.display = 'block';
                
                // Show notification
                showNotification(`✓ ${successCount} video(s) added successfully`, 'success');
                
                // Refresh dashboard after a short delay
                setTimeout(async () => {
                    await loadDashboard(false);
                    await loadCampaigns();
                    hideAddVideoModal();
                    // Clear input
                    input.value = '';
                }, 1500);
            } else {
                errorDiv.textContent = `Failed to add all videos. ${errorCount} error(s) occurred.`;
                errorDiv.style.display = 'block';
                addButton.disabled = false;
                cancelButton.disabled = false;
                addButton.textContent = 'Add Video(s)';
            }
        }
        
        function showNotification(message, type = 'info') {
            // Create notification element
            const notification = document.createElement('div');
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: ${type === 'success' ? '#10b981' : type === 'error' ? '#ef4444' : '#667eea'};
                color: white;
                padding: 16px 24px;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                z-index: 100000;
                font-size: 14px;
                font-weight: 600;
                animation: slideIn 0.3s ease-out;
                max-width: 400px;
            `;
            notification.textContent = message;
            
            // Add animation
            const style = document.createElement('style');
            style.textContent = `
                @keyframes slideIn {
                    from {
                        transform: translateX(400px);
                        opacity: 0;
                    }
                    to {
                        transform: translateX(0);
                        opacity: 1;
                    }
                }
            `;
            document.head.appendChild(style);
            
            document.body.appendChild(notification);
            
            // Remove after 3 seconds
            setTimeout(() => {
                notification.style.animation = 'slideIn 0.3s ease-out reverse';
                setTimeout(() => {
                    notification.remove();
                    style.remove();
                }, 300);
            }, 3000);
        }

        function populateAddVideoCampaignSelector() {
            const selector = document.getElementById('add-video-campaign-selector');
            if (!selector) return;

            let html = '<option value="">No campaign</option>';
            for (const [campaignId, campaign] of Object.entries(campaignsData || {})) {
                const name = (campaign && campaign.name) ? String(campaign.name) : 'Unnamed Campaign';
                const safeName = name.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\\"/g, '&quot;');
                html += `<option value="${campaignId}">${safeName}</option>`;
            }
            selector.innerHTML = html;
        }
        
        // Close modals when clicking outside
        // Event delegation for catch-up buttons (they're dynamically created)
        document.addEventListener('click', function(e) {
            if (e.target && e.target.classList.contains('catch-up-btn')) {
                e.preventDefault();
                e.stopPropagation();
                const videoUrl = e.target.getAttribute('data-video-url');
                const metric = e.target.getAttribute('data-metric');
                const amount = parseInt(e.target.getAttribute('data-amount'));
                catchUp(videoUrl, metric, amount, e.target);
            }
            
            if (e.target && e.target.classList.contains('manual-order-btn')) {
                e.preventDefault();
                e.stopPropagation();
                const videoUrl = e.target.getAttribute('data-video-url');
                const metric = e.target.getAttribute('data-metric');
                const minimum = parseInt(e.target.getAttribute('data-minimum'));
                manualOrder(videoUrl, metric, minimum, e.target);
            }
        });
        
        document.addEventListener('DOMContentLoaded', function() {
            const addVideoModal = document.getElementById('add-video-modal');
            if (addVideoModal) {
                addVideoModal.addEventListener('click', function(e) {
                    if (e.target === addVideoModal) {
                        hideAddVideoModal();
                    }
                });
            }
            
            const createCampaignModal = document.getElementById('create-campaign-modal');
            if (createCampaignModal) {
                createCampaignModal.addEventListener('click', function(e) {
                    if (e.target === createCampaignModal) {
                        hideCreateCampaignModal();
                    }
                });
            }
            
            const editCampaignModal = document.getElementById('edit-campaign-modal');
            if (editCampaignModal) {
                editCampaignModal.addEventListener('click', function(e) {
                    if (e.target === editCampaignModal) {
                        hideEditCampaignModal();
                    }
                });
            }

            const addVideoNewCampaignBtn = document.getElementById('add-video-new-campaign-btn');
            if (addVideoNewCampaignBtn) {
                addVideoNewCampaignBtn.addEventListener('click', function(e) {
                    e.preventDefault();
                    e.stopPropagation();
                    hideAddVideoModal();
                    showCreateCampaignModal();
                });
            }
            
            // Attach event listener to New Campaign button in campaign bar
            const newCampaignBtnBar = document.getElementById('new-campaign-btn-bar');
            if (newCampaignBtnBar) {
                newCampaignBtnBar.addEventListener('click', function(e) {
                    e.preventDefault();
                    showCreateCampaignModal();
                });
            }
            
            // Close on Escape key
            document.addEventListener('keydown', function(e) {
                if (e.key === 'Escape') {
                    if (addVideoModal && addVideoModal.style.display === 'flex') {
                        hideAddVideoModal();
                    }
                    if (createCampaignModal && createCampaignModal.style.display === 'flex') {
                        hideCreateCampaignModal();
                    }
                }
            });
        });
        
        async function loadDashboard(showLoading = false) {
            // Prevent multiple simultaneous refreshes
            if (isRefreshing) {
                console.log('Already refreshing, skipping...');
                return;
            }
            isRefreshing = true;
            
            const route = getCurrentRoute();
            console.log('loadDashboard - route:', route);
            const content = document.getElementById('dashboard-content');
            
            // Only show loading on manual refresh or first load
            if (showLoading) {
                content.style.opacity = '0.5';
            }
            
            try {
                const response = await fetch('/api/progress');
                const progress = await response.json();
                
                // Store all videos data for filtering
                allVideosData = progress;
                
                // Load campaigns ONLY on first/full load. Avoid re-rendering campaign UI every refresh
                // (it wipes calculator inputs, checkbox selection state, etc.).
                if (showLoading && (!campaignsData || Object.keys(campaignsData).length === 0)) {
                    await loadCampaigns();
                }
                
                // Render summary stats
                renderSummaryStats(progress);
                
                if (Object.keys(progress).length === 0) {
                    content.innerHTML = `
                        <div class="empty-state">
                            <h2>No videos in progress</h2>
                            <p>Add a video using: python run_delivery_bot.py &lt;video_url&gt;</p>
                        </div>
                    `;
                    content.style.opacity = '1';
                    isRefreshing = false;
                    return;
                }
                
                let html = '';
                
                if (route.type === 'campaign') {
                    // Show campaign detail view with all posts
                    const campaignId = route.campaignId;
                    const campaign = campaignsData[campaignId];
                    
                    if (!campaign) {
                        html = `
                            <div class="empty-state">
                                <h2>Campaign Not Found</h2>
                                <p>The requested campaign no longer exists.</p>
                                <div class="back-button" data-action="navigate-home" style="margin-top: 20px;">← Back to All Campaigns</div>
                            </div>
                        `;
                    } else {
                        const campaignVideos = campaign.videos || [];
                        const financial = campaign.financial || {};
                        
                        html += '<div class="back-button" data-action="navigate-home">← Back to All Campaigns</div>';
                        html += `<div style="background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%); border-radius: 16px; padding: 30px; margin-bottom: 30px; border: 1px solid rgba(255,255,255,0.1);">`;
                        html += `<h1 style="color: #fff; font-size: 2em; margin-bottom: 10px;">${campaign.name || 'Unnamed Campaign'}</h1>`;
                        html += `<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-top: 20px;">`;
                        html += `<div><div style="color: #b0b0b0; font-size: 0.9em;">CPM</div><div style="color: #fff; font-size: 1.5em; font-weight: 600;">$${campaign.cpm ? campaign.cpm.toFixed(2) : '0.00'}</div></div>`;
                        html += `<div><div style="color: #b0b0b0; font-size: 0.9em;">Total Videos</div><div style="color: #fff; font-size: 1.5em; font-weight: 600;">${campaignVideos.length}</div></div>`;
                        html += `<div><div style="color: #b0b0b0; font-size: 0.9em;">Total Views</div><div style="color: #fff; font-size: 1.5em; font-weight: 600;">${formatNumber(financial.total_views || 0)}</div></div>`;
                        html += `<div><div style="color: #b0b0b0; font-size: 0.9em;">Spent</div><div style="color: #ef4444; font-size: 1.5em; font-weight: 600;">$${financial.total_spent ? financial.total_spent.toFixed(2) : '0.00'}</div></div>`;
                        html += `<div><div style="color: #b0b0b0; font-size: 0.9em;">Earned</div><div style="color: #10b981; font-size: 1.5em; font-weight: 600;">$${financial.total_earned ? financial.total_earned.toFixed(2) : '0.00'}</div></div>`;
                        html += `<div><div style="color: #b0b0b0; font-size: 0.9em;">Profit</div><div style="color: ${(financial.profit || 0) >= 0 ? '#10b981' : '#ef4444'}; font-size: 1.5em; font-weight: 600;">$${financial.profit ? financial.profit.toFixed(2) : '0.00'}</div></div>`;
                        html += `</div></div>`;
                        
                        html += `<h2 style="color: #fff; font-size: 1.5em; margin: 30px 0 20px 0;">Posts in Campaign</h2>`;
                        
                        if (campaignVideos.length === 0) {
                            html += `<div style="text-align: center; padding: 40px; color: #b0b0b0;">No videos in this campaign yet. Add videos using the "➕ Add Video" button.</div>`;
                        } else {
                            // Show loading indicator while rendering videos
                            html += '<div id="campaign-videos-loading" style="text-align: center; padding: 20px; color: #b0b0b0;">Loading videos...</div>';
                            html += '<div id="campaign-videos-container" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(350px, 1fr)); gap: 20px;"></div>';
                        }
                    }
                } else if (route.type === 'detail') {
                    // Show detail view for specific video
                    const videoUrl = route.videoUrl;
                    console.log('Detail view - looking for video:', videoUrl);
                    console.log('Video URL type:', typeof videoUrl, 'length:', videoUrl ? videoUrl.length : 0);
                    console.log('Available videos:', Object.keys(progress));
                    console.log('Available video count:', Object.keys(progress).length);
                    
                    // Try exact match first
                    let videoData = progress[videoUrl];
                    if (videoData) {
                        console.log('Found video with exact match');
                    }
                    
                    // If not found, try URL decoding variations
                    if (!videoData) {
                        try {
                            const decodedUrl = decodeURIComponent(videoUrl);
                            videoData = progress[decodedUrl];
                            if (videoData) {
                                console.log('Found video with decoded URL:', decodedUrl);
                            }
                        } catch (e) {
                            console.log('Error decoding URL:', e);
                        }
                    }
                    
                    // Try matching by comparing URLs (handle encoding differences)
                    if (!videoData) {
                        console.log('Trying fuzzy URL matching...');
                        for (const [key, value] of Object.entries(progress)) {
                            try {
                                const decodedKey = decodeURIComponent(key);
                                const decodedVideoUrl = decodeURIComponent(videoUrl);
                                if (decodedKey === decodedVideoUrl || 
                                    key === videoUrl || 
                                    decodedKey === videoUrl ||
                                    key === decodedVideoUrl ||
                                    key.replace(/\/$/, '') === videoUrl.replace(/\/$/, '') ||
                                    decodedKey.replace(/\/$/, '') === decodedVideoUrl.replace(/\/$/, '')) {
                                    videoData = value;
                                    console.log('Found video by URL matching. Key:', key, 'VideoUrl:', videoUrl);
                                    break;
                                }
                            } catch (e) {
                                // Skip this key if decoding fails
                            }
                        }
                    }
                    
                    if (videoData) {
                        console.log('Rendering detail view for video:', videoUrl);
                        html += '<div class="back-button" data-action="navigate-home">← Back to All Campaigns</div>';
                        html += renderVideoCard(videoUrl, videoData);
                        console.log('Detail view HTML length:', html.length);
                    } else {
                        console.error('Video data not found for URL:', videoUrl);
                        html = `
                            <div class="empty-state">
                                <h2>Video Not Found</h2>
                                <p>The requested video is no longer in progress.</p>
                                <p>Looking for: ${escapeTemplateLiteral(videoUrl)}</p>
                                <p>Available videos: ${Object.keys(progress).join(', ')}</p>
                                <div class="back-button" data-action="navigate-home" style="margin-top: 20px;">← Back to All Campaigns</div>
                            </div>
                        `;
                    }
                } else {
                    // Show homepage with all videos
                    html = renderHomepage(progress);
                }
                
                // Smooth update without full reload
                content.innerHTML = html;
                content.style.opacity = '1';
                
                // If we're showing a campaign, render videos asynchronously in batches
                if (route.type === 'campaign') {
                    const campaignId = route.campaignId;
                    const campaign = campaignsData[campaignId];
                    if (campaign) {
                        const campaignVideos = campaign.videos || [];
                        if (campaignVideos.length > 0) {
                            // Render videos in batches to avoid blocking UI
                            const batchSize = 5;
                            let currentIndex = 0;
                            const container = document.getElementById('campaign-videos-container');
                            const loading = document.getElementById('campaign-videos-loading');
                            
                            function renderBatch() {
                                if (!container) return;
                                
                                const batch = campaignVideos.slice(currentIndex, currentIndex + batchSize);
                                let batchHtml = '';
                                
                                for (const videoUrl of batch) {
                                    const videoData = progress[videoUrl];
                                    if (videoData) {
                                        batchHtml += renderVideoCard(videoUrl, videoData);
                                    }
                                }
                                
                                container.innerHTML += batchHtml;
                                currentIndex += batchSize;
                                
                                if (currentIndex < campaignVideos.length) {
                                    // Continue with next batch
                                    setTimeout(renderBatch, 50);
                                } else {
                                    // All videos rendered
                                    if (loading) loading.style.display = 'none';
                                    // Initialize charts after all videos are rendered
                                    setTimeout(initializeGrowthCharts, 100);
                                }
                            }
                            
                            // Start rendering
                            setTimeout(renderBatch, 0);
                        }
                    }
                }
                
                // Attach event listeners directly to Show Analytics buttons after rendering
                // Use requestAnimationFrame to ensure DOM is ready
                requestAnimationFrame(function() {
                    setTimeout(function() {
                        try {
                            const analyticsButtons = content.querySelectorAll('.show-analytics-btn');
                            console.log('[loadDashboard] Found', analyticsButtons.length, 'Show Analytics buttons');
                            analyticsButtons.forEach(function(btn) {
                                // Remove any existing listeners by cloning
                                const newBtn = btn.cloneNode(true);
                                btn.parentNode.replaceChild(newBtn, btn);
                                
                                // Attach click listener directly
                                newBtn.addEventListener('click', function(e) {
                                    e.preventDefault();
                                    e.stopPropagation();
                                    e.stopImmediatePropagation();
                                    try {
                                        const url = newBtn.getAttribute('data-video-url');
                                        console.log('[Direct Listener] Show Analytics clicked, URL:', url);
                                        if (url) {
                                            const decodedUrl = url.replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>');
                                            console.log('[Direct Listener] Decoded URL:', decodedUrl);
                                            if (typeof navigateToVideo === 'function') {
                                                navigateToVideo(decodedUrl);
                                            } else {
                                                window.location.hash = '#video/' + encodeURIComponent(decodedUrl);
                                                loadDashboard(false);
                                            }
                                        } else {
                                            console.error('[Direct Listener] No data-video-url attribute found');
                                        }
                                    } catch (err) {
                                        console.error('[Direct Listener] Error:', err, err.stack);
                                    }
                                    return false;
                                }, true); // Use capture phase
                            });
                        } catch (err) {
                            console.error('[loadDashboard] Error attaching listeners:', err, err.stack);
                        }
                    }, 150);
                });
                
                // Apply filters if on homepage
                if (route.type === 'home') {
                    setTimeout(() => {
                        filterVideos();
                    }, 100);
                } else if (route.type === 'detail' || route.type === 'campaign') {
                    // For detail/campaign view, ensure charts are initialized after a delay
                    setTimeout(initializeGrowthCharts, 500);
                    setTimeout(startTimeToGoalCountdowns, 600);
                }
                
                // Initialize charts after content is updated
                if (route.type !== 'detail') {
                    setTimeout(initializeGrowthCharts, 100);
                    setTimeout(startTimeToGoalCountdowns, 200);
                }
                
                // Start countdown timers for activity status (works for both homepage and detail view)
                setTimeout(startActivityCountdowns, 300);
                // Start countdown timers for next purchases
                setTimeout(startNextPurchaseCountdowns, 350);
                // Start countdown timers for "Time to Goal" displays
                setTimeout(startTimeToGoalCountdowns, 400);
            } catch (error) {
                console.error('Error loading dashboard:', error);
                // Only show error on manual refresh, not auto-refresh
                if (showLoading) {
                    // Escape error message for template literal
                    function escapeTemplateLiteral(str) {
                        if (!str) return '';
                        return String(str).replace(/\\\\/g, '\\\\\\\\').replace(/`/g, '\\\\`').replace(/\\$/g, '\\\\$');
                    }
                    content.innerHTML = `
                        <div class="empty-state">
                            <h2>Error loading dashboard</h2>
                            <p>${escapeTemplateLiteral(error.message)}</p>
                        </div>
                    `;
                }
                content.style.opacity = '1';
            } finally {
                isRefreshing = false;
            }
        }
        
        function initializeGrowthCharts() {
            // Find all chart data divs and initialize charts
            document.querySelectorAll('div[id^="chart-data-"][data-chart-data]').forEach(div => {
                try {
                    // Properly decode HTML entities
                    let dataStr = div.getAttribute('data-chart-data');
                    if (!dataStr) return;
                    
                    // Decode HTML entities
                    dataStr = dataStr
                        .replace(/&quot;/g, '"')
                        .replace(/&#39;/g, "'")
                        .replace(/&amp;/g, '&')
                        .replace(/&lt;/g, '<')
                        .replace(/&gt;/g, '>')
                        .replace(/&#10;/g, '\\n')
                        .replace(/&#13;/g, '\\r');
                    
                    const data = JSON.parse(dataStr);
                    const ctx = document.getElementById(data.chartId);
                    if (ctx && typeof Chart !== 'undefined') {
                        // Destroy existing chart if it exists
                        if (ctx.chart) {
                            ctx.chart.destroy();
                        }
                        
                        ctx.chart = new Chart(ctx, {
                            type: 'line',
                            data: {
                                labels: data.labels,
                                datasets: [{
                                    label: 'Views (Actual)',
                                    data: data.viewsData,
                                    borderColor: 'rgba(102, 126, 234, 1)',
                                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                                    tension: 0.4,
                                    fill: true,
                                    yAxisID: 'y',
                                    borderWidth: 2,
                                    spanGaps: false
                                }, {
                                    label: 'Views (Expected)',
                                    data: data.expectedViewsData || [],
                                    borderColor: 'rgba(102, 126, 234, 0.8)',
                                    backgroundColor: 'transparent',
                                    borderDash: [8, 4],
                                    tension: 0.4,
                                    fill: false,
                                    yAxisID: 'y',
                                    borderWidth: 2.5,
                                    pointRadius: 0,
                                    order: 0
                                }, {
                                    label: 'Likes (Actual)',
                                    data: data.likesData,
                                    borderColor: 'rgba(16, 185, 129, 1)',
                                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                                    tension: 0.4,
                                    fill: true,
                                    yAxisID: 'y',
                                    borderWidth: 2,
                                    spanGaps: false
                                }, {
                                    label: 'Likes (Expected)',
                                    data: data.expectedLikesData || [],
                                    borderColor: 'rgba(16, 185, 129, 0.8)',
                                    backgroundColor: 'transparent',
                                    borderDash: [8, 4],
                                    tension: 0.4,
                                    fill: false,
                                    yAxisID: 'y',
                                    borderWidth: 2.5,
                                    pointRadius: 0,
                                    order: 0
                                }, {
                                    label: 'Comments (Actual)',
                                    data: data.commentsData,
                                    borderColor: 'rgba(239, 68, 68, 1)',
                                    backgroundColor: 'rgba(239, 68, 68, 0.1)',
                                    tension: 0.4,
                                    fill: true,
                                    yAxisID: 'y1',
                                    borderWidth: 2,
                                    spanGaps: false
                                }, {
                                    label: 'Comments (Expected)',
                                    data: data.expectedCommentsData || [],
                                    borderColor: 'rgba(239, 68, 68, 0.8)',
                                    backgroundColor: 'transparent',
                                    borderDash: [8, 4],
                                    tension: 0.4,
                                    fill: false,
                                    yAxisID: 'y1',
                                    borderWidth: 2.5,
                                    pointRadius: 0,
                                    order: 0
                                }]
                            },
                            options: {
                                responsive: true,
                                maintainAspectRatio: false,
                                plugins: {
                                    legend: {
                                        display: false
                                    },
                                    tooltip: {
                                        mode: 'index',
                                        intersect: false,
                                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                                        titleColor: '#ffffff',
                                        bodyColor: '#e0e0e0',
                                        borderColor: 'rgba(255, 255, 255, 0.1)',
                                        borderWidth: 1
                                    }
                                },
                                scales: {
                                    x: {
                                        ticks: {
                                            color: '#b0b0b0',
                                            maxRotation: 45,
                                            minRotation: 45
                                        },
                                        grid: {
                                            color: 'rgba(255, 255, 255, 0.1)'
                                        }
                                    },
                                    y: {
                                        type: 'linear',
                                        display: true,
                                        position: 'left',
                                        ticks: {
                                            color: '#b0b0b0',
                                            callback: function(value) {
                                                return value.toLocaleString();
                                            }
                                        },
                                        grid: {
                                            color: 'rgba(255, 255, 255, 0.1)'
                                        }
                                    },
                                    y1: {
                                        type: 'linear',
                                        display: true,
                                        position: 'right',
                                        ticks: {
                                            color: '#b0b0b0'
                                        },
                                        grid: {
                                            drawOnChartArea: false
                                        }
                                    }
                                },
                                interaction: {
                                    mode: 'nearest',
                                    axis: 'x',
                                    intersect: false
                                }
                            }
                        });
                    }
                } catch (e) {
                    console.error('Error initializing chart:', e);
                }
            });
        }
        
        // Start countdown timers for activity status (works for both homepage and detail view)
        function startActivityCountdowns() {
            // Clear any existing intervals
            if (window.activityCountdownIntervals) {
                window.activityCountdownIntervals.forEach(interval => clearInterval(interval));
            }
            window.activityCountdownIntervals = [];
            
            // Find all countdown elements (both on homepage cards and detail view)
            document.querySelectorAll('[data-countdown][data-next-action-time]').forEach(countdownEl => {
                const nextActionTimeStr = countdownEl.getAttribute('data-next-action-time');
                if (!nextActionTimeStr) return;
                
                const videoUrl = countdownEl.getAttribute('data-video-url') || '';
                const nextActionTime = new Date(nextActionTimeStr);
                
                // Find the corresponding display element
                const displayEl = document.querySelector(`[data-countdown-display][data-video-url="${videoUrl}"]`);
                if (!displayEl) return;
                
                // Update countdown every second
                const interval = setInterval(function() {
                    const now = new Date();
                    const secondsRemaining = Math.max(0, Math.floor((nextActionTime - now) / 1000));
                    
                    if (secondsRemaining <= 0) {
                        // Countdown finished, refresh the dashboard to get updated status
                        clearInterval(interval);
                        requestSafeRefresh();
                        return;
                    }
                    
                    const hours = Math.floor(secondsRemaining / 3600);
                    const minutes = Math.floor((secondsRemaining % 3600) / 60);
                    const seconds = secondsRemaining % 60;
                    
                    let timeDisplay = '';
                    if (hours > 0) {
                        timeDisplay = hours + 'h ' + minutes + 'm ' + seconds + 's';
                    } else if (minutes > 0) {
                        timeDisplay = minutes + 'm ' + seconds + 's';
                    } else {
                        timeDisplay = seconds + 's';
                    }
                    
                    displayEl.textContent = timeDisplay;
                }, 1000);
                
                // Initial update
                const now = new Date();
                const secondsRemaining = Math.max(0, Math.floor((nextActionTime - now) / 1000));
                const hours = Math.floor(secondsRemaining / 3600);
                const minutes = Math.floor((secondsRemaining % 3600) / 60);
                const seconds = secondsRemaining % 60;
                
                let timeDisplay = '';
                if (hours > 0) {
                    timeDisplay = hours + 'h ' + minutes + 'm ' + seconds + 's';
                } else if (minutes > 0) {
                    timeDisplay = minutes + 'm ' + seconds + 's';
                } else {
                    timeDisplay = seconds + 's';
                }
                
                displayEl.textContent = timeDisplay;
                
                window.activityCountdownIntervals.push(interval);
            });
        }
        
        // Start countdown timers for next purchases
        function startNextPurchaseCountdowns() {
            // Clear any existing intervals
            if (window.nextPurchaseIntervals) {
                window.nextPurchaseIntervals.forEach(interval => clearInterval(interval));
            }
            window.nextPurchaseIntervals = [];
            
            // Find all next purchase countdown elements
            document.querySelectorAll('[data-next-purchase][data-purchase-time]').forEach(purchaseEl => {
                const purchaseTimeStr = purchaseEl.getAttribute('data-purchase-time');
                if (!purchaseTimeStr) return;
                
                const purchaseTime = new Date(purchaseTimeStr);
                const displayEl = purchaseEl.querySelector('[data-countdown-display]');
                if (!displayEl) return;
                
                // Format time remaining helper with seconds support
                function formatTimeRemainingWithSeconds(totalSeconds) {
                    if (totalSeconds <= 0 || !isFinite(totalSeconds)) return '0s';
                    
                    const days = Math.floor(totalSeconds / (24 * 3600));
                    const remainingAfterDays = totalSeconds % (24 * 3600);
                    const hours = Math.floor(remainingAfterDays / 3600);
                    const remainingAfterHours = remainingAfterDays % 3600;
                    const minutes = Math.floor(remainingAfterHours / 60);
                    const seconds = Math.floor(remainingAfterHours % 60);
                    
                    if (days > 0) {
                        return days + 'd ' + hours + 'h ' + minutes + 'm';
                    } else if (hours > 0) {
                        return hours + 'h ' + minutes + 'm ' + seconds + 's';
                    } else if (minutes > 0) {
                        return minutes + 'm ' + seconds + 's';
                    } else {
                        return seconds + 's';
                    }
                }
                
                // Update countdown every second
                const interval = setInterval(function() {
                    const now = new Date();
                    const totalSecondsRemaining = Math.max(0, Math.floor((purchaseTime - now) / 1000));
                    
                    if (totalSecondsRemaining <= 0) {
                        // Purchase time reached, refresh the dashboard
                        clearInterval(interval);
                        requestSafeRefresh();
                        return;
                    }
                    
                    displayEl.textContent = formatTimeRemainingWithSeconds(totalSecondsRemaining);
                }, 1000);
                
                // Initial update
                const now = new Date();
                const totalSecondsRemaining = Math.max(0, Math.floor((purchaseTime - now) / 1000));
                displayEl.textContent = formatTimeRemainingWithSeconds(totalSecondsRemaining);
                
                window.nextPurchaseIntervals.push(interval);
            });
        }
        
        // Start countdown timers for "Time to Goal" displays
        function startTimeToGoalCountdowns() {
            // Clear any existing intervals
            if (window.timeToGoalIntervals) {
                window.timeToGoalIntervals.forEach(interval => clearInterval(interval));
            }
            window.timeToGoalIntervals = [];
            
            // Find all "to goal" countdown elements
            document.querySelectorAll('[data-time-to-goal]').forEach(goalEl => {
                const hoursAttr = goalEl.getAttribute('data-hours');
                if (!hoursAttr || isNaN(parseFloat(hoursAttr))) return;
                
                const initialHours = parseFloat(hoursAttr);
                const displayEl = goalEl.querySelector('[data-countdown-to-goal]');
                if (!displayEl) return;
                
                // Calculate initial time in seconds
                let currentHours = initialHours;
                const startTime = Date.now();
                
                // Update countdown every second
                const interval = setInterval(function() {
                    // Decrease time by 1 second (1/3600 hours)
                    currentHours = Math.max(0, currentHours - (1 / 3600));
                    
                    if (currentHours <= 0) {
                        displayEl.textContent = '0s';
                        clearInterval(interval);
                        return;
                    }
                    
                    const totalSeconds = Math.floor(currentHours * 3600);
                    const days = Math.floor(totalSeconds / (24 * 3600));
                    const remainingAfterDays = totalSeconds % (24 * 3600);
                    const hours = Math.floor(remainingAfterDays / 3600);
                    const remainingAfterHours = remainingAfterDays % 3600;
                    const minutes = Math.floor(remainingAfterHours / 60);
                    const seconds = remainingAfterHours % 60;
                    
                    let timeDisplay = '';
                    if (days > 0) {
                        timeDisplay = days + 'd ' + hours + 'h ' + minutes + 'm';
                    } else if (hours > 0) {
                        timeDisplay = hours + 'h ' + minutes + 'm ' + seconds + 's';
                    } else if (minutes > 0) {
                        timeDisplay = minutes + 'm ' + seconds + 's';
                    } else {
                        timeDisplay = seconds + 's';
                    }
                    
                    displayEl.textContent = timeDisplay;
                }, 1000);
                
                // Initial update
                const totalSeconds = Math.floor(currentHours * 3600);
                const days = Math.floor(totalSeconds / (24 * 3600));
                const remainingAfterDays = totalSeconds % (24 * 3600);
                const hours = Math.floor(remainingAfterDays / 3600);
                const remainingAfterHours = remainingAfterDays % 3600;
                const minutes = Math.floor(remainingAfterHours / 60);
                const seconds = remainingAfterHours % 60;
                
                let timeDisplay = '';
                if (days > 0) {
                    timeDisplay = days + 'd ' + hours + 'h ' + minutes + 'm';
                } else if (hours > 0) {
                    timeDisplay = hours + 'h ' + minutes + 'm ' + seconds + 's';
                } else if (minutes > 0) {
                    timeDisplay = minutes + 'm ' + seconds + 's';
                } else {
                    timeDisplay = seconds + 's';
                }
                
                displayEl.textContent = timeDisplay;
                
                window.timeToGoalIntervals.push(interval);
            });
        }
        
        // Event delegation for all buttons
        console.log('[Event Setup] Setting up event delegation listener');
        document.addEventListener('click', function(e) {
            // Find the button element (could be clicked directly or on child text)
            let btn = e.target;
            let attempts = 0;
            const maxAttempts = 10;
            
            // Traverse up the DOM tree to find the button
            while (btn && attempts < maxAttempts) {
                attempts++;
                // Check if this is an element node
                if (btn.nodeType === 1 && btn.classList) {
                    // Handle Show Analytics button
                    if (btn.classList.contains('show-analytics-btn')) {
                        e.preventDefault();
                        e.stopPropagation();
                        e.stopImmediatePropagation();
                        try {
                            const url = btn.getAttribute('data-video-url');
                            console.log('[Event Delegation] Show Analytics clicked! URL:', url);
                            if (url) {
                                const decodedUrl = url.replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>');
                                console.log('[Event Delegation] Decoded URL:', decodedUrl);
                                const hash = '#video/' + encodeURIComponent(decodedUrl);
                                console.log('[Event Delegation] Setting hash to:', hash);
                                window.location.hash = hash;
                                setTimeout(function() {
                                    console.log('[Event Delegation] Loading dashboard');
                                    loadDashboard(false);
                                }, 100);
                            } else {
                                console.error('[Event Delegation] No data-video-url attribute found');
                            }
                        } catch (err) {
                            console.error('[Event Delegation] Error:', err);
                        }
                        return false;
                    }
                    // Handle back button
                    if (btn.classList.contains('back-button') || btn.getAttribute('data-action') === 'navigate-home') {
                        e.preventDefault();
                        e.stopPropagation();
                        try {
                            if (typeof navigateToHome === 'function') {
                                navigateToHome();
                            } else {
                                window.location.hash = '';
                                loadDashboard(false);
                            }
                        } catch (err) {
                            console.error('Error navigating home:', err);
                            window.location.hash = '';
                        }
                        return false;
                    }
                    // Handle campaign card clicks (delegated)
                    if (btn.classList.contains('campaign-card-clickable')) {
                        e.preventDefault();
                        e.stopPropagation();
                        const campaignId = btn.getAttribute('data-campaign-id');
                        if (campaignId && typeof navigateToCampaign === 'function') {
                            navigateToCampaign(campaignId);
                        }
                        return false;
                    }
                    // Handle Remove Video button
                    if (btn.classList.contains('remove-video-btn')) {
                        e.preventDefault();
                        e.stopPropagation();
                        const url = btn.getAttribute('data-video-url');
                        if (url) {
                            const decodedUrl = url.replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&amp;/g, '&');
                            removeVideo(decodedUrl);
                        }
                        return false;
                    }
                    // Handle Quick Set Target button
                    if (btn.classList.contains('quick-set-target-btn')) {
                        e.preventDefault();
                        e.stopPropagation();
                        const url = btn.getAttribute('data-video-url');
                        const hoursId = btn.getAttribute('data-hours-id');
                        const minutesId = btn.getAttribute('data-minutes-id');
                        if (url && hoursId && minutesId) {
                            const decodedUrl = url.replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&amp;/g, '&');
                            quickSetTargetTime(decodedUrl, hoursId, minutesId);
                        }
                        return false;
                    }
                    // Handle Set Target button
                    if (btn.classList.contains('set-target-btn')) {
                        e.preventDefault();
                        e.stopPropagation();
                        const url = btn.getAttribute('data-video-url');
                        const targetId = btn.getAttribute('data-target-id');
                        if (url && targetId) {
                            const decodedUrl = url.replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&amp;/g, '&');
                            const targetInput = document.getElementById(targetId);
                            if (targetInput) {
                                updateTargetTime(decodedUrl, targetInput.value);
                            }
                        }
                        return false;
                    }
                    // Handle Save Comments button
                    if (btn.classList.contains('comments-save-btn')) {
                        e.preventDefault();
                        e.stopPropagation();
                        const url = btn.getAttribute('data-video-url');
                        const textareaId = btn.getAttribute('data-textarea-id');
                        if (url && textareaId) {
                            const decodedUrl = url.replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&amp;/g, '&');
                            saveComments(decodedUrl, textareaId);
                        }
                        return false;
                    }
                    // Handle Order Comments button
                    if (btn.classList.contains('order-comments-btn')) {
                        e.preventDefault();
                        e.stopPropagation();
                        const url = btn.getAttribute('data-video-url');
                        if (url) {
                            const decodedUrl = url.replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&amp;/g, '&');
                            orderComments(decodedUrl, btn);
                        }
                        return false;
                    }
                    // Handle Select Comments button
                    if (btn.classList.contains('select-comments-btn')) {
                        e.preventDefault();
                        e.stopPropagation();
                        const url = btn.getAttribute('data-video-url');
                        if (url) {
                            const decodedUrl = url.replace(/&quot;/g, '"').replace(/&#39;/g, "'").replace(/&amp;/g, '&');
                            showCommentSelectionModal(decodedUrl);
                        }
                        return false;
                    }
                    // Handle video embed stop propagation
                    if (btn.classList.contains('video-embed-mini') || btn.getAttribute('data-action') === 'stop-propagation') {
                        e.stopPropagation();
                        return false;
                    }
                }
                btn = btn.parentElement;
            }
        }); // Regular event bubbling
        
        // Listen for hash changes (back/forward browser buttons)
        window.addEventListener('hashchange', () => {
            console.log('Hash changed to:', window.location.hash);
            loadDashboard(false);
        });

        // -----------------------------
        // Auto-refresh without wiping UI
        // -----------------------------
        let lastUserInteractionTs = Date.now();
        const USER_INTERACTION_GRACE_MS = 5000;

        function markUserInteraction() {
            lastUserInteractionTs = Date.now();
        }

        // Capture user activity anywhere (use capture so we see it early)
        document.addEventListener('input', markUserInteraction, true);
        document.addEventListener('change', markUserInteraction, true);
        document.addEventListener('click', markUserInteraction, true);
        document.addEventListener('keydown', markUserInteraction, true);

        function isAnyModalOpen() {
            const modalIds = ['add-video-modal', 'create-campaign-modal', 'edit-campaign-modal', 'comment-selection-modal'];
            for (const id of modalIds) {
                const el = document.getElementById(id);
                if (!el) continue;
                const d = (el.style && el.style.display) ? el.style.display : '';
                if (d === 'flex' || d === 'block') return true;
            }
            return false;
        }

        function isFormElementFocused() {
            const ae = document.activeElement;
            if (!ae) return false;
            const tag = ae.tagName;
            return tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT';
        }

        function hasSelectedVideos() {
            try {
                return document.querySelectorAll('.video-select-checkbox:checked').length > 0;
            } catch {
                return false;
            }
        }

        function shouldPauseAutoRefresh() {
            if ((Date.now() - lastUserInteractionTs) < USER_INTERACTION_GRACE_MS) return true;
            if (isAnyModalOpen()) return true;
            if (isFormElementFocused()) return true;
            if (hasSelectedVideos()) return true;
            return false;
        }

        function requestSafeRefresh() {
            if (!shouldPauseAutoRefresh()) {
                loadDashboard(false);
                return;
            }
            // Try again shortly without interrupting the user
            setTimeout(requestSafeRefresh, 2000);
        }
        
        // Load dashboard on page load (show loading on first load)
        // Always check hash on initial load - use setTimeout to ensure DOM is ready
        console.log('Initial page load, hash:', window.location.hash, 'full URL:', window.location.href);
        setTimeout(async () => {
            const route = getCurrentRoute();
            console.log('Initial route detection:', route);
            await loadCampaigns(); // Load campaigns first
            loadDashboard(true);
        }, 100);
        
        // Initialize charts after a short delay to ensure Chart.js is loaded
        setTimeout(initializeGrowthCharts, 500);
        
        // Auto-refresh every 60 seconds (1 minute) to reduce API load
        setInterval(() => {
            if (shouldPauseAutoRefresh()) return;
            loadDashboard(false);
        }, 60000);
    </script>
</body>
</html>"""
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass

def run_server(port=PORT):
    """Run the dashboard server"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, DashboardHandler)
    
    url = f'http://localhost:{port}'
    print(f"\n{'='*60}")
    print(f"  Campaign Dashboard Server")
    print(f"{'='*60}")
    print(f"\n  Server running at: {Fore.CYAN}{url}{Style.RESET_ALL}")
    print(f"  Press Ctrl+C to stop\n")
    
    # Open browser automatically (only if not on Render)
    if not os.environ.get('RENDER'):
        try:
            webbrowser.open(url)
        except:
            pass
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Server stopped.{Style.RESET_ALL}")

if __name__ == '__main__':
    # Use PORT from environment (Render provides this) or command line arg or default
    port = PORT
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except:
            print(f"Invalid port, using {PORT}")
    
    print(f"{Fore.GREEN}Starting dashboard server on port {port}{Style.RESET_ALL}")
    print(f"{Fore.CYAN}Health check: http://localhost:{port}/health{Style.RESET_ALL}")
    run_server(port)

