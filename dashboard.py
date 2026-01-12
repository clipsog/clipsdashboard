#!/usr/bin/env python3
"""
Dashboard to view all active videos and their progress
"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta
from colorama import Fore, Style, init

init(autoreset=True)

PROGRESS_FILE = Path.home() / '.smmfollows_bot' / 'progress.json'

def load_progress():
    """Load progress from file"""
    if not PROGRESS_FILE.exists():
        return {}
    
    try:
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def format_number(num):
    """Format number with commas"""
    return f"{int(num):,}"

def format_percentage(current, target):
    """Format percentage"""
    if target == 0:
        return "0%"
    pct = (current / target) * 100
    return f"{pct:.1f}%"

def format_time_elapsed(start_time_str):
    """Format time elapsed since start"""
    try:
        start_time = datetime.fromisoformat(start_time_str)
        elapsed = datetime.now() - start_time
        
        hours = int(elapsed.total_seconds() // 3600)
        minutes = int((elapsed.total_seconds() % 3600) // 60)
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    except:
        return "N/A"

def extract_video_info(video_url):
    """Extract username and video ID from URL"""
    try:
        # Format: https://www.tiktok.com/@username/video/1234567890
        parts = video_url.split('/')
        username = None
        video_id = None
        
        for i, part in enumerate(parts):
            if part.startswith('@'):
                username = part[1:]  # Remove @
            if part == 'video' and i + 1 < len(parts):
                video_id = parts[i + 1].split('?')[0]  # Remove query params
        
        return username, video_id
    except:
        return None, None

def get_status_emoji(progress_pct):
    """Get status emoji based on progress"""
    if progress_pct >= 100:
        return "✅"
    elif progress_pct >= 75:
        return "🟢"
    elif progress_pct >= 50:
        return "🟡"
    elif progress_pct >= 25:
        return "🟠"
    else:
        return "🔴"

def display_dashboard():
    """Display the dashboard"""
    progress = load_progress()
    
    if not progress:
        print(f"{Fore.YELLOW}No videos in progress.{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Add a video using: python run_delivery_bot.py <video_url>{Style.RESET_ALL}")
        return
    
    # Header
    print(f"\n{Fore.CYAN}{'='*120}")
    print(f"{Fore.CYAN}{'TIKTOK BOT DASHBOARD':^120}")
    print(f"{Fore.CYAN}{'='*120}{Style.RESET_ALL}\n")
    
    # Table header
    header = f"{Fore.CYAN}{'Video':<30} {'Views':<15} {'Likes':<12} {'Comments':<12} {'C.Likes':<12} {'Progress':<10} {'Time':<10} {'Status':<6}{Style.RESET_ALL}"
    print(header)
    print(f"{Fore.CYAN}{'-'*120}{Style.RESET_ALL}")
    
    # Process each video
    for video_url, video_progress in progress.items():
        username, video_id = extract_video_info(video_url)
        
        # Display name
        if username and video_id:
            display_name = f"@{username[:15]}"
            if len(username) > 15:
                display_name += "..."
            display_name += f"\n{Style.DIM}{video_id[:20]}...{Style.RESET_ALL}"
        else:
            display_name = video_url[:30]
            if len(video_url) > 30:
                display_name += "..."
        
        # Get current stats
        orders_placed = video_progress.get('orders_placed', {})
        initial_views = video_progress.get('initial_views', 0)
        initial_likes = video_progress.get('initial_likes', 0)
        
        # Calculate totals
        views_ordered = orders_placed.get('views', 0)
        likes_ordered = orders_placed.get('likes', 0)
        comments_ordered = orders_placed.get('comments', 0)
        comment_likes_ordered = orders_placed.get('comment_likes', 0)
        
        total_views = initial_views + views_ordered
        total_likes = initial_likes + likes_ordered
        
        # Targets
        target_views = video_progress.get('target_views', 4000)
        target_likes = video_progress.get('target_likes', 125)
        target_comments = video_progress.get('target_comments', 7)
        target_comment_likes = video_progress.get('target_comment_likes', 15)
        
        # Progress percentages (use views as main indicator)
        views_progress = format_percentage(total_views, target_views)
        views_pct = (total_views / target_views * 100) if target_views > 0 else 0
        
        # Time elapsed
        start_time = video_progress.get('start_time', '')
        time_elapsed = format_time_elapsed(start_time)
        
        # Status emoji
        status = get_status_emoji(views_pct)
        
        # Format row - handle multi-line display_name
        display_lines = display_name.split('\n')
        if len(display_lines) > 1:
            # First line
            row1 = (
                f"{display_lines[0]:<30} "
                f"{Fore.GREEN}{format_number(total_views):<8}{Style.DIM}/{format_number(target_views):<6}{Style.RESET_ALL} "
                f"{Fore.GREEN}{format_number(total_likes):<6}{Style.DIM}/{format_number(target_likes):<5}{Style.RESET_ALL} "
                f"{Fore.CYAN}{comments_ordered:<6}{Style.DIM}/{target_comments:<5}{Style.RESET_ALL} "
                f"{Fore.CYAN}{comment_likes_ordered:<6}{Style.DIM}/{target_comment_likes:<5}{Style.RESET_ALL} "
                f"{Fore.YELLOW}{views_progress:<10}{Style.RESET_ALL} "
                f"{Fore.MAGENTA}{time_elapsed:<10}{Style.RESET_ALL} "
                f"{status:<6}"
            )
            print(row1)
            # Second line (video ID)
            print(f"{display_lines[1]:<30}")
        else:
            # Single line
            row = (
                f"{display_name:<30} "
                f"{Fore.GREEN}{format_number(total_views):<8}{Style.DIM}/{format_number(target_views):<6}{Style.RESET_ALL} "
                f"{Fore.GREEN}{format_number(total_likes):<6}{Style.DIM}/{format_number(target_likes):<5}{Style.RESET_ALL} "
                f"{Fore.CYAN}{comments_ordered:<6}{Style.DIM}/{target_comments:<5}{Style.RESET_ALL} "
                f"{Fore.CYAN}{comment_likes_ordered:<6}{Style.DIM}/{target_comment_likes:<5}{Style.RESET_ALL} "
                f"{Fore.YELLOW}{views_progress:<10}{Style.RESET_ALL} "
                f"{Fore.MAGENTA}{time_elapsed:<10}{Style.RESET_ALL} "
                f"{status:<6}"
            )
            print(row)
    
    print(f"\n{Fore.CYAN}{'-'*120}{Style.RESET_ALL}")
    
    # Summary
    total_videos = len(progress)
    total_cost = sum(v.get('total_cost', 0) for v in progress.values())
    
    print(f"\n{Fore.CYAN}Summary:{Style.RESET_ALL}")
    print(f"  Total videos: {Fore.GREEN}{total_videos}{Style.RESET_ALL}")
    print(f"  Total cost: {Fore.GREEN}${total_cost:.4f}{Style.RESET_ALL}")
    
    # Legend
    print(f"\n{Fore.CYAN}Legend:{Style.RESET_ALL}")
    print(f"  ✅ Complete  🟢 75%+  🟡 50%+  🟠 25%+  🔴 <25%")
    print(f"  Format: {Fore.GREEN}current{Style.DIM}/target{Style.RESET_ALL}")
    print()

def display_detailed_view(video_url=None):
    """Display detailed view for a specific video or all videos"""
    progress = load_progress()
    
    if not progress:
        print(f"{Fore.YELLOW}No videos in progress.{Style.RESET_ALL}")
        return
    
    if video_url and video_url in progress:
        videos_to_show = {video_url: progress[video_url]}
    else:
        videos_to_show = progress
    
    for video_url, video_progress in videos_to_show.items():
        username, video_id = extract_video_info(video_url)
        
        print(f"\n{Fore.CYAN}{'='*80}")
        if username:
            print(f"{Fore.CYAN}Video: @{username} - {video_id}{Style.RESET_ALL}")
        else:
            print(f"{Fore.CYAN}Video: {video_url}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*80}{Style.RESET_ALL}\n")
        
        # Targets
        target_views = video_progress.get('target_views', 4000)
        target_likes = video_progress.get('target_likes', 125)
        target_comments = video_progress.get('target_comments', 7)
        target_comment_likes = video_progress.get('target_comment_likes', 15)
        
        # Current stats
        orders_placed = video_progress.get('orders_placed', {})
        initial_views = video_progress.get('initial_views', 0)
        initial_likes = video_progress.get('initial_likes', 0)
        
        views_ordered = orders_placed.get('views', 0)
        likes_ordered = orders_placed.get('likes', 0)
        comments_ordered = orders_placed.get('comments', 0)
        comment_likes_ordered = orders_placed.get('comment_likes', 0)
        
        total_views = initial_views + views_ordered
        total_likes = initial_likes + likes_ordered
        
        # Progress bars
        def progress_bar(current, target, width=30):
            if target == 0:
                return "█" * width
            pct = min(current / target, 1.0)
            filled = int(width * pct)
            bar = "█" * filled + "░" * (width - filled)
            return f"{Fore.GREEN}{bar}{Style.RESET_ALL}"
        
        # Views
        print(f"{Fore.CYAN}Views:{Style.RESET_ALL}")
        print(f"  {progress_bar(total_views, target_views)}")
        print(f"  {Fore.GREEN}{format_number(total_views)}{Style.RESET_ALL} / {format_number(target_views)} ({format_percentage(total_views, target_views)})")
        print(f"  {Style.DIM}  Existing: {format_number(initial_views)} | Ordered: {format_number(views_ordered)}{Style.RESET_ALL}\n")
        
        # Likes
        print(f"{Fore.CYAN}Likes:{Style.RESET_ALL}")
        print(f"  {progress_bar(total_likes, target_likes)}")
        print(f"  {Fore.GREEN}{format_number(total_likes)}{Style.RESET_ALL} / {format_number(target_likes)} ({format_percentage(total_likes, target_likes)})")
        print(f"  {Style.DIM}  Existing: {format_number(initial_likes)} | Ordered: {format_number(likes_ordered)}{Style.RESET_ALL}\n")
        
        # Comments
        print(f"{Fore.CYAN}Comments:{Style.RESET_ALL}")
        print(f"  {progress_bar(comments_ordered, target_comments)}")
        print(f"  {Fore.CYAN}{comments_ordered}{Style.RESET_ALL} / {target_comments} ({format_percentage(comments_ordered, target_comments)})\n")
        
        # Comment Likes
        print(f"{Fore.CYAN}Comment Likes:{Style.RESET_ALL}")
        print(f"  {progress_bar(comment_likes_ordered, target_comment_likes)}")
        print(f"  {Fore.CYAN}{comment_likes_ordered}{Style.RESET_ALL} / {target_comment_likes} ({format_percentage(comment_likes_ordered, target_comment_likes)})\n")
        
        # Time info
        start_time = video_progress.get('start_time', '')
        if start_time:
            try:
                start_dt = datetime.fromisoformat(start_time)
                elapsed = datetime.now() - start_dt
                print(f"{Fore.CYAN}Time Elapsed:{Style.RESET_ALL} {format_time_elapsed(start_time)}")
                print(f"{Fore.CYAN}Started:{Style.RESET_ALL} {start_dt.strftime('%Y-%m-%d %H:%M:%S')}\n")
            except:
                pass
        
        # Cost
        total_cost = video_progress.get('total_cost', 0)
        print(f"{Fore.CYAN}Total Cost:{Style.RESET_ALL} ${total_cost:.4f}\n")
        
        # Order history count
        order_history = video_progress.get('order_history', [])
        print(f"{Fore.CYAN}Orders Placed:{Style.RESET_ALL} {len(order_history)}\n")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == "--detailed" or sys.argv[1] == "-d":
            if len(sys.argv) > 2:
                display_detailed_view(sys.argv[2])
            else:
                display_detailed_view()
        elif sys.argv[1] == "--help" or sys.argv[1] == "-h":
            print(f"{Fore.CYAN}TikTok Bot Dashboard{Style.RESET_ALL}\n")
            print("Usage:")
            print("  python dashboard.py              - Show summary dashboard")
            print("  python dashboard.py --detailed  - Show detailed view of all videos")
            print("  python dashboard.py --detailed <video_url>  - Show detailed view of specific video")
        else:
            display_detailed_view(sys.argv[1])
    else:
        display_dashboard()

