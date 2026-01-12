#!/usr/bin/env python3
"""
Budget Assessment for smmfollows.com
"""

from colorama import Fore, Style, init
import json

init(autoreset=True)

def calculate_cost(rate_per_1000, quantity):
    """Calculate cost based on rate per 1000"""
    return (quantity / 1000.0) * rate_per_1000

def main():
    print(f"""
    {Fore.CYAN}╔══════════════════════════════════════════════╗
    ║   smmfollows.com Budget Assessment      ║
    ╚══════════════════════════════════════════════╝{Style.RESET_ALL}
    """)
    
    # Service information from user
    services = {
        'views': {
            'id': '1321',
            'min': 50,
            'name': 'TikTok Views'
        },
        'likes': {
            'id': '250',
            'min': None,  # Unknown
            'name': 'TikTok Likes'
        },
        'comments': {
            'id': '1384',
            'min': 10,
            'name': 'TikTok Comments',
            'note': 'Has text area for comments (1 per line)'
        },
        'comment_likes': {
            'id': '14718',
            'min': 50,
            'name': 'TikTok Comment Likes',
            'note': 'Says "by username" but has place for post link (not username)'
        }
    }
    
    # Default targets
    target_views = 4000
    target_likes = 125
    num_comments = 7
    comment_likes = 15
    
    print(f"{Fore.CYAN}Service Information:{Style.RESET_ALL}\n")
    for name, info in services.items():
        print(f"{Fore.YELLOW}{info['name']} (ID: {info['id']}):{Style.RESET_ALL}")
        print(f"  Minimum: {info['min'] if info['min'] else 'Unknown'}")
        if 'note' in info:
            print(f"  {Fore.CYAN}Note: {info['note']}{Style.RESET_ALL}")
        print()
    
    print(f"{Fore.CYAN}{'='*60}")
    print(f"ENTER PRICING FROM WEBSITE")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    print(f"{Fore.YELLOW}Please check smmfollows.com and enter the rates per 1000:{Style.RESET_ALL}\n")
    
    rates = {}
    
    # Get rates (with defaults based on typical SMM pricing)
    views_rate = input(f"{Fore.CYAN}Views rate per 1000 (default 0.02): {Style.RESET_ALL}").strip()
    rates['views'] = float(views_rate) if views_rate else 0.02
    
    likes_rate = input(f"{Fore.CYAN}Likes rate per 1000 (default 0.05): {Style.RESET_ALL}").strip()
    rates['likes'] = float(likes_rate) if likes_rate else 0.05
    
    comments_rate = input(f"{Fore.CYAN}Comments rate per 1000 (default 0.10): {Style.RESET_ALL}").strip()
    rates['comments'] = float(comments_rate) if comments_rate else 0.10
    
    comment_likes_rate = input(f"{Fore.CYAN}Comment Likes rate per 1000 (default 0.03): {Style.RESET_ALL}").strip()
    rates['comment_likes'] = float(comment_likes_rate) if comment_likes_rate else 0.03
    
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"BUDGET BREAKDOWN")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    
    # Views
    views_per_batch = max(100, services['views']['min'])  # Use 100 or minimum, whichever is higher
    num_batches = (target_views + views_per_batch - 1) // views_per_batch
    views_cost_per_batch = calculate_cost(rates['views'], views_per_batch)
    total_views_cost = calculate_cost(rates['views'], target_views)
    
    print(f"{Fore.YELLOW}Views:{Style.RESET_ALL}")
    print(f"  Target: {target_views:,} views")
    print(f"  Minimum per order: {services['views']['min']}")
    print(f"  Batch size: {views_per_batch} views")
    print(f"  Number of batches: {num_batches}")
    print(f"  Rate: ${rates['views']:.4f} per 1000")
    print(f"  Cost per batch: ${views_cost_per_batch:.6f}")
    print(f"  {Fore.GREEN}Total Views Cost: ${total_views_cost:.4f}{Style.RESET_ALL}\n")
    
    # Likes
    total_likes_cost = calculate_cost(rates['likes'], target_likes)
    print(f"{Fore.YELLOW}Likes:{Style.RESET_ALL}")
    print(f"  Target: {target_likes} likes")
    if services['likes']['min']:
        print(f"  Minimum per order: {services['likes']['min']}")
    print(f"  Rate: ${rates['likes']:.4f} per 1000")
    print(f"  {Fore.GREEN}Total Likes Cost: ${total_likes_cost:.4f}{Style.RESET_ALL}\n")
    
    # Comments
    # Note: Need to adjust to minimum if below
    comments_to_order = max(num_comments, services['comments']['min'])
    total_comments_cost = calculate_cost(rates['comments'], comments_to_order)
    print(f"{Fore.YELLOW}Comments:{Style.RESET_ALL}")
    print(f"  Target: {num_comments} comments")
    print(f"  Minimum per order: {services['comments']['min']}")
    if comments_to_order > num_comments:
        print(f"  {Fore.YELLOW}⚠ Will order {comments_to_order} (minimum) instead of {num_comments}{Style.RESET_ALL}")
    print(f"  Rate: ${rates['comments']:.4f} per 1000")
    print(f"  {Fore.CYAN}Note: Comments can be entered in text area (1 per line){Style.RESET_ALL}")
    print(f"  {Fore.GREEN}Total Comments Cost: ${total_comments_cost:.4f}{Style.RESET_ALL}\n")
    
    # Comment Likes
    # Note: Need to adjust to minimum if below
    comment_likes_to_order = max(comment_likes, services['comment_likes']['min'])
    total_comment_likes_cost = calculate_cost(rates['comment_likes'], comment_likes_to_order)
    print(f"{Fore.YELLOW}Comment Likes:{Style.RESET_ALL}")
    print(f"  Target: {comment_likes} likes on one comment")
    print(f"  Minimum per order: {services['comment_likes']['min']}")
    if comment_likes_to_order > comment_likes:
        print(f"  {Fore.YELLOW}⚠ Will order {comment_likes_to_order} (minimum) instead of {comment_likes}{Style.RESET_ALL}")
    print(f"  Rate: ${rates['comment_likes']:.4f} per 1000")
    print(f"  {Fore.CYAN}Note: Service says 'by username' but has place for post link{Style.RESET_ALL}")
    print(f"  {Fore.GREEN}Total Comment Likes Cost: ${total_comment_likes_cost:.4f}{Style.RESET_ALL}\n")
    
    # Total
    total_cost = total_views_cost + total_likes_cost + total_comments_cost + total_comment_likes_cost
    
    print(f"{Fore.CYAN}{'='*60}")
    print(f"{Fore.GREEN}TOTAL COST PER POST: ${total_cost:.4f}")
    print(f"{'='*60}{Style.RESET_ALL}\n")
    
    # Recommendations
    print(f"{Fore.CYAN}RECOMMENDATIONS:{Style.RESET_ALL}")
    print(f"  • Add at least ${total_cost * 1.1:.2f} to your account (10% buffer)")
    print(f"  • For multiple posts, multiply by number of posts")
    print(f"  • Example: 10 posts = ${total_cost * 10:.2f}")
    print()
    
    # Minimum order adjustments summary
    print(f"{Fore.YELLOW}MINIMUM ORDER ADJUSTMENTS:{Style.RESET_ALL}")
    adjustments = []
    if comments_to_order > num_comments:
        adjustments.append(f"Comments: {num_comments} → {comments_to_order} (+${total_comments_cost - calculate_cost(rates['comments'], num_comments):.4f})")
    if comment_likes_to_order > comment_likes:
        adjustments.append(f"Comment Likes: {comment_likes} → {comment_likes_to_order} (+${total_comment_likes_cost - calculate_cost(rates['comment_likes'], comment_likes):.4f})")
    
    if adjustments:
        for adj in adjustments:
            print(f"  ⚠ {adj}")
    else:
        print(f"  ✓ No adjustments needed - all quantities meet minimums")
    print()
    
    # Save to file
    budget_data = {
        'panel': 'smmfollows.com',
        'services': services,
        'rates': rates,
        'targets': {
            'views': target_views,
            'likes': target_likes,
            'comments': num_comments,
            'comment_likes': comment_likes
        },
        'adjusted_quantities': {
            'comments': comments_to_order,
            'comment_likes': comment_likes_to_order
        },
        'costs': {
            'views': total_views_cost,
            'likes': total_likes_cost,
            'comments': total_comments_cost,
            'comment_likes': total_comment_likes_cost,
            'total': total_cost
        }
    }
    
    output_file = 'smmfollows_budget.json'
    with open(output_file, 'w') as f:
        json.dump(budget_data, f, indent=2)
    print(f"{Fore.CYAN}Budget saved to: {output_file}{Style.RESET_ALL}")

if __name__ == "__main__":
    main()


