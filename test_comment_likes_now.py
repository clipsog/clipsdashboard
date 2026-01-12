#!/usr/bin/env python3
"""
Test comment likes with a real order to see how it works
"""

import requests
import json
from colorama import Fore, Style, init

init(autoreset=True)

API_KEY = "3327db2d9f02b8c241b200a40fe3d12d"
BASE_URL = "https://smmfollows.com/api/v2"
COMMENT_LIKES_SERVICE_ID = "14718"

test_url = "https://www.tiktok.com/@the.clips.origins/video/7589415681972538631"

print(f"""
{Fore.CYAN}╔══════════════════════════════════════════════╗
║   Test Comment Likes Behavior         ║
╚══════════════════════════════════════════════╝{Style.RESET_ALL}
""")

print(f"{Fore.YELLOW}This will place a REAL order to test how comment likes work.{Style.RESET_ALL}")
print(f"Cost: ~$0.01 (50 likes minimum)\n")

# Check balance
response = requests.post(BASE_URL, data={'key': API_KEY, 'action': 'balance'}, timeout=10)
if response.status_code == 200:
    data = response.json()
    balance = float(data.get('balance', 0)) if data.get('balance') else 0
    print(f"Balance: ${balance:.4f}\n")

# Get username from user
print(f"{Fore.CYAN}Enter the TikTok username whose comment you want to test:{Style.RESET_ALL}")
print(f"{Fore.YELLOW}(This should be a user who has commented on your video){Style.RESET_ALL}")
print(f"{Fore.CYAN}Username (without @): {Style.RESET_ALL}", end="")

try:
    username = input().strip()
    if not username:
        print(f"\n{Fore.RED}No username provided. Exiting.{Style.RESET_ALL}")
        exit(1)
    
    print(f"\n{Fore.YELLOW}Placing test order...{Style.RESET_ALL}")
    print(f"  Video: {test_url}")
    print(f"  Username: {username}")
    print(f"  Quantity: 50 likes\n")
    
    response = requests.post(
        BASE_URL,
        data={
            'key': API_KEY,
            'action': 'add',
            'service': COMMENT_LIKES_SERVICE_ID,
            'link': test_url,
            'quantity': 50,
            'username': username
        },
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        order_id = data.get('order', 0)
        error = data.get('error', '')
        
        if order_id and order_id != 0:
            print(f"{Fore.GREEN}✓ Order created: {order_id}{Style.RESET_ALL}\n")
            print(f"{Fore.CYAN}Next steps:{Style.RESET_ALL}")
            print(f"  1. Check your TikTok video comments")
            print(f"  2. See which comment from @{username} got the likes")
            print(f"  3. This will tell us how the API behaves:\n")
            print(f"     - If FIRST comment got likes → API likes oldest comment")
            print(f"     - If MOST RECENT got likes → API likes newest comment")
            print(f"     - If ALL comments got likes → API distributes across all")
            print(f"     - If specific comment → Need to investigate further\n")
            print(f"{Fore.YELLOW}Check back in a few minutes to see the results!{Style.RESET_ALL}")
        else:
            print(f"{Fore.RED}✗ Error: {error}{Style.RESET_ALL}")
    else:
        print(f"{Fore.RED}✗ HTTP Error: {response.status_code}{Style.RESET_ALL}")
        print(f"Response: {response.text}")
        
except KeyboardInterrupt:
    print(f"\n{Fore.YELLOW}Cancelled.{Style.RESET_ALL}")
except Exception as e:
    print(f"\n{Fore.RED}Error: {e}{Style.RESET_ALL}")


