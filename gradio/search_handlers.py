"""
Search Handlers for GameQuest Gradio App
"""

import os
import sys
import logging
import json
import re
from typing import Dict, Any

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))

from models.load_models import ModelManager
from retrieval.search_service import SearchService
from retrieval.agentic_rag import AgenticRAGService
from utils.database import search_games_by_text

logger = logging.getLogger(__name__)


class SearchHandlers:

    def __init__(self, model_manager: ModelManager, search_service: SearchService, agentic_rag_service: AgenticRAGService):
        self.model_manager = model_manager
        self.search_service = search_service
        self.agentic_rag_service = agentic_rag_service

    def create_game_card_html(self, game: Dict[str, Any], index: int) -> str:
        try:
            if not isinstance(game, dict):
                raise ValueError(f"Game data is not a dictionary: {type(game)}")

            year = "Unknown"
            if game.get('release_date'):
                release_date = game['release_date']
                if isinstance(release_date, str):
                    if "-" in release_date:
                        year = release_date.split("-")[0]
                    elif "/" in release_date:
                        year = release_date.split("/")[2] or release_date.split("/")[0]
                    else:
                        year = release_date[:4]
                else:
                    try:
                        from datetime import datetime
                        if isinstance(release_date, datetime):
                            year = str(release_date.year)
                        else:
                            year = str(release_date)[:4]
                    except:
                        year = "Unknown"

            platforms_data = game.get('platforms', [])
            if isinstance(platforms_data, list) and platforms_data:
                platforms = ", ".join(str(p) for p in platforms_data)
            else:
                platforms = "Unknown"

            genres_data = game.get('genres', [])
            if isinstance(genres_data, list) and genres_data:
                genres = ", ".join(str(g) for g in genres_data)
            else:
                genres = "Unknown"

            score_html = ""
            if game.get('moby_score') is not None and game.get('moby_score') != "N/A":
                score = game['moby_score']
                if isinstance(score, (int, float)) and score > 0:
                    if score >= 8:
                        score_class = "score-high"
                    elif score >= 6:
                        score_class = "score-medium"
                    else:
                        score_class = "score-low"
                    score_html = f'<span class="meta-item {score_class}">Score: {score}/10</span>'

            description = game.get('description', '')
            if description and isinstance(description, str):
                description = description[:200] + "..." if len(description) > 200 else description
            else:
                description = ""

            cover_url = game.get('cover_path', '') if game.get('cover_path') else ""

            game_id = game.get('id', 0)
            if not game_id:
                raise ValueError("Game ID is missing or invalid")

            screenshots = game.get('screenshot_paths', [])
            if not isinstance(screenshots, list):
                screenshots = []

            game_data = {
                'id': game_id,
                'title': game.get('title', 'Unknown Title'),
                'year': year,
                'platforms': platforms,
                'genres': genres,
                'score': game.get('moby_score', 'N/A'),
                'description': game.get('description', 'No description available'),
                'cover_url': cover_url,
                'screenshots': screenshots
            }

            game_id = game_data['id']

            game_data_json = json.dumps(game_data).replace('"', '&quot;')

            return f"""
            <div class="game-card" style="border: 1px solid #ddd; border-radius: 8px; padding: 15px; margin: 10px 0; background: white; cursor: pointer;" 
                 onclick="showGameDetails({game_id})" data-game-data="{game_data_json}">
                <div style="display: flex; gap: 15px;">
                    <img src="{cover_url}" alt="{game.get('title', 'Unknown')}" style="width: 100px; height: 130px; object-fit: cover; border-radius: 4px;" onerror="this.style.display='none'">
                    <div style="flex: 1;">
                        <h3 style="margin: 0 0 10px 0; color: #333;">{game.get('title', 'Unknown Title')}</h3>
                        <div class="game-meta" style="margin-bottom: 10px;">
                            <span class="meta-item" style="background: #f0f0f0; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; margin-right: 5px;">{year}</span>
                            {score_html}
                            <span class="meta-item" style="background: #f0f0f0; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; margin-right: 5px;">{platforms}</span>
                            <span class="meta-item" style="background: #f0f0f0; padding: 2px 8px; border-radius: 12px; font-size: 0.8em; margin-right: 5px;">{genres}</span>
                        </div>
                        {f'<p class="game-description" style="color: #666; font-size: 0.9em; margin: 10px 0;">{description}</p>' if description else ''}
                        <div style="margin-top: 10px; color: #333; font-size: 0.9em; font-weight: bold;">
                            Click to view full details
                        </div>
                    </div>
                </div>
            </div>
            """
        except Exception as e:
            return f"<div style='color: red; padding: 10px; border: 1px solid red; border-radius: 4px; margin: 10px 0;'>Error displaying game: {str(e)}</div>"

    def text_search(self, query: str, platform: str, genre: str, score: float, year: int, scored_only: bool) -> str:
        try:
            results = search_games_by_text(
                query=query,
                platform=platform if platform != "All" else None,
                genre=genre if genre != "All" else None,
                score=float(score) if score else None,
                year=int(year) if year else None,
                scored_only=scored_only,
                limit=10
            )

            if not results:
                return ("<div style='text-align: center; color: #666;'>"
                        "No games found matching your criteria.</div>")

            html = f"<h3>Found {len(results)} games:</h3>"
            for i, game in enumerate(results, 1):
                html += self.create_game_card_html(game, i)

            # Update JavaScript with game results
            js_results = []
            for game in results:
                game_id = game.get('id')
                if game_id is not None:
                    try:
                        game_id = int(game_id)
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid game ID: {game_id}, skipping game")
                        continue

                js_game = {
                    'id': game_id,
                    'title': game.get('title'),
                    'release_date': game.get('release_date'),
                    'platforms': game.get('platforms'),
                    'genres': game.get('genres'),
                    'moby_score': game.get('moby_score'),
                    'description': game.get('description'),
                    'cover_path': game.get('cover_path'),
                    'screenshot_paths': game.get('screenshot_paths'),
                    'critics': game.get('critics', [])
                }
                js_results.append(js_game)

            # Debug: Log the first game to see what data we're getting
            if js_results:
                logger.info(f"First game data: {js_results[0]}")
                logger.info(f"Cover path from database: {results[0].get('cover_path')}")

            # Inject JavaScript to update the global game results variable
            html += f"""
            <script>
                console.log('Injecting game results into JavaScript...');
                if (window.updateGameResultsFromGradio) {{
                    window.updateGameResultsFromGradio({json.dumps(js_results)});
                }} else {{
                    console.error('updateGameResultsFromGradio function not available');
                    // Fallback: directly update the global variable
                    if (typeof currentGameResults !== 'undefined') {{
                        currentGameResults = {json.dumps(js_results)};
                        console.log('Updated currentGameResults directly:', currentGameResults);
                    }} else {{
                        console.error('currentGameResults variable not defined');
                    }}
                }}
            </script>
            """

            return html, js_results

        except Exception as e:
            logger.error(f"Text search error: {e}")
            return f"<div style='color: red;'>❌ Search error: {str(e)}</div>"

    def semantic_search(self, query: str, platform: str, genre: str, score: float, year: int, scored_only: bool) -> str:
        """Semantic search with filters"""
        try:
            results = self.search_service.semantic_search(
                query=query,
                platform=platform if platform != "All" else None,
                genre=genre if genre != "All" else None,
                score=float(score) if score else None,
                year=int(year) if year else None,
                scored_only=scored_only,
                num_results=10
            )

            games = results.get('games', [])

            if not games:
                return ("<div style='text-align: center; color: #666;'>"
                        "No games found matching your criteria.</div>")

            html = f"<h3>Found {len(games)} games (semantic search):</h3>"
            for i, game in enumerate(games, 1):
                html += self.create_game_card_html(game, i)

            # Update JavaScript with game results
            js_results = []
            for game in games:
                game_id = game.get('id')
                if game_id is not None:
                    try:
                        game_id = int(game_id)
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid game ID: {game_id}, skipping game")
                        continue

                js_game = {
                    'id': game_id,
                    'title': game.get('title'),
                    'release_date': game.get('release_date'),
                    'platforms': game.get('platforms'),
                    'genres': game.get('genres'),
                    'moby_score': game.get('moby_score'),
                    'description': game.get('description'),
                    'cover_path': game.get('cover_path'),
                    'screenshot_paths': game.get('screenshot_paths'),
                    'critics': game.get('critics', [])
                }
                js_results.append(js_game)
            html += f"""
            <script>
                console.log('Updating semantic game results with {len(js_results)} games');
                updateGameResults({json.dumps(js_results)});
                console.log('Semantic game results updated successfully');
            </script>
            """

            return html

        except Exception as e:
            logger.error(f"Semantic search error: {e}")
            return f"<div style='color: red;'>❌ Search error: {str(e)}</div>"

    def ai_search(self, query: str, platform: str, genre: str, score: float, year: int, scored_only: bool) -> tuple:
        """AI Agent search with reasoning"""
        try:
            results = self.agentic_rag_service.agentic_rag_search(
                query=query,
                platform=platform if platform != "All" else None,
                genre=genre if genre != "All" else None,
                score=float(score) if score else None,
                year=int(year) if year else None,
                scored_only=scored_only
            )

            games = results.get('games', [])
            ai_response = results.get('response', '')

            if not games:
                return ("<div style='text-align: center; color: #666;'>"
                        "No games found matching your criteria.</div>", 
                        "<div style='background: white; padding: 15px; border: 1px solid #ddd; border-radius: 8px; color: #666;'>AI could not find suitable recommendations.</div>")

            html = f"<h3>🤖 AI Recommendations ({len(games)} games):</h3>"
            for i, game in enumerate(games, 1):
                html += self.create_game_card_html(game, i)

            # Update JavaScript with game results
            js_results = []
            for game in games:
                game_id = game.get('id')
                if game_id is not None:
                    try:
                        game_id = int(game_id)
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid game ID: {game_id}, skipping game")
                        continue

                js_game = {
                    'id': game_id,
                    'title': game.get('title'),
                    'release_date': game.get('release_date'),
                    'platforms': game.get('platforms'),
                    'genres': game.get('genres'),
                    'moby_score': game.get('moby_score'),
                    'description': game.get('description'),
                    'cover_path': game.get('cover_path'),
                    'screenshot_paths': game.get('screenshot_paths'),
                    'critics': game.get('critics', [])
                }
                js_results.append(js_game)

            logger.info(f"Storing {len(js_results)} games in Gradio state")

            # Format AI response for display
            formatted_ai_response = self._format_ai_response(ai_response) if ai_response else "<div style='background: white; padding: 15px; border: 1px solid #ddd; border-radius: 8px; color: #666;'>AI analysis is not available at the moment.</div>"

            return html, formatted_ai_response, js_results

        except Exception as e:
            logger.error(f"AI search error: {e}")
            return (f"<div style='color: red;'>❌ Search error: {str(e)}</div>",
                    "<div style='background: white; padding: 15px; border: 1px solid #ddd; border-radius: 8px; color: #666;'>AI search encountered an error.</div>")

    def show_game_details(self, game_id: int, current_games: list) -> str:
        """Show detailed game information in a modal"""
        try:
            # Find the game in the current results
            game_data = None
            for game in current_games:
                if game.get('id') == game_id:
                    game_data = game
                    break

            if not game_data:
                return f"<div style='color: red; padding: 20px;'>❌ Game data not found for ID: {game_id}</div>"

            # Extract year
            year = "Unknown"
            if game_data.get('release_date'):
                if isinstance(game_data['release_date'], str):
                    year = game_data['release_date'][:4] if len(game_data['release_date']) >= 4 else "Unknown"
                else:
                    year = str(game_data['release_date'])[:4] if len(str(game_data['release_date'])) >= 4 else "Unknown"

            # Format platforms and genres
            platforms = ", ".join(game_data.get('platforms', [])) if game_data.get('platforms') else "Unknown"
            genres = ", ".join(game_data.get('genres', [])) if game_data.get('genres') else "Unknown"

            # Get cover image URL
            cover_url = f"/cover/{game_data['id']}" if game_data.get('id') else ""

            # Format screenshots
            screenshots_html = ""
            if game_data.get('screenshot_paths'):
                screenshots = game_data['screenshot_paths'] if isinstance(game_data['screenshot_paths'], list) else [game_data['screenshot_paths']]
                for screenshot in screenshots[:5]:
                    if screenshot:
                        screenshots_html += f'<img src="{screenshot}" style="max-width: 200px; max-height: 150px; margin: 5px; border-radius: 8px; border: 1px solid #ddd;">'

            # Format critics
            critics_html = ""
            if game_data.get('critics'):
                critics = game_data['critics'] if isinstance(game_data['critics'], list) else [game_data['critics']]
                for critic in critics[:3]:
                    if critic:
                        critics_html += f'<div style="background: #f8f9fa; padding: 10px; margin: 5px 0; border-radius: 5px; border-left: 3px solid #667eea;"><strong>Critic Review:</strong> {critic}</div>'

            # Create detailed modal content
            modal_html = f"""
            <div style="background: white; padding: 20px; border-radius: 10px; max-width: 800px; margin: 20px auto; box-shadow: 0 4px 12px rgba(0,0,0,0.15);">
                <div style="display: flex; gap: 20px; margin-bottom: 20px;">
                    <div style="flex: 0 0 200px;">
                        <img src="{cover_url}" style="width: 100%; border-radius: 8px; border: 1px solid #ddd;" alt="Game Cover">
                    </div>
                    <div style="flex: 1;">
                        <h2 style="color: #667eea; margin: 0 0 10px 0;">{game_data.get('title', 'Unknown Title')}</h2>
                        <p><strong>Release Year:</strong> {year}</p>
                        <p><strong>Platforms:</strong> {platforms}</p>
                        <p><strong>Genres:</strong> {genres}</p>
                        <p><strong>Score:</strong> {game_data.get('moby_score', 'N/A')}/100</p>
                    </div>
                </div>

                <div style="margin-bottom: 20px;">
                    <h3 style="color: #667eea;">Description</h3>
                    <p style="line-height: 1.6; color: #555;">{game_data.get('description', 'No description available.')}</p>
                </div>

                {f'<div style="margin-bottom: 20px;"><h3 style="color: #667eea;">Screenshots</h3><div style="display: flex; flex-wrap: wrap; gap: 10px;">{screenshots_html}</div></div>' if screenshots_html else ''}

                {f'<div style="margin-bottom: 20px;"><h3 style="color: #667eea;">Critic Reviews</h3>{critics_html}</div>' if critics_html else ''}
            </div>
            """

            return modal_html

        except Exception as e:
            logger.error(f"Error showing game details: {e}")
            return f"<div style='color: red; padding: 20px;'>❌ Error loading game details: {str(e)}</div>"

    def cover_search(self, image_file, platform: str, genre: str, score: float, year: int, scored_only: bool) -> str:
        """Cover image similarity search"""
        try:
            if not image_file:
                return "<div style='color: red;'>❌ Please upload an image first!</div>"

            if hasattr(image_file, 'read'):
                image_data = image_file.read()
            elif isinstance(image_file, str):
                with open(image_file, 'rb') as f:
                    image_data = f.read()
            else:
                image_data = bytes(image_file)

            # Extract image embedding
            try:
                image_embedding = self.model_manager.extract_image_embedding(image_data)
            except Exception as e:
                return f"<div style='color: red;'>❌ Error extracting image embedding: {str(e)}</div>"

            # Perform similarity search
            try:
                results = self.search_service.search_by_image_embedding(
                    image_embedding=image_embedding,
                    search_type='covers',
                    platform=platform if platform != "All" else None,
                    genre=genre if genre != "All" else None,
                    score=float(score) if score else None,
                    year=int(year) if year else None,
                    scored_only=scored_only,
                    num_results=10
                )
            except Exception as e:
                return f"<div style='color: red;'>❌ Error in similarity search: {str(e)}</div>"

            if not results:
                return ("<div style='text-align: center; color: #666;'>"
                        "No similar games found.</div>")

            html = f"<h3>🎨 Similar Cover Results ({len(results)} games):</h3>"
            for i, game in enumerate(results, 1):
                try:
                    html += self.create_game_card_html(game, i)
                except Exception as e:
                    html += f"<div style='color: red; padding: 10px; border: 1px solid red; border-radius: 4px; margin: 10px 0;'>Error displaying game {i}: {str(e)}</div>"

            # Update JavaScript with game results
            js_results = []
            for game in results:
                game_id = game.get('id')
                if game_id is not None:
                    try:
                        game_id = int(game_id)
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid game ID: {game_id}, skipping game")
                        continue

                js_game = {
                    'id': game_id,
                    'title': game.get('title'),
                    'release_date': game.get('release_date'),
                    'platforms': game.get('platforms'),
                    'genres': game.get('genres'),
                    'moby_score': game.get('moby_score'),
                    'description': game.get('description'),
                    'cover_path': game.get('cover_path'),
                    'screenshot_paths': game.get('screenshot_paths'),
                    'critics': game.get('critics', [])
                }
                js_results.append(js_game)
            html += f"""
            <script>
                updateGameResults({json.dumps(js_results)});
            </script>
            """

            return html

        except Exception as e:
            logger.error(f"Cover search error: {e}")
            return f"<div style='color: red;'>❌ Cover search error: {str(e)}</div>"

    def screenshot_search(self, image_file, platform: str, genre: str, score: float, year: int, scored_only: bool) -> str:
        """Screenshot image similarity search"""
        try:
            if not image_file:
                return "<div style='color: red;'>❌ Please upload an image first!</div>"

            if hasattr(image_file, 'read'):
                image_data = image_file.read()
            elif isinstance(image_file, str):
                with open(image_file, 'rb') as f:
                    image_data = f.read()
            else:
                image_data = bytes(image_file)

            # Extract image embedding
            try:
                image_embedding = self.model_manager.extract_image_embedding(image_data)
            except Exception as e:
                return f"<div style='color: red;'>❌ Error extracting image embedding: {str(e)}</div>"

            # Perform similarity search
            try:
                results = self.search_service.search_by_image_embedding(
                    image_embedding=image_embedding,
                    search_type='screenshots',
                    platform=platform if platform != "All" else None,
                    genre=genre if genre != "All" else None,
                    score=float(score) if score else None,
                    year=int(year) if year else None,
                    scored_only=scored_only,
                    num_results=10
                )
            except Exception as e:
                return f"<div style='color: red;'>❌ Error in similarity search: {str(e)}</div>"

            if not results:
                return ("<div style='text-align: center; color: #666;'>"
                        "No similar games found.</div>")

            html = f"<h3>📸 Similar Screenshot Results ({len(results)} games):</h3>"
            for i, game in enumerate(results, 1):
                try:
                    html += self.create_game_card_html(game, i)
                except Exception as e:
                    html += f"<div style='color: red; padding: 10px; border: 1px solid red; border-radius: 4px; margin: 10px 0;'>Error displaying game {i}: {str(e)}</div>"

            # Update JavaScript with game results
            js_results = []
            for game in results:
                game_id = game.get('id')
                if game_id is not None:
                    try:
                        game_id = int(game_id)
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid game ID: {game_id}, skipping game")
                        continue

                js_game = {
                    'id': game_id,
                    'title': game.get('title'),
                    'release_date': game.get('release_date'),
                    'platforms': game.get('platforms'),
                    'genres': game.get('genres'),
                    'moby_score': game.get('moby_score'),
                    'description': game.get('description'),
                    'cover_path': game.get('cover_path'),
                    'screenshot_paths': game.get('screenshot_paths'),
                    'critics': game.get('critics', [])
                }
                js_results.append(js_game)
            html += f"""
            <script>
                updateGameResults({json.dumps(js_results)});
            </script>
            """

            return html

        except Exception as e:
            logger.error(f"Screenshot search error: {e}")
            return f"<div style='color: red;'>❌ Screenshot search error: {str(e)}</div>"

    def _format_ai_response(self, ai_response: str) -> str:
        """Format AI response with proper styling"""
        if not ai_response:
            return "<div style='background: white; padding: 15px; border: 1px solid #ddd; border-radius: 8px; color: #666;'>No AI analysis available.</div>"

        # Clean and format the AI response
        import re

        # Remove any filter text that might appear at the end
        clean_text = ai_response.replace(
            r"I applied filters:.*?\. These are ranked by relevance\.?$",
            ""
        )

        analysis_patterns = [
            r"Based on your query",
            r"Here are the games",
            r"I found \d+ games",
            r"^\d+\. \*\*.*?\*\* \(",
            r"Recommendations:",
        ]

        # Find the earliest analysis start pattern
        analysis_start_index = -1
        for pattern in analysis_patterns:
            match = re.search(pattern, clean_text, re.IGNORECASE)
            if match is not None and (analysis_start_index == -1 or match.start() < analysis_start_index):
                analysis_start_index = match.start()

        if analysis_start_index != -1:
            thinking_part = clean_text[:analysis_start_index].strip()
            analysis_part = clean_text[analysis_start_index:].strip()

            if len(thinking_part) > 50:
                thinking_html = f'<div class="thinking-section" style="background: #333; color: white; padding: 15px; border-radius: 8px; margin-bottom: 15px; font-style: italic;">{thinking_part.replace(chr(10), "<br>")}</div>'
                analysis_html = self._format_analysis_section(analysis_part)

                return f'<div class="ai-response-content" style="color: white; padding: 20px;">{thinking_html}{analysis_html}</div>'

        return f'<div class="ai-response-content" style="color: white; padding: 20px;">{self._format_analysis_section(clean_text)}</div>'

    def _format_analysis_section(self, text: str) -> str:
        """Format analysis section with markdown rendering"""
        # Convert markdown to HTML
        formatted_text = self._markdown_to_html(text)
        return f'<div class="analysis-section" style="color: white; line-height: 1.6;">{formatted_text}</div>'

    def _markdown_to_html(self, text: str) -> str:
        """Convert basic markdown to HTML"""
        if not text:
            return ""

        # Convert **bold** to <strong>
        text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)

        # Convert *italic* to <em>
        text = re.sub(r'\*(.*?)\*', r'<em>\1</em>', text)

        # Convert numbered lists (1. **Title** (year) -> proper list items)
        lines = text.split('\n')
        formatted_lines = []
        in_list = False

        for line in lines:
            line = line.strip()
            if not line:
                if in_list:
                    formatted_lines.append('</ol>')
                    in_list = False
                formatted_lines.append('<br>')
                continue

            if re.match(r'^\d+\.\s*\*\*.*?\*\*', line):
                if not in_list:
                    formatted_lines.append('<ol>')
                    in_list = True
                content = re.sub(r'^\d+\.\s*', '', line)
                formatted_lines.append(f'<li>{content}</li>')
            else:
                if in_list:
                    formatted_lines.append('</ol>')
                    in_list = False
                formatted_lines.append(line)

        if in_list:
            formatted_lines.append('</ol>')

        result = '\n'.join(formatted_lines)
        result = result.replace('\n', '<br>')

        return result
