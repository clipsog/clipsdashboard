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

# Import database module for PostgreSQL support
try:
    import database
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False
    print("⚠️ Database module not available, using JSON files")

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
        try:
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
            elif path == '/api/delete-campaign':
                self.handle_delete_campaign()
            elif path == '/api/assign-videos':
                self.handle_assign_videos()
            elif path == '/api/save-next-purchase-time':
                self.handle_save_next_purchase_time()
            elif path == '/api/catch-up':
                self.handle_catch_up()
            elif path == '/api/manual-order':
                self.handle_manual_order()
            elif path == '/api/update-video-time':
                self.handle_update_video_time()
            elif path == '/api/stop-overtime':
                self.handle_stop_overtime()
            elif path == '/api/video-details':
                self.handle_video_details()
            elif path == '/health' or path == '/api/health':
                self.handle_health()
            else:
                self.send_error(404)
        except Exception as e:
            print(f"❌ Unhandled exception in do_GET: {e}")
            import traceback
            traceback.print_exc()
            try:
                self.send_response(500)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(f"Internal Server Error: {str(e)}".encode())
            except:
                pass  # Connection may be closed
    
    def do_POST(self):
        """Handle POST requests"""
        try:
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
            elif path == '/api/delete-campaign':
                self.handle_delete_campaign()
            elif path == '/api/assign-videos':
                self.handle_assign_videos()
            elif path == '/api/save-next-purchase-time':
                self.handle_save_next_purchase_time()
            elif path == '/api/catch-up':
                self.handle_catch_up()
            elif path == '/api/manual-order':
                self.handle_manual_order()
            elif path == '/api/update-video-time':
                self.handle_update_video_time()
            elif path == '/api/stop-overtime':
                self.handle_stop_overtime()
            elif path == '/api/video-details':
                self.handle_video_details()
            elif path == '/health' or path == '/api/health':
                self.handle_health()
            else:
                self.send_error(404)
        except Exception as e:
            print(f"❌ Unhandled exception in do_POST: {e}")
            import traceback
            traceback.print_exc()
            try:
                self.send_response(500)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(f"Internal Server Error: {str(e)}".encode())
            except:
                pass  # Connection may be closed
    
    def send_dashboard(self):
        """Send the HTML dashboard"""
        try:
            html = self.get_dashboard_html()
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            try:
                self.wfile.write(html.encode())
            except BrokenPipeError:
                # Client disconnected, ignore
                pass
        except Exception as e:
            print(f"❌ Error in send_dashboard: {e}")
            import traceback
            traceback.print_exc()
            try:
                self.send_response(500)
                self.send_header('Content-type', 'text/html')
                self.end_headers()
                error_html = f"""<!DOCTYPE html>
<html><head><title>Error</title></head>
<body><h1>500 Internal Server Error</h1>
<p>An error occurred while loading the dashboard.</p>
<p>Error: {str(e)}</p>
</body></html>"""
                self.wfile.write(error_html.encode())
            except:
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
        try:
            progress = self.load_progress()
        except Exception as e:
            print(f"❌ Error loading progress in send_progress_json: {e}")
            import traceback
            traceback.print_exc()
            progress = {}  # Return empty progress on error
        
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
        
        # Save updated progress to database
        try:
            self.save_progress(progress)
        except Exception as e:
            print(f"⚠️ Failed to save progress after analytics update: {e}")
            # Continue anyway - at least return the updated data
        
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
                    # CRITICAL: Save campaigns FIRST, then progress
                    # This ensures campaign has the video before progress.json is saved
                    self.save_campaigns(campaigns)
                    print(f"[ADD VIDEO] Saved campaign {campaign_id} with video")
                else:
                    # Invalid campaign_id passed; ignore assignment
                    pass
            
            # CRITICAL: Save progress AFTER campaigns to ensure campaign_id is set
            # This ensures rebuild logic can restore videos if campaigns.json is lost
            self.save_progress(progress)
            print(f"[ADD VIDEO] Saved progress for {video_url[:50]}...")
            
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
            # CRITICAL: Load campaigns FIRST to preserve existing video lists
            try:
                campaigns = self.load_campaigns()
            except Exception as e:
                print(f"❌ Error loading campaigns in handle_get_campaigns: {e}")
                campaigns = {}
            
            try:
                progress = self.load_progress()
            except Exception as e:
                print(f"❌ Error loading progress in handle_get_campaigns: {e}")
                progress = {}
            
            campaigns_changed = False
            
            # PRESERVE existing videos in campaigns - never clear them
            # Store original video lists before rebuilding
            original_campaign_videos = {}
            for campaign_id, campaign_data in campaigns.items():
                original_campaign_videos[campaign_id] = list(campaign_data.get('videos', []))
            
            # Rebuild campaign videos from progress.json (ensure persistence after restarts)
            # This ensures videos with campaign_id in progress.json are added to campaigns
            # CRITICAL: We ADD videos, never remove existing ones
            rebuild_count = 0
            for video_url, video_data in progress.items():
                campaign_id = video_data.get('campaign_id')
                if campaign_id:
                    # Skip if campaign doesn't exist and looks deleted (avoid recreating deleted campaigns)
                    # But allow creating if it's a genuinely missing campaign (e.g., from progress.json)
                    if campaign_id not in campaigns:
                        # Don't auto-create campaigns - this prevents recreating deleted campaigns
                        # The video should be reassigned to a new campaign or removed from progress
                        print(f"[REBUILD] Warning: Video {video_url[:50]}... references non-existent campaign {campaign_id}, skipping")
                        continue
                    
                    # Initialize videos list if it doesn't exist
                    if 'videos' not in campaigns[campaign_id]:
                        campaigns[campaign_id]['videos'] = []
                    
                    # PRESERVE existing videos from original load
                    if campaign_id in original_campaign_videos:
                        for existing_video in original_campaign_videos[campaign_id]:
                            if existing_video not in campaigns[campaign_id]['videos']:
                                campaigns[campaign_id]['videos'].append(existing_video)
                    
                    # Add video if not already in list (prevents duplicates)
                    if video_url not in campaigns[campaign_id]['videos']:
                        campaigns[campaign_id]['videos'].append(video_url)
                        campaigns_changed = True
                        rebuild_count += 1
                        print(f"[REBUILD] Added video {video_url[:50]}... to campaign {campaign_id}")
            
            # CRITICAL: Restore any videos that were in campaigns but not in progress
            # This prevents videos from disappearing if progress.json is temporarily incomplete
            for campaign_id, original_videos in original_campaign_videos.items():
                if campaign_id in campaigns:
                    if 'videos' not in campaigns[campaign_id]:
                        campaigns[campaign_id]['videos'] = []
                    for video_url in original_videos:
                        if video_url not in campaigns[campaign_id]['videos']:
                            campaigns[campaign_id]['videos'].append(video_url)
                            campaigns_changed = True
                            print(f"[PRESERVE] Restored video {video_url[:50]}... to campaign {campaign_id} (was in campaign but not in progress)")
            
            if rebuild_count > 0:
                print(f"[REBUILD] Restored {rebuild_count} video(s) to campaigns")
            
            # Ensure all campaigns have a videos list (even if empty)
            for campaign_id, campaign_data in campaigns.items():
                if 'videos' not in campaign_data:
                    campaign_data['videos'] = []
                    campaigns_changed = True
            
            # DEFENSIVE: Triple-check that videos with campaign_id are in campaigns
            # This is a safety net in case something went wrong
            for video_url, video_data in progress.items():
                campaign_id = video_data.get('campaign_id')
                if campaign_id and campaign_id in campaigns:
                    if 'videos' not in campaigns[campaign_id]:
                        campaigns[campaign_id]['videos'] = []
                        campaigns_changed = True
                    if video_url not in campaigns[campaign_id]['videos']:
                        campaigns[campaign_id]['videos'].append(video_url)
                        campaigns_changed = True
                        rebuild_count += 1
                        print(f"[DEFENSIVE REBUILD] Restored missing video {video_url[:50]}... to campaign {campaign_id}")
            
            # Calculate financial data for each campaign
            # Wrap in try-except to prevent individual campaign errors from crashing entire request
            for campaign_id, campaign_data in list(campaigns.items()):
                try:
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
                            
                            # Calculate earned from views - try multiple sources
                            # Priority: real_views > initial_views > orders_placed (as estimate)
                            real_views = video_data.get('real_views', 0) or video_data.get('initial_views', 0)
                            
                            # If no real views found, use orders_placed as fallback estimate
                            if real_views == 0:
                                orders_placed = video_data.get('orders_placed', {})
                                ordered_views = orders_placed.get('views', 0)
                                if ordered_views > 0:
                                    # Use ordered views as estimate if real views not available
                                    # This helps show progress even if analytics haven't been fetched yet
                                    real_views = ordered_views
                            
                            # Also check if there's a current views count from recent analytics fetch
                            # Some videos might have this updated more recently than real_views
                            current_views = video_data.get('current_views', 0)
                            if current_views > real_views:
                                real_views = current_views
                            
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
                except Exception as e:
                    print(f"⚠️ Error calculating financial data for campaign {campaign_id}: {e}")
                    import traceback
                    traceback.print_exc()
                    # Set default financial data to prevent crashes
                    campaign_data['financial'] = {
                        'total_spent': 0,
                        'total_views': 0,
                        'total_earned': 0,
                        'profit': 0,
                        'roi': 0
                    }

            # VERIFICATION: Check for videos that have campaign_id but aren't in campaigns
            # This helps diagnose the "videos disappearing" issue
            # If found, automatically fix them (this is a safety net)
            orphaned_videos = []
            for video_url, video_data in progress.items():
                campaign_id = video_data.get('campaign_id')
                if campaign_id:
                    if campaign_id not in campaigns:
                        orphaned_videos.append((video_url, campaign_id, 'campaign_not_found'))
                    elif video_url not in campaigns[campaign_id].get('videos', []):
                        orphaned_videos.append((video_url, campaign_id, 'not_in_campaign_list'))
                        # AUTO-FIX: Add the orphaned video back to its campaign
                        if 'videos' not in campaigns[campaign_id]:
                            campaigns[campaign_id]['videos'] = []
                        campaigns[campaign_id]['videos'].append(video_url)
                        campaigns_changed = True
                        rebuild_count += 1
                        print(f"[AUTO-FIX] Restored orphaned video {video_url[:50]}... to campaign {campaign_id}")
            
            # CRITICAL: Also check campaigns for videos that should be there based on progress
            # This is a reverse check - ensure all videos in progress with campaign_id are in campaigns
            for video_url, video_data in progress.items():
                campaign_id = video_data.get('campaign_id')
                if campaign_id and campaign_id in campaigns:
                    if 'videos' not in campaigns[campaign_id]:
                        campaigns[campaign_id]['videos'] = []
                        campaigns_changed = True
                    if video_url not in campaigns[campaign_id]['videos']:
                        campaigns[campaign_id]['videos'].append(video_url)
                        campaigns_changed = True
                        rebuild_count += 1
                        print(f"[REBUILD] Added missing video {video_url[:50]}... to campaign {campaign_id}")
            
            # ALWAYS save campaigns after rebuild to ensure persistence
            # CRITICAL: Save even if nothing changed to ensure rebuild state is persisted
            # This prevents videos from disappearing due to timing issues or file corruption
            # On Render free tier, files may not persist between deployments, so we always save
            try:
                self.save_campaigns(campaigns)
                if campaigns_changed or rebuild_count > 0:
                    print(f"[REBUILD] Saved campaigns (changed={campaigns_changed}, rebuilt={rebuild_count})")
                else:
                    print(f"[REBUILD] Verified campaigns (no changes needed)")
            except Exception as e:
                print(f"⚠️ Failed to save campaigns after rebuild: {e}")
                import traceback
                traceback.print_exc()
                # Continue anyway - at least return the data
                # Don't crash the whole request if save fails
            
            # LOG: Report campaign video counts for debugging
            for campaign_id, campaign_data in campaigns.items():
                video_count = len(campaign_data.get('videos', []))
                video_list = campaign_data.get('videos', [])
                print(f"[VERIFY] Campaign {campaign_id}: {video_count} videos")
                if video_count > 0:
                    print(f"         Videos: {', '.join([v[:30] + '...' for v in video_list[:3]])}{'...' if len(video_list) > 3 else ''}")
            
            if orphaned_videos:
                print(f"[WARNING] Found {len(orphaned_videos)} orphaned video(s), auto-fixed")
            
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
            
            # Check for duplicate campaign name
            campaign_name_lower = campaign_name.lower().strip()
            for existing_id, existing_campaign in campaigns.items():
                if existing_campaign.get('name', '').lower().strip() == campaign_name_lower:
                    response_data = json.dumps({
                        'success': False,
                        'error': f'A campaign with the name "{campaign_name}" already exists. Please use a different name.'
                    })
                    self.send_response(400)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Content-Length', str(len(response_data)))
                    self.end_headers()
                    self.wfile.write(response_data.encode())
                    return
            
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
            
            try:
                self.save_campaigns(campaigns)
            except Exception as save_error:
                error_msg = str(save_error)
                # Check for circuit breaker or auth errors
                if 'Circuit breaker' in error_msg or 'authentication' in error_msg.lower():
                    error_msg = "Database connection failed: Circuit breaker open (too many auth errors). Please check DATABASE_URL password in Render Dashboard. Wait 5-10 minutes for circuit breaker to reset, then verify password is correct."
                elif 'DATABASE_URL' in error_msg:
                    error_msg = "DATABASE_URL not configured. Please set it in Render Dashboard > Environment Variables"
                
                response_data = json.dumps({'success': False, 'error': error_msg})
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
                return
            
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
            error_msg = str(e)
            if 'Circuit breaker' in error_msg or 'authentication' in error_msg.lower():
                error_msg = "Database connection failed: Circuit breaker open. Please check DATABASE_URL password in Render Dashboard."
            response_data = json.dumps({'success': False, 'error': error_msg})
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
                    
                    # Determine order type - check if this is an automatic order
                    order_type = 'manual'  # Default to manual
                    # Check if this order was triggered automatically
                    automatic_flag = params.get('automatic', [None])[0]
                    if automatic_flag and automatic_flag.lower() == 'true':
                        order_type = 'scheduled'
                    
                    progress[video_url]['order_history'].append({
                        'service': metric,
                        'quantity': amount,
                        'order_id': str(order_id),
                        'timestamp': datetime.now().isoformat(),
                        'type': order_type
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
    
    def handle_delete_campaign(self):
        """Delete a campaign permanently"""
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
            
            # Delete campaign from database
            if DATABASE_AVAILABLE:
                try:
                    import database
                    with database.get_db_connection() as conn:
                        if conn:
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM campaigns WHERE campaign_id = %s", (campaign_id,))
                            conn.commit()
                            print(f"[DELETE] Deleted campaign {campaign_id} from database")
                        else:
                            print(f"❌ No database connection available")
                except Exception as e:
                    print(f"❌ Error deleting campaign from database: {e}")
                    import traceback
                    traceback.print_exc()
                    # If database delete failed, don't proceed
                    response_data = json.dumps({'success': False, 'error': f'Failed to delete campaign from database: {str(e)}'})
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Content-Length', str(len(response_data)))
                    self.end_headers()
                    self.wfile.write(response_data.encode())
                    return
            
            # Remove campaign from in-memory dict and save
            if campaign_id in campaigns:
                del campaigns[campaign_id]
                self.save_campaigns(campaigns)
                print(f"[DELETE] Removed campaign {campaign_id} from in-memory dict")
            
            # CRITICAL: Clean up campaign_id from all videos in progress.json
            # This prevents orphaned references that cause crashes when loading campaigns
            progress = self.load_progress()
            videos_cleaned = 0
            for video_url, video_data in progress.items():
                if video_data.get('campaign_id') == campaign_id:
                    video_data['campaign_id'] = None
                    videos_cleaned += 1
                    print(f"[DELETE] Cleaned campaign_id from video {video_url[:50]}...")
            
            if videos_cleaned > 0:
                self.save_progress(progress)
                print(f"[DELETE] Cleaned {videos_cleaned} video(s) from deleted campaign")
            
            response_data = json.dumps({
                'success': True,
                'message': 'Campaign deleted successfully'
            })
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(response_data)))
            self.end_headers()
            self.wfile.write(response_data.encode())
            
        except Exception as e:
            print(f"EXCEPTION in handle_delete_campaign: {str(e)}")
            import traceback
            traceback.print_exc()
            response_data = json.dumps({'success': False, 'error': str(e)})
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(response_data)))
            self.end_headers()
            self.wfile.write(response_data.encode())
    
    def handle_stop_overtime(self):
        """Stop overtime mode for a video"""
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            query_string = parsed_path.query
            params = urllib.parse.parse_qs(query_string)
            
            video_url = params.get('video_url', [None])[0]
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
                response_data = json.dumps({'success': False, 'error': 'Video not found'})
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
                return
            
            # Set overtime_stopped flag
            progress[video_url]['overtime_stopped'] = True
            self.save_progress(progress)
            
            response_data = json.dumps({
                'success': True,
                'message': 'Overtime stopped successfully'
            })
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(response_data)))
            self.end_headers()
            self.wfile.write(response_data.encode())
            
        except Exception as e:
            print(f"EXCEPTION in handle_stop_overtime: {str(e)}")
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
            
            # Remove videos from other campaigns first (only if they're being reassigned)
            # This prevents videos from being in multiple campaigns
            # BUT: Only remove if the video is actually being assigned to the new campaign
            for cid, camp_data in campaigns.items():
                if cid != campaign_id:
                    original_videos = camp_data.get('videos', [])
                    # Only remove videos that are in BOTH the old campaign AND being assigned to new campaign
                    videos_to_remove = [v for v in original_videos if v in video_urls and v in progress]
                    if videos_to_remove:
                        camp_data['videos'] = [v for v in original_videos if v not in videos_to_remove]
                        print(f"[ASSIGN] Removed {len(videos_to_remove)} video(s) from campaign {cid} (reassigning to {campaign_id})")
            
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
            
            # CRITICAL: Save campaigns FIRST, then progress
            # This ensures campaign has videos before progress.json is saved
            self.save_campaigns(campaigns)
            print(f"[ASSIGN] Saved campaigns with {len(campaigns[campaign_id]['videos'])} video(s) in campaign {campaign_id}")
            
            self.save_progress(progress)
            print(f"[ASSIGN] Saved progress with campaign_id assignments")
            
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
    
    def handle_update_video_time(self):
        """Update video target completion time"""
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            query_string = parsed_path.query
            params = urllib.parse.parse_qs(query_string)
            
            video_url = params.get('video_url', [None])[0]
            target_completion_time_str = params.get('target_completion_time', [None])[0]
            
            if not video_url or not target_completion_time_str:
                response_data = json.dumps({'success': False, 'error': 'Missing video_url or target_completion_time'})
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
                return
            
            video_url = urllib.parse.unquote(video_url)
            
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
            
            # Update target completion time
            progress[video_url]['target_completion_time'] = target_completion_time_str
            progress[video_url]['target_completion_datetime'] = target_completion_time_str
            
            self.save_progress(progress)
            
            response_data = json.dumps({'success': True, 'message': 'Video time updated successfully'})
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(response_data)))
            self.end_headers()
            self.wfile.write(response_data.encode())
        except Exception as e:
            print(f"EXCEPTION in handle_update_video_time: {str(e)}")
            import traceback
            traceback.print_exc()
            response_data = json.dumps({'success': False, 'error': str(e)})
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(response_data)))
            self.end_headers()
            self.wfile.write(response_data.encode())
    
    def handle_video_details(self):
        """Get video details"""
        try:
            parsed_path = urllib.parse.urlparse(self.path)
            query_string = parsed_path.query
            params = urllib.parse.parse_qs(query_string)
            
            video_url = params.get('video_url', [None])[0]
            
            if not video_url:
                response_data = json.dumps({'success': False, 'error': 'Missing video_url'})
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
                return
            
            video_url = urllib.parse.unquote(video_url)
            
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
            
            video_data = progress[video_url]
            
            response_data = json.dumps({'success': True, 'video': video_data})
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(response_data)))
            self.end_headers()
            self.wfile.write(response_data.encode())
        except Exception as e:
            print(f"EXCEPTION in handle_video_details: {str(e)}")
            import traceback
            traceback.print_exc()
            response_data = json.dumps({'success': False, 'error': str(e)})
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Content-Length', str(len(response_data)))
            self.end_headers()
            self.wfile.write(response_data.encode())
    
    def handle_wipe_database(self):
        """Handle POST request to wipe all data from database"""
        try:
            if self.command != 'POST':
                response_data = json.dumps({'success': False, 'error': 'POST required'})
                self.send_response(405)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
                return
            
            # Parse confirmation from body
            content_length = int(self.headers.get('Content-Length', 0))
            if content_length > 0:
                post_data = self.rfile.read(content_length)
                params = json.loads(post_data.decode())
                confirm = params.get('confirm', '').upper()
            else:
                confirm = ''
            
            if confirm != 'YES':
                response_data = json.dumps({'success': False, 'error': 'Confirmation required. Send {"confirm": "YES"}'})
                self.send_response(400)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
                return
            
            if not DATABASE_AVAILABLE:
                response_data = json.dumps({'success': False, 'error': 'Database module not available'})
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
                return
            
            print("🗑️  Wiping all data from database...")
            
            try:
                with database.get_db_connection() as conn:
                    if not conn:
                        raise Exception("Failed to connect to database")
                    
                    cursor = conn.cursor()
                    
                    # Delete all videos
                    cursor.execute("DELETE FROM videos")
                    videos_deleted = cursor.rowcount
                    print(f"   ✅ Deleted {videos_deleted} videos")
                    
                    # Delete all campaigns
                    cursor.execute("DELETE FROM campaigns")
                    campaigns_deleted = cursor.rowcount
                    print(f"   ✅ Deleted {campaigns_deleted} campaigns")
                    
                    conn.commit()
                    
                    response_data = json.dumps({
                        'success': True,
                        'message': 'All data wiped successfully',
                        'videos_deleted': videos_deleted,
                        'campaigns_deleted': campaigns_deleted
                    })
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Content-Length', str(len(response_data)))
                    self.end_headers()
                    self.wfile.write(response_data.encode())
                    print(f"✅ Database wiped: {videos_deleted} videos, {campaigns_deleted} campaigns")
                    return
                    
            except Exception as e:
                print(f"❌ Error wiping database: {e}")
                import traceback
                traceback.print_exc()
                response_data = json.dumps({'success': False, 'error': str(e)})
                self.send_response(500)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Content-Length', str(len(response_data)))
                self.end_headers()
                self.wfile.write(response_data.encode())
                return
                
        except Exception as e:
            print(f"EXCEPTION in handle_wipe_database: {str(e)}")
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
        """Load progress from database ONLY - Supabase is the single source of truth"""
        if DATABASE_AVAILABLE:
            try:
                progress = database.load_progress()
                if progress:
                    print(f"[LOAD] Loaded {len(progress)} videos from database")
                else:
                    print(f"[LOAD] No videos found in database")
                return progress or {}
            except Exception as e:
                print(f"❌ Database load failed: {e}")
                import traceback
                traceback.print_exc()
                # Return empty dict instead of raising - let API handlers decide how to respond
                return {}
        
        print("❌ Database module not available - cannot load data!")
        return {}
    
    def save_progress(self, progress):
        """Save progress to database ONLY - Supabase is the single source of truth"""
        if DATABASE_AVAILABLE:
            try:
                database.save_progress(progress)
                print(f"[SAVE] Saved {len(progress)} videos to database")
                return
            except Exception as e:
                print(f"❌ Database save failed: {e}")
                import traceback
                traceback.print_exc()
                raise  # Re-raise to prevent silent data loss
        
        raise Exception("Database module not available - cannot save data!")
    
    def load_campaigns(self):
        """Load campaigns from database ONLY - Supabase is the single source of truth"""
        if DATABASE_AVAILABLE:
            try:
                campaigns = database.load_campaigns()
                if campaigns:
                    print(f"[LOAD] Loaded {len(campaigns)} campaigns from database")
                    # Log video counts for debugging
                    for campaign_id, campaign_data in campaigns.items():
                        video_count = len(campaign_data.get('videos', []))
                        if video_count > 0:
                            print(f"       {campaign_id}: {video_count} videos")
                else:
                    print(f"[LOAD] No campaigns found in database")
                return campaigns or {}
            except Exception as e:
                print(f"❌ Database load failed: {e}")
                import traceback
                traceback.print_exc()
                # Return empty dict instead of raising - let API handlers decide how to respond
                return {}
        
        print("❌ Database module not available - cannot load data!")
        return {}
    
    def save_campaigns(self, campaigns):
        """Save campaigns to database ONLY - Supabase is the single source of truth"""
        if DATABASE_AVAILABLE:
            try:
                database.save_campaigns(campaigns)
                print(f"[SAVE] Saved {len(campaigns)} campaigns to database")
                return
            except Exception as e:
                print(f"❌ Database save failed: {e}")
                import traceback
                traceback.print_exc()
                raise  # Re-raise to prevent silent data loss
        
        raise Exception("Database module not available - cannot save data!")
    
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
            padding: 8px;
            color: #e0e0e0;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .header {
            background: #1a1a1a;
            border-radius: 0;
            padding: 4px 8px;
            margin-bottom: 3px;
            box-shadow: none;
            border: 1px solid rgba(255,255,255,0.05);
        }
        
        .header h1 {
            color: #ffffff;
            font-size: 1em;
            margin-bottom: 1px;
            font-weight: 600;
        }
        
        .header h1:hover {
            color: #667eea;
            text-decoration: underline;
        }
        
        .header p {
            color: #888;
            font-size: 0.7em;
            margin: 0;
        }
        
        .video-card {
            background: #1a1a1a;
            border-radius: 0;
            padding: 10px;
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
            border-radius: 0;
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
            margin-bottom: 12px;
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
            background: #1a1a1a;
            color: white;
            border: none;
            border-radius: 0;
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
            background: #1a1a1a;
        }
        
        .remove-video-btn:active {
            transform: translateY(0);
        }
        
        .status-badge {
            padding: 8px 16px;
            border-radius: 0;
            font-weight: 600;
            font-size: 0.9em;
        }
        
        .status-complete { background: #10b981; color: white; }
        .status-good { background: #3b82f6; color: white; }
        .status-moderate { background: #f59e0b; color: white; }
        .status-early { background: #ef4444; color: white; }
        
        .target-time-section {
            background: #1a1a1a;
            border-radius: 0;
            padding: 8px;
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
            border-radius: 0;
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
            background: #1a1a1a;
            color: white;
            border: none;
            border-radius: 0;
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
            padding: 10px;
            background: rgba(0,0,0,0.3);
            border-radius: 0;
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
            margin-bottom: 12px;
        }
        
        .metric {
            background: #1a1a1a;
            border-radius: 0;
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
            border-radius: 0;
            height: 24px;
            overflow: hidden;
            margin-top: 12px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        
        .progress-bar {
            height: 100%;
            background: #1a1a1a;
            border-radius: 0;
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
            background: #1a1a1a;
            border-radius: 0;
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
            border-radius: 0;
        }
        
        .milestones-section {
            margin-top: 30px;
            padding: 25px;
            background: #1a1a1a;
            border-radius: 0;
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
            border-radius: 0;
            padding: 8px;
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
            border-radius: 0;
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
            border-radius: 0;
            color: #d0d0d0;
            border-left: 2px solid rgba(102, 126, 234, 0.5);
        }
        
        .milestone-username {
            margin-top: 10px;
            padding: 8px;
            background: rgba(102, 126, 234, 0.2);
            border-radius: 0;
            color: #e0e0e0;
            border-left: 3px solid #667eea;
        }
        
        .milestone-username strong {
            color: #ffffff;
        }
        
        .comments-editor-section {
            margin-top: 30px;
            padding: 25px;
            background: #1a1a1a;
            border-radius: 0;
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
            padding: 10px;
            border: 2px solid rgba(255,255,255,0.2);
            border-radius: 0;
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
            background: #1a1a1a;
            color: white;
            border: none;
            border-radius: 0;
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
            border-radius: 0;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
        }
        
        .add-campaign-btn:hover {
            background: #333;
        }
        
        .delete-campaign-btn {
            position: absolute !important;
            top: 5px !important;
            right: 5px !important;
            z-index: 100 !important;
            display: flex !important;
            visibility: visible !important;
            opacity: 1 !important;
            background: rgba(239,68,68,0.25) !important;
            color: #ef4444 !important;
            border: 2px solid rgba(239,68,68,0.6) !important;
        }
        
        .comments-save-status {
            margin-top: 12px;
            padding: 8px;
            border-radius: 0;
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
            background: #1a1a1a;
            border-radius: 0;
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
            border-radius: 0;
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
            background: #1a1a1a;
            border-radius: 0;
            padding: 8px;
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
            border-radius: 0;
            overflow: hidden;
        }
        
        .mini-stat-progress-bar {
            height: 100%;
            background: #1a1a1a;
            border-radius: 0;
        }
        
        .back-button {
            display: inline-flex;
            align-items: center;
            gap: 3px;
            padding: 2px 8px;
            background: #1a1a1a;
            color: #ffffff;
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 0;
            text-decoration: none;
            font-weight: 500;
            font-size: 10px;
            margin-bottom: 3px;
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
            border-radius: 0;
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
            gap: 12px;
            margin-bottom: 6px;
            padding: 4px 8px;
            background: #1a1a1a;
            border-radius: 0;
            border: 1px solid rgba(255,255,255,0.05);
            flex-wrap: wrap;
            align-items: center;
        }
        
        .summary-stat-card {
            display: flex;
            align-items: baseline;
            gap: 4px;
            flex: 0 1 auto;
        }
        
        .summary-stat-label {
            color: #666;
            font-size: 0.65em;
            text-transform: uppercase;
            letter-spacing: 0.2px;
            font-weight: 500;
        }
        
        .summary-stat-value {
            color: #ffffff;
            font-size: 0.85em;
            font-weight: 600;
        }
        
        .summary-stat-change {
            display: none;
        }
        
        /* Tab Navigation */
        .tab-navigation {
            display: flex;
            gap: 2px;
            margin-bottom: 3px;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        
        .tab-btn {
            background: transparent;
            border: none;
            color: #888;
            padding: 2px 8px;
            font-size: 10px;
            font-weight: 500;
            cursor: pointer;
            border-bottom: 2px solid transparent;
            transition: all 0.2s;
            margin-bottom: -1px;
        }
        
        .tab-btn:hover {
            color: #fff;
            background: rgba(255,255,255,0.05);
        }
        
        .tab-btn.active {
            color: #667eea;
            border-bottom-color: #667eea;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        /* Search and Filter Bar */
        .controls-bar {
            background: #1a1a1a;
            border-radius: 0;
            padding: 2px 4px;
            margin-bottom: 4px;
            display: flex;
            gap: 3px;
            flex-wrap: wrap;
            align-items: center;
            border: 1px solid rgba(255,255,255,0.05);
        }
        
        .search-box {
            flex: 1;
            min-width: 120px;
            padding: 2px 6px;
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 0;
            background: #1a1a1a;
            color: #e0e0e0;
            font-size: 10px;
            transition: all 0.2s;
            height: 20px;
            line-height: 20px;
        }
        
        .search-box:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 1px rgba(102, 126, 234, 0.2);
        }
        
        .filter-select {
            padding: 2px 6px;
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 0;
            background: #1a1a1a;
            color: #e0e0e0;
            font-size: 10px;
            cursor: pointer;
            transition: all 0.2s;
            height: 20px;
            line-height: 20px;
        }
        
        .filter-select:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 1px rgba(102, 126, 234, 0.2);
        }
        
        .export-btn {
            padding: 2px 8px;
            background: #2a2a2a;
            color: #fff;
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 0;
            font-size: 9px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
            height: 20px;
            white-space: nowrap;
            line-height: 16px;
        }
        
        .export-btn:hover {
            background: #333;
        }
        
        .clear-filters-btn {
            padding: 2px 8px;
            background: #2a2a2a;
            color: #fff;
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 0;
            font-size: 9px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s;
            height: 20px;
            white-space: nowrap;
            line-height: 16px;
        }
        
        .clear-filters-btn:hover {
            background: #333;
        }
        
        .add-video-btn {
            padding: 2px 8px;
            background: #667eea;
            color: #fff;
            border: 1px solid rgba(102,126,234,0.3);
            border-radius: 0;
            font-size: 9px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s;
            height: 20px;
            white-space: nowrap;
            line-height: 16px;
        }
        
        .add-video-btn:hover {
            background: #5568d3;
        }
        
        /* Mobile Responsive Styles */
        @media (max-width: 768px) {
            body {
                padding: 10px;
            }
            
            .header {
                padding: 8px;
            }
            
            .header h1 {
                font-size: 1.8em;
            }
            
            .video-card {
                padding: 10px;
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
            
            .delete-campaign-btn {
                position: absolute !important;
                top: 5px !important;
                right: 5px !important;
                z-index: 100 !important;
                display: flex !important;
                visibility: visible !important;
                opacity: 1 !important;
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
            <h1 style="cursor: pointer;" onclick="navigateToHome();" title="Click to go home">Campaign Dashboard</h1>
            <p>Monitor your videos and set target completion times</p>
        </div>
        
        <div id="summary-stats-container"></div>
        
        <!-- Tab Navigation -->
        <div class="tab-navigation">
            <button class="tab-btn active" data-tab="dashboard" onclick="switchTab('dashboard')">Dashboard</button>
            <button class="tab-btn" data-tab="campaigns" onclick="switchTab('campaigns')">Campaigns</button>
            <button class="tab-btn" data-tab="order-log" onclick="switchTab('order-log')">Order Log</button>
        </div>
        
        <div class="controls-bar" id="dashboard-controls">
            <input type="text" id="search-box" class="search-box" placeholder="Search..." oninput="filterVideos()">
            <select id="status-filter" class="filter-select" onchange="filterVideos()">
                <option value="all">All</option>
                <option value="complete">Complete</option>
                <option value="good">Good</option>
                <option value="moderate">Moderate</option>
                <option value="early">Early</option>
            </select>
            <select id="sort-by" class="filter-select" onchange="filterVideos()">
                <option value="progress-desc">Progress: H→L</option>
                <option value="progress-asc">Progress: L→H</option>
                <option value="views-desc">Views: H→L</option>
                <option value="views-asc">Views: L→H</option>
                <option value="recent">Recent</option>
                <option value="oldest">Oldest</option>
            </select>
            <button class="export-btn" onclick="exportData()">Export</button>
            <button class="add-video-btn" onclick="showAddVideoModal()">+ Video</button>
            <button class="clear-filters-btn" onclick="clearFilters()">Clear</button>
        </div>
        
        <!-- Campaign Management Bar -->
        <div id="campaign-bar" style="display: none; background: #2a2a2a; padding: 10px; border-radius: 0; margin-bottom: 12px; border: 1px solid rgba(255,255,255,0.1);">
            <div style="display: flex; align-items: center; gap: 15px; flex-wrap: wrap;">
                <div style="flex: 1; min-width: 200px;">
                    <div style="color: #b0b0b0; font-size: 0.85em; margin-bottom: 5px;">Selected: <span id="selected-count">0</span> video(s)</div>
                    <div style="display: flex; gap: 10px;">
                        <select id="campaign-selector" style="flex: 1; padding: 8px 12px; background: #1a1a1a; border: 1px solid rgba(255,255,255,0.2); border-radius: 0; color: #fff; font-size: 14px;">
                            <option value="">Select Campaign...</option>
                        </select>
                        <button id="new-campaign-btn-bar" style="background: #10b981; color: white; border: none; padding: 6px 12px; border-radius: 0; cursor: pointer; font-weight: 600; font-size: 13px;">New Campaign</button>
                        <button onclick="assignToCampaign()" id="assign-campaign-btn" style="background: #667eea; color: white; border: none; padding: 8px 16px; border-radius: 0; cursor: pointer; font-weight: 600; font-size: 14px;" disabled>Assign</button>
                        <button onclick="clearSelection()" style="background: #444; color: white; border: none; padding: 8px 16px; border-radius: 0; cursor: pointer; font-size: 14px;">Clear</button>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Campaigns Summary -->
        <div id="campaigns-summary" style="margin-bottom: 25px;"></div>
        
        <!-- Add Video Modal -->
        <div id="add-video-modal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 10000; align-items: center; justify-content: center;">
            <div style="background: #1a1a1a; border-radius: 0; padding: 10px; max-width: 500px; width: 90%; border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 8px 32px rgba(0,0,0,0.5);">
                <h2 style="margin: 0 0 15px 0; color: #fff; font-size: 20px;">Add Video to Campaign</h2>
                <p style="color: #b0b0b0; margin-bottom: 12px; font-size: 14px;">Enter a TikTok video URL to start tracking it in your campaign.</p>
                <div style="margin-bottom: 12px;">
                    <label style="display: block; color: #fff; margin-bottom: 8px; font-weight: 600;">Assign to Campaign (optional)</label>
                    <div style="display: flex; gap: 10px;">
                        <select id="add-video-campaign-selector" style="flex: 1; padding: 10px 12px; background: #252525; border: 1px solid rgba(255,255,255,0.2); border-radius: 0; color: #fff; font-size: 14px;">
                            <option value="">No campaign</option>
                        </select>
                        <button id="add-video-new-campaign-btn" style="background: #10b981; color: white; border: none; padding: 8px 12px; border-radius: 0; cursor: pointer; font-weight: 700; font-size: 12px;">New</button>
                    </div>
                    <div style="color: #888; font-size: 12px; margin-top: 6px;">If you choose a campaign, we’ll apply that campaign’s goals & speed to this post.</div>
                </div>
                <div style="margin-bottom: 12px;">
                    <label style="display: block; color: #fff; margin-bottom: 8px; font-weight: 600;">Add Video URL</label>
                    <div style="display: flex; gap: 8px;">
                        <input type="text" id="new-video-url-input" placeholder="https://www.tiktok.com/@username/video/1234567890" style="flex: 1; padding: 10px 12px; border-radius: 0; border: 1px solid rgba(255,255,255,0.2); background: #252525; color: #fff; font-size: 14px; font-family: monospace;" onkeypress="if(event.key === 'Enter') { event.preventDefault(); addUrlToList(); }">
                        <button onclick="addUrlToList()" style="background: #667eea; color: white; border: none; padding: 10px 16px; border-radius: 0; cursor: pointer; font-weight: 700; font-size: 18px; min-width: 48px; line-height: 1;">+</button>
                    </div>
                </div>
                <div id="url-list-container" style="margin-bottom: 12px; display: none;">
                    <label style="display: block; color: #fff; margin-bottom: 8px; font-weight: 600;">URLs to Add (<span id="url-count">0</span>)</label>
                    <div id="url-list" style="background: #252525; border: 1px solid rgba(255,255,255,0.1); padding: 8px; max-height: 200px; overflow-y: auto;"></div>
                </div>
                <textarea id="new-video-url" style="display: none;"></textarea>
                <div id="add-video-progress" style="display: none; margin-bottom: 15px;">
                    <div style="color: #667eea; font-size: 13px; margin-bottom: 8px;">Adding videos...</div>
                    <div style="background: #252525; border-radius: 0; padding: 8px; max-height: 200px; overflow-y: auto;">
                        <div id="add-video-progress-list" style="color: #b0b0b0; font-size: 12px; font-family: monospace;"></div>
                    </div>
                    <div style="background: #252525; height: 4px; border-radius: 0; margin-top: 8px; overflow: hidden;">
                        <div id="add-video-progress-bar" style="background: #1a1a1a; height: 100%; width: 0%; transition: width 0.3s;"></div>
                    </div>
                </div>
                <div id="add-video-error" style="color: #ff4444; font-size: 13px; margin-bottom: 15px; display: none;"></div>
                <div id="add-video-success" style="color: #10b981; font-size: 13px; margin-bottom: 15px; display: none;"></div>
                <div style="display: flex; gap: 10px; justify-content: flex-end;">
                    <button onclick="hideAddVideoModal()" id="add-video-cancel-btn" style="padding: 10px 20px; border-radius: 0; border: 1px solid rgba(255,255,255,0.2); background: transparent; color: #fff; cursor: pointer; font-size: 14px;">Cancel</button>
                    <button onclick="addVideo()" id="add-video-submit-btn" style="padding: 10px 20px; border-radius: 0; border: none; background: #1a1a1a; color: white; cursor: pointer; font-weight: 600; font-size: 14px;">Add Video(s)</button>
                </div>
            </div>
        </div>

        <!-- Create Campaign Modal -->
        <div id="create-campaign-modal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 10002; align-items: center; justify-content: center;">
            <div style="background: #1a1a1a; border-radius: 0; padding: 10px; max-width: 500px; width: 90%; border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 8px 32px rgba(0,0,0,0.5);">
                <h2 style="margin: 0 0 20px 0; color: #fff; font-size: 24px;">Create New Campaign</h2>
                <p style="color: #b0b0b0; margin-bottom: 12px; font-size: 14px;">Create a new campaign to group videos and track financial performance.</p>
                <div style="margin-bottom: 12px;">
                    <label style="display: block; color: #fff; margin-bottom: 8px; font-weight: 600;">Campaign Name</label>
                    <input type="text" id="new-campaign-name" placeholder="e.g., Q1 2026 Campaign" style="width: 100%; padding: 8px; background: #2a2a2a; border: 1px solid rgba(255,255,255,0.2); border-radius: 0; color: #fff; font-size: 14px; box-sizing: border-box;">
                </div>
                <div style="margin-bottom: 12px;">
                    <label style="display: block; color: #fff; margin-bottom: 8px; font-weight: 600;">CPM (Cost Per Mille)</label>
                    <p style="color: #b0b0b0; font-size: 12px; margin-bottom: 8px;">How much you get paid per 1,000 views (e.g., 2.50 = $2.50 per 1000 views)</p>
                    <input type="number" id="new-campaign-cpm" placeholder="0.00" step="0.01" min="0" style="width: 100%; padding: 8px; background: #2a2a2a; border: 1px solid rgba(255,255,255,0.2); border-radius: 0; color: #fff; font-size: 14px; box-sizing: border-box;">
                </div>
                <div style="margin-bottom: 12px;">
                    <label style="display: block; color: #fff; margin-bottom: 8px; font-weight: 600;">Goals per Post</label>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                        <div>
                            <div style="color: #b0b0b0; font-size: 12px; margin-bottom: 6px;">Views goal</div>
                            <input type="number" id="new-campaign-target-views" placeholder="4000" min="0" step="1" style="width: 100%; padding: 10px; background: #2a2a2a; border: 1px solid rgba(255,255,255,0.2); border-radius: 0; color: #fff; font-size: 14px; box-sizing: border-box;">
                        </div>
                        <div>
                            <div style="color: #b0b0b0; font-size: 12px; margin-bottom: 6px;">Likes goal</div>
                            <input type="number" id="new-campaign-target-likes" placeholder="125" min="0" step="1" style="width: 100%; padding: 10px; background: #2a2a2a; border: 1px solid rgba(255,255,255,0.2); border-radius: 0; color: #fff; font-size: 14px; box-sizing: border-box;">
                        </div>
                        <div>
                            <div style="color: #b0b0b0; font-size: 12px; margin-bottom: 6px;">Comments goal</div>
                            <input type="number" id="new-campaign-target-comments" placeholder="7" min="0" step="1" style="width: 100%; padding: 10px; background: #2a2a2a; border: 1px solid rgba(255,255,255,0.2); border-radius: 0; color: #fff; font-size: 14px; box-sizing: border-box;">
                        </div>
                        <div>
                            <div style="color: #b0b0b0; font-size: 12px; margin-bottom: 6px;">Comment likes goal</div>
                            <input type="number" id="new-campaign-target-comment-likes" placeholder="15" min="0" step="1" style="width: 100%; padding: 10px; background: #2a2a2a; border: 1px solid rgba(255,255,255,0.2); border-radius: 0; color: #fff; font-size: 14px; box-sizing: border-box;">
                        </div>
                    </div>
                </div>
                <div style="margin-bottom: 12px;">
                    <label style="display: block; color: #fff; margin-bottom: 8px; font-weight: 600;">Growth Speed</label>
                    <p style="color: #b0b0b0; font-size: 12px; margin-bottom: 8px;">How long each post should take to reach the goal (used to set the target completion time).</p>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                        <div>
                            <div style="color: #b0b0b0; font-size: 12px; margin-bottom: 6px;">Hours</div>
                            <input type="number" id="new-campaign-duration-hours" placeholder="24" min="0" step="1" style="width: 100%; padding: 10px; background: #2a2a2a; border: 1px solid rgba(255,255,255,0.2); border-radius: 0; color: #fff; font-size: 14px; box-sizing: border-box;">
                        </div>
                        <div>
                            <div style="color: #b0b0b0; font-size: 12px; margin-bottom: 6px;">Minutes</div>
                            <input type="number" id="new-campaign-duration-minutes" placeholder="0" min="0" step="1" style="width: 100%; padding: 10px; background: #2a2a2a; border: 1px solid rgba(255,255,255,0.2); border-radius: 0; color: #fff; font-size: 14px; box-sizing: border-box;">
                        </div>
                    </div>
                </div>
                <div id="create-campaign-error" style="color: #ef4444; margin-bottom: 15px; font-size: 14px; display: none;"></div>
                <div style="display: flex; gap: 10px; justify-content: flex-end;">
                    <button onclick="hideCreateCampaignModal()" style="background: #444; color: white; border: none; padding: 10px 20px; border-radius: 0; cursor: pointer;">Cancel</button>
                    <button onclick="createCampaign()" style="background: #10b981; color: white; border: none; padding: 10px 20px; border-radius: 0; cursor: pointer; font-weight: 600;">Create Campaign</button>
                </div>
            </div>
        </div>
        
        <!-- Edit Time Left Modal -->
        <div id="edit-time-left-modal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 10004; align-items: center; justify-content: center;">
            <div style="background: #1a1a1a; border-radius: 0; padding: 20px; max-width: 400px; width: 90%; border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 8px 32px rgba(0,0,0,0.5);">
                <h2 style="margin: 0 0 15px 0; color: #fff; font-size: 20px;">Edit Time Left</h2>
                <p style="color: #b0b0b0; margin-bottom: 15px; font-size: 13px;">Set how much time is left for this video to reach its goal.</p>
                <div style="margin-bottom: 15px;">
                    <label style="display: block; color: #fff; margin-bottom: 8px; font-weight: 600; font-size: 13px;">Hours</label>
                    <input type="number" id="edit-time-hours" placeholder="0" min="0" step="1" style="width: 100%; padding: 8px; background: #2a2a2a; border: 1px solid rgba(255,255,255,0.2); border-radius: 0; color: #fff; font-size: 14px; box-sizing: border-box;">
                </div>
                <div style="margin-bottom: 15px;">
                    <label style="display: block; color: #fff; margin-bottom: 8px; font-weight: 600; font-size: 13px;">Minutes</label>
                    <input type="number" id="edit-time-minutes" placeholder="0" min="0" max="59" step="1" style="width: 100%; padding: 8px; background: #2a2a2a; border: 1px solid rgba(255,255,255,0.2); border-radius: 0; color: #fff; font-size: 14px; box-sizing: border-box;">
                </div>
                <div id="edit-time-error" style="color: #ef4444; margin-bottom: 15px; font-size: 13px; display: none;"></div>
                <div style="display: flex; gap: 10px; justify-content: flex-end;">
                    <button onclick="hideEditTimeLeftModal()" style="background: #444; color: white; border: none; padding: 8px 16px; border-radius: 0; cursor: pointer; font-size: 13px;">Cancel</button>
                    <button onclick="saveTimeLeft()" style="background: #10b981; color: white; border: none; padding: 8px 16px; border-radius: 0; cursor: pointer; font-weight: 600; font-size: 13px;">Save</button>
                </div>
            </div>
        </div>

        <!-- Video Details Modal -->
        <div id="video-details-modal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 10005; align-items: center; justify-content: center; overflow-y: auto;">
            <div style="background: #1a1a1a; border-radius: 0; padding: 20px; max-width: 700px; width: 90%; max-height: 90vh; border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 8px 32px rgba(0,0,0,0.5); margin: 20px 0;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <h2 style="margin: 0; color: #fff; font-size: 20px;">Video Details</h2>
                    <button onclick="hideVideoDetailsModal()" style="background: transparent; color: #fff; border: none; font-size: 24px; cursor: pointer; padding: 0; width: 30px; height: 30px; line-height: 30px;">&times;</button>
                </div>
                <div id="video-details-content" style="color: #fff; font-size: 13px; line-height: 1.6;">
                    <p style="color: #b0b0b0;">Loading...</p>
                </div>
            </div>
        </div>

        <!-- Edit Campaign Modal -->
        <div id="edit-campaign-modal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 10003; align-items: center; justify-content: center;">
            <div style="background: #1a1a1a; border-radius: 0; padding: 10px; max-width: 500px; width: 90%; border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 8px 32px rgba(0,0,0,0.5);">
                <h2 style="margin: 0 0 20px 0; color: #fff; font-size: 24px;">Edit Campaign</h2>
                <p style="color: #b0b0b0; margin-bottom: 12px; font-size: 14px;">Update campaign CPM and goals.</p>
                <div style="margin-bottom: 12px;">
                    <label style="display: block; color: #fff; margin-bottom: 8px; font-weight: 600;">Campaign Name</label>
                    <input type="text" id="edit-campaign-name" placeholder="e.g., Q1 2026 Campaign" style="width: 100%; padding: 8px; background: #2a2a2a; border: 1px solid rgba(255,255,255,0.2); border-radius: 0; color: #fff; font-size: 14px; box-sizing: border-box;">
                </div>
                <div style="margin-bottom: 12px;">
                    <label style="display: block; color: #fff; margin-bottom: 8px; font-weight: 600;">CPM (Cost Per Mille)</label>
                    <p style="color: #b0b0b0; font-size: 12px; margin-bottom: 8px;">How much you get paid per 1,000 views (e.g., 2.50 = $2.50 per 1000 views)</p>
                    <input type="number" id="edit-campaign-cpm" placeholder="0.00" step="0.01" min="0" style="width: 100%; padding: 8px; background: #2a2a2a; border: 1px solid rgba(255,255,255,0.2); border-radius: 0; color: #fff; font-size: 14px; box-sizing: border-box;">
                </div>
                <div style="margin-bottom: 12px;">
                    <label style="display: block; color: #fff; margin-bottom: 8px; font-weight: 600;">Goals per Post</label>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                        <div>
                            <div style="color: #b0b0b0; font-size: 12px; margin-bottom: 6px;">Views goal</div>
                            <input type="number" id="edit-campaign-target-views" placeholder="4000" min="0" step="1" style="width: 100%; padding: 10px; background: #2a2a2a; border: 1px solid rgba(255,255,255,0.2); border-radius: 0; color: #fff; font-size: 14px; box-sizing: border-box;">
                        </div>
                        <div>
                            <div style="color: #b0b0b0; font-size: 12px; margin-bottom: 6px;">Likes goal</div>
                            <input type="number" id="edit-campaign-target-likes" placeholder="125" min="0" step="1" style="width: 100%; padding: 10px; background: #2a2a2a; border: 1px solid rgba(255,255,255,0.2); border-radius: 0; color: #fff; font-size: 14px; box-sizing: border-box;">
                        </div>
                        <div>
                            <div style="color: #b0b0b0; font-size: 12px; margin-bottom: 6px;">Comments goal</div>
                            <input type="number" id="edit-campaign-target-comments" placeholder="7" min="0" step="1" style="width: 100%; padding: 10px; background: #2a2a2a; border: 1px solid rgba(255,255,255,0.2); border-radius: 0; color: #fff; font-size: 14px; box-sizing: border-box;">
                        </div>
                        <div>
                            <div style="color: #b0b0b0; font-size: 12px; margin-bottom: 6px;">Comment likes goal</div>
                            <input type="number" id="edit-campaign-target-comment-likes" placeholder="15" min="0" step="1" style="width: 100%; padding: 10px; background: #2a2a2a; border: 1px solid rgba(255,255,255,0.2); border-radius: 0; color: #fff; font-size: 14px; box-sizing: border-box;">
                        </div>
                    </div>
                </div>
                <div style="margin-bottom: 12px;">
                    <label style="display: block; color: #fff; margin-bottom: 8px; font-weight: 600;">Growth Speed</label>
                    <p style="color: #b0b0b0; font-size: 12px; margin-bottom: 8px;">How long each post should take to reach the goal (used to set the target completion time).</p>
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
                        <div>
                            <div style="color: #b0b0b0; font-size: 12px; margin-bottom: 6px;">Hours</div>
                            <input type="number" id="edit-campaign-duration-hours" placeholder="24" min="0" step="1" style="width: 100%; padding: 10px; background: #2a2a2a; border: 1px solid rgba(255,255,255,0.2); border-radius: 0; color: #fff; font-size: 14px; box-sizing: border-box;">
                        </div>
                        <div>
                            <div style="color: #b0b0b0; font-size: 12px; margin-bottom: 6px;">Minutes</div>
                            <input type="number" id="edit-campaign-duration-minutes" placeholder="0" min="0" step="1" style="width: 100%; padding: 10px; background: #2a2a2a; border: 1px solid rgba(255,255,255,0.2); border-radius: 0; color: #fff; font-size: 14px; box-sizing: border-box;">
                        </div>
                    </div>
                </div>
                <div id="edit-campaign-error" style="color: #ef4444; margin-bottom: 15px; font-size: 14px; display: none;"></div>
                <div style="display: flex; gap: 10px; justify-content: flex-end;">
                    <button onclick="hideEditCampaignModal()" style="background: #444; color: white; border: none; padding: 10px 20px; border-radius: 0; cursor: pointer;">Cancel</button>
                    <button onclick="updateCampaign()" style="background: #10b981; color: white; border: none; padding: 10px 20px; border-radius: 0; cursor: pointer; font-weight: 600;">Update Campaign</button>
                </div>
            </div>
        </div>
        
        <div id="dashboard-content" class="tab-content active">
            <div class="loading">Loading...</div>
        </div>
        
        <div id="campaigns-content" class="tab-content">
            <div id="campaigns-summary"></div>
        </div>
        
        <div id="order-log-content" class="tab-content">
            <div class="loading">Loading order log...</div>
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
    
    <!-- Global Loading Overlay -->
    <div id="global-loading" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); z-index: 99999; align-items: center; justify-content: center; flex-direction: column;">
        <div style="background: #1a1a1a; padding: 20px 30px; border-radius: 0; border: 1px solid rgba(255,255,255,0.1); display: flex; align-items: center; gap: 15px;">
            <div class="spinner" style="width: 24px; height: 24px; border: 3px solid rgba(102,126,234,0.3); border-top-color: #667eea; border-radius: 50%; animation: spin 0.8s linear infinite;"></div>
            <span id="loading-message" style="color: #fff; font-size: 14px; font-weight: 600;">Loading...</span>
        </div>
    </div>
    
    <style>
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        .spinner {
            animation: spin 0.8s linear infinite;
        }
    </style>
    
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
            if (progress >= 75) return 'Good Progress';
            if (progress >= 50) return 'Moderate';
            return 'Early Stage';
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
        
        function calculateTimeRemaining(targetTime, isOvertimeStopped = false) {
            if (!targetTime) return null;
            try {
                const target = new Date(targetTime);
                const now = new Date();
                const diff = target - now;
                if (diff < 0) {
                    if (isOvertimeStopped) {
                        return 'Overtime stopped';
                    }
                    return 'OVERTIME';
                }
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
                return String(str)
                    .split('\\\\').join('\\\\\\\\')  // Escape backslashes first
                    .split("'").join("\\\\'")
                    .split('`').join('\\\\`')
                    .split('$').join('\\\\$');
            }
            if (!confirm(`Are you sure you want to remove this video from the process?\\n\\nVideo: ${escapeForTemplate(videoUrl)}\\n\\nThis will stop tracking but won't cancel existing orders.`)) {
                return;
            }
            
            try {
                showLoading('Removing video...');
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
                hideLoading();
                
                if (data.success) {
                    showNotification('Video removed successfully', 'success');
                    invalidateCache(); // Force fresh data
                    // Navigate to home if we're on detail page
                    const route = getCurrentRoute();
                    if (route.type === 'detail') {
                        navigateToHome();
                    } else {
                        // Fast refresh in background
                        loadDashboard(false, true);
                    }
                } else {
                    alert('Error: ' + (data.error || 'Failed to remove video'));
                }
            } catch (error) {
                hideLoading();
                console.error('Error:', error);
                alert('Error removing video: ' + error.message);
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
            button.textContent = 'Placing...';
            showLoading(`Placing order for ${amount.toLocaleString()} ${metric}...`);
            
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
                hideLoading();
                if (data.success) {
                    showNotification(`Order placed! ID: ${data.order_id}`, 'success');
                    invalidateCache();
                    loadDashboard(false, true); // Background refresh
                } else {
                    alert('Error: ' + (data.error || 'Failed to place catch-up order'));
                    button.disabled = false;
                    button.textContent = originalText;
                }
            } catch (error) {
                hideLoading();
                console.error('Error:', error);
                alert('Error placing catch-up order: ' + error.message);
                button.disabled = false;
                button.textContent = originalText;
            }
        }
        
        async function manualOrder(videoUrl, metric, minimum, buttonElement) {
            showLoading(`Placing manual order for ${metric}...`);
            const button = buttonElement || (event && event.target) || null;
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
            
            const originalText = button ? button.textContent : '';
            if (button) {
                button.disabled = true;
                button.textContent = 'Placing...';
            }
            showLoading(`Placing manual order for ${amount.toLocaleString()} ${metric}...`);
            
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
                hideLoading();
                if (data.success) {
                    showNotification(`Manual order placed! ID: ${data.order_id}`, 'success');
                    invalidateCache();
                    loadDashboard(false, true); // Background refresh
                } else {
                    alert('Error: ' + (data.error || 'Failed to place manual order'));
                    if (button) {
                        button.disabled = false;
                        button.textContent = originalText;
                    }
                }
            } catch (error) {
                hideLoading();
                console.error('Error:', error);
                alert('Error placing manual order: ' + error.message);
                if (button) {
                    button.disabled = false;
                    button.textContent = originalText;
                }
            }
        }
        
        async function saveComments(videoUrl, textareaId) {
            showLoading('Saving comments...');
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
                        loadDashboard(false).catch(() => {});
                        statusDiv.className = 'comments-save-status';
                    }, 2000);
                } else {
                    statusDiv.className = 'comments-save-status error';
                    statusDiv.textContent = `Error: ${data.error || 'Failed to save comments'}`;
                }
            } catch (error) {
                console.error('Error:', error);
                statusDiv.className = 'comments-save-status error';
                statusDiv.textContent = `Error: ${error.message}`;
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
                    alert('Error: ' + (data.error || 'Failed to order comments'));
                    button.disabled = false;
                    button.textContent = originalText;
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Error ordering comments: ' + error.message);
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
                        <div style="background: #1a1a1a; border-radius: 0; padding: 10px; max-width: 700px; width: 90%; margin: 20px auto; border: 1px solid rgba(255,255,255,0.1); box-shadow: 0 8px 32px rgba(0,0,0,0.5); max-height: 90vh; overflow-y: auto;">
                            <h2 style="margin: 0 0 20px 0; color: #fff; font-size: 24px;">📝 Select Comments to Boost</h2>
                            <div id="comment-selection-loading" style="color: #b0b0b0; text-align: center; padding: 8px;">Loading comments...</div>
                            <div id="comment-selection-list" style="display: none; margin-bottom: 12px;"></div>
                            <div id="comment-selection-error" style="display: none; color: #ef4444; margin-bottom: 12px;"></div>
                            <div style="display: flex; gap: 10px; justify-content: flex-end;">
                                <button onclick="hideCommentSelectionModal()" style="background: #444; color: white; border: none; padding: 10px 20px; border-radius: 0; cursor: pointer;">Cancel</button>
                                <button id="order-comment-likes-btn" onclick="orderSelectedCommentLikes()" style="background: #667eea; color: white; border: none; padding: 10px 20px; border-radius: 0; cursor: pointer; display: none;">🚀 Order Likes for Selected</button>
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
                            <div style="background: #2a2a2a; border: 1px solid rgba(255,255,255,0.1); border-radius: 0; padding: 10px; margin-bottom: 10px;">
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
                    alert('Error: ' + (data.error || 'Failed to order comment likes'));
                    orderBtn.disabled = false;
                    orderBtn.textContent = originalText;
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Error ordering comment likes: ' + error.message);
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
                    alert('Error: ' + (data.error || 'Failed to update'));
                }
            } catch (error) {
                console.error('Error:', error);
                alert('Error updating target time: ' + error.message);
            }
        }
        
        // Campaign Management Functions
        let campaignsData = {};
        
        async function loadCampaigns() {
            try {
                const response = await fetch('/api/campaigns');
                
                // Handle server errors gracefully
                if (!response.ok) {
                    console.warn(`[loadCampaigns] Server error ${response.status}`);
                    campaignsData = {}; // Use empty campaigns on error
                    return;
                }
                
                // Try to parse JSON, handle empty/invalid responses
                let data;
                try {
                    const text = await response.text();
                    if (!text || text.trim() === '') {
                        console.warn('[loadCampaigns] Empty response');
                        campaignsData = {};
                        return;
                    }
                    data = JSON.parse(text);
                } catch (parseError) {
                    console.error('[loadCampaigns] Failed to parse JSON:', parseError);
                    campaignsData = {};
                    return;
                }
                
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
            // Prevent duplicate submissions
            const createBtn = document.querySelector('#create-campaign-modal button[onclick="createCampaign()"]');
            if (createBtn && createBtn.disabled) {
                return; // Already submitting
            }
            
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
            
            // Disable button and show loading state
            if (createBtn) {
                createBtn.disabled = true;
                const originalText = createBtn.textContent;
                createBtn.textContent = 'Creating...';
                createBtn.style.opacity = '0.6';
                createBtn.style.cursor = 'not-allowed';
                
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
                        invalidateCache(); // Force fresh data
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
                } finally {
                    // Re-enable button
                    createBtn.disabled = false;
                    createBtn.textContent = originalText;
                    createBtn.style.opacity = '1';
                    createBtn.style.cursor = 'pointer';
                }
            } else {
                // Fallback if button not found
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
        }
        
        async function stopOvertime(videoUrl) {
            if (!confirm('Stop overtime mode for this video? Orders will no longer be placed until goal is reached.')) {
                return;
            }
            
            try {
                showLoading('Stopping overtime...');
                const response = await fetch(`/api/stop-overtime?video_url=${encodeURIComponent(videoUrl)}`, {
                    method: 'POST'
                });
                
                const data = await response.json();
                hideLoading();
                
                if (data.success) {
                    showNotification('Overtime stopped successfully', 'success');
                    invalidateCache();
                    loadDashboard(false, true); // Background refresh
                } else {
                    alert('Error: ' + (data.error || 'Failed to stop overtime'));
                }
            } catch (error) {
                hideLoading();
                alert('Error: ' + error.message);
            }
        }
        
        async function endCampaign(campaignId) {
            if (!confirm('Are you sure you want to end this campaign? The campaign will remain visible for stats tracking, but no new orders will be placed.')) {
                return;
            }
            
            try {
                showLoading('Ending campaign...');
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
                hideLoading();
                
                if (data.success) {
                    showNotification('Campaign ended successfully', 'success');
                    invalidateCache(); // Force fresh data
                    await loadCampaigns();
                    await loadDashboard(false, true);
                } else {
                    alert('Error: ' + (data.error || 'Failed to end campaign'));
                }
            } catch (error) {
                hideLoading();
                alert('Error: ' + error.message);
            }
        }
        
        async function deleteCampaign(campaignId, campaignName) {
            // Escape campaignName for use in confirm dialog
            function escapeForConfirm(str) {
                if (!str) return '';
                return String(str)
                    .split('\\\\').join('\\\\\\\\')  // Escape backslashes first
                    .split('"').join('\\\\\"')     // Escape double quotes
                    .split("'").join("\\\\'")     // Escape single quotes
                    .split('\\n').join('\\\\n')    // Escape newlines
                    .split('\\r').join('\\\\r');   // Escape carriage returns
            }
            const safeName = escapeForConfirm(campaignName || 'Unnamed Campaign');
            if (!confirm(`Are you sure you want to DELETE "${safeName}"?\\n\\nThis action cannot be undone. All campaign data will be permanently removed.`)) {
                return;
            }
            
            // Double confirmation for safety
            if (!confirm('⚠️ FINAL WARNING: This will permanently delete the campaign and all its data.\\n\\nClick OK to confirm deletion.')) {
                return;
            }
            
            try {
                showLoading('Deleting campaign...');
                const params = new URLSearchParams({
                    campaign_id: campaignId
                });
                
                const response = await fetch('/api/delete-campaign?' + params.toString(), {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: params.toString()
                });
                
                const data = await response.json();
                hideLoading();
                
                if (data.success) {
                    showNotification('Campaign deleted successfully', 'success');
                    invalidateCache(); // Force fresh data
                    await loadCampaigns();
                    await loadDashboard(false, true);
                    // Navigate to home if we're viewing this campaign
                    if (typeof getCurrentRoute === 'function') {
                        const route = getCurrentRoute();
                        if (route.type === 'campaign' && route.campaignId === campaignId) {
                            if (typeof navigateToHome === 'function') {
                                navigateToHome();
                            }
                        }
                    }
                } else {
                    alert('Error: ' + (data.error || 'Failed to delete campaign'));
                }
            } catch (error) {
                hideLoading();
                alert('Error: ' + error.message);
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
        
        // Edit Time Left Modal Functions
        let currentEditTimeVideoUrl = null;
        
        function showEditTimeLeftModal(videoUrl, currentHours = 0, currentMinutes = 0) {
            currentEditTimeVideoUrl = videoUrl;
            const modal = document.getElementById('edit-time-left-modal');
            document.getElementById('edit-time-hours').value = currentHours || '';
            document.getElementById('edit-time-minutes').value = currentMinutes || '';
            document.getElementById('edit-time-error').style.display = 'none';
            modal.style.display = 'flex';
        }
        
        function hideEditTimeLeftModal() {
            const modal = document.getElementById('edit-time-left-modal');
            modal.style.display = 'none';
            currentEditTimeVideoUrl = null;
        }
        
        async function saveTimeLeft() {
            if (!currentEditTimeVideoUrl) return;
            
            const hours = parseInt(document.getElementById('edit-time-hours').value) || 0;
            const minutes = parseInt(document.getElementById('edit-time-minutes').value) || 0;
            showLoading('Saving time left...');
            
            if (hours === 0 && minutes === 0) {
                hideLoading();
                document.getElementById('edit-time-error').textContent = 'Please enter at least 1 minute';
                document.getElementById('edit-time-error').style.display = 'block';
                return;
            }
            
            // Disable save button to prevent multiple submissions
            const saveButton = document.querySelector('#edit-time-left-modal button[onclick="saveTimeLeft()"]');
            if (saveButton) {
                saveButton.disabled = true;
                saveButton.textContent = 'Saving...';
            }
            
            try {
                const now = new Date();
                const targetTime = new Date(now.getTime() + (hours * 60 + minutes) * 60 * 1000);
                
                const response = await fetch(`/api/update-video-time?video_url=${encodeURIComponent(currentEditTimeVideoUrl)}&target_completion_time=${encodeURIComponent(targetTime.toISOString())}`, {
                    method: 'POST'
                });
                
                // Handle server errors
                if (!response.ok) {
                    throw new Error(`Server error: ${response.status}`);
                }
                
                let result;
                try {
                    result = await response.json();
                } catch (parseError) {
                    throw new Error('Failed to parse server response');
                }
                
                if (result.success) {
                    hideLoading();
                    // Show "Saved" feedback briefly before closing
                    if (saveButton) {
                        saveButton.textContent = 'Saved ✓';
                        saveButton.style.background = '#10b981';
                    }
                    
                    // Update the UI immediately without waiting for full refresh
                    const targetTime = new Date(now.getTime() + (hours * 60 + minutes) * 60 * 1000);
                    
                    // Update the time left cell directly if visible
                    // Find cell by iterating through all time-left cells (more reliable than querySelector with special chars)
                    const timeLeftCells = document.querySelectorAll('[data-time-left]');
                    let timeLeftCell = null;
                    for (const cell of timeLeftCells) {
                        if (cell.getAttribute('data-video-url') === currentEditTimeVideoUrl) {
                            timeLeftCell = cell;
                            break;
                        }
                    }
                    if (timeLeftCell) {
                        const remainingMs = targetTime - new Date();
                        if (remainingMs > 0) {
                            const remainingHours = Math.floor(remainingMs / (1000 * 60 * 60));
                            const remainingMinutes = Math.floor((remainingMs % (1000 * 60 * 60)) / (1000 * 60));
                            const remainingSeconds = Math.floor((remainingMs % (1000 * 60)) / 1000);
                            timeLeftCell.textContent = remainingHours + 'h' + (remainingMinutes > 0 ? remainingMinutes + 'm' : '') + remainingSeconds + 's';
                            timeLeftCell.setAttribute('data-target-time', targetTime.toISOString());
                            timeLeftCell.style.color = '#fff';
                        } else {
                            // Check if overtime is stopped - fetch current video data
                            const isOvertimeStopped = allVideosData && allVideosData[currentEditTimeVideoUrl] && allVideosData[currentEditTimeVideoUrl].overtime_stopped === true;
                            if (isOvertimeStopped) {
                                timeLeftCell.textContent = 'Overtime stopped';
                                timeLeftCell.style.color = '#888';
                            } else {
                                timeLeftCell.textContent = 'OVERTIME';
                                timeLeftCell.style.color = '#f59e0b';
                            }
                        }
                    }
                    
                    // Close modal after brief delay, then reset button
                    setTimeout(() => {
                        hideEditTimeLeftModal();
                        // Reset button after modal closes so user can save another edit
                        if (saveButton) {
                            saveButton.disabled = false;
                            saveButton.textContent = 'Save';
                            saveButton.style.background = '';
                        }
                        // Refresh in background without blocking
                        loadDashboard(false).catch(err => console.error('[saveTimeLeft] Background refresh error:', err));
                    }, 800);
                } else {
                    hideLoading();
                    document.getElementById('edit-time-error').textContent = result.error || 'Failed to update time';
                    document.getElementById('edit-time-error').style.display = 'block';
                    if (saveButton) {
                        saveButton.disabled = false;
                        saveButton.textContent = 'Save';
                    }
                }
            } catch (error) {
                hideLoading();
                document.getElementById('edit-time-error').textContent = 'Error: ' + error.message;
                document.getElementById('edit-time-error').style.display = 'block';
                if (saveButton) {
                    saveButton.disabled = false;
                    saveButton.textContent = 'Save';
                }
            }
        }
        
        // Video Details Modal Functions
        let currentVideoDetailsUrl = null;
        
        async function showVideoDetailsModal(videoUrl) {
            currentVideoDetailsUrl = videoUrl;
            const modal = document.getElementById('video-details-modal');
            const content = document.getElementById('video-details-content');
            content.innerHTML = '<p style="color: #b0b0b0;">Loading...</p>';
            modal.style.display = 'flex';
            
            try {
                // Fetch video data
                const response = await fetch(`/api/video-details?video_url=${encodeURIComponent(videoUrl)}`);
                const result = await response.json();
                
                if (result.success && result.video) {
                    const video = result.video;
                    const { username, videoId } = extractVideoInfo(videoUrl);
                    
                    // Escape videoUrl for use in onclick handlers - use same escaping as elsewhere
                    function escapeTemplateLiteral(str) {
                        if (!str) return '';
                        return String(str)
                            .split('\\\\').join('\\\\\\\\')  // Escape backslashes first
                            .split("'").join("\\\\'")
                            .split('`').join('\\\\`')
                            .split('$').join('\\\\$');
                    }
                    const safeVideoUrlAttr = escapeTemplateLiteral(videoUrl);
                    
                    let html = `
                        <div style="margin-bottom: 15px;">
                            <h3 style="color: #fff; margin: 0 0 10px 0; font-size: 16px;">Video Information</h3>
                            <p style="margin: 5px 0;"><strong style="color: #667eea;">Video ID:</strong> <a href="${escapeTemplateLiteral(videoUrl)}" target="_blank" style="color: #667eea; text-decoration: none;">${videoId}</a></p>
                            <p style="margin: 5px 0;"><strong style="color: #667eea;">URL:</strong> <a href="${escapeTemplateLiteral(videoUrl)}" target="_blank" style="color: #667eea; text-decoration: none; word-break: break-all;">${escapeTemplateLiteral(videoUrl)}</a></p>
                            <p style="margin: 5px 0;"><strong style="color: #667eea;">Username:</strong> ${username || 'N/A'}</p>
                            <p style="margin: 5px 0;"><strong style="color: #667eea;">Date Posted:</strong> ${video.start_time ? new Date(video.start_time).toLocaleString() : 'N/A'}</p>
                        </div>
                        <div style="margin-bottom: 15px;">
                            <h3 style="color: #fff; margin: 0 0 10px 0; font-size: 16px;">Current Metrics</h3>
                            <p style="margin: 5px 0;"><strong style="color: #667eea;">Views:</strong> ${formatNumber(video.real_views || video.initial_views || 0)}</p>
                            <p style="margin: 5px 0;"><strong style="color: #667eea;">Likes:</strong> ${formatNumber(video.real_likes || video.initial_likes || 0)}</p>
                            <p style="margin: 5px 0;"><strong style="color: #667eea;">Comments:</strong> ${formatNumber(video.real_comments || video.initial_comments || 0)}</p>
                        </div>
                        <div style="margin-bottom: 15px;">
                            <h3 style="color: #fff; margin: 0 0 10px 0; font-size: 16px;">Targets</h3>
                            <p style="margin: 5px 0;"><strong style="color: #667eea;">Target Views:</strong> ${formatNumber(video.target_views || 0)}</p>
                            <p style="margin: 5px 0;"><strong style="color: #667eea;">Target Likes:</strong> ${formatNumber(video.target_likes || 0)}</p>
                            <p style="margin: 5px 0;"><strong style="color: #667eea;">Target Comments:</strong> ${formatNumber(video.target_comments || 0)}</p>
                        </div>
                    `;
                    
                    const targetCompletion = video.target_completion_time || video.target_completion_datetime;
                    if (targetCompletion) {
                        const targetDate = new Date(targetCompletion);
                        const now = new Date();
                        const remainingMs = targetDate - now;
                        if (remainingMs > 0) {
                            const hours = Math.floor(remainingMs / (1000 * 60 * 60));
                            const minutes = Math.floor((remainingMs % (1000 * 60 * 60)) / (1000 * 60));
                            html += `
                                <div style="margin-bottom: 15px;">
                                    <h3 style="color: #fff; margin: 0 0 10px 0; font-size: 16px;">Timeline</h3>
                                    <p style="margin: 5px 0;"><strong style="color: #667eea;">Target Completion:</strong> ${targetDate.toLocaleString()}</p>
                                    <p style="margin: 5px 0;"><strong style="color: #667eea;">Time Left:</strong> ${hours}h ${minutes}m</p>
                                </div>
                            `;
                        } else {
                            const isOvertimeStopped = video.overtime_stopped === true;
                            html += `
                                <div style="margin-bottom: 15px;">
                                    <h3 style="color: #fff; margin: 0 0 10px 0; font-size: 16px;">Timeline</h3>
                                    <p style="margin: 5px 0; color: ${isOvertimeStopped ? '#888' : '#f59e0b'};"><strong>Status:</strong> ${isOvertimeStopped ? 'Overtime stopped' : 'OVERTIME'}</p>
                                    ${!isOvertimeStopped ? `<button class="stop-overtime-btn" data-video-url="${safeVideoUrlAttr}" style="margin-top: 8px; background: #ef4444; color: white; border: none; padding: 6px 12px; border-radius: 0; cursor: pointer; font-size: 12px; font-weight: 600;">End Overtime</button>` : ''}
                                </div>
                            `;
                        }
                    }
                    
                    const orderHistory = video.order_history || [];
                    if (orderHistory.length > 0) {
                        html += `
                            <div style="margin-bottom: 15px;">
                                <h3 style="color: #fff; margin: 0 0 10px 0; font-size: 16px;">Order History (${orderHistory.length})</h3>
                                <div style="max-height: 200px; overflow-y: auto;">
                        `;
                        orderHistory.slice(-10).reverse().forEach(order => {
                            const date = order.timestamp ? new Date(order.timestamp).toLocaleString() : 'N/A';
                            html += `
                                <div style="padding: 8px; margin-bottom: 5px; background: #2a2a2a; border-left: 3px solid #667eea;">
                                    <p style="margin: 3px 0; font-size: 12px;"><strong>${order.service}</strong> - ${formatNumber(order.quantity || 0)} units - $${(order.cost || 0).toFixed(4)}</p>
                                    <p style="margin: 3px 0; font-size: 11px; color: #b0b0b0;">${date} ${(order.type === 'manual' || (!order.type && order.manual)) ? '(Manual)' : '(Scheduled)'}</p>
                                </div>
                            `;
                        });
                        html += `</div></div>`;
                    }
                    
                    content.innerHTML = html;
                } else {
                    content.innerHTML = `<p style="color: #ef4444;">Failed to load video details: ${result.error || 'Unknown error'}</p>`;
                }
            } catch (error) {
                content.innerHTML = `<p style="color: #ef4444;">Error loading video details: ${error.message}</p>`;
            }
        }
        
        function hideVideoDetailsModal() {
            const modal = document.getElementById('video-details-modal');
            modal.style.display = 'none';
            currentVideoDetailsUrl = null;
        }
        
        // Close modals when clicking outside
        document.addEventListener('click', function(event) {
            const editTimeModal = document.getElementById('edit-time-left-modal');
            const videoDetailsModal = document.getElementById('video-details-modal');
            
            if (event.target === editTimeModal) {
                hideEditTimeLeftModal();
            }
            if (event.target === videoDetailsModal) {
                hideVideoDetailsModal();
            }
        });
        
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
                    invalidateCache();
                    loadCampaigns();
                    loadDashboard(false, true); // Background refresh
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
                    invalidateCache();
                    loadCampaigns();
                    loadDashboard(false, true); // Background refresh
                } else {
                    alert('Error: ' + (data.error || 'Failed to assign videos'));
                }
            } catch (error) {
                alert('Error: ' + error.message);
            }
        }
        
        function renderCampaignsSummary() {
            const container = document.getElementById('campaigns-summary');
            if (!container) {
                // If campaigns tab is active, create container
                const campaignsContent = document.getElementById('campaigns-content');
                if (campaignsContent) {
                    campaignsContent.innerHTML = '<div id="campaigns-summary"></div>';
                    const newContainer = document.getElementById('campaigns-summary');
                    if (newContainer) {
                        container = newContainer;
                    } else {
                        return;
                    }
                } else {
                    return;
                }
            }
            
            const campaigns = Object.entries(campaignsData);
            
            let html = '<div style="background: #1a1a1a; border-radius: 0; padding: 8px; margin-bottom: 25px; border: 1px solid rgba(255,255,255,0.1);">';
            html += '<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">';
            html += '<h3 style="margin: 0; color: #fff; font-size: 1.2em; font-weight: 600;">Campaigns Overview</h3>';
            html += '<button id="add-campaign-btn-header" class="add-campaign-btn">Add Campaign</button>';
            html += '</div>';

            // CPM + Goals calculator (home)
            html += '<div style="background: #252525; border-radius: 0; padding: 10px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 12px;">';
            html += '<div style="display: flex; justify-content: space-between; align-items: center; gap: 10px; margin-bottom: 12px; flex-wrap: wrap;">';
            html += '<div style="color: #fff; font-weight: 700;">CPM & Goals Calculator</div>';
            if (campaigns.length > 0) {
                html += '<select id="calc-campaign-select" style="padding: 8px 10px; background: #1a1a1a; border: 1px solid rgba(255,255,255,0.2); border-radius: 0; color: #fff; font-size: 13px;">';
                html += '<option value="">Use campaign defaults…</option>';
                for (const [campaignId, campaign] of campaigns) {
                    const name = (campaign && campaign.name) ? String(campaign.name) : 'Unnamed Campaign';
                    const safeName = name.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
                    html += `<option value="${escapeTemplateLiteral(campaignId)}">${safeName}</option>`;
                }
                html += '</select>';
            }
            html += '</div>';
            html += '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px;">';
            html += '<div><div style="color:#b0b0b0; font-size:12px; margin-bottom:6px;">CPM ($ / 1000 views)</div><input id="calc-cpm" type="number" min="0" step="0.01" placeholder="2.50" style="width:100%; padding:10px; background:#1a1a1a; border:1px solid rgba(255,255,255,0.2); border-radius: 0; color:#fff;"></div>';
            html += '<div><div style="color:#b0b0b0; font-size:12px; margin-bottom:6px;"># of videos</div><input id="calc-videos" type="number" min="1" step="1" placeholder="10" style="width:100%; padding:10px; background:#1a1a1a; border:1px solid rgba(255,255,255,0.2); border-radius: 0; color:#fff;"></div>';
            html += '<div><div style="color:#b0b0b0; font-size:12px; margin-bottom:6px;">Views goal / video</div><input id="calc-views" type="number" min="0" step="1" placeholder="4000" style="width:100%; padding:10px; background:#1a1a1a; border:1px solid rgba(255,255,255,0.2); border-radius: 0; color:#fff;"></div>';
            html += '<div><div style="color:#b0b0b0; font-size:12px; margin-bottom:6px;">Likes goal / video</div><input id="calc-likes" type="number" min="0" step="1" placeholder="125" style="width:100%; padding:10px; background:#1a1a1a; border:1px solid rgba(255,255,255,0.2); border-radius: 0; color:#fff;"></div>';
            html += '<div><div style="color:#b0b0b0; font-size:12px; margin-bottom:6px;">Comments goal / video</div><input id="calc-comments" type="number" min="0" step="1" placeholder="7" style="width:100%; padding:10px; background:#1a1a1a; border:1px solid rgba(255,255,255,0.2); border-radius: 0; color:#fff;"></div>';
            html += '<div><div style="color:#b0b0b0; font-size:12px; margin-bottom:6px;">Comment likes goal / video</div><input id="calc-comment-likes" type="number" min="0" step="1" placeholder="15" style="width:100%; padding:10px; background:#1a1a1a; border:1px solid rgba(255,255,255,0.2); border-radius: 0; color:#fff;"></div>';
            html += '</div>';
            html += '<div style="margin-top: 12px; padding-top: 12px; border-top: 1px solid rgba(255,255,255,0.08); display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 10px;">';
            html += '<div style="background:#1f1f1f; border:1px solid rgba(255,255,255,0.06); border-radius: 0; padding: 8px;"><div style="color:#b0b0b0; font-size:12px;">Estimated Invest</div><div id="calc-invest" style="color:#ef4444; font-weight:800; font-size:18px;">$0.00</div></div>';
            html += '<div style="background:#1f1f1f; border:1px solid rgba(255,255,255,0.06); border-radius: 0; padding: 8px;"><div style="color:#b0b0b0; font-size:12px;">Estimated Earn</div><div id="calc-earn" style="color:#10b981; font-weight:800; font-size:18px;">$0.00</div></div>';
            html += '<div style="background:#1f1f1f; border:1px solid rgba(255,255,255,0.06); border-radius: 0; padding: 8px;"><div style="color:#b0b0b0; font-size:12px;">Profit</div><div id="calc-profit" style="color:#fff; font-weight:800; font-size:18px;">$0.00</div><div id="calc-roi" style="color:#b0b0b0; font-size:12px; margin-top:4px;">ROI: 0%</div></div>';
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
                    
                    html += `<div class="campaign-card-clickable" data-campaign-id="${escapeTemplateLiteral(campaignId)}" style="background: #2a2a2a; border-radius: 0; padding: 10px; border: 1px solid rgba(255,255,255,0.1); cursor: pointer; transition: all 0.2s; position: relative; display: flex; flex-direction: column;" onmouseover="this.style.borderColor='rgba(102,126,234,0.5)'; this.style.transform='translateY(-2px)';" onmouseout="this.style.borderColor='rgba(255,255,255,0.1)'; this.style.transform='translateY(0)';">
                        <button class="delete-campaign-btn" data-campaign-id="${escapeTemplateLiteral(campaignId)}" data-campaign-name="${escapeTemplateLiteral(campaign.name || 'Unnamed Campaign')}" style="position: absolute; top: 5px; right: 5px; background: rgba(239,68,68,0.25); color: #ef4444; border: 2px solid rgba(239,68,68,0.6); padding: 0; border-radius: 0; cursor: pointer; font-size: 22px; font-weight: 700; transition: all 0.2s; width: 30px; height: 30px; display: flex; align-items: center; justify-content: center; z-index: 100; line-height: 1; box-shadow: 0 2px 4px rgba(0,0,0,0.3);" onmouseover="this.style.background='rgba(239,68,68,0.5)'; this.style.borderColor='rgba(239,68,68,1)'; this.style.transform='scale(1.2)'; this.style.boxShadow='0 3px 6px rgba(239,68,68,0.4)';" onmouseout="this.style.background='rgba(239,68,68,0.25)'; this.style.borderColor='rgba(239,68,68,0.6)'; this.style.transform='scale(1)'; this.style.boxShadow='0 2px 4px rgba(0,0,0,0.3)';" title="Delete Campaign">×</button>
                        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 15px; padding-right: 40px;">
                            <div style="flex: 1;">
                                <h4 style="margin: 0 0 5px 0; color: #fff; font-size: 1.1em; font-weight: 600;">${campaign.name || 'Unnamed Campaign'}</h4>
                                ${campaign.cpm > 0 ? `<span style="color: #667eea; font-size: 0.85em;">CPM: $${campaign.cpm.toFixed(2)}</span>` : '<span style="color: #888; font-size: 0.85em;">No CPM set</span>'}
                            </div>
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
                            <button class="edit-campaign-btn" data-campaign-id="${escapeTemplateLiteral(campaignId)}" style="flex: 1; min-width: 80px; background: #2a2a2a; color: #fff; border: 1px solid rgba(255,255,255,0.2); padding: 8px 12px; border-radius: 0; cursor: pointer; font-size: 12px; font-weight: 600; transition: all 0.2s;" onmouseover="this.style.background='#333'; this.style.borderColor='rgba(255,255,255,0.3)';" onmouseout="this.style.background='#2a2a2a'; this.style.borderColor='rgba(255,255,255,0.2)';">Edit</button>
                            <button class="add-video-to-campaign-btn" data-campaign-id="${escapeTemplateLiteral(campaignId)}" style="flex: 1; min-width: 100px; background: #2a2a2a; color: #667eea; border: 1px solid rgba(102,126,234,0.3); padding: 8px 12px; border-radius: 0; cursor: pointer; font-size: 12px; font-weight: 600; transition: all 0.2s;" onmouseover="this.style.background='#333'; this.style.borderColor='rgba(102,126,234,0.5)';" onmouseout="this.style.background='#2a2a2a'; this.style.borderColor='rgba(102,126,234,0.3)';">Add Video</button>
                            ${campaign.status !== 'ended' ? `<button class="end-campaign-btn" data-campaign-id="${escapeTemplateLiteral(campaignId)}" style="flex: 1; min-width: 120px; background: #2a2a2a; color: #ef4444; border: 1px solid rgba(239,68,68,0.3); padding: 8px 12px; border-radius: 0; cursor: pointer; font-size: 12px; font-weight: 600; transition: all 0.2s;" onmouseover="this.style.background='#333'; this.style.borderColor='rgba(239,68,68,0.5)';" onmouseout="this.style.background='#2a2a2a'; this.style.borderColor='rgba(239,68,68,0.3)';">End Campaign</button>` : '<span style="flex: 1; color: #888; font-size: 11px; padding: 8px 12px; text-align: center;">Ended</span>'}
                        </div>
                        <div style="border-top: 1px solid rgba(255,255,255,0.1); padding-top: 8px; margin-top: 8px; text-align: center;">
                            <a href="#" class="remove-campaign-link" data-campaign-id="${escapeTemplateLiteral(campaignId)}" data-campaign-name="${escapeTemplateLiteral(campaign.name || 'Unnamed Campaign')}" style="color: #fff; text-decoration: none; font-size: 12px; cursor: pointer; transition: all 0.2s;" onmouseover="this.style.textDecoration='underline'; this.style.color='#ef4444';" onmouseout="this.style.textDecoration='none'; this.style.color='#fff';">Remove Campaign</a>
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
                return String(str)
                    .split('\\\\').join('\\\\\\\\')  // Escape backslashes first
                    .split("'").join("\\\\'")
                    .split('`').join('\\\\`')
                    .split('$').join('\\\\$');
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
            
            // Check if target is overdue and if overtime is stopped
            const isTargetOverdue = targetCompletionTime && hoursToTarget <= 0;
            const isOvertimeStopped = video.overtime_stopped === true;
            
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
                // In overtime mode, continue ordering until goal is reached (ignore time limit)
                // Use isOvertimeStopped from outer scope
                if (needed <= 0 || isOvertimeStopped) {
                    return null;
                }
                
                // OVERTIME MODE: Check if bot has set a next_purchase_time
                if (isTargetOverdue && !isOvertimeStopped) {
                    const nextPurchaseTimeStr = video[`next_${metricName}_purchase_time`];
                    if (nextPurchaseTimeStr) {
                        // Use the time set by the bot (every 30s in overtime)
                        const nextPurchaseTime = new Date(nextPurchaseTimeStr);
                        const msUntilNext = Math.max(0, nextPurchaseTime - Date.now());
                        const hoursUntilNext = msUntilNext / 3600000;
                        const orderSize = Math.min(needed, minOrder * 2);
                        const cost = (orderSize / 1000.0) * rates[metricName];
                        
                        return {
                            timeUntilNext: hoursUntilNext,
                            nextPurchaseTime: nextPurchaseTime,
                            units: orderSize,
                            cost: cost,
                            totalCost: cost,
                            purchasesCount: Math.ceil(needed / orderSize),
                            totalUnitsNeeded: needed
                        };
                    }
                }
                
                // In overtime mode, ignore hoursRemaining check - continue ordering
                if (!isTargetOverdue && hoursRemaining <= 0) {
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
            
            // isOvertimeStopped already declared above at line 6332
            
            if (isTargetOverdue && !isOvertimeStopped) {
                // Target is overdue - OVERTIME MODE: Continue ordering until goal reached
                // Calculate time based on delivery rates (no time limit)
                hoursToViewsGoal = combinedViewsPerHour > 0 ? viewsNeeded / combinedViewsPerHour : 999;
                hoursToLikesGoal = combinedLikesPerHour > 0 ? likesNeeded / combinedLikesPerHour : 999;
                hoursToCommentsGoal = combinedCommentsPerHour > 0 ? commentsNeeded / combinedCommentsPerHour : 999;
                hoursToCommentLikesGoal = commentLikesPerHour > 0 ? commentLikesNeeded / commentLikesPerHour : 999;
            } else if (isTargetOverdue && isOvertimeStopped) {
                // Overtime stopped - show as stopped
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
                if (hours < 0) return 'OVERTIME';
                if (hours <= 0 || !isFinite(hours)) return 'N/A';
                const totalSeconds = Math.floor(hours * 3600);
                const days = Math.floor(totalSeconds / (24 * 3600));
                const remainingAfterDays = totalSeconds % (24 * 3600);
                const hoursVal = Math.floor(remainingAfterDays / 3600);
                const remainingAfterHours = remainingAfterDays % 3600;
                const minutes = Math.floor(remainingAfterHours / 60);
                const seconds = remainingAfterHours % 60;
                
                if (days > 0) {
                    return days + 'd ' + hoursVal + 'h ' + minutes + 'm ' + seconds + 's';
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
                if (totalSeconds < 0) return 'OVERTIME';
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
                                Remove
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
                        <h3>Target Completion Time</h3>
                        <div style="margin-bottom: 15px;">
                            <div style="color: #b0b0b0; font-size: 0.9em; margin-bottom: 10px;">Quick Set (from now):</div>
                            <div class="target-input-group" style="margin-bottom: 10px;">
                                <input type="number" id="quick-hours-${safeVideoUrlId}" placeholder="Hours" min="0" max="999" style="padding: 10px 12px; background: #2a2a2a; border: 1px solid rgba(255,255,255,0.2); border-radius: 0; color: #fff; width: 100px; font-size: 14px;">
                                <span style="color: #b0b0b0;">:</span>
                                <input type="number" id="quick-minutes-${safeVideoUrlId}" placeholder="Minutes" min="0" max="59" style="padding: 10px 12px; background: #2a2a2a; border: 1px solid rgba(255,255,255,0.2); border-radius: 0; color: #fff; width: 100px; font-size: 14px;">
                                <button class="quick-set-target-btn" data-video-url="${safeVideoUrlAttr}" data-hours-id="quick-hours-${safeVideoUrlId}" data-minutes-id="quick-minutes-${safeVideoUrlId}" style="background: #667eea; color: white; border: none; padding: 10px 20px; border-radius: 0; cursor: pointer; font-weight: 600;">Quick Set</button>
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
                            ${viewsOrdered > 0 ? `<div style="color: #667eea; font-size: 0.85em; margin-top: 3px;">Orders placed: <strong>${viewsOrdersCount}</strong> (${formatNumber(viewsOrdered)} total ordered)</div>` : ''}
                            ${viewsCatchUp > 0 && targetCompletionTime ? `<div style="background: rgba(239, 68, 68, 0.1); border-radius: 0; padding: 8px; margin-top: 8px; font-size: 0.85em; border: 1px solid rgba(239, 68, 68, 0.3);">
                                <div style="color: #ef4444; font-weight: 600; margin-bottom: 4px;">Behind Schedule</div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Expected: <span style="color: #fff;">${formatNumber(Math.ceil(expectedViewsNow))}</span></div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Actual: <span style="color: #fff;">${formatNumber(totalViews)}</span></div>
                                <div style="color: #b0b0b0; margin-bottom: 6px;">Gap: <span style="color: #ef4444; font-weight: 600;">${formatNumber(viewsCatchUp)}</span></div>
                                <button class="catch-up-btn" data-video-url="${safeVideoUrlAttr}" data-metric="views" data-amount="${viewsCatchUp}" style="width: 100%; background: #ef4444; color: white; border: none; padding: 6px 12px; border-radius: 0; cursor: pointer; font-weight: 600; font-size: 0.9em;">Catch Up (${formatNumber(viewsCatchUp)})</button>
                            </div>` : ''}
                            ${viewsNeeded > 0 && hoursToViewsGoal > 0 ? `<div style="color: #888; font-size: 0.85em; margin-top: 5px;" data-time-to-goal data-hours="${hoursToViewsGoal}" data-metric="views"><span data-countdown-to-goal>${formatTimeRemaining(hoursToViewsGoal)}</span> to goal</div>` : viewsNeeded <= 0 ? `<div style="color: #10b981; font-size: 0.85em; margin-top: 5px;">Target reached</div>` : viewsNeeded > 0 && isTargetOverdue && !isOvertimeStopped ? `<div style="color: #f59e0b; font-size: 0.85em; margin-top: 5px;">OVERTIME</div>` : viewsNeeded > 0 && isTargetOverdue && isOvertimeStopped ? `<div style="color: #888; font-size: 0.85em; margin-top: 5px;">Overtime stopped</div>` : ''}
                            ${nextViewsPurchase ? `<div style="background: rgba(102, 126, 234, 0.1); border-radius: 0; padding: 8px; margin-top: 8px; font-size: 0.85em;">
                                <div style="color: #667eea; font-weight: 600; margin-bottom: 4px;">Next Purchase</div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Time: <span data-next-purchase data-purchase-time="${nextViewsPurchase.nextPurchaseTime.toISOString()}" data-metric="views" style="color: #fff;"><span data-countdown-display>${formatTimeRemaining(nextViewsPurchase.timeUntilNext)}</span></span></div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Units: <span style="color: #fff;">${formatNumber(nextViewsPurchase.units)}</span> (min order)</div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Orders: <span style="color: #fff;">${nextViewsPurchase.purchasesCount}x</span> (${formatNumber(nextViewsPurchase.purchasesCount * nextViewsPurchase.units)} total)</div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Expected total: <span style="color: #fff;">${formatNumber(expectedViewsToOrder)}</span></div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Already ordered: <span style="color: #10b981; font-weight: 600;">${formatNumber(viewsOrdered)}</span></div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Per order: <span style="color: #10b981; font-weight: 600;">$${nextViewsPurchase.cost.toFixed(4)}</span></div>
                                <div style="color: #b0b0b0; margin-bottom: 6px;">Total cost: <span style="color: #10b981; font-weight: 600;">$${nextViewsPurchase.totalCost.toFixed(4)}</span></div>
                                <button class="manual-order-btn" data-video-url="${safeVideoUrlAttr}" data-metric="views" data-minimum="50" style="width: 100%; background: #10b981; color: white; border: none; padding: 6px 12px; border-radius: 0; cursor: pointer; font-weight: 600; font-size: 0.9em; margin-top: 4px;">Manual Order</button>
                            </div>` : nextViewsPurchaseTime ? `<div style="color: #667eea; font-size: 0.85em; margin-top: 3px;" data-next-purchase data-purchase-time="${nextViewsPurchaseTime.toISOString()}" data-metric="views">Next purchase: <span data-countdown-display>${formatTimeRemaining((nextViewsPurchaseTime - now) / (1000 * 60 * 60))}</span></div>` : ''}
                            ${targetViews > 0 ? `<button class="manual-order-btn" data-video-url="${safeVideoUrlAttr}" data-metric="views" data-minimum="50" style="width: 100%; background: #10b981; color: white; border: none; padding: 6px 12px; border-radius: 0; cursor: pointer; font-weight: 600; font-size: 0.85em; margin-top: 8px;">Manual Order Views</button>` : ''}
                            <div class="progress-bar-container">
                                <div class="progress-bar" style="width: ${Math.min(viewsProgress, 100)}%">${formatPercentage(totalViews, targetViews)}</div>
                            </div>
                        </div>
                        
                        <div class="metric">
                            <div class="metric-label">Likes</div>
                            <div class="metric-value">${formatNumber(totalLikes)}</div>
                            <div class="metric-target">/ ${formatNumber(targetLikes)} (${formatPercentage(totalLikes, targetLikes)})</div>
                            ${likesOrdered > 0 ? `<div style="color: #667eea; font-size: 0.85em; margin-top: 3px;">Orders placed: <strong>${likesOrdersCount}</strong> (${formatNumber(likesOrdered)} total ordered)</div>` : ''}
                            ${likesCatchUp > 0 && targetCompletionTime ? `<div style="background: rgba(239, 68, 68, 0.1); border-radius: 0; padding: 8px; margin-top: 8px; font-size: 0.85em; border: 1px solid rgba(239, 68, 68, 0.3);">
                                <div style="color: #ef4444; font-weight: 600; margin-bottom: 4px;">Behind Schedule</div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Expected: <span style="color: #fff;">${formatNumber(Math.ceil(expectedLikesNow))}</span></div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Actual: <span style="color: #fff;">${formatNumber(totalLikes)}</span></div>
                                <div style="color: #b0b0b0; margin-bottom: 6px;">Gap: <span style="color: #ef4444; font-weight: 600;">${formatNumber(likesCatchUp)}</span></div>
                                <button class="catch-up-btn" data-video-url="${safeVideoUrlAttr}" data-metric="likes" data-amount="${likesCatchUp}" style="width: 100%; background: #ef4444; color: white; border: none; padding: 6px 12px; border-radius: 0; cursor: pointer; font-weight: 600; font-size: 0.9em;">Catch Up (${formatNumber(likesCatchUp)})</button>
                            </div>` : ''}
                            ${likesNeeded > 0 && hoursToLikesGoal > 0 ? `<div style="color: #888; font-size: 0.85em; margin-top: 5px;" data-time-to-goal data-hours="${hoursToLikesGoal}" data-metric="likes"><span data-countdown-to-goal>${formatTimeRemaining(hoursToLikesGoal)}</span> to goal</div>` : likesNeeded <= 0 ? `<div style="color: #10b981; font-size: 0.85em; margin-top: 5px;">Target reached</div>` : likesNeeded > 0 && isTargetOverdue && !isOvertimeStopped ? `<div style="color: #f59e0b; font-size: 0.85em; margin-top: 5px;">OVERTIME</div>` : likesNeeded > 0 && isTargetOverdue && isOvertimeStopped ? `<div style="color: #888; font-size: 0.85em; margin-top: 5px;">Overtime stopped</div>` : likesNeeded > 0 && targetCompletionTime ? `<div style="color: #888; font-size: 0.85em; margin-top: 5px;" data-time-to-goal data-hours="${hoursToTarget}" data-metric="likes"><span data-countdown-to-goal>${formatTimeRemaining(hoursToTarget)}</span> to goal</div>` : ''}
                            ${nextLikesPurchase ? `<div style="background: rgba(102, 126, 234, 0.1); border-radius: 0; padding: 8px; margin-top: 8px; font-size: 0.85em;">
                                <div style="color: #667eea; font-weight: 600; margin-bottom: 4px;">Next Purchase</div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Time: <span data-next-purchase data-purchase-time="${nextLikesPurchase.nextPurchaseTime.toISOString()}" data-metric="likes" style="color: #fff;"><span data-countdown-display>${formatTimeRemaining(nextLikesPurchase.timeUntilNext)}</span></span></div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Units: <span style="color: #fff;">${formatNumber(nextLikesPurchase.units)}</span> (min order)</div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Orders: <span style="color: #fff;">${nextLikesPurchase.purchasesCount}x</span> (${formatNumber(nextLikesPurchase.purchasesCount * nextLikesPurchase.units)} total)</div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Expected total: <span style="color: #fff;">${formatNumber(expectedLikesToOrder)}</span></div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Already ordered: <span style="color: #10b981; font-weight: 600;">${formatNumber(likesOrdered)}</span></div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Per order: <span style="color: #10b981; font-weight: 600;">$${nextLikesPurchase.cost.toFixed(4)}</span></div>
                                <div style="color: #b0b0b0; margin-bottom: 6px;">Total cost: <span style="color: #10b981; font-weight: 600;">$${nextLikesPurchase.totalCost.toFixed(4)}</span></div>
                                <button class="manual-order-btn" data-video-url="${safeVideoUrlAttr}" data-metric="likes" data-minimum="10" style="width: 100%; background: #10b981; color: white; border: none; padding: 6px 12px; border-radius: 0; cursor: pointer; font-weight: 600; font-size: 0.9em; margin-top: 4px;">Manual Order</button>
                            </div>` : nextLikesPurchaseTime ? `<div style="color: #667eea; font-size: 0.85em; margin-top: 3px;" data-next-purchase data-purchase-time="${nextLikesPurchaseTime.toISOString()}" data-metric="likes">Next purchase: <span data-countdown-display>${formatTimeRemaining((nextLikesPurchaseTime - now) / (1000 * 60 * 60))}</span></div>` : ''}
                            ${targetLikes > 0 ? `<button class="manual-order-btn" data-video-url="${safeVideoUrlAttr}" data-metric="likes" data-minimum="10" style="width: 100%; background: #10b981; color: white; border: none; padding: 6px 12px; border-radius: 0; cursor: pointer; font-weight: 600; font-size: 0.85em; margin-top: 8px;">Manual Order Likes</button>` : ''}
                            <div class="progress-bar-container">
                                <div class="progress-bar" style="width: ${Math.min(likesProgress, 100)}%">${formatPercentage(totalLikes, targetLikes)}</div>
                            </div>
                        </div>
                        
                        <div class="metric">
                            <div class="metric-label">Comments</div>
                            <div class="metric-value">${totalComments}</div>
                            <div class="metric-target">/ ${targetComments} (${formatPercentage(totalComments, targetComments)})</div>
                            ${commentsOrdered > 0 ? `<div style="color: #667eea; font-size: 0.85em; margin-top: 3px;">Orders placed: <strong>${commentsOrdersCount}</strong> (${formatNumber(commentsOrdered)} total ordered)</div>` : ''}
                            ${commentsNeeded > 0 && hoursToCommentsGoal > 0 ? `<div style="color: #888; font-size: 0.85em; margin-top: 5px;" data-time-to-goal data-hours="${hoursToCommentsGoal}" data-metric="comments"><span data-countdown-to-goal>${formatTimeRemaining(hoursToCommentsGoal)}</span> to goal</div>` : commentsNeeded <= 0 ? `<div style="color: #10b981; font-size: 0.85em; margin-top: 5px;">Target reached</div>` : commentsNeeded > 0 && isTargetOverdue && !isOvertimeStopped ? `<div style="color: #f59e0b; font-size: 0.85em; margin-top: 5px;">OVERTIME</div>` : commentsNeeded > 0 && isTargetOverdue && isOvertimeStopped ? `<div style="color: #888; font-size: 0.85em; margin-top: 5px;">Overtime stopped</div>` : commentsNeeded > 0 && targetCompletionTime ? `<div style="color: #888; font-size: 0.85em; margin-top: 5px;" data-time-to-goal data-hours="${hoursToTarget}" data-metric="comments"><span data-countdown-to-goal>${formatTimeRemaining(hoursToTarget)}</span> to goal</div>` : ''}
                            ${nextCommentsPurchase ? `<div style="background: rgba(102, 126, 234, 0.1); border-radius: 0; padding: 8px; margin-top: 8px; font-size: 0.85em;">
                                <div style="color: #667eea; font-weight: 600; margin-bottom: 4px;">Next Purchase</div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Time: <span data-next-purchase data-purchase-time="${nextCommentsPurchase.nextPurchaseTime.toISOString()}" data-metric="comments" style="color: #fff;"><span data-countdown-display>${formatTimeRemaining(nextCommentsPurchase.timeUntilNext)}</span></span></div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Units: <span style="color: #fff;">${formatNumber(nextCommentsPurchase.units)}</span> (min order)</div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Orders: <span style="color: #fff;">${nextCommentsPurchase.purchasesCount}x</span> (${formatNumber(nextCommentsPurchase.purchasesCount * nextCommentsPurchase.units)} total)</div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Expected total: <span style="color: #fff;">${formatNumber(expectedCommentsToOrder)}</span></div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Already ordered: <span style="color: #10b981; font-weight: 600;">${formatNumber(commentsOrdered)}</span></div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Per order: <span style="color: #10b981; font-weight: 600;">$${nextCommentsPurchase.cost.toFixed(4)}</span></div>
                                <div style="color: #b0b0b0;">Total cost: <span style="color: #10b981; font-weight: 600;">$${nextCommentsPurchase.totalCost.toFixed(4)}</span></div>
                            </div>` : nextCommentsPurchaseTime ? `<div style="color: #667eea; font-size: 0.85em; margin-top: 3px;" data-next-purchase data-purchase-time="${nextCommentsPurchaseTime.toISOString()}" data-metric="comments">Next purchase: <span data-countdown-display>${formatTimeRemaining((nextCommentsPurchaseTime - now) / (1000 * 60 * 60))}</span></div>` : ''}
                            <div class="progress-bar-container">
                                <div class="progress-bar" style="width: ${Math.min(commentsProgress, 100)}%">${formatPercentage(totalComments, targetComments)}</div>
                            </div>
                        </div>
                        
                        <div class="metric">
                            <div class="metric-label">Comment Likes</div>
                            <div class="metric-value">${commentLikesOrdered}</div>
                            <div class="metric-target">/ ${targetCommentLikes} (${formatPercentage(commentLikesOrdered, targetCommentLikes)})</div>
                            ${commentLikesOrdered > 0 ? `<div style="color: #667eea; font-size: 0.85em; margin-top: 3px;">Orders placed: <strong>${commentLikesOrdersCount}</strong> (${formatNumber(commentLikesOrdered)} total ordered)</div>` : ''}
                            ${commentLikesNeeded > 0 && hoursToCommentLikesGoal > 0 ? `<div style="color: #888; font-size: 0.85em; margin-top: 5px;" data-time-to-goal data-hours="${hoursToCommentLikesGoal}" data-metric="comment_likes"><span data-countdown-to-goal>${formatTimeRemaining(hoursToCommentLikesGoal)}</span> to goal</div>` : commentLikesNeeded <= 0 ? `<div style="color: #10b981; font-size: 0.85em; margin-top: 5px;">Target reached</div>` : commentLikesNeeded > 0 && isTargetOverdue && !isOvertimeStopped ? `<div style="color: #f59e0b; font-size: 0.85em; margin-top: 5px;">OVERTIME</div>` : commentLikesNeeded > 0 && isTargetOverdue && isOvertimeStopped ? `<div style="color: #888; font-size: 0.85em; margin-top: 5px;">Overtime stopped</div>` : commentLikesNeeded > 0 && targetCompletionTime ? `<div style="color: #888; font-size: 0.85em; margin-top: 5px;" data-time-to-goal data-hours="${hoursToTarget}" data-metric="comment_likes"><span data-countdown-to-goal>${formatTimeRemaining(hoursToTarget)}</span> to goal</div>` : ''}
                            ${nextCommentLikesPurchase ? `<div style="background: rgba(102, 126, 234, 0.1); border-radius: 0; padding: 8px; margin-top: 8px; font-size: 0.85em;">
                                <div style="color: #667eea; font-weight: 600; margin-bottom: 4px;">Next Purchase</div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Time: <span data-next-purchase data-purchase-time="${nextCommentLikesPurchase.nextPurchaseTime.toISOString()}" data-metric="comment_likes" style="color: #fff;"><span data-countdown-display>${formatTimeRemaining(nextCommentLikesPurchase.timeUntilNext)}</span></span></div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Units: <span style="color: #fff;">${formatNumber(nextCommentLikesPurchase.units)}</span> (min order)</div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Orders: <span style="color: #fff;">${nextCommentLikesPurchase.purchasesCount}x</span> (${formatNumber(nextCommentLikesPurchase.purchasesCount * nextCommentLikesPurchase.units)} total)</div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Expected total: <span style="color: #fff;">${formatNumber(expectedCommentLikesToOrder)}</span></div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Already ordered: <span style="color: #10b981; font-weight: 600;">${formatNumber(commentLikesOrdered)}</span></div>
                                <div style="color: #b0b0b0; margin-bottom: 2px;">Per order: <span style="color: #10b981; font-weight: 600;">$${nextCommentLikesPurchase.cost.toFixed(4)}</span></div>
                                <div style="color: #b0b0b0;">Total cost: <span style="color: #10b981; font-weight: 600;">$${nextCommentLikesPurchase.totalCost.toFixed(4)}</span></div>
                            </div>` : nextCommentLikesPurchaseTime ? `<div style="color: #667eea; font-size: 0.85em; margin-top: 3px;" data-next-purchase data-purchase-time="${nextCommentLikesPurchaseTime.toISOString()}" data-metric="comment_likes">Next purchase: <span data-countdown-display>${formatTimeRemaining((nextCommentLikesPurchaseTime - now) / (1000 * 60 * 60))}</span></div>` : ''}
                            <div class="progress-bar-container">
                                <div class="progress-bar" style="width: ${Math.min(commentLikesProgress, 100)}%">${formatPercentage(commentLikesOrdered, targetCommentLikes)}</div>
                            </div>
                            ${commentLikesNeeded > 0 && totalComments > 0 ? `<div style="margin-top: 10px;"><button class="select-comments-btn" data-video-url="${safeVideoUrlAttr}" style="background: #667eea; color: white; border: none; padding: 8px 16px; border-radius: 0; cursor: pointer; font-size: 0.9em;">📝 Select Comments to Boost</button></div>` : commentLikesNeeded > 0 && totalComments === 0 ? `<div style="margin-top: 10px; color: #888; font-size: 0.85em;">No comments yet. Comments must be added before ordering likes.</div>` : ''}
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
                                    return String(label || '').split('`').join('\\`').split('$').join('\\$');
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
                                        return String(label || '').split('`').join('\\`').split('$').join('\\$');
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
                                    ${currentTotalViews >= commentsMilestone ? (hasCommentsOrdered ? 'Ordered' : '⚠ Ready to Order') : ' Pending'}
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
                                    <button class="order-comments-btn" data-video-url="${safeVideoUrlAttr}" style="margin-top: 15px; padding: 10px 20px; background: #1a1a1a; border: none; border-radius: 0; color: white; font-weight: 600; cursor: pointer; font-size: 14px; width: 100%;">
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
                                    <strong>Status:</strong> No comments saved. Please add comments below to order.
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
                                    ${currentTotalViews >= commentLikesMilestone ? (hasCommentLikesOrdered ? 'Ordered' : '⚠ Ready to Order') : ' Pending'}
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
                    
                    <div class="live-activity-section" style="background: #1a1a1a; padding: 8px; border-radius: 0; margin-bottom: 16px; color: white;">
                        <h3 style="margin: 0 0 12px 0; color: white; font-size: 16px;">Live Activity Status</h3>
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
                                hoursToGoal = -1; // Will show "OVERTIME"
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
                                    '<div style="font-size: 24px;"></div>' +
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
                                statusHtml = '<div style="display: flex; align-items: center; gap: 12px;">' +
                                    '<div style="font-size: 20px; font-weight: 700;">...</div>' +
                                    '<div style="flex: 1;">' +
                                    '<div style="font-weight: 600; font-size: 15px; margin-bottom: 4px;">Ordering Now</div>' +
                                    '<div style="opacity: 0.9; font-size: 13px;">' + (currentActivity.action || 'Placing order') + '</div>' +
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
                                    timeToGoal = 'OVERTIME';
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
            // INSTANT navigation - hashchange handler will render
            window.location.hash = '';
        }
        
        function renderHomepage(videos) {
            if (Object.keys(videos).length === 0) {
                return `
                    <div class="empty-state">
                        <h2>No Videos</h2>
                        <p>Add videos to start tracking campaigns</p>
                    </div>
                `;
            }
            
            // Render as accounting-style table instead of cards
            let html = `
                <div style="overflow-x: auto; margin-top: 10px;">
                    <table style="width: 100%; border-collapse: collapse; background: #1a1a1a; border: 1px solid rgba(255,255,255,0.1); font-family: monospace; font-size: 10px;">
                        <thead>
                            <tr style="background: #252525; border-bottom: 2px solid rgba(255,255,255,0.1);">
                                <th style="padding: 6px 4px; text-align: left; color: #fff; font-weight: 600; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);">VIDEO ID</th>
                                <th style="padding: 6px 4px; text-align: center; color: #fff; font-weight: 600; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);">DATE POSTED</th>
                                <th style="padding: 6px 4px; text-align: center; color: #fff; font-weight: 600; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);">TIME LEFT</th>
                                <th style="padding: 6px 4px; text-align: right; color: #fff; font-weight: 600; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);">CURR VIEWS</th>
                                <th style="padding: 6px 4px; text-align: right; color: #fff; font-weight: 600; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);">EXP VIEWS</th>
                                <th style="padding: 6px 4px; text-align: center; color: #fff; font-weight: 600; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);">MANUAL ORD</th>
                                <th style="padding: 6px 4px; text-align: center; color: #fff; font-weight: 600; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);">SCHED ORD</th>
                                <th style="padding: 6px 4px; text-align: center; color: #fff; font-weight: 600; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);">TIME NEXT</th>
                                <th style="padding: 6px 4px; text-align: right; color: #fff; font-weight: 600; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);">UNITS/ORD</th>
                                <th style="padding: 6px 4px; text-align: right; color: #fff; font-weight: 600; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);">$/UNIT</th>
                                <th style="padding: 6px 4px; text-align: right; color: #fff; font-weight: 600; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);">CURR LIKES</th>
                                <th style="padding: 6px 4px; text-align: right; color: #fff; font-weight: 600; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);">EXP LIKES</th>
                                <th style="padding: 6px 4px; text-align: center; color: #fff; font-weight: 600; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);">LIKES MAN</th>
                                <th style="padding: 6px 4px; text-align: center; color: #fff; font-weight: 600; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);">LIKES SCH</th>
                                <th style="padding: 6px 4px; text-align: center; color: #fff; font-weight: 600; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);">LIKES NEXT</th>
                                <th style="padding: 6px 4px; text-align: right; color: #fff; font-weight: 600; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);">LIKES UNITS</th>
                                <th style="padding: 6px 4px; text-align: right; color: #fff; font-weight: 600; font-size: 9px;">LIKES $/U</th>
                            </tr>
                        </thead>
                        <tbody>
            `;
            
            for (const [videoUrl, videoData] of Object.entries(videos)) {
                const { username, videoId } = extractVideoInfo(videoUrl);
                function escapeTemplateLiteral(str) {
                    if (!str) return '';
                    return String(str)
                        .split('\\\\').join('\\\\\\\\')  // Escape backslashes first
                        .split("'").join("\\\\'")
                        .split('`').join('\\\\`')
                        .split('$').join('\\\\$');
                }
                
                // Get start time (date posted) and calculate time left
                const startTime = videoData.start_time ? new Date(videoData.start_time) : null;
                const uploadTime = startTime ? startTime.toLocaleString('en-US', {month: '2-digit', day: '2-digit', year: '2-digit', hour: '2-digit', minute: '2-digit'}) : 'N/A';
                
                // Calculate time left to reach goal
                const target_completion = videoData.target_completion_time || videoData.target_completion_datetime;
                let timeLeft = 'N/A';
                if (target_completion && startTime) {
                    const now = new Date();
                    const endTime = new Date(target_completion);
                    const remainingMs = endTime - now;
                    if (remainingMs > 0) {
                        const remainingHours = Math.floor(remainingMs / (1000 * 60 * 60));
                        const remainingMinutes = Math.floor((remainingMs % (1000 * 60 * 60)) / (1000 * 60));
                        const remainingSeconds = Math.floor((remainingMs % (1000 * 60)) / 1000);
                        timeLeft = remainingHours + 'h' + (remainingMinutes > 0 ? remainingMinutes + 'm' : '') + remainingSeconds + 's';
                    } else {
                        // Check if overtime is stopped
                        const videoOvertimeStopped = videoData && videoData.overtime_stopped === true;
                        timeLeft = videoOvertimeStopped ? 'Overtime stopped' : 'OVERTIME';
                    }
                }
                
                const real_views = videoData.real_views !== undefined ? videoData.real_views : (videoData.initial_views || 0);
                const real_likes = videoData.real_likes !== undefined ? videoData.real_likes : (videoData.initial_likes || 0);
                const target_views = videoData.target_views || 4000;
                const target_likes = videoData.target_likes || 125;
                
                // Calculate expected views/likes
                let expected_views = 0;
                let expected_likes = 0;
                if (startTime && target_completion) {
                    const now = new Date();
                    const endTime = new Date(target_completion);
                    const totalDuration = endTime - startTime;
                    const elapsed = now - startTime;
                    if (totalDuration > 0 && elapsed > 0) {
                        const progress = Math.min(1, elapsed / totalDuration);
                        expected_views = Math.floor(target_views * progress);
                        expected_likes = Math.floor(target_likes * progress);
                    }
                }
                
                // Order counts - MUST be calculated BEFORE TIME NEXT calculation
                const orderHistory = videoData.order_history || [];
                const viewsOrders = orderHistory.filter(o => o.service === 'views');
                const manualViewsOrders = viewsOrders.filter(o => o.type === 'manual' || (!o.type && o.manual)).length;
                const schedViewsOrders = viewsOrders.filter(o => o.type === 'scheduled' || (!o.type && !o.manual)).length;
                
                const likesOrders = orderHistory.filter(o => o.service === 'likes');
                const manualLikesOrders = likesOrders.filter(o => o.type === 'manual' || (!o.type && o.manual)).length;
                const schedLikesOrders = likesOrders.filter(o => o.type === 'scheduled' || (!o.type && !o.manual)).length;
                
                // Time to next order - calculate based on remaining time divided by orders needed
                let timeToNext = 'N/A';
                let likesTimeToNext = 'N/A';
                
                // Minimum order sizes
                const MIN_VIEWS_ORDER = 50;
                const MIN_LIKES_ORDER = 10;
                
                // Calculate for views (reuse target_completion from above)
                if (target_completion && startTime) {
                    const now = new Date();
                    const endTime = new Date(target_completion);
                    const remainingMs = endTime - now;
                    
                    if (remainingMs > 0) {
                        // Calculate views needed
                        const viewsNeeded = Math.max(0, target_views - real_views);
                        
                        if (viewsNeeded <= 0) {
                            timeToNext = 'DONE';
                        } else {
                            // Calculate average units per scheduled order, or use minimum if no orders
                            const schedViewsOrdersList = viewsOrders.filter(o => o.type === 'scheduled' || (!o.type && !o.manual));
                            let unitsPerOrder = MIN_VIEWS_ORDER; // Default to minimum
                            
                            if (schedViewsOrdersList.length > 0) {
                                const totalViewsUnits = schedViewsOrdersList.reduce((sum, o) => sum + (o.quantity || 0), 0);
                                const avgViewsUnits = Math.floor(totalViewsUnits / schedViewsOrdersList.length);
                                if (avgViewsUnits > 0) {
                                    unitsPerOrder = avgViewsUnits;
                                }
                            }
                            
                            // Calculate orders needed based on units per order
                            const ordersNeeded = Math.ceil(viewsNeeded / unitsPerOrder);
                            
                            if (ordersNeeded > 0) {
                                const timePerOrder = remainingMs / ordersNeeded;
                                const hours = Math.floor(timePerOrder / (1000 * 60 * 60));
                                const mins = Math.floor((timePerOrder % (1000 * 60 * 60)) / (1000 * 60));
                                const secs = Math.floor((timePerOrder % (1000 * 60)) / 1000);
                                if (hours > 0 || mins > 0 || secs > 0) {
                                    timeToNext = hours + 'h' + (mins > 0 ? mins + 'm' : '') + secs + 's';
                                } else {
                                    timeToNext = 'READY';
                                }
                            } else {
                                timeToNext = 'READY';
                            }
                        }
                    } else {
                        timeToNext = 'OVERTIME';
                    }
                }
                
                // Calculate for likes
                if (target_completion && startTime) {
                    const now = new Date();
                    const endTime = new Date(target_completion);
                    const remainingMs = endTime - now;
                    
                    if (remainingMs > 0) {
                        // Calculate likes needed
                        const likesNeeded = Math.max(0, target_likes - real_likes);
                        
                        if (likesNeeded <= 0) {
                            likesTimeToNext = 'DONE';
                        } else {
                            // Calculate average units per scheduled order, or use minimum if no orders
                            const schedLikesOrdersList = likesOrders.filter(o => o.type === 'scheduled' || (!o.type && !o.manual));
                            let unitsPerOrder = MIN_LIKES_ORDER; // Default to minimum
                            
                            if (schedLikesOrdersList.length > 0) {
                                const totalLikesUnits = schedLikesOrdersList.reduce((sum, o) => sum + (o.quantity || 0), 0);
                                const avgLikesUnits = Math.floor(totalLikesUnits / schedLikesOrdersList.length);
                                if (avgLikesUnits > 0) {
                                    unitsPerOrder = avgLikesUnits;
                                }
                            }
                            
                            // Calculate orders needed based on units per order
                            const ordersNeeded = Math.ceil(likesNeeded / unitsPerOrder);
                            
                            if (ordersNeeded > 0) {
                                const timePerOrder = remainingMs / ordersNeeded;
                                const hours = Math.floor(timePerOrder / (1000 * 60 * 60));
                                const mins = Math.floor((timePerOrder % (1000 * 60 * 60)) / (1000 * 60));
                                const secs = Math.floor((timePerOrder % (1000 * 60)) / 1000);
                                if (hours > 0 || mins > 0 || secs > 0) {
                                    likesTimeToNext = hours + 'h' + (mins > 0 ? mins + 'm' : '') + secs + 's';
                                } else {
                                    likesTimeToNext = 'READY';
                                }
                            } else {
                                likesTimeToNext = 'READY';
                            }
                        }
                    } else {
                        likesTimeToNext = 'OVERTIME';
                    }
                }
                
                // Units and cost per unit (average of scheduled orders only)
                let avgViewsUnits = 0;
                let avgViewsCostPerUnit = 0;
                const schedViewsOrdersList = viewsOrders.filter(o => !o.manual);
                if (schedViewsOrdersList.length > 0) {
                    const totalViewsUnits = schedViewsOrdersList.reduce((sum, o) => sum + (o.quantity || 0), 0);
                    const totalViewsCost = schedViewsOrdersList.reduce((sum, o) => sum + (o.cost || 0), 0);
                    avgViewsUnits = Math.floor(totalViewsUnits / schedViewsOrdersList.length);
                    avgViewsCostPerUnit = totalViewsUnits > 0 ? totalViewsCost / totalViewsUnits : 0;
                }
                
                let avgLikesUnits = 0;
                let avgLikesCostPerUnit = 0;
                const schedLikesOrdersList = likesOrders.filter(o => !o.manual);
                if (schedLikesOrdersList.length > 0) {
                    const totalLikesUnits = schedLikesOrdersList.reduce((sum, o) => sum + (o.quantity || 0), 0);
                    const totalLikesCost = schedLikesOrdersList.reduce((sum, o) => sum + (o.cost || 0), 0);
                    avgLikesUnits = Math.floor(totalLikesUnits / schedLikesOrdersList.length);
                    avgLikesCostPerUnit = totalLikesUnits > 0 ? totalLikesCost / totalLikesUnits : 0;
                }
                
                // Calculate current hours/minutes for time left edit
                let currentHours = 0;
                let currentMinutes = 0;
                if (target_completion && startTime) {
                    const now = new Date();
                    const endTime = new Date(target_completion);
                    const remainingMs = endTime - now;
                    if (remainingMs > 0) {
                        currentHours = Math.floor(remainingMs / (1000 * 60 * 60));
                        currentMinutes = Math.floor((remainingMs % (1000 * 60 * 60)) / (1000 * 60));
                    }
                }
                
                html += `
                    <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);" onmouseover="this.style.background='#252525'" onmouseout="this.style.background='transparent'">
                        <td style="padding: 4px 3px; color: #667eea; font-family: monospace; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05); text-align: left;" title="${escapeTemplateLiteral(videoUrl)}"><a href="#" class="show-video-details-link" data-video-url="${escapeTemplateLiteral(videoUrl)}" style="color: #667eea; text-decoration: none; cursor: pointer;">${videoId}</a></td>
                        <td style="padding: 4px 3px; text-align: center; color: #fff; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);">${uploadTime}</td>
                        <td style="padding: 4px 3px; text-align: center; color: ${timeLeft === 'OVERTIME' ? '#f59e0b' : timeLeft === 'Overtime stopped' ? '#888' : '#fff'}; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05); cursor: pointer; text-decoration: underline;" class="edit-time-left-cell" data-video-url="${escapeTemplateLiteral(videoUrl)}" data-current-hours="${currentHours}" data-current-minutes="${currentMinutes}" title="Click to edit time left" data-time-left data-target-time="${target_completion || ''}">${timeLeft}</td>
                        <td style="padding: 4px 3px; text-align: right; color: #fff; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);" data-real-views data-video-url="${escapeTemplateLiteral(videoUrl)}">${formatNumber(real_views)}</td>
                        <td style="padding: 4px 3px; text-align: right; color: ${real_views >= expected_views ? '#10b981' : '#f59e0b'}; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);">${formatNumber(expected_views)}</td>
                        <td style="padding: 4px 3px; text-align: center; color: #b0b0b0; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);" data-manual-views-orders data-video-url="${escapeTemplateLiteral(videoUrl)}"><span class="manual-order-link" data-video-url="${escapeTemplateLiteral(videoUrl)}" data-metric="views" style="cursor: pointer; text-decoration: underline; color: #667eea;">${manualViewsOrders}</span></td>
                        <td style="padding: 4px 3px; text-align: center; color: #b0b0b0; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);" data-sched-views-orders data-video-url="${escapeTemplateLiteral(videoUrl)}">${schedViewsOrders}</td>
                        <td style="padding: 4px 3px; text-align: center; color: ${timeToNext === 'READY' ? '#10b981' : '#fff'}; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);" data-time-next data-video-url="${escapeTemplateLiteral(videoUrl)}" data-target-time="${target_completion || ''}" data-target-views="${target_views}" data-real-views="${real_views}" data-avg-units="${avgViewsUnits || MIN_VIEWS_ORDER}">${timeToNext}</td>
                        <td style="padding: 4px 3px; text-align: right; color: #fff; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);">${avgViewsUnits > 0 ? formatNumber(avgViewsUnits) : '-'}</td>
                        <td style="padding: 4px 3px; text-align: right; color: #fff; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);">${avgViewsCostPerUnit > 0 ? '$' + avgViewsCostPerUnit.toFixed(4) : '-'}</td>
                        <td style="padding: 4px 3px; text-align: right; color: #fff; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);" data-real-likes data-video-url="${escapeTemplateLiteral(videoUrl)}">${formatNumber(real_likes)}</td>
                        <td style="padding: 4px 3px; text-align: right; color: ${real_likes >= expected_likes ? '#10b981' : '#f59e0b'}; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);">${formatNumber(expected_likes)}</td>
                        <td style="padding: 4px 3px; text-align: center; color: #b0b0b0; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);" data-manual-likes-orders data-video-url="${escapeTemplateLiteral(videoUrl)}"><span class="manual-order-link" data-video-url="${escapeTemplateLiteral(videoUrl)}" data-metric="likes" style="cursor: pointer; text-decoration: underline; color: #667eea;">${manualLikesOrders}</span></td>
                        <td style="padding: 4px 3px; text-align: center; color: #b0b0b0; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);" data-sched-likes-orders data-video-url="${escapeTemplateLiteral(videoUrl)}">${schedLikesOrders}</td>
                        <td style="padding: 4px 3px; text-align: center; color: ${likesTimeToNext === 'READY' ? '#10b981' : '#fff'}; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);" data-likes-next data-video-url="${escapeTemplateLiteral(videoUrl)}" data-target-time="${target_completion || ''}" data-target-likes="${target_likes}" data-real-likes="${real_likes}" data-avg-units="${avgLikesUnits || MIN_LIKES_ORDER}">${likesTimeToNext}</td>
                        <td style="padding: 4px 3px; text-align: right; color: #fff; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);">${avgLikesUnits > 0 ? formatNumber(avgLikesUnits) : '-'}</td>
                        <td style="padding: 4px 3px; text-align: right; color: #fff; font-size: 9px;">${avgLikesCostPerUnit > 0 ? '$' + avgLikesCostPerUnit.toFixed(4) : '-'}</td>
                    </tr>
                `;
            }
            
            html += `
                        </tbody>
                    </table>
                </div>
            `;
            return html;
        }
        
        let isRefreshing = false;
        let allVideosData = {};
        let cachedProgressData = null;
        let lastProgressFetch = 0;
        const CACHE_DURATION = 5000; // Cache for 5 seconds
        
        // TIMER PERSISTENCE: Store timer target times globally so they survive refreshes
        window.timerStates = window.timerStates || {};
        // Format: { videoUrl: { targetTime: timestamp, type: 'views'|'likes' } }
        
        // Invalidate cache to force fresh data load (call after mutations)
        function invalidateCache() {
            cachedProgressData = null;
            lastProgressFetch = 0;
            console.log('Cache invalidated - next load will fetch fresh data');
        }
        
        // Instant render from cached data (no API calls) - FOR FAST NAVIGATION
        function renderFromCache(progress, route, content) {
            allVideosData = progress;
            renderSummaryStats(progress);
            
            if (Object.keys(progress).length === 0) {
                content.innerHTML = '<div class="empty-state"><h2>No videos in progress</h2></div>';
                return;
            }
            
            // Just render the cached data directly - no need to call loadDashboard again
            // The data is already fresh (checked in loadDashboard)
            console.log('[renderFromCache] Rendering directly from cache');
        }
        
        // Loading indicator functions
        function showLoading(message = 'Loading...') {
            const loadingEl = document.getElementById('global-loading');
            const messageEl = document.getElementById('loading-message');
            if (loadingEl) {
                messageEl.textContent = message;
                loadingEl.style.display = 'flex';
            }
        }
        
        function hideLoading() {
            const loadingEl = document.getElementById('global-loading');
            if (loadingEl) {
                loadingEl.style.display = 'none';
            }
        }
        
        // Global helper function to escape template literals
        function escapeTemplateLiteral(str) {
            if (!str) return '';
            return String(str)
                .split('\\\\').join('\\\\\\\\')  // Escape backslashes first
                .split("'").join("\\\\'")
                .split('`').join('\\\\`')
                .split('$').join('\\\\$');
        }
        
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
            // INSTANT navigation - hashchange handler will render
            window.location.hash = '';
        }
        
        function navigateToCampaign(campaignId) {
            // INSTANT navigation - just change hash
            // Switch to dashboard tab and navigate to campaign detail
            switchTab('dashboard');
            window.location.hash = '#campaign/' + encodeURIComponent(campaignId);
            // hashchange handler will trigger rendering with cached data
        }
        
        function navigateToVideo(videoUrl) {
            window.location.hash = '#video/' + encodeURIComponent(videoUrl);
            loadDashboard(false);
        }
        
        function handleManualOrder(videoUrl, service) {
            // Map service name to metric name
            const metricMap = {
                'views': 'views',
                'likes': 'likes',
                'comments': 'comments',
                'comment_likes': 'comment_likes'
            };
            const metric = metricMap[service] || service;
            
            // Get minimum order amount (defaults)
            const minimums = {
                'views': 100,
                'likes': 50,
                'comments': 10,
                'comment_likes': 5
            };
            const minimum = minimums[metric] || 10;
            
            // Call the manualOrder function to prompt and place order
            if (typeof manualOrder === 'function') {
                manualOrder(videoUrl, metric, minimum, null);
            } else {
                // Fallback: navigate to video page
                window.location.hash = '#video/' + encodeURIComponent(videoUrl);
                loadDashboard(false);
            }
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
                        <div class="summary-stat-label">Campaigns:</div>
                        <div class="summary-stat-value">${totalVideos}</div>
                    </div>
                    <div class="summary-stat-card">
                        <div class="summary-stat-label">Views:</div>
                        <div class="summary-stat-value">${formatNumber(totalViews)}</div>
                    </div>
                    <div class="summary-stat-card">
                        <div class="summary-stat-label">Likes:</div>
                        <div class="summary-stat-value">${formatNumber(totalLikes)}</div>
                    </div>
                    <div class="summary-stat-card">
                        <div class="summary-stat-label">Comments:</div>
                        <div class="summary-stat-value">${formatNumber(totalComments)}</div>
                    </div>
                    <div class="summary-stat-card">
                        <div class="summary-stat-label">Spent:</div>
                        <div class="summary-stat-value">$${totalCost.toFixed(2)}</div>
                    </div>
                </div>
            `;
            
            document.getElementById('summary-stats-container').innerHTML = html;
        }
        
        function switchTab(tabName) {
            // Update tab buttons
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.remove('active');
                if (btn.getAttribute('data-tab') === tabName) {
                    btn.classList.add('active');
                }
            });
            
            // Update tab content
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
            });
            
            // Show/hide controls bar based on tab
            const controlsBar = document.getElementById('dashboard-controls');
            if (controlsBar) {
                controlsBar.style.display = tabName === 'dashboard' ? 'flex' : 'none';
            }
            
            if (tabName === 'dashboard') {
                document.getElementById('dashboard-content').classList.add('active');
                loadDashboard(false);
            } else if (tabName === 'campaigns') {
                document.getElementById('campaigns-content').classList.add('active');
                loadCampaigns();
            } else if (tabName === 'order-log') {
                document.getElementById('order-log-content').classList.add('active');
                renderOrderLog();
            }
        }
        
        async function renderOrderLog() {
            const container = document.getElementById('order-log-content');
            container.innerHTML = '<div class="loading">Loading order log...</div>';
            
            try {
                const response = await fetch('/api/progress');
                const progress = await response.json();
                
                // Collect all orders from all videos
                const allOrders = [];
                for (const [videoUrl, videoData] of Object.entries(progress)) {
                    const orderHistory = videoData.order_history || [];
                    for (const order of orderHistory) {
                        allOrders.push({
                            ...order,
                            video_url: videoUrl
                        });
                    }
                }
                
                // Sort by timestamp (newest first)
                allOrders.sort((a, b) => {
                    const timeA = new Date(a.timestamp || 0).getTime();
                    const timeB = new Date(b.timestamp || 0).getTime();
                    return timeB - timeA;
                });
                
                if (allOrders.length === 0) {
                    container.innerHTML = `
                        <div class="empty-state">
                            <h2>No Orders Yet</h2>
                            <p>Orders will appear here once they are placed.</p>
                        </div>
                    `;
                    return;
                }
                
                let html = '<div style="background: #1a1a1a; border-radius: 0; padding: 8px; border: 1px solid rgba(255,255,255,0.1);">';
                html += '<h2 style="color: #fff; margin-bottom: 12px; font-size: 1.5em;">Order History</h2>';
                html += '<div style="display: grid; gap: 12px;">';
                
                for (const order of allOrders) {
                    const { username, videoId } = extractVideoInfo(order.video_url);
                    const orderDate = order.timestamp ? new Date(order.timestamp).toLocaleString() : 'Unknown';
                    const orderType = order.type || 'scheduled';
                    const typeColor = orderType === 'manual' ? '#10b981' : orderType === 'catch_up' ? '#ef4444' : '#667eea';
                    
                    html += `
                        <div style="background: #2a2a2a; border-radius: 0; padding: 10px; border: 1px solid rgba(255,255,255,0.08);">
                            <div style="display: flex; justify-content: space-between; align-items: start; flex-wrap: wrap; gap: 12px;">
                                <div style="flex: 1; min-width: 200px;">
                                    <div style="color: #fff; font-weight: 600; margin-bottom: 6px;">${order.service ? order.service.charAt(0).toUpperCase() + order.service.slice(1) : 'Unknown'}</div>
                                    <div style="color: #888; font-size: 0.85em; margin-bottom: 4px;">${username || 'Video'}: ${videoId || order.video_url.substring(0, 40)}...</div>
                                    <div style="color: #666; font-size: 0.8em;">${orderDate}</div>
                                </div>
                                <div style="display: flex; gap: 16px; align-items: center; flex-wrap: wrap;">
                                    <div style="text-align: right;">
                                        <div style="color: #888; font-size: 0.8em; margin-bottom: 2px;">Quantity</div>
                                        <div style="color: #fff; font-weight: 600;">${formatNumber(order.quantity || 0)}</div>
                                    </div>
                                    <div style="text-align: right;">
                                        <div style="color: #888; font-size: 0.8em; margin-bottom: 2px;">Order ID</div>
                                        <div style="color: #667eea; font-weight: 600; font-family: monospace; font-size: 0.9em;">${order.order_id || 'N/A'}</div>
                                    </div>
                                    <div style="text-align: right;">
                                        <div style="color: #888; font-size: 0.8em; margin-bottom: 2px;">Type</div>
                                        <div style="color: ${typeColor}; font-weight: 600; font-size: 0.85em; text-transform: capitalize;">${orderType}</div>
                                    </div>
                                    ${order.cost ? `
                                    <div style="text-align: right;">
                                        <div style="color: #888; font-size: 0.8em; margin-bottom: 2px;">Cost</div>
                                        <div style="color: #ef4444; font-weight: 600;">$${parseFloat(order.cost).toFixed(4)}</div>
                                    </div>
                                    ` : ''}
                                </div>
                            </div>
                        </div>
                    `;
                }
                
                html += '</div></div>';
                container.innerHTML = html;
            } catch (error) {
                console.error('Error loading order log:', error);
                container.innerHTML = `
                    <div class="empty-state">
                        <h2>Error Loading Order Log</h2>
                        <p>${error.message}</p>
                    </div>
                `;
            }
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
            const input = document.getElementById('new-video-url-input');
            const textarea = document.getElementById('new-video-url');
            const errorDiv = document.getElementById('add-video-error');
            const campaignSelector = document.getElementById('add-video-campaign-selector');
            const urlListContainer = document.getElementById('url-list-container');
            const urlList = document.getElementById('url-list');
            const urlCount = document.getElementById('url-count');
            
            modal.style.display = 'flex';
            input.value = '';
            textarea.value = '';
            errorDiv.style.display = 'none';
            errorDiv.textContent = '';
            urlListContainer.style.display = 'none';
            urlList.innerHTML = '';
            urlCount.textContent = '0';
            if (campaignSelector) {
                populateAddVideoCampaignSelector();
                campaignSelector.value = campaignId || '';
            }
            
            // Focus input after modal appears
            setTimeout(() => input.focus(), 100);
        }
        
        function addUrlToList() {
            const input = document.getElementById('new-video-url-input');
            const textarea = document.getElementById('new-video-url');
            const urlListContainer = document.getElementById('url-list-container');
            const urlList = document.getElementById('url-list');
            const urlCount = document.getElementById('url-count');
            const errorDiv = document.getElementById('add-video-error');
            
            const url = input.value.trim();
            
            // Validate URL
            if (!url) {
                return;
            }
            
            if (!url.includes('tiktok.com')) {
                errorDiv.textContent = 'Please enter a valid TikTok URL';
                errorDiv.style.display = 'block';
                return;
            }
            
            // Hide error
            errorDiv.style.display = 'none';
            
            // Get existing URLs from textarea
            const existingUrls = textarea.value.trim().split('\\n').filter(u => u.trim().length > 0);
            
            // Check for duplicates
            if (existingUrls.includes(url)) {
                errorDiv.textContent = 'This URL is already in the list';
                errorDiv.style.display = 'block';
                return;
            }
            
            // Add URL to list
            existingUrls.push(url);
            textarea.value = existingUrls.join('\\n');
            
            // Update UI - escape URL for HTML attribute
            function escapeForAttr(str) {
                if (!str) return '';
                return String(str)
                    .replace(/&/g, '&amp;')
                    .replace(/"/g, '&quot;')
                    .replace(/'/g, '&#39;')
                    .replace(/</g, '&lt;')
                    .replace(/>/g, '&gt;');
            }
            const urlItem = document.createElement('div');
            urlItem.style.cssText = 'display: flex; align-items: center; justify-content: space-between; padding: 6px 8px; border-bottom: 1px solid rgba(255,255,255,0.05); font-family: monospace; font-size: 12px;';
            urlItem.innerHTML = `
                <span style="color: #b0b0b0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1;">${escapeForAttr(url)}</span>
                <button class="remove-url-btn" data-url="${escapeForAttr(url)}" style="background: transparent; border: none; color: #ef4444; cursor: pointer; padding: 2px 6px; font-size: 14px; margin-left: 8px;">×</button>
            `;
            urlList.appendChild(urlItem);
            
            // Show container and update count
            urlListContainer.style.display = 'block';
            urlCount.textContent = existingUrls.length;
            
            // Clear input
            input.value = '';
            input.focus();
        }
        
        function removeUrlFromList(urlToRemove) {
            const textarea = document.getElementById('new-video-url');
            const urlListContainer = document.getElementById('url-list-container');
            const urlList = document.getElementById('url-list');
            const urlCount = document.getElementById('url-count');
            
            // Get existing URLs
            const existingUrls = textarea.value.trim().split('\\n').filter(u => u.trim().length > 0);
            
            // Remove URL
            const filteredUrls = existingUrls.filter(u => u !== urlToRemove);
            textarea.value = filteredUrls.join('\\n');
            
            // Rebuild list - escape URL for HTML attribute
            function escapeForAttr(str) {
                if (!str) return '';
                return String(str)
                    .replace(/&/g, '&amp;')
                    .replace(/"/g, '&quot;')
                    .replace(/'/g, '&#39;')
                    .replace(/</g, '&lt;')
                    .replace(/>/g, '&gt;');
            }
            urlList.innerHTML = '';
            filteredUrls.forEach(url => {
                const urlItem = document.createElement('div');
                urlItem.style.cssText = 'display: flex; align-items: center; justify-content: space-between; padding: 6px 8px; border-bottom: 1px solid rgba(255,255,255,0.05); font-family: monospace; font-size: 12px;';
                urlItem.innerHTML = `
                    <span style="color: #b0b0b0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; flex: 1;">${escapeForAttr(url)}</span>
                    <button class="remove-url-btn" data-url="${escapeForAttr(url)}" style="background: transparent; border: none; color: #ef4444; cursor: pointer; padding: 2px 6px; font-size: 14px; margin-left: 8px;">×</button>
                `;
                urlList.appendChild(urlItem);
            });
            
            // Update count and hide container if empty
            urlCount.textContent = filteredUrls.length;
            if (filteredUrls.length === 0) {
                urlListContainer.style.display = 'none';
            }
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
                    
                    // Handle server errors (502/503) gracefully
                    if (!response.ok) {
                        const errorMsg = `Server error ${response.status}`;
                        errorCount++;
                        statusLine.innerHTML = `[${i + 1}/${urls.length}] ${url.substring(0, 60)}... <span style="color: #ef4444;">✗ ${errorMsg}</span>`;
                        results.push({ url, success: false, error: errorMsg });
                        continue;
                    }
                    
                    // Try to parse JSON
                    let data;
                    try {
                        const text = await response.text();
                        if (!text || text.trim() === '') {
                            throw new Error('Empty response');
                        }
                        data = JSON.parse(text);
                    } catch (parseError) {
                        errorCount++;
                        statusLine.innerHTML = `[${i + 1}/${urls.length}] ${url.substring(0, 60)}... <span style="color: #ef4444;">✗ Parse error</span>`;
                        results.push({ url, success: false, error: 'Invalid response from server' });
                        continue;
                    }
                    
                    if (data.success) {
                        successCount++;
                        statusLine.innerHTML = `[${i + 1}/${urls.length}] ${url.substring(0, 60)}... <span style="color: #10b981;">Added</span>`;
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
                successDiv.textContent = `Successfully added ${successCount} video(s)${errorCount > 0 ? ` (${errorCount} failed)` : ''}`;
                successDiv.style.display = 'block';
                
                // Show notification
                showNotification(`${successCount} video(s) added successfully`, 'success');
                
                // Close modal immediately for better UX
                hideAddVideoModal();
                // Clear input immediately
                input.value = '';
                
                // Refresh in background without blocking (faster)
                loadDashboard(false).catch(err => console.error('[addVideo] Dashboard refresh error:', err));
                loadCampaigns().catch(err => console.error('[addVideo] Campaigns refresh error:', err));
                
                // Re-enable buttons
                addButton.disabled = false;
                cancelButton.disabled = false;
                addButton.textContent = 'Add Video(s)';
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
                border-radius: 0;
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
                const safeName = name.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
                html += `<option value="${escapeTemplateLiteral(campaignId)}">${safeName}</option>`;
            }
            selector.innerHTML = html;
        }
        
        // Close modals when clicking outside
        // Event delegation for catch-up buttons (they're dynamically created)
        document.addEventListener('click', function(e) {
            // Handle stop overtime button
            if (e.target && e.target.classList.contains('stop-overtime-btn')) {
                e.preventDefault();
                e.stopPropagation();
                const videoUrl = e.target.getAttribute('data-video-url');
                if (videoUrl) {
                    stopOvertime(videoUrl);
                }
                return;
            }
            
            // Handle show video details link
            if (e.target && e.target.classList.contains('show-video-details-link')) {
                e.preventDefault();
                e.stopPropagation();
                const videoUrl = e.target.getAttribute('data-video-url');
                if (videoUrl) {
                    showVideoDetailsModal(videoUrl);
                }
                return false;
            }
            
            // Handle edit time left cell
            if (e.target && e.target.classList.contains('edit-time-left-cell')) {
                e.preventDefault();
                e.stopPropagation();
                const videoUrl = e.target.getAttribute('data-video-url');
                const currentHours = parseInt(e.target.getAttribute('data-current-hours')) || 0;
                const currentMinutes = parseInt(e.target.getAttribute('data-current-minutes')) || 0;
                if (videoUrl) {
                    showEditTimeLeftModal(videoUrl, currentHours, currentMinutes);
                }
                return;
            }
            
            // Handle manual order link (in table cells)
            if (e.target && e.target.classList.contains('manual-order-link')) {
                e.preventDefault();
                e.stopPropagation();
                const videoUrl = e.target.getAttribute('data-video-url');
                const metric = e.target.getAttribute('data-metric');
                if (videoUrl && metric) {
                    handleManualOrder(videoUrl, metric);
                }
                return;
            }
            
            // Handle delete campaign button
            if (e.target && e.target.classList.contains('delete-campaign-btn')) {
                e.preventDefault();
                e.stopPropagation();
                const campaignId = e.target.getAttribute('data-campaign-id');
                const campaignName = e.target.getAttribute('data-campaign-name');
                if (campaignId) {
                    deleteCampaign(campaignId, campaignName || 'Unnamed Campaign');
                }
                return;
            }
            
            // Handle remove campaign link
            if (e.target && e.target.classList.contains('remove-campaign-link')) {
                e.preventDefault();
                e.stopPropagation();
                const campaignId = e.target.getAttribute('data-campaign-id');
                const campaignName = e.target.getAttribute('data-campaign-name');
                if (campaignId) {
                    deleteCampaign(campaignId, campaignName || 'Unnamed Campaign');
                }
                return false;
            }
            
            // Handle edit campaign button
            if (e.target && e.target.classList.contains('edit-campaign-btn')) {
                e.preventDefault();
                e.stopPropagation();
                const campaignId = e.target.getAttribute('data-campaign-id');
                if (campaignId) {
                    showEditCampaignModal(campaignId);
                }
                return;
            }
            
            // Handle add video to campaign button
            if (e.target && e.target.classList.contains('add-video-to-campaign-btn')) {
                e.preventDefault();
                e.stopPropagation();
                const campaignId = e.target.getAttribute('data-campaign-id');
                if (campaignId) {
                    showAddVideoToCampaignModal(campaignId);
                }
                return;
            }
            
            // Handle end campaign button
            if (e.target && e.target.classList.contains('end-campaign-btn')) {
                e.preventDefault();
                e.stopPropagation();
                const campaignId = e.target.getAttribute('data-campaign-id');
                if (campaignId) {
                    endCampaign(campaignId);
                }
                return;
            }
            
            // Handle remove URL button
            if (e.target && e.target.classList.contains('remove-url-btn')) {
                e.preventDefault();
                e.stopPropagation();
                const url = e.target.getAttribute('data-url');
                if (url) {
                    removeUrlFromList(url);
                }
                return;
            }
            
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
        
        async function loadDashboard(showLoadingIndicator = false, forceRefresh = false) {
            const route = getCurrentRoute();
            const content = document.getElementById('dashboard-content');
            const now = Date.now();
            
            // FAST PATH: Use cached data for instant navigation (if available and fresh)
            if (!forceRefresh && cachedProgressData && (now - lastProgressFetch) < CACHE_DURATION) {
                console.log('[FAST PATH] Using cached data (age: ' + Math.floor((now - lastProgressFetch)/1000) + 's)');
                // CRITICAL: Still need to start countdown timers even with cached data!
                try {
                    setTimeout(startNextPurchaseCountdowns, 100);
                    setTimeout(startTimeToGoalCountdowns, 150);
                    setTimeout(startTableCountdowns, 200);
                } catch(e) {
                    console.error('Error starting countdowns:', e);
                }
                return Promise.resolve();
            }
            
            // Prevent multiple simultaneous refreshes
            if (isRefreshing) {
                console.log('Already refreshing, skipping...');
                return Promise.resolve();
            }
            isRefreshing = true;
            
            // Show subtle loading only if not using cache
            if (showLoadingIndicator) {
                showLoading('Loading...');
            }
            // Skip dimming for faster perceived performance
            // Content updates instantly with no visual interruption
            
            try {
                const response = await fetch('/api/progress');
                
                // Handle server errors gracefully
                if (!response.ok) {
                    console.warn(`[loadDashboard] Server error ${response.status}, will retry on next refresh`);
                    // Don't crash, use empty progress and let periodic refresh retry
                    const progress = {};
                    allVideosData = progress;
                    if (content) content.style.opacity = '1';
                    hideLoading();
                    isRefreshing = false;
                    return;
                }
                
                // Try to parse JSON, handle empty/invalid responses
                let progress;
                try {
                    const text = await response.text();
                    if (!text || text.trim() === '') {
                        console.warn('[loadDashboard] Empty response, using empty progress');
                        progress = {};
                    } else {
                        progress = JSON.parse(text);
                    }
                } catch (parseError) {
                    console.error('[loadDashboard] Failed to parse JSON:', parseError);
                    progress = {}; // Use empty progress on parse error
                }
                
                // Store all videos data for filtering
                allVideosData = progress;
                
                // Update cache
                cachedProgressData = progress;
                lastProgressFetch = Date.now();
                
                // Load campaigns ONLY on first/full load OR if we're viewing a campaign and don't have it
                // Avoid re-rendering campaign UI every refresh (it wipes calculator inputs, checkbox selection state, etc.).
                const route = getCurrentRoute();
                const needsCampaigns = showLoading && (!campaignsData || Object.keys(campaignsData).length === 0);
                const needsSpecificCampaign = route.type === 'campaign' && (!campaignsData || !campaignsData[route.campaignId]);
                
                // Render summary stats immediately
                renderSummaryStats(progress);
                
                if (Object.keys(progress).length === 0) {
                    content.innerHTML = `
                        <div class="empty-state">
                            <h2>No videos in progress</h2>
                            <p>Add a video using: python run_delivery_bot.py &lt;video_url&gt;</p>
                        </div>
                    `;
                    if (content) content.style.opacity = '1';
                    hideLoading();
                    isRefreshing = false;
                    return;
                }
                
                let html = '';
                
                if (route.type === 'campaign') {
                    // Show campaign detail view with all posts - full page view
                    const campaignId = route.campaignId;
                    
                    // Ensure campaigns are loaded before rendering campaign view
                    if (needsCampaigns || needsSpecificCampaign) {
                        try {
                            await loadCampaigns();
                        } catch (campaignError) {
                            console.error('[loadDashboard] Failed to load campaigns:', campaignError);
                            // Continue without campaigns if load fails
                        }
                    }
                    
                    const campaign = campaignsData && campaignsData[campaignId] ? campaignsData[campaignId] : null;
                    
                    // Hide campaigns tab content when viewing campaign detail
                    const campaignsContent = document.getElementById('campaigns-content');
                    if (campaignsContent) {
                        campaignsContent.classList.remove('active');
                    }
                    // Hide campaigns overview summary on dashboard tab
                    const campaignsSummary = document.getElementById('campaigns-summary');
                    if (campaignsSummary) {
                        campaignsSummary.style.display = 'none';
                    }
                    // Ensure dashboard content is visible
                    const dashboardContent = document.getElementById('dashboard-content');
                    if (dashboardContent) {
                        dashboardContent.classList.add('active');
                    }
                    // Activate dashboard tab button
                    document.querySelectorAll('.tab-btn').forEach(btn => {
                        btn.classList.remove('active');
                        if (btn.getAttribute('data-tab') === 'dashboard') {
                            btn.classList.add('active');
                        }
                    });
                    
                    if (!campaign) {
                        html = `
                            <div class="empty-state">
                                <h2>Campaign Not Found</h2>
                                <p>The requested campaign no longer exists or is still loading.</p>
                                <div class="back-button" data-action="navigate-home" style="margin-top: 20px;">← Back to All Campaigns</div>
                            </div>
                        `;
                    } else {
                        // Render campaign header immediately for faster perceived performance
                        const campaignVideos = (campaign && campaign.videos) ? campaign.videos : [];
                        const financial = (campaign && campaign.financial) ? campaign.financial : {};
                        
                        html += '<div class="back-button" data-action="navigate-home" data-switch-to="campaigns">← Back to All Campaigns</div>';
                        html += `<div style="background: #1a1a1a; border-radius: 0; padding: 10px; margin-bottom: 16px; border: 1px solid rgba(255,255,255,0.1);">`;
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
                            html += `<div style="text-align: center; padding: 30px; color: #b0b0b0;">No videos in this campaign yet. Add videos using the "Add Video" button.</div>`;
                        } else {
                            // Render accounting-style table directly in HTML (optimized for speed)
                            // Define escapeTemplateLiteral function for this scope
                            function escapeTemplateLiteral(str) {
                                if (!str) return '';
                                return String(str)
                                    .split('\\\\').join('\\\\\\\\')  // Escape backslashes first
                                    .split("'").join("\\\\'")
                                    .split('`').join('\\\\`')
                                    .split('$').join('\\\\$');
                            }
                            
                            // Ensure progress data exists
                            if (!progress || typeof progress !== 'object') {
                                progress = {};
                            }
                            
                            let tableHtml = `
                                <div style="overflow-x: auto; margin-top: 10px;">
                                    <table style="width: 100%; border-collapse: collapse; background: #1a1a1a; border: 1px solid rgba(255,255,255,0.1); font-family: monospace; font-size: 10px;">
                                        <thead>
                                            <tr style="background: #252525; border-bottom: 2px solid rgba(255,255,255,0.1);">
                                                <th style="padding: 6px 4px; text-align: left; color: #fff; font-weight: 600; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);">VIDEO ID</th>
                                                <th style="padding: 6px 4px; text-align: center; color: #fff; font-weight: 600; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);">DATE POSTED</th>
                                                <th style="padding: 6px 4px; text-align: center; color: #fff; font-weight: 600; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);">TIME LEFT</th>
                                                <th style="padding: 6px 4px; text-align: right; color: #fff; font-weight: 600; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);">CURR VIEWS</th>
                                                <th style="padding: 6px 4px; text-align: right; color: #fff; font-weight: 600; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);">EXP VIEWS</th>
                                                <th style="padding: 6px 4px; text-align: center; color: #fff; font-weight: 600; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);">MANUAL ORD</th>
                                                <th style="padding: 6px 4px; text-align: center; color: #fff; font-weight: 600; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);">SCHED ORD</th>
                                                <th style="padding: 6px 4px; text-align: center; color: #fff; font-weight: 600; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);">TIME NEXT</th>
                                                <th style="padding: 6px 4px; text-align: right; color: #fff; font-weight: 600; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);">UNITS/ORD</th>
                                                <th style="padding: 6px 4px; text-align: right; color: #fff; font-weight: 600; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);">$/UNIT</th>
                                                <th style="padding: 6px 4px; text-align: right; color: #fff; font-weight: 600; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);">CURR LIKES</th>
                                                <th style="padding: 6px 4px; text-align: right; color: #fff; font-weight: 600; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);">EXP LIKES</th>
                                                <th style="padding: 6px 4px; text-align: center; color: #fff; font-weight: 600; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);">LIKES MAN</th>
                                                <th style="padding: 6px 4px; text-align: center; color: #fff; font-weight: 600; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);">LIKES SCH</th>
                                                <th style="padding: 6px 4px; text-align: center; color: #fff; font-weight: 600; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);">LIKES NEXT</th>
                                                <th style="padding: 6px 4px; text-align: right; color: #fff; font-weight: 600; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);">LIKES UNITS</th>
                                                <th style="padding: 6px 4px; text-align: right; color: #fff; font-weight: 600; font-size: 9px;">LIKES $/U</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                            `;
                            
                            // Render table rows for each video (optimized loop)
                            for (const videoUrl of campaignVideos) {
                                if (!videoUrl) continue; // Skip invalid URLs
                                const videoData = progress[videoUrl];
                                if (!videoData) continue; // Skip if video data not found
                                
                                try {
                                    // Extract video ID
                                    const videoIdMatch = videoUrl.match(/video\\/(\\d+)/);
                                    const videoId = videoIdMatch ? videoIdMatch[1] : videoUrl.substring(videoUrl.length - 15);
                                    
                                    // Get start time (date posted) and calculate time left
                                    const startTime = videoData.start_time ? new Date(videoData.start_time) : null;
                                    const uploadTime = startTime ? startTime.toLocaleString('en-US', {month: '2-digit', day: '2-digit', year: '2-digit', hour: '2-digit', minute: '2-digit'}) : 'N/A';
                                    
                                    // Calculate time left to reach goal
                                    const target_completion = videoData.target_completion_time || videoData.target_completion_datetime;
                                    let timeLeft = 'N/A';
                                    if (target_completion && startTime) {
                                        const now = new Date();
                                        const endTime = new Date(target_completion);
                                        const remainingMs = endTime - now;
                                        if (remainingMs > 0) {
                                            const remainingHours = Math.floor(remainingMs / (1000 * 60 * 60));
                                            const remainingMinutes = Math.floor((remainingMs % (1000 * 60 * 60)) / (1000 * 60));
                                            const remainingSeconds = Math.floor((remainingMs % (1000 * 60)) / 1000);
                                            timeLeft = remainingHours + 'h' + (remainingMinutes > 0 ? remainingMinutes + 'm' : '') + remainingSeconds + 's';
                                        } else {
                                            // Check if overtime is stopped
                                            const videoOvertimeStopped = videoData && videoData.overtime_stopped === true;
                                            timeLeft = videoOvertimeStopped ? 'Overtime stopped' : 'OVERTIME';
                                        }
                                    }
                                    
                                    const real_views = videoData.real_views || 0;
                                    const real_likes = videoData.real_likes || 0;
                                    const target_views = videoData.target_views || 0;
                                    const target_likes = videoData.target_likes || 0;
                                    
                                    // Calculate expected views/likes
                                    let expected_views = 0;
                                    let expected_likes = 0;
                                    if (startTime && target_completion) {
                                        const now = new Date();
                                        const endTime = new Date(target_completion);
                                        const totalDuration = endTime - startTime;
                                        const elapsed = now - startTime;
                                        if (totalDuration > 0 && elapsed > 0) {
                                            const progress = Math.min(1, elapsed / totalDuration);
                                            expected_views = Math.floor(target_views * progress);
                                            expected_likes = Math.floor(target_likes * progress);
                                        }
                                    }
                                    
                                    // Order counts
                                    const orderHistory = videoData.order_history || [];
                                    const viewsOrders = orderHistory.filter(o => o.service === 'views');
                                    const manualViewsOrders = viewsOrders.filter(o => o.type === 'manual' || (!o.type && o.manual)).length;
                                    const schedViewsOrders = viewsOrders.filter(o => o.type === 'scheduled' || (!o.type && !o.manual)).length;
                                    
                                    const likesOrders = orderHistory.filter(o => o.service === 'likes');
                                    const manualLikesOrders = likesOrders.filter(o => o.type === 'manual' || (!o.type && o.manual)).length;
                                    const schedLikesOrders = likesOrders.filter(o => o.type === 'scheduled' || (!o.type && !o.manual)).length;
                                    
                                    // Units and cost per unit (average of scheduled orders only)
                                    let avgViewsUnits = 0;
                                    let avgViewsCostPerUnit = 0;
                                    const schedViewsOrdersList = viewsOrders.filter(o => o.type === 'scheduled' || (!o.type && !o.manual));
                                    if (schedViewsOrdersList.length > 0) {
                                        const totalViewsUnits = schedViewsOrdersList.reduce((sum, o) => sum + (o.quantity || 0), 0);
                                        const totalViewsCost = schedViewsOrdersList.reduce((sum, o) => sum + (o.cost || 0), 0);
                                        avgViewsUnits = Math.floor(totalViewsUnits / schedViewsOrdersList.length);
                                        avgViewsCostPerUnit = totalViewsUnits > 0 ? totalViewsCost / totalViewsUnits : 0;
                                    }
                                    
                                    let avgLikesUnits = 0;
                                    let avgLikesCostPerUnit = 0;
                                    const schedLikesOrdersList = likesOrders.filter(o => o.type === 'scheduled' || (!o.type && !o.manual));
                                    if (schedLikesOrdersList.length > 0) {
                                        const totalLikesUnits = schedLikesOrdersList.reduce((sum, o) => sum + (o.quantity || 0), 0);
                                        const totalLikesCost = schedLikesOrdersList.reduce((sum, o) => sum + (o.cost || 0), 0);
                                        avgLikesUnits = Math.floor(totalLikesUnits / schedLikesOrdersList.length);
                                        avgLikesCostPerUnit = totalLikesUnits > 0 ? totalLikesCost / totalLikesUnits : 0;
                                    }
                                    
                                    // Time to next order - calculate based on remaining time divided by orders needed
                                    let timeToNext = 'N/A';
                                    let likesTimeToNext = 'N/A';
                                    
                                    // Minimum order sizes
                                    const MIN_VIEWS_ORDER = 50;
                                    const MIN_LIKES_ORDER = 10;
                                    
                                    // Calculate for views
                                    if (target_completion && startTime) {
                                        const now = new Date();
                                        const endTime = new Date(target_completion);
                                        const remainingMs = endTime - now;
                                        
                                        if (remainingMs > 0) {
                                            // Calculate views needed
                                            const viewsNeeded = Math.max(0, target_views - real_views);
                                            
                                            if (viewsNeeded <= 0) {
                                                timeToNext = 'DONE';
                                            } else {
                                                // Use average from scheduled orders, or minimum if no orders
                                                let unitsPerOrder = avgViewsUnits > 0 ? avgViewsUnits : MIN_VIEWS_ORDER;
                                                
                                                // Calculate orders needed based on units per order
                                                const ordersNeeded = Math.ceil(viewsNeeded / unitsPerOrder);
                                                
                                                if (ordersNeeded > 0) {
                                                    const timePerOrder = remainingMs / ordersNeeded;
                                                    const hours = Math.floor(timePerOrder / (1000 * 60 * 60));
                                                    const mins = Math.floor((timePerOrder % (1000 * 60 * 60)) / (1000 * 60));
                                                    const secs = Math.floor((timePerOrder % (1000 * 60)) / 1000);
                                                    if (hours > 0 || mins > 0 || secs > 0) {
                                                        timeToNext = hours + 'h' + (mins > 0 ? mins + 'm' : '') + secs + 's';
                                                    } else {
                                                        timeToNext = 'READY';
                                                    }
                                                } else {
                                                    timeToNext = 'READY';
                                                }
                                            }
                                        } else {
                                            timeToNext = 'OVERTIME';
                                        }
                                    }
                                    
                                    // Calculate for likes
                                    if (target_completion && startTime) {
                                        const now = new Date();
                                        const endTime = new Date(target_completion);
                                        const remainingMs = endTime - now;
                                        
                                        if (remainingMs > 0) {
                                            // Calculate likes needed
                                            const likesNeeded = Math.max(0, target_likes - real_likes);
                                            
                                            if (likesNeeded <= 0) {
                                                likesTimeToNext = 'DONE';
                                            } else {
                                                // Use average from scheduled orders, or minimum if no orders
                                                let unitsPerOrder = avgLikesUnits > 0 ? avgLikesUnits : MIN_LIKES_ORDER;
                                                
                                                // Calculate orders needed based on units per order
                                                const ordersNeeded = Math.ceil(likesNeeded / unitsPerOrder);
                                                
                                                if (ordersNeeded > 0) {
                                                    const timePerOrder = remainingMs / ordersNeeded;
                                                    const hours = Math.floor(timePerOrder / (1000 * 60 * 60));
                                                    const mins = Math.floor((timePerOrder % (1000 * 60 * 60)) / (1000 * 60));
                                                    const secs = Math.floor((timePerOrder % (1000 * 60)) / 1000);
                                                    if (hours > 0 || mins > 0 || secs > 0) {
                                                        likesTimeToNext = hours + 'h' + (mins > 0 ? mins + 'm' : '') + secs + 's';
                                                    } else {
                                                        likesTimeToNext = 'READY';
                                                    }
                                                } else {
                                                    likesTimeToNext = 'READY';
                                                }
                                            }
                                        } else {
                                            likesTimeToNext = 'OVERTIME';
                                        }
                                    }
                                    
                                    // Calculate current hours/minutes for time left edit
                                    let currentHours = 0;
                                    let currentMinutes = 0;
                                    if (target_completion && startTime) {
                                        const now = new Date();
                                        const endTime = new Date(target_completion);
                                        const remainingMs = endTime - now;
                                        if (remainingMs > 0) {
                                            currentHours = Math.floor(remainingMs / (1000 * 60 * 60));
                                            currentMinutes = Math.floor((remainingMs % (1000 * 60 * 60)) / (1000 * 60));
                                        }
                                    }
                                    
                                    tableHtml += `
                                        <tr style="border-bottom: 1px solid rgba(255,255,255,0.05);" onmouseover="this.style.background='#252525'" onmouseout="this.style.background='transparent'">
                                            <td style="padding: 4px 3px; color: #667eea; font-family: monospace; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05); text-align: left;" title="${escapeTemplateLiteral(videoUrl || '')}"><a href="#" class="show-video-details-link" data-video-url="${escapeTemplateLiteral(videoUrl || '')}" style="color: #667eea; text-decoration: none; cursor: pointer;">${videoId || 'N/A'}</a></td>
                                            <td style="padding: 4px 3px; text-align: center; color: #fff; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);">${uploadTime}</td>
                                            <td style="padding: 4px 3px; text-align: center; color: ${timeLeft === 'OVERTIME' ? '#f59e0b' : timeLeft === 'Overtime stopped' ? '#888' : '#fff'}; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05); cursor: pointer; text-decoration: underline;" class="edit-time-left-cell" data-video-url="${escapeTemplateLiteral(videoUrl)}" data-current-hours="${currentHours}" data-current-minutes="${currentMinutes}" title="Click to edit time left" data-time-left data-target-time="${target_completion || ''}">${timeLeft}</td>
                                            <td style="padding: 4px 3px; text-align: right; color: #fff; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);" data-real-views data-video-url="${escapeTemplateLiteral(videoUrl)}">${formatNumber(real_views)}</td>
                                            <td style="padding: 4px 3px; text-align: right; color: ${real_views >= expected_views ? '#10b981' : '#f59e0b'}; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);">${formatNumber(expected_views)}</td>
                                            <td style="padding: 4px 3px; text-align: center; color: #b0b0b0; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);" data-manual-views-orders data-video-url="${escapeTemplateLiteral(videoUrl)}"><span class="manual-order-link" data-video-url="${escapeTemplateLiteral(videoUrl)}" data-metric="views" style="cursor: pointer; text-decoration: underline; color: #667eea;">${manualViewsOrders}</span></td>
                                            <td style="padding: 4px 3px; text-align: center; color: #b0b0b0; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);" data-sched-views-orders data-video-url="${escapeTemplateLiteral(videoUrl)}">${schedViewsOrders}</td>
                                            <td style="padding: 4px 3px; text-align: center; color: ${timeToNext === 'READY' ? '#10b981' : '#fff'}; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);" data-time-next data-video-url="${escapeTemplateLiteral(videoUrl)}" data-target-time="${target_completion || ''}" data-target-views="${target_views}" data-real-views="${real_views}" data-avg-units="${avgViewsUnits || MIN_VIEWS_ORDER}">${timeToNext}</td>
                                            <td style="padding: 4px 3px; text-align: right; color: #fff; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);">${avgViewsUnits > 0 ? formatNumber(avgViewsUnits) : '-'}</td>
                                            <td style="padding: 4px 3px; text-align: right; color: #fff; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);">${avgViewsCostPerUnit > 0 ? '$' + avgViewsCostPerUnit.toFixed(4) : '-'}</td>
                                            <td style="padding: 4px 3px; text-align: right; color: #fff; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);" data-real-likes data-video-url="${escapeTemplateLiteral(videoUrl)}">${formatNumber(real_likes)}</td>
                                            <td style="padding: 4px 3px; text-align: right; color: ${real_likes >= expected_likes ? '#10b981' : '#f59e0b'}; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);">${formatNumber(expected_likes)}</td>
                                            <td style="padding: 4px 3px; text-align: center; color: #b0b0b0; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);" data-manual-likes-orders data-video-url="${escapeTemplateLiteral(videoUrl)}"><span class="manual-order-link" data-video-url="${escapeTemplateLiteral(videoUrl)}" data-metric="likes" style="cursor: pointer; text-decoration: underline; color: #667eea;">${manualLikesOrders}</span></td>
                                            <td style="padding: 4px 3px; text-align: center; color: #b0b0b0; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);" data-sched-likes-orders data-video-url="${escapeTemplateLiteral(videoUrl)}">${schedLikesOrders}</td>
                                            <td style="padding: 4px 3px; text-align: center; color: ${likesTimeToNext === 'READY' ? '#10b981' : '#fff'}; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);" data-likes-next data-video-url="${escapeTemplateLiteral(videoUrl)}" data-target-time="${target_completion || ''}" data-target-likes="${target_likes}" data-real-likes="${real_likes}" data-avg-units="${avgLikesUnits || MIN_LIKES_ORDER}">${likesTimeToNext}</td>
                                            <td style="padding: 4px 3px; text-align: right; color: #fff; font-size: 9px; border-right: 1px solid rgba(255,255,255,0.05);">${avgLikesUnits > 0 ? formatNumber(avgLikesUnits) : '-'}</td>
                                            <td style="padding: 4px 3px; text-align: right; color: #fff; font-size: 9px;">${avgLikesCostPerUnit > 0 ? '$' + avgLikesCostPerUnit.toFixed(4) : '-'}</td>
                                        </tr>
                                    `;
                                } catch (rowError) {
                                    console.error('[loadDashboard] Error rendering table row for', videoUrl, ':', rowError);
                                    // Continue with next video instead of crashing
                                }
                            }
                            
                            tableHtml += `
                                        </tbody>
                                    </table>
                                </div>
                            `;
                            html += tableHtml;
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
                
                // Fast update - use innerHTML but keep opacity at 1 (no flicker)
                content.innerHTML = html;
                
                // Table is now rendered directly in HTML, no async rendering needed
                
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
                
                // Show/hide campaigns overview based on route
                const campaignsSummary = document.getElementById('campaigns-summary');
                if (campaignsSummary) {
                    if (route.type === 'campaign') {
                        // Hide campaigns overview when viewing campaign detail
                        campaignsSummary.style.display = 'none';
                    } else {
                        // Show campaigns overview on home page
                        campaignsSummary.style.display = 'block';
                    }
                }
                
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
                // Start countdown timers for table cells (TIME LEFT, TIME NEXT, LIKES NEXT)
                setTimeout(startTableCountdowns, 700);
                // Start periodic table data refresh
                setTimeout(startTableDataRefresh, 1000);
            } catch (error) {
                console.error('Error loading dashboard:', error);
                // Only show error on manual refresh, not auto-refresh
                if (showLoading) {
                    try {
                        // Escape error message for template literal
                        function escapeTemplateLiteral(str) {
                            if (!str) return '';
                            return String(str)
                                .split('\\\\').join('\\\\\\\\')  // Escape backslashes first
                                .split("'").join("\\\\'")
                                .split('`').join('\\\\`')
                                .split('$').join('\\\\$');
                        }
                        const errorMsg = error && error.message ? error.message : String(error);
                        content.innerHTML = `
                            <div class="empty-state">
                                <h2>Error loading dashboard</h2>
                                <p>${escapeTemplateLiteral(errorMsg)}</p>
                                <button onclick="loadDashboard(true)" style="margin-top: 20px; padding: 10px 20px; background: #667eea; color: white; border: none; border-radius: 4px; cursor: pointer;">Retry</button>
                            </div>
                        `;
                    } catch (innerError) {
                        console.error('Error rendering error message:', innerError);
                        // Fallback to simple error message
                        content.innerHTML = '<div class="empty-state"><h2>Error loading dashboard</h2><p>Please refresh the page.</p></div>';
                    }
                } else {
                    // For auto-refresh, just use empty state silently
                    allVideosData = {};
                }
            } finally {
                // Always reset refreshing flag and hide loading, even on error
                hideLoading();
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
                                    backgroundColor: 'transparent',
                                    tension: 0.1,
                                    fill: true,
                                    yAxisID: 'y',
                                    borderWidth: 3,
                                    spanGaps: false,
                                    pointRadius: 3,
                                    pointHoverRadius: 5
                                }, {
                                    label: 'Views (Expected)',
                                    data: data.expectedViewsData || [],
                                    borderColor: 'rgba(102, 126, 234, 0.8)',
                                    backgroundColor: 'transparent',
                                    borderDash: [8, 4],
                                    tension: 0.1,
                                    fill: false,
                                    yAxisID: 'y',
                                    borderWidth: 3,
                                    pointRadius: 0,
                                    order: 0
                                }, {
                                    label: 'Likes (Actual)',
                                    data: data.likesData,
                                    borderColor: 'rgba(16, 185, 129, 1)',
                                    backgroundColor: 'transparent',
                                    tension: 0.1,
                                    fill: true,
                                    yAxisID: 'y',
                                    borderWidth: 3,
                                    spanGaps: false,
                                    pointRadius: 3,
                                    pointHoverRadius: 5
                                }, {
                                    label: 'Likes (Expected)',
                                    data: data.expectedLikesData || [],
                                    borderColor: 'rgba(16, 185, 129, 0.8)',
                                    backgroundColor: 'transparent',
                                    borderDash: [8, 4],
                                    tension: 0.1,
                                    fill: false,
                                    yAxisID: 'y',
                                    borderWidth: 3,
                                    pointRadius: 0,
                                    order: 0
                                }, {
                                    label: 'Comments (Actual)',
                                    data: data.commentsData,
                                    borderColor: 'rgba(239, 68, 68, 1)',
                                    backgroundColor: 'transparent',
                                    tension: 0.1,
                                    fill: true,
                                    yAxisID: 'y1',
                                    borderWidth: 3,
                                    spanGaps: false,
                                    pointRadius: 3,
                                    pointHoverRadius: 5
                                }, {
                                    label: 'Comments (Expected)',
                                    data: data.expectedCommentsData || [],
                                    borderColor: 'rgba(239, 68, 68, 0.8)',
                                    backgroundColor: 'transparent',
                                    borderDash: [8, 4],
                                    tension: 0.1,
                                    fill: false,
                                    yAxisID: 'y1',
                                    borderWidth: 3,
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
        
        // Global lock to prevent duplicate simultaneous orders
        if (!window.placingOrders) {
            window.placingOrders = new Set();
        }
        
        // Function to place automatic orders when TIME NEXT reaches 0
        async function placeAutomaticOrder(videoUrl, metric, amount) {
            // Create unique key for this video+metric combination
            const orderKey = `${videoUrl}|${metric}`;
            
            // Check if order is already being placed
            if (window.placingOrders.has(orderKey)) {
                console.log(`[Auto Order] Order already in progress for ${orderKey}, skipping...`);
                return false;
            }
            
            // Add to lock
            window.placingOrders.add(orderKey);
            
            try {
                console.log(`[Auto Order] Placing ${amount} ${metric} for ${videoUrl}`);
                const params = new URLSearchParams();
                params.append('video_url', videoUrl);
                params.append('metric', metric);
                params.append('amount', amount);
                params.append('automatic', 'true');  // Flag to mark as automatic/scheduled order
                
                const response = await fetch('/api/manual-order', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: params.toString()
                });
                
                // Handle server errors (502, 503) without trying to parse JSON
                if (!response.ok) {
                    const statusText = response.statusText || 'Unknown error';
                    console.error(`[Auto Order] Server error ${response.status}: ${statusText}`);
                    // Remove from lock after a delay to allow retry
                    setTimeout(() => {
                        window.placingOrders.delete(orderKey);
                    }, 10000); // Wait 10 seconds before allowing retry
                    return false;
                }
                
                // Try to parse JSON, but handle empty/invalid responses
                let data;
                try {
                    const text = await response.text();
                    if (!text || text.trim() === '') {
                        console.error('[Auto Order] Empty response from server');
                        setTimeout(() => {
                            window.placingOrders.delete(orderKey);
                        }, 10000);
                        return false;
                    }
                    data = JSON.parse(text);
                } catch (parseError) {
                    console.error('[Auto Order] Failed to parse JSON response:', parseError);
                    setTimeout(() => {
                        window.placingOrders.delete(orderKey);
                    }, 10000);
                    return false;
                }
                
                if (data.success && data.order_id) {
                    console.log(`[Auto Order] Success! Order ID: ${data.order_id}, Amount: ${data.amount}`);
                    
                    // Verify order was actually saved by checking order history (with retry)
                    let verified = false;
                    for (let attempt = 0; attempt < 3; attempt++) {
                        try {
                            await new Promise(resolve => setTimeout(resolve, 1000 * (attempt + 1))); // Wait before each attempt
                            const progressResponse = await fetch('/api/progress');
                            if (!progressResponse.ok) {
                                continue; // Try again
                            }
                            const progressData = await progressResponse.json();
                            
                            if (progressData && progressData[videoUrl] && progressData[videoUrl].order_history) {
                                const recentOrder = progressData[videoUrl].order_history
                                    .filter(o => o.service === metric)
                                    .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp))[0];
                                
                                if (recentOrder && recentOrder.order_id === String(data.order_id)) {
                                    console.log(`[Auto Order] Verified! Order ${data.order_id} found in order history`);
                                    verified = true;
                                    break;
                                }
                            }
                        } catch (verifyError) {
                            console.warn(`[Auto Order] Verification attempt ${attempt + 1} failed:`, verifyError);
                        }
                    }
                    
                    if (!verified) {
                        console.warn(`[Auto Order] Could not verify order ${data.order_id} after 3 attempts, but API reported success`);
                    }
                    
                    // Remove from lock after successful order
                    setTimeout(() => {
                        window.placingOrders.delete(orderKey);
                    }, 5000); // Keep lock for 5 seconds to prevent immediate duplicate
                    
                    return true;
                } else {
                    console.error(`[Auto Order] Failed: ${data.error || 'Unknown error'}`);
                    // Remove from lock after error
                    setTimeout(() => {
                        window.placingOrders.delete(orderKey);
                    }, 30000); // Wait 30 seconds before allowing retry on error
                    return false;
                }
            } catch (error) {
                console.error('[Auto Order] Exception:', error);
                // Remove from lock after exception
                setTimeout(() => {
                    window.placingOrders.delete(orderKey);
                }, 30000); // Wait 30 seconds before allowing retry
                return false;
            }
        }
        
        // Start countdown timers for table cells (TIME LEFT, TIME NEXT, LIKES NEXT)
        function startTableCountdowns() {
            // Clear any existing intervals
            if (window.tableCountdownIntervals) {
                window.tableCountdownIntervals.forEach(interval => clearInterval(interval));
            }
            window.tableCountdownIntervals = [];
            
            // Format time with seconds
            function formatTimeWithSeconds(totalSeconds) {
                if (totalSeconds < 0) return 'OVERTIME';
                if (totalSeconds <= 0 || !isFinite(totalSeconds)) return 'N/A';
                const hours = Math.floor(totalSeconds / 3600);
                const minutes = Math.floor((totalSeconds % 3600) / 60);
                const seconds = Math.floor(totalSeconds % 60);
                if (hours > 0) {
                    return hours + 'h' + minutes + 'm' + seconds + 's';
                } else if (minutes > 0) {
                    return minutes + 'm' + seconds + 's';
                } else {
                    return seconds + 's';
                }
            }
            
            // Update TIME LEFT cells
            document.querySelectorAll('[data-time-left][data-target-time]').forEach(cell => {
                const targetTimeStr = cell.getAttribute('data-target-time');
                if (!targetTimeStr) return;
                
                const interval = setInterval(function() {
                    const now = new Date();
                    const targetTime = new Date(targetTimeStr);
                    const remainingMs = targetTime - now;
                    const remainingSeconds = Math.floor(remainingMs / 1000);
                    
                    if (remainingSeconds <= 0) {
                        cell.textContent = 'OVERTIME';
                        cell.style.color = '#ef4444';
                        clearInterval(interval);
                        return;
                    }
                    
                    cell.textContent = formatTimeWithSeconds(remainingSeconds);
                }, 1000);
                
                // Initial update
                const now = new Date();
                const targetTime = new Date(targetTimeStr);
                const remainingMs = targetTime - now;
                const remainingSeconds = Math.floor(remainingMs / 1000);
                if (remainingSeconds > 0) {
                    cell.textContent = formatTimeWithSeconds(remainingSeconds);
                } else {
                    cell.textContent = 'OVERTIME';
                    cell.style.color = '#ef4444';
                }
                
                window.tableCountdownIntervals.push(interval);
            });
            
            // Update TIME NEXT cells
            document.querySelectorAll('[data-time-next][data-target-time]').forEach(cell => {
                const targetTimeStr = cell.getAttribute('data-target-time');
                const targetViews = parseFloat(cell.getAttribute('data-target-views')) || 0;
                let avgUnits = parseFloat(cell.getAttribute('data-avg-units')) || 50;
                const videoUrl = cell.getAttribute('data-video-url');
                let orderPlaced = false; // Track if order was already placed for this countdown
                let orderPlacedTime = 0; // Track when order was placed
                let nextOrderTime = null; // Fixed time when next order should be placed
                let lastRecalcTime = Date.now(); // Track when we last recalculated
                const MIN_VIEWS_ORDER = 50; // Minimum order size for views
                
                if (!targetTimeStr || targetViews <= 0) return;
                
                // Ensure avgUnits is at least the minimum
                if (avgUnits < MIN_VIEWS_ORDER) {
                    avgUnits = MIN_VIEWS_ORDER;
                }
                
                // Function to recalculate next order time
                function recalculateNextOrderTime() {
                    // Get current real views from the DOM (updated by periodic refresh)
                    let realViews = parseFloat(cell.getAttribute('data-real-views')) || 0;
                    const realViewsCell = document.querySelector('[data-real-views][data-video-url="' + videoUrl + '"]');
                    if (realViewsCell) {
                        const cellText = realViewsCell.textContent.replace(/,/g, '');
                        realViews = parseFloat(cellText) || realViews;
                    }
                    
                    // Get updated avgUnits from DOM if available
                    const avgUnitsCell = cell.closest('tr')?.querySelector('[data-avg-units]');
                    if (avgUnitsCell) {
                        const newAvgUnits = parseFloat(avgUnitsCell.textContent.replace(/,/g, '')) || avgUnits;
                        if (newAvgUnits > 0) {
                            avgUnits = Math.max(newAvgUnits, MIN_VIEWS_ORDER); // Ensure minimum
                        }
                    } else {
                        avgUnits = MIN_VIEWS_ORDER; // Default to minimum if not found
                    }
                    
                    const now = new Date();
                    const targetTime = new Date(targetTimeStr);
                    const remainingMs = targetTime - now;
                    
                    if (remainingMs <= 0) {
                        nextOrderTime = null;
                        return;
                    }
                    
                    const viewsNeeded = Math.max(0, targetViews - realViews);
                    if (viewsNeeded <= 0) {
                        nextOrderTime = null;
                        return;
                    }
                    
                    const ordersNeeded = Math.ceil(viewsNeeded / avgUnits);
                    if (ordersNeeded > 0) {
                        // Calculate time per order and set next order time
                        const timePerOrderMs = remainingMs / ordersNeeded;
                        nextOrderTime = now.getTime() + timePerOrderMs;
                    } else {
                        nextOrderTime = null;
                    }
                    
                    lastRecalcTime = Date.now();
                }
                
                // Initial calculation
                recalculateNextOrderTime();
                
                const interval = setInterval(function() {
                    // Skip updates if we're waiting for order confirmation (within 3 seconds of placing)
                    if (orderPlaced && (Date.now() - orderPlacedTime) < 3000) {
                        return; // Keep showing PLACING... or ORDERED status
                    }
                    
                    const now = Date.now();
                    const targetTime = new Date(targetTimeStr).getTime();
                    
                    if (targetTime <= now) {
                        cell.textContent = 'OVERTIME';
                        cell.style.color = '#ef4444';
                        clearInterval(interval);
                        return;
                    }
                    
                    // Check if we need to recalculate (views might have changed)
                    let realViews = parseFloat(cell.getAttribute('data-real-views')) || 0;
                    const realViewsCell = document.querySelector('[data-real-views][data-video-url="' + videoUrl + '"]');
                    if (realViewsCell) {
                        const cellText = realViewsCell.textContent.replace(/,/g, '');
                        realViews = parseFloat(cellText) || realViews;
                    }
                    
                    const viewsNeeded = Math.max(0, targetViews - realViews);
                    if (viewsNeeded <= 0) {
                        cell.textContent = 'DONE';
                        cell.style.color = '#10b981';
                        clearInterval(interval);
                        return;
                    }
                    
                    // Only recalculate if nextOrderTime is null OR if we've passed it (should have placed order)
                    if (!nextOrderTime || (nextOrderTime && now >= nextOrderTime)) {
                        recalculateNextOrderTime();
                        // If still no nextOrderTime after recalculation, show READY
                        if (!nextOrderTime) {
                            cell.textContent = 'READY';
                            cell.style.color = '#10b981';
                            return;
                        }
                    }
                    
                    // Count down to the fixed next order time
                    const remainingMs = nextOrderTime - now;
                    const remainingSeconds = Math.max(0, Math.floor(remainingMs / 1000));
                    
                    if (remainingSeconds > 0) {
                        // Update display every second - smooth countdown
                        cell.textContent = formatTimeWithSeconds(remainingSeconds);
                        cell.style.color = '#fff';
                        orderPlaced = false; // Reset flag when time is positive
                        orderPlacedTime = 0;
                    } else {
                        // Time reached 0 - place order automatically
                        if (!orderPlaced) {
                            orderPlaced = true;
                            orderPlacedTime = Date.now();
                            cell.textContent = 'PLACING...';
                            cell.style.color = '#f59e0b';
                            
                            // Place order automatically - ensure minimum order size
                            const orderAmount = Math.max(avgUnits, MIN_VIEWS_ORDER);
                            placeAutomaticOrder(videoUrl, 'views', orderAmount).then(success => {
                                if (success) {
                                    cell.textContent = 'ORDERED ✓';
                                    cell.style.color = '#10b981';
                                    // Reset and recalculate WITHOUT reloading dashboard
                                    setTimeout(() => {
                                        orderPlaced = false;
                                        orderPlacedTime = 0;
                                        recalculateNextOrderTime();
                                        // Invalidate cache so next manual refresh gets fresh data
                                        invalidateCache();
                                    }, 5000);
                                } else {
                                    cell.textContent = 'ERROR';
                                    cell.style.color = '#ef4444';
                                    // Don't allow immediate retry - wait 30 seconds before allowing retry
                                    setTimeout(() => {
                                        orderPlaced = false;
                                        orderPlacedTime = 0;
                                        recalculateNextOrderTime();
                                    }, 30000);
                                }
                            });
                        } else {
                            // Order already placed, wait for refresh
                            if ((Date.now() - orderPlacedTime) > 5000) {
                                cell.textContent = 'READY';
                                cell.style.color = '#10b981';
                            }
                        }
                    }
                }, 1000);
                
                // Initial update
                let initialRealViews = parseFloat(cell.getAttribute('data-real-views')) || 0;
                const initialRealViewsCell = document.querySelector('[data-real-views][data-video-url="' + videoUrl + '"]');
                if (initialRealViewsCell) {
                    const cellText = initialRealViewsCell.textContent.replace(/,/g, '');
                    initialRealViews = parseFloat(cellText) || initialRealViews;
                }
                
                const now = new Date();
                const targetTime = new Date(targetTimeStr);
                const remainingMs = targetTime - now;
                const viewsNeeded = Math.max(0, targetViews - initialRealViews);
                if (viewsNeeded <= 0) {
                    cell.textContent = 'DONE';
                    cell.style.color = '#10b981';
                } else {
                    const ordersNeeded = Math.ceil(viewsNeeded / avgUnits);
                    if (ordersNeeded > 0) {
                        const timePerOrder = remainingMs / ordersNeeded;
                        const remainingSeconds = Math.floor(timePerOrder / 1000);
                        if (remainingSeconds > 0) {
                            cell.textContent = formatTimeWithSeconds(remainingSeconds);
                        } else {
                            cell.textContent = 'READY';
                            cell.style.color = '#10b981';
                        }
                    } else {
                        cell.textContent = 'READY';
                        cell.style.color = '#10b981';
                    }
                }
                
                window.tableCountdownIntervals.push(interval);
            });
            
            // Update LIKES NEXT cells
            document.querySelectorAll('[data-likes-next][data-target-time]').forEach(cell => {
                const targetTimeStr = cell.getAttribute('data-target-time');
                const targetLikes = parseFloat(cell.getAttribute('data-target-likes')) || 0;
                let avgUnits = parseFloat(cell.getAttribute('data-avg-units')) || 10;
                const videoUrl = cell.getAttribute('data-video-url');
                let orderPlaced = false; // Track if order was already placed for this countdown
                let orderPlacedTime = 0; // Track when order was placed
                let nextOrderTime = null; // Fixed time when next order should be placed
                let lastRecalcTime = Date.now(); // Track when we last recalculated
                const MIN_LIKES_ORDER = 10; // Minimum order size for likes
                
                if (!targetTimeStr || targetLikes <= 0) return;
                
                // Ensure avgUnits is at least the minimum
                if (avgUnits < MIN_LIKES_ORDER) {
                    avgUnits = MIN_LIKES_ORDER;
                }
                
                // Function to recalculate next order time
                function recalculateNextOrderTime() {
                    // Get current real likes from the DOM (updated by periodic refresh)
                    let realLikes = parseFloat(cell.getAttribute('data-real-likes')) || 0;
                    const realLikesCell = document.querySelector('[data-real-likes][data-video-url="' + videoUrl + '"]');
                    if (realLikesCell) {
                        const cellText = realLikesCell.textContent.replace(/,/g, '');
                        realLikes = parseFloat(cellText) || realLikes;
                    }
                    
                    // Get updated avgUnits from DOM if available
                    const avgUnitsCell = cell.closest('tr')?.querySelector('[data-avg-likes-units]');
                    if (avgUnitsCell) {
                        const newAvgUnits = parseFloat(avgUnitsCell.textContent.replace(/,/g, '')) || avgUnits;
                        if (newAvgUnits > 0) avgUnits = newAvgUnits;
                    }
                    
                    const now = new Date();
                    const targetTime = new Date(targetTimeStr);
                    const remainingMs = targetTime - now;
                    
                    if (remainingMs <= 0) {
                        nextOrderTime = null;
                        return;
                    }
                    
                    const likesNeeded = Math.max(0, targetLikes - realLikes);
                    if (likesNeeded <= 0) {
                        nextOrderTime = null;
                        return;
                    }
                    
                    const ordersNeeded = Math.ceil(likesNeeded / avgUnits);
                    if (ordersNeeded > 0) {
                        // Calculate time per order and set next order time
                        const timePerOrderMs = remainingMs / ordersNeeded;
                        nextOrderTime = now.getTime() + timePerOrderMs;
                    } else {
                        nextOrderTime = null;
                    }
                    
                    lastRecalcTime = Date.now();
                }
                
                // Initial calculation
                recalculateNextOrderTime();
                
                const interval = setInterval(function() {
                    // Skip updates if we're waiting for order confirmation (within 3 seconds of placing)
                    if (orderPlaced && (Date.now() - orderPlacedTime) < 3000) {
                        return; // Keep showing PLACING... or ORDERED status
                    }
                    
                    const now = Date.now();
                    const targetTime = new Date(targetTimeStr).getTime();
                    
                    if (targetTime <= now) {
                        cell.textContent = 'OVERTIME';
                        cell.style.color = '#ef4444';
                        clearInterval(interval);
                        return;
                    }
                    
                    // Check if we need to recalculate (likes might have changed)
                    let realLikes = parseFloat(cell.getAttribute('data-real-likes')) || 0;
                    const realLikesCell = document.querySelector('[data-real-likes][data-video-url="' + videoUrl + '"]');
                    if (realLikesCell) {
                        const cellText = realLikesCell.textContent.replace(/,/g, '');
                        realLikes = parseFloat(cellText) || realLikes;
                    }
                    
                    const likesNeeded = Math.max(0, targetLikes - realLikes);
                    if (likesNeeded <= 0) {
                        cell.textContent = 'DONE';
                        cell.style.color = '#10b981';
                        clearInterval(interval);
                        return;
                    }
                    
                    // Only recalculate if nextOrderTime is null OR if we've passed it (should have placed order)
                    if (!nextOrderTime || (nextOrderTime && now >= nextOrderTime)) {
                        recalculateNextOrderTime();
                        // If still no nextOrderTime after recalculation, show READY
                        if (!nextOrderTime) {
                            cell.textContent = 'READY';
                            cell.style.color = '#10b981';
                            return;
                        }
                    }
                    
                    // Count down to the fixed next order time
                    const remainingMs = nextOrderTime - now;
                    const remainingSeconds = Math.max(0, Math.floor(remainingMs / 1000));
                    
                    if (remainingSeconds > 0) {
                        // Update display every second - smooth countdown
                        cell.textContent = formatTimeWithSeconds(remainingSeconds);
                        cell.style.color = '#fff';
                        orderPlaced = false; // Reset flag when time is positive
                        orderPlacedTime = 0;
                    } else {
                        // Time reached 0 - place order automatically
                        if (!orderPlaced) {
                            orderPlaced = true;
                            orderPlacedTime = Date.now();
                            cell.textContent = 'PLACING...';
                            cell.style.color = '#f59e0b';
                            
                            // Place order automatically - ensure minimum order size
                            const orderAmount = Math.max(avgUnits, MIN_LIKES_ORDER);
                            placeAutomaticOrder(videoUrl, 'likes', orderAmount).then(success => {
                                if (success) {
                                    cell.textContent = 'ORDERED ✓';
                                    cell.style.color = '#10b981';
                                    // Reset and recalculate WITHOUT reloading dashboard
                                    setTimeout(() => {
                                        orderPlaced = false;
                                        orderPlacedTime = 0;
                                        recalculateNextOrderTime();
                                        // Invalidate cache so next manual refresh gets fresh data
                                        invalidateCache();
                                    }, 5000);
                                } else {
                                    cell.textContent = 'ERROR';
                                    cell.style.color = '#ef4444';
                                    // Don't allow immediate retry - wait 30 seconds before allowing retry
                                    setTimeout(() => {
                                        orderPlaced = false;
                                        orderPlacedTime = 0;
                                        recalculateNextOrderTime();
                                    }, 30000);
                                }
                            });
                        } else {
                            // Order already placed, wait for refresh
                            if ((Date.now() - orderPlacedTime) > 5000) {
                                cell.textContent = 'READY';
                                cell.style.color = '#10b981';
                            }
                        }
                    }
                }, 1000);
                
                // Initial update
                let initialRealLikes = parseFloat(cell.getAttribute('data-real-likes')) || 0;
                const initialRealLikesCell = document.querySelector('[data-real-likes][data-video-url="' + videoUrl + '"]');
                if (initialRealLikesCell) {
                    const cellText = initialRealLikesCell.textContent.replace(/,/g, '');
                    initialRealLikes = parseFloat(cellText) || initialRealLikes;
                }
                
                const now = new Date();
                const targetTime = new Date(targetTimeStr);
                const remainingMs = targetTime - now;
                const likesNeeded = Math.max(0, targetLikes - initialRealLikes);
                if (likesNeeded <= 0) {
                    cell.textContent = 'DONE';
                    cell.style.color = '#10b981';
                } else {
                    const ordersNeeded = Math.ceil(likesNeeded / avgUnits);
                    if (ordersNeeded > 0) {
                        const timePerOrder = remainingMs / ordersNeeded;
                        const remainingSeconds = Math.floor(timePerOrder / 1000);
                        if (remainingSeconds > 0) {
                            cell.textContent = formatTimeWithSeconds(remainingSeconds);
                        } else {
                            cell.textContent = 'READY';
                            cell.style.color = '#10b981';
                        }
                    } else {
                        cell.textContent = 'READY';
                        cell.style.color = '#10b981';
                    }
                }
                
                window.tableCountdownIntervals.push(interval);
            });
        }
        
        // Refresh table data periodically - UPDATE ONLY, don't rebuild HTML
        function startTableDataRefresh() {
            // Clear any existing interval
            if (window.tableDataRefreshInterval) {
                clearInterval(window.tableDataRefreshInterval);
            }
            
            window.tableDataRefreshInterval = setInterval(function() {
                const route = getCurrentRoute();
                if (route.type === 'home' || route.type === 'campaign') {
                    // Silently fetch fresh data and update cache WITHOUT rebuilding UI
                    fetch('/api/progress')
                        .then(response => response.json())
                        .then(data => {
                            cachedProgressData = data;
                            lastProgressFetch = Date.now();
                            console.log('[Silent Refresh] Cache updated, timers continue running');
                        })
                        .catch(error => {
                            console.error('[Silent Refresh] Error:', error);
                        });
                }
            }, 120000); // Every 2 minutes - timers run independently
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
                            // Check if we need to switch tabs first
                            const switchTo = btn.getAttribute('data-switch-to');
                            if (switchTo && typeof switchTab === 'function') {
                                switchTab(switchTo);
                            } else {
                                // Check if we're in a campaign view
                                const route = getCurrentRoute();
                                if (route.type === 'campaign') {
                                    // Switch to campaigns tab first
                                    if (typeof switchTab === 'function') {
                                        switchTab('campaigns');
                                    }
                                }
                            }
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
        
        // Listen for hash changes (back/forward browser buttons) - INSTANT navigation
        window.addEventListener('hashchange', () => {
            console.log('Hash changed to:', window.location.hash);
            // Use cached data for instant navigation, no forced refresh
            loadDashboard(false, false);
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
        
        // Background cache update - timers run independently, no UI rebuilds
        setInterval(() => {
            if (shouldPauseAutoRefresh()) return;
            // Silently update cache without rebuilding UI or resetting timers
            fetch('/api/progress')
                .then(response => response.json())
                .then(data => {
                    cachedProgressData = data;
                    lastProgressFetch = Date.now();
                    console.log('[Background Update] Cache refreshed, timers unaffected');
                })
                .catch(error => console.error('[Background Update] Error:', error));
        }, 180000); // 3 minutes - timers are completely independent
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

