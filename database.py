"""
PostgreSQL database module for persistent data storage
Replaces JSON file storage with PostgreSQL for reliable persistence on Render
"""

import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor
from psycopg2 import pool
from contextlib import contextmanager
from datetime import datetime
from typing import Dict, Optional, List

# Connection pool (thread-safe)
_connection_pool = None

def get_database_url():
    """Get database URL from environment or return None if not configured"""
    database_url = os.environ.get('DATABASE_URL')
    # Handle Supabase connection string format
    if database_url and '$$$$' in database_url:
        # Replace escaped $$ with single $ for password
        database_url = database_url.replace('$$$$', '$')
    return database_url

def init_database_pool():
    """Initialize database connection pool"""
    global _connection_pool
    database_url = get_database_url()
    if not database_url:
        return None
    
    try:
        _connection_pool = psycopg2.pool.SimpleConnectionPool(
            1, 20, database_url
        )
        print("✅ Database connection pool initialized")
        return _connection_pool
    except Exception as e:
        print(f"❌ Failed to initialize database pool: {e}")
        return None

@contextmanager
def get_db_connection():
    """Get database connection from pool"""
    database_url = get_database_url()
    if not database_url:
        # Fallback to JSON files if no database URL
        yield None
        return
    
    if not _connection_pool:
        init_database_pool()
    
    conn = None
    try:
        if _connection_pool:
            conn = _connection_pool.getconn()
        else:
            conn = psycopg2.connect(database_url)
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        print(f"❌ Database error: {e}")
        raise
    finally:
        if conn and _connection_pool:
            _connection_pool.putconn(conn)
        elif conn:
            conn.close()

def init_schema():
    """Initialize database schema"""
    database_url = get_database_url()
    if not database_url:
        print("⚠️ No DATABASE_URL, skipping schema initialization")
        return False
    
    try:
        with get_db_connection() as conn:
            if not conn:
                return False
            
            cursor = conn.cursor()
            
            # Videos table - stores all video progress data
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS videos (
                    video_url TEXT PRIMARY KEY,
                    data JSONB NOT NULL DEFAULT '{}'::jsonb,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Campaigns table - stores campaign data
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS campaigns (
                    campaign_id TEXT PRIMARY KEY,
                    data JSONB NOT NULL DEFAULT '{}'::jsonb,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create indexes for better performance
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_videos_campaign_id 
                ON videos ((data->>'campaign_id'))
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_videos_start_time 
                ON videos ((data->>'start_time'))
            """)
            
            conn.commit()
            print("✅ Database schema initialized")
            return True
    except Exception as e:
        print(f"❌ Failed to initialize schema: {e}")
        import traceback
        traceback.print_exc()
        return False

def load_progress() -> Dict:
    """Load all video progress from database"""
    database_url = get_database_url()
    if not database_url:
        # Fallback to JSON file
        from dashboard_server import PROGRESS_FILE
        if PROGRESS_FILE.exists():
            with open(PROGRESS_FILE, 'r') as f:
                return json.load(f)
        return {}
    
    try:
        with get_db_connection() as conn:
            if not conn:
                return {}
            
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT video_url, data FROM videos")
            rows = cursor.fetchall()
            
            progress = {}
            for row in rows:
                progress[row['video_url']] = dict(row['data'])
            
            return progress
    except Exception as e:
        print(f"❌ Error loading progress: {e}")
        import traceback
        traceback.print_exc()
        # Fallback to JSON file
        from dashboard_server import PROGRESS_FILE
        if PROGRESS_FILE.exists():
            with open(PROGRESS_FILE, 'r') as f:
                return json.load(f)
        return {}

def save_progress(progress: Dict):
    """Save video progress to database"""
    database_url = get_database_url()
    if not database_url:
        # Fallback to JSON file
        from dashboard_server import PROGRESS_FILE
        import tempfile
        import shutil
        
        PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
        temp_fd, temp_path = tempfile.mkstemp(dir=PROGRESS_FILE.parent, suffix='.tmp')
        try:
            with os.fdopen(temp_fd, 'w') as f:
                json.dump(progress, f, indent=2)
            shutil.move(temp_path, PROGRESS_FILE)
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise
        return
    
    try:
        with get_db_connection() as conn:
            if not conn:
                return
            
            cursor = conn.cursor()
            
            # Get all existing video URLs
            cursor.execute("SELECT video_url FROM videos")
            existing_urls = {row[0] for row in cursor.fetchall()}
            
            # Update or insert each video
            # CRITICAL: Never delete videos - they might be in campaigns
            # Only update existing ones or add new ones
            for video_url, video_data in progress.items():
                cursor.execute("""
                    INSERT INTO videos (video_url, data, updated_at)
                    VALUES (%s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (video_url)
                    DO UPDATE SET 
                        data = EXCLUDED.data,
                        updated_at = CURRENT_TIMESTAMP
                """, (video_url, json.dumps(video_data)))
            
            # DO NOT DELETE videos - they may still be referenced in campaigns
            # Videos should only be removed via explicit delete API call
            # This prevents videos from disappearing due to timing issues
            
            conn.commit()
    except Exception as e:
        print(f"❌ Error saving progress: {e}")
        import traceback
        traceback.print_exc()
        raise

def load_campaigns() -> Dict:
    """Load all campaigns from database"""
    database_url = get_database_url()
    if not database_url:
        # Fallback to JSON file
        from dashboard_server import CAMPAIGNS_FILE
        if CAMPAIGNS_FILE.exists():
            with open(CAMPAIGNS_FILE, 'r') as f:
                return json.load(f)
        return {}
    
    try:
        with get_db_connection() as conn:
            if not conn:
                return {}
            
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute("SELECT campaign_id, data FROM campaigns")
            rows = cursor.fetchall()
            
            campaigns = {}
            for row in rows:
                campaigns[row['campaign_id']] = dict(row['data'])
            
            return campaigns
    except Exception as e:
        print(f"❌ Error loading campaigns: {e}")
        import traceback
        traceback.print_exc()
        # Fallback to JSON file
        from dashboard_server import CAMPAIGNS_FILE
        if CAMPAIGNS_FILE.exists():
            with open(CAMPAIGNS_FILE, 'r') as f:
                return json.load(f)
        return {}

def save_campaigns(campaigns: Dict):
    """Save campaigns to database - MERGES with existing data to preserve videos"""
    database_url = get_database_url()
    if not database_url:
        # Fallback to JSON file
        from dashboard_server import CAMPAIGNS_FILE
        import tempfile
        import shutil
        
        CAMPAIGNS_FILE.parent.mkdir(parents=True, exist_ok=True)
        temp_fd, temp_path = tempfile.mkstemp(dir=CAMPAIGNS_FILE.parent, suffix='.tmp')
        try:
            with os.fdopen(temp_fd, 'w') as f:
                json.dump(campaigns, f, indent=2)
            shutil.move(temp_path, CAMPAIGNS_FILE)
        except Exception as e:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            raise
        return
    
    try:
        with get_db_connection() as conn:
            if not conn:
                return
            
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            
            # CRITICAL: Load existing campaigns FIRST to preserve video lists
            cursor.execute("SELECT campaign_id, data FROM campaigns")
            existing_campaigns = {}
            for row in cursor.fetchall():
                existing_campaigns[row['campaign_id']] = dict(row['data'])
            
            # MERGE: Preserve existing videos when updating campaigns
            for campaign_id, campaign_data in campaigns.items():
                # Get existing campaign data if it exists
                existing_data = existing_campaigns.get(campaign_id, {})
                existing_videos = existing_data.get('videos', [])
                new_videos = campaign_data.get('videos', [])
                
                # MERGE video lists - combine existing and new, remove duplicates
                merged_videos = list(set(existing_videos + new_videos))
                
                # Update campaign_data with merged videos
                merged_campaign_data = campaign_data.copy()
                merged_campaign_data['videos'] = merged_videos
                
                # Also preserve other important fields from existing data
                for key in ['created_at', 'name']:
                    if key in existing_data and key not in merged_campaign_data:
                        merged_campaign_data[key] = existing_data[key]
                
                cursor.execute("""
                    INSERT INTO campaigns (campaign_id, data, updated_at)
                    VALUES (%s, %s, CURRENT_TIMESTAMP)
                    ON CONFLICT (campaign_id)
                    DO UPDATE SET 
                        data = EXCLUDED.data,
                        updated_at = CURRENT_TIMESTAMP
                """, (campaign_id, json.dumps(merged_campaign_data)))
            
            # DO NOT DELETE campaigns - they may be referenced by videos
            # Only update/insert, never remove
            
            conn.commit()
            print(f"[DB SAVE] Saved {len(campaigns)} campaigns with merged video lists")
    except Exception as e:
        print(f"❌ Error saving campaigns: {e}")
        import traceback
        traceback.print_exc()
        raise

def migrate_from_json():
    """Migrate existing JSON data to PostgreSQL"""
    database_url = get_database_url()
    if not database_url:
        return
    
    try:
        from dashboard_server import PROGRESS_FILE, CAMPAIGNS_FILE
        
        # Migrate progress
        if PROGRESS_FILE.exists():
            with open(PROGRESS_FILE, 'r') as f:
                progress = json.load(f)
            if progress:
                save_progress(progress)
                print(f"✅ Migrated {len(progress)} videos from JSON to PostgreSQL")
        
        # Migrate campaigns
        if CAMPAIGNS_FILE.exists():
            with open(CAMPAIGNS_FILE, 'r') as f:
                campaigns = json.load(f)
            if campaigns:
                save_campaigns(campaigns)
                print(f"✅ Migrated {len(campaigns)} campaigns from JSON to PostgreSQL")
    except Exception as e:
        print(f"⚠️ Error migrating from JSON: {e}")
