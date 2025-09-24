# GameQuest

**Intelligent Game Recommendation System** using Agentic RAG (Retrieval-Augmented Generation) with advanced AI-powered search capabilities.

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://flask.palletsprojects.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue.svg)](https://postgresql.org)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-0.4+-orange.svg)](https://chromadb.ai)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## Features

### AI-Powered Search

- **Text-Based Search**: Natural language game discovery using semantic search
- **Visual Search**: Upload images to find visually similar games using DINOv2
- **Agentic RAG**: Intelligent recommendations with reasoning using Qwen3 LLM

### Advanced Filtering & Search

- Filter by genres, platforms, scores, and release years
- **Score-based filtering**: Show only scored games
- **Multi-modal search**: Text + visual similarity
- **Smart reranking**: Cross-encoder for improved relevance

## Architecture

GameQuest combines PostgreSQL for structured data with vector databases and AI models for intelligent search:

### System Components

```
Frontend (Browser)
↓
Flask Application
↓
├── PostgreSQL (Neon) - Game metadata, reviews, filtering
│   └── 188,267 games, 609,000 reviews, image URLs
├── ChromaDB - Vector similarity search
│   └── Text embeddings, image embeddings
└── AI Models - Intelligent analysis and reasoning
    └── SentenceTransformers, DINOv2, CrossEncoder, Qwen3 LLM
```

### Tech Stack

- **Frontend**: HTML5, CSS3, JavaScript
- **Backend**: Python 3.11+, Flask 3.0+
- **Databases**: PostgreSQL (Neon cloud), ChromaDB (vector storage)
- **AI/ML**: Hugging Face Transformers, Ollama, SentenceTransformers
- **Deployment**: Docker-ready

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+ (or use Neon cloud database)
- Docker (optional)

### Local Development

```bash
# 1. Clone the repository
git clone https://github.com/Arc-Celt/gamequest.git
cd gamequest

# 2. Set up virtual environment
python -m venv .game-env
source .game-env/bin/activate  # Windows: .game-env\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start the application
python app.py
```

Visit `http://localhost:5000` to see the app!

### Using the Remote Database

GameQuest is configured to use a Neon PostgreSQL database with:

- **188,267 games** with complete metadata
- **609,000 critic reviews**
- **Image URLs** for covers and screenshots
- **Optimized schema** for fast queries

## Search Types

### 1. **Text-Based Search**

Natural language queries like:

- "fantasy RPG with crafting"
- "co-op games for friends"
- "indie games with pixel art"

### 2. **Visual Search**

Upload images to find similar games:

- Screenshot similarity
- Cover art matching
- Visual style discovery

### 3. **AI Agent Recommendations**

Intelligent analysis with reasoning:

- Context-aware suggestions
- Detailed explanations
- Personalized recommendations

## Database Schema

### Games Table (188,267 records)

```sql
- id, title, description, release_date
- moby_score, moby_url, platforms, genres
- developers, publishers
- sample_cover_url, sample_screenshot_urls
```

### Critics Table (609,000 records)

```sql
- review_id, game_id, citation
```

### Vector Embeddings

- **Text embeddings**: SentenceTransformer (all-MiniLM-L6-v2)
- **Image embeddings**: DINOv2 (facebook/dinov2-base)
- **Reranking**: CrossEncoder (bge-reranker-base-crossencoder)

## Project Structure

```
gamequest/
├── app.py                           # Main Flask application
├── config.py                        # Configuration settings
├── requirements.txt                 # Python dependencies
├── gamequest_schema.sql            # Database schema
├──
├── static/                         # Frontend assets
│   ├── css/style.css              # Styling with AI analysis formatting
│   ├── js/main.js                 # Frontend logic and API calls
│   └── images/
│
├── templates/                      # HTML templates
│   └── index.html                 # Main UI
│
├── utils/                          # Utility modules
│   ├── database.py                # Database operations
│   └── logging_utils.py           # Logging configuration
│
├── retrieval/                      # Search and AI logic
│   ├── search_service.py          # Search orchestration
│   ├── agentic_rag.py             # AI agent implementation
│   ├── vector_index.py            # Vector search
│   └── score_fusion.py            # Score combination
│
├── models/                         # ML model management
│   └── load_models.py             # Model loading and caching
│
├── notebooks/                      # Analysis and development
│   ├── eda.ipynb                  # Exploratory data analysis
│   └── reranking.ipynb            # Reranking experiments
│
├── data/                          # Data files
├── embeddings/                    # Vector embeddings
├── chroma_db/                     # ChromaDB storage
└── logs/                          # Application logs
```

## Configuration

### Database Configuration

```python
# utils/database.py
DB_CONFIG = {
    'host': 'your-neon-host',
    'database': 'neondb',
    'user': 'your-user',
    'password': 'your-password',
    'sslmode': 'require'
}
```

### Model Configuration

```python
# models/load_models.py
- SentenceTransformer: 'all-MiniLM-L6-v2'
- DINOv2: 'facebook/dinov2-base'
- CrossEncoder: 'bge-reranker-base-crossencoder'
- LLM: 'qwen3:0.6b' (via Ollama)
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [MobyGames](https://www.mobygames.com/) for comprehensive game data
- [Neon](https://neon.tech/) for PostgreSQL hosting
- [Hugging Face](https://huggingface.co/) for ML models and hosting
- [ChromaDB](https://github.com/chroma-core/chroma) for vector search
- [Ollama](https://ollama.ai/) for LLM integration

## Support

- Issues: [GitHub Issues](https://github.com/Arc-Celt/gamequest/issues)
- Discussions: [GitHub Discussions](https://github.com/Arc-Celt/gamequest/discussions)
