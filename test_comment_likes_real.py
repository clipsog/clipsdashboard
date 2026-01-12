#!/usr/bin/env python3
"""
Test Comment Likes API with documented parameters to verify it works
"""

import requests
import json
from colorama import Fore, Style, init

init(autoreset=True)

API_KEY = "3327db2d9f02b8c241b200a40fe3d12d"
BASE_URL = "https://smmfollows.com/api/v2"
COMMENT_LIKES_SERVICE_ID = "14718"
test_url = "https://www.tiktok.com/@the.clips.origins/video/7589415681972538631"
test_username = "the.clips.origins"

print(f"{Fore.CYAN}Testing Comment Likes API with Documented Parameters{Style.RESET_ALL}\n")
print(f"Based on API docs at smmfollows.com/api:")
print(f"  - action: 'add' (not 'order')")
print(f"  - username: Required")
print(f"  - service: {COMMENT_LIKES_SERVICE_ID}")
print(f"  - link: {test_url}")
print(f"  - quantity: 50")
print(f"  - username: {test_username}\n")

# Test 1: With documented parameters
print(f"{Fore.YELLOW}Test 1: Using documented parameters (action='add', username provided){Style.RESET_ALL}")
try:
    response = requests.post(
        BASE_URL,
        data={
            'key': API_KEY,
            'action': 'add',  # As per docs
            'service': COMMENT_LIKES_SERVICE_ID,
            'link': test_url,
            'quantity': 50,
            'username': test_username  # As per docs
        },
        timeout=10
    )
    
    print(f"  Status: {response.status_code}")
    print(f"  Response: {response.text}")
    
    try:
        data = response.json()
        print(f"  JSON: {json.dumps(data, indent=2)}")
        
        if response.status_code == 200:
            order_id = data.get('order', 0) or data.get('id', 0)
            if order_id and order_id != 0:
                print(f"\n  {Fore.GREEN}✓ SUCCESS! Order created: {order_id}{Style.RESET_ALL}")
                print(f"  {Fore.GREEN}API works as documented!{Style.RESET_ALL}")
            else:
                error = data.get('error', 'Unknown')
                print(f"\n  {Fore.YELLOW}Response received but:{Style.RESET_ALL}")
                print(f"    Error: {error}")
                if 'balance' in error.lower() or 'insufficient' in error.lower():
                    print(f"    {Fore.CYAN}→ This is expected - account has $0 balance{Style.RESET_ALL}")
                    print(f"    {Fore.GREEN}→ But API accepted the parameters!{Style.RESET_ALL}")
                elif 'username' in error.lower():
                    print(f"    {Fore.RED}→ Username parameter might be wrong{Style.RESET_ALL}")
                else:
                    print(f"    {Fore.YELLOW}→ Need to investigate this error{Style.RESET_ALL}")
        else:
            print(f"  {Fore.RED}HTTP Error: {response.status_code}{Style.RESET_ALL}")
    except Exception as e:
        print(f"  {Fore.RED}JSON Parse Error: {e}{Style.RESET_ALL}")
        print(f"  Raw response: {response.text[:500]}")
        
except Exception as e:
    print(f"  {Fore.RED}Request Error: {e}{Style.RESET_ALL}")

print("\n" + "="*60 + "\n")

# Test 2: Compare with 'order' action (wrong)
print(f"{Fore.YELLOW}Test 2: Using 'order' action (wrong - for comparison){Style.RESET_ALL}")
try:
    response = requests.post(
        BASE_URL,
        data={
            'key': API_KEY,
            'action': 'order',  # Wrong action
            'service': COMMENT_LIKES_SERVICE_ID,
            'link': test_url,
            'quantity': 50,
            'username': test_username
        },
        timeout=10
    )
    
    print(f"  Status: {response.status_code}")
    try:
        data = response.json()
        error = data.get('error', '')
        print(f"  Error: {error}")
        if 'incorrect' in error.lower():
            print(f"  {Fore.RED}→ Confirms 'order' doesn't work for comment likes{Style.RESET_ALL}")
    except:
        print(f"  Response: {response.text[:200]}")
        
except Exception as e:
    print(f"  Error: {e}")

print("\n" + "="*60 + "\n")

# Test 3: Without username (should fail)
print(f"{Fore.YELLOW}Test 3: Without username (should fail){Style.RESET_ALL}")
try:
    response = requests.post(
        BASE_URL,
        data={
            'key': API_KEY,
            'action': 'add',
            'service': COMMENT_LIKES_SERVICE_ID,
            'link': test_url,
            'quantity': 50
            # No username
        },
        timeout=10
    )
    
    print(f"  Status: {response.status_code}")
    try:
        data = response.json()
        error = data.get('error', '')
        print(f"  Error: {error}")
        if 'username' in error.lower() or 'required' in error.lower():
            print(f"  {Fore.GREEN}→ Confirms username is required{Style.RESET_ALL}")
        elif 'incorrect' in error.lower():
            print(f"  {Fore.YELLOW}→ Generic error (might be missing username){Style.RESET_ALL}")
    except:
        print(f"  Response: {response.text[:200]}")
        
except Exception as e:
    print(f"  Error: {e}")

print(f"\n{Fore.CYAN}Summary:{Style.RESET_ALL}")
print(f"  - If Test 1 succeeds or gives balance error → API works as documented")
print(f"  - If Test 1 gives 'Incorrect request' → Need to investigate further")
print(f"  - If Test 2 gives different error → Confirms 'add' vs 'order' matters")
print(f"  - If Test 3 requires username → Confirms username is mandatory")


