#!/usr/bin/env python3
"""
Database connection and query utilities for GameQuest
"""

import psycopg2
from typing import List, Dict, Any, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Database configuration
DB_CONFIG = {
    'host': 'ep-purple-tooth-afn0imyh-pooler.c-2.us-west-2.aws.neon.tech',
    'database': 'neondb',
    'user': 'neondb_owner',
    'password': 'npg_6H8mCAYSLhrQ',
    'port': 5432,
    'sslmode': 'require'
}

def get_db_connection():
    """Get a database connection"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise

def search_games_by_genre(genre: str) -> List[Dict[str, Any]]:
    """Search games by genre using PostgreSQL"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, title, description, release_date, moby_score, platforms, genres,
                   developers, publishers, cover_path, screenshot_paths
            FROM games 
            WHERE %s = ANY(genres)
            ORDER BY moby_score DESC NULLS LAST
            LIMIT 20
        """, (genre,))
        
        games = []
        for row in cursor.fetchall():
            games.append({
                'id': int(row[0]),
                'title': row[1],
                'description': row[2],
                'release_date': row[3].strftime('%Y-%m-%d') if row[3] else None,
                'moby_score': float(row[4]) if row[4] is not None else None,
                'platforms': row[5],
                'genres': row[6],
                'developers': row[7],
                'publishers': row[8],
                'cover_path': row[9],
                'screenshot_paths': row[10]
            })
        
        cursor.close()
        conn.close()
        return games
        
    except Exception as e:
        logger.error(f"Error searching games by genre: {e}")
        return []

def search_games_by_platform(platform: str) -> List[Dict[str, Any]]:
    """Search games by platform using PostgreSQL"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, title, description, release_date, moby_score, platforms, genres,
                   developers, publishers, sample_cover_url, sample_screenshot_urls
            FROM games 
            WHERE %s = ANY(platforms)
            ORDER BY moby_score DESC NULLS LAST
            LIMIT 20
        """, (platform,))
        
        games = []
        for row in cursor.fetchall():
            games.append({
                'id': int(row[0]),
                'title': row[1],
                'description': row[2],
                'release_date': row[3].strftime('%Y-%m-%d') if row[3] else None,
                'moby_score': float(row[4]) if row[4] is not None else None,
                'platforms': row[5],
                'genres': row[6],
                'developers': row[7],
                'publishers': row[8],
                'cover_path': row[9],
                'screenshot_paths': row[10]
            })
        
        cursor.close()
        conn.close()
        return games
        
    except Exception as e:
        logger.error(f"Error searching games by platform: {e}")
        return []

def search_games_by_text(query: str, platform: Optional[str] = None, 
                        score: Optional[float] = None, genre: Optional[str] = None, 
                        year: Optional[int] = None, scored_only: bool = False, 
                        limit: int = 20) -> List[Dict[str, Any]]:
    """Search games by text query with optional filters"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build dynamic WHERE clause
        where_conditions = ["(LOWER(title) LIKE LOWER(%s) OR LOWER(description) LIKE LOWER(%s))"]
        params = [f"%{query}%", f"%{query}%"]
        
        if platform:
            where_conditions.append("%s = ANY(platforms)")
            params.append(platform)
        
        if score is not None:
            if scored_only:
                # Only show games with scores >= specified value
                where_conditions.append("moby_score >= %s")
                params.append(score)
            else:
                # Show games with scores >= specified value OR no score
                where_conditions.append("(moby_score >= %s OR moby_score IS NULL)")
                params.append(score)
        elif scored_only:
            # Only show games that have scores (any score)
            where_conditions.append("moby_score IS NOT NULL")
        
        if genre:
            where_conditions.append("%s = ANY(genres)")
            params.append(genre)
        
        if year:
            where_conditions.append("EXTRACT(YEAR FROM release_date) >= %s")
            params.append(year)
        
        where_clause = " AND ".join(where_conditions)
        
        sql_query = f"""
            SELECT id, title, description, release_date, moby_score, platforms, genres,
                   developers, publishers, sample_cover_url, sample_screenshot_urls, all_critics
            FROM games_with_critics 
            WHERE {where_clause}
            ORDER BY moby_score DESC NULLS LAST
            LIMIT %s
        """
        
        params.append(limit)
        cursor.execute(sql_query, params)
        rows = cursor.fetchall()
        
        games = []
        for row in rows:
            # Parse critics - now it's an array from the view
            critics_array = row[11] if row[11] else []
            critics = []
            if critics_array:
                for i, review in enumerate(critics_array):  # No limit, show all reviews
                    if review and review.strip():
                        critics.append({
                            'source': f"Critic {i+1}",
                            'score': '',
                            'review': review.strip()  # No truncation, show full review
                        })
            
            games.append({
                'id': int(row[0]),
                'title': row[1],
                'description': row[2],
                'release_date': row[3].strftime('%Y-%m-%d') if row[3] else None,
                'moby_score': float(row[4]) if row[4] is not None else None,
                'platforms': row[5],
                'genres': row[6],
                'developers': row[7],
                'publishers': row[8],
                'cover_path': row[9],
                'screenshot_paths': row[10],
                'critics': critics
            })
        
        conn.close()
        return games
        
    except Exception as e:
        logger.error(f"Error searching games by text: {e}")
        return []

def get_games_from_db(game_ids: List[int], platform: Optional[str] = None, 
                     score: Optional[float] = None, genre: Optional[str] = None, 
                     year: Optional[int] = None, scored_only: bool = False) -> List[Dict[str, Any]]:
    """Get games from database with optional filters"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Build dynamic WHERE clause
        where_conditions = ["id = ANY(%s)"]
        params = [game_ids]
        
        if platform:
            where_conditions.append("%s = ANY(platforms)")
            params.append(platform)
        
        if score is not None:
            if scored_only:
                # Only show games with scores >= specified value
                where_conditions.append("moby_score >= %s")
                params.append(score)
            else:
                # Show games with scores >= specified value OR no score
                where_conditions.append("(moby_score >= %s OR moby_score IS NULL)")
                params.append(score)
        elif scored_only:
            # Only show games that have scores (any score)
            where_conditions.append("moby_score IS NOT NULL")
        
        if genre:
            where_conditions.append("%s = ANY(genres)")
            params.append(genre)
        
        if year:
            where_conditions.append("EXTRACT(YEAR FROM release_date) >= %s")
            params.append(year)
        
        where_clause = " AND ".join(where_conditions)
        
        query = f"""
            SELECT id, title, description, release_date, moby_score, platforms, genres,
                   developers, publishers, sample_cover_url, sample_screenshot_urls, all_critics
            FROM games_with_critics 
            WHERE {where_clause}
            ORDER BY moby_score DESC NULLS LAST
        """
        
        cursor.execute(query, params)
        
        games = []
        for row in cursor.fetchall():
            # Clean up critics data - now it's an array from the view
            critics_array = row[11] if row[11] else []
            cleaned_critics = []
            if critics_array:
                for i, review in enumerate(critics_array):  # No limit, show all reviews
                    if review and review.strip():
                        cleaned_critics.append({
                            'source': f"Critic {i+1}",
                            'score': '',
                            'review': review.strip()  # No truncation, show full review
                        })
            
            games.append({
                'id': int(row[0]),
                'title': row[1],
                'description': row[2],
                'release_date': row[3].strftime('%Y-%m-%d') if row[3] else None,
                'moby_score': float(row[4]) if row[4] is not None else None,
                'platforms': row[5],
                'genres': row[6],
                'developers': row[7],
                'publishers': row[8],
                'cover_path': row[9],
                'screenshot_paths': row[10],
                'critics': cleaned_critics
            })
        
        cursor.close()
        conn.close()
        return games
        
    except Exception as e:
        logger.error(f"Error getting games from database: {e}")
        return []

def get_game_cover_path(game_id: int) -> Optional[str]:
    """Get cover URL for a specific game"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT sample_cover_url FROM games WHERE id = %s", (game_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()
        
        return result[0] if result and result[0] else None
        
    except Exception as e:
        logger.error(f"Error getting cover URL for game {game_id}: {e}")
        return None

def get_platforms() -> List[str]:
    """Get all unique platforms from database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT unnest(platforms) as platform 
            FROM games 
            WHERE platforms IS NOT NULL 
            ORDER BY platform
        """)
        platforms = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return platforms
    except Exception as e:
        logger.error(f"Error getting platforms: {e}")
        return []

def get_genres() -> List[str]:
    """Get all unique genres from database"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT unnest(genres) as genre 
            FROM games 
            WHERE genres IS NOT NULL 
            ORDER BY genre
        """)
        genres = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return genres
    except Exception as e:
        logger.error(f"Error getting genres: {e}")
        return []