#!/usr/bin/env python3
"""
Dry Run Delivery Bot - Simulates full 24-hour delivery without placing orders
"""

import json
import time
import sys
from datetime import datetime, timedelta
from pathlib import Path
from colorama import Fore, Style, init

init(autoreset=True)

video_url = "https://www.tiktok.com/@the.clips.origins/video/7589415681972538631"

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

RATES = {
    'views': 0.0140,
    'likes': 0.2100,
    'comments': 13.5000,
    'comment_likes': 0.2100
}

class DryRunBot:
    def __init__(self, video_url):
        self.video_url = video_url
        self.progress_file = Path.home() / '.smmfollows_bot' / 'progress.json'
        self.progress_file.parent.mkdir(exist_ok=True)
        
        self.orders_placed = {'views': 0, 'likes': 0, 'comments': 0, 'comment_likes': 0}
        self.order_history = []
        self.total_cost = 0
        
    def simulate_order(self, service_type, quantity, order_time):
        """Simulate placing an order"""
        service_name = service_type.replace('_', ' ').title()
        cost = (quantity / 1000.0) * RATES.get(service_type, 0)
        
        self.orders_placed[service_type] += quantity
        self.total_cost += cost
        
        order_id = f"DRY-RUN-{len(self.order_history) + 1}"
        
        self.order_history.append({
            'timestamp': order_time.isoformat(),
            'service': service_type,
            'quantity': quantity,
            'order_id': order_id,
            'cost': cost
        })
        
        return True, order_id
    
    def save_progress(self):
        """Save simulated progress"""
        progress = {}
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r') as f:
                    progress = json.load(f)
            except:
                pass
        
        progress[self.video_url] = {
            'start_time': self.start_time.isoformat(),
            'target_views': 4000,
            'target_likes': 125,
            'target_comments': 7,
            'target_comment_likes': 15,
            'orders_placed': self.orders_placed.copy(),
            'order_history': self.order_history.copy(),
            'total_cost': self.total_cost,
            'dry_run': True
        }
        
        try:
            with open(self.progress_file, 'w') as f:
                json.dump(progress, f, indent=2)
        except Exception as e:
            print(f"{Fore.RED}Error saving progress: {e}{Style.RESET_ALL}")
    
    def run_dry_run(self, speed_multiplier=1.0):
        """Run dry run simulation"""
        # Load purchase schedule
        schedule_file = Path(__file__).parent / 'purchase_schedule.json'
        if not schedule_file.exists():
            print(f"{Fore.RED}Error: purchase_schedule.json not found{Style.RESET_ALL}")
            return
        
        with open(schedule_file, 'r') as f:
            purchases = json.load(f)
        
        # Filter out comments and comment_likes (milestone-based)
        views_likes_purchases = [p for p in purchases if p['service'] not in ['Comments', 'Comment Likes']]
        
        # Milestone tracking
        comments_milestone = 2000
        comment_likes_milestone = 2600
        comments_ordered = False
        comment_likes_ordered = False
        
        print(f"""
    {Fore.CYAN}╔══════════════════════════════════════════════╗
    ║   DRY RUN - No Orders Will Be Placed      ║
    ╚══════════════════════════════════════════════╝{Style.RESET_ALL}
    """)
        
        print(f"{Fore.YELLOW}Video: {self.video_url}{Style.RESET_ALL}")
        print(f"Total purchases: {len(views_likes_purchases)} (views/likes only)")
        print(f"Milestone-based: Comments @ {comments_milestone:,} views, Comment Likes @ {comment_likes_milestone:,} views")
        print(f"Speed multiplier: {speed_multiplier}x (for testing)")
        print(f"{Fore.CYAN}Press Ctrl+C to stop{Style.RESET_ALL}\n")
        
        self.start_time = datetime.now()
        simulated_start = self.start_time
        
        try:
            for i, purchase in enumerate(views_likes_purchases):
                # Calculate when this order should be placed
                purchase_time = simulated_start + timedelta(seconds=purchase['time_seconds'] / speed_multiplier)
                
                # Wait until it's time (or skip if speed multiplier is high)
                now = datetime.now()
                if purchase_time > now and speed_multiplier <= 60:
                    wait_seconds = (purchase_time - now).total_seconds()
                    if wait_seconds > 0 and wait_seconds < 300:  # Don't wait more than 5 min in dry run
                        time.sleep(min(wait_seconds, 1))  # Max 1 second wait
                
                # Simulate order
                service = purchase['service']
                quantity = purchase['quantity']
                service_type = service.lower().replace(' ', '_')
                
                order_time = datetime.now()
                success, order_id = self.simulate_order(service_type, quantity, order_time)
                
                if success:
                    elapsed = (order_time - self.start_time).total_seconds() / 3600
                    total_views = self.orders_placed['views']
                    
                    print(f"{Fore.GREEN}[{purchase['time_str']}] {Fore.YELLOW}[DRY RUN]{Style.RESET_ALL} {service}: {quantity} "
                          f"{Fore.CYAN}(Order ID: {order_id}){Style.RESET_ALL}")
                    print(f"  Elapsed: {elapsed:.2f}h | "
                          f"Views: {total_views}/4000 | "
                          f"Likes: {self.orders_placed['likes']}/125 | "
                          f"Cost: ${self.total_cost:.4f}")
                    
                    # Check for milestones
                    if not comments_ordered and total_views >= comments_milestone:
                        print(f"\n{Fore.CYAN}{'='*60}")
                        print(f"{Fore.GREEN}🎯 MILESTONE REACHED: {total_views} views")
                        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
                        print(f"\n{Fore.YELLOW}[DRY RUN] It's time to order comments!{Style.RESET_ALL}")
                        print(f"{Fore.CYAN}Video: {self.video_url}{Style.RESET_ALL}")
                        print(f"\n{Fore.YELLOW}In a real run, you would be prompted to enter {MINIMUMS['comments']} comments here.{Style.RESET_ALL}")
                        print(f"{Fore.CYAN}For dry run, simulating with placeholder comments...{Style.RESET_ALL}\n")
                        
                        comments_qty = 10
                        success_comments, order_id_comments = self.simulate_order('comments', comments_qty, order_time)
                        if success_comments:
                            print(f"  {Fore.GREEN}✓ Comments would be ordered! ID: {order_id_comments}{Style.RESET_ALL}")
                            print(f"  {Fore.CYAN}(In real run, you'll enter custom comments){Style.RESET_ALL}")
                            comments_ordered = True
                    
                    if not comment_likes_ordered and total_views >= comment_likes_milestone:
                        print(f"\n  {Fore.GREEN}🎯 Milestone reached: {total_views} views - Ordering comment likes!{Style.RESET_ALL}")
                        comment_likes_qty = 50
                        success_clikes, order_id_clikes = self.simulate_order('comment_likes', comment_likes_qty, order_time)
                        if success_clikes:
                            print(f"  {Fore.GREEN}✓ Comment likes ordered! ID: {order_id_clikes}{Style.RESET_ALL}")
                            comment_likes_ordered = True
                    
                    # Save progress every 10 orders
                    if (i + 1) % 10 == 0:
                        self.save_progress()
                        print(f"  {Fore.CYAN}✓ Progress saved{Style.RESET_ALL}")
                
                # Small delay
                if speed_multiplier <= 60:
                    time.sleep(0.1)
            
            # Final save
            self.save_progress()
            
            print(f"\n{Fore.GREEN}{'='*60}")
            print(f"DRY RUN COMPLETE!")
            print(f"{'='*60}{Style.RESET_ALL}\n")
            
            print(f"{Fore.CYAN}Summary:{Style.RESET_ALL}")
            print(f"  Total Orders: {len(self.order_history)}")
            print(f"  Views Ordered: {self.orders_placed['views']}/4000")
            print(f"  Likes Ordered: {self.orders_placed['likes']}/125")
            print(f"  Comments Ordered: {self.orders_placed['comments']}")
            print(f"  Comment Likes Ordered: {self.orders_placed['comment_likes']}")
            print(f"  Total Cost: ${self.total_cost:.4f}")
            print(f"\n{Fore.GREEN}✓ Progress saved to: {self.progress_file}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}Run 'python monitor_progress.py' to view status{Style.RESET_ALL}")
            
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Dry run stopped by user{Style.RESET_ALL}")
            self.save_progress()
            print(f"{Fore.CYAN}Progress saved. {len(self.order_history)} orders simulated.{Style.RESET_ALL}")

def main():
    import sys
    
    speed_multiplier = 3600  # Default: 1 hour = 1 second (for fast testing)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == '--real-time':
            speed_multiplier = 1.0  # Real-time (24 hours)
        elif sys.argv[1] == '--fast':
            speed_multiplier = 60  # 1 minute = 1 second
        elif sys.argv[1].startswith('--speed='):
            speed_multiplier = float(sys.argv[1].split('=')[1])
    
    bot = DryRunBot(video_url)
    bot.run_dry_run(speed_multiplier=speed_multiplier)

if __name__ == "__main__":
    main()

