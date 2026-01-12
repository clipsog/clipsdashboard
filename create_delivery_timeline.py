#!/usr/bin/env python3
"""
Create visual timeline graphic of purchases over 24 hours
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from datetime import datetime, timedelta
import json

# Data from slowest delivery plan
total_time = 24 * 3600  # 24 hours in seconds

# Views: 80 orders every 1080 seconds (18 minutes)
views_orders = 80
views_delay = 1080
views_quantity = 50
views_color = '#3498db'  # Blue

# Likes: 13 orders every 6646 seconds (~110.8 minutes)
likes_orders = 13
likes_delay = 6646
likes_quantities = [10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 5]
likes_color = '#e74c3c'  # Red

# Comments: 1 order (milestone-based, not time-based)
# Will be ordered when views reach 2,000 (milestone, not fixed time)
comments_quantity = 10
comments_color = '#2ecc71'  # Green
comments_milestone_views = 2000  # Order when this many views are ordered

# Comment Likes: 1 order (milestone-based, not time-based)
# Will be ordered when views reach 2,600 (milestone, not fixed time)
comment_likes_quantity = 50
comment_likes_color = '#f39c12'  # Orange
comment_likes_milestone_views = 2600  # Order when this many views are ordered

def create_timeline():
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(16, 10))
    fig.suptitle('Organic Growth Purchase Timeline - 24 Hours', fontsize=16, fontweight='bold')
    
    # Timeline in hours
    hours = list(range(25))
    
    # Create timeline for all services
    ax1.set_xlim(0, 24)
    ax1.set_ylim(-0.5, 4.5)
    ax1.set_xlabel('Time (Hours)', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Service Type', fontsize=12, fontweight='bold')
    ax1.set_title('Purchase Points Over 24 Hours', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.3, linestyle='--')
    ax1.set_yticks([0, 1, 2, 3])
    ax1.set_yticklabels(['Views', 'Likes', 'Comments', 'Comment Likes'])
    
    # Plot Views purchases
    for i in range(views_orders):
        time_hours = (i * views_delay) / 3600
        ax1.scatter(time_hours, 0, s=100, c=views_color, alpha=0.7, edgecolors='black', linewidth=0.5)
        if i % 10 == 0:  # Label every 10th purchase
            ax1.text(time_hours, 0.15, f'{views_quantity}', fontsize=8, ha='center', fontweight='bold')
    
    # Plot Likes purchases
    for i in range(likes_orders):
        time_hours = (i * likes_delay) / 3600
        ax1.scatter(time_hours, 1, s=100, c=likes_color, alpha=0.7, edgecolors='black', linewidth=0.5)
        ax1.text(time_hours, 1.15, f'{likes_quantities[i]}', fontsize=8, ha='center', fontweight='bold')
    
    # Calculate when milestones will be reached
    comments_milestone_time_hours = None
    comment_likes_milestone_time_hours = None
    
    cumulative_views = 0
    for i in range(views_orders):
        cumulative_views += views_quantity
        time_hours = (i * views_delay) / 3600
        
        if comments_milestone_time_hours is None and cumulative_views >= comments_milestone_views:
            comments_milestone_time_hours = time_hours
            # Plot comments marker
            ax1.scatter(time_hours, 2, s=300, c=comments_color, alpha=0.8, 
                       edgecolors='black', linewidth=2, marker='*', zorder=5)
            ax1.text(time_hours, 2.25, f'{comments_quantity}', fontsize=10, 
                    ha='center', fontweight='bold')
            ax1.axvline(time_hours, color=comments_color, linestyle='--', alpha=0.3)
        
        if comment_likes_milestone_time_hours is None and cumulative_views >= comment_likes_milestone_views:
            comment_likes_milestone_time_hours = time_hours
            # Plot comment likes marker
            ax1.scatter(time_hours, 3, s=300, c=comment_likes_color, alpha=0.8,
                       edgecolors='black', linewidth=2, marker='*', zorder=5)
            ax1.text(time_hours, 3.25, f'{comment_likes_quantity}', fontsize=10,
                    ha='center', fontweight='bold')
            ax1.axvline(time_hours, color=comment_likes_color, linestyle='--', alpha=0.3)
    
    # Create cumulative progress chart
    ax2.set_xlim(0, 24)
    ax2.set_ylim(0, 4500)
    ax2.set_xlabel('Time (Hours)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Cumulative Quantity', fontsize=12, fontweight='bold')
    ax2.set_title('Cumulative Progress Over 24 Hours', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3, linestyle='--')
    
    # Calculate cumulative views
    views_times = [(i * views_delay) / 3600 for i in range(views_orders + 1)]
    views_cumulative = [i * views_quantity for i in range(views_orders + 1)]
    ax2.plot(views_times, views_cumulative, color=views_color, linewidth=3, label=f'Views (Total: {sum([views_quantity] * views_orders)})', marker='o', markersize=4)
    
    # Calculate cumulative likes
    likes_times = [(i * likes_delay) / 3600 for i in range(likes_orders + 1)]
    likes_cumulative = []
    total = 0
    for qty in likes_quantities + [0]:
        likes_cumulative.append(total)
        total += qty
    ax2.plot(likes_times, likes_cumulative, color=likes_color, linewidth=3, label=f'Likes (Total: {sum(likes_quantities)})', marker='s', markersize=4)
    
    # Plot milestone markers
    if comments_milestone_time_hours:
        ax2.scatter(comments_milestone_time_hours, comments_quantity, s=200, c=comments_color, 
                    marker='*', edgecolors='black', linewidth=2, zorder=5, label=f'Comments (Total: {comments_quantity})')
        ax2.axvline(comments_milestone_time_hours, color=comments_color, linestyle='--', alpha=0.5, linewidth=1)
        ax2.text(comments_milestone_time_hours, ax2.get_ylim()[1] * 0.95, f'Comments\n@ {comments_milestone_views:,} views', 
                 ha='center', fontsize=9, color=comments_color, fontweight='bold')
    
    if comment_likes_milestone_time_hours:
        ax2.scatter(comment_likes_milestone_time_hours, comment_likes_quantity, s=200, c=comment_likes_color,
                    marker='*', edgecolors='black', linewidth=2, zorder=5, label=f'Comment Likes (Total: {comment_likes_quantity})')
        ax2.axvline(comment_likes_milestone_time_hours, color=comment_likes_color, linestyle='--', alpha=0.5, linewidth=1)
        ax2.text(comment_likes_milestone_time_hours, ax2.get_ylim()[1] * 0.85, f'Comment Likes\n@ {comment_likes_milestone_views:,} views',
                 ha='center', fontsize=9, color=comment_likes_color, fontweight='bold')
    
    ax2.legend(loc='upper left', fontsize=10)
    
    # Add summary text box
    summary_text = f"""
    Total Orders: {views_orders + likes_orders + 1 + 1}
    • Views: {views_orders} orders ({views_quantity} each, every {views_delay/60:.0f} min)
    • Likes: {likes_orders} orders ({sum(likes_quantities)} total, every {likes_delay/60:.0f} min)
    • Comments: 1 order ({comments_quantity} comments) - Ordered at {comments_milestone_views:,} views milestone
    • Comment Likes: 1 order ({comment_likes_quantity} likes) - Ordered at {comment_likes_milestone_views:,} views milestone
    
    Total Cost: $0.2278
    """
    
    fig.text(0.02, 0.02, summary_text, fontsize=9, verticalalignment='bottom',
             bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig('purchase_timeline.png', dpi=300, bbox_inches='tight')
    print("✓ Timeline saved to: purchase_timeline.png")
    
    # Create detailed purchase schedule
    create_purchase_schedule()

def create_purchase_schedule():
    """Create a detailed table of all purchases"""
    purchases = []
    
    # Views
    cumulative_views = 0
    for i in range(views_orders):
        time_seconds = i * views_delay
        time_hours = time_seconds / 3600
        cumulative_views += views_quantity
        purchases.append({
            'time_seconds': time_seconds,
            'time_hours': time_hours,
            'time_str': f"{int(time_hours)}h {int((time_hours % 1) * 60)}m",
            'service': 'Views',
            'quantity': views_quantity,
            'cumulative_views': cumulative_views
        })
    
    # Likes
    cumulative_likes = 0
    for i, qty in enumerate(likes_quantities):
        time_seconds = i * likes_delay
        time_hours = time_seconds / 3600
        cumulative_likes += qty
        purchases.append({
            'time_seconds': time_seconds,
            'time_hours': time_hours,
            'time_str': f"{int(time_hours)}h {int((time_hours % 1) * 60)}m",
            'service': 'Likes',
            'quantity': qty,
            'cumulative_likes': cumulative_likes
        })
    
    # Comments - milestone-based (not in schedule, will be ordered when views reach milestone)
    # Note: Comments will be ordered dynamically when cumulative_views >= comments_milestone_views
    # Find approximate time when milestone will be reached for display purposes
    comments_milestone_time = None
    for purchase in purchases:
        if purchase.get('cumulative_views', 0) >= comments_milestone_views:
            comments_milestone_time = purchase['time_str']
            break
    
    # Comment Likes - milestone-based (not in schedule, will be ordered when views reach milestone)
    # Note: Comment Likes will be ordered dynamically when cumulative_views >= comment_likes_milestone_views
    comment_likes_milestone_time = None
    for purchase in purchases:
        if purchase.get('cumulative_views', 0) >= comment_likes_milestone_views:
            comment_likes_milestone_time = purchase['time_str']
            break
    
    # Sort by time
    purchases.sort(key=lambda x: x['time_hours'])
    
    # Save to JSON
    with open('purchase_schedule.json', 'w') as f:
        json.dump(purchases, f, indent=2)
    
    print("✓ Purchase schedule saved to: purchase_schedule.json")
    
    # Print first 20 purchases
    print("\nFirst 20 Purchases:")
    print("-" * 80)
    print(f"{'Time':<12} {'Service':<15} {'Quantity':<10} {'Cumulative':<20}")
    print("-" * 80)
    for p in purchases[:20]:
        cumulative = ""
        if 'cumulative_views' in p:
            cumulative = f"Views: {p['cumulative_views']}"
        elif 'cumulative_likes' in p:
            cumulative = f"Likes: {p['cumulative_likes']}"
        elif 'cumulative_comments' in p:
            cumulative = f"Comments: {p['cumulative_comments']}"
        elif 'cumulative_comment_likes' in p:
            cumulative = f"Comment Likes: {p['cumulative_comment_likes']}"
        
        print(f"{p['time_str']:<12} {p['service']:<15} {p['quantity']:<10} {cumulative:<20}")
    
    if len(purchases) > 20:
        print(f"\n... and {len(purchases) - 20} more purchases")

if __name__ == "__main__":
    try:
        create_timeline()
        print("\n✓ Graphics created successfully!")
    except ImportError:
        print("Error: matplotlib not installed. Installing...")
        import subprocess
        subprocess.check_call(['pip', 'install', 'matplotlib'])
        create_timeline()
        print("\n✓ Graphics created successfully!")

