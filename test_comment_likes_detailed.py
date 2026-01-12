#!/usr/bin/env python3
"""
Detailed test of comment likes API to understand exact requirements
"""

import requests
import json
from colorama import Fore, Style, init

init(autoreset=True)

API_KEY = "3327db2d9f02b8c241b200a40fe3d12d"
BASE_URL = "https://smmfollows.com/api/v2"
COMMENT_LIKES_SERVICE_ID = "14718"

test_url = "https://www.tiktok.com/@the.clips.origins/video/7589415681972538631"

print(f"{Fore.CYAN}Testing Comment Likes API - What Parameters Does It Need?{Style.RESET_ALL}\n")
print(f"Service: TikTok Comments Likes | By Username")
print(f"Service ID: {COMMENT_LIKES_SERVICE_ID}")
print(f"Video URL: {test_url}\n")

# Test different parameter combinations
test_cases = [
    {
        'name': 'Test 1: Video URL only',
        'data': {
            'key': API_KEY,
            'action': 'order',
            'service': COMMENT_LIKES_SERVICE_ID,
            'link': test_url,
            'quantity': 50
        }
    },
    {
        'name': 'Test 2: Video URL + username',
        'data': {
            'key': API_KEY,
            'action': 'order',
            'service': COMMENT_LIKES_SERVICE_ID,
            'link': test_url,
            'quantity': 50,
            'username': 'the.clips.origins'
        }
    },
    {
        'name': 'Test 3: Video URL + usernames (plural)',
        'data': {
            'key': API_KEY,
            'action': 'order',
            'service': COMMENT_LIKES_SERVICE_ID,
            'link': test_url,
            'quantity': 50,
            'usernames': 'the.clips.origins'
        }
    },
    {
        'name': 'Test 4: Video URL + comment_username',
        'data': {
            'key': API_KEY,
            'action': 'order',
            'service': COMMENT_LIKES_SERVICE_ID,
            'link': test_url,
            'quantity': 50,
            'comment_username': 'the.clips.origins'
        }
    },
    {
        'name': 'Test 5: Video URL + comment_id',
        'data': {
            'key': API_KEY,
            'action': 'order',
            'service': COMMENT_LIKES_SERVICE_ID,
            'link': test_url,
            'quantity': 50,
            'comment_id': '1234567890'
        }
    },
    {
        'name': 'Test 6: Video URL + target',
        'data': {
            'key': API_KEY,
            'action': 'order',
            'service': COMMENT_LIKES_SERVICE_ID,
            'link': test_url,
            'quantity': 50,
            'target': 'the.clips.origins'
        }
    }
]

print(f"{Fore.YELLOW}Testing different parameter combinations...{Style.RESET_ALL}\n")

for i, test_case in enumerate(test_cases, 1):
    print(f"{Fore.CYAN}{test_case['name']}{Style.RESET_ALL}")
    try:
        response = requests.post(
            BASE_URL,
            data=test_case['data'],
            timeout=10
        )
        
        print(f"  Status: {response.status_code}")
        
        try:
            data = response.json()
            if response.status_code == 200:
                order_id = data.get('order', 0)
                if order_id and order_id != 0:
                    print(f"  {Fore.GREEN}✓ SUCCESS! Order ID: {order_id}{Style.RESET_ALL}")
                    print(f"  {Fore.GREEN}This parameter combination works!{Style.RESET_ALL}")
                    print(f"\n{Fore.CYAN}Working parameters:{Style.RESET_ALL}")
                    for key, value in test_case['data'].items():
                        if key != 'key':
                            print(f"  - {key}: {value}")
                    break
                else:
                    error = data.get('error', 'Unknown')
                    print(f"  {Fore.RED}✗ Error: {error}{Style.RESET_ALL}")
            else:
                error = data.get('error', response.text[:100])
                print(f"  {Fore.RED}✗ Error: {error}{Style.RESET_ALL}")
        except:
            print(f"  {Fore.RED}✗ Invalid JSON: {response.text[:200]}{Style.RESET_ALL}")
            
    except Exception as e:
        print(f"  {Fore.RED}✗ Exception: {e}{Style.RESET_ALL}")
    
    print()

# Also check service details for hints
print(f"\n{Fore.CYAN}Checking service details for hints...{Style.RESET_ALL}")
try:
    response = requests.post(
        BASE_URL,
        data={
            'key': API_KEY,
            'action': 'services'
        },
        timeout=10
    )
    if response.status_code == 200:
        services = response.json()
        for service in services:
            if str(service.get('service')) == COMMENT_LIKES_SERVICE_ID:
                print(f"\n{Fore.GREEN}Service Details:{Style.RESET_ALL}")
                print(json.dumps(service, indent=2))
                print(f"\n{Fore.YELLOW}Service Name: {service.get('name', 'N/A')}{Style.RESET_ALL}")
                print(f"{Fore.YELLOW}Service Type: {service.get('type', 'N/A')}{Style.RESET_ALL}")
                break
except Exception as e:
    print(f"Error: {e}")

print(f"\n{Fore.CYAN}Note: These are test calls. No actual orders will be placed.{Style.RESET_ALL}")
print(f"{Fore.YELLOW}If all tests fail, the API may require:{Style.RESET_ALL}")
print(f"  - Account balance (currently $0)")
print(f"  - Different parameter name")
print(f"  - Comment ID instead of username")
print(f"  - Multiple parameters together")


