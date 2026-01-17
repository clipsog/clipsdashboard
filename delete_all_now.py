#!/usr/bin/env python3
"""
Direct Database Reset - NO CONFIRMATION REQUIRED
Deletes all data immediately
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import database
    print("✓ Database module loaded")
except ImportError as e:
    print(f"❌ Failed to import database: {e}")
    sys.exit(1)

print("\n" + "="*60)
print("🗑️  DELETING ALL DATA FROM DATABASE")
print("="*60)

try:
    with database.get_db_connection() as conn:
        if not conn:
            print("❌ Failed to connect to database")
            sys.exit(1)
        
        cursor = conn.cursor()
        
        # Count records before deletion
        cursor.execute("SELECT COUNT(*) FROM videos")
        video_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM campaigns")
        campaign_count = cursor.fetchone()[0]
        
        print(f"\n📊 Current database:")
        print(f"   - Videos: {video_count}")
        print(f"   - Campaigns: {campaign_count}")
        
        # Delete all videos
        print("\n🗑️  Deleting all videos...")
        cursor.execute("DELETE FROM videos")
        print(f"   ✓ Deleted {video_count} videos")
        
        # Delete all campaigns
        print("🗑️  Deleting all campaigns...")
        cursor.execute("DELETE FROM campaigns")
        print(f"   ✓ Deleted {campaign_count} campaigns")
        
        # Reset sequences (auto-increment IDs)
        print("\n🔄 Resetting database sequences...")
        cursor.execute("ALTER SEQUENCE IF EXISTS videos_id_seq RESTART WITH 1")
        cursor.execute("ALTER SEQUENCE IF EXISTS campaigns_id_seq RESTART WITH 1")
        print("   ✓ Sequences reset")
        
        # Commit changes
        conn.commit()
        print("\n✅ DATABASE RESET COMPLETE!")
        print("   All videos and campaigns have been permanently deleted.")
        
        print("\n" + "="*60)
        print("⏸️  TO STOP ORDERING PROCESSES:")
        print("="*60)
        print("\n1. Go to Render Dashboard: https://dashboard.render.com/")
        print("2. Find 'continuous-ordering-service' (if running)")
        print("3. Click 'Suspend' to stop background ordering")
        print("4. Dashboard will continue but no orders will be placed")
        print("\n" + "="*60)
        
except Exception as e:
    print(f"\n❌ Error resetting database: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
