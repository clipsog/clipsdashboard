#!/usr/bin/env python3
"""
Test comment likes API to understand what parameters are needed
"""

import requests
import json
from colorama import Fore, Style, init

init(autoreset=True)

API_KEY = "3327db2d9f02b8c241b200a40fe3d12d"
BASE_URL = "https://smmfollows.com/api/v2"
COMMENT_LIKES_SERVICE_ID = "14718"

# Test video URL
test_url = "https://www.tiktok.com/@the.clips.origins/video/7589415681972538631"

print(f"{Fore.CYAN}Testing Comment Likes API{Style.RESET_ALL}\n")
print(f"Service ID: {COMMENT_LIKES_SERVICE_ID}")
print(f"Video URL: {test_url}")
print(f"Note: Service description says 'comments likes by username' but has post link field\n")

# Test 1: Standard order (just video URL)
print(f"{Fore.YELLOW}Test 1: Standard order (video URL only){Style.RESET_ALL}")
try:
    response = requests.post(
        BASE_URL,
        data={
            'key': API_KEY,
            'action': 'order',
            'service': COMMENT_LIKES_SERVICE_ID,
            'link': test_url,
            'quantity': 50
        },
        timeout=10
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*60 + "\n")

# Test 2: Get service details
print(f"{Fore.YELLOW}Test 2: Get service details{Style.RESET_ALL}")
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
        data = response.json()
        # Find comment likes service
        for service in data:
            if str(service.get('service')) == COMMENT_LIKES_SERVICE_ID:
                print(f"Service Details:")
                print(json.dumps(service, indent=2))
                print(f"\n{Fore.CYAN}Service Name: {service.get('name', 'N/A')}{Style.RESET_ALL}")
                print(f"{Fore.CYAN}Service Type: {service.get('type', 'N/A')}{Style.RESET_ALL}")
                print(f"{Fore.CYAN}Description/Notes: Check if it mentions username requirement{Style.RESET_ALL}")
                break
except Exception as e:
    print(f"Error: {e}")

print(f"\n{Fore.CYAN}Note: These are test calls. No actual orders will be placed.{Style.RESET_ALL}")
print(f"\n{Fore.YELLOW}Question: Does the service need:{Style.RESET_ALL}")
print(f"  1. Just the video URL? (current implementation)")
print(f"  2. A specific comment ID/username?")
print(f"  3. The first comment on the video?")
print(f"  4. A random comment?")


