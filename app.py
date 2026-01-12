#!/usr/bin/env python3
"""
Main application entry point for Render deployment
Runs both the dashboard server and continuous delivery bot
"""

import os
import sys
import threading
import time
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

# Import dashboard server
from dashboard_server import run_server, PORT

# Import delivery bot
from run_delivery_bot import DeliveryBot

def run_continuous_bot():
    """Run delivery bot continuously for all videos"""
    print("🤖 Starting continuous delivery bot...")
    
    # Wait a bit for dashboard to start
    time.sleep(10)
    
    from datetime import datetime
    
    while True:
        try:
            # Load progress to get all videos
            from dashboard_server import DashboardHandler, PROGRESS_FILE
            import json
            
            # Load progress directly from file
            if PROGRESS_FILE.exists():
                with open(PROGRESS_FILE, 'r') as f:
                    progress = json.load(f)
            else:
                progress = {}
            
            if not progress:
                print("📭 No videos in progress, waiting...")
                time.sleep(60)  # Check every 1 minute
                continue
            
            # Process each video (run delivery plan in a non-blocking way)
            now = datetime.now()
            videos_need_check = []
            
            for video_url in list(progress.keys()):
                try:
                    video_progress = progress.get(video_url, {})
                    
                    # Check if there are pending orders by checking next_*_purchase_time fields
                    next_views_time = video_progress.get('next_views_purchase_time')
                    next_likes_time = video_progress.get('next_likes_purchase_time')
                    next_comments_time = video_progress.get('next_comments_purchase_time')
                    next_comment_likes_time = video_progress.get('next_comment_likes_purchase_time')
                    
                    # Check if any timer has expired
                    time_to_order = False
                    if next_views_time:
                        try:
                            purchase_time = datetime.fromisoformat(next_views_time.replace('Z', '+00:00'))
                            if purchase_time <= now:
                                time_to_order = True
                                print(f"⏰ Views timer expired for: {video_url[:50]}")
                        except:
                            pass
                    
                    if next_likes_time:
                        try:
                            purchase_time = datetime.fromisoformat(next_likes_time.replace('Z', '+00:00'))
                            if purchase_time <= now:
                                time_to_order = True
                                print(f"⏰ Likes timer expired for: {video_url[:50]}")
                        except:
                            pass
                    
                    if next_comments_time:
                        try:
                            purchase_time = datetime.fromisoformat(next_comments_time.replace('Z', '+00:00'))
                            if purchase_time <= now:
                                time_to_order = True
                                print(f"⏰ Comments timer expired for: {video_url[:50]}")
                        except:
                            pass
                    
                    if next_comment_likes_time:
                        try:
                            purchase_time = datetime.fromisoformat(next_comment_likes_time.replace('Z', '+00:00'))
                            if purchase_time <= now:
                                time_to_order = True
                                print(f"⏰ Comment likes timer expired for: {video_url[:50]}")
                        except:
                            pass
                    
                    # Also check if there are next_orders or if campaign is active
                    next_orders = video_progress.get('next_orders', [])
                    has_target = video_progress.get('target_completion_time')
                    
                    if time_to_order or next_orders or (has_target and not video_progress.get('completed_purchases')):
                        videos_need_check.append(video_url)
                        
                except Exception as e:
                    print(f"❌ Error checking {video_url}: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Run delivery plan for videos that need checking
            for video_url in videos_need_check:
                try:
                    print(f"🚀 Running delivery plan for: {video_url[:50]}...")
                    bot = DeliveryBot(video_url)
                    # Run in a thread to avoid blocking
                    bot_thread = threading.Thread(target=bot.run_delivery_plan, daemon=True)
                    bot_thread.start()
                    bot_thread.join(timeout=60)  # Wait max 60 seconds per video
                except Exception as e:
                    print(f"❌ Error processing {video_url}: {e}")
                    import traceback
                    traceback.print_exc()
            
            if not videos_need_check:
                print("✓ No orders due, checking again in 1 minute...")
            
            # Wait before next cycle (check every 1 minute for more accurate timing)
            time.sleep(60)
            
        except Exception as e:
            print(f"❌ Error in continuous bot: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(60)

def start_health_pinger():
    """Send periodic health pings to keep Render instance alive"""
    import requests
    
    # Get the service URL from environment or use localhost
    service_url = os.environ.get('RENDER_EXTERNAL_URL', os.environ.get('RENDER_SERVICE_URL', f'http://localhost:{PORT}'))
    
    while True:
        try:
            # Ping every 5 minutes (Render free tier sleeps after 15 min of inactivity)
            time.sleep(300)
            response = requests.get(f"{service_url}/health", timeout=10)
            if response.status_code == 200:
                print("✅ Health ping successful")
            else:
                print(f"⚠️ Health ping returned status {response.status_code}")
        except Exception as e:
            print(f"⚠️ Health ping failed: {e}")

if __name__ == '__main__':
    print("🚀 Starting SMM Follows Dashboard and Bot...")
    
    # Start continuous bot in background thread
    bot_thread = threading.Thread(target=run_continuous_bot, daemon=True)
    bot_thread.start()
    
    # Start health pinger in background thread (only if on Render)
    if os.environ.get('RENDER'):
        pinger_thread = threading.Thread(target=start_health_pinger, daemon=True)
        pinger_thread.start()
    
    # Run dashboard server (blocking)
    print(f"🌐 Starting dashboard server on port {PORT}...")
    run_server(PORT)
