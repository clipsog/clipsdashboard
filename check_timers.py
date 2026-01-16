#!/usr/bin/env python3
"""
Quick diagnostic script to check timer status for all videos
Run this to see why orders aren't being placed
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from colorama import Fore, Style, init

init(autoreset=True)

def load_progress():
    progress_file = Path.home() / '.smmfollows_bot' / 'progress.json'
    if progress_file.exists():
        with open(progress_file, 'r') as f:
            return json.load(f)
    return {}

def load_schedule():
    schedule_file = Path(__file__).parent / 'purchase_schedule.json'
    if schedule_file.exists():
        with open(schedule_file, 'r') as f:
            return json.load(f)
    return []

def main():
    print(f"""
{Fore.CYAN}╔══════════════════════════════════════════════════╗
║   Timer Diagnostic Tool                          ║
╚══════════════════════════════════════════════════╝{Style.RESET_ALL}
""")
    
    progress = load_progress()
    schedule = load_schedule()
    
    if not progress:
        print(f"{Fore.RED}❌ No videos found in progress.json{Style.RESET_ALL}")
        print(f"   Location: {Path.home() / '.smmfollows_bot' / 'progress.json'}")
        return
    
    if not schedule:
        print(f"{Fore.RED}❌ No purchase_schedule.json found{Style.RESET_ALL}")
        return
    
    print(f"{Fore.GREEN}Found {len(progress)} video(s) and {len(schedule)} scheduled order(s){Style.RESET_ALL}\n")
    
    now = datetime.now()
    views_likes_purchases = [p for p in schedule if p['service'] not in ['Comments', 'Comment Likes']]
    
    for idx, (video_url, video_data) in enumerate(progress.items(), 1):
        print(f"{Fore.CYAN}{'='*80}")
        print(f"Video #{idx}: {video_url[:70]}...")
        print(f"{'='*80}{Style.RESET_ALL}")
        
        # Check start_time
        start_time_str = video_data.get('start_time') or video_data.get('campaign_start_time')
        if not start_time_str:
            print(f"{Fore.RED}❌ NO START_TIME - Cannot check timers!{Style.RESET_ALL}")
            print(f"   This video needs a start_time to calculate order timing")
            print()
            continue
        
        try:
            start_time = datetime.fromisoformat(start_time_str.replace('Z', '+00:00'))
        except:
            print(f"{Fore.RED}❌ INVALID START_TIME: {start_time_str}{Style.RESET_ALL}")
            print()
            continue
        
        # Show campaign info
        elapsed = (now - start_time.replace(tzinfo=None)).total_seconds()
        print(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Elapsed: {elapsed/3600:.2f} hours")
        print(f"Status: {video_data.get('status', 'active')}")
        
        # Check completed orders
        completed_purchases = video_data.get('completed_purchases', [])
        print(f"Completed orders: {len(completed_purchases)}")
        
        # Check targets
        target_views = video_data.get('target_views', 4000)
        target_likes = video_data.get('target_likes', 125)
        current_views = video_data.get('real_views', 0)
        current_likes = video_data.get('real_likes', 0)
        
        print(f"Goals: {current_views}/{target_views} views, {current_likes}/{target_likes} likes")
        
        # Check OVERTIME
        target_completion = video_data.get('target_completion_time') or video_data.get('target_completion_datetime')
        overtime_stopped = video_data.get('overtime_stopped', False)
        
        if target_completion:
            try:
                target_dt = datetime.fromisoformat(target_completion.replace('Z', '+00:00'))
                if now > target_dt.replace(tzinfo=None):
                    if overtime_stopped:
                        print(f"{Fore.YELLOW}⏸ OVERTIME STOPPED{Style.RESET_ALL}")
                    else:
                        print(f"{Fore.MAGENTA}⚡ IN OVERTIME MODE - Should order every 30s{Style.RESET_ALL}")
            except:
                pass
        
        print(f"\n{Fore.CYAN}Scheduled Orders:{Style.RESET_ALL}")
        
        # Check each scheduled order
        due_count = 0
        for purchase in views_likes_purchases:
            purchase_id = f"{purchase.get('time_seconds', 0)}_{purchase.get('service', '')}_{purchase.get('quantity', 0)}"
            is_completed = purchase_id in completed_purchases
            
            purchase_time = start_time.replace(tzinfo=None) + timedelta(seconds=purchase.get('time_seconds', 0))
            time_diff = (now - purchase_time).total_seconds()
            is_due = time_diff >= -60 and not is_completed
            
            status = "✓ COMPLETED" if is_completed else ("🔴 DUE NOW" if is_due else f"⏰ in {-time_diff/60:.0f}min")
            color = Fore.GREEN if is_completed else (Fore.RED if is_due else Fore.YELLOW)
            
            print(f"  {color}[{purchase['time_str']}] {purchase['quantity']} {purchase['service']}: {status}{Style.RESET_ALL}")
            
            if is_due:
                due_count += 1
        
        if due_count > 0:
            print(f"\n{Fore.RED}⚠️  {due_count} ORDER(S) ARE DUE!{Style.RESET_ALL}")
            print(f"   The continuous ordering service should be placing these.")
        else:
            print(f"\n{Fore.GREEN}✓ No orders due yet{Style.RESET_ALL}")
        
        print()
    
    # Check if continuous ordering service is running
    print(f"{Fore.CYAN}{'='*80}")
    print(f"Service Status Check")
    print(f"{'='*80}{Style.RESET_ALL}")
    print(f"\n{Fore.YELLOW}To place orders automatically, you need to run:{Style.RESET_ALL}")
    print(f"  python3 continuous_ordering_service.py")
    print(f"\nOr check if it's running:")
    print(f"  ps aux | grep continuous_ordering_service")

if __name__ == "__main__":
    main()
