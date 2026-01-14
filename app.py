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
            
            # Process each video - check ALL active campaigns for due orders
            # This ensures we catch up on missed orders after server restarts
            now = datetime.now()
            videos_need_check = set()  # Use set for O(1) lookup and automatic deduplication
            
            for video_url in list(progress.keys()):
                try:
                    video_progress = progress.get(video_url, {})
                    
                    # Check if campaign is active (has start_time and target_completion_time)
                    has_start_time = video_progress.get('start_time') or video_progress.get('campaign_start_time')
                    has_target = video_progress.get('target_completion_time') or video_progress.get('target_completion_datetime')
                    
                    # Check if campaign is still active (target not reached or not overdue)
                    if has_target:
                        try:
                            target_time = datetime.fromisoformat(has_target.replace('Z', '+00:00'))
                            if target_time < now:
                                # Campaign target time has passed, might still have pending orders
                                # Check if there are any uncompleted purchases
                                pass
                        except:
                            pass
                    
                    # Always check videos with active campaigns (has start_time and target)
                    # The check_and_place_due_orders method will determine if orders are actually due
                    if has_start_time and has_target:
                        videos_need_check.add(video_url)
                    # Also check videos with expired timers (for immediate response)
                    # This runs independently of the campaign check above
                    next_views_time = video_progress.get('next_views_purchase_time')
                    next_likes_time = video_progress.get('next_likes_purchase_time')
                    next_comments_time = video_progress.get('next_comments_purchase_time')
                    next_comment_likes_time = video_progress.get('next_comment_likes_purchase_time')
                    
                    # Check if any timer has expired
                    if next_views_time or next_likes_time or next_comments_time or next_comment_likes_time:
                        for timer_str in [next_views_time, next_likes_time, next_comments_time, next_comment_likes_time]:
                            if timer_str:
                                try:
                                    purchase_time = datetime.fromisoformat(timer_str.replace('Z', '+00:00'))
                                    if purchase_time <= now:
                                        videos_need_check.add(video_url)  # Set automatically handles duplicates
                                        break
                                except (ValueError, TypeError):
                                    pass
                        
                except Exception as e:
                    print(f"❌ Error checking {video_url}: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Check and place due orders for videos that need checking
            for video_url in videos_need_check:
                try:
                    print(f"🔍 Checking due orders for: {video_url[:50]}...")
                    bot = DeliveryBot(video_url)
                    # Check and place due orders immediately (non-blocking)
                    orders_placed = bot.check_and_place_due_orders()
                    if orders_placed:
                        print(f"✅ Orders placed for: {video_url[:50]}")
                    else:
                        print(f"✓ No orders due for: {video_url[:50]}")
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
    
    # Initialize PostgreSQL database if available
    try:
        import database
        if database.get_database_url():
            print("🗄️ Initializing PostgreSQL database...")
            database.init_database_pool()
            if database.init_schema():
                print("🔄 Migrating existing JSON data to PostgreSQL...")
                database.migrate_from_json()
            else:
                print("⚠️ Database schema initialization failed, using JSON fallback")
        else:
            print("📁 No DATABASE_URL found, using JSON file storage")
    except ImportError:
        print("⚠️ Database module not available, using JSON files")
    except Exception as e:
        print(f"⚠️ Database initialization error: {e}, using JSON fallback")
    
    # CRITICAL: Rebuild campaigns from progress.json on startup
    # This ensures videos don't disappear after redeployment
    print("🔄 Rebuilding campaigns from progress.json...")
    try:
        import json
        from pathlib import Path
        
        campaigns_file = Path(__file__).parent / 'data' / 'campaigns.json'
        progress_file = Path(__file__).parent / 'data' / 'progress.json'
        
        if campaigns_file.exists() and progress_file.exists():
            with open(campaigns_file, 'r') as f:
                campaigns = json.load(f)
            
            with open(progress_file, 'r') as f:
                progress = json.load(f)
            
            rebuild_count = 0
            campaigns_changed = False
            
            # Ensure all campaigns have a videos list
            for campaign_id, campaign_data in campaigns.items():
                if 'videos' not in campaign_data:
                    campaign_data['videos'] = []
                    campaigns_changed = True
            
            # Rebuild videos from progress.json
            # CRITICAL: This ensures videos never disappear
            for video_url, video_data in progress.items():
                campaign_id = video_data.get('campaign_id')
                if campaign_id:
                    # Ensure campaign exists (create if missing)
                    if campaign_id not in campaigns:
                        print(f"  ⚠️ Campaign {campaign_id} not found, creating placeholder")
                        campaigns[campaign_id] = {'videos': []}
                        campaigns_changed = True
                    
                    # Ensure videos list exists
                    if 'videos' not in campaigns[campaign_id]:
                        campaigns[campaign_id]['videos'] = []
                        campaigns_changed = True
                    
                    # Add video if not already in list
                    if video_url not in campaigns[campaign_id]['videos']:
                        campaigns[campaign_id]['videos'].append(video_url)
                        campaigns_changed = True
                        rebuild_count += 1
                        print(f"  ✓ Restored video to {campaign_id}: {video_url[:50]}...")
            
            # DEFENSIVE: Double-check all videos with campaign_id are in campaigns
            for video_url, video_data in progress.items():
                campaign_id = video_data.get('campaign_id')
                if campaign_id and campaign_id in campaigns:
                    if video_url not in campaigns[campaign_id].get('videos', []):
                        if 'videos' not in campaigns[campaign_id]:
                            campaigns[campaign_id]['videos'] = []
                        campaigns[campaign_id]['videos'].append(video_url)
                        campaigns_changed = True
                        rebuild_count += 1
                        print(f"  ✓ [DEFENSIVE] Restored video to {campaign_id}: {video_url[:50]}...")
            
            # ALWAYS save campaigns after rebuild, even if nothing changed
            # This ensures the rebuilt state is persisted, especially important on Render
            # where files may reset on deployment
            import tempfile
            import shutil
            temp_fd, temp_path = tempfile.mkstemp(dir=campaigns_file.parent, suffix='.tmp')
            try:
                with os.fdopen(temp_fd, 'w') as f:
                    json.dump(campaigns, f, indent=2)
                shutil.move(temp_path, campaigns_file)
                if rebuild_count > 0:
                    print(f"✅ Rebuilt {rebuild_count} video(s) to campaigns and saved")
                else:
                    print(f"✅ Verified campaigns ({len(campaigns)} campaigns, {sum(len(c.get('videos', [])) for c in campaigns.values())} videos)")
            except Exception as e:
                if Path(temp_path).exists():
                    os.remove(temp_path)
                print(f"❌ Failed to save campaigns: {e}")
    except Exception as e:
        print(f"⚠️ Error rebuilding campaigns: {e}")
    
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
