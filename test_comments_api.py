#!/usr/bin/env python3
"""
Test comments API to see what parameters are needed for comment text
"""

import requests
import json
from colorama import Fore, Style, init

init(autoreset=True)

API_KEY = "3327db2d9f02b8c241b200a40fe3d12d"
BASE_URL = "https://smmfollows.com/api/v2"
COMMENTS_SERVICE_ID = "1384"

# Test video URL
test_url = "https://www.tiktok.com/@the.clips.origins/video/7589415681972538631"

# Sample comments (one per line as user mentioned)
sample_comments = [
    "Great video!",
    "Love this!",
    "Amazing content!",
    "So good!",
    "🔥🔥🔥",
    "This is awesome!",
    "Keep it up!",
    "Best one yet!",
    "Incredible!",
    "Perfect!"
]

print(f"{Fore.CYAN}Testing Comments API Parameters{Style.RESET_ALL}\n")
print(f"Service ID: {COMMENTS_SERVICE_ID}")
print(f"Video URL: {test_url}")
print(f"Comments to send: {len(sample_comments)} comments\n")

# Test 1: Standard order (current implementation)
print(f"{Fore.YELLOW}Test 1: Standard order (no comment text){Style.RESET_ALL}")
try:
    response = requests.post(
        BASE_URL,
        data={
            'key': API_KEY,
            'action': 'order',
            'service': COMMENTS_SERVICE_ID,
            'link': test_url,
            'quantity': 10
        },
        timeout=10
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*60 + "\n")

# Test 2: Try with 'comments' parameter
print(f"{Fore.YELLOW}Test 2: With 'comments' parameter (one per line){Style.RESET_ALL}")
try:
    comments_text = "\n".join(sample_comments)
    response = requests.post(
        BASE_URL,
        data={
            'key': API_KEY,
            'action': 'order',
            'service': COMMENTS_SERVICE_ID,
            'link': test_url,
            'quantity': 10,
            'comments': comments_text
        },
        timeout=10
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*60 + "\n")

# Test 3: Try with 'comment' parameter (singular)
print(f"{Fore.YELLOW}Test 3: With 'comment' parameter{Style.RESET_ALL}")
try:
    comments_text = "\n".join(sample_comments)
    response = requests.post(
        BASE_URL,
        data={
            'key': API_KEY,
            'action': 'order',
            'service': COMMENTS_SERVICE_ID,
            'link': test_url,
            'quantity': 10,
            'comment': comments_text
        },
        timeout=10
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*60 + "\n")

# Test 4: Try with 'comments_list' parameter
print(f"{Fore.YELLOW}Test 4: With 'comments_list' parameter{Style.RESET_ALL}")
try:
    comments_text = "\n".join(sample_comments)
    response = requests.post(
        BASE_URL,
        data={
            'key': API_KEY,
            'action': 'order',
            'service': COMMENTS_SERVICE_ID,
            'link': test_url,
            'quantity': 10,
            'comments_list': comments_text
        },
        timeout=10
    )
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "="*60 + "\n")

# Test 5: Check service details to see if it shows comment requirements
print(f"{Fore.YELLOW}Test 5: Get service details{Style.RESET_ALL}")
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
        # Find comments service
        for service in data:
            if str(service.get('service')) == COMMENTS_SERVICE_ID:
                print(f"Service Details:")
                print(json.dumps(service, indent=2))
                break
except Exception as e:
    print(f"Error: {e}")

print(f"\n{Fore.CYAN}Note: These are test calls. No actual orders will be placed.{Style.RESET_ALL}")


