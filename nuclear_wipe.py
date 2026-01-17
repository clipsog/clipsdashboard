#!/usr/bin/env python3
"""
NUCLEAR OPTION: Wipe everything and stop all processes
Run this on Render Shell to completely reset
"""

import os
import sys
import psycopg2
from urllib.parse import urlparse

print("\n" + "="*70)
print("🚨 NUCLEAR RESET - WIPING EVERYTHING")
print("="*70 + "\n")

# Get database URL from environment
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("❌ DATABASE_URL not found in environment")
    sys.exit(1)

# Parse database URL
parsed = urlparse(DATABASE_URL)
database = parsed.path[1:]
user = parsed.username
password = parsed.password
host = parsed.hostname
port = parsed.port

print(f"📡 Connecting to database: {user}@{host}:{port}/{database}")

try:
    # Connect to database
    conn = psycopg2.connect(
        dbname=database,
        user=user,
        password=password,
        host=host,
        port=port,
        connect_timeout=10
    )
    
    conn.autocommit = True  # Important for immediate effect
    cursor = conn.cursor()
    
    print("✓ Connected to database\n")
    
    # Count data before deletion
    cursor.execute("SELECT COUNT(*) FROM videos")
    video_count = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM campaigns")
    campaign_count = cursor.fetchone()[0]
    
    print(f"📊 Current data:")
    print(f"   Videos: {video_count}")
    print(f"   Campaigns: {campaign_count}\n")
    
    if video_count == 0 and campaign_count == 0:
        print("✅ Database is already empty!")
    else:
        # TRUNCATE is faster and avoids deadlocks
        print("🗑️  Truncating tables...")
        
        # Truncate videos (CASCADE will handle foreign keys)
        cursor.execute("TRUNCATE TABLE videos CASCADE")
        print(f"   ✓ Deleted {video_count} videos")
        
        # Truncate campaigns
        cursor.execute("TRUNCATE TABLE campaigns CASCADE")
        print(f"   ✓ Deleted {campaign_count} campaigns")
        
        # Reset sequences (auto-increment counters)
        cursor.execute("ALTER SEQUENCE IF EXISTS videos_id_seq RESTART WITH 1")
        cursor.execute("ALTER SEQUENCE IF EXISTS campaigns_id_seq RESTART WITH 1")
        print("   ✓ Reset ID sequences")
    
    # Verify deletion
    cursor.execute("SELECT COUNT(*) FROM videos")
    remaining_videos = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM campaigns")
    remaining_campaigns = cursor.fetchone()[0]
    
    print(f"\n✅ WIPE COMPLETE!")
    print(f"   Videos remaining: {remaining_videos}")
    print(f"   Campaigns remaining: {remaining_campaigns}")
    
    cursor.close()
    conn.close()
    
    print("\n" + "="*70)
    print("⚠️  IMPORTANT: Now suspend 'continuous-ordering-service' on Render!")
    print("   Otherwise it will recreate data from memory/cache")
    print("="*70 + "\n")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
