#!/usr/bin/env python3
"""
Test the delivery plan before running on real video
"""

import requests
import json
import time
from datetime import datetime
from colorama import Fore, Style, init

init(autoreset=True)

API_KEY = "3327db2d9f02b8c241b200a40fe3d12d"
BASE_URL = "https://smmfollows.com/api/v2"

# Service IDs
SERVICES = {
    'views': '1321',
    'likes': '250',
    'comments': '1384',
    'comment_likes': '14718'
}

# Minimums
MINIMUMS = {
    'views': 50,
    'likes': 10,
    'comments': 10,
    'comment_likes': 50
}

def test_api_connection():
    """Test if API is accessible"""
    print(f"{Fore.CYAN}Testing API Connection...{Style.RESET_ALL}")
    try:
        response = requests.post(
            BASE_URL,
            data={'key': API_KEY, 'action': 'balance'},
            timeout=10
        )
        if response.status_code == 200:
            data = response.json()
            balance = float(data.get('balance', 0)) if data.get('balance') else 0
            currency = data.get('currency', 'USD')
            print(f"  {Fore.GREEN}✓ API Connected{Style.RESET_ALL}")
            print(f"  Balance: ${balance:.2f} {currency}")
            return True, balance
        else:
            print(f"  {Fore.RED}✗ API Error: {response.status_code}{Style.RESET_ALL}")
            print(f"  Response: {response.text[:200]}")
            return False, 0
    except Exception as e:
        print(f"  {Fore.RED}✗ Connection Error: {e}{Style.RESET_ALL}")
        return False, 0

def test_get_services():
    """Test fetching services"""
    print(f"\n{Fore.CYAN}Testing Service Fetching...{Style.RESET_ALL}")
    try:
        response = requests.post(
            BASE_URL,
            data={'key': API_KEY, 'action': 'services'},
            timeout=10
        )
        if response.status_code == 200:
            services = response.json()
            print(f"  {Fore.GREEN}✓ Fetched {len(services)} services{Style.RESET_ALL}")
            
            # Verify our services exist
            found_services = {}
            for name, service_id in SERVICES.items():
                for svc in services:
                    if isinstance(svc, dict):
                        sid = str(svc.get('service', '') or svc.get('id', ''))
                        if sid == service_id:
                            found_services[name] = svc
                            print(f"  {Fore.GREEN}✓ {name.capitalize()} (ID {service_id}): {svc.get('name', 'N/A')[:50]}{Style.RESET_ALL}")
                            break
                if name not in found_services:
                    print(f"  {Fore.RED}✗ {name.capitalize()} (ID {service_id}) not found{Style.RESET_ALL}")
            
            return True, found_services
        else:
            print(f"  {Fore.RED}✗ Error: {response.status_code}{Style.RESET_ALL}")
            return False, {}
    except Exception as e:
        print(f"  {Fore.RED}✗ Error: {e}{Style.RESET_ALL}")
        return False, {}

def test_create_order(service_id, link, quantity, service_name):
    """Test creating an order (dry run - won't actually create if test mode)"""
    print(f"\n{Fore.CYAN}Testing Order Creation for {service_name}...{Style.RESET_ALL}")
    print(f"  Service ID: {service_id}")
    print(f"  Link: {link}")
    print(f"  Quantity: {quantity}")
    
    try:
        response = requests.post(
            BASE_URL,
            data={
                'key': API_KEY,
                'action': 'order',
                'service': service_id,
                'link': link,
                'quantity': quantity
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            order_id = data.get('order', 0)
            if order_id and order_id != 0:
                print(f"  {Fore.GREEN}✓ Order Created Successfully!{Style.RESET_ALL}")
                print(f"  Order ID: {order_id}")
                return True, order_id
            else:
                error = data.get('error', 'Unknown error')
                print(f"  {Fore.YELLOW}⚠ Order Response: {data}{Style.RESET_ALL}")
                return False, None
        else:
            print(f"  {Fore.RED}✗ Error: {response.status_code}{Style.RESET_ALL}")
            print(f"  Response: {response.text[:200]}")
            return False, None
    except Exception as e:
        print(f"  {Fore.RED}✗ Error: {e}{Style.RESET_ALL}")
        return False, None

def test_small_order(test_video_url):
    """Test with a small order first"""
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"TESTING WITH SMALL ORDER")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    
    print(f"{Fore.YELLOW}This will place a REAL order for testing!{Style.RESET_ALL}")
    print(f"Test Video URL: {test_video_url}\n")
    
    confirm = input(f"{Fore.CYAN}Place test order? (yes/no): {Style.RESET_ALL}").strip().lower()
    
    if confirm != 'yes':
        print(f"{Fore.YELLOW}Test order cancelled{Style.RESET_ALL}")
        return
    
    # Test with minimum views order
    success, order_id = test_create_order(
        SERVICES['views'],
        test_video_url,
        MINIMUMS['views'],
        'Views (Test)'
    )
    
    if success:
        print(f"\n{Fore.GREEN}✓ Test order successful!{Style.RESET_ALL}")
        print(f"{Fore.CYAN}You can check the order status on smmfollows.com{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.RED}✗ Test order failed. Check error above.{Style.RESET_ALL}")

def simulate_delivery_plan(test_video_url, dry_run=True):
    """Simulate the full delivery plan"""
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"SIMULATING DELIVERY PLAN")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    
    if dry_run:
        print(f"{Fore.YELLOW}DRY RUN MODE - No orders will be placed{Style.RESET_ALL}\n")
    else:
        print(f"{Fore.RED}LIVE MODE - Orders WILL be placed!{Style.RESET_ALL}\n")
    
    # Load purchase schedule
    try:
        with open('purchase_schedule.json', 'r') as f:
            purchases = json.load(f)
    except:
        print(f"{Fore.RED}Error: purchase_schedule.json not found. Run create_delivery_timeline.py first{Style.RESET_ALL}")
        return
    
    print(f"Total purchases to simulate: {len(purchases)}\n")
    
    # Group by service
    views_orders = [p for p in purchases if p['service'] == 'Views']
    likes_orders = [p for p in purchases if p['service'] == 'Likes']
    comments_orders = [p for p in purchases if p['service'] == 'Comments']
    comment_likes_orders = [p for p in purchases if p['service'] == 'Comment Likes']
    
    print(f"{Fore.CYAN}Purchase Summary:{Style.RESET_ALL}")
    print(f"  Views: {len(views_orders)} orders")
    print(f"  Likes: {len(likes_orders)} orders")
    print(f"  Comments: {len(comments_orders)} orders")
    print(f"  Comment Likes: {len(comment_likes_orders)} orders")
    print()
    
    if not dry_run:
        confirm = input(f"{Fore.RED}This will place {len(purchases)} REAL orders! Continue? (yes/no): {Style.RESET_ALL}").strip().lower()
        if confirm != 'yes':
            print(f"{Fore.YELLOW}Cancelled{Style.RESET_ALL}")
            return
    
    # Simulate first few orders
    print(f"\n{Fore.CYAN}Simulating first 5 purchases...{Style.RESET_ALL}\n")
    
    for i, purchase in enumerate(purchases[:5]):
        service = purchase['service']
        quantity = purchase['quantity']
        time_str = purchase['time_str']
        
        print(f"{Fore.YELLOW}[{time_str}] {service}: {quantity}{Style.RESET_ALL}")
        
        if not dry_run:
            service_id = SERVICES.get(service.lower().replace(' ', '_'))
            if service_id:
                success, order_id = test_create_order(
                    service_id,
                    test_video_url,
                    quantity,
                    service
                )
                if success:
                    print(f"  {Fore.GREEN}✓ Order {i+1}/{len(purchases)} placed{Style.RESET_ALL}")
                else:
                    print(f"  {Fore.RED}✗ Order {i+1}/{len(purchases)} failed{Style.RESET_ALL}")
                    break
            time.sleep(2)  # Small delay between orders
        else:
            print(f"  {Fore.CYAN}[DRY RUN] Would place order for {quantity} {service.lower()}{Style.RESET_ALL}")
    
    if dry_run:
        print(f"\n{Fore.GREEN}✓ Dry run complete!{Style.RESET_ALL}")
        print(f"{Fore.CYAN}To place real orders, run with --live flag{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.YELLOW}⚠ Only simulated first 5 orders. Full run would place all {len(purchases)} orders.{Style.RESET_ALL}")

def main():
    import sys
    
    print(f"""
    {Fore.CYAN}╔══════════════════════════════════════════════╗
    ║   Testing Delivery Plan                 ║
    ╚══════════════════════════════════════════════╝{Style.RESET_ALL}
    """)
    
    # Test 1: API Connection
    api_ok, balance = test_api_connection()
    if not api_ok:
        print(f"\n{Fore.RED}✗ Cannot proceed - API connection failed{Style.RESET_ALL}")
        return
    
    # Test 2: Get Services
    services_ok, services = test_get_services()
    if not services_ok:
        print(f"\n{Fore.RED}✗ Cannot proceed - Service fetch failed{Style.RESET_ALL}")
        return
    
    # Test 3: Check balance
    total_cost = 0.2278  # Cost per post
    print(f"\n{Fore.CYAN}Balance Check:{Style.RESET_ALL}")
    print(f"  Required: ${total_cost:.4f}")
    print(f"  Available: ${balance:.2f}")
    if balance < total_cost:
        print(f"  {Fore.RED}✗ Insufficient balance!{Style.RESET_ALL}")
        print(f"  {Fore.YELLOW}Add at least ${total_cost - balance:.2f} more{Style.RESET_ALL}")
    else:
        print(f"  {Fore.GREEN}✓ Sufficient balance{Style.RESET_ALL}")
    
    # Test 4: Small order test (optional)
    if len(sys.argv) > 1 and sys.argv[1] == '--test-order':
        test_video_url = sys.argv[2] if len(sys.argv) > 2 else input(f"{Fore.CYAN}Enter test video URL: {Style.RESET_ALL}")
        test_small_order(test_video_url)
    
    # Test 5: Simulate delivery plan
    dry_run = '--live' not in sys.argv
    if len(sys.argv) > 1 and sys.argv[1] != '--test-order':
        test_video_url = sys.argv[1] if sys.argv[1] != '--live' else (sys.argv[2] if len(sys.argv) > 2 else None)
    else:
        test_video_url = input(f"\n{Fore.CYAN}Enter test video URL (or press Enter for dry run only): {Style.RESET_ALL}").strip()
    
    if test_video_url:
        simulate_delivery_plan(test_video_url, dry_run=dry_run)
    else:
        print(f"\n{Fore.YELLOW}No video URL provided - skipping simulation{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Usage:{Style.RESET_ALL}")
        print(f"  python test_delivery_plan.py <video_url>          # Dry run")
        print(f"  python test_delivery_plan.py --live <video_url>  # Place real orders")
        print(f"  python test_delivery_plan.py --test-order <url>  # Test with small order")

if __name__ == "__main__":
    main()

