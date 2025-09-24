#!/usr/bin/env python3
"""
Update Local Database URLs from JSONL
"""

import psycopg2
import json
import os
from tqdm import tqdm

def get_local_db_config():
    """Get local database configuration"""
    return {
        'host': 'localhost',
        'database': 'gamequest',
        'user': 'postgres',
        'password': os.environ.get('LOCAL_DB_PASSWORD', ''),
        'port': 5432
    }

def load_jsonl_data(jsonl_path):
    """Load data from JSONL file"""
    try:
        print(f"📄 Loading data from {jsonl_path}...")
        
        if not os.path.exists(jsonl_path):
            print(f"❌ File not found: {jsonl_path}")
            return None
        
        url_data = {}
        total_lines = 0
        processed_lines = 0
        
        # Count total lines first
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            total_lines = sum(1 for _ in f)
        
        print(f"📊 Found {total_lines:,} lines in JSONL file")
        
        # Process each line
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line in tqdm(f, total=total_lines, desc="Loading JSONL"):
                line = line.strip()
                if not line:
                    continue
                
                try:
                    data = json.loads(line)
                    game_id = data.get('id')
                    
                    if game_id:
                        url_data[game_id] = {
                            'sample_cover_url': data.get('sample_cover_url'),
                            'sample_screenshot_urls': data.get('sample_screenshot_urls')
                        }
                        processed_lines += 1
                
                except json.JSONDecodeError as e:
                    print(f"⚠️ JSON decode error: {e}")
                    continue
        
        print(f"✅ Loaded {processed_lines:,} games with URL data")
        return url_data
        
    except Exception as e:
        print(f"❌ Error loading JSONL: {e}")
        return None

def update_local_urls(url_data):
    """Update URLs in local database"""
    try:
        print("🔄 Updating URLs in LOCAL database...")
        
        config = get_local_db_config()
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        
        # Get total games to update
        cursor.execute("SELECT COUNT(*) FROM games WHERE id = ANY(%s);", (list(url_data.keys()),))
        total_games = cursor.fetchone()[0]
        
        print(f"📊 Found {total_games:,} games to update in local DB")
        
        if total_games == 0:
            print("❌ No matching games found!")
            return False
        
        # Update URLs
        updated_count = 0
        skipped_count = 0
        
        update_query = """
            UPDATE games 
            SET sample_cover_url = %s, sample_screenshot_urls = %s 
            WHERE id = %s;
        """
        
        for game_id, urls in tqdm(url_data.items(), desc="Updating URLs"):
            cover_url = urls.get('sample_cover_url')
            screenshot_urls = urls.get('sample_screenshot_urls')
            
            # Only update if we have actual URLs
            if cover_url or screenshot_urls:
                try:
                    cursor.execute(update_query, (cover_url, screenshot_urls, game_id))
                    updated_count += 1
                except Exception as e:
                    print(f"⚠️ Error updating game {game_id}: {e}")
                    skipped_count += 1
            else:
                skipped_count += 1
        
        # Commit changes
        conn.commit()
        
        print(f"\n✅ URL update completed!")
        print(f"   Updated: {updated_count:,} games")
        print(f"   Skipped: {skipped_count:,} games")
        
        # Verify updates
        cursor.execute("SELECT COUNT(*) FROM games WHERE sample_cover_url IS NOT NULL;")
        games_with_covers = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM games WHERE sample_screenshot_urls IS NOT NULL;")
        games_with_screenshots = cursor.fetchone()[0]
        
        print(f"\n🎯 Verification:")
        print(f"   Games with cover URLs: {games_with_covers:,}")
        print(f"   Games with screenshot URLs: {games_with_screenshots:,}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"❌ Error updating URLs: {e}")
        return False

def show_sample_updates():
    """Show sample of updated games"""
    try:
        print("\n🔍 Sample of updated games:")
        
        config = get_local_db_config()
        conn = psycopg2.connect(**config)
        cursor = conn.cursor()
        
        # Show games with cover URLs
        cursor.execute("""
            SELECT id, title, sample_cover_url 
            FROM games 
            WHERE sample_cover_url IS NOT NULL 
            LIMIT 3;
        """)
        games_with_covers = cursor.fetchall()
        
        if games_with_covers:
            print("\n🖼️ Games with cover URLs:")
            for game in games_with_covers:
                game_id, title, cover_url = game
                print(f"   {game_id}: {title[:50]}...")
                print(f"      Cover: {cover_url}")
        
        # Show games with screenshot URLs
        cursor.execute("""
            SELECT id, title, sample_screenshot_urls 
            FROM games 
            WHERE sample_screenshot_urls IS NOT NULL 
            LIMIT 3;
        """)
        games_with_screenshots = cursor.fetchall()
        
        if games_with_screenshots:
            print("\n📸 Games with screenshot URLs:")
            for game in games_with_screenshots:
                game_id, title, screenshot_urls = game
                print(f"   {game_id}: {title[:50]}...")
                print(f"      Screenshots: {len(screenshot_urls) if screenshot_urls else 0} URLs")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error showing samples: {e}")

if __name__ == "__main__":
    print("🎮 GameQuest Local URL Updater")
    print("=" * 40)
    
    # Path to JSONL file
    jsonl_path = "data/mobygames_index_updated_dates.jsonl"
    
    print(f"\n🚀 Starting LOCAL URL update process...")
    print(f"📄 JSONL file: {jsonl_path}")
    print("💡 This will update your local DB first, then you can migrate to Aiven!")
    
    # Step 1: Load JSONL data
    print("\n📦 Step 1: Loading JSONL data...")
    url_data = load_jsonl_data(jsonl_path)
    
    if not url_data:
        print("❌ Cannot proceed without URL data")
        exit(1)
    
    # Step 2: Update local database
    print("\n🔄 Step 2: Updating LOCAL database...")
    if update_local_urls(url_data):
        print("\n🎉 LOCAL URL update completed successfully!")
        
        # Step 3: Show samples
        show_sample_updates()
        
        print("\n✅ Next step: Run 'python migrate_to_aiven.py' to migrate everything to Aiven!")
    else:
        print("\n❌ URL update failed!")