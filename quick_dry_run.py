#!/usr/bin/env python3
"""
Quick dry run - simulates all orders instantly for preview
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from colorama import Fore, Style, init

init(autoreset=True)

video_url = "https://www.tiktok.com/@the.clips.origins/video/7589415681972538631"

RATES = {
    'views': 0.0140,
    'likes': 0.2100,
    'comments': 13.5000,
    'comment_likes': 0.2100
}

def main():
    print(f"""
    {Fore.CYAN}╔══════════════════════════════════════════════╗
    ║   Quick Dry Run Preview                ║
    ╚══════════════════════════════════════════════╝{Style.RESET_ALL}
    """)
    
    # Load schedule
    schedule_file = Path(__file__).parent / 'purchase_schedule.json'
    with open(schedule_file, 'r') as f:
        purchases = json.load(f)
    
    print(f"Video: {video_url}\n")
    print(f"{Fore.CYAN}Simulating {len(purchases)} orders over 24 hours...{Style.RESET_ALL}\n")
    
    # Simulate all orders
    orders_placed = {'views': 0, 'likes': 0, 'comments': 0, 'comment_likes': 0}
    total_cost = 0
    order_times = []
    
    start_time = datetime.now()
    
    for purchase in purchases:
        service_type = purchase['service'].lower().replace(' ', '_')
        quantity = purchase['quantity']
        time_seconds = purchase['time_seconds']
        
        orders_placed[service_type] += quantity
        cost = (quantity / 1000.0) * RATES.get(service_type, 0)
        total_cost += cost
        
        order_time = start_time + timedelta(seconds=time_seconds)
        order_times.append({
            'time': order_time,
            'service': purchase['service'],
            'quantity': quantity
        })
    
    # Show summary
    print(f"{Fore.GREEN}✓ Simulation Complete!{Style.RESET_ALL}\n")
    
    print(f"{Fore.CYAN}{'='*60}")
    print(f"ORDER SUMMARY")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    
    print(f"{Fore.YELLOW}Views:{Style.RESET_ALL}")
    print(f"  Orders: {len([p for p in purchases if p['service'] == 'Views'])}")
    print(f"  Total: {orders_placed['views']:,} views")
    print(f"  Cost: ${(orders_placed['views']/1000.0) * RATES['views']:.4f}\n")
    
    print(f"{Fore.YELLOW}Likes:{Style.RESET_ALL}")
    print(f"  Orders: {len([p for p in purchases if p['service'] == 'Likes'])}")
    print(f"  Total: {orders_placed['likes']} likes")
    print(f"  Cost: ${(orders_placed['likes']/1000.0) * RATES['likes']:.4f}\n")
    
    print(f"{Fore.YELLOW}Comments:{Style.RESET_ALL}")
    print(f"  Orders: {len([p for p in purchases if p['service'] == 'Comments'])}")
    print(f"  Total: {orders_placed['comments']} comments")
    print(f"  Cost: ${(orders_placed['comments']/1000.0) * RATES['comments']:.4f}\n")
    
    print(f"{Fore.YELLOW}Comment Likes:{Style.RESET_ALL}")
    print(f"  Orders: {len([p for p in purchases if p['service'] == 'Comment Likes'])}")
    print(f"  Total: {orders_placed['comment_likes']} likes")
    print(f"  Cost: ${(orders_placed['comment_likes']/1000.0) * RATES['comment_likes']:.4f}\n")
    
    print(f"{Fore.CYAN}{'='*60}")
    print(f"{Fore.GREEN}TOTAL COST: ${total_cost:.4f}")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    
    # Show timeline milestones
    print(f"{Fore.CYAN}Key Milestones:{Style.RESET_ALL}\n")
    
    milestones = [
        (0, "Start - First views and likes"),
        (2*3600, "2 hours - Comments ordered"),
        (2.6*3600, "2.6 hours - Comment likes ordered"),
        (12*3600, "12 hours - Halfway point"),
        (24*3600, "24 hours - Complete")
    ]
    
    for time_sec, description in milestones:
        time_hours = time_sec / 3600
        orders_by_time = [o for o in order_times if (o['time'] - start_time).total_seconds() <= time_sec]
        views_by_time = sum(o['quantity'] for o in orders_by_time if o['service'] == 'Views')
        likes_by_time = sum(o['quantity'] for o in orders_by_time if o['service'] == 'Likes')
        
        print(f"  [{int(time_hours)}h] {description}")
        print(f"      Views: {views_by_time:,} | Likes: {likes_by_time}")
    
    print(f"\n{Fore.CYAN}Timeline:{Style.RESET_ALL}")
    print(f"  First order: {order_times[0]['time'].strftime('%H:%M:%S')}")
    print(f"  Last order: {order_times[-1]['time'].strftime('%H:%M:%S')}")
    print(f"  Duration: 24 hours")
    
    print(f"\n{Fore.YELLOW}This is a DRY RUN preview{Style.RESET_ALL}")
    print(f"{Fore.CYAN}When payment is confirmed, run:{Style.RESET_ALL}")
    print(f"  python run_delivery_bot.py \"{video_url}\"")

if __name__ == "__main__":
    main()


