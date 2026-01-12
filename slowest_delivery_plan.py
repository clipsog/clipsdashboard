#!/usr/bin/env python3
"""
Calculate slowest delivery plan over 24 hours using minimum order quantities
"""

import json
from colorama import Fore, Style, init
from datetime import datetime, timedelta

init(autoreset=True)

# Real rates from API
rates = {
    'views': 0.0140,
    'likes': 0.2100,
    'comments': 13.5000,
    'comment_likes': 0.2100
}

minimums = {
    'views': 50,
    'likes': 10,
    'comments': 10,
    'comment_likes': 50
}

targets = {
    'views': 4000,
    'likes': 125,
    'comments': 7,
    'comment_likes': 15
}

def calculate_cost(rate_per_1000, quantity):
    """Calculate cost"""
    return (quantity / 1000.0) * rate_per_1000

def format_time(seconds):
    """Format seconds to readable time"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"

def main():
    print(f"""
    {Fore.CYAN}╔══════════════════════════════════════════════╗
    ║   Slowest Delivery Plan (24 Hours)        ║
    ╚══════════════════════════════════════════════╝{Style.RESET_ALL}
    """)
    
    total_time = 24 * 3600  # 24 hours in seconds
    
    print(f"{Fore.CYAN}COST PER POST:{Style.RESET_ALL}\n")
    
    # Calculate costs
    views_cost = calculate_cost(rates['views'], targets['views'])
    likes_cost = calculate_cost(rates['likes'], targets['likes'])
    
    # Adjust for minimums
    comments_to_order = max(targets['comments'], minimums['comments'])
    comments_cost = calculate_cost(rates['comments'], comments_to_order)
    
    comment_likes_to_order = max(targets['comment_likes'], minimums['comment_likes'])
    comment_likes_cost = calculate_cost(rates['comment_likes'], comment_likes_to_order)
    
    total_cost = views_cost + likes_cost + comments_cost + comment_likes_cost
    
    print(f"  Views: ${views_cost:.4f}")
    print(f"  Likes: ${likes_cost:.4f}")
    print(f"  Comments: ${comments_cost:.4f} ({comments_to_order} comments, min {minimums['comments']})")
    print(f"  Comment Likes: ${comment_likes_cost:.4f} ({comment_likes_to_order} likes, min {minimums['comment_likes']})")
    print(f"\n  {Fore.GREEN}TOTAL COST PER POST: ${total_cost:.4f}{Style.RESET_ALL}\n")
    
    print(f"{Fore.CYAN}{'='*60}")
    print(f"SLOWEST DELIVERY PLAN (24 HOURS)")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    
    # Views - slowest delivery
    views_min = minimums['views']
    views_needed = targets['views']
    num_views_orders = (views_needed + views_min - 1) // views_min  # Ceiling division
    
    views_delay = total_time / num_views_orders if num_views_orders > 0 else 0
    
    print(f"{Fore.YELLOW}VIEWS:{Style.RESET_ALL}")
    print(f"  Target: {views_needed:,} views")
    print(f"  Minimum per order: {views_min}")
    print(f"  Number of orders: {num_views_orders}")
    print(f"  Quantity per order: {views_min} views")
    print(f"  Delay between orders: {format_time(views_delay)} ({views_delay:.0f} seconds)")
    print(f"  Cost per order: ${calculate_cost(rates['views'], views_min):.6f}")
    print(f"  Total views cost: ${views_cost:.4f}")
    print()
    
    # Likes - slowest delivery
    likes_min = minimums['likes']
    likes_needed = targets['likes']
    num_likes_orders = (likes_needed + likes_min - 1) // likes_min
    
    likes_delay = total_time / num_likes_orders if num_likes_orders > 0 else 0
    
    print(f"{Fore.YELLOW}LIKES:{Style.RESET_ALL}")
    print(f"  Target: {likes_needed} likes")
    print(f"  Minimum per order: {likes_min}")
    print(f"  Number of orders: {num_likes_orders}")
    
    # Calculate distribution
    likes_per_order = []
    remaining = likes_needed
    for i in range(num_likes_orders):
        if i == num_likes_orders - 1:
            likes_per_order.append(remaining)  # Last order gets remainder
        else:
            likes_per_order.append(likes_min)
            remaining -= likes_min
    
    print(f"  Quantities per order: {likes_per_order}")
    print(f"  Delay between orders: {format_time(likes_delay)} ({likes_delay:.0f} seconds)")
    print(f"  Cost per order: ${calculate_cost(rates['likes'], likes_min):.6f} (for {likes_min} likes)")
    print(f"  Total likes cost: ${likes_cost:.4f}")
    print()
    
    # Comments - one order at minimum
    print(f"{Fore.YELLOW}COMMENTS:{Style.RESET_ALL}")
    print(f"  Target: {targets['comments']} comments")
    print(f"  Minimum per order: {minimums['comments']}")
    print(f"  Will order: {comments_to_order} comments (minimum)")
    print(f"  Number of orders: 1")
    print(f"  Order timing: Can be placed anytime during 24 hours")
    print(f"  Cost: ${comments_cost:.4f}")
    if comments_to_order > targets['comments']:
        print(f"  {Fore.YELLOW}⚠ Ordering {comments_to_order} instead of {targets['comments']} (minimum requirement){Style.RESET_ALL}")
    print()
    
    # Comment Likes - one order at minimum
    print(f"{Fore.YELLOW}COMMENT LIKES:{Style.RESET_ALL}")
    print(f"  Target: {targets['comment_likes']} likes")
    print(f"  Minimum per order: {minimums['comment_likes']}")
    print(f"  Will order: {comment_likes_to_order} likes (minimum)")
    print(f"  Number of orders: 1")
    print(f"  Order timing: Can be placed anytime during 24 hours")
    print(f"  Cost: ${comment_likes_cost:.4f}")
    if comment_likes_to_order > targets['comment_likes']:
        print(f"  {Fore.YELLOW}⚠ Ordering {comment_likes_to_order} instead of {targets['comment_likes']} (minimum requirement){Style.RESET_ALL}")
    print()
    
    # Summary timeline
    print(f"{Fore.CYAN}{'='*60}")
    print(f"DELIVERY TIMELINE SUMMARY")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    
    print(f"{Fore.GREEN}Views:{Style.RESET_ALL}")
    print(f"  • {num_views_orders} orders of {views_min} views each")
    print(f"  • Every {format_time(views_delay)} ({views_delay/60:.1f} minutes)")
    print(f"  • Starts immediately, completes in 24 hours")
    print()
    
    print(f"{Fore.GREEN}Likes:{Style.RESET_ALL}")
    print(f"  • {num_likes_orders} orders: {likes_per_order}")
    print(f"  • Every {format_time(likes_delay)} ({likes_delay/60:.1f} minutes)")
    print(f"  • Starts immediately, completes in 24 hours")
    print()
    
    print(f"{Fore.GREEN}Comments:{Style.RESET_ALL}")
    print(f"  • 1 order of {comments_to_order} comments")
    print(f"  • Can be placed anytime (suggest: when video reaches 2,000 views)")
    print()
    
    print(f"{Fore.GREEN}Comment Likes:{Style.RESET_ALL}")
    print(f"  • 1 order of {comment_likes_to_order} likes")
    print(f"  • Can be placed anytime (suggest: when video reaches 2,600 views)")
    print()
    
    # Cost breakdown
    print(f"{Fore.CYAN}{'='*60}")
    print(f"COST BREAKDOWN")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    
    views_order_cost = calculate_cost(rates['views'], views_min)
    likes_order_cost = calculate_cost(rates['likes'], likes_min)
    
    print(f"Views: {num_views_orders} orders × ${views_order_cost:.6f} = ${views_cost:.4f}")
    print(f"Likes: {num_likes_orders} orders × ${likes_order_cost:.6f} = ${likes_cost:.4f}")
    print(f"Comments: 1 order × ${comments_cost:.4f} = ${comments_cost:.4f}")
    print(f"Comment Likes: 1 order × ${comment_likes_cost:.4f} = ${comment_likes_cost:.4f}")
    print(f"\n{Fore.GREEN}Total: ${total_cost:.4f}{Style.RESET_ALL}")
    print()
    
    # Save plan
    plan = {
        'cost_per_post': total_cost,
        'delivery_plan': {
            'views': {
                'orders': num_views_orders,
                'quantity_per_order': views_min,
                'delay_seconds': views_delay,
                'delay_formatted': format_time(views_delay),
                'cost_per_order': views_order_cost,
                'total_cost': views_cost
            },
            'likes': {
                'orders': num_likes_orders,
                'quantities_per_order': likes_per_order,
                'delay_seconds': likes_delay,
                'delay_formatted': format_time(likes_delay),
                'cost_per_order': likes_order_cost,
                'total_cost': likes_cost
            },
            'comments': {
                'orders': 1,
                'quantity': comments_to_order,
                'cost': comments_cost
            },
            'comment_likes': {
                'orders': 1,
                'quantity': comment_likes_to_order,
                'cost': comment_likes_cost
            }
        }
    }
    
    with open('slowest_delivery_plan.json', 'w') as f:
        json.dump(plan, f, indent=2)
    
    print(f"{Fore.CYAN}Plan saved to: slowest_delivery_plan.json{Style.RESET_ALL}")

if __name__ == "__main__":
    main()


