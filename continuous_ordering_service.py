#!/usr/bin/env python3
"""
Continuous Ordering Service - Monitors all videos and places orders automatically
Runs 24/7 to ensure goals are reached, especially in OVERTIME mode
"""

import time
import json
import sys
from pathlib import Path
from datetime import datetime
from colorama import Fore, Style, init
from run_delivery_bot import DeliveryBot

init(autoreset=True)

class ContinuousOrderingService:
    def __init__(self):
        self.progress_file = Path.home() / '.smmfollows_bot' / 'progress.json'
        self.check_interval = 30  # Check every 30 seconds
        
    def load_progress(self):
        """Load progress for all videos"""
        if self.progress_file.exists():
            try:
                with open(self.progress_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def process_all_videos(self):
        """Process all videos - check and place due orders"""
        progress = self.load_progress()
        
        if not progress:
            print(f"{Fore.YELLOW}No videos to process{Style.RESET_ALL}")
            return
        
        videos_processed = 0
        orders_placed = 0
        
        for video_url, video_data in progress.items():
            try:
                # Skip if video is ended
                if video_data.get('status') == 'ended':
                    continue
                
                # Check if in overtime mode
                target_time = video_data.get('target_completion_time') or video_data.get('target_completion_datetime')
                overtime_stopped = video_data.get('overtime_stopped', False)
                
                in_overtime = False
                if target_time and not overtime_stopped:
                    try:
                        target_dt = datetime.fromisoformat(target_time.replace('Z', '+00:00'))
                        in_overtime = datetime.now() > target_dt.replace(tzinfo=None)
                    except:
                        pass
                
                # Create bot instance and check for due orders
                bot = DeliveryBot(video_url)
                placed = bot.check_and_place_due_orders()
                
                if placed:
                    orders_placed += 1
                    if in_overtime:
                        print(f"{Fore.MAGENTA}[OVERTIME] Orders placed for: {video_url[:50]}...{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.GREEN}✓ Orders placed for: {video_url[:50]}...{Style.RESET_ALL}")
                
                videos_processed += 1
                
            except Exception as e:
                print(f"{Fore.RED}Error processing {video_url[:50]}...: {e}{Style.RESET_ALL}")
                continue
        
        return videos_processed, orders_placed
    
    def run(self):
        """Run continuous monitoring loop"""
        print(f"""
{Fore.CYAN}╔══════════════════════════════════════════════════╗
║   Continuous Ordering Service (24/7)            ║
║   Monitors all videos and places orders         ║
║   Automatically until goals are reached          ║
╚══════════════════════════════════════════════════╝{Style.RESET_ALL}

{Fore.YELLOW}✓ Checks every {self.check_interval} seconds
✓ Places orders when due
✓ Continues in OVERTIME mode until goals reached
✓ Press Ctrl+C to stop{Style.RESET_ALL}
        """)
        
        cycle_count = 0
        
        try:
            while True:
                cycle_count += 1
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                print(f"\n{Fore.CYAN}{'='*60}")
                print(f"Cycle #{cycle_count} - {timestamp}")
                print(f"{'='*60}{Style.RESET_ALL}")
                
                # Process all videos
                videos_processed, orders_placed = self.process_all_videos()
                
                if orders_placed > 0:
                    print(f"\n{Fore.GREEN}✓ Placed orders for {orders_placed} video(s){Style.RESET_ALL}")
                else:
                    print(f"\n{Fore.CYAN}No orders due for: {videos_processed} video(s){Style.RESET_ALL}")
                
                # Wait before next check
                print(f"{Fore.CYAN}Next check in {self.check_interval} seconds...{Style.RESET_ALL}")
                time.sleep(self.check_interval)
                
        except KeyboardInterrupt:
            print(f"\n\n{Fore.YELLOW}╔══════════════════════════════════════════════════╗")
            print(f"║   Continuous Ordering Service Stopped           ║")
            print(f"╚══════════════════════════════════════════════════╝{Style.RESET_ALL}\n")

def main():
    service = ContinuousOrderingService()
    service.run()

if __name__ == "__main__":
    main()
