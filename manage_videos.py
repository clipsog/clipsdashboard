#!/usr/bin/env python3
"""
Video Management System
View all active videos, their progress, and add new videos
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
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_progress(progress):
    """Save progress to file"""
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f, indent=2)

def format_number(num):
    """Format number with commas"""
    return f"{int(num):,}" if num else "0"

def format_percentage(current, target):
    """Calculate and format percentage"""
    if target == 0:
        return "0%"
    return f"{(current / target * 100):.1f}%"

def format_time_ago(iso_string):
    """Format ISO timestamp as time ago"""
    try:
        dt = datetime.fromisoformat(iso_string)
        now = datetime.now()
        diff = now - dt
        
        if diff.days > 0:
            return f"{diff.days}d {diff.seconds // 3600}h ago"
        elif diff.seconds >= 3600:
            hours = diff.seconds // 3600
            return f"{hours}h {diff.seconds % 3600 // 60}m ago"
        elif diff.seconds >= 60:
            return f"{diff.seconds // 60}m ago"
        else:
            return "Just now"
    except:
        return "Unknown"

def show_all_videos():
    """Display all active videos and their progress"""
    progress = load_progress()
    
    if not progress:
        print(f"{Fore.YELLOW}No videos in progress.{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Use 'python manage_videos.py add VIDEO_URL' to add a video{Style.RESET_ALL}")
        return
    
    print(f"\n{Fore.CYAN}{'='*100}")
    print(f"{Fore.GREEN}{'VIDEO MANAGEMENT DASHBOARD':^100}")
    print(f"{Fore.CYAN}{'='*100}{Style.RESET_ALL}\n")
    
    videos = []
    for video_url, video_data in progress.items():
        start_time = video_data.get('start_time', '')
        orders_placed = video_data.get('orders_placed', {})
        real_views = video_data.get('real_views', 0) or video_data.get('initial_views', 0)
        real_likes = video_data.get('real_likes', 0) or video_data.get('initial_likes', 0)
        real_comments = video_data.get('real_comments', 0) or video_data.get('initial_comments', 0)
        
        views_ordered = orders_placed.get('views', 0)
        likes_ordered = orders_placed.get('likes', 0)
        comments_ordered = orders_placed.get('comments', 0)
        comment_likes_ordered = orders_placed.get('comment_likes', 0)
        
        target_views = video_data.get('target_views', 4000)
        target_likes = video_data.get('target_likes', 125)
        target_comments = video_data.get('target_comments', 7)
        target_comment_likes = video_data.get('target_comment_likes', 15)
        
        total_views = real_views + views_ordered
        total_likes = real_likes + likes_ordered
        total_comments = real_comments + comments_ordered
        
        videos.append({
            'url': video_url,
            'start_time': start_time,
            'real_views': real_views,
            'real_likes': real_likes,
            'real_comments': real_comments,
            'views_ordered': views_ordered,
            'likes_ordered': likes_ordered,
            'comments_ordered': comments_ordered,
            'comment_likes_ordered': comment_likes_ordered,
            'total_views': total_views,
            'total_likes': total_likes,
            'total_comments': total_comments,
            'target_views': target_views,
            'target_likes': target_likes,
            'target_comments': target_comments,
            'target_comment_likes': target_comment_likes,
            'total_cost': video_data.get('total_cost', 0),
            'order_count': len(video_data.get('order_history', []))
        })
    
    # Sort by start time (newest first)
    videos.sort(key=lambda x: x['start_time'], reverse=True)
    
    for i, video in enumerate(videos, 1):
        video_id = video['url'].split('/video/')[-1].split('?')[0]
        username = video['url'].split('@')[1].split('/')[0] if '@' in video['url'] else 'unknown'
        
        print(f"{Fore.CYAN}{'─'*100}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}Video #{i}: @{username} | Video ID: {video_id[:20]}...{Style.RESET_ALL}")
        print(f"{Fore.CYAN}URL: {video['url']}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Started: {format_time_ago(video['start_time'])} ({video['start_time'][:19]}){Style.RESET_ALL}")
        print(f"{Fore.CYAN}Orders placed: {video['order_count']}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Total cost: ${video['total_cost']:.4f}{Style.RESET_ALL}\n")
        
        # Views progress
        views_pct = format_percentage(video['total_views'], video['target_views'])
        print(f"  {Fore.GREEN}Views:{Style.RESET_ALL}")
        print(f"    Current: {format_number(video['real_views'])} (existing) + {format_number(video['views_ordered'])} (ordered) = {format_number(video['total_views'])}")
        print(f"    Target: {format_number(video['target_views'])} ({views_pct})")
        if video['total_views'] >= video['target_views']:
            print(f"    {Fore.GREEN}✓ Target reached!{Style.RESET_ALL}")
        else:
            remaining = video['target_views'] - video['total_views']
            print(f"    {Fore.YELLOW}Remaining: {format_number(remaining)}{Style.RESET_ALL}")
        
        # Likes progress
        likes_pct = format_percentage(video['total_likes'], video['target_likes'])
        print(f"  {Fore.GREEN}Likes:{Style.RESET_ALL}")
        print(f"    Current: {format_number(video['real_likes'])} (existing) + {format_number(video['likes_ordered'])} (ordered) = {format_number(video['total_likes'])}")
        print(f"    Target: {format_number(video['target_likes'])} ({likes_pct})")
        if video['total_likes'] >= video['target_likes']:
            print(f"    {Fore.GREEN}✓ Target reached!{Style.RESET_ALL}")
        else:
            remaining = video['target_likes'] - video['total_likes']
            print(f"    {Fore.YELLOW}Remaining: {format_number(remaining)}{Style.RESET_ALL}")
        
        # Comments progress
        comments_pct = format_percentage(video['total_comments'], video['target_comments'])
        print(f"  {Fore.GREEN}Comments:{Style.RESET_ALL}")
        print(f"    Current: {format_number(video['real_comments'])} (existing) + {format_number(video['comments_ordered'])} (ordered) = {format_number(video['total_comments'])}")
        print(f"    Target: {format_number(video['target_comments'])} ({comments_pct})")
        if video['total_comments'] >= video['target_comments']:
            print(f"    {Fore.GREEN}✓ Target reached!{Style.RESET_ALL}")
        else:
            remaining = video['target_comments'] - video['total_comments']
            print(f"    {Fore.YELLOW}Remaining: {format_number(remaining)}{Style.RESET_ALL}")
        
        # Comment likes
        print(f"  {Fore.GREEN}Comment Likes:{Style.RESET_ALL}")
        print(f"    Ordered: {format_number(video['comment_likes_ordered'])}")
        print(f"    Target: {format_number(video['target_comment_likes'])}")
        if video['comment_likes_ordered'] >= video['target_comment_likes']:
            print(f"    {Fore.GREEN}✓ Target reached!{Style.RESET_ALL}")
        else:
            remaining = video['target_comment_likes'] - video['comment_likes_ordered']
            print(f"    {Fore.YELLOW}Remaining: {format_number(remaining)}{Style.RESET_ALL}")
        
        print()
    
    print(f"{Fore.CYAN}{'='*100}{Style.RESET_ALL}")
    print(f"\n{Fore.GREEN}Total videos in progress: {len(videos)}{Style.RESET_ALL}")
    total_cost = sum(v['total_cost'] for v in videos)
    print(f"{Fore.GREEN}Total cost across all videos: ${total_cost:.4f}{Style.RESET_ALL}\n")

def add_video(video_url):
    """Add a new video to the system"""
    if not video_url.startswith('http'):
        print(f"{Fore.RED}Error: Invalid URL format{Style.RESET_ALL}")
        return False
    
    progress = load_progress()
    
    if video_url in progress:
        print(f"{Fore.YELLOW}Video already exists in system!{Style.RESET_ALL}")
        print(f"{Fore.CYAN}URL: {video_url}{Style.RESET_ALL}")
        response = input(f"{Fore.YELLOW}Do you want to reset it? (y/n): {Style.RESET_ALL}").strip().lower()
        if response != 'y':
            print(f"{Fore.CYAN}Cancelled.{Style.RESET_ALL}")
            return False
    
    # Initialize video entry
    progress[video_url] = {
        'start_time': datetime.now().isoformat(),
        'target_views': 4000,
        'target_likes': 125,
        'target_comments': 7,
        'target_comment_likes': 15,
        'initial_views': 0,
        'initial_likes': 0,
        'initial_comments': 0,
        'real_views': 0,
        'real_likes': 0,
        'real_comments': 0,
        'orders_placed': {'views': 0, 'likes': 0, 'comments': 0, 'comment_likes': 0},
        'order_history': [],
        'next_orders': [],
        'total_cost': 0
    }
    
    save_progress(progress)
    
    print(f"{Fore.GREEN}✓ Video added successfully!{Style.RESET_ALL}")
    print(f"{Fore.CYAN}URL: {video_url}{Style.RESET_ALL}")
    print(f"\n{Fore.YELLOW}Next steps:{Style.RESET_ALL}")
    print(f"  1. Run: python run_delivery_bot.py \"{video_url}\"")
    print(f"  2. Or view all videos: python manage_videos.py list")
    
    return True

def remove_video(video_url):
    """Remove a video from the system"""
    progress = load_progress()
    
    if video_url not in progress:
        print(f"{Fore.RED}Video not found in system!{Style.RESET_ALL}")
        return False
    
    print(f"{Fore.YELLOW}Removing video:{Style.RESET_ALL}")
    print(f"{Fore.CYAN}URL: {video_url}{Style.RESET_ALL}")
    response = input(f"{Fore.YELLOW}Are you sure? (y/n): {Style.RESET_ALL}").strip().lower()
    
    if response == 'y':
        del progress[video_url]
        save_progress(progress)
        print(f"{Fore.GREEN}✓ Video removed successfully!{Style.RESET_ALL}")
        return True
    else:
        print(f"{Fore.CYAN}Cancelled.{Style.RESET_ALL}")
        return False

def main():
    """Main function"""
    if len(sys.argv) < 2:
        print(f"{Fore.CYAN}Video Management System{Style.RESET_ALL}\n")
        print(f"Usage:")
        print(f"  python manage_videos.py list              - Show all videos and progress")
        print(f"  python manage_videos.py add VIDEO_URL     - Add a new video")
        print(f"  python manage_videos.py remove VIDEO_URL  - Remove a video")
        print(f"\nExample:")
        print(f"  python manage_videos.py add \"https://www.tiktok.com/@user/video/123\"")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'list':
        show_all_videos()
    elif command == 'add':
        if len(sys.argv) < 3:
            print(f"{Fore.RED}Error: Please provide a video URL{Style.RESET_ALL}")
            print(f"{Fore.CYAN}Usage: python manage_videos.py add VIDEO_URL{Style.RESET_ALL}")
            return
        add_video(sys.argv[2])
    elif command == 'remove':
        if len(sys.argv) < 3:
            print(f"{Fore.RED}Error: Please provide a video URL{Style.RESET_ALL}")
            print(f"{Fore.CYAN}Usage: python manage_videos.py remove VIDEO_URL{Style.RESET_ALL}")
            return
        remove_video(sys.argv[2])
    else:
        print(f"{Fore.RED}Unknown command: {command}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}Use 'list', 'add', or 'remove'{Style.RESET_ALL}")

if __name__ == '__main__':
    main()


