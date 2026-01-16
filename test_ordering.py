#!/usr/bin/env python3
"""
Test script to identify errors when placing orders
Run this to see the exact error you're getting
"""

import sys
from pathlib import Path
from colorama import Fore, Style, init

init(autoreset=True)

print(f"""
{Fore.CYAN}╔══════════════════════════════════════════════════╗
║   Ordering Test Script                           ║
╚══════════════════════════════════════════════════╝{Style.RESET_ALL}
""")

# Test 1: Check imports
print(f"{Fore.CYAN}Test 1: Checking imports...{Style.RESET_ALL}")
try:
    from run_delivery_bot import DeliveryBot
    print(f"{Fore.GREEN}✓ DeliveryBot imported successfully{Style.RESET_ALL}")
except Exception as e:
    print(f"{Fore.RED}✗ Failed to import DeliveryBot: {e}{Style.RESET_ALL}")
    sys.exit(1)

# Test 2: Check purchase schedule
print(f"\n{Fore.CYAN}Test 2: Checking purchase_schedule.json...{Style.RESET_ALL}")
schedule_file = Path(__file__).parent / 'purchase_schedule.json'
if schedule_file.exists():
    print(f"{Fore.GREEN}✓ purchase_schedule.json found{Style.RESET_ALL}")
    try:
        import json
        with open(schedule_file, 'r') as f:
            schedule = json.load(f)
        print(f"{Fore.GREEN}✓ Schedule loaded: {len(schedule)} orders{Style.RESET_ALL}")
    except Exception as e:
        print(f"{Fore.RED}✗ Failed to load schedule: {e}{Style.RESET_ALL}")
else:
    print(f"{Fore.RED}✗ purchase_schedule.json not found{Style.RESET_ALL}")

# Test 3: Check progress.json
print(f"\n{Fore.CYAN}Test 3: Checking progress.json...{Style.RESET_ALL}")
progress_file = Path.home() / '.smmfollows_bot' / 'progress.json'
if progress_file.exists():
    print(f"{Fore.GREEN}✓ progress.json found at {progress_file}{Style.RESET_ALL}")
    try:
        import json
        with open(progress_file, 'r') as f:
            progress = json.load(f)
        print(f"{Fore.GREEN}✓ Progress loaded: {len(progress)} videos{Style.RESET_ALL}")
        
        # Show first video
        if progress:
            first_url = list(progress.keys())[0]
            first_video = progress[first_url]
            print(f"\n{Fore.CYAN}First video:{Style.RESET_ALL}")
            print(f"  URL: {first_url[:80]}...")
            print(f"  Has start_time: {bool(first_video.get('start_time'))}")
            print(f"  Status: {first_video.get('status', 'active')}")
    except Exception as e:
        print(f"{Fore.RED}✗ Failed to load progress: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
else:
    print(f"{Fore.RED}✗ progress.json not found at {progress_file}{Style.RESET_ALL}")
    print(f"   Run: python run_delivery_bot.py YOUR_VIDEO_URL")

# Test 4: Check API configuration
print(f"\n{Fore.CYAN}Test 4: Checking API configuration...{Style.RESET_ALL}")
try:
    from run_delivery_bot import API_KEY, BASE_URL, SERVICES
    print(f"{Fore.GREEN}✓ API_KEY: {API_KEY[:10]}...{Style.RESET_ALL}")
    print(f"{Fore.GREEN}✓ BASE_URL: {BASE_URL}{Style.RESET_ALL}")
    print(f"{Fore.GREEN}✓ SERVICES: {list(SERVICES.keys())}{Style.RESET_ALL}")
except Exception as e:
    print(f"{Fore.RED}✗ API configuration error: {e}{Style.RESET_ALL}")

# Test 5: Try to create a DeliveryBot instance
print(f"\n{Fore.CYAN}Test 5: Creating DeliveryBot instance...{Style.RESET_ALL}")
if progress and list(progress.keys()):
    test_url = list(progress.keys())[0]
    try:
        bot = DeliveryBot(test_url)
        print(f"{Fore.GREEN}✓ DeliveryBot created successfully{Style.RESET_ALL}")
        
        # Test 6: Try to check for due orders
        print(f"\n{Fore.CYAN}Test 6: Testing check_and_place_due_orders()...{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}(This will attempt to place real orders if any are due!){Style.RESET_ALL}")
        
        try:
            result = bot.check_and_place_due_orders()
            if result:
                print(f"{Fore.GREEN}✓ Orders placed successfully!{Style.RESET_ALL}")
            else:
                print(f"{Fore.YELLOW}No orders were due{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}✗ ERROR when checking/placing orders:{Style.RESET_ALL}")
            print(f"{Fore.RED}Error type: {type(e).__name__}{Style.RESET_ALL}")
            print(f"{Fore.RED}Error message: {str(e)}{Style.RESET_ALL}")
            print(f"\n{Fore.RED}Full traceback:{Style.RESET_ALL}")
            import traceback
            traceback.print_exc()
            print(f"\n{Fore.YELLOW}This is the error you're seeing when timers reach 0!{Style.RESET_ALL}")
            
    except Exception as e:
        print(f"{Fore.RED}✗ Failed to create DeliveryBot: {e}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
else:
    print(f"{Fore.YELLOW}⚠ No videos in progress.json, skipping bot creation test{Style.RESET_ALL}")

print(f"\n{Fore.CYAN}{'='*60}")
print(f"Test Complete")
print(f"{'='*60}{Style.RESET_ALL}")
print(f"\nIf you saw an error in Test 6, that's the error causing your timer issues.")
print(f"Copy the error message and traceback to help with debugging.")
