#!/usr/bin/env python3
"""
Wipe all data from Supabase database
This will delete all videos and campaigns
"""

import os
import sys

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

try:
    import database
    
    def wipe_all_data():
        """Delete all videos and campaigns from database"""
        database_url = database.get_database_url()
        if not database_url:
            print("❌ No DATABASE_URL configured!")
            print("   Please set DATABASE_URL environment variable")
            return False
        
        print("🗑️  Wiping all data from Supabase database...")
        
        try:
            with database.get_db_connection() as conn:
                if not conn:
                    print("❌ Failed to connect to database")
                    return False
                
                cursor = conn.cursor()
                
                # Delete all videos
                cursor.execute("DELETE FROM videos")
                videos_deleted = cursor.rowcount
                print(f"   ✅ Deleted {videos_deleted} videos")
                
                # Delete all campaigns
                cursor.execute("DELETE FROM campaigns")
                campaigns_deleted = cursor.rowcount
                print(f"   ✅ Deleted {campaigns_deleted} campaigns")
                
                conn.commit()
                print(f"\n✅ Successfully wiped all data!")
                print(f"   Videos deleted: {videos_deleted}")
                print(f"   Campaigns deleted: {campaigns_deleted}")
                return True
                
        except Exception as e:
            print(f"❌ Error wiping database: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    if __name__ == "__main__":
        print("⚠️  WARNING: This will delete ALL videos and campaigns!")
        response = input("Type 'YES' to confirm: ")
        if response == 'YES':
            wipe_all_data()
        else:
            print("Cancelled.")

except ImportError as e:
    print(f"❌ Failed to import database module: {e}")
    sys.exit(1)
