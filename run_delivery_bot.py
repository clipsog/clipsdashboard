#!/usr/bin/env python3
"""
Main bot to run delivery plan for multiple videos
Integrates with monitoring system
"""

import requests
import json
import time
import sys
import re
from datetime import datetime, timedelta
from pathlib import Path
from colorama import Fore, Style, init
from bs4 import BeautifulSoup

init(autoreset=True)

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

class DeliveryBot:
    def __init__(self, video_url):
        self.video_url = video_url
        self.progress_file = Path.home() / '.smmfollows_bot' / 'progress.json'
        self.orders_file = Path.home() / '.smmfollows_bot' / 'orders.json'
        self.progress_file.parent.mkdir(exist_ok=True)
    
    def log_activity(self, message, level='info'):
        """Log activity for this video"""
        progress = self.load_progress()
        if self.video_url not in progress:
            return
        
        if 'activity_log' not in progress[self.video_url]:
            progress[self.video_url]['activity_log'] = []
        
        timestamp = datetime.now().isoformat()
        log_entry = {
            'timestamp': timestamp,
            'message': message,
            'level': level  # info, success, warning, error
        }
        
        # Keep only last 50 log entries
        progress[self.video_url]['activity_log'].append(log_entry)
        if len(progress[self.video_url]['activity_log']) > 50:
            progress[self.video_url]['activity_log'] = progress[self.video_url]['activity_log'][-50:]
        
        self.save_progress(progress)
        
    def load_progress(self):
        """Load progress for this video"""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_progress(self, progress):
        """Save progress"""
        try:
            with open(self.progress_file, 'w') as f:
                json.dump(progress, f, indent=2)
        except Exception as e:
            print(f"{Fore.RED}Error saving progress: {e}{Style.RESET_ALL}")
    
    def fetch_all_analytics(self):
        """Fetch ALL real-time analytics: views, likes, comments - BEFORE every action"""
        # Only print if called from initial fetch (not during loop)
        print_analytics = not hasattr(self, '_analytics_fetch_quiet')
        if print_analytics:
            print(f"{Fore.CYAN}📊 Fetching real-time analytics...{Style.RESET_ALL}")
        
        analytics = {'views': 0, 'likes': 0, 'comments': 0}
        
        # Method 1: Try direct TikTok scraping (most accurate for current state)
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            response = requests.get(self.video_url, headers=headers, timeout=20, allow_redirects=True)
            if response.status_code == 200:
                html = response.text
                
                # Look for JSON data in script tags - try multiple patterns
                patterns = [
                    r'<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__"[^>]*>(.*?)</script>',
                    r'<script[^>]*>window\.__UNIVERSAL_DATA_FOR_REHYDRATION__\s*=\s*({.*?});</script>',
                    r'<script[^>]*>__UNIVERSAL_DATA_FOR_REHYDRATION__\s*=\s*({.*?});</script>',
                ]
                
                for pattern in patterns:
                    script_match = re.search(pattern, html, re.DOTALL)
                    if script_match:
                        try:
                            json_str = script_match.group(1)
                            # Clean up if needed
                            if json_str.startswith('{'):
                                data = json.loads(json_str)
                                
                                # Try multiple navigation paths
                                paths = [
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
                                            # Successfully navigated path
                                            views = int(item.get('playCount', 0) or item.get('viewCount', 0) or item.get('play_count', 0) or 0)
                                            likes = int(item.get('diggCount', 0) or item.get('likeCount', 0) or item.get('digg_count', 0) or 0)
                                            comments = int(item.get('commentCount', 0) or item.get('comment_count', 0) or 0)
                                            
                                            if views > 0 or likes > 0:
                                                analytics['views'] = views
                                                analytics['likes'] = likes
                                                analytics['comments'] = comments
                                                if print_analytics:
                                                    print(f"  {Fore.GREEN}✓ Found: {analytics['views']:,} views, {analytics['likes']:,} likes, {analytics['comments']:,} comments{Style.RESET_ALL}")
                                                return analytics
                                    except:
                                        continue
                        except Exception as e:
                            continue
                
                # Alternative: Try to find in meta tags or other places
                soup = BeautifulSoup(html, 'html.parser')
                # Look for og:description which sometimes has view counts
                meta_desc = soup.find('meta', {'property': 'og:description'})
                if meta_desc:
                    desc = meta_desc.get('content', '')
                    # Try to extract numbers (less reliable)
                    views_match = re.search(r'([\d,]+)\s*views?', desc, re.I)
                    if views_match:
                        views_str = views_match.group(1).replace(',', '')
                        if views_str.isdigit():
                            analytics['views'] = int(views_str)
                            if print_analytics and analytics['views'] > 0:
                                print(f"  {Fore.GREEN}✓ Found from meta: {analytics['views']:,} views{Style.RESET_ALL}")
                                return analytics
        except Exception as e:
            if print_analytics:
                pass  # Silent fail, try next method
        
        # Method 2: Try TikTok API endpoint
        try:
            video_id_match = re.search(r'tiktok\.com/@[^/]+/video/(\d+)', self.video_url)
            if video_id_match:
                video_id = video_id_match.group(1)
                api_url = f"https://www.tiktok.com/api/post/item_list/?aid=1988&app_name=tiktok_web&device_platform=web&device_id=&region=US&count=1&itemID={video_id}"
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Referer': self.video_url,
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
                            if print_analytics:
                                print(f"  {Fore.GREEN}✓ Found via API: {analytics['views']:,} views, {analytics['likes']:,} likes, {analytics['comments']:,} comments{Style.RESET_ALL}")
                            return analytics
        except:
            pass
        
        # Method 3: Try trollishly.com API
        try:
            video_id_match = re.search(r'tiktok\.com/@[^/]+/video/(\d+)', self.video_url)
            if video_id_match:
                video_id = video_id_match.group(1)
                csrf_url = "https://www.trollishly.com/tiktok-counter/"
                response = requests.get(csrf_url, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    csrf_token = soup.find('meta', {'name': 'csrf-token'})
                    if csrf_token:
                        csrf_token = csrf_token.get('content')
                        api_url = "https://www.trollishly.com/nocache/search_tiktok_user_counter_val/"
                        payload = {'username': video_id}
                        headers = {
                            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                            'Accept': 'application/json',
                            'Content-Type': 'application/x-www-form-urlencoded',
                            'Referer': 'https://www.trollishly.com/tiktok-counter/',
                            'X-CSRF-Token': csrf_token,
                            'X-Requested-With': 'XMLHttpRequest'
                        }
                        response = requests.post(api_url, data=payload, headers=headers, cookies=response.cookies, timeout=10)
                        if response.status_code == 200:
                            data = response.json()
                            if 'error' not in data and ('video_views_count' in data or 'video_likes_count' in data):
                                analytics['views'] = int(data.get('video_views_count', 0) or 0)
                                analytics['likes'] = int(data.get('video_likes_count', 0) or 0)
                                # Note: trollishly doesn't provide comment count
                                if analytics['views'] > 0 or analytics['likes'] > 0:
                                    if print_analytics:
                                        print(f"  {Fore.GREEN}✓ Found via trollishly: {analytics['views']:,} views, {analytics['likes']:,} likes{Style.RESET_ALL}")
                                    return analytics
        except:
            pass
        
        if print_analytics:
            print(f"  {Fore.YELLOW}⚠ Could not fetch analytics (will use 0 as baseline){Style.RESET_ALL}")
        return analytics
    
    def load_comments(self):
        """Load comments from config file"""
        comments_file = Path.home() / '.smmfollows_bot' / 'comments.txt'
        if comments_file.exists():
            try:
                with open(comments_file, 'r', encoding='utf-8') as f:
                    comments = [line.strip() for line in f.readlines() if line.strip()]
                return comments
            except Exception as e:
                print(f"  {Fore.YELLOW}⚠ Could not load comments: {e}{Style.RESET_ALL}")
        return []
    
    def create_order(self, service_id, quantity, service_name, comments_text=None, username=None):
        """Create an order"""
        try:
            # All services use 'add' action (tested and confirmed)
            # Build order data
            # For comment likes, link format MUST be: video_url|username
            link = self.video_url
            if service_id == SERVICES['comment_likes']:
                if username:
                    # Format: https://www.tiktok.com/@user/video/123|username
                    link = f"{self.video_url}|{username}"
                else:
                    # Username is required for comment likes
                    print(f"  {Fore.RED}✗ Error: Username is required for comment likes{Style.RESET_ALL}")
                    return False, None
            
            order_data = {
                'key': API_KEY,
                'action': 'add',  # All services use 'add', not 'order'
                'service': service_id,
                'link': link,  # Use formatted link with username for comment likes
                'quantity': quantity
            }
            
            # Add comments text if this is a comments order and we have comments
            if service_id == SERVICES['comments'] and comments_text:
                # Try different parameter names (common in SMM APIs)
                # Most SMM panels use 'comments' or 'comment' parameter
                order_data['comments'] = comments_text
            
            response = requests.post(
                BASE_URL,
                data=order_data,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                order_id = data.get('order', 0)
                if order_id and order_id != 0:
                    return True, order_id
                else:
                    error = data.get('error', 'Unknown error')
                    print(f"  {Fore.RED}✗ Error: {error}{Style.RESET_ALL}")
                    if 'active order' in error.lower():
                        print(f"  {Fore.YELLOW}⚠ There's already an active order for this video{Style.RESET_ALL}")
                        print(f"  {Fore.CYAN}The bot will continue - order will be processed{Style.RESET_ALL}")
                    return False, None
            else:
                print(f"  {Fore.RED}✗ HTTP {response.status_code}: {response.text[:200]}{Style.RESET_ALL}")
                return False, None
        except Exception as e:
            print(f"  {Fore.RED}✗ Error: {e}{Style.RESET_ALL}")
            return False, None
    
    def update_progress(self, service_type, quantity, order_id):
        """Update progress after placing order"""
        progress = self.load_progress()
        
        if self.video_url not in progress:
            progress[self.video_url] = {
                'start_time': datetime.now().isoformat(),
                'target_views': 4000,
                'target_likes': 125,
                'target_comments': 7,
                'target_comment_likes': 15,
                'orders_placed': {'views': 0, 'likes': 0, 'comments': 0, 'comment_likes': 0},
                'order_history': [],
                'next_orders': [],
                'total_cost': 0
            }
        
        video_progress = progress[self.video_url]
        
        # Update orders placed
        if service_type in video_progress['orders_placed']:
            video_progress['orders_placed'][service_type] += quantity
        
        # Add to history
        video_progress['order_history'].append({
            'timestamp': datetime.now().isoformat(),
            'service': service_type,
            'quantity': quantity,
            'order_id': order_id
        })
        
        # Calculate cost
        rates = {'views': 0.0140, 'likes': 0.2100, 'comments': 13.5000, 'comment_likes': 0.2100}
        cost = (quantity / 1000.0) * rates.get(service_type, 0)
        video_progress['total_cost'] += cost
        
        self.save_progress(progress)
    
    def calculate_adjusted_schedule(self, purchases, target_completion_time, start_time):
        """Calculate adjusted schedule based on target completion time"""
        if not target_completion_time:
            return purchases  # Use original schedule if no target time set
        
        try:
            target_dt = datetime.fromisoformat(target_completion_time)
            total_time_available = (target_dt - start_time).total_seconds()
            
            if total_time_available <= 0:
                print(f"{Fore.YELLOW}⚠ Target time is in the past. Using original schedule.{Style.RESET_ALL}")
                return purchases
            
            # Get total time from original schedule
            original_total_time = max([p.get('time_seconds', 0) for p in purchases], default=24*3600)
            
            # Calculate time compression factor
            time_factor = total_time_available / original_total_time
            
            # Adjust all purchase times
            adjusted_purchases = []
            for purchase in purchases:
                adjusted_purchase = purchase.copy()
                original_time = purchase.get('time_seconds', 0)
                adjusted_time = original_time * time_factor
                adjusted_purchase['time_seconds'] = adjusted_time
                
                # Update time string
                hours = int(adjusted_time // 3600)
                minutes = int((adjusted_time % 3600) // 60)
                adjusted_purchase['time_str'] = f"{hours}h {minutes}m"
                
                adjusted_purchases.append(adjusted_purchase)
            
            print(f"{Fore.CYAN}📅 Schedule adjusted for target completion time{Style.RESET_ALL}")
            print(f"  Original duration: {original_total_time/3600:.1f} hours")
            print(f"  Target duration: {total_time_available/3600:.1f} hours")
            print(f"  Compression factor: {time_factor:.2f}x\n")
            
            return adjusted_purchases
        except Exception as e:
            print(f"{Fore.YELLOW}⚠ Error adjusting schedule: {e}. Using original schedule.{Style.RESET_ALL}")
            return purchases
    
    def run_delivery_plan(self):
        """Run the full delivery plan"""
        # Load purchase schedule
        schedule_file = Path(__file__).parent / 'purchase_schedule.json'
        if not schedule_file.exists():
            print(f"{Fore.RED}Error: purchase_schedule.json not found{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Run create_delivery_timeline.py first{Style.RESET_ALL}")
            return
        
        with open(schedule_file, 'r') as f:
            purchases = json.load(f)
        
        print(f"""
    {Fore.CYAN}╔══════════════════════════════════════════════╗
    ║   Starting Delivery Bot                 ║
    ╚══════════════════════════════════════════════╝{Style.RESET_ALL}
    """)
        
        print(f"Video: {self.video_url}")
        print(f"Total purchases: {len(purchases)}")
        print(f"{Fore.YELLOW}Press Ctrl+C to stop (progress will be saved){Style.RESET_ALL}\n")
        
        # Log bot start
        self.log_activity("🚀 Delivery bot started", 'info')
        self.log_activity(f"Total purchases scheduled: {len(purchases)}", 'info')
        
        # Check for target completion time and adjust schedule
        progress = self.load_progress()
        if self.video_url in progress:
            target_completion_time = progress[self.video_url].get('target_completion_time') or progress[self.video_url].get('target_completion_datetime')
            if target_completion_time:
                start_time = datetime.now()
                purchases = self.calculate_adjusted_schedule(purchases, target_completion_time, start_time)
        
        # CRITICAL: Fetch current analytics BEFORE placing any orders
        print(f"{Fore.CYAN}Fetching current video analytics (BEFORE ordering)...{Style.RESET_ALL}")
        
        progress = self.load_progress()
        
        # ALWAYS use fetch_all_analytics() first (tries multiple methods to get REAL views)
        real_analytics = self.fetch_all_analytics()
        initial_views = real_analytics.get('views', 0)
        initial_likes = real_analytics.get('likes', 0)
        initial_comments = real_analytics.get('comments', 0)
        
        # If fetch_all_analytics failed, try fallback: check order history
        if initial_views == 0:
            # Method 1: Check existing orders for this video to get latest start_count
            if self.video_url in progress:
                video_progress = progress[self.video_url]
                order_history = video_progress.get('order_history', [])
            
            if order_history:
                print(f"  Checking {len(order_history)} existing order(s)...")
                # Check all orders, use the highest start_count (most recent)
                max_views = 0
                for order in order_history:
                    order_id = order.get('order_id')
                    if order_id:
                        try:
                            response = requests.post(
                                BASE_URL,
                                data={'key': API_KEY, 'action': 'status', 'order': order_id},
                                timeout=10
                            )
                            if response.status_code == 200:
                                data = response.json()
                                start_count = data.get('start_count', '')
                                if start_count and start_count.isdigit():
                                    views = int(start_count)
                                    if views > max_views:
                                        max_views = views
                        except:
                            continue
                
                if max_views > 0:
                    initial_views = max_views
                    print(f"  {Fore.GREEN}✓ Found from order history: {initial_views:,} views{Style.RESET_ALL}")
                    print(f"  {Fore.CYAN}(This is the count when the latest order was placed){Style.RESET_ALL}")
        
        # Method 2: If no orders exist, place a tiny test order to get current count
        if initial_views == 0:
            print(f"  No existing orders found. Placing test order to get current count...")
            try:
                response = requests.post(
                    BASE_URL,
                    data={
                        'key': API_KEY,
                        'action': 'add',
                        'service': SERVICES['views'],
                        'link': self.video_url,
                        'quantity': MINIMUMS['views']
                    },
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    order_id = data.get('order', 0)
                    if order_id and order_id != 0:
                        print(f"  {Fore.CYAN}Test order placed: {order_id}{Style.RESET_ALL}")
                        print(f"  Waiting for order to process...")
                        time.sleep(3)  # Wait for order to be processed
                        
                        # Get order status
                        status_response = requests.post(
                            BASE_URL,
                            data={'key': API_KEY, 'action': 'status', 'order': order_id},
                            timeout=10
                        )
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            start_count = status_data.get('start_count', '')
                            if start_count and start_count.isdigit():
                                initial_views = int(start_count)
                                print(f"  {Fore.GREEN}✓ Current: {initial_views:,} views{Style.RESET_ALL}")
                                
                                # Save this test order to history
                                if self.video_url not in progress:
                                    progress[self.video_url] = {
                                        'start_time': datetime.now().isoformat(),
                                        'target_views': 4000,
                                        'target_likes': 125,
                                        'target_comments': 7,
                                        'target_comment_likes': 15,
                                        'orders_placed': {'views': 0, 'likes': 0, 'comments': 0, 'comment_likes': 0},
                                        'order_history': [],
                                        'total_cost': 0
                                    }
                                if 'order_history' not in progress[self.video_url]:
                                    progress[self.video_url]['order_history'] = []
                                
                                progress[self.video_url]['order_history'].append({
                                    'timestamp': datetime.now().isoformat(),
                                    'service': 'views',
                                    'quantity': MINIMUMS['views'],
                                    'order_id': order_id
                                })
                                progress[self.video_url]['orders_placed'] = progress[self.video_url].get('orders_placed', {'views': 0, 'likes': 0, 'comments': 0, 'comment_likes': 0})
                                progress[self.video_url]['orders_placed']['views'] = MINIMUMS['views']
                                self.save_progress(progress)
                            else:
                                print(f"  {Fore.YELLOW}⚠ Could not get count from test order{Style.RESET_ALL}")
                        else:
                            print(f"  {Fore.YELLOW}⚠ Could not check test order status{Style.RESET_ALL}")
                    else:
                        error = data.get('error', '')
                        if 'active order' in error.lower():
                            print(f"  {Fore.YELLOW}⚠ Active order exists - will use that order's count{Style.RESET_ALL}")
                            # Try to get count from active order
                            # This is tricky - we'd need to list all orders
                        else:
                            print(f"  {Fore.YELLOW}⚠ Could not place test order: {error}{Style.RESET_ALL}")
            except Exception as e:
                print(f"  {Fore.YELLOW}⚠ Error: {e}{Style.RESET_ALL}")
        
        # Save initial values
        if self.video_url not in progress:
            progress[self.video_url] = {
                'start_time': datetime.now().isoformat(),
                'target_views': 4000,
                'target_likes': 125,
                'target_comments': 7,
                'target_comment_likes': 15,
                'initial_views': initial_views,
                'initial_likes': initial_likes,
                'orders_placed': {'views': 0, 'likes': 0, 'comments': 0, 'comment_likes': 0},
                'order_history': [],
                'next_orders': [],
                'total_cost': 0
            }
        else:
            # Always update initial_views with latest count
            progress[self.video_url]['initial_views'] = initial_views
            progress[self.video_url]['initial_likes'] = initial_likes
        
        self.save_progress(progress)
        
        if initial_views > 0 or initial_likes > 0:
            print(f"\n{Fore.GREEN}✓ Analytics fetched: {initial_views:,} views, {initial_likes:,} likes, {initial_comments} comments{Style.RESET_ALL}")
            print(f"{Fore.CYAN}Bot will track: {initial_views:,} existing + ordered = total{Style.RESET_ALL}\n")
        else:
            print(f"\n{Fore.YELLOW}⚠ Could not fetch current analytics{Style.RESET_ALL}")
            print(f"{Fore.CYAN}Bot will track orders only. Will keep trying to fetch real analytics.{Style.RESET_ALL}\n")
        
        # Set initial values for use in the loop
        initial_views = progress[self.video_url].get('initial_views', 0)
        initial_likes = progress[self.video_url].get('initial_likes', 0)
        
        # Check if comments/comment likes were already ordered
        orders_placed = progress[self.video_url].get('orders_placed', {'views': 0, 'likes': 0, 'comments': 0, 'comment_likes': 0})
        comments_ordered = orders_placed.get('comments', 0) > 0
        comment_likes_ordered = orders_placed.get('comment_likes', 0) > 0
        
        start_time = datetime.now()
        
        # Milestone tracking (based on TOTAL views: existing + ordered)
        comments_milestone = 2000  # Order comments at 2k TOTAL views
        comment_likes_milestone = 2600  # Order comment likes at 2.6k TOTAL views
        
        # Check if we're already past milestones (existing views alone)
        total_current_views = initial_views + orders_placed.get('views', 0)
        
        print(f"{Fore.CYAN}Milestone-based ordering:{Style.RESET_ALL}")
        print(f"  Comments milestone: {comments_milestone:,} TOTAL views (existing + ordered)")
        print(f"  Comment likes milestone: {comment_likes_milestone:,} TOTAL views")
        print(f"  Current total: {total_current_views:,} views ({initial_views:,} existing + {orders_placed.get('views', 0)} ordered)\n")
        
        # PREPARE COMMENTS IN ADVANCE (before milestone is reached)
        # This way when milestone is reached, comments can be ordered automatically
        saved_comments = progress[self.video_url].get('saved_comments', [])
        if not comments_ordered and len(saved_comments) < MINIMUMS['comments']:
            print(f"{Fore.YELLOW}{'='*60}")
            print(f"{Fore.GREEN}📝 PREPARING COMMENTS IN ADVANCE")
            print(f"{Fore.YELLOW}{'='*60}{Style.RESET_ALL}")
            print(f"\n{Fore.CYAN}To ensure smooth ordering when the milestone is reached,{Style.RESET_ALL}")
            print(f"{Fore.CYAN}please provide {MINIMUMS['comments']} comments now.{Style.RESET_ALL}")
            print(f"{Fore.CYAN}These will be saved and used automatically when views reach {comments_milestone:,}.{Style.RESET_ALL}\n")
            
            comments_list = []
            while len(comments_list) < MINIMUMS['comments']:
                try:
                    comment_num = len(comments_list) + 1
                    comment = input(f"{Fore.CYAN}Comment {comment_num}/{MINIMUMS['comments']}: {Style.RESET_ALL}").strip()
                    if comment:
                        comments_list.append(comment)
                    else:
                        print(f"  {Fore.RED}Empty comment not allowed. Please enter a comment.{Style.RESET_ALL}")
                except (EOFError, KeyboardInterrupt):
                    print(f"\n{Fore.RED}Input cancelled.{Style.RESET_ALL}")
                    print(f"{Fore.YELLOW}Comments not saved. Bot will prompt again at milestone.{Style.RESET_ALL}")
                    break
            
            if len(comments_list) == MINIMUMS['comments']:
                # Save comments to progress
                progress[self.video_url]['saved_comments'] = comments_list
                self.save_progress(progress)
                
                print(f"\n{Fore.GREEN}✓ Comments saved successfully!{Style.RESET_ALL}")
                print(f"{Fore.CYAN}Comments to be used:{Style.RESET_ALL}")
                for i, comment in enumerate(comments_list, 1):
                    print(f"  {i}. {comment}")
                print(f"\n{Fore.CYAN}These will be ordered automatically when views reach {comments_milestone:,}.{Style.RESET_ALL}\n")
            else:
                print(f"\n{Fore.YELLOW}⚠ Not enough comments saved. Bot will prompt again at milestone.{Style.RESET_ALL}\n")
        
        # If already past milestones and not ordered yet, check current comments and order if needed
        if total_current_views >= comments_milestone and not comments_ordered:
            print(f"\n{Fore.CYAN}{'='*60}")
            print(f"{Fore.GREEN}🎯 MILESTONE REACHED: {total_current_views:,} TOTAL views")
            print(f"{Fore.CYAN}({initial_views:,} existing + {orders_placed.get('views', 0)} ordered)")
            print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            
            # Fetch REAL-TIME analytics to check current comments
            print(f"\n{Fore.CYAN}Checking current comment count on video...{Style.RESET_ALL}")
            real_analytics = self.fetch_all_analytics()
            current_comments = real_analytics.get('comments', 0)
            target_comments = progress[self.video_url].get('target_comments', 7)
            comments_ordered_count = orders_placed.get('comments', 0)
            
            # Only count ACTUAL comments on video, not ordered ones (they take time to deliver)
            actual_comments_on_video = current_comments
            
            print(f"  Current comments on video: {actual_comments_on_video}")
            print(f"  Comments ordered (pending delivery): {comments_ordered_count}")
            print(f"  Target: {target_comments}")
            
            # Only skip if we have enough ACTUAL comments on the video
            if actual_comments_on_video >= target_comments:
                print(f"\n  {Fore.GREEN}✓ Already have enough comments on video ({actual_comments_on_video} >= {target_comments}){Style.RESET_ALL}")
                print(f"  {Fore.CYAN}Skipping comment order.{Style.RESET_ALL}")
                comments_ordered = True
            else:
                needed = target_comments - actual_comments_on_video
                print(f"\n  {Fore.YELLOW}Need {needed} more comments (have {actual_comments_on_video} actual, target {target_comments}){Style.RESET_ALL}")
                print(f"  {Fore.CYAN}Note: {comments_ordered_count} comments are ordered but not yet delivered{Style.RESET_ALL}")
                print(f"  {Fore.CYAN}Minimum order: {MINIMUMS['comments']} comments{Style.RESET_ALL}")
            
            # Only order if we don't have enough ACTUAL comments
            if not comments_ordered:
                print(f"\n{Fore.YELLOW}It's time to order comments!{Style.RESET_ALL}")
                print(f"{Fore.CYAN}Video: {self.video_url}{Style.RESET_ALL}")
                print(f"\n{Fore.YELLOW}Please enter exactly {MINIMUMS['comments']} comments (one per line):{Style.RESET_ALL}")
                print(f"{Fore.CYAN}You MUST enter {MINIMUMS['comments']} comments - this is the minimum order.{Style.RESET_ALL}")
                print(f"{Fore.CYAN}Press Enter after each comment.{Style.RESET_ALL}\n")
                
                comments_list = []
                while len(comments_list) < MINIMUMS['comments']:
                    try:
                        comment_num = len(comments_list) + 1
                        comment = input(f"{Fore.CYAN}Comment {comment_num}/{MINIMUMS['comments']}: {Style.RESET_ALL}").strip()
                        if comment:
                            comments_list.append(comment)
                        else:
                            print(f"  {Fore.RED}Empty comment not allowed. Please enter a comment.{Style.RESET_ALL}")
                    except (EOFError, KeyboardInterrupt):
                        print(f"\n{Fore.RED}Input cancelled.{Style.RESET_ALL}")
                        print(f"{Fore.YELLOW}Need {MINIMUMS['comments']} comments minimum. Order cancelled.{Style.RESET_ALL}")
                        comments_ordered = True  # Mark as attempted to avoid retrying
                        break
                
                if len(comments_list) == MINIMUMS['comments']:
                    comments_text = '\n'.join(comments_list)
                    
                    print(f"\n{Fore.CYAN}Comments to be posted:{Style.RESET_ALL}")
                    for i, comment in enumerate(comments_list, 1):
                        print(f"  {i}. {comment}")
                    
                    # Update activity status - ordering comments
                    progress = self.load_progress()
                    if self.video_url in progress:
                        progress[self.video_url]['current_activity'] = {
                            'status': 'ordering',
                            'action': f"Ordering {MINIMUMS['comments']} comments",
                            'service': 'Comments',
                            'quantity': MINIMUMS['comments'],
                            'last_updated': datetime.now().isoformat()
                        }
                        self.save_progress(progress)
                    
                    print(f"\n{Fore.YELLOW}Ordering {MINIMUMS['comments']} comments...{Style.RESET_ALL}")
                    success_comments, order_id_comments = self.create_order(
                        SERVICES['comments'], MINIMUMS['comments'], 'Comments', comments_text
                    )
                    if success_comments:
                        print(f"  {Fore.GREEN}✓ Comments ordered! ID: {order_id_comments}{Style.RESET_ALL}")
                        self.update_progress('comments', MINIMUMS['comments'], order_id_comments)
                        comments_ordered = True
                        
                        # Save comments for reference
                        comments_file = Path.home() / '.smmfollows_bot' / 'comments.txt'
                        try:
                            with open(comments_file, 'w', encoding='utf-8') as f:
                                f.write('\n'.join(comments_list))
                            print(f"  {Fore.CYAN}✓ Comments saved{Style.RESET_ALL}")
                        except:
                            pass
                    else:
                        print(f"  {Fore.RED}✗ Failed to order comments{Style.RESET_ALL}")
                        comments_ordered = True
            
            print(f"\n{Fore.CYAN}Continuing with delivery plan...{Style.RESET_ALL}\n")
        
        if total_current_views >= comment_likes_milestone and not comment_likes_ordered:
            print(f"\n{Fore.CYAN}{'='*60}")
            print(f"{Fore.GREEN}🎯 MILESTONE REACHED: {total_current_views:,} TOTAL views")
            print(f"{Fore.CYAN}({initial_views:,} existing + {orders_placed.get('views', 0)} ordered)")
            print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
            
            # Fetch REAL-TIME analytics to check if comments exist
            print(f"\n{Fore.CYAN}Checking if comments exist on video...{Style.RESET_ALL}")
            real_analytics = self.fetch_all_analytics()
            current_comments = real_analytics.get('comments', 0)
            comments_ordered_count = orders_placed.get('comments', 0)
            
            # Only check ACTUAL comments on video (not ordered ones - they take time to deliver)
            actual_comments_on_video = current_comments
            
            print(f"  Current comments on video: {actual_comments_on_video}")
            print(f"  Comments ordered (pending delivery): {comments_ordered_count}")
            
            if actual_comments_on_video == 0:
                print(f"\n  {Fore.YELLOW}⚠ No comments exist on the video yet!{Style.RESET_ALL}")
                print(f"  {Fore.CYAN}Comment likes can only be ordered after comments are posted.{Style.RESET_ALL}")
                print(f"  {Fore.CYAN}Skipping comment likes for now. Will retry after comments are delivered.{Style.RESET_ALL}")
                # Don't mark as ordered - allow retry later
            else:
                print(f"\n{Fore.YELLOW}It's time to order comment likes!{Style.RESET_ALL}")
                print(f"{Fore.CYAN}Video: {self.video_url}{Style.RESET_ALL}")
                print(f"\n{Fore.YELLOW}The service requires a username to identify which comment to like.{Style.RESET_ALL}")
                print(f"{Fore.CYAN}Enter the username (without @):{Style.RESET_ALL}\n")
                
                try:
                    username = input(f"{Fore.CYAN}Username: {Style.RESET_ALL}").strip()
                    if not username:
                        print(f"{Fore.YELLOW}⚠ No username provided. Skipping comment likes.{Style.RESET_ALL}")
                        comment_likes_ordered = True
                    else:
                        comment_likes_qty = max(MINIMUMS['comment_likes'], progress[self.video_url].get('target_comment_likes', 15))
                        
                        # Update activity status - ordering comment likes
                        progress = self.load_progress()
                        if self.video_url in progress:
                            progress[self.video_url]['current_activity'] = {
                                'status': 'ordering',
                                'action': f"Ordering {comment_likes_qty} comment likes",
                                'service': 'Comment Likes',
                                'quantity': comment_likes_qty,
                                'username': username,
                                'last_updated': datetime.now().isoformat()
                            }
                            self.save_progress(progress)
                        
                        print(f"\n{Fore.YELLOW}Ordering {comment_likes_qty} comment likes...{Style.RESET_ALL}")
                        print(f"  {Fore.CYAN}Target username: @{username}{Style.RESET_ALL}")
                        
                        success_clikes, order_id_clikes = self.create_order(
                            SERVICES['comment_likes'], comment_likes_qty, 'Comment Likes', username=username
                        )
                        if success_clikes:
                            print(f"  {Fore.GREEN}✓ Comment likes ordered! ID: {order_id_clikes}{Style.RESET_ALL}")
                            # Save username for dashboard display
                            progress[self.video_url]['comment_username'] = username
                            self.save_progress(progress)
                            self.update_progress('comment_likes', comment_likes_qty, order_id_clikes)
                            comment_likes_ordered = True
                        else:
                            print(f"  {Fore.RED}✗ Failed to order comment likes{Style.RESET_ALL}")
                            comment_likes_ordered = True
                except (EOFError, KeyboardInterrupt):
                    print(f"\n{Fore.YELLOW}Input cancelled. Skipping comment likes.{Style.RESET_ALL}")
                    comment_likes_ordered = True
            
            print(f"\n{Fore.CYAN}Continuing with delivery plan...{Style.RESET_ALL}\n")
        
        # Filter out comments and comment_likes from schedule (will be milestone-based)
        views_likes_purchases = [p for p in purchases if p['service'] not in ['Comments', 'Comment Likes']]
        
        # Load completed purchases to avoid duplicates
        progress = self.load_progress()
        if self.video_url not in progress:
            progress[self.video_url] = {}
        if 'completed_purchases' not in progress[self.video_url]:
            progress[self.video_url]['completed_purchases'] = []
        completed_purchases = progress[self.video_url]['completed_purchases']
        
        # Create a function to generate purchase ID
        def get_purchase_id(purchase):
            """Generate unique ID for a purchase"""
            return f"{purchase.get('time_seconds', 0)}_{purchase.get('service', '')}_{purchase.get('quantity', 0)}"
        
        # Filter out already completed purchases
        remaining_purchases = []
        skipped_count = 0
        for purchase in views_likes_purchases:
            purchase_id = get_purchase_id(purchase)
            if purchase_id in completed_purchases:
                skipped_count += 1
                print(f"{Fore.CYAN}⏭ Skipping already completed purchase: {purchase['service']} ({purchase['quantity']}) at {purchase['time_str']}{Style.RESET_ALL}")
            else:
                remaining_purchases.append(purchase)
        
        if skipped_count > 0:
            print(f"{Fore.GREEN}✓ Skipped {skipped_count} already completed purchase(s){Style.RESET_ALL}")
            print(f"{Fore.CYAN}Processing {len(remaining_purchases)} remaining purchase(s)\n{Style.RESET_ALL}")
        
        try:
            for i, purchase in enumerate(remaining_purchases):
                # Calculate when this order should be placed
                purchase_time = start_time + timedelta(seconds=purchase.get('time_seconds', 0))
                
                # Wait until it's time
                now = datetime.now()
                if purchase_time > now:
                    wait_seconds = (purchase_time - now).total_seconds()
                    if wait_seconds > 0:
                        # Update activity status - waiting
                        progress = self.load_progress()
                        if self.video_url in progress:
                            progress[self.video_url]['current_activity'] = {
                                'status': 'waiting',
                                'action': f"Order {purchase['service']}",
                                'waiting_for': purchase['service'],
                                'next_action_time': purchase_time.isoformat(),
                                'wait_seconds': wait_seconds,
                                'last_updated': now.isoformat()
                            }
                            
                            # Save next purchase time for the specific metric (for dashboard timer)
                            service_lower = purchase['service'].lower().replace(' ', '_')
                            if service_lower == 'views':
                                progress[self.video_url]['next_views_purchase_time'] = purchase_time.isoformat()
                            elif service_lower == 'likes':
                                progress[self.video_url]['next_likes_purchase_time'] = purchase_time.isoformat()
                            elif service_lower == 'comments':
                                progress[self.video_url]['next_comments_purchase_time'] = purchase_time.isoformat()
                            elif service_lower == 'comment_likes':
                                progress[self.video_url]['next_comment_likes_purchase_time'] = purchase_time.isoformat()
                            
                            self.save_progress(progress)
                        
                        print(f"{Fore.CYAN}[{purchase['time_str']}] Waiting {wait_seconds/60:.1f} minutes...{Style.RESET_ALL}")
                        time.sleep(min(wait_seconds, 60))  # Check every minute
                        continue
                
                # Place order
                service = purchase['service']
                quantity = purchase['quantity']
                service_key = service.lower().replace(' ', '_')
                service_id = SERVICES.get(service_key)
                
                if not service_id:
                    print(f"{Fore.RED}Unknown service: {service} (key: {service_key}, available: {list(SERVICES.keys())}){Style.RESET_ALL}")
                    continue
                
                print(f"{Fore.CYAN}Service: {service} -> key: {service_key} -> ID: {service_id}{Style.RESET_ALL}")
                
                # Update activity status - ordering
                progress = self.load_progress()
                if self.video_url in progress:
                    progress[self.video_url]['current_activity'] = {
                        'status': 'ordering',
                        'action': f"Ordering {quantity} {service.lower()}",
                        'service': service,
                        'quantity': quantity,
                        'last_updated': datetime.now().isoformat()
                    }
                    self.save_progress(progress)
                
                print(f"{Fore.YELLOW}[{purchase['time_str']}] Ordering {quantity} {service.lower()}...{Style.RESET_ALL}")
                self.log_activity(f"[{purchase['time_str']}] Ordering {quantity} {service.lower()}...", 'info')
                
                success, order_id = self.create_order(service_id, quantity, service)
                
                if success:
                    print(f"  {Fore.GREEN}✓ Order placed! ID: {order_id}{Style.RESET_ALL}")
                    self.log_activity(f"✓ Order placed! {quantity} {service.lower()} - Order ID: {order_id}", 'success')
                    self.update_progress(service.lower().replace(' ', '_'), quantity, order_id)
                    
                    # Mark this purchase as completed
                    progress = self.load_progress()
                    if self.video_url in progress:
                        purchase_id = get_purchase_id(purchase)
                        if 'completed_purchases' not in progress[self.video_url]:
                            progress[self.video_url]['completed_purchases'] = []
                        if purchase_id not in progress[self.video_url]['completed_purchases']:
                            progress[self.video_url]['completed_purchases'].append(purchase_id)
                            self.save_progress(progress)
                    
                    # Update activity status - delivering
                    progress = self.load_progress()
                    if self.video_url in progress:
                        # Check if there's a next order in the schedule (from remaining purchases)
                        next_order = None
                        if i + 1 < len(remaining_purchases):
                            next_purchase = remaining_purchases[i + 1]
                            next_purchase_time = start_time + timedelta(seconds=next_purchase.get('time_seconds', 0))
                            if next_purchase_time > datetime.now():
                                wait_seconds = (next_purchase_time - datetime.now()).total_seconds()
                                next_order = {
                                    'status': 'waiting',
                                    'action': f"Order {next_purchase['service']}",
                                    'waiting_for': next_purchase['service'],
                                    'next_action_time': next_purchase_time.isoformat(),
                                    'wait_seconds': wait_seconds,
                                    'last_updated': datetime.now().isoformat()
                                }
                                
                                # Save next purchase time for the specific metric (for dashboard timer)
                                service_lower = next_purchase['service'].lower().replace(' ', '_')
                                if service_lower == 'views':
                                    progress[self.video_url]['next_views_purchase_time'] = next_purchase_time.isoformat()
                                elif service_lower == 'likes':
                                    progress[self.video_url]['next_likes_purchase_time'] = next_purchase_time.isoformat()
                                elif service_lower == 'comments':
                                    progress[self.video_url]['next_comments_purchase_time'] = next_purchase_time.isoformat()
                                elif service_lower == 'comment_likes':
                                    progress[self.video_url]['next_comment_likes_purchase_time'] = next_purchase_time.isoformat()
                        
                        if next_order:
                            progress[self.video_url]['current_activity'] = next_order
                        else:
                            progress[self.video_url]['current_activity'] = {
                                'status': 'delivering',
                                'action': 'Delivering orders',
                                'last_updated': datetime.now().isoformat()
                            }
                            # Clear next purchase times if no more orders
                            if 'next_views_purchase_time' in progress[self.video_url]:
                                del progress[self.video_url]['next_views_purchase_time']
                            if 'next_likes_purchase_time' in progress[self.video_url]:
                                del progress[self.video_url]['next_likes_purchase_time']
                            if 'next_comments_purchase_time' in progress[self.video_url]:
                                del progress[self.video_url]['next_comments_purchase_time']
                            if 'next_comment_likes_purchase_time' in progress[self.video_url]:
                                del progress[self.video_url]['next_comment_likes_purchase_time']
                        self.save_progress(progress)
                else:
                    self.log_activity(f"✗ Failed to place order for {quantity} {service.lower()}", 'error')
                    
                    # Fetch REAL-TIME analytics BEFORE checking milestones
                    real_analytics = self.fetch_all_analytics()
                    current_views = real_analytics.get('views', 0)
                    current_likes = real_analytics.get('likes', 0)
                    current_comments = real_analytics.get('comments', 0)
                    
                    # Update progress with real analytics
                    progress = self.load_progress()
                    if self.video_url in progress:
                        progress[self.video_url]['real_views'] = current_views
                        progress[self.video_url]['real_likes'] = current_likes
                        progress[self.video_url]['real_comments'] = current_comments
                        self.save_progress(progress)
                    
                    # Show progress
                    video_progress = progress[self.video_url]
                    orders_placed = video_progress['orders_placed']
                    total_views_ordered = orders_placed.get('views', 0)
                    
                    # Calculate totals including initial
                    initial_views = video_progress.get('initial_views', 0)
                    initial_likes = video_progress.get('initial_likes', 0)
                    total_views_with_initial = initial_views + total_views_ordered
                    total_likes_with_initial = initial_likes + orders_placed.get('likes', 0)
                    
                    print(f"  Progress: {total_views_ordered} ordered + {initial_views} existing = {total_views_with_initial}/{video_progress['target_views']} views")
                    print(f"            {orders_placed.get('likes', 0)} ordered + {initial_likes} existing = {total_likes_with_initial}/{video_progress['target_likes']} likes")
                    print(f"  Total cost: ${video_progress['total_cost']:.4f}")
                    
                    # Check for milestones (based on REAL-TIME TOTAL views: current + ordered)
                    total_views_real_time = current_views + total_views_ordered
                    
                    # Update activity status - waiting for milestone if not reached
                    progress = self.load_progress()
                    if self.video_url in progress:
                        if not comments_ordered and total_views_real_time < comments_milestone:
                            views_needed = comments_milestone - total_views_real_time
                            progress[self.video_url]['current_activity'] = {
                                'status': 'waiting',
                                'action': 'Waiting for milestone',
                                'waiting_for': f'{views_needed} more views to reach comments milestone ({comments_milestone:,})',
                                'milestone_type': 'comments',
                                'views_needed': views_needed,
                                'last_updated': datetime.now().isoformat()
                            }
                            self.save_progress(progress)
                        elif not comment_likes_ordered and total_views_real_time < comment_likes_milestone:
                            views_needed = comment_likes_milestone - total_views_real_time
                            progress[self.video_url]['current_activity'] = {
                                'status': 'waiting',
                                'action': 'Waiting for milestone',
                                'waiting_for': f'{views_needed} more views to reach comment likes milestone ({comment_likes_milestone:,})',
                                'milestone_type': 'comment_likes',
                                'views_needed': views_needed,
                                'last_updated': datetime.now().isoformat()
                            }
                            self.save_progress(progress)
                    
                    if not comments_ordered and total_views_real_time >= comments_milestone:
                        print(f"\n{Fore.CYAN}{'='*60}")
                        print(f"{Fore.GREEN}🎯 MILESTONE REACHED: {total_views_real_time:,} TOTAL views")
                        print(f"{Fore.CYAN}({current_views:,} existing + {total_views_ordered} ordered)")
                        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
                        print(f"\n{Fore.YELLOW}It's time to order comments!{Style.RESET_ALL}")
                        print(f"{Fore.CYAN}Video: {self.video_url}{Style.RESET_ALL}")
                        
                        # Use real-time comment count we just fetched
                        target_comments = video_progress.get('target_comments', 7)
                        comments_ordered_count = orders_placed.get('comments', 0)
                        total_comments = current_comments + comments_ordered_count
                        
                        print(f"\n{Fore.CYAN}Current comment state:{Style.RESET_ALL}")
                        print(f"  Comments on video: {current_comments}")
                        print(f"  Comments ordered: {comments_ordered_count}")
                        print(f"  Total expected: {total_comments} (target: {target_comments})")
                        
                        if total_comments >= target_comments:
                            print(f"\n  {Fore.GREEN}✓ Already have enough comments ({total_comments} >= {target_comments}){Style.RESET_ALL}")
                            print(f"  {Fore.CYAN}Skipping comment order.{Style.RESET_ALL}")
                            comments_ordered = True
                            continue
                        else:
                            needed = target_comments - total_comments
                            print(f"\n  {Fore.YELLOW}Need {needed} more comments{Style.RESET_ALL}")
                            print(f"  {Fore.CYAN}Minimum order: {MINIMUMS['comments']} comments{Style.RESET_ALL}")
                        
                        # Check if we have saved comments from earlier
                        saved_comments = video_progress.get('saved_comments', [])
                        
                        if len(saved_comments) >= MINIMUMS['comments']:
                            # Use saved comments automatically
                            comments_list = saved_comments[:MINIMUMS['comments']]
                            print(f"\n{Fore.GREEN}✓ Using saved comments from earlier!{Style.RESET_ALL}")
                            print(f"{Fore.CYAN}Comments to be posted:{Style.RESET_ALL}")
                            for i, comment in enumerate(comments_list, 1):
                                print(f"  {i}. {comment}")
                        else:
                            # Prompt for comments if not saved
                            print(f"\n{Fore.YELLOW}Please enter exactly {MINIMUMS['comments']} comments (one per line):{Style.RESET_ALL}")
                            print(f"{Fore.CYAN}You MUST enter {MINIMUMS['comments']} comments - this is the minimum order.{Style.RESET_ALL}")
                            print(f"{Fore.CYAN}Press Enter after each comment.{Style.RESET_ALL}\n")
                            
                            comments_list = []
                            while len(comments_list) < MINIMUMS['comments']:
                                try:
                                    comment_num = len(comments_list) + 1
                                    comment = input(f"{Fore.CYAN}Comment {comment_num}/{MINIMUMS['comments']}: {Style.RESET_ALL}").strip()
                                    if comment:
                                        comments_list.append(comment)
                                    else:
                                        print(f"  {Fore.RED}Empty comment not allowed. Please enter a comment.{Style.RESET_ALL}")
                                except (EOFError, KeyboardInterrupt):
                                    print(f"\n{Fore.RED}Input cancelled.{Style.RESET_ALL}")
                                    print(f"{Fore.YELLOW}Need {MINIMUMS['comments']} comments minimum. Order cancelled.{Style.RESET_ALL}")
                                    comments_ordered = True
                                    break
                        
                        if len(comments_list) == MINIMUMS['comments']:
                            comments_text = '\n'.join(comments_list)
                            
                            print(f"\n{Fore.CYAN}Comments to be posted:{Style.RESET_ALL}")
                            for i, comment in enumerate(comments_list, 1):
                                print(f"  {i}. {comment}")
                            
                            print(f"\n{Fore.YELLOW}Ordering {MINIMUMS['comments']} comments...{Style.RESET_ALL}")
                            success_comments, order_id_comments = self.create_order(
                                SERVICES['comments'], MINIMUMS['comments'], 'Comments', comments_text
                            )
                            if success_comments:
                                print(f"  {Fore.GREEN}✓ Comments ordered! ID: {order_id_comments}{Style.RESET_ALL}")
                                self.update_progress('comments', MINIMUMS['comments'], order_id_comments)
                                comments_ordered = True
                                
                                # Save comments for reference
                                comments_file = Path.home() / '.smmfollows_bot' / 'comments.txt'
                                try:
                                    with open(comments_file, 'w', encoding='utf-8') as f:
                                        f.write('\n'.join(comments_list))
                                    print(f"  {Fore.CYAN}✓ Comments saved{Style.RESET_ALL}")
                                except:
                                    pass
                            else:
                                print(f"  {Fore.RED}✗ Failed to order comments{Style.RESET_ALL}")
                                comments_ordered = True
                        else:
                            print(f"\n{Fore.RED}✗ Not enough comments. Need exactly {MINIMUMS['comments']}.{Style.RESET_ALL}")
                            comments_ordered = True
                        
                        print(f"\n{Fore.CYAN}Continuing with delivery plan...{Style.RESET_ALL}\n")
                    
                    if not comment_likes_ordered and total_views_real_time >= comment_likes_milestone:
                        print(f"\n{Fore.CYAN}{'='*60}")
                        print(f"{Fore.GREEN}🎯 MILESTONE REACHED: {total_views_with_initial:,} TOTAL views")
                        print(f"{Fore.CYAN}({initial_views:,} existing + {total_views_ordered} ordered)")
                        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
                        # Check if comments exist before ordering comment likes
                        # Only check ACTUAL comments on video (not ordered ones - they take time to deliver)
                        comments_ordered_count = orders_placed.get('comments', 0)
                        actual_comments_on_video = current_comments
                        
                        print(f"\n{Fore.CYAN}Checking if comments exist...{Style.RESET_ALL}")
                        print(f"  Current comments on video: {actual_comments_on_video}")
                        print(f"  Comments ordered (pending delivery): {comments_ordered_count}")
                        
                        if actual_comments_on_video == 0:
                            print(f"\n  {Fore.YELLOW}⚠ No comments exist on the video yet!{Style.RESET_ALL}")
                            print(f"  {Fore.CYAN}Comment likes can only be ordered after comments are posted.{Style.RESET_ALL}")
                            print(f"  {Fore.CYAN}Skipping comment likes for now. Will retry after comments are delivered.{Style.RESET_ALL}")
                            # Don't mark as ordered - allow retry later when comments exist
                        else:
                            print(f"\n{Fore.YELLOW}It's time to order comment likes!{Style.RESET_ALL}")
                            print(f"{Fore.CYAN}Video: {self.video_url}{Style.RESET_ALL}")
                            print(f"\n{Fore.YELLOW}The service requires a username to identify which comment to like.{Style.RESET_ALL}")
                            print(f"{Fore.CYAN}Enter the username (without @):{Style.RESET_ALL}\n")
                            
                            try:
                                username = input(f"{Fore.CYAN}Username: {Style.RESET_ALL}").strip()
                                if not username:
                                    print(f"{Fore.YELLOW}⚠ No username provided. Skipping comment likes.{Style.RESET_ALL}")
                                    comment_likes_ordered = True
                                else:
                                    comment_likes_qty = max(MINIMUMS['comment_likes'], video_progress['target_comment_likes'])
                                    
                                    # Update activity status - ordering comment likes
                                    progress = self.load_progress()
                                    if self.video_url in progress:
                                        progress[self.video_url]['current_activity'] = {
                                            'status': 'ordering',
                                            'action': f"Ordering {comment_likes_qty} comment likes",
                                            'service': 'Comment Likes',
                                            'quantity': comment_likes_qty,
                                            'username': username,
                                            'last_updated': datetime.now().isoformat()
                                        }
                                        self.save_progress(progress)
                                    
                                    print(f"\n{Fore.YELLOW}Ordering {comment_likes_qty} comment likes...{Style.RESET_ALL}")
                                    print(f"  {Fore.CYAN}Target username: @{username}{Style.RESET_ALL}")
                                    
                                    success_clikes, order_id_clikes = self.create_order(
                                        SERVICES['comment_likes'], comment_likes_qty, 'Comment Likes', username=username
                                    )
                                    if success_clikes:
                                        print(f"  {Fore.GREEN}✓ Comment likes ordered! ID: {order_id_clikes}{Style.RESET_ALL}")
                                        # Save username for dashboard display
                                        progress[self.video_url]['comment_username'] = username
                                        self.save_progress(progress)
                                        self.update_progress('comment_likes', comment_likes_qty, order_id_clikes)
                                        comment_likes_ordered = True
                                    else:
                                        print(f"  {Fore.RED}✗ Failed to order comment likes{Style.RESET_ALL}")
                                        comment_likes_ordered = True
                            except (EOFError, KeyboardInterrupt):
                                print(f"\n{Fore.YELLOW}Input cancelled. Skipping comment likes.{Style.RESET_ALL}")
                                comment_likes_ordered = True
                        
                        print(f"\n{Fore.CYAN}Continuing with delivery plan...{Style.RESET_ALL}\n")
                
                # Small delay between orders
                time.sleep(2)
            
            print(f"\n{Fore.GREEN}✓ Delivery plan complete!{Style.RESET_ALL}")
            
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Bot stopped by user{Style.RESET_ALL}")
            print(f"{Fore.CYAN}Progress saved. Run again to resume.{Style.RESET_ALL}")

def main():
    if len(sys.argv) < 2:
        print(f"{Fore.YELLOW}Usage: python run_delivery_bot.py <video_url>{Style.RESET_ALL}")
        sys.exit(1)
    
    video_url = sys.argv[1]
    bot = DeliveryBot(video_url)
    bot.run_delivery_plan()

if __name__ == "__main__":
    main()

