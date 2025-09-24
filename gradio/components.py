"""
Gradio UI Components for GameQuest
"""

import gradio as gr
from typing import Dict, Any, List
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from core.utils.database import get_platforms, get_genres
except ImportError:
    def get_platforms():
        return ["PC", "PlayStation", "Xbox", "Nintendo Switch", "Mobile"]

    def get_genres():
        return ["Action", "Adventure", "RPG", "Strategy", "Simulation", "Sports", "Racing"]


class GameQuestUI:

    def __init__(self):
        self.components = {}

    def _get_platform_choices(self) -> List[str]:
        """Get platform choices from database"""
        try:
            platforms = get_platforms()
            return ["All"] + platforms
        except Exception as e:
            print(f"Error getting platforms: {e}")
            return ["All", "PC", "PlayStation", "Xbox", "Nintendo Switch", "Mobile"]

    def _get_genre_choices(self) -> List[str]:
        """Get genre choices from database"""
        try:
            genres = get_genres()
            return ["All"] + genres
        except Exception as e:
            print(f"Error getting genres: {e}")
            return ["All", "Action", "Adventure", "RPG", "Strategy", "Simulation", "Sports", "Racing"]

    def create_layout(self, search_handlers) -> Dict[str, Any]:
        """Create the main UI layout"""

        with gr.Blocks(
            title="GameQuest",
            theme=gr.themes.Soft(),
            css=self._get_css(),
            head=self._get_javascript()
        ) as interface:

            with gr.Column(elem_classes=["main-container"]):
                # Title Card
                with gr.Column(elem_classes=["title-card"]):
                    gr.Markdown("""
                    # 🎮 GameQuest
                    Discover amazing games with multi-modal search and Agentic RAG recommendations!
                    """)

                # Filters Row
                with gr.Column(elem_classes=["filters-container"]):
                    with gr.Row(elem_classes=["filters-row"]):
                        platform_filter = gr.Dropdown(
                            choices=self._get_platform_choices(),
                            value="All",
                            label="Platform",
                            interactive=True
                        )
                        genre_filter = gr.Dropdown(
                            choices=self._get_genre_choices(),
                            value="All",
                            label="Genre",
                            interactive=True
                        )
                        score_filter = gr.Slider(
                            minimum=0,
                            maximum=10,
                            value=0,
                            step=0.1,
                            label="Min Score",
                            interactive=True
                        )
                        year_filter = gr.Slider(
                            minimum=1990,
                            maximum=2024,
                            value=1990,
                            step=1,
                            label="Year",
                            interactive=True
                        )
                        scored_only = gr.Checkbox(
                            label="Scored Only",
                            value=False
                        )

                # Search Sections Row
                with gr.Row():
                    # Left: Description Search
                    with gr.Column(scale=1):
                        gr.Markdown("### 📝 Description Search")
                        search_query = gr.Textbox(
                            placeholder="Describe what kind of game you're looking for...",
                            label="Search Query",
                            lines=3
                        )
                        with gr.Row():
                            text_search_btn = gr.Button("🔍 Text Search", variant="primary")
                            semantic_search_btn = gr.Button("🧠 Vector Search", variant="secondary")
                            ai_search_btn = gr.Button("🤖 Agent Search", variant="secondary")

                    # Right: Visual Search
                    with gr.Column(scale=1):
                        gr.Markdown("### 🖼️ Visual Search")
                        image_input = gr.File(
                            label="Upload Image",
                            file_types=["image"],
                            type="filepath"
                        )
                        with gr.Row():
                            cover_search_btn = gr.Button("🎨 Cover Search", variant="secondary")
                            screenshot_search_btn = gr.Button("📸 Screenshot Search", variant="secondary")

                # Results Area
                with gr.Row():
                    results_output = gr.HTML(
                        value="<div style='text-align: center; color: #666; padding: 40px;'>Search for games to see results here!</div>"
                    )

                # AI response content
                ai_response_content = gr.HTML(
                    value="<div style='background: white; padding: 15px; border: 1px solid #ddd; border-radius: 8px; color: #333;'>AI analysis will appear here when you use AI Agent search.</div>",
                    visible=True,
                    elem_id="ai_response_content"
                )

                # Current games state for modal access
                current_games = gr.State([])

            self._setup_event_handlers(search_handlers, {
                'interface': interface,
                'platform_filter': platform_filter,
                'genre_filter': genre_filter,
                'score_filter': score_filter,
                'year_filter': year_filter,
                'scored_only': scored_only,
                'search_query': search_query,
                'text_search_btn': text_search_btn,
                'semantic_search_btn': semantic_search_btn,
                'ai_search_btn': ai_search_btn,
                'image_input': image_input,
                'cover_search_btn': cover_search_btn,
                'screenshot_search_btn': screenshot_search_btn,
                'results_output': results_output,
                'ai_response_content': ai_response_content,
                'current_games': current_games
            })

        # Store components
        self.components = {
            'interface': interface,
            'platform_filter': platform_filter,
            'genre_filter': genre_filter,
            'score_filter': score_filter,
            'year_filter': year_filter,
            'scored_only': scored_only,
            'search_query': search_query,
            'text_search_btn': text_search_btn,
            'semantic_search_btn': semantic_search_btn,
            'ai_search_btn': ai_search_btn,
            'image_input': image_input,
            'cover_search_btn': cover_search_btn,
            'screenshot_search_btn': screenshot_search_btn,
            'results_output': results_output,
            'ai_response_content': ai_response_content,
            'current_games': current_games
        }

        return self.components

    def _setup_event_handlers(self, search_handlers, components):
        """Set up all event handlers for the UI components"""

        # Text-based search handlers
        components['text_search_btn'].click(
            search_handlers.text_search,
            inputs=[
                components['search_query'],
                components['platform_filter'],
                components['genre_filter'],
                components['score_filter'],
                components['year_filter'],
                components['scored_only']
            ],
            outputs=[components['results_output'], components['current_games']]
        )

        # Semantic search handler
        components['semantic_search_btn'].click(
            search_handlers.semantic_search,
            inputs=[
                components['search_query'],
                components['platform_filter'],
                components['genre_filter'],
                components['score_filter'],
                components['year_filter'],
                components['scored_only']
            ],
            outputs=[components['results_output'], components['current_games']]
        )

        # Agentic RAG search handler
        components['ai_search_btn'].click(
            search_handlers.ai_search,
            inputs=[
                components['search_query'],
                components['platform_filter'],
                components['genre_filter'],
                components['score_filter'],
                components['year_filter'],
                components['scored_only']
            ],
            outputs=[components['results_output'], components['ai_response_content'], components['current_games']]
        )

        # Image search handlers
        components['cover_search_btn'].click(
            search_handlers.cover_search,
            inputs=[
                components['image_input'],
                components['platform_filter'],
                components['genre_filter'],
                components['score_filter'],
                components['year_filter'],
                components['scored_only']
            ],
            outputs=[components['results_output']]
        )

        components['screenshot_search_btn'].click(
            search_handlers.screenshot_search,
            inputs=[
                components['image_input'],
                components['platform_filter'],
                components['genre_filter'],
                components['score_filter'],
                components['year_filter'],
                components['scored_only']
            ],
            outputs=[components['results_output']]
        )

        def clear_ai_response():
            return "<div style='background: white; padding: 15px; border: 1px solid #ddd; border-radius: 0 0 8px 8px; color: #666;'>AI analysis will appear here when you use AI Agent search.</div>"

        components['text_search_btn'].click(
            clear_ai_response,
            outputs=[components['ai_response_content']]
        )

        components['semantic_search_btn'].click(
            clear_ai_response,
            outputs=[components['ai_response_content']]
        )

        components['cover_search_btn'].click(
            clear_ai_response,
            outputs=[components['ai_response_content']]
        )

        components['screenshot_search_btn'].click(
            clear_ai_response,
            outputs=[components['ai_response_content']]
        )

    def _get_css(self) -> str:
        """Get CSS styling"""
        return r"""
        /* Main Layout */
        .main-container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }

        .title-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 15px;
            text-align: center;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
        }

        .title-card h1 {
            margin: 0 0 10px 0;
            font-size: 2.5em;
            font-weight: 700;
        }

        .title-card p {
            margin: 0;
            font-size: 1.2em;
            opacity: 0.9;
        }

        .filters-container {
            display: flex;
            justify-content: center;
            margin-bottom: 30px;
        }

        .filters-row {
            display: flex;
            gap: 15px;
            align-items: end;
            flex-wrap: wrap;
            justify-content: center;
            width: 100%;
        }

        .filters-row > * {
            flex: 0 0 auto;
            min-width: 120px;
        }

        /* Ensure filter elements are centered */
        .filters-row .gradio-dropdown,
        .filters-row .gradio-slider,
        .filters-row .gradio-checkbox {
            margin: 0 auto;
        }

        /* Responsive adjustments */
        @media (max-width: 768px) {
            .main-container {
                padding: 10px;
            }

            .title-card {
                padding: 20px;
                margin-bottom: 20px;
            }

            .title-card h1 {
                font-size: 2em;
            }

            .title-card p {
                font-size: 1em;
            }

            .filters-row {
                flex-direction: column;
                align-items: center;
                gap: 10px;
            }
        }

        .game-card {
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            margin: 10px 0;
            background: white;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        .game-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            border-color: #667eea;
        }
        .game-card img {
            width: 100px;
            height: 100px;
            object-fit: cover;
            border-radius: 4px;
            float: left;
            margin-right: 15px;
        }
        .game-card h3 {
            margin: 0 0 8px 0;
            color: #333;
            font-size: 18px;
        }
        .game-card p {
            margin: 5px 0;
            color: #666;
            font-size: 14px;
        }
        .game-meta {
            display: flex;
            gap: 10px;
            margin: 8px 0;
            flex-wrap: wrap;
        }
        .meta-item {
            background: #f0f0f0;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 12px;
            color: #555;
        }
        .score-high { background: #d4edda; color: #155724; }
        .score-medium { background: #fff3cd; color: #856404; }
        .score-low { background: #f8d7da; color: #721c24; }
        .game-description {
            margin-top: 10px;
            color: #666;
            font-size: 13px;
            line-height: 1.4;
        }
        .view-details-btn {
            background: #667eea;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
            margin-top: 8px;
        }
        .view-details-btn:hover {
            background: #5a6fd8;
        }

        /* Modal Styling */
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            z-index: 1000;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .modal-content {
            background: white;
            border-radius: 8px;
            max-width: 800px;
            max-height: 90vh;
            overflow-y: auto;
            margin: 20px;
            position: relative;
        }
        .modal-header {
            padding: 20px;
            border-bottom: 1px solid #ddd;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .modal-header h3 {
            margin: 0;
            color: #333;
        }
        .modal-close {
            background: none;
            border: none;
            font-size: 24px;
            cursor: pointer;
            color: #666;
        }
        .modal-close:hover {
            color: #333;
        }
        .modal-body {
            padding: 20px;
        }
        .modal-game-cover {
            width: 200px;
            height: 280px;
            object-fit: cover;
            border-radius: 8px;
            float: left;
            margin-right: 20px;
            margin-bottom: 20px;
        }
        .modal-game-title {
            margin: 0 0 10px 0;
            color: #333;
        }
        .modal-game-meta {
            display: flex;
            gap: 10px;
            margin: 10px 0;
            flex-wrap: wrap;
        }
        .modal-description {
            clear: both;
            margin-top: 20px;
        }
        .modal-description h4 {
            margin: 0 0 10px 0;
            color: #333;
        }
        .modal-description p {
            line-height: 1.6;
            color: #666;
        }
        .modal-screenshots {
            margin-top: 20px;
        }
        .modal-screenshots h4 {
            margin: 0 0 15px 0;
            color: #333;
        }
        .screenshot-container {
            display: flex;
            gap: 10px;
            overflow-x: auto;
            padding: 10px 0;
        }
        .screenshot-item {
            flex-shrink: 0;
        }
        .screenshot-item img {
            width: 200px;
            height: 150px;
            object-fit: cover;
            border-radius: 4px;
            border: 1px solid #ddd;
        }
        .modal-critics {
            margin-top: 20px;
        }
        .modal-critics h4 {
            margin: 0 0 15px 0;
            color: #333;
        }
        .critic-card {
            background: #f8f9fa;
            border: 1px solid #e9ecef;
            border-radius: 6px;
            padding: 15px;
            margin-bottom: 10px;
        }
        .critic-content {
            color: #495057;
            line-height: 1.5;
        }

        /* AI Response Styling */
        .ai-response-content {
            color: #555;
            line-height: 1.5;
            font-size: 0.9em;
        }

        /* AI Sidebar - Floating */
        .ai-sidebar {
            position: fixed;
            top: 50%;
            right: -350px;
            width: 350px;
            height: 400px;
            background: white;
            border-radius: 15px 0 0 15px;
            box-shadow: -10px 0 30px rgba(0, 0, 0, 0.2);
            transform: translateY(-50%);
            transition: right 0.3s ease-in-out;
            z-index: 100;
            overflow: hidden;
        }

        .ai-sidebar.open {
            right: 0;
        }

        .ai-sidebar-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .ai-sidebar-title {
            font-size: 1em;
            font-weight: 600;
            margin: 0;
        }

        .ai-sidebar-toggle {
            background: none;
            border: none;
            color: white;
            font-size: 18px;
            cursor: pointer;
            padding: 5px;
            border-radius: 4px;
            transition: background 0.2s;
        }

        .ai-sidebar-toggle:hover {
            background: rgba(255, 255, 255, 0.2);
        }

        .ai-sidebar-content {
            padding: 20px;
            height: calc(100% - 60px);
            overflow-y: auto;
        }

        .ai-sidebar-content p {
            margin: 0;
            color: #555;
            line-height: 1.5;
            font-size: 0.9em;
        }

        /* AI Sidebar Trigger Button */
        .ai-sidebar-trigger {
            position: fixed;
            top: 50%;
            right: 20px;
            width: 50px;
            height: 50px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            border-radius: 50%;
            color: white;
            font-size: 20px;
            cursor: pointer;
            transform: translateY(-50%);
            transition: all 0.3s ease;
            z-index: 101;
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }

        .ai-sidebar-trigger:hover {
            transform: translateY(-50%) scale(1.1);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
        }

        .ai-sidebar-trigger.hidden {
            display: none;
        }
        .thinking-section {
            color: #999;
            font-style: italic;
            font-size: 0.85em;
            opacity: 0.8;
            border-left: 3px solid #e0e0e0;
            padding-left: 15px;
            margin: 10px 0;
        }
        .analysis-section {
            color: #555;
            font-weight: normal;
        }
        .ai-intro {
            margin-bottom: 20px;
            padding: 15px;
            background: #f0f8ff;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        .game-item {
            margin-bottom: 25px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }
        .game-item:last-child {
            margin-bottom: 0;
        }
        .game-item h4 {
            margin: 0 0 10px 0;
            color: #667eea;
            font-size: 1em;
            font-weight: 600;
        }

        /* AI Sidebar (matching Flask exactly) */
        .ai-sidebar {
            position: fixed;
            top: 50%;
            right: -350px;
            width: 350px;
            height: 400px;
            background: white;
            border-radius: 15px 0 0 15px;
            box-shadow: -10px 0 30px rgba(0, 0, 0, 0.2);
            transform: translateY(-50%);
            transition: right 0.3s ease-in-out;
            z-index: 100;
            overflow: hidden;
        }

        .ai-sidebar.open {
            right: 0;
        }

        .ai-sidebar-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .ai-sidebar-title {
            font-size: 1em;
            font-weight: 600;
            margin: 0;
        }

        .ai-sidebar-toggle {
            background: none;
            border: none;
            color: white;
            font-size: 18px;
            cursor: pointer;
            padding: 5px;
            border-radius: 4px;
            transition: background 0.2s;
        }

        .ai-sidebar-toggle:hover {
            background: rgba(255, 255, 255, 0.2);
        }

        .ai-sidebar-content {
            padding: 20px;
            height: calc(100% - 60px);
            overflow-y: auto;
        }

        .ai-sidebar-trigger {
            position: fixed;
            top: 50%;
            right: 20px;
            width: 50px;
            height: 50px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border: none;
            border-radius: 50%;
            color: white;
            font-size: 20px;
            cursor: pointer;
            transform: translateY(-50%);
            transition: all 0.3s ease;
            z-index: 101;
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }

        .ai-sidebar-trigger:hover {
            transform: translateY(-50%) scale(1.1);
            box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
        }

        /* Modal Styles (matching Flask exactly) */
        .modal-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.7);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 1000;
        }

        .modal-content {
            background: white;
            border-radius: 15px;
            max-width: 90%;
            max-height: 90%;
            overflow-y: auto;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
            position: relative;
        }

        .modal-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 15px 15px 0 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .modal-header h3 {
            margin: 0;
            font-size: 1.5em;
        }

        .modal-close {
            background: none;
            border: none;
            color: white;
            font-size: 24px;
            cursor: pointer;
            padding: 5px;
            border-radius: 4px;
            transition: background 0.2s;
        }

        .modal-close:hover {
            background: rgba(255, 255, 255, 0.2);
        }

        .modal-body {
            padding: 20px;
        }

        .modal-game-cover {
            width: 200px;
            height: 280px;
            object-fit: cover;
            border-radius: 8px;
            float: left;
            margin-right: 20px;
            margin-bottom: 20px;
        }

        .modal-game-info {
            margin-bottom: 20px;
        }

        .modal-game-title {
            color: #667eea;
            margin: 0 0 10px 0;
            font-size: 1.8em;
        }

        .modal-game-meta {
            margin-bottom: 15px;
        }

        .modal-description {
            clear: both;
            margin-top: 20px;
        }

        .modal-description h4 {
            color: #667eea;
            margin-bottom: 10px;
        }

        .modal-screenshots {
            margin-top: 20px;
        }

        .modal-screenshots h4 {
            color: #667eea;
            margin-bottom: 10px;
        }

        .screenshot-container {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
        }

        .screenshot-item img {
            max-width: 200px;
            max-height: 150px;
            border-radius: 8px;
            border: 1px solid #ddd;
        }

        .modal-critics {
            margin-top: 20px;
        }

        .modal-critics h4 {
            color: #667eea;
            margin-bottom: 10px;
        }

        .critic-card {
            background: #f8f9fa;
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }

        .critic-content {
            color: #495057;
            line-height: 1.5;
        }
        """

    def _get_javascript(self) -> str:
        """Get JavaScript functionality"""
        return r"""
        <script>
        // Global variable to store current game results (like Flask version)
        let currentGameResults = [];

        // Initialize AI sidebar trigger button on page load
        document.addEventListener('DOMContentLoaded', function() {
            console.log('Page loaded, adding AI sidebar trigger');
            // Add a floating AI button that's always visible
            const triggerButton = document.createElement('button');
            triggerButton.className = 'ai-sidebar-trigger';
            triggerButton.innerHTML = '🤖';
            triggerButton.onclick = toggleAISidebar;
            triggerButton.title = 'AI Analysis';
            document.body.appendChild(triggerButton);

            // Listen for game results updates
            window.addEventListener('gameResultsUpdated', function(event) {
                console.log('🎯 Game results updated via event:', event.detail);
                updateGameResults(event.detail);
            });

            // Try to get game results from Gradio state
            setTimeout(function() {
                console.log('Attempting to get game results from Gradio state...');
                // This will be called by the search handlers
            }, 1000);
        });

        // Global function to update game results from Gradio state
        window.updateGameResultsFromGradio = function(games) {
            console.log('updateGameResultsFromGradio called with:', games);
            updateGameResults(games);
        };

        // Simple function to show game modal with embedded data
        function showGameModal(id, title, year, platforms, genres, score, description, coverUrl, screenshots) {
            console.log('showGameModal called with:', {id, title, year, platforms, genres, score, screenshots});

            // Parse screenshots
            let screenshotsList = [];
            try {
                screenshotsList = JSON.parse(screenshots);
            } catch (e) {
                console.log('Failed to parse screenshots:', screenshots);
                screenshotsList = [];
            }

            // Call the modal creation function
            createGameModal(id, title, year, platforms, genres, score, description, coverUrl, screenshotsList);
        }

        // New function to show modal from data attribute
        function showGameModalFromData(element) {
            try {
                // Get game ID from data attribute
                const gameId = element.getAttribute('data-game-id');
                if (!gameId) {
                    throw new Error('Game ID not found');
                }

                // Get game data from global store
                if (!window.gameDataStore || !window.gameDataStore[gameId]) {
                    throw new Error('Game data not found in store');
                }

                const gameData = window.gameDataStore[gameId];
                console.log('showGameModalFromData called with:', gameData);

                // Screenshots should already be an array
                let screenshotsList = gameData.screenshots || [];
                console.log('Screenshots list:', screenshotsList);

                createGameModal(
                    gameData.id,
                    gameData.title,
                    gameData.year,
                    gameData.platforms,
                    gameData.genres,
                    gameData.score,
                    gameData.description,
                    gameData.cover_url,
                    screenshotsList
                );
            } catch (e) {
                console.error('Error parsing game data:', e);
                alert('Error loading game details');
            }
        }

        // Function to create the actual modal
        function createGameModal(id, title, year, platforms, genres, score, description, coverUrl, screenshotsList) {

            // Helper function to check if a value should be displayed
            function shouldShow(value) {
                return value && value !== 'null' && value !== 'N/A' && value.toString().trim() !== '';
            }

            // Build game info section conditionally
            let gameInfoHtml = '<h4 style="color: #333; margin: 0 0 15px 0;">Game Information</h4>';
            gameInfoHtml += `<p style="margin: 5px 0; color: #333;"><strong style="color: #666;">Year:</strong> ${year}</p>`;
            gameInfoHtml += `<p style="margin: 5px 0; color: #333;"><strong style="color: #666;">Platforms:</strong> ${platforms}</p>`;
            gameInfoHtml += `<p style="margin: 5px 0; color: #333;"><strong style="color: #666;">Genres:</strong> ${genres}</p>`;

            // Only show score if it's valid
            if (shouldShow(score)) {
                gameInfoHtml += `<p style="margin: 5px 0; color: #333;"><strong style="color: #666;">Score:</strong> ${score}</p>`;
            }

            // Build description section conditionally
            let descriptionHtml = '';
            if (shouldShow(description)) {
                descriptionHtml = `
                    <div style="margin-bottom: 20px;">
                        <h4 style="color: #333; margin: 0 0 10px 0;">Description</h4>
                        <p style="line-height: 1.6; color: #333; margin: 0;">${description}</p>
                    </div>
                `;
            }

            // Build screenshots section conditionally
            let screenshotsHtml = '';
            if (screenshotsList && screenshotsList.length > 0) {
                screenshotsHtml = `
                    <div id="screenshots-${id}" style="margin-top: 20px;">
                        <h4 style="color: #333; margin: 0 0 15px 0;">Screenshots</h4>
                        <div id="screenshots-container-${id}" style="display: flex; gap: 15px; overflow-x: auto; padding: 10px 0; scrollbar-width: thin;">
                            <p style="color: #666; font-style: italic;">Loading screenshots...</p>
                        </div>
                    </div>
                `;
            }

            // Create modal HTML with conditional sections
            const modalHtml = `
                <div style="position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000; display: flex; align-items: center; justify-content: center;" onclick="this.remove()">
                    <div style="background: white; border-radius: 10px; max-width: 800px; max-height: 90%; overflow-y: auto; position: relative; margin: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.3);" onclick="event.stopPropagation()">
                        <div style="padding: 20px; border-bottom: 1px solid #ddd; display: flex; justify-content: space-between; align-items: center; background: #f8f9fa;">
                            <h3 style="margin: 0; color: #333; font-size: 1.5em;">${title}</h3>
                            <button onclick="this.closest('div').parentElement.parentElement.remove()" style="background: none; border: none; font-size: 28px; cursor: pointer; color: #666; padding: 5px;">&times;</button>
                        </div>
                        <div style="padding: 20px;">
                            <div style="display: flex; gap: 20px; margin-bottom: 20px;">
                                <img src="${coverUrl}" alt="${title}" style="width: 150px; height: 200px; object-fit: cover; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1);" onerror="this.style.display='none'">
                                <div style="flex: 1;">
                                    ${gameInfoHtml}
                                </div>
                            </div>
                            ${descriptionHtml}
                            ${screenshotsHtml}
                        </div>
                    </div>
                </div>
            `;

            // Remove any existing modal
            const existingModal = document.querySelector('div[style*="position: fixed"][style*="z-index: 1000"]');
            if (existingModal) {
                existingModal.remove();
            }

            // Add modal to page
            document.body.insertAdjacentHTML('beforeend', modalHtml);

            // Load screenshots if section exists
            if (screenshotsList && screenshotsList.length > 0) {
                setTimeout(() => {
                    const screenshotsContainer = document.getElementById(`screenshots-container-${id}`);
                    if (screenshotsContainer) {
                        const screenshotsHtml = screenshotsList.map(url => `
                            <div style="flex-shrink: 0; width: 200px; height: 150px; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                                <img src="${url}" alt="Screenshot" style="width: 100%; height: 100%; object-fit: cover; cursor: pointer;" 
                                     onclick="this.style.transform = this.style.transform ? '' : 'scale(1.5)'; this.style.transition = 'transform 0.3s ease';"
                                     onerror="this.style.display='none'">
                            </div>
                        `).join('');
                        screenshotsContainer.innerHTML = screenshotsHtml;
                    }
                }, 100);
            }
        }

        function showGameDetails(gameId) {
            // Find the game card element and get data from it
            const gameCards = document.querySelectorAll('.game-card');
            let gameData = null;

            for (let card of gameCards) {
                if (card.onclick && card.onclick.toString().includes(gameId)) {
                    const dataAttr = card.getAttribute('data-game-data');
                    if (dataAttr) {
                        try {
                            gameData = JSON.parse(dataAttr.replace(/&quot;/g, '"'));
                            break;
                        } catch (e) {
                            console.error('Error parsing game data:', e);
                        }
                    }
                }
            }

            if (!gameData) {
                alert('Game data not found for ID: ' + gameId);
                return;
            }

            // Create modal using the found game data
            createGameModal(
                gameData.id,
                gameData.title,
                gameData.year || 'Unknown',
                gameData.platforms || 'Unknown',
                gameData.genres || 'Unknown',
                gameData.score || 'N/A',
                gameData.description || 'No description available',
                gameData.cover_url || '',
                gameData.screenshots || []
            );
        }

        function extractYear(releaseDate) {
            if (typeof releaseDate === 'string') {
                if (releaseDate.includes('-')) {
                    return releaseDate.split('-')[0];
                } else if (releaseDate.includes('/')) {
                    return releaseDate.split('/')[2] || releaseDate.split('/')[0];
                } else {
                    return releaseDate.substring(0, 4);
                }
            } else {
                const date = new Date(releaseDate);
                return date.getFullYear();
            }
        }

        function showGameDetailsFromGradio(gameId) {
            // Same function for compatibility
            showGameDetails(gameId);
        }

        function findGameById(gameId) {
            console.log('=== findGameById called ===');
            console.log('Looking for ID:', gameId, 'Type:', typeof gameId);
            console.log('currentGameResults:', currentGameResults);
            console.log('currentGameResults length:', currentGameResults.length);

            if (currentGameResults.length === 0) {
                console.warn('No game results available!');
                return null;
            }

            // Log all available IDs for debugging
            console.log('Available game IDs:');
            currentGameResults.forEach((game, index) => {
                console.log(`  [${index}] ID: ${game.id} (${typeof game.id}), Title: ${game.title}`);
            });

            // Find the game in the currently displayed results (same as Flask)
            // Try both string and number comparison
            const game = currentGameResults.find((g) => {
                console.log(`Comparing ${g.id} (${typeof g.id}) with ${gameId} (${typeof gameId})`);
                return g.id == gameId || g.id === gameId;
            });

            if (game) {
                console.log('✅ Found game:', game);
                return game;
            }
            console.warn("❌ Game data not found for ID:", gameId);
            console.log('=== findGameById completed ===');
            return null;
        }

        function createModalContent(gameData) {
            // Extract year (same logic as Flask)
            let year = "Unknown";
            if (gameData.release_date) {
                if (typeof gameData.release_date === "string") {
                    if (gameData.release_date.includes("-")) {
                        year = gameData.release_date.split("-")[0];
                    } else if (gameData.release_date.includes("/")) {
                        year = gameData.release_date.split("/")[2] || gameData.release_date.split("/")[0];
                    } else {
                        year = gameData.release_date.substring(0, 4);
                    }
                } else {
                    const date = new Date(gameData.release_date);
                    year = date.getFullYear();
                }
            }

            const platforms = gameData.platforms ? gameData.platforms.join(", ") : "Unknown";
            const genres = gameData.genres ? gameData.genres.join(", ") : "Unknown";
            const coverUrl = gameData.cover_path || "";

            // Score display (same as Flask)
            let scoreHtml = "";
            if (gameData.moby_score !== null && gameData.moby_score !== undefined && gameData.moby_score !== "N/A") {
                let scoreClass = "";
                if (typeof gameData.moby_score === "number") {
                    if (gameData.moby_score >= 8) scoreClass = "score-high";
                    else if (gameData.moby_score >= 6) scoreClass = "score-medium";
                    else scoreClass = "score-low";
                }
                scoreHtml = `<span class="meta-item ${scoreClass}">Score: ${gameData.moby_score}/10</span>`;
            }

            // Screenshots (same as Flask)
            let screenshotsHtml = "";
            if (gameData.screenshot_paths && gameData.screenshot_paths.length > 0) {
                screenshotsHtml = `
                    <div class="modal-screenshots">
                        <h4>Screenshots</h4>
                        <div class="screenshot-container">
                            ${gameData.screenshot_paths.slice(0, 10).map((url) => `
                                <div class="screenshot-item">
                                    <img src="${url}" alt="Screenshot" onerror="this.style.display='none'">
                                </div>
                            `).join("")}
                        </div>
                    </div>
                `;
            }

            // Critics (same as Flask)
            let criticsHtml = "";
            if (gameData.critics && gameData.critics.length > 0) {
                criticsHtml = `
                    <div class="modal-critics">
                        <h4>Critic Reviews</h4>
                        ${gameData.critics.map((critic) => {
                            const reviewText = critic.review || "";
                            return `
                                <div class="critic-card">
                                    <div class="critic-content">${reviewText}</div>
                                </div>
                            `;
                        }).join("")}
                    </div>
                `;
            }

            // Create full modal content (same as Flask)
            return `
                <img src="${coverUrl}" alt="${gameData.title}" class="modal-game-cover" onerror="this.style.display='none'">
                <div class="modal-game-info">
                    <h2 class="modal-game-title">${gameData.title}</h2>
                    <div class="modal-game-meta">
                        <span class="meta-item">${year}</span>
                        ${scoreHtml}
                        <span class="meta-item">${platforms}</span>
                        <span class="meta-item">${genres}</span>
                    </div>
                </div>
                ${gameData.description ? `
                    <div class="modal-description">
                        <h4>Description</h4>
                        <p>${gameData.description}</p>
                    </div>
                ` : ""}
                ${screenshotsHtml}
                ${criticsHtml}
            `;
        }

        function closeModal() {
            const modal = document.querySelector('.modal-overlay');
            if (modal) {
                modal.remove();
            }
        }

        // AI Sidebar functions (matching Flask exactly)
        function createAISidebar(response) {
            console.log('createAISidebar called with response:', response);
            // Remove existing sidebar if any
            removeAISidebar();

            // Clean up the response text
            const cleanResponse = cleanAIResponse(response);
            console.log('Cleaned response:', cleanResponse);

            // Create sidebar HTML
            const sidebarHTML = `
                <div class="ai-sidebar open" id="aiSidebar">
                    <div class="ai-sidebar-header">
                        <h3 class="ai-sidebar-title">🤖 AI Analysis</h3>
                        <button class="ai-sidebar-toggle" onclick="toggleAISidebar()">×</button>
                    </div>
                    <div class="ai-sidebar-content">
                        ${cleanResponse}
                    </div>
                </div>
                <button class="ai-sidebar-trigger" onclick="toggleAISidebar()" id="aiSidebarTrigger">
                    🤖
                </button>
            `;

            // Add to body
            document.body.insertAdjacentHTML("beforeend", sidebarHTML);
        }

        function removeAISidebar() {
            console.log('removeAISidebar called');
            const existingSidebar = document.getElementById("aiSidebar");
            const existingTrigger = document.getElementById("aiSidebarTrigger");

            if (existingSidebar) {
                console.log('Removing existing sidebar');
                existingSidebar.remove();
            }
            if (existingTrigger) {
                console.log('Removing existing trigger');
                existingTrigger.remove();
            }
        }

        function toggleAISidebar() {
            const sidebar = document.getElementById("aiSidebar");
            if (sidebar) {
                sidebar.classList.toggle("open");
            }
        }

        function cleanAIResponse(response) {
            console.log('cleanAIResponse called with:', response);
            // Remove any filter text that might appear at the end
            let cleanText = response.replace(
                /I applied filters:.*?\. These are ranked by relevance\.?$/g,
                ""
            );

            // Simple approach: Find where analysis starts, everything before is thinking
            const analysisStartPatterns = [
                /Based on your query/i,
                /Here are the games/i,
                /I found \d+ games/i,
                /^\d+\. \*\*.*?\*\* \(/m,
                /Recommendations:/i,
            ];

            // Find the earliest analysis start pattern
            let analysisStartIndex = -1;
            for (const pattern of analysisStartPatterns) {
                const match = cleanText.search(pattern);
                if (
                    match !== -1 &&
                    (analysisStartIndex === -1 || match < analysisStartIndex)
                ) {
                    analysisStartIndex = match;
                }
            }

            // If we found an analysis start and there's substantial content before it
            if (analysisStartIndex !== -1) {
                const thinkingPart = cleanText.substring(0, analysisStartIndex).trim();
                const analysisPart = cleanText.substring(analysisStartIndex).trim();

                // Only split if there's meaningful thinking content (more than just a few words)
                if (thinkingPart.length > 50) {
                    // Format thinking section in light gray
                    const thinkingHTML = `<div class="thinking-section">${thinkingPart.replace(
                        /\n/g,
                        "<br>"
                    )}</div>`;

                    // Format analysis section normally
                    const analysisHTML = formatAnalysisSection(analysisPart);

                    return `<div class="ai-response-content">${thinkingHTML}${analysisHTML}</div>`;
                }
            }

            // If no clear thinking/analysis split detected, format normally
            return `<div class="ai-response-content">${formatAnalysisSection(
                cleanText
            )}</div>`;
        }

        function formatAnalysisSection(text) {
            // Simple formatting for now
            return `<div class="analysis-section">${text.replace(/\n/g, "<br>")}</div>`;
        }

        // Function to update currentGameResults when search results change
        function updateGameResults(results) {
            console.log('=== updateGameResults called ===');
            console.log('Input results:', results);
            console.log('Results type:', typeof results);
            console.log('Results length:', results ? results.length : 'undefined');

            if (results && results.length > 0) {
                console.log('First result:', results[0]);
                console.log('First result ID:', results[0].id);
                console.log('First result title:', results[0].title);
                console.log('First result cover_path:', results[0].cover_path);
            }

            currentGameResults = results || [];
            console.log('currentGameResults updated to:', currentGameResults);
            console.log('currentGameResults length:', currentGameResults.length);
            console.log('=== updateGameResults completed ===');
        }

        // Test function to verify JavaScript is working
        function testJavaScript() {
            console.log('JavaScript is working!');
            console.log('Current game results:', currentGameResults);
            console.log('Current game results length:', currentGameResults.length);

            let message = 'JavaScript is working!\\n';
            message += 'Current game results: ' + currentGameResults.length + '\\n';
            if (currentGameResults.length > 0) {
                message += 'First game: ' + currentGameResults[0].title + '\\n';
                message += 'First game ID: ' + currentGameResults[0].id + '\\n';
                message += 'First game cover: ' + (currentGameResults[0].cover_path || 'No cover');
            } else {
                message += 'No game results found. Try searching first.';
            }
            alert(message);
        }

        // Debug function to manually set test data
        function setTestGameData() {
            const testData = [{
                id: 123,
                title: 'Test Game',
                release_date: '2023-01-01',
                platforms: 'PC',
                genres: 'Action',
                moby_score: 85,
                description: 'This is a test game for debugging.',
                cover_path: 'https://example.com/cover.jpg',
                screenshot_paths: [],
                critics: []
            }];
            updateGameResults(testData);
            console.log('Test game data set:', testData);
        }
        </script>
        """
