#!/usr/bin/env python3
"""
Thorough API testing to determine exact parameters needed
"""

import requests
import json
from colorama import Fore, Style, init

init(autoreset=True)

API_KEY = "3327db2d9f02b8c241b200a40fe3d12d"
BASE_URL = "https://smmfollows.com/api/v2"
COMMENT_LIKES_SERVICE_ID = "14718"
test_url = "https://www.tiktok.com/@the.clips.origins/video/7589415681972538631"

print(f"{Fore.CYAN}Thorough API Testing for Comment Likes{Style.RESET_ALL}\n")

# Test 1: Check balance first
print(f"{Fore.YELLOW}Test 1: Check Balance{Style.RESET_ALL}")
try:
    response = requests.post(BASE_URL, data={'key': API_KEY, 'action': 'balance'}, timeout=10)
    if response.status_code == 200:
        data = response.json()
        balance = data.get('balance', 0)
        print(f"  Balance: ${balance}")
        if float(balance) == 0:
            print(f"  {Fore.RED}⚠ No balance - API will reject orders{Style.RESET_ALL}")
            print(f"  {Fore.YELLOW}But we can still check error messages for clues{Style.RESET_ALL}")
    else:
        print(f"  Status: {response.status_code}")
except Exception as e:
    print(f"  Error: {e}")

print()

# Test 2: Get service details with all fields
print(f"{Fore.YELLOW}Test 2: Get Full Service Details{Style.RESET_ALL}")
try:
    response = requests.post(BASE_URL, data={'key': API_KEY, 'action': 'services'}, timeout=10)
    if response.status_code == 200:
        services = response.json()
        for service in services:
            if str(service.get('service')) == COMMENT_LIKES_SERVICE_ID:
                print(f"  Full service object:")
                print(json.dumps(service, indent=2))
                # Check for any hints about required fields
                if 'name' in service:
                    name = service['name']
                    print(f"\n  Service name analysis:")
                    print(f"    - Contains 'By Username': {'By Username' in name}")
                    print(f"    - Full name: {name}")
                break
except Exception as e:
    print(f"  Error: {e}")

print()

# Test 3: Try order with minimal params and capture full error
print(f"{Fore.YELLOW}Test 3: Order with Video URL Only (Capture Full Error){Style.RESET_ALL}")
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
    print(f"  Status: {response.status_code}")
    print(f"  Full response:")
    print(f"    Headers: {dict(response.headers)}")
    print(f"    Text: {response.text}")
    try:
        data = response.json()
        print(f"    JSON: {json.dumps(data, indent=2)}")
    except:
        print(f"    (Not JSON)")
except Exception as e:
    print(f"  Error: {e}")

print()

# Test 4: Check if there's a validation/status endpoint
print(f"{Fore.YELLOW}Test 4: Check for Validation Endpoints{Style.RESET_ALL}")
validation_actions = ['validate', 'check', 'status', 'info', 'details']
for action in validation_actions:
    try:
        response = requests.post(
            BASE_URL,
            data={
                'key': API_KEY,
                'action': action,
                'service': COMMENT_LIKES_SERVICE_ID
            },
            timeout=5
        )
        if response.status_code != 404:
            print(f"  {action}: Status {response.status_code}")
            print(f"    Response: {response.text[:200]}")
    except:
        pass

print()

# Test 5: Check API documentation endpoint
print(f"{Fore.YELLOW}Test 5: Check for API Documentation{Style.RESET_ALL}")
doc_endpoints = [
    '/api',
    '/api/docs',
    '/api/documentation',
    '/api/v2/docs',
    '/help',
    '/api/help'
]
for endpoint in doc_endpoints:
    try:
        url = BASE_URL.replace('/api/v2', '') + endpoint
        response = requests.get(url, timeout=5)
        if response.status_code == 200 and len(response.text) > 100:
            print(f"  Found docs at: {url}")
            # Look for comment likes mentions
            if 'comment' in response.text.lower() or '14718' in response.text:
                print(f"    Contains comment-related info!")
    except:
        pass

print()

# Test 6: Try common SMM panel parameter patterns
print(f"{Fore.YELLOW}Test 6: Try Common Parameter Patterns{Style.RESET_ALL}")
common_patterns = [
    {'username': 'test_user'},
    {'usernames': 'test_user'},
    {'target': 'test_user'},
    {'comment_username': 'test_user'},
    {'comment_user': 'test_user'},
    {'user': 'test_user'},
    {'comment_id': '123456'},
    {'cid': '123456'},
    {'comment': '123456'},
    {'link2': test_url},  # Some panels use link2 for secondary link
    {'url': test_url},
    {'post_url': test_url},
]

for i, extra_params in enumerate(common_patterns[:5], 1):  # Test first 5 to avoid too many requests
    try:
        data = {
            'key': API_KEY,
            'action': 'order',
            'service': COMMENT_LIKES_SERVICE_ID,
            'link': test_url,
            'quantity': 50
        }
        data.update(extra_params)
        
        response = requests.post(BASE_URL, data=data, timeout=10)
        if response.status_code == 200:
            result = response.json()
            order_id = result.get('order', 0)
            if order_id and order_id != 0:
                print(f"  {Fore.GREEN}✓ SUCCESS with: {extra_params}{Style.RESET_ALL}")
                print(f"    Order ID: {order_id}")
                break
        else:
            error = response.json().get('error', '') if response.status_code == 200 else response.text[:100]
            # Look for specific error messages that might hint at missing params
            if 'username' in error.lower() or 'user' in error.lower():
                print(f"  Pattern {i} ({list(extra_params.keys())[0]}): Error mentions username/user")
            elif 'comment' in error.lower():
                print(f"  Pattern {i} ({list(extra_params.keys())[0]}): Error mentions comment")
    except Exception as e:
        pass

print()

# Test 7: Compare with comments service (we know it works differently)
print(f"{Fore.YELLOW}Test 7: Compare with Comments Service Structure{Style.RESET_ALL}")
try:
    # Try comments order to see what works
    response = requests.post(
        BASE_URL,
        data={
            'key': API_KEY,
            'action': 'order',
            'service': '1384',  # Comments service
            'link': test_url,
            'quantity': 10
        },
        timeout=10
    )
    print(f"  Comments service test:")
    print(f"    Status: {response.status_code}")
    print(f"    Response: {response.text[:200]}")
    # If comments gives different error, it might hint at structure
except Exception as e:
    print(f"  Error: {e}")

print(f"\n{Fore.CYAN}Testing complete. Analyzing results...{Style.RESET_ALL}")


