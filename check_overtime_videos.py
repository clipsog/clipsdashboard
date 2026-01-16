#!/usr/bin/env python3
"""
Quick script to check which videos are in OVERTIME mode
and verify the continuous ordering service should be placing orders for them
"""

import json
from pathlib import Path
from datetime import datetime
import sys

# Import database if available
try:
    import database
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False

def load_progress():
    """Load progress from database or JSON"""
    if DATABASE_AVAILABLE:
        videos = database.get_all_videos()
        progress = {}
        for video in videos:
            progress[video['video_url']] = video
        return progress
    else:
        progress_file = Path.home() / '.smmfollows_bot' / 'progress.json'
        if progress_file.exists():
            with open(progress_file, 'r') as f:
                return json.load(f)
        return {}

def check_overtime_status():
    """Check which videos are in OVERTIME mode"""
    progress = load_progress()
    
    if not progress:
        print("❌ No videos found in progress")
        return
    
    print(f"\n{'='*80}")
    print(f"OVERTIME STATUS CHECK - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*80}\n")
    
    overtime_videos = []
    normal_videos = []
    stopped_videos = []
    
    for video_url, data in progress.items():
        video_id = video_url.split('/')[-1][:20]
        
        target_time_str = data.get('target_completion_time') or data.get('target_completion_datetime')
        overtime_stopped = data.get('overtime_stopped', False)
        target_views = data.get('target_views', 0)
        target_likes = data.get('target_likes', 0)
        real_views = data.get('real_views', 0)
        real_likes = data.get('real_likes', 0)
        
        if not target_time_str:
            continue
        
        try:
            target_dt = datetime.fromisoformat(target_time_str.replace('Z', '+00:00'))
            target_dt = target_dt.replace(tzinfo=None)
            now = datetime.now()
            is_past_deadline = now > target_dt
            
            views_needed = max(0, target_views - real_views)
            likes_needed = max(0, target_likes - real_likes)
            goals_reached = views_needed == 0 and likes_needed == 0
            
            status = {
                'video_id': video_id,
                'url': video_url,
                'deadline': target_dt.strftime('%Y-%m-%d %H:%M'),
                'is_past': is_past_deadline,
                'stopped': overtime_stopped,
                'views': f"{real_views}/{target_views}",
                'likes': f"{real_likes}/{target_likes}",
                'views_needed': views_needed,
                'likes_needed': likes_needed,
                'goals_reached': goals_reached
            }
            
            if is_past_deadline and not overtime_stopped and not goals_reached:
                overtime_videos.append(status)
            elif overtime_stopped:
                stopped_videos.append(status)
            else:
                normal_videos.append(status)
                
        except Exception as e:
            print(f"⚠️  Error parsing {video_id}: {e}")
    
    # Print OVERTIME videos (these should be placing orders!)
    if overtime_videos:
        print(f"🔴 OVERTIME MODE - {len(overtime_videos)} video(s) should be placing orders:")
        print(f"{'-'*80}")
        for v in overtime_videos:
            print(f"  Video: ...{v['video_id']}")
            print(f"  Deadline: {v['deadline']} (PASSED)")
            print(f"  Views: {v['views']} (need {v['views_needed']} more)")
            print(f"  Likes: {v['likes']} (need {v['likes_needed']} more)")
            print(f"  ✓ Background service should be placing orders every 30s")
            print()
    else:
        print("✅ No videos in OVERTIME mode")
    
    # Print stopped overtime videos
    if stopped_videos:
        print(f"\n⏹️  OVERTIME STOPPED - {len(stopped_videos)} video(s):")
        print(f"{'-'*80}")
        for v in stopped_videos:
            print(f"  Video: ...{v['video_id']}")
            print(f"  Status: Overtime manually stopped")
            print()
    
    # Print normal videos
    if normal_videos:
        print(f"\n⏱️  NORMAL MODE - {len(normal_videos)} video(s) on schedule:")
        print(f"{'-'*80}")
        for v in normal_videos[:5]:  # Show first 5 only
            print(f"  Video: ...{v['video_id']}")
            print(f"  Deadline: {v['deadline']}")
            print(f"  Views: {v['views']}, Likes: {v['likes']}")
        if len(normal_videos) > 5:
            print(f"  ... and {len(normal_videos) - 5} more")
        print()
    
    print(f"{'='*80}")
    print(f"SUMMARY:")
    print(f"  🔴 OVERTIME (should order): {len(overtime_videos)}")
    print(f"  ⏹️  OVERTIME STOPPED: {len(stopped_videos)}")
    print(f"  ⏱️  NORMAL (on schedule): {len(normal_videos)}")
    print(f"{'='*80}\n")
    
    if overtime_videos:
        print("⚠️  ACTION REQUIRED:")
        print("   The continuous_ordering_service.py should be placing orders for OVERTIME videos")
        print("   Check Render dashboard → worker service → Logs")
        print("   Look for: [OVERTIME MODE] messages every 30 seconds")
        print()

if __name__ == "__main__":
    check_overtime_status()
