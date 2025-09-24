#!/usr/bin/env python3
"""
Create database schema for GameQuest
"""
import psycopg2
import json
from datetime import datetime

def get_db_connection():
    """Get database connection"""
    return psycopg2.connect(
        host='localhost',
        database='gamequest',
        user='postgres',
        password='ST5780@BCsp'
    )

def create_schema():
    """Create the complete database schema"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    print("🏗️ Creating database schema...")
    
    try:
        # Create games table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS games (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                release_date DATE,
                moby_score FLOAT,
                moby_url TEXT,
                platforms TEXT[],
                genres TEXT[],
                developers TEXT[],
                publishers TEXT[],
                sample_cover_url TEXT,
                sample_screenshot_urls TEXT[],
                cover_path TEXT,
                screenshot_paths TEXT[],
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("✅ Created games table")
        
        # Create critics table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS critics (
                review_id INTEGER PRIMARY KEY,
                game_id INTEGER REFERENCES games(id) ON DELETE CASCADE,
                game_title TEXT,
                citation TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("✅ Created critics table")
        
        # Create embeddings table (for future use, storing paths only)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                id SERIAL PRIMARY KEY,
                game_id INTEGER REFERENCES games(id) ON DELETE CASCADE,
                embedding_type TEXT NOT NULL, -- 'description', 'cover', 'screenshot', 'critic'
                chromadb_id TEXT, -- Reference to ChromaDB document ID
                image_path TEXT, -- For image embeddings
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("✅ Created embeddings table")
        
        # Create indexes for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_games_title ON games USING gin(to_tsvector('english', title));
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_games_description ON games USING gin(to_tsvector('english', description));
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_games_genres ON games USING gin(genres);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_games_platforms ON games USING gin(platforms);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_critics_game_id ON critics(game_id);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_embeddings_game_id ON embeddings(game_id);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_embeddings_type ON embeddings(embedding_type);
        """)
        print("✅ Created performance indexes")
        
        # Create a view for easy game + critic queries
        cursor.execute("""
            CREATE OR REPLACE VIEW games_with_critics AS
            SELECT 
                g.*,
                COUNT(c.review_id) as critic_count,
                STRING_AGG(c.citation, ' | ' ORDER BY c.review_id) as all_critics
            FROM games g
            LEFT JOIN critics c ON g.id = c.game_id
            GROUP BY g.id, g.title, g.description, g.release_date, g.moby_score, 
                     g.moby_url, g.platforms, g.genres, g.developers, g.publishers,
                     g.sample_cover_url, g.sample_screenshot_urls, g.cover_path,
                     g.screenshot_paths, g.created_at, g.updated_at;
        """)
        print("✅ Created games_with_critics view")
        
        # Commit all changes
        conn.commit()
        print("\n🎉 Database schema created successfully!")
        
        # Show table info
        cursor.execute("""
            SELECT table_name, 
                   (xpath('/row/cnt/text()', xml_count))[1]::text::int as row_count
            FROM (
                SELECT table_name, 
                       query_to_xml(format('select count(*) as cnt from %I.%I', 
                                          table_schema, table_name), false, true, '') as xml_count
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
            ) t
            ORDER BY table_name;
        """)
        
        print("\n📊 Current table status:")
        for row in cursor.fetchall():
            print(f"   {row[0]}: {row[1]} rows")
            
    except Exception as e:
        print(f"❌ Error creating schema: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

def test_schema():
    """Test the schema by inserting a sample record"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # Insert a test game
        test_game = {
            'id': 999999,
            'title': 'Test Game',
            'description': 'This is a test game for schema validation',
            'release_date': '2024-01-01',
            'moby_score': 8.5,
            'moby_url': 'https://example.com/test-game',
            'platforms': ['Windows', 'Mac'],
            'genres': ['Action', 'Adventure'],
            'developers': ['Test Developer'],
            'publishers': ['Test Publisher'],
            'sample_cover_url': 'https://example.com/cover.jpg',
            'sample_screenshot_urls': ['https://example.com/screenshot1.jpg'],
            'cover_path': 'G:/Data/images/999999/cover.jpg',
            'screenshot_paths': ['G:/Data/images/999999/screenshot_01.jpg']
        }
        
        cursor.execute("""
            INSERT INTO games (id, title, description, release_date, moby_score, moby_url,
                             platforms, genres, developers, publishers, sample_cover_url,
                             sample_screenshot_urls, cover_path, screenshot_paths)
            VALUES (%(id)s, %(title)s, %(description)s, %(release_date)s, %(moby_score)s,
                   %(moby_url)s, %(platforms)s, %(genres)s, %(developers)s, %(publishers)s,
                   %(sample_cover_url)s, %(sample_screenshot_urls)s, %(cover_path)s, %(screenshot_paths)s)
            ON CONFLICT (id) DO NOTHING;
        """, test_game)
        
        # Insert a test critic
        cursor.execute("""
            INSERT INTO critics (review_id, game_id, game_title, citation)
            VALUES (999999, 999999, 'Test Game', 'This is a test review for schema validation')
            ON CONFLICT (review_id) DO NOTHING;
        """)
        
        conn.commit()
        print("✅ Schema test successful - sample data inserted")
        
        # Test the view
        cursor.execute("SELECT title, critic_count FROM games_with_critics WHERE id = 999999;")
        result = cursor.fetchone()
        if result:
            print(f"✅ View test successful - Game: {result[0]}, Critics: {result[1]}")
        
        # Clean up test data
        cursor.execute("DELETE FROM critics WHERE review_id = 999999;")
        cursor.execute("DELETE FROM games WHERE id = 999999;")
        conn.commit()
        print("✅ Test data cleaned up")
        
    except Exception as e:
        print(f"❌ Schema test failed: {e}")
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    create_schema()
    test_schema()
    
    print("\n🚀 Next steps:")
    print("1. Load game metadata from G:\\Data\\images\\")
    print("2. Migrate critics data")
    print("3. Update your code to use PostgreSQL")