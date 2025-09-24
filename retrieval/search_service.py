#!/usr/bin/env python3
"""
Search service for GameQuest - handles semantic search and reranking
"""

from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import logging
from utils.database import get_games_from_db

logger = logging.getLogger(__name__)

class SearchService:
    """Handles semantic search and reranking operations"""
    
    def __init__(self, model_manager):
        self.model_manager = model_manager
    
    def format_game_result(self, game_data: Dict[str, Any], score: Optional[float] = None) -> str:
        """Format a single game result into a readable string"""
        title = game_data.get('title', 'Unknown')
        # Handle date properly - could be string or date object
        release_date = game_data.get('release_date', '')
        if release_date:
            if isinstance(release_date, str):
                year = release_date.split('-')[0]
            else:
                year = str(release_date.year)
        else:
            year = 'Unknown'
        platforms = ', '.join(game_data.get('platforms', []))
        genres = ', '.join(game_data.get('genres', []))
        moby_score = game_data.get('moby_score', 'N/A')
        
        result = f"🎮 {title} ({year})\n"
        result += f"📊 Score: {moby_score}/10\n"
        result += f"🖥️ Platforms: {platforms}\n"
        result += f"🎯 Genres: {genres}\n"
        
        if score:
            result += f"🔍 Relevance: {score:.3f}\n"
        
        description = game_data.get('description', '')
        if description:
            # Truncate description to 200 characters
            if len(description) > 200:
                description = description[:200] + "..."
            result += f"📝 {description}\n"
        
        return result
    
    def semantic_search(self, query: str, platform: Optional[str] = None, 
                       score: Optional[float] = None, genre: Optional[str] = None, 
                       year: Optional[int] = None, scored_only: bool = False,
                       num_results: int = 10) -> Dict[str, Any]:
        """Perform semantic search with filtering and reranking"""
        try:
            # Search descriptions
            desc_ids, desc_scores = self.model_manager.search_descriptions(query, num_results * 2)
            
            # Get games from database with filters
            games_data = get_games_from_db(desc_ids, platform, score, genre, year, scored_only)
            
            if not games_data:
                return {
                    'games': [],
                    'total': 0,
                    'query': query,
                    'filters': {'platform': platform, 'score': score, 'genre': genre, 'year': year}
                }
            
            # Extract descriptions and scores for reranking
            game_descriptions = []
            game_scores = []
            game_id_to_index = {}
            
            for i, game in enumerate(games_data):
                game_descriptions.append(game.get('description', ''))
                # Find original score for this game
                try:
                    orig_idx = desc_ids.index(game['id'])
                    game_scores.append(float(desc_scores[orig_idx]))
                except ValueError:
                    game_scores.append(0.0)
                game_id_to_index[game['id']] = i
            
            # Rerank results
            if len(game_descriptions) > 1:
                reranked_descriptions, reranked_scores = self.model_manager.rerank_results(
                    query, game_descriptions, game_scores
                )
                
                # Reorder games based on reranking
                reranked_games = []
                for desc, score in zip(reranked_descriptions, reranked_scores):
                    # Find the game with this description
                    for game in games_data:
                        if game.get('description', '') == desc:
                            game['relevance_score'] = score
                            reranked_games.append(game)
                            break
                
                games_data = reranked_games
            
            # Limit results
            games_data = games_data[:num_results]
            
            # Format results for display
            formatted_games = []
            for game in games_data:
                formatted_game = {
                    'id': game['id'],
                    'title': game['title'],
                    'description': game.get('description', ''),
                    'release_date': game.get('release_date', ''),
                    'moby_score': float(game.get('moby_score')) if game.get('moby_score') is not None else None,
                    'platforms': game.get('platforms', []),
                    'genres': game.get('genres', []),
                    'developers': game.get('developers', []),
                    'publishers': game.get('publishers', []),
                    'cover_path': game.get('cover_path'),
                    'screenshot_paths': game.get('screenshot_paths', []),
                    'relevance_score': float(game.get('relevance_score', 0.0))
                }
                formatted_games.append(formatted_game)
            
            return {
                'games': formatted_games,
                'total': len(formatted_games),
                'query': query,
                'filters': {'platform': platform, 'score': score, 'genre': genre, 'year': year}
            }
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return {
                'games': [],
                'total': 0,
                'query': query,
                'error': str(e),
                'filters': {'platform': platform, 'score': score, 'genre': genre, 'year': year}
            }
    
    def get_games_for_display(self, query: str, platform: Optional[str] = None,
                             score: Optional[float] = None, genre: Optional[str] = None,
                             year: Optional[int] = None, scored_only: bool = False, 
                             num_results: int = 5) -> List[Dict[str, Any]]:
        """Get games formatted for display with reranking"""
        try:
            # Search descriptions
            desc_ids, desc_scores = self.model_manager.search_descriptions(query, num_results * 2)
            
            # Get games from database with filters
            games_data = get_games_from_db(desc_ids, platform, score, genre, year, scored_only)
            
            if not games_data:
                return []
            
            # Extract descriptions and scores for reranking
            game_descriptions = []
            game_scores = []
            
            for game in games_data:
                game_descriptions.append(game.get('description', ''))
                # Find original score for this game
                try:
                    orig_idx = desc_ids.index(game['id'])
                    game_scores.append(float(desc_scores[orig_idx]))
                except ValueError:
                    game_scores.append(0.0)
            
            # Rerank results
            if len(game_descriptions) > 1:
                reranked_descriptions, reranked_scores = self.model_manager.rerank_results(
                    query, game_descriptions, game_scores
                )
                
                # Reorder games based on reranking
                reranked_games = []
                for desc, score in zip(reranked_descriptions, reranked_scores):
                    # Find the game with this description
                    for game in games_data:
                        if game.get('description', '') == desc:
                            game['relevance_score'] = score
                            reranked_games.append(game)
                            break
                
                games_data = reranked_games
            
            # Limit results
            games_data = games_data[:num_results]
            
            # Format results for display
            formatted_games = []
            for game in games_data:
                formatted_game = {
                    'id': game['id'],
                    'title': game['title'],
                    'description': game.get('description', ''),
                    'release_date': game.get('release_date', ''),
                    'moby_score': float(game.get('moby_score')) if game.get('moby_score') is not None else None,
                    'platforms': game.get('platforms', []),
                    'genres': game.get('genres', []),
                    'developers': game.get('developers', []),
                    'publishers': game.get('publishers', []),
                    'critics': game.get('critics', []),
                    'cover_path': game.get('cover_path'),
                    'screenshot_paths': game.get('screenshot_paths', []),
                    'relevance_score': float(game.get('relevance_score', 0.0))
                }
                formatted_games.append(formatted_game)
            
            return formatted_games
            
        except Exception as e:
            logger.error(f"Error getting games for display: {e}")
            return []
    
    def image_search(self, query: str, search_type: str = "covers", 
                    platform: Optional[str] = None, score: Optional[float] = None,
                    genre: Optional[str] = None, year: Optional[int] = None,
                    num_results: int = 10) -> List[Dict[str, Any]]:
        """Search games by image similarity (covers or screenshots)"""
        try:
            if search_type == "covers":
                game_ids, scores = self.model_manager.search_covers(query, num_results * 2)
            elif search_type == "screenshots":
                game_ids, scores = self.model_manager.search_screenshots(query, num_results * 2)
            else:
                raise ValueError("search_type must be 'covers' or 'screenshots'")
            
            # Get games from database with filters
            games_data = get_games_from_db(game_ids, platform, score, genre, year)
            
            if not games_data:
                return []
            
            # Create mapping of game_id to score
            id_to_score = dict(zip(game_ids, scores))
            
            # Add relevance scores and format
            formatted_games = []
            for game in games_data:
                game['relevance_score'] = id_to_score.get(game['id'], 0.0)
                formatted_game = {
                    'id': game['id'],
                    'title': game['title'],
                    'description': game.get('description', ''),
                    'release_date': game.get('release_date', ''),
                    'moby_score': float(game.get('moby_score')) if game.get('moby_score') is not None else None,
                    'platforms': game.get('platforms', []),
                    'genres': game.get('genres', []),
                    'developers': game.get('developers', []),
                    'publishers': game.get('publishers', []),
                    'cover_path': game.get('cover_path'),
                    'screenshot_paths': game.get('screenshot_paths', []),
                    'relevance_score': float(game['relevance_score'])
                }
                formatted_games.append(formatted_game)
            
            # Sort by relevance score
            formatted_games.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            return formatted_games[:num_results]
            
        except Exception as e:
            logger.error(f"Error in image search: {e}")
            return []
    
    def search_by_image_embedding(self, image_embedding: np.ndarray, search_type: str = "covers",
                                platform: Optional[str] = None, score: Optional[float] = None,
                                genre: Optional[str] = None, year: Optional[int] = None,
                                scored_only: bool = False, num_results: int = 10) -> List[Dict[str, Any]]:
        """Search games by uploaded image embedding"""
        try:
            if search_type == "covers":
                collection = self.model_manager.covers_collection
            elif search_type == "screenshots":
                collection = self.model_manager.screenshots_collection
            else:
                raise ValueError("search_type must be 'covers' or 'screenshots'")
            
            if not collection:
                raise RuntimeError(f"{search_type} collection not loaded")
            
            # Search by embedding
            results = collection.query(
                query_embeddings=[image_embedding.tolist()],
                n_results=num_results * 2,
                include=['metadatas', 'distances']
            )
            
            game_ids = [int(metadata['game_id']) for metadata in results['metadatas'][0]]
            # Convert L2 distances to similarity scores (ChromaDB uses L2 distance by default)
            # For image embeddings, we want higher similarity for lower distances
            max_distance = max(results['distances'][0]) if results['distances'][0] else 1.0
            scores = [float(1 - (distance / max_distance)) for distance in results['distances'][0]]
            
            # Get games from database with filters
            games_data = get_games_from_db(game_ids, platform, score, genre, year, scored_only)
            
            if not games_data:
                return []
            
            # Create mapping of game_id to score
            id_to_score = dict(zip(game_ids, scores))
            
            # Add relevance scores and format
            formatted_games = []
            for game in games_data:
                game['relevance_score'] = id_to_score.get(game['id'], 0.0)
                formatted_game = {
                    'id': game['id'],
                    'title': game['title'],
                    'description': game.get('description', ''),
                    'release_date': game.get('release_date', ''),
                    'moby_score': float(game.get('moby_score')) if game.get('moby_score') is not None else None,
                    'platforms': game.get('platforms', []),
                    'genres': game.get('genres', []),
                    'developers': game.get('developers', []),
                    'publishers': game.get('publishers', []),
                    'cover_path': game.get('cover_path'),
                    'screenshot_paths': game.get('screenshot_paths', []),
                    'relevance_score': float(game['relevance_score'])
                }
                formatted_games.append(formatted_game)
            
            # Sort by relevance score
            formatted_games.sort(key=lambda x: x['relevance_score'], reverse=True)
            
            return formatted_games[:num_results]
            
        except Exception as e:
            logger.error(f"Error in image embedding search: {e}")
            return []
