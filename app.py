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
                time.sleep(300)  # Check every 5 minutes
                continue
            
            # Process each video (run delivery plan in a non-blocking way)
            for video_url in list(progress.keys()):
                try:
                    print(f"📹 Checking video: {video_url[:50]}...")
                    bot = DeliveryBot(video_url)
                    
                    # Check if there are pending orders by checking next_orders or completed_purchases
                    video_progress = progress.get(video_url, {})
                    next_orders = video_progress.get('next_orders', [])
                    completed_purchases = video_progress.get('completed_purchases', [])
                    
                    # Only run if there are orders to process
                    if next_orders or (not completed_purchases and video_progress.get('target_completion_time')):
                        print(f"🚀 Running delivery plan for: {video_url[:50]}...")
                        # Run in a thread to avoid blocking
                        bot_thread = threading.Thread(target=bot.run_delivery_plan, daemon=True)
                        bot_thread.start()
                        bot_thread.join(timeout=30)  # Wait max 30 seconds per video
                    else:
                        print(f"✓ No pending orders for: {video_url[:50]}")
                        
                except Exception as e:
                    print(f"❌ Error processing {video_url}: {e}")
                    import traceback
                    traceback.print_exc()
            
            # Wait before next cycle (check every 5 minutes)
            print("⏳ Waiting 5 minutes before next cycle...")
            time.sleep(300)
            
        except Exception as e:
            print(f"❌ Error in continuous bot: {e}")
            import traceback
            traceback.print_exc()
            time.sleep(300)

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
