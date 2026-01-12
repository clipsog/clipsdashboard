#!/usr/bin/env python3
"""
Monitor progress of multiple videos over 24+ hours
"""

import requests
import json
import time
from datetime import datetime, timedelta
from pathlib import Path
from colorama import Fore, Style, init
import sys

init(autoreset=True)

API_KEY = "3327db2d9f02b8c241b200a40fe3d12d"
BASE_URL = "https://smmfollows.com/api/v2"

class ProgressMonitor:
    def __init__(self):
        self.progress_file = Path.home() / '.smmfollows_bot' / 'progress.json'
        self.orders_file = Path.home() / '.smmfollows_bot' / 'orders.json'
        self.log_file = Path.home() / '.smmfollows_bot' / 'monitor.log'
        
        # Create directories
        self.progress_file.parent.mkdir(exist_ok=True)
        
    def load_progress(self):
        """Load progress for all videos"""
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
    
    def load_orders(self):
        """Load order history"""
        if self.orders_file.exists():
            try:
                with open(self.orders_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def check_order_status(self, order_id):
        """Check status of an order"""
        try:
            response = requests.post(
                BASE_URL,
                data={
                    'key': API_KEY,
                    'action': 'status',
                    'order': order_id
                },
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
            return None
        except:
            return None
    
    def fetch_tiktok_analytics(self, video_url):
        """Fetch real TikTok analytics"""
        # Using trollishly.com method (from earlier bot)
        try:
            import re
            from bs4 import BeautifulSoup
            from fake_useragent import UserAgent
            
            video_id_match = re.search(r'tiktok\.com/@[^/]+/video/(\d+)', video_url) or re.search(r'tiktok\.com/@[^/]+/photo/(\d+)', video_url)
            if not video_id_match:
                return None
            
            video_id = video_id_match.group(1)
            ua = UserAgent()
            
            # Get CSRF token
            csrf_url = "https://www.trollishly.com/tiktok-counter/"
            headers = {'User-Agent': ua.random}
            response = requests.get(csrf_url, headers=headers, timeout=10)
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            csrf_token = soup.find('meta', {'name': 'csrf-token'})
            if not csrf_token:
                return None
            
            csrf_token = csrf_token.get('content')
            cookies = response.cookies
            
            # Fetch video data
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
            
            response = requests.post(api_url, data=payload, headers=headers, cookies=cookies, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if 'error' not in data:
                    return {
                        'views': int(data.get('video_views_count', 0)) if data.get('video_views_count') else 0,
                        'likes': int(data.get('video_likes_count', 0)) if data.get('video_likes_count') else 0,
                        'comments': int(data.get('video_comment_count', 0)) if data.get('video_comment_count') else 0
                    }
        except Exception as e:
            pass
        return None
    
    def display_status(self, video_url, video_progress):
        """Display status for one video"""
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"Video: {video_url[:50]}...")
        print(f"{'='*60}{Style.RESET_ALL}")
        
        # Basic info
        start_time = video_progress.get('start_time')
        target_views = video_progress.get('target_views', 4000)
        target_likes = video_progress.get('target_likes', 125)
        
        if start_time:
            start_dt = datetime.fromisoformat(start_time)
            elapsed = datetime.now() - start_dt
            elapsed_hours = elapsed.total_seconds() / 3600
            print(f"Started: {start_dt.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"Elapsed: {elapsed_hours:.1f} hours / 24 hours")
            print(f"Progress: {(elapsed_hours / 24 * 100):.1f}% of timeline")
        
        # Orders placed
        orders_placed = video_progress.get('orders_placed', {})
        views_ordered = orders_placed.get('views', 0)
        likes_ordered = orders_placed.get('likes', 0)
        comments_ordered = orders_placed.get('comments', 0)
        comment_likes_ordered = orders_placed.get('comment_likes', 0)
        
        print(f"\n{Fore.YELLOW}Orders Placed:{Style.RESET_ALL}")
        print(f"  Views: {views_ordered}/{target_views} ({views_ordered/target_views*100:.1f}%)")
        print(f"  Likes: {likes_ordered}/{target_likes} ({likes_ordered/target_likes*100:.1f}%)")
        print(f"  Comments: {comments_ordered} (target: {video_progress.get('target_comments', 7)})")
        print(f"  Comment Likes: {comment_likes_ordered} (target: {video_progress.get('target_comment_likes', 15)})")
        
        # Real analytics
        analytics = self.fetch_tiktok_analytics(video_url)
        if analytics:
            real_views = analytics.get('views', 0)
            real_likes = analytics.get('likes', 0)
            real_comments = analytics.get('comments', 0)
            
            print(f"\n{Fore.GREEN}Real TikTok Analytics:{Style.RESET_ALL}")
            print(f"  Views: {real_views:,} / {target_views:,} ({real_views/target_views*100:.1f}%)")
            print(f"  Likes: {real_likes} / {target_likes} ({real_likes/target_likes*100:.1f}%)")
            print(f"  Comments: {real_comments}")
            
            # Calculate delivery progress
            if views_ordered > 0:
                delivery_rate = (real_views / views_ordered) * 100 if views_ordered > 0 else 0
                print(f"\n{Fore.CYAN}Delivery Status:{Style.RESET_ALL}")
                print(f"  Views Delivery: {delivery_rate:.1f}% ({real_views}/{views_ordered} delivered)")
        else:
            print(f"\n{Fore.YELLOW}⚠ Could not fetch real analytics{Style.RESET_ALL}")
        
        # Next orders
        next_orders = video_progress.get('next_orders', [])
        if next_orders:
            print(f"\n{Fore.CYAN}Next Orders Scheduled:{Style.RESET_ALL}")
            for order in next_orders[:5]:
                order_time = datetime.fromisoformat(order['time'])
                time_until = order_time - datetime.now()
                if time_until.total_seconds() > 0:
                    print(f"  {order['service']}: {order['quantity']} at {order_time.strftime('%H:%M:%S')} (in {time_until.total_seconds()/60:.0f} min)")
        
        # Issues/Warnings
        issues = []
        if views_ordered < target_views and start_time:
            elapsed_hours = (datetime.now() - datetime.fromisoformat(start_time)).total_seconds() / 3600
            expected_orders = int((elapsed_hours / 24) * 80)  # 80 orders in 24h
            if len(video_progress.get('order_history', [])) < expected_orders * 0.8:
                issues.append(f"Views orders behind schedule ({len(video_progress.get('order_history', []))} vs expected {expected_orders})")
        
        if issues:
            print(f"\n{Fore.RED}⚠ Issues:{Style.RESET_ALL}")
            for issue in issues:
                print(f"  • {issue}")
    
    def monitor_all(self):
        """Monitor all active videos"""
        progress = self.load_progress()
        
        if not progress:
            print(f"{Fore.YELLOW}No active videos found{Style.RESET_ALL}")
            return
        
        print(f"""
    {Fore.CYAN}╔══════════════════════════════════════════════╗
    ║   Monitoring {len(progress)} Active Video(s)        ║
    ╚══════════════════════════════════════════════╝{Style.RESET_ALL}
    """)
        
        for video_url, video_progress in progress.items():
            self.display_status(video_url, video_progress)
        
        # Summary
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"SUMMARY")
        print(f"{'='*60}{Style.RESET_ALL}\n")
        
        total_views_ordered = sum(v.get('orders_placed', {}).get('views', 0) for v in progress.values())
        total_likes_ordered = sum(v.get('orders_placed', {}).get('likes', 0) for v in progress.values())
        total_cost = sum(v.get('total_cost', 0) for v in progress.values())
        
        print(f"Active Videos: {len(progress)}")
        print(f"Total Views Ordered: {total_views_ordered:,}")
        print(f"Total Likes Ordered: {total_likes_ordered}")
        print(f"Total Cost: ${total_cost:.4f}")
    
    def check_order_statuses(self, video_url):
        """Check status of all orders for a video"""
        progress = self.load_progress()
        if video_url not in progress:
            print(f"{Fore.RED}Video not found in progress{Style.RESET_ALL}")
            return
        
        video_progress = progress[video_url]
        order_history = video_progress.get('order_history', [])
        
        print(f"\n{Fore.CYAN}Checking order statuses...{Style.RESET_ALL}\n")
        
        statuses = {'completed': 0, 'processing': 0, 'pending': 0, 'error': 0}
        
        for order in order_history[-20:]:  # Check last 20 orders
            order_id = order.get('order_id')
            if order_id:
                status_data = self.check_order_status(order_id)
                if status_data:
                    status = status_data.get('status', 'unknown')
                    statuses[status] = statuses.get(status, 0) + 1
                    print(f"  Order {order_id}: {status}")
        
        print(f"\n{Fore.CYAN}Status Summary:{Style.RESET_ALL}")
        for status, count in statuses.items():
            if count > 0:
                print(f"  {status.capitalize()}: {count}")

def main():
    monitor = ProgressMonitor()
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--check-orders':
            video_url = sys.argv[2] if len(sys.argv) > 2 else None
            if video_url:
                monitor.check_order_statuses(video_url)
            else:
                print(f"{Fore.RED}Please provide video URL{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}Unknown command{Style.RESET_ALL}")
    else:
        monitor.monitor_all()

if __name__ == "__main__":
    main()


