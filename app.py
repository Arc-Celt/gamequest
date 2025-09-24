#!/usr/bin/env python3
"""
GameQuest - Intelligent Game Discovery with Agentic RAG
Main Flask application with clean separation of concerns
"""

import asyncio
import nest_asyncio
import logging
from flask import Flask, request, jsonify, render_template, redirect

# Import our modules
from models.load_models import ModelManager
from retrieval.search_service import SearchService
from retrieval.agentic_rag import AgenticRAGService
from utils.database import get_games_from_db, get_platforms, get_genres, search_games_by_text

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Apply nest_asyncio to allow nested event loops
nest_asyncio.apply()

# Initialize Flask app
app = Flask(__name__)

# Global variables for services
model_manager = None
search_service = None
agentic_rag_service = None

def initialize_app():
    """Initialize all services and models"""
    global model_manager, search_service, agentic_rag_service
    
    logger.info("Starting GameQuest app with Agentic RAG...")
    
    # Load models
    model_manager = ModelManager()
    if model_manager.load_models():
        logger.info("All models loaded successfully!")
        
        # Initialize services
        search_service = SearchService(model_manager)
        agentic_rag_service = AgenticRAGService(model_manager, search_service)
        
        logger.info("Visit: http://localhost:5000")
        logger.info("Try both 'Text Search' and 'AI Search' buttons!")
        return True
    else:
        logger.error("Failed to load models")
        return False

@app.route('/')
def index():
    """Main page"""
    return render_template('index.html')

@app.route('/api/search')
def search():
    """Text-based search endpoint"""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({'error': 'Query parameter is required'}), 400
        
        # Get filters
        platform = request.args.get('platform')
        score = request.args.get('score', type=float)
        genre = request.args.get('genre')
        year = request.args.get('year', type=int)
        scored_only = request.args.get('scored_only', 'false').lower() == 'true'
        if year == 0:  # Convert 0 to None for empty year
            year = None
        
        # Search games by text
        games = search_games_by_text(
            query=query,
            platform=platform,
            score=score,
            genre=genre,
            year=year,
            scored_only=scored_only
        )
        
        return jsonify({'games': games})
        
    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/semantic-search')
def semantic_search():
    """Semantic search endpoint"""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({'error': 'Query parameter is required'}), 400
        
        # Get filters
        platform = request.args.get('platform')
        score = request.args.get('score', type=float)
        genre = request.args.get('genre')
        year = request.args.get('year', type=int)
        scored_only = request.args.get('scored_only', 'false').lower() == 'true'
        if year == 0:  # Convert 0 to None for empty year
            year = None
        
        # Perform semantic search
        results = search_service.semantic_search(
            query=query,
            platform=platform,
            score=score,
            genre=genre,
            year=year,
            scored_only=scored_only,
            num_results=20
        )
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Semantic search error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/agentic-rag')
def agentic_rag():
    """Agentic RAG search endpoint"""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({'error': 'Query parameter is required'}), 400
        
        # Get filters
        platform = request.args.get('platform')
        score = request.args.get('score', type=float)
        genre = request.args.get('genre')
        year = request.args.get('year', type=int)
        scored_only = request.args.get('scored_only', 'false').lower() == 'true'
        if year == 0:  # Convert 0 to None for empty year
            year = None
        
        # Perform agentic RAG search
        results = agentic_rag_service.agentic_rag_search(
            query=query,
            platform=platform,
            score=score,
            genre=genre,
            year=year,
            scored_only=scored_only
        )
        
        return jsonify(results)
        
    except Exception as e:
        logger.error(f"Agentic RAG error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/platforms')
def platforms():
    """Get available platforms"""
    try:
        platforms = get_platforms()
        return jsonify(platforms)
    except Exception as e:
        logger.error(f"Platforms error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/genres')
def genres():
    """Get available genres"""
    try:
        genres = get_genres()
        return jsonify(genres)
    except Exception as e:
        logger.error(f"Genres error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload-image-search', methods=['POST'])
def upload_image_search():
    """Image upload and similarity search endpoint"""
    try:
        # Check if image file is present
        if 'image' not in request.files:
            return jsonify({'error': 'No image file provided'}), 400
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'error': 'No image file selected'}), 400
        
        # Get search type
        search_type = request.form.get('search_type', 'covers')
        if search_type not in ['covers', 'screenshots']:
            return jsonify({'error': 'Type must be "covers" or "screenshots"'}), 400
        
        # Get filters
        platform = request.form.get('platform')
        score = request.form.get('score', type=float)
        genre = request.form.get('genre')
        year = request.form.get('year', type=int)
        scored_only = request.form.get('scored_only', 'false').lower() == 'true'
        if year == 0:  # Convert 0 to None for empty year
            year = None
        
        # Read image data
        image_data = file.read()
        
        # Extract image embedding using DINOv2
        image_embedding = model_manager.extract_image_embedding(image_data)
        
        # Perform similarity search
        results = search_service.search_by_image_embedding(
            image_embedding=image_embedding,
            search_type=search_type,
            platform=platform,
            score=score,
            genre=genre,
            year=year,
            scored_only=scored_only,
            num_results=20
        )
        
        return jsonify({
            'games': results,
            'total': len(results),
            'search_type': search_type,
            'filters': {'platform': platform, 'score': score, 'genre': genre, 'year': year}
        })
        
    except Exception as e:
        logger.error(f"Upload image search error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/cover/<int:game_id>')
def get_cover(game_id):
    """Serve game cover image"""
    try:
        from utils.database import get_game_cover_path
        
        cover_path = get_game_cover_path(game_id)
        if cover_path and cover_path.startswith(('http://', 'https://')):
            # Redirect to external URL
            return redirect(cover_path)
        else:
            return jsonify({'error': 'Cover not found'}), 404
            
    except Exception as e:
        logger.error(f"Cover error for game {game_id}: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    if initialize_app():
        app.run(host='0.0.0.0', port=5000, debug=True)
    else:
        logger.error("Failed to initialize app")