#!/usr/bin/env python3
"""
Test to understand how comment likes work - which comment gets liked?
"""

import requests
import json
from colorama import Fore, Style, init

init(autoreset=True)

API_KEY = "3327db2d9f02b8c241b200a40fe3d12d"
BASE_URL = "https://smmfollows.com/api/v2"
COMMENT_LIKES_SERVICE_ID = "14718"

test_url = "https://www.tiktok.com/@the.clips.origins/video/7589415681972538631"

print(f"{Fore.CYAN}Testing Comment Likes Behavior{Style.RESET_ALL}\n")
print(f"Question: If a user has multiple comments, which one gets liked?\n")

# Check balance first
print(f"{Fore.YELLOW}Step 1: Checking balance...{Style.RESET_ALL}")
try:
    response = requests.post(BASE_URL, data={'key': API_KEY, 'action': 'balance'}, timeout=10)
    if response.status_code == 200:
        data = response.json()
        balance = float(data.get('balance', 0)) if data.get('balance') else 0
        print(f"  Balance: ${balance:.4f}")
        
        if balance < 0.01:
            print(f"\n{Fore.YELLOW}⚠ Not enough balance to test. Need at least $0.01{Style.RESET_ALL}")
            print(f"{Fore.CYAN}But we can still check the API documentation...{Style.RESET_ALL}\n")
    else:
        print(f"  Error: {response.status_code}")
except Exception as e:
    print(f"  Error: {e}")

print(f"\n{Fore.YELLOW}What We Know:{Style.RESET_ALL}")
print(f"  - API requires: video URL + username")
print(f"  - Username = TikTok username of comment owner")
print(f"  - But: What if user has MULTIPLE comments on the video?\n")

print(f"{Fore.YELLOW}Possible Behaviors:{Style.RESET_ALL}")
print(f"  1. Likes the FIRST comment from that user")
print(f"  2. Likes the MOST RECENT comment from that user")
print(f"  3. Likes ALL comments from that user (distributes likes)")
print(f"  4. Requires additional parameter (comment ID) - but docs don't mention it\n")

print(f"{Fore.CYAN}Best Strategy:{Style.RESET_ALL}")
print(f"  Since we don't know for sure, here's what to do:\n")
print(f"  1. {Fore.GREEN}Post YOUR OWN comment first{Style.RESET_ALL}")
print(f"     - Before starting the bot, comment on your video")
print(f"     - Use your TikTok username")
print(f"     - This ensures you control which comment gets boosted\n")
print(f"  2. {Fore.GREEN}Use YOUR username when prompted{Style.RESET_ALL}")
print(f"     - At 2,600 views milestone, enter YOUR TikTok username")
print(f"     - The API will like YOUR comment\n")
print(f"  3. {Fore.YELLOW}If you want to boost someone else's comment:{Style.RESET_ALL}")
print(f"     - Make sure they only have ONE comment on the video")
print(f"     - Or test with a small order first to see behavior\n")

# Try to find more info in API docs or test
print(f"\n{Fore.YELLOW}Testing API call format...{Style.RESET_ALL}")
print(f"  Video: {test_url}")
print(f"  Username: the.clips.origins (example)")
print(f"  Quantity: 50 likes\n")

if balance >= 0.01:
    print(f"{Fore.GREEN}You have balance - we can test!{Style.RESET_ALL}")
    print(f"{Fore.YELLOW}Would you like to place a small test order?{Style.RESET_ALL}")
    print(f"  Cost: ~$0.01 (50 likes minimum)")
    print(f"  This will show us exactly how it works\n")
else:
    print(f"{Fore.CYAN}Once you have balance, we can test with a small order{Style.RESET_ALL}")
    print(f"  to see exactly which comment gets liked.\n")

print(f"{Fore.CYAN}Recommendation:{Style.RESET_ALL}")
print(f"  For now, use YOUR OWN comment to be safe.")
print(f"  Post a comment before starting the bot, then use your username.")


