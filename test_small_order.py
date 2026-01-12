#!/usr/bin/env python3
"""
Test with a small order to verify everything works
"""

import requests
import json
import time
from colorama import Fore, Style, init

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

test_url = "https://www.tiktok.com/@the.clips.origins/video/7589415681972538631"

print(f"""
{Fore.CYAN}╔══════════════════════════════════════════════╗
║   Testing Small Order                  ║
╚══════════════════════════════════════════════╝{Style.RESET_ALL}
""")

# Check balance first
print(f"{Fore.YELLOW}Step 1: Checking balance...{Style.RESET_ALL}")
try:
    response = requests.post(BASE_URL, data={'key': API_KEY, 'action': 'balance'}, timeout=10)
    if response.status_code == 200:
        data = response.json()
        balance = float(data.get('balance', 0)) if data.get('balance') else 0
        print(f"  {Fore.GREEN}✓ Balance: ${balance:.4f}{Style.RESET_ALL}")
        
        if balance < 0.01:
            print(f"\n{Fore.RED}✗ Insufficient balance for testing{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Need at least $0.01 to test{Style.RESET_ALL}")
            exit(1)
    else:
        print(f"  {Fore.RED}✗ Error checking balance: {response.status_code}{Style.RESET_ALL}")
        exit(1)
except Exception as e:
    print(f"  {Fore.RED}✗ Error: {e}{Style.RESET_ALL}")
    exit(1)

# Test 1: Small views order (cheapest)
print(f"\n{Fore.YELLOW}Step 2: Testing Views order (50 views = $0.0007)...{Style.RESET_ALL}")
try:
    response = requests.post(
        BASE_URL,
        data={
            'key': API_KEY,
            'action': 'add',  # All services use 'add', not 'order'
            'service': SERVICES['views'],
            'link': test_url,
            'quantity': MINIMUMS['views']
        },
        timeout=10
    )
    
    if response.status_code == 200:
        data = response.json()
        order_id = data.get('order', 0)
        error = data.get('error', '')
        
        if order_id and order_id != 0:
            print(f"  {Fore.GREEN}✓ SUCCESS! Order created: {order_id}{Style.RESET_ALL}")
            print(f"  {Fore.CYAN}Views order works!{Style.RESET_ALL}")
            
            # Check order status
            print(f"\n{Fore.YELLOW}Step 3: Checking order status...{Style.RESET_ALL}")
            time.sleep(2)
            status_response = requests.post(
                BASE_URL,
                data={
                    'key': API_KEY,
                    'action': 'status',
                    'order': order_id
                },
                timeout=10
            )
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"  {Fore.CYAN}Order Status:{Style.RESET_ALL}")
                print(f"    {json.dumps(status_data, indent=2)}")
            
            print(f"\n{Fore.GREEN}✓ Test successful! Bot is ready to run.{Style.RESET_ALL}")
        else:
            print(f"  {Fore.RED}✗ Failed: {error}{Style.RESET_ALL}")
            if 'balance' in error.lower():
                print(f"  {Fore.YELLOW}⚠ Check your balance{Style.RESET_ALL}")
    else:
        print(f"  {Fore.RED}✗ HTTP Error: {response.status_code}{Style.RESET_ALL}")
        print(f"  Response: {response.text[:200]}")
        
except Exception as e:
    print(f"  {Fore.RED}✗ Error: {e}{Style.RESET_ALL}")

print(f"\n{Fore.CYAN}Test complete!{Style.RESET_ALL}")

