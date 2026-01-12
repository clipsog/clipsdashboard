#!/usr/bin/env python3
"""
Check smmfollows.com services and prices
"""

import requests
import json
import sys
from colorama import Fore, Style, init

init(autoreset=True)

def try_api_endpoints(api_key=None):
    """Try different API endpoints"""
    # Common SMM panel API formats
    endpoints = [
        "https://smmfollows.com/api/v2",
        "https://smmfollows.com/api",
        "https://api.smmfollows.com/v2",
        "https://api.smmfollows.com",
    ]
    
    params = {}
    if api_key:
        params['key'] = api_key
    
    for base_url in endpoints:
        print(f"\n{Fore.CYAN}Trying: {base_url}{Style.RESET_ALL}")
        
        # Try services endpoint
        try:
            response = requests.get(
                base_url,
                params={**params, 'action': 'services'},
                timeout=10
            )
            print(f"  Services: Status {response.status_code}")
            if response.status_code == 200:
                print(f"  ✓ Success! Response: {response.text[:200]}")
                return base_url, response.json()
            else:
                print(f"  Response: {response.text[:200]}")
        except Exception as e:
            print(f"  Error: {e}")
    
    return None, None

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
    print(f"""
    {Fore.CYAN}╔══════════════════════════════════════════════╗
    ║   Checking smmfollows.com Services      ║
    ╚══════════════════════════════════════════════╝{Style.RESET_ALL}
    """)
    
    api_key = sys.argv[1] if len(sys.argv) > 1 else None
    
    if api_key:
        print(f"{Fore.CYAN}Using API key: {api_key[:20]}...{Style.RESET_ALL}")
    else:
        print(f"{Fore.YELLOW}No API key provided - trying without authentication{Style.RESET_ALL}")
    
    # Try to find API endpoint
    base_url, services = try_api_endpoints(api_key)
    
    # Service IDs from user
    service_ids = {
        'views': '1321',
        'likes': '250',
        'comments': '1384',
        'comment_likes': '14718'
    }
    
    # Minimums from user
    minimums = {
        'views': 50,
        'likes': None,  # Unknown
        'comments': 10,
        'comment_likes': 50
    }
    
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"SERVICE DETAILS")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    
    results = {}
    
    if services:
        for name, service_id in service_ids.items():
            print(f"{Fore.YELLOW}{name.upper()} (Service ID: {service_id}):{Style.RESET_ALL}")
            service = find_service_by_id(services, service_id)
            
            if service:
                rate = service.get('rate', 0)
                min_order = service.get('min', minimums.get(name, 'N/A'))
                max_order = service.get('max', 'N/A')
                service_name = service.get('name', 'N/A')
                
                print(f"  {Fore.GREEN}✓ Found:{Style.RESET_ALL}")
                print(f"    Name: {service_name}")
                print(f"    Rate: ${rate} per 1000")
                print(f"    Min: {min_order}")
                print(f"    Max: {max_order}")
                
                results[name] = {
                    'rate': float(rate),
                    'min': int(min_order) if isinstance(min_order, (int, float)) else minimums.get(name),
                    'max': max_order,
                    'name': service_name
                }
            else:
                print(f"  {Fore.RED}✗ Service not found in API response{Style.RESET_ALL}")
                results[name] = None
            print()
    else:
        print(f"{Fore.YELLOW}⚠ Could not fetch services from API{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Using manual information provided...{Style.RESET_ALL}\n")
        
        for name, service_id in service_ids.items():
            print(f"{Fore.YELLOW}{name.upper()} (Service ID: {service_id}):{Style.RESET_ALL}")
            print(f"  Min: {minimums.get(name, 'Unknown')}")
            print(f"  {Fore.YELLOW}⚠ Need to check rate on website{Style.RESET_ALL}\n")
    
    # Calculate budget if we have rates
    if results and any(r and r.get('rate') for r in results.values()):
        print(f"\n{Fore.CYAN}{'='*60}")
        print(f"BUDGET CALCULATION")
        print(f"{'='*60}{Style.RESET_ALL}\n")
        
        target_views = 4000
        target_likes = 125
        num_comments = 7
        comment_likes = 15
        
        total_cost = 0
        
        # Views
        if results.get('views') and results['views'].get('rate'):
            views_rate = results['views']['rate']
            views_cost = (target_views / 1000.0) * views_rate
            total_cost += views_cost
            print(f"{Fore.YELLOW}Views:{Style.RESET_ALL}")
            print(f"  {target_views:,} views @ ${views_rate:.4f}/1000 = ${views_cost:.4f}")
        else:
            print(f"{Fore.YELLOW}Views:{Style.RESET_ALL} Rate unknown - check website")
        
        # Likes
        if results.get('likes') and results['likes'].get('rate'):
            likes_rate = results['likes']['rate']
            likes_cost = (target_likes / 1000.0) * likes_rate
            total_cost += likes_cost
            print(f"{Fore.YELLOW}Likes:{Style.RESET_ALL}")
            print(f"  {target_likes} likes @ ${likes_rate:.4f}/1000 = ${likes_cost:.4f}")
        else:
            print(f"{Fore.YELLOW}Likes:{Style.RESET_ALL} Rate unknown - check website")
        
        # Comments
        if results.get('comments') and results['comments'].get('rate'):
            comments_rate = results['comments']['rate']
            comments_cost = (num_comments / 1000.0) * comments_rate
            total_cost += comments_cost
            print(f"{Fore.YELLOW}Comments:{Style.RESET_ALL}")
            print(f"  {num_comments} comments @ ${comments_rate:.4f}/1000 = ${comments_cost:.4f}")
        else:
            print(f"{Fore.YELLOW}Comments:{Style.RESET_ALL} Rate unknown - check website")
        
        # Comment Likes
        if results.get('comment_likes') and results['comment_likes'].get('rate'):
            clikes_rate = results['comment_likes']['rate']
            clikes_cost = (comment_likes / 1000.0) * clikes_rate
            total_cost += clikes_cost
            print(f"{Fore.YELLOW}Comment Likes:{Style.RESET_ALL}")
            print(f"  {comment_likes} likes @ ${clikes_rate:.4f}/1000 = ${clikes_cost:.4f}")
        else:
            print(f"{Fore.YELLOW}Comment Likes:{Style.RESET_ALL} Rate unknown - check website")
        
        if total_cost > 0:
            print(f"\n{Fore.GREEN}Estimated Total: ${total_cost:.4f}{Style.RESET_ALL}")

if __name__ == "__main__":
    main()


