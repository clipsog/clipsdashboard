#!/usr/bin/env python3
"""
Emergency Reset Script
Deletes all data from database and stops all ordering processes
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

def reset_database():
    """Delete ALL data from videos and campaigns tables"""
    print("\n" + "="*60)
    print("🚨 WARNING: This will DELETE ALL DATA from the database!")
    print("="*60)
    
    # Get confirmation
    response = input("\nType 'DELETE EVERYTHING' to confirm: ")
    if response != "DELETE EVERYTHING":
        print("❌ Reset cancelled")
        return False
    
    print("\n🗑️  Starting database reset...")
    
    try:
        with database.get_db_connection() as conn:
            if not conn:
                print("❌ Failed to connect to database")
                return False
            
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
            
            # Commit changes
            conn.commit()
            print("\n✅ Database reset complete!")
            print("   All videos and campaigns have been deleted.")
            
            return True
            
    except Exception as e:
        print(f"\n❌ Error resetting database: {e}")
        import traceback
        traceback.print_exc()
        return False

def stop_ordering_processes():
    """Instructions to stop background ordering services"""
    print("\n" + "="*60)
    print("⏸️  STOPPING ORDERING PROCESSES")
    print("="*60)
    print("\n📋 To stop all ordering processes on Render:")
    print("\n1. Go to your Render Dashboard:")
    print("   https://dashboard.render.com/")
    print("\n2. Find the 'continuous-ordering-service' worker")
    print("   (if you have one running)")
    print("\n3. Click 'Suspend' to stop the background ordering")
    print("\n4. The dashboard server will continue running but")
    print("   no automated orders will be placed")
    print("\n" + "="*60)

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🔥 EMERGENCY RESET SCRIPT")
    print("="*60)
    print("\nThis script will:")
    print("  1. Delete ALL videos from the database")
    print("  2. Delete ALL campaigns from the database")
    print("  3. Provide instructions to stop ordering services")
    
    # Reset database
    success = reset_database()
    
    if success:
        # Show instructions for stopping services
        stop_ordering_processes()
        
        print("\n✅ Reset complete!")
        print("\n📝 Next steps:")
        print("   1. Stop the continuous-ordering-service on Render (see above)")
        print("   2. Refresh your dashboard - it should be empty")
        print("   3. You can now start fresh with new campaigns")
    else:
        print("\n❌ Reset failed - see errors above")
        sys.exit(1)
