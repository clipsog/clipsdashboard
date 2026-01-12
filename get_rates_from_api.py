#!/usr/bin/env python3
"""
Get real rates from smmfollows.com API
"""

import requests
import json
import sys
from colorama import Fore, Style, init

init(autoreset=True)

def get_services_from_api(api_key):
    """Fetch services from smmfollows.com API"""
    base_url = "https://smmfollows.com/api/v2"
    
    # Try POST request (common SMM panel format)
    try:
        response = requests.post(
            base_url,
            data={
                'key': api_key,
                'action': 'services'
            },
            timeout=10
        )
        
        if response.status_code == 200:
            try:
                return response.json()
            except:
                return None
        else:
            print(f"Status {response.status_code}: {response.text[:200]}")
            return None
    except Exception as e:
        print(f"Error: {e}")
        return None

def find_service_by_id(services, service_id):
    """Find service by ID"""
    if not services:
        return None
    
    for service in services:
        if isinstance(service, dict):
            sid = str(service.get('service', '') or service.get('id', '') or service.get('service_id', ''))
            if sid == str(service_id):
                return service
    return None

def main():
    if len(sys.argv) < 2:
        print(f"{Fore.YELLOW}Usage: python get_rates_from_api.py <API_KEY>{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Get your API key from: https://smmfollows.com (Profile/API section){Style.RESET_ALL}")
        sys.exit(1)
    
    api_key = sys.argv[1]
    
    print(f"""
    {Fore.CYAN}╔══════════════════════════════════════════════╗
    ║   Fetching Rates from smmfollows.com API  ║
    ╚══════════════════════════════════════════════╝{Style.RESET_ALL}
    """)
    
    print(f"{Fore.CYAN}Fetching services from API...{Style.RESET_ALL}")
    services = get_services_from_api(api_key)
    
    if not services:
        print(f"{Fore.RED}✗ Failed to fetch services{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Make sure your API key is correct and account is active{Style.RESET_ALL}")
        sys.exit(1)
    
    print(f"{Fore.GREEN}✓ Successfully fetched {len(services)} services{Style.RESET_ALL}\n")
    
    # Service IDs from user
    service_ids = {
        'views': '1321',
        'likes': '250',
        'comments': '1384',
        'comment_likes': '14718'
    }
    
    print(f"{Fore.CYAN}{'='*60}")
    print(f"SERVICE RATES")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    
    results = {}
    
    for name, service_id in service_ids.items():
        print(f"{Fore.YELLOW}{name.upper()} (Service ID: {service_id}):{Style.RESET_ALL}")
        service = find_service_by_id(services, service_id)
        
        if service:
            rate = float(service.get('rate', 0))
            min_order = int(service.get('min', 0))
            max_order = service.get('max', 'N/A')
            service_name = service.get('name', 'N/A')
            
            print(f"  {Fore.GREEN}✓ Found:{Style.RESET_ALL}")
            print(f"    Name: {service_name}")
            print(f"    {Fore.GREEN}Rate: ${rate:.4f} per 1000{Style.RESET_ALL}")
            print(f"    Min: {min_order}")
            print(f"    Max: {max_order}")
            
            results[name] = {
                'rate': rate,
                'min': min_order,
                'max': max_order,
                'name': service_name
            }
        else:
            print(f"  {Fore.RED}✗ Service not found{Style.RESET_ALL}")
            results[name] = None
        print()
    
    # Calculate budget
    if all(results.values()):
        print(f"{Fore.CYAN}{'='*60}")
        print(f"BUDGET CALCULATION")
        print(f"{'='*60}{Style.RESET_ALL}\n")
        
        target_views = 4000
        target_likes = 125
        num_comments = 7
        comment_likes = 15
        
        # Views
        views_rate = results['views']['rate']
        views_cost = (target_views / 1000.0) * views_rate
        print(f"{Fore.YELLOW}Views:{Style.RESET_ALL}")
        print(f"  {target_views:,} views @ ${views_rate:.4f}/1000 = ${views_cost:.4f}")
        
        # Likes
        likes_rate = results['likes']['rate']
        likes_cost = (target_likes / 1000.0) * likes_rate
        print(f"{Fore.YELLOW}Likes:{Style.RESET_ALL}")
        print(f"  {target_likes} likes @ ${likes_rate:.4f}/1000 = ${likes_cost:.4f}")
        
        # Comments (adjust for minimum)
        comments_rate = results['comments']['rate']
        comments_min = results['comments']['min']
        comments_to_order = max(num_comments, comments_min)
        comments_cost = (comments_to_order / 1000.0) * comments_rate
        print(f"{Fore.YELLOW}Comments:{Style.RESET_ALL}")
        print(f"  {comments_to_order} comments @ ${comments_rate:.4f}/1000 = ${comments_cost:.4f}")
        if comments_to_order > num_comments:
            print(f"  {Fore.YELLOW}⚠ Adjusted from {num_comments} to {comments_to_order} (minimum){Style.RESET_ALL}")
        
        # Comment Likes (adjust for minimum)
        clikes_rate = results['comment_likes']['rate']
        clikes_min = results['comment_likes']['min']
        clikes_to_order = max(comment_likes, clikes_min)
        clikes_cost = (clikes_to_order / 1000.0) * clikes_rate
        print(f"{Fore.YELLOW}Comment Likes:{Style.RESET_ALL}")
        print(f"  {clikes_to_order} likes @ ${clikes_rate:.4f}/1000 = ${clikes_cost:.4f}")
        if clikes_to_order > comment_likes:
            print(f"  {Fore.YELLOW}⚠ Adjusted from {comment_likes} to {clikes_to_order} (minimum){Style.RESET_ALL}")
        
        total_cost = views_cost + likes_cost + comments_cost + clikes_cost
        
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"{Fore.GREEN}TOTAL COST PER POST: ${total_cost:.4f}")
        print(f"{'='*60}{Style.RESET_ALL}\n")
        
        # Save results
        output = {
            'rates': {name: r['rate'] for name, r in results.items()},
            'minimums': {name: r['min'] for name, r in results.items()},
            'total_cost': total_cost
        }
        
        with open('smmfollows_rates.json', 'w') as f:
            json.dump(output, f, indent=2)
        print(f"{Fore.CYAN}Rates saved to: smmfollows_rates.json{Style.RESET_ALL}")

if __name__ == "__main__":
    main()


