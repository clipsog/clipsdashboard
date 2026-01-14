"""
PostgreSQL database module for persistent data storage
Replaces JSON file storage with PostgreSQL for reliable persistence on Render
"""

import os
import json
import time
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
    if not database_url:
        return None
    
    # Check for placeholder or malformed URL
    if '[YOUR-PASSWORD]' in database_url or 'password' in database_url.lower():
        print("❌ DATABASE_URL contains placeholder - please set actual password in Render dashboard")
        return None
    
    # Debug: Log host info (without password)
    if database_url:
        host_part = database_url.split('@')[-1] if '@' in database_url else 'unknown'
        print(f"[DB] DATABASE_URL found (host: {host_part})")
    
    return database_url

def init_database_pool():
    """Initialize database connection pool with retry logic"""
    global _connection_pool
    database_url = get_database_url()
    if not database_url:
        return None
    
    # Try direct connection port (5432) if pooler (6543) fails
    # Supabase pooler can have circuit breaker issues
    urls_to_try = [database_url]
    
    # If using pooler port (6543), also try direct port (5432)
    if ':6543' in database_url:
        direct_url = database_url.replace(':6543', ':5432')
        urls_to_try.append(direct_url)
        print(f"   Will try pooler (6543) first, then direct (5432) if needed")
    
    for attempt, url in enumerate(urls_to_try, 1):
        try:
            # Test connection first
            test_conn = psycopg2.connect(url, connect_timeout=5)
            test_conn.close()
            
            # If test succeeds, create pool
            _connection_pool = psycopg2.pool.SimpleConnectionPool(
                1, 10, url, connect_timeout=5
            )
            print(f"✅ Database connection pool initialized (attempt {attempt})")
            return _connection_pool
        except psycopg2.OperationalError as e:
            if 'Circuit breaker' in str(e) or 'authentication' in str(e).lower():
                if attempt < len(urls_to_try):
                    print(f"   ⚠️ Connection attempt {attempt} failed (circuit breaker), trying next...")
                    continue
                else:
                    print(f"❌ All connection attempts failed: {e}")
                    print(f"   Circuit breaker is open - too many auth errors")
                    print(f"   Please check DATABASE_URL password in Render dashboard")
                    return None
            else:
                print(f"❌ Connection error: {e}")
                if attempt < len(urls_to_try):
                    continue
                return None
        except Exception as e:
            print(f"❌ Failed to initialize database pool: {e}")
            if attempt < len(urls_to_try):
                continue
            return None
    
    return None

@contextmanager
def get_db_connection():
    """Get database connection from pool with retry logic"""
    global _connection_pool
    
    database_url = get_database_url()
    if not database_url:
        yield None
        return
    
    if not _connection_pool:
        init_database_pool()
    
    conn = None
    max_retries = 3
    retry_delay = 1
    
    try:
        for attempt in range(max_retries):
            try:
                if _connection_pool:
                    conn = _connection_pool.getconn()
                else:
                    # Fallback to direct connection if pool unavailable
                    conn = psycopg2.connect(database_url, connect_timeout=5)
                
                # Test the connection
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                
                yield conn
                conn.commit()
                break  # Success, exit retry loop
                
            except psycopg2.OperationalError as e:
                if conn:
                    try:
                        conn.rollback()
                        if _connection_pool:
                            _connection_pool.putconn(conn)
                        else:
                            conn.close()
                    except:
                        pass
                    conn = None
                
                if 'Circuit breaker' in str(e):
                    if attempt < max_retries - 1:
                        print(f"   ⚠️ Circuit breaker open, retrying in {retry_delay}s... (attempt {attempt + 1}/{max_retries})")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                        # Reinitialize pool on circuit breaker
                        _connection_pool = None
                        init_database_pool()
                        continue
                    else:
                        print(f"❌ Database circuit breaker still open after {max_retries} attempts")
                        raise
                else:
                    print(f"❌ Database error: {e}")
                    raise
                    
            except Exception as e:
                if conn:
                    try:
                        conn.rollback()
                    except:
                        pass
                print(f"❌ Database error: {e}")
                raise
        else:
            # All retries exhausted
            raise Exception("Failed to get database connection after retries")
    finally:
        if conn and _connection_pool:
            try:
                _connection_pool.putconn(conn)
            except:
                pass
        elif conn:
            try:
                conn.close()
            except:
                pass

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
        print("❌ No DATABASE_URL - cannot save progress! Data will be lost!")
        raise Exception("DATABASE_URL not configured - cannot persist data")
    
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
        print("❌ No DATABASE_URL - cannot save campaigns! Data will be lost!")
        raise Exception("DATABASE_URL not configured - cannot persist data")
    
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
    """Migrate existing JSON data to PostgreSQL - PRESERVES existing database data"""
    database_url = get_database_url()
    if not database_url:
        print("⚠️ No DATABASE_URL, skipping migration")
        return
    
    try:
        from dashboard_server import PROGRESS_FILE, CAMPAIGNS_FILE
        
        # Load existing database data FIRST to preserve it
        existing_progress = load_progress()
        existing_campaigns = load_campaigns()
        
        print(f"[MIGRATION] Existing DB: {len(existing_progress)} videos, {len(existing_campaigns)} campaigns")
        
        # Migrate progress - MERGE with existing
        json_progress = {}
        if PROGRESS_FILE.exists():
            with open(PROGRESS_FILE, 'r') as f:
                json_progress = json.load(f)
            print(f"[MIGRATION] JSON file: {len(json_progress)} videos")
        
        # Merge: existing database + JSON file (database takes precedence)
        merged_progress = existing_progress.copy()
        for video_url, video_data in json_progress.items():
            if video_url not in merged_progress:
                merged_progress[video_url] = video_data
                print(f"[MIGRATION] Adding video from JSON: {video_url[:50]}...")
        
        if merged_progress:
            save_progress(merged_progress)
            print(f"✅ Migrated {len(merged_progress)} videos (preserved {len(existing_progress)} existing)")
        
        # Migrate campaigns - MERGE with existing (preserve video lists)
        json_campaigns = {}
        if CAMPAIGNS_FILE.exists():
            with open(CAMPAIGNS_FILE, 'r') as f:
                json_campaigns = json.load(f)
            print(f"[MIGRATION] JSON file: {len(json_campaigns)} campaigns")
        
        # Merge campaigns - preserve video lists from both sources
        merged_campaigns = existing_campaigns.copy()
        for campaign_id, campaign_data in json_campaigns.items():
            if campaign_id in merged_campaigns:
                # Merge video lists
                existing_videos = set(merged_campaigns[campaign_id].get('videos', []))
                json_videos = set(campaign_data.get('videos', []))
                merged_videos = list(existing_videos | json_videos)  # Union of both sets
                merged_campaigns[campaign_id]['videos'] = merged_videos
                print(f"[MIGRATION] Merged campaign {campaign_id}: {len(existing_videos)} existing + {len(json_videos)} JSON = {len(merged_videos)} total videos")
            else:
                merged_campaigns[campaign_id] = campaign_data
                print(f"[MIGRATION] Adding new campaign from JSON: {campaign_id}")
        
        if merged_campaigns:
            save_campaigns(merged_campaigns)
            print(f"✅ Migrated {len(merged_campaigns)} campaigns (preserved {len(existing_campaigns)} existing)")
        
        # CRITICAL: Rebuild campaigns from progress to ensure all videos are in campaigns
        print("[MIGRATION] Rebuilding campaigns from progress...")
        rebuild_count = 0
        for video_url, video_data in merged_progress.items():
            campaign_id = video_data.get('campaign_id')
            if campaign_id:
                if campaign_id not in merged_campaigns:
                    merged_campaigns[campaign_id] = {'videos': []}
                if 'videos' not in merged_campaigns[campaign_id]:
                    merged_campaigns[campaign_id]['videos'] = []
                if video_url not in merged_campaigns[campaign_id]['videos']:
                    merged_campaigns[campaign_id]['videos'].append(video_url)
                    rebuild_count += 1
                    print(f"[MIGRATION] Rebuilt: Added {video_url[:50]}... to {campaign_id}")
        
        if rebuild_count > 0:
            save_campaigns(merged_campaigns)
            print(f"✅ Rebuilt {rebuild_count} video(s) into campaigns after migration")
        
    except Exception as e:
        print(f"⚠️ Error migrating from JSON: {e}")
        import traceback
        traceback.print_exc()
