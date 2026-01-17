#!/usr/bin/env python3
"""
EMERGENCY KILL SWITCH
Run this to immediately stop all ordering
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import database
    
    print("\n" + "="*60)
    print("🚨 EMERGENCY KILL SWITCH - STOPPING ALL ORDERS")
    print("="*60)
    
    # Connect to database
    with database.get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Get counts
        cursor.execute("SELECT COUNT(*) FROM videos")
        video_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM campaigns")
        campaign_count = cursor.fetchone()[0]
        
        print(f"\n📊 Current state:")
        print(f"   - {video_count} videos")
        print(f"   - {campaign_count} campaigns")
        
        # Delete EVERYTHING
        print(f"\n🗑️  Deleting all data...")
        cursor.execute("DELETE FROM videos")
        print(f"   ✓ Deleted {video_count} videos")
        
        cursor.execute("DELETE FROM campaigns")
        print(f"   ✓ Deleted {campaign_count} campaigns")
        
        conn.commit()
        
        print(f"\n✅ EMERGENCY KILL COMPLETE!")
        print(f"   - All videos deleted")
        print(f"   - All campaigns deleted")
        print(f"   - No more orders will be placed")
        print("="*60 + "\n")
        
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
    print("\nMANUAL FALLBACK:")
    print("1. Go to Render Dashboard")
    print("2. Click 'continuous-ordering-service'")
    print("3. Click 'Suspend' to stop ordering immediately")
    sys.exit(1)
