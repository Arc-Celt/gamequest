#!/usr/bin/env python3
"""
Agentic RAG service for GameQuest - handles intelligent game recommendations
"""

import asyncio
import nest_asyncio
from typing import List, Dict, Any, Optional
import logging
from utils.database import get_games_from_db

logger = logging.getLogger(__name__)

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

class AgenticRAGService:
    """Handles Agentic RAG operations with AI-powered reasoning capabilities"""
    
    def __init__(self, model_manager, search_service):
        self.model_manager = model_manager
        self.search_service = search_service
    
    def text_search_tool(self, query: str, num_results: int = 10, 
                        platform: Optional[str] = None, score: Optional[float] = None,
                        genre: Optional[str] = None, year: Optional[int] = None, 
                        scored_only: bool = False) -> str:
        """Perform intelligent text search using AI reasoning"""
        try:
            # Get game data for display
            games_data = self.search_service.get_games_for_display(
                query, platform=platform, score=score, genre=genre, year=year, 
                scored_only=scored_only, num_results=num_results
            )
            
            if not games_data:
                return f"I couldn't find any games matching your search for '{query}'."
            
            # Create a comprehensive prompt for the AI
            games_info = []
            for i, game in enumerate(games_data, 1):
                title = game.get('title', 'Unknown')
                genres = game.get('genres', [])
                description = game.get('description', '')
                release_date = game.get('release_date', '')
                
                # Get year for context
                year = 'Unknown'
                if release_date:
                    if isinstance(release_date, str):
                        year = release_date.split('-')[0]
                    else:
                        year = str(release_date.year)
                
                games_info.append({
                    'title': title,
                    'year': year,
                    'genres': genres,
                    'description': description
                })
            
            # Create the AI prompt
            prompt = f"""You are a knowledgeable gaming expert. A user is searching for games with the query: "{query}"

I found {len(games_info)} relevant games for them. Please provide intelligent recommendations explaining WHY each game matches their search, focusing on the reasoning rather than just listing facts.

For each game, provide:
1. The game title and year
2. A thoughtful explanation of WHY this game matches their search query
3. Focus on what makes this game special or relevant to what they're looking for

Be insightful and explain the connection between their search intent and each game. Don't just repeat game descriptions - provide intelligent analysis.

Here are the games:
"""
            
            for i, game in enumerate(games_info, 1):
                prompt += f"""
{i}. **{game['title']}** ({game['year']})
   Genres: {', '.join(game['genres']) if game['genres'] else 'Unknown'}
   Description: {game['description'][:300]}{'...' if len(game['description']) > 300 else ''}
"""
            
            prompt += """
Please provide your recommendations in this format:

Based on your query, I found X highly relevant games:

1. **Game Title** (Year)
   🎯 **Why I recommend it**: [Intelligent reasoning about why this matches their search]

2. **Game Title** (Year)  
   🎯 **Why I recommend it**: [Intelligent reasoning about why this matches their search]

Continue for all games...
"""
            
            # Use the LLM to generate intelligent recommendations
            if hasattr(self.model_manager, 'llm') and self.model_manager.llm:
                try:
                    response = self.model_manager.llm.complete(prompt)
                    return str(response)
                except Exception as e:
                    logger.error(f"LLM error: {e}")
                    # Fallback to simple response
                    return self._generate_fallback_response(query, games_info)
            else:
                logger.warning("No LLM available, using fallback")
                return self._generate_fallback_response(query, games_info)
            
        except Exception as e:
            logger.error(f"Error in text search tool: {e}")
            return f"I encountered an error while searching for '{query}': {str(e)}"
    
    def _generate_fallback_response(self, query, games_info):
        """Fallback response when LLM is not available"""
        response = f"Based on your query, I found {len(games_info)} highly relevant games:\n\n"
        
        for i, game in enumerate(games_info, 1):
            response += f"{i}. **{game['title']}** ({game['year']})\n"
            response += f"   🎯 **Why I recommend it**: This game appears relevant to your search for '{query}' based on its content and features.\n\n"
        
        return response
    
    def agentic_rag_search(self, query: str, platform: Optional[str] = None,
                          score: Optional[float] = None, genre: Optional[str] = None,
                          year: Optional[int] = None, scored_only: bool = False) -> Dict[str, Any]:
        """Perform Agentic RAG search with both AI response and structured data"""
        try:
            # Convert 0 to None for year to avoid false positives
            if year == 0:
                year = None
                
            # Get AI text response
            ai_response = self.text_search_tool(query, num_results=5, platform=platform, 
                                              score=score, genre=genre, year=year, scored_only=scored_only)
            
            # Get structured game data for display
            games_data = self.search_service.get_games_for_display(
                query, platform=platform, score=score, genre=genre, year=year, scored_only=scored_only, num_results=5
            )
            
            return {
                'response': ai_response,
                'games': games_data,
                'query': query,
                'filters': {
                    'platform': platform,
                    'score': score,
                    'genre': genre,
                    'year': year
                }
            }
            
        except Exception as e:
            logger.error(f"Error in agentic RAG search: {e}")
            return {
                'response': f"I encountered an error while processing your request: {str(e)}",
                'games': [],
                'query': query,
                'error': str(e),
                'filters': {
                    'platform': platform,
                    'score': score,
                    'genre': genre,
                    'year': year
                }
            }
    
    def search_by_genre(self, genre: str) -> List[Dict[str, Any]]:
        """Search games by genre with intelligent recommendations"""
        try:
            from utils.database import search_games_by_genre
            games = search_games_by_genre(genre)
            
            if not games:
                return []
            
            # Use AI to provide intelligent recommendations
            prompt = f"""You are a gaming expert. A user is looking for {genre} games. 

Here are some {genre} games I found:
{chr(10).join([f"- {game.get('title', 'Unknown')} ({game.get('year', 'Unknown')})" for game in games[:10]])}

Please provide a brief, intelligent recommendation explaining why these are good {genre} games and what makes them special in this genre. Be insightful and helpful.

Format your response as:
"Here are some excellent {genre} games I recommend:

[Your intelligent analysis and recommendations]"
"""
            
            if hasattr(self.model_manager, 'llm') and self.model_manager.llm:
                try:
                    ai_response = self.model_manager.llm.complete(prompt)
                    return [{'games': games, 'ai_recommendation': str(ai_response)}]
                except Exception as e:
                    logger.error(f"LLM error in genre search: {e}")
                    return games
            else:
                return games
                
        except Exception as e:
            logger.error(f"Error in genre search: {e}")
            return []