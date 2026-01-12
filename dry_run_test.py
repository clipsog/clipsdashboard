#!/usr/bin/env python3
"""
Dry run test - shows what would happen without placing orders
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from colorama import Fore, Style, init

init(autoreset=True)

video_url = "https://www.tiktok.com/@the.clips.origins/video/7589415681972538631"

print(f"""
    {Fore.CYAN}╔══════════════════════════════════════════════╗
    ║   Dry Run Test - No Orders Will Be Placed ║
    ╚══════════════════════════════════════════════╝{Style.RESET_ALL}
    """)

print(f"Video: {video_url}\n")

# Load purchase schedule
schedule_file = Path(__file__).parent / 'purchase_schedule.json'
with open(schedule_file, 'r') as f:
    purchases = json.load(f)

print(f"{Fore.CYAN}Purchase Schedule:{Style.RESET_ALL}")
print(f"  Total purchases: {len(purchases)}")
print(f"  Duration: 24 hours")
print(f"  First order: {purchases[0]['time_str']}")
print(f"  Last order: {purchases[-1]['time_str']}\n")

# Group by service
views_orders = [p for p in purchases if p['service'] == 'Views']
likes_orders = [p for p in purchases if p['service'] == 'Likes']
comments_orders = [p for p in purchases if p['service'] == 'Comments']
comment_likes_orders = [p for p in purchases if p['service'] == 'Comment Likes']

print(f"{Fore.CYAN}Order Breakdown:{Style.RESET_ALL}")
print(f"  Views: {len(views_orders)} orders (50 views each)")
print(f"  Likes: {len(likes_orders)} orders")
print(f"  Comments: {len(comments_orders)} orders (10 comments)")
print(f"  Comment Likes: {len(comment_likes_orders)} orders (50 likes)\n")

# Show first 10 purchases
print(f"{Fore.CYAN}First 10 Purchases (what would happen):{Style.RESET_ALL}\n")
for i, purchase in enumerate(purchases[:10]):
    print(f"  [{purchase['time_str']}] {purchase['service']}: {purchase['quantity']}")

print(f"\n  ... and {len(purchases) - 10} more purchases\n")

# Cost calculation
rates = {'views': 0.0140, 'likes': 0.2100, 'comments': 13.5000, 'comment_likes': 0.2100}
total_cost = 0

for purchase in purchases:
    service = purchase['service'].lower().replace(' ', '_')
    quantity = purchase['quantity']
    cost = (quantity / 1000.0) * rates.get(service, 0)
    total_cost += cost

print(f"{Fore.GREEN}Total Cost: ${total_cost:.4f}{Style.RESET_ALL}\n")

print(f"{Fore.YELLOW}This is a DRY RUN - no orders will be placed{Style.RESET_ALL}")
print(f"{Fore.CYAN}To start real delivery, run:{Style.RESET_ALL}")
print(f"  python run_delivery_bot.py \"{video_url}\"")


