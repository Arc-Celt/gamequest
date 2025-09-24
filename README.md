# GameQuest

## Overview

GameQuest is an intelligent game recommendation system that leverages multi-modal vector search and Agentic RAG technologies to help users discover their next favorite game. The system integrates multiple AI models including SentenceTransformers for semantic search, DINOv2 for visual similarity, and Qwen3 LLM for intelligent reasoning, providing both traditional filtering and advanced AI-powered recommendations with detailed explanations.

## Live Demo

🚀 **Try GameQuest live**: [Hugging Face Spaces Demo](https://huggingface.co/spaces/celt313/agentic-rag-gamequest)

<img width="800" alt="Image" src="https://github.com/user-attachments/assets/b03b1882-a379-4192-874b-82e34d79f947" />

## Features

- **Advanced Filtering**: Platform, genre, score, year, and scored-only filters
- **Text Search**: Find games by description, title, or metadata
- **Semantic Search**: Vector-based similarity search using SentenceTransformers embeddings
- **AI Agentic RAG**: Intelligent recommendations with reasoning using Qwen3 LLM
- **Visual Search**: Find similar games by cover art or screenshots using DINOv2
- **Interactive UI**: Clickable game cards with detailed modals

## Architecture

```
Frontend (Flask/Gradio)
↓
Core Backend
├── Models (SentenceTransformers, DINOv2, Qwen3)
├── Retrieval (Vector Search, Reranking)
├── Database (PostgreSQL + ChromaDB)
└── AI Agent (Agentic RAG)
```

## Project Structure

```
gamequest/
├── flask/              # Flask web application
│   ├── app.py         # Main Flask app
│   ├── static/        # CSS, JS, images
│   └── templates/     # HTML templates
├── gradio/             # Gradio interface
│   ├── app.py         # Main Gradio app
│   ├── components.py  # UI components
│   └── search_handlers.py # Search logic
├── core/               # Shared backend logic
│   ├── models/        # Model loading and inference
│   ├── retrieval/     # Search services and RAG
│   ├── utils/         # Database utilities
│   └── database/      # Database migration scripts
├── data/               # Database files and embeddings
├── notebooks/          # Jupyter notebooks for analysis
├── Dockerfile          # Container configuration
├── requirements.txt    # Python dependencies
└── README.md
```

## Search Capabilities

### Text Search

- Search by game description, title, or metadata
- Filter by platform, genre, score, year
- Supports both exact and fuzzy matching

### Semantic Search

- Vector-based similarity search
- Uses SentenceTransformers embeddings
- Finds conceptually similar games

### AI Agentic RAG

- Intelligent recommendations with reasoning
- Uses Qwen3 LLM for natural language understanding
- Provides detailed explanations for recommendations

### Visual Search

- Upload cover art or screenshots
- Find visually similar games using DINOv2
- Supports both cover and screenshot similarity

## Data Sources

- **188,000+ games** from MobyGames database
- **600,000+ critic reviews** and ratings
- **Vector embeddings** for semantic search
- **Image embeddings** for visual similarity
- **Structured metadata** (platforms, genres, scores, years)

## Tech Stack

- **Frontend**: HTML5, CSS3, JavaScript (Flask) / Gradio
- **Backend**: Python 3.11+, Flask/Gradio
- **AI/ML**: Hugging Face Transformers, SentenceTransformers, DINOv2
- **Database**: PostgreSQL (Neon), ChromaDB
- **LLM**: Qwen3 (Ollama local / HF Transformers cloud)
- **Deployment**: Docker, Hugging Face Spaces

## Configuration

- **SentenceTransformers**: `all-MiniLM-L6-v2` for text embeddings
- **DINOv2**: `dinov2-base` for image embeddings
- **Reranker**: `BAAI/bge-reranker-base` for result ranking
- **LLM**: `qwen3:0.6b` (for lightweight reasoning)

## Use Cases

- **Game Discovery**: Find games by description or visual similarity
- **AI Recommendations**: Get intelligent suggestions with reasoning
- **Research**: Explore game database with advanced filtering
- **Development**: Build on top of the vector search infrastructure

## License

MIT License - see [LICENSE](LICENSE) file for details.
