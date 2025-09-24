"""
Agentic RAG service for GameQuest - handles intelligent game recommendations
"""

import asyncio
import nest_asyncio
from typing import List, Dict, Any, Optional
import logging
from utils.database import get_games_from_db

logger = logging.getLogger(__name__)
nest_asyncio.apply()


class AgenticRAGService:
    """Handles Agentic RAG operations with AI-powered reasoning capabilities"""

    def __init__(self, model_manager, search_service):
        self.model_manager = model_manager
        self.search_service = search_service
        self.rerank_weight = 0.3

    def text_search_tool(self, query: str, num_results: int = 10,
                         platform: Optional[str] = None, score: Optional[float] = None,
                         genre: Optional[str] = None, year: Optional[int] = None, 
                         scored_only: bool = False) -> str:
        """Perform intelligent text search using AI reasoning"""
        try:
            games_data = self.search_service.get_games_for_display(
                query, platform=platform, score=score, genre=genre, year=year, 
                scored_only=scored_only, num_results=num_results
            )

            if not games_data:
                return f"I couldn't find any games matching your search for '{query}'."

            games_info = []
            for i, game in enumerate(games_data, 1):
                title = game.get('title', 'Unknown')
                genres = game.get('genres', [])
                description = game.get('description', '')
                release_date = game.get('release_date', '')

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

            # Prompt for the LLM
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

IMPORTANT: Be concise and stop after listing all games. Do not repeat yourself or add extra explanations.
"""

            # Generate intelligent recommendations
            if hasattr(self.model_manager, 'llm') and self.model_manager.llm:
                try:
                    if hasattr(self.model_manager.llm, 'complete'):
                        # Ollama backend
                        response = self.model_manager.llm.complete(prompt)
                        return str(response)
                    else:
                        # Hugging Face Transformers backend
                        try:
                            response = self.model_manager.llm(prompt)
                            if isinstance(response, list) and "generated_text" in response[0]:
                                answer = response[0]["generated_text"]
                            else:
                                answer = str(response)
                        except Exception as e:
                            logger.error(f"Transformers LLM failed: {e}")
                            answer = self._generate_fallback_response(query, games_info)
                        return self._clean_text(answer)
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

    def _clean_text(self, text: str) -> str:
        """Simple text cleaning to remove repeated trailing sentences"""
        parts = text.split(". ")
        cleaned = []
        for p in parts:
            if not cleaned or cleaned[-1] != p:
                cleaned.append(p)
        return ". ".join(cleaned)

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
            # Convert 0 to None for year
            if year == 0:
                year = None

            ai_response = self.text_search_tool(
                query,
                num_results=5,
                platform=platform,
                score=score,
                genre=genre,
                year=year,
                scored_only=scored_only
            )

            # Get structured game data
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
