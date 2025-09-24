#!/usr/bin/env python3
"""
Optimized GameQuest Database Migration Script
Handles 180K+ metadata.json files safely with batch processing
"""

import json
import psycopg2
import psycopg2.extras
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Configuration
DATA_ROOT = Path("G:/Data/images")
INDEX_FILE = Path("data/mobygames_index_updated_dates.jsonl")
BATCH_SIZE = 1000
MAX_WORKERS = 4
CHUNK_SIZE = 100

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'database': 'gamequest',
    'user': 'postgres',
    'password': 'ST5780@BCsp'
}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/migration.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class GameMigrator:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.games_index = {}
        self.stats = {
            'total_games': 0,
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'start_time': None
        }
        self.lock = threading.Lock()

    def connect_db(self):
        """Establish database connection with retry logic"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.conn = psycopg2.connect(**DB_CONFIG)
                self.conn.autocommit = False
                self.cursor = self.conn.cursor()
                logger.info(f"✅ Database connected successfully (attempt {attempt + 1})")
                return True
            except Exception as e:
                logger.warning(f"❌ Connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
        return False

    def close_db(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info("🔒 Database connection closed")

    def load_games_index(self):
        """Load authoritative games metadata from index file"""
        logger.info(f"📖 Loading games index from {INDEX_FILE}...")

        if not INDEX_FILE.exists():
            logger.error(f"❌ Index file not found: {INDEX_FILE}")
            return False

        try:
            with open(INDEX_FILE, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        game_data = json.loads(line.strip())
                        game_id = game_data.get('id')
                        if game_id:
                            self.games_index[game_id] = game_data
                    except json.JSONDecodeError as e:
                        logger.warning(f"⚠️ JSON decode error on line {line_num}: {e}")
                        continue
                    except Exception as e:
                        logger.warning(f"⚠️ Error processing line {line_num}: {e}")
                        continue

            logger.info(f"✅ Loaded {len(self.games_index):,} games from index")
            return True

        except Exception as e:
            logger.error(f"❌ Error loading games index: {e}")
            return False

    def get_games_to_process(self) -> List[Dict[str, Any]]:
        """Get list of games to process from index, checking for local folders"""
        logger.info(f"🔍 Checking which games have local folders in {DATA_ROOT}...")

        if not DATA_ROOT.exists():
            logger.error(f"❌ Data root path does not exist: {DATA_ROOT}")
            return []

        games_to_process = []

        try:
            # Get all existing game folders efficiently using os.scandir
            existing_folders = set()
            import os
            with os.scandir(DATA_ROOT) as entries:
                for entry in entries:
                    if entry.is_dir() and entry.name.isdigit():
                        existing_folders.add(int(entry.name))

            logger.info(f"📁 Found {len(existing_folders):,} existing game folders")

            # Match existing folders with games in index
            for game_id, game_data in self.games_index.items():
                if game_id in existing_folders:
                    game_folder = DATA_ROOT / str(game_id)
                    games_to_process.append({
                        'game_id': game_id,
                        'game_data': game_data,
                        'folder_path': game_folder
                    })

        except Exception as e:
            logger.error(f"❌ Error checking game folders: {e}")
            return []

        logger.info(f"📁 Found {len(games_to_process):,} games with local folders")
        return games_to_process


    def extract_image_paths(self, folder_path: Path, game_id: str, game_data: Dict[str, Any]) -> tuple:
        """Extract cover and screenshot paths from local files or JSONL URLs"""
        cover_path = None
        screenshot_paths = []
        
        try:
            # First, try to find local files
            cover_file = folder_path / "cover.jpg"
            if cover_file.exists():
                cover_path = str(cover_file)
            
            # Look for local screenshot files
            for file in folder_path.glob("screenshot_*.jpg"):
                screenshot_paths.append(str(file))
            
            # If no local cover found, use URL from JSONL data
            if not cover_path and game_data.get('sample_cover_url'):
                cover_path = game_data['sample_cover_url']
            
            # If no local screenshots found, use URLs from JSONL data
            if not screenshot_paths and game_data.get('sample_screenshot_urls'):
                screenshot_paths = game_data['sample_screenshot_urls']
                
        except Exception as e:
            logger.warning(f"⚠️ Error extracting image paths for {game_id}: {e}")
        
        return cover_path, screenshot_paths
    
    def prepare_game_data(self, game_info: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare game data for database insertion using authoritative index data"""
        game_id = game_info['game_id']
        game_data = game_info['game_data']
        folder_path = game_info['folder_path']
        
        # Extract image paths from local folder or JSONL URLs
        cover_path, screenshot_paths = self.extract_image_paths(folder_path, str(game_id), game_data)
        
        # Use authoritative data from index file (correct release dates, etc.)
        prepared_data = {
            'id': game_id,
            'title': game_data.get('title', '').strip(),
            'description': self.clean_html(game_data.get('description', '')),
            'release_date': game_data.get('release_date'),  # Already in correct format from index
            'moby_score': self.safe_float(game_data.get('moby_score')),
            'moby_url': game_data.get('moby_url', '').strip(),
            'platforms': self.safe_list(game_data.get('platforms', [])),
            'genres': self.safe_list(game_data.get('genres', [])),
            'developers': self.safe_list(game_data.get('developers', [])),
            'publishers': self.safe_list(game_data.get('publishers', [])),
            'cover_path': cover_path,
            'screenshot_paths': screenshot_paths
        }
        
        return prepared_data
    
    def clean_html(self, text: str) -> str:
        """Remove HTML tags from text"""
        if not text:
            return ''
        import re
        # Remove HTML tags
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text).strip()
    
    def parse_date(self, date_str: str) -> Optional[str]:
        """Parse date string safely"""
        if not date_str:
            return None
        try:
            # Try common date formats
            for fmt in ['%Y-%m-%d', '%Y', '%m/%d/%Y', '%d/%m/%Y']:
                try:
                    parsed = datetime.strptime(str(date_str), fmt)
                    return parsed.strftime('%Y-%m-%d')
                except ValueError:
                    continue
            return None
        except (ValueError, TypeError):
            return None
    
    def safe_float(self, value: Any) -> Optional[float]:
        """Convert to float safely"""
        if value is None or value == '':
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None
    
    def safe_list(self, value: Any) -> List[str]:
        """Convert to list of strings safely"""
        if not value:
            return []
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        return [str(value).strip()] if str(value).strip() else []
    
    def insert_games_batch(self, games_batch: List[Dict[str, Any]]) -> int:
        """Insert a batch of games into database"""
        if not games_batch:
            return 0
        
        insert_query = """
        INSERT INTO games (
            id, title, description, release_date, moby_score, moby_url,
            platforms, genres, developers, publishers, cover_path, screenshot_paths
        ) VALUES (
            %(id)s, %(title)s, %(description)s, %(release_date)s, %(moby_score)s, %(moby_url)s,
            %(platforms)s, %(genres)s, %(developers)s, %(publishers)s, %(cover_path)s, %(screenshot_paths)s
        ) ON CONFLICT (id) DO UPDATE SET
            title = EXCLUDED.title,
            description = EXCLUDED.description,
            release_date = EXCLUDED.release_date,
            moby_score = EXCLUDED.moby_score,
            moby_url = EXCLUDED.moby_url,
            platforms = EXCLUDED.platforms,
            genres = EXCLUDED.genres,
            developers = EXCLUDED.developers,
            publishers = EXCLUDED.publishers,
            cover_path = EXCLUDED.cover_path,
            screenshot_paths = EXCLUDED.screenshot_paths
        """
        
        try:
            psycopg2.extras.execute_batch(
                self.cursor, insert_query, games_batch, page_size=100
            )
            self.conn.commit()
            return len(games_batch)
        except Exception as e:
            logger.error(f"❌ Batch insert failed: {e}")
            self.conn.rollback()
            return 0
    
    def process_games_chunk(self, games_chunk: List[Dict[str, Any]]) -> Dict[str, int]:
        """Process a chunk of games in a thread"""
        chunk_stats = {'successful': 0, 'failed': 0, 'skipped': 0}
        games_batch = []
        
        for game_info in games_chunk:
            try:
                # Prepare data using authoritative index data
                game_data = self.prepare_game_data(game_info)
                games_batch.append(game_data)
                
                # Insert when batch is full
                if len(games_batch) >= CHUNK_SIZE:
                    inserted = self.insert_games_batch(games_batch)
                    chunk_stats['successful'] += inserted
                    chunk_stats['failed'] += len(games_batch) - inserted
                    games_batch = []
                    
            except Exception as e:
                logger.warning(f"⚠️ Error processing game {game_info['game_id']}: {e}")
                chunk_stats['failed'] += 1
        
        # Insert remaining games
        if games_batch:
            inserted = self.insert_games_batch(games_batch)
            chunk_stats['successful'] += inserted
            chunk_stats['failed'] += len(games_batch) - inserted
        
        return chunk_stats
    
    def update_stats(self, chunk_stats: Dict[str, int]):
        """Thread-safe stats update"""
        with self.lock:
            self.stats['successful'] += chunk_stats['successful']
            self.stats['failed'] += chunk_stats['failed']
            self.stats['skipped'] += chunk_stats['skipped']
            self.stats['processed'] += (chunk_stats['successful'] + 
                                      chunk_stats['failed'] + 
                                      chunk_stats['skipped'])
    
    def print_progress(self):
        """Print migration progress"""
        elapsed = time.time() - self.stats['start_time']
        rate = self.stats['processed'] / elapsed if elapsed > 0 else 0
        eta = (self.stats['total_games'] - self.stats['processed']) / rate if rate > 0 else 0
        
        logger.info(f"📊 Progress: {self.stats['processed']:,}/{self.stats['total_games']:,} "
                   f"({self.stats['processed']/self.stats['total_games']*100:.1f}%) | "
                   f"✅ {self.stats['successful']:,} | ❌ {self.stats['failed']:,} | ⏭️ {self.stats['skipped']:,} | "
                   f"⏱️ {rate:.1f}/s | ETA: {eta/60:.1f}m")
    
    def migrate_all_games(self):
        """Main migration function"""
        logger.info("🚀 Starting GameQuest database migration...")
        self.stats['start_time'] = time.time()
        
        # Load authoritative games index first
        if not self.load_games_index():
            logger.error("❌ Failed to load games index")
            return False
        
        # Connect to database
        if not self.connect_db():
            logger.error("❌ Failed to connect to database")
            return False
        
        try:
            # Get games to process (those with local folders)
            games_to_process = self.get_games_to_process()
            if not games_to_process:
                logger.error("❌ No games with local folders found")
                return False
            
            self.stats['total_games'] = len(games_to_process)
            logger.info(f"📁 Processing {len(games_to_process):,} games with local folders...")
            
            # Process in parallel chunks
            games_chunks = [games_to_process[i:i+CHUNK_SIZE] for i in range(0, len(games_to_process), CHUNK_SIZE)]
            
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
                # Submit all chunks
                future_to_chunk = {
                    executor.submit(self.process_games_chunk, chunk): chunk 
                    for chunk in games_chunks
                }
                
                # Process completed chunks
                for future in as_completed(future_to_chunk):
                    chunk_stats = future.result()
                    self.update_stats(chunk_stats)
                    
                    # Print progress every 10 chunks
                    if self.stats['processed'] % (CHUNK_SIZE * 10) == 0:
                        self.print_progress()
            
            # Final progress report
            self.print_progress()
            
            # Verify results
            self.cursor.execute("SELECT COUNT(*) FROM games")
            db_count = self.cursor.fetchone()[0]
            
            logger.info(f"🎉 Migration completed!")
            logger.info(f"📊 Final stats:")
            logger.info(f"   Total games in index: {len(self.games_index):,}")
            logger.info(f"   Games with local folders: {self.stats['total_games']:,}")
            logger.info(f"   Successful: {self.stats['successful']:,}")
            logger.info(f"   Failed: {self.stats['failed']:,}")
            logger.info(f"   Skipped: {self.stats['skipped']:,}")
            logger.info(f"   Database count: {db_count:,}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            return False
        finally:
            self.close_db()

def main():
    """Main entry point"""
    print("🎮 GameQuest Database Migration")
    print("=" * 50)
    
    # Check if required files exist
    if not DATA_ROOT.exists():
        print(f"❌ Data root not found: {DATA_ROOT}")
        print("💡 Please ensure the path is correct and accessible")
        return
    
    if not INDEX_FILE.exists():
        print(f"❌ Index file not found: {INDEX_FILE}")
        print("💡 Please ensure the games index file exists")
        return
    
    # Confirm before starting
    print(f"📁 Data root: {DATA_ROOT}")
    print(f"📖 Index file: {INDEX_FILE}")
    print(f"⚙️ Batch size: {BATCH_SIZE}")
    print(f"🧵 Threads: {MAX_WORKERS}")
    print(f"💾 Uses authoritative metadata from index file (correct release dates)")
    
    response = input("\n🤔 Proceed with migration? (y/N): ").strip().lower()
    if response != 'y':
        print("❌ Migration cancelled")
        return
    
    # Start migration
    migrator = GameMigrator()
    success = migrator.migrate_all_games()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("📝 Check database/migration.log for detailed logs")
    else:
        print("\n❌ Migration failed - check logs for details")

if __name__ == "__main__":
    main()