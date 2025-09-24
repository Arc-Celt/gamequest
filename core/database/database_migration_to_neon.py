#!/usr/bin/env python3
"""
Final migration script to migrate local database to Neon PostgreSQL
This includes the updated URLs and optimized schema
"""

import os
import psycopg2
import sys
from tqdm import tqdm
import time

# Database configurations
LOCAL_DB_CONFIG = {
    'host': os.environ.get('LOCAL_DB_HOST', 'localhost'),
    'database': os.environ.get('LOCAL_DB_NAME', 'gamequest'),
    'user': os.environ.get('LOCAL_DB_USER', 'postgres'),
    'password': os.environ.get('LOCAL_DB_PASSWORD', ''),
    'port': int(os.environ.get('LOCAL_DB_PORT', 5432))
}

NEON_DB_CONFIG = {
    'host': os.environ.get('DB_HOST', 'localhost'),
    'database': os.environ.get('DB_NAME', 'postgres'),
    'user': os.environ.get('DB_USER', 'postgres'),
    'password': os.environ.get('DB_PASSWORD', ''),
    'port': int(os.environ.get('DB_PORT', 5432)),
    'sslmode': os.environ.get('DB_SSLMODE', 'require'),
    'channel_binding': 'require'
}

def get_local_connection():
    """Get connection to local database"""
    return psycopg2.connect(**LOCAL_DB_CONFIG)

def get_neon_connection():
    """Get connection to Neon database"""
    return psycopg2.connect(**NEON_DB_CONFIG)

def create_neon_schema():
    """Create schema in Neon database"""
    print("🏗️  Creating schema in Neon database...")
    
    conn = get_neon_connection()
    cursor = conn.cursor()
    
    try:
        # Create games table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS games (
                id SERIAL PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                release_date DATE,
                moby_score REAL,
                moby_url TEXT,
                platforms TEXT[],
                genres TEXT[],
                developers TEXT[],
                publishers TEXT[],
                sample_cover_url TEXT,
                sample_screenshot_urls TEXT[]
            );
        """)
        
        # Create critics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS critics (
                review_id SERIAL PRIMARY KEY,
                game_id INTEGER REFERENCES games(id) ON DELETE CASCADE,
                citation TEXT
            );
        """)
        
        # Create games_with_critics view
        cursor.execute("""
            CREATE OR REPLACE VIEW games_with_critics AS
            SELECT g.id,
                   g.title,
                   g.description,
                   g.release_date,
                   g.moby_score,
                   g.moby_url,
                   g.platforms,
                   g.genres,
                   g.developers,
                   g.publishers,
                   g.sample_cover_url,
                   g.sample_screenshot_urls,
                   ARRAY_AGG(c.citation) AS all_critics
            FROM games g
            LEFT JOIN critics c ON g.id = c.game_id
            GROUP BY g.id, g.title, g.description, g.release_date, g.moby_score, 
                     g.moby_url, g.platforms, g.genres, g.developers, g.publishers,
                     g.sample_cover_url, g.sample_screenshot_urls;
        """)
        
        conn.commit()
        print("✅ Schema created successfully")
        
    except Exception as e:
        print(f"❌ Error creating schema: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def migrate_games_data():
    """Migrate games data from local to Neon"""
    print("\n🎮 Migrating games data...")
    
    local_conn = get_local_connection()
    neon_conn = get_neon_connection()
    
    local_cursor = local_conn.cursor()
    neon_cursor = neon_conn.cursor()
    
    try:
        # Get total count
        local_cursor.execute("SELECT COUNT(*) FROM games;")
        total_games = local_cursor.fetchone()[0]
        print(f"📊 Found {total_games:,} games to migrate")
        
        # Get games data in batches
        batch_size = 1000
        migrated = 0
        
        for offset in tqdm(range(0, total_games, batch_size), desc="Migrating games"):
            local_cursor.execute("""
                SELECT id, title, description, release_date, moby_score, moby_url,
                       platforms, genres, developers, publishers, 
                       sample_cover_url, sample_screenshot_urls
                FROM games 
                ORDER BY id 
                LIMIT %s OFFSET %s
            """, (batch_size, offset))
            
            games_batch = local_cursor.fetchall()
            
            for game in games_batch:
                try:
                    neon_cursor.execute("""
                        INSERT INTO games (id, title, description, release_date, moby_score, moby_url,
                                         platforms, genres, developers, publishers,
                                         sample_cover_url, sample_screenshot_urls)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """, game)
                    migrated += 1
                    
                except Exception as e:
                    if "duplicate key value" in str(e):
                        # Skip duplicate
                        continue
                    else:
                        print(f"⚠️  Error inserting game {game[0]}: {e}")
                        continue
            
            # Commit batch
            neon_conn.commit()
            
            # Small delay to avoid overwhelming Neon
            time.sleep(0.1)
        
        print(f"✅ Migrated {migrated:,} games successfully")
        
    except Exception as e:
        print(f"❌ Error migrating games: {e}")
        neon_conn.rollback()
        raise
    finally:
        local_cursor.close()
        local_conn.close()
        neon_cursor.close()
        neon_conn.close()

def migrate_critics_data():
    """Migrate critics data from local to Neon"""
    print("\n📝 Migrating critics data...")
    
    local_conn = get_local_connection()
    neon_conn = get_neon_connection()
    
    local_cursor = local_conn.cursor()
    neon_cursor = neon_conn.cursor()
    
    try:
        # Get total count
        local_cursor.execute("SELECT COUNT(*) FROM critics;")
        total_critics = local_cursor.fetchone()[0]
        print(f"📊 Found {total_critics:,} critic reviews to migrate")
        
        # Get critics data in batches
        batch_size = 1000
        migrated = 0
        
        for offset in tqdm(range(0, total_critics, batch_size), desc="Migrating critics"):
            local_cursor.execute("""
                SELECT game_id, citation
                FROM critics 
                ORDER BY review_id 
                LIMIT %s OFFSET %s
            """, (batch_size, offset))
            
            critics_batch = local_cursor.fetchall()
            
            for critic in critics_batch:
                try:
                    neon_cursor.execute("""
                        INSERT INTO critics (game_id, citation)
                        VALUES (%s, %s)
                    """, critic)
                    migrated += 1
                    
                except Exception as e:
                    print(f"⚠️  Error inserting critic: {e}")
                    continue
            
            # Commit batch
            neon_conn.commit()
            
            # Small delay to avoid overwhelming Neon
            time.sleep(0.1)
        
        print(f"✅ Migrated {migrated:,} critic reviews successfully")
        
    except Exception as e:
        print(f"❌ Error migrating critics: {e}")
        neon_conn.rollback()
        raise
    finally:
        local_cursor.close()
        local_conn.close()
        neon_cursor.close()
        neon_conn.close()

def verify_migration():
    """Verify the migration was successful"""
    print("\n🔍 Verifying migration...")
    
    conn = get_neon_connection()
    cursor = conn.cursor()
    
    try:
        # Check games count
        cursor.execute("SELECT COUNT(*) FROM games;")
        games_count = cursor.fetchone()[0]
        
        # Check critics count
        cursor.execute("SELECT COUNT(*) FROM critics;")
        critics_count = cursor.fetchone()[0]
        
        # Check URLs
        cursor.execute("SELECT COUNT(*) FROM games WHERE sample_cover_url IS NOT NULL;")
        games_with_covers = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM games WHERE sample_screenshot_urls IS NOT NULL;")
        games_with_screenshots = cursor.fetchone()[0]
        
        # Check database size
        cursor.execute("SELECT pg_size_pretty(pg_database_size(current_database()));")
        db_size = cursor.fetchone()[0]
        
        print(f"📊 Migration Summary:")
        print(f"  - Games: {games_count:,}")
        print(f"  - Critic reviews: {critics_count:,}")
        print(f"  - Games with covers: {games_with_covers:,}")
        print(f"  - Games with screenshots: {games_with_screenshots:,}")
        print(f"  - Database size: {db_size}")
        
        # Test a sample query
        cursor.execute("SELECT title, sample_cover_url FROM games WHERE sample_cover_url IS NOT NULL LIMIT 3;")
        sample_games = cursor.fetchall()
        
        print(f"\n🎯 Sample games with URLs:")
        for game in sample_games:
            print(f"  - {game[0]}: {game[1][:50]}..." if game[1] else f"  - {game[0]}: No URL")
        
        return True
        
    except Exception as e:
        print(f"❌ Error verifying migration: {e}")
        return False
    finally:
        cursor.close()
        conn.close()

def main():
    """Main migration function"""
    print("🚀 Starting migration to Neon PostgreSQL...")
    print(f"📡 Target: {NEON_DB_CONFIG['host']}")
    
    try:
        # Step 1: Create schema
        create_neon_schema()
        
        # Step 2: Migrate games
        migrate_games_data()
        
        # Step 3: Migrate critics
        migrate_critics_data()
        
        # Step 4: Verify
        if verify_migration():
            print("\n🎉 Migration completed successfully!")
            print("✅ Your GameQuest database is now ready on Neon!")
        else:
            print("\n⚠️  Migration completed with some issues")
            
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()