#!/usr/bin/env python3
"""
GameQuest Critics Migration Script
Migrates critic reviews from JSONL to PostgreSQL
"""

import os
import json
import psycopg2
import psycopg2.extras
from pathlib import Path
from typing import Dict, List, Any
import logging
import time

# Configuration
CRITICS_FILE = Path("data/mobygames_critic_reviews.jsonl")
BATCH_SIZE = 1000

# Database connection
DB_CONFIG = {
    'host': 'localhost',
    'database': 'gamequest',
    'user': 'postgres',
    'password': os.environ.get('LOCAL_DB_PASSWORD', '')
}

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/critics_migration.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CriticsMigrator:
    def __init__(self):
        self.conn = None
        self.cursor = None
        self.stats = {
            'total_reviews': 0,
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'skipped': 0,
            'start_time': None
        }
        
    def connect_db(self):
        """Establish database connection"""
        try:
            self.conn = psycopg2.connect(**DB_CONFIG)
            self.conn.autocommit = False
            self.cursor = self.conn.cursor()
            logger.info("✅ Database connected successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            return False
    
    def close_db(self):
        """Close database connection"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
        logger.info("🔒 Database connection closed")
    
    def count_reviews(self):
        """Count total reviews in the file"""
        logger.info(f"📖 Counting reviews in {CRITICS_FILE}...")
        
        if not CRITICS_FILE.exists():
            logger.error(f"❌ Critics file not found: {CRITICS_FILE}")
            return 0
        
        try:
            count = 0
            with open(CRITICS_FILE, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        count += 1
            return count
        except Exception as e:
            logger.error(f"❌ Error counting reviews: {e}")
            return 0
    
    def clean_html(self, text: str) -> str:
        """Remove HTML tags from text"""
        if not text:
            return ''
        import re
        clean = re.compile('<.*?>')
        return re.sub(clean, '', text).strip()
    
    def insert_critics_batch(self, critics_batch: List[Dict[str, Any]]) -> int:
        """Insert a batch of critics into database"""
        if not critics_batch:
            return 0
        
        insert_query = """
        INSERT INTO critics (review_id, game_id, citation)
        VALUES (%(review_id)s, %(game_id)s, %(citation)s)
        ON CONFLICT (review_id) DO UPDATE SET
            game_id = EXCLUDED.game_id,
            citation = EXCLUDED.citation
        """
        
        try:
            psycopg2.extras.execute_batch(
                self.cursor, insert_query, critics_batch, page_size=100
            )
            self.conn.commit()
            return len(critics_batch)
        except Exception as e:
            logger.error(f"❌ Batch insert failed: {e}")
            self.conn.rollback()
            return 0
    
    def migrate_critics(self):
        """Main migration function"""
        logger.info("🚀 Starting critics migration...")
        self.stats['start_time'] = time.time()
        
        # Connect to database
        if not self.connect_db():
            return False
        
        try:
            # Count total reviews
            total_reviews = self.count_reviews()
            if total_reviews == 0:
                logger.error("❌ No reviews found to migrate")
                return False
            
            self.stats['total_reviews'] = total_reviews
            logger.info(f"📖 Found {total_reviews:,} critic reviews to migrate")
            
            # Process reviews in batches
            critics_batch = []
            processed = 0
            
            with open(CRITICS_FILE, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        if not line.strip():
                            continue
                        
                        review_data = json.loads(line.strip())
                        
                        # Extract and clean data
                        review_id = review_data.get('review_id')
                        game_id = review_data.get('game_id')
                        citation = self.clean_html(review_data.get('citation', ''))
                        
                        if not review_id or not game_id or not citation:
                            self.stats['skipped'] += 1
                            continue
                        
                        critics_batch.append({
                            'review_id': int(review_id),
                            'game_id': int(game_id),
                            'citation': citation
                        })
                        
                        processed += 1
                        
                        # Insert when batch is full
                        if len(critics_batch) >= BATCH_SIZE:
                            inserted = self.insert_critics_batch(critics_batch)
                            self.stats['successful'] += inserted
                            self.stats['failed'] += len(critics_batch) - inserted
                            self.stats['processed'] += len(critics_batch)
                            critics_batch = []
                            
                            # Print progress
                            if processed % 10000 == 0:
                                elapsed = time.time() - self.stats['start_time']
                                rate = processed / elapsed if elapsed > 0 else 0
                                logger.info(f"📊 Progress: {processed:,}/{total_reviews:,} "
                                           f"({processed/total_reviews*100:.1f}%) | "
                                           f"✅ {self.stats['successful']:,} | ❌ {self.stats['failed']:,} | "
                                           f"⏱️ {rate:.1f}/s")
                        
                    except json.JSONDecodeError as e:
                        logger.warning(f"⚠️ JSON decode error on line {line_num}: {e}")
                        self.stats['skipped'] += 1
                        continue
                    except Exception as e:
                        logger.warning(f"⚠️ Error processing line {line_num}: {e}")
                        self.stats['failed'] += 1
                        continue
            
            # Insert remaining reviews
            if critics_batch:
                inserted = self.insert_critics_batch(critics_batch)
                self.stats['successful'] += inserted
                self.stats['failed'] += len(critics_batch) - inserted
                self.stats['processed'] += len(critics_batch)
            
            # Final stats
            elapsed = time.time() - self.stats['start_time']
            rate = self.stats['processed'] / elapsed if elapsed > 0 else 0
            
            logger.info("🎉 Critics migration completed!")
            logger.info("📊 Final stats:")
            logger.info(f"   Total reviews: {self.stats['total_reviews']:,}")
            logger.info(f"   Successful: {self.stats['successful']:,}")
            logger.info(f"   Failed: {self.stats['failed']:,}")
            logger.info(f"   Skipped: {self.stats['skipped']:,}")
            logger.info(f"   Processing rate: {rate:.1f} reviews/second")
            
            # Verify results
            self.cursor.execute("SELECT COUNT(*) FROM critics")
            db_count = self.cursor.fetchone()[0]
            logger.info(f"   Database count: {db_count:,}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            return False
        finally:
            self.close_db()

def main():
    """Main entry point"""
    print("🎮 GameQuest Critics Migration")
    print("=" * 50)
    
    # Check if critics file exists
    if not CRITICS_FILE.exists():
        print(f"❌ Critics file not found: {CRITICS_FILE}")
        print("💡 Please ensure the critics file exists")
        return
    
    # Confirm before starting
    print(f"📖 Critics file: {CRITICS_FILE}")
    print(f"⚙️ Batch size: {BATCH_SIZE}")
    
    response = input("\n🤔 Proceed with critics migration? (y/N): ").strip().lower()
    if response != 'y':
        print("❌ Migration cancelled")
        return
    
    # Start migration
    migrator = CriticsMigrator()
    success = migrator.migrate_critics()
    
    if success:
        print("\n🎉 Critics migration completed successfully!")
        print("📝 Check logs/critics_migration.log for detailed logs")
    else:
        print("\n❌ Critics migration failed - check logs for details")

if __name__ == "__main__":
    main()