"""
GameQuest Gradio App
"""

import os
import sys
import logging
from dotenv import load_dotenv

load_dotenv()

sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'core'))

from models.load_models import ModelManager
from retrieval.search_service import SearchService
from retrieval.agentic_rag import AgenticRAGService
from components import GameQuestUI
from search_handlers import SearchHandlers

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GameQuestGradioApp:

    def __init__(self):
        self.model_manager = None
        self.search_service = None
        self.agentic_rag_service = None
        self.search_handlers = None
        self.ui = GameQuestUI()
        self.initialized = False

    def initialize_models(self):
        try:
            logger.info("🔄 Initializing GameQuest Gradio app...")

            # Load models
            logger.info("🔄 Loading ML models and Agent...")
            self.model_manager = ModelManager()

            if not self.model_manager.load_models():
                logger.error("Failed to load models")
                return False

            # Initialize services
            self.search_service = SearchService(self.model_manager)
            self.agentic_rag_service = AgenticRAGService(self.model_manager, self.search_service)

            # Initialize search handlers
            self.search_handlers = SearchHandlers(
                self.model_manager, 
                self.search_service, 
                self.agentic_rag_service
            )

            self.initialized = True
            logger.info("✅ GameQuest Gradio app initialized successfully!")
            return True

        except Exception as e:
            logger.error(f"❌ Initialization failed: {e}")
            return False

    def create_app(self):
        """Create and configure the Gradio interface"""
        if not self.initialize_models():
            logger.error("Failed to initialize models")
            return None

        # Create UI components with event handlers
        components = self.ui.create_layout(self.search_handlers)

        return components['interface']


def main():
    app = GameQuestGradioApp()
    interface = app.create_app()

    if interface:
        interface.launch(
            server_name="0.0.0.0",
            server_port=7860,
            share=False,
            debug=False
        )
    else:
        logger.error("Failed to create app interface")


if __name__ == "__main__":
    main()
