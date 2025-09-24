"""
ML Models loading and initialization for GameQuest
"""

import os
import logging

os.environ["HF_HOME"] = "/home/user/huggingface"
os.environ["HF_HUB_CACHE"] = "/home/user/huggingface/hub"
os.environ["TRANSFORMERS_CACHE"] = "/home/user/huggingface/hub"
os.environ["TMPDIR"] = "/tmp"
os.environ["XDG_CACHE_HOME"] = "/home/user/cache"
os.environ["HOME"] = "/home/user"
os.environ["CACHE_DIR"] = "/home/user/cache"

try:
    import os
    if not os.path.exists("/.cache"):
        os.symlink("/home/user/cache", "/.cache")
except Exception:
    pass


def _setup_hf_cache():
    """Setup Hugging Face cache directories with proper permissions"""
    try:
        hf_home = os.environ.get("HF_HOME", "/home/user/huggingface")
        hf_hub_cache = os.environ.get("HF_HUB_CACHE", "/home/user/huggingface/hub")
        transformers_cache = os.environ.get("TRANSFORMERS_CACHE", hf_hub_cache)

        # Create directories
        for path in [hf_home, hf_hub_cache, transformers_cache]:
            if path:
                os.makedirs(path, exist_ok=True)
                try:
                    os.chmod(path, 0o777)
                except Exception:
                    pass

        # Set environment variables
        os.environ["HF_HOME"] = hf_home
        os.environ["HF_HUB_CACHE"] = hf_hub_cache
        os.environ["TRANSFORMERS_CACHE"] = transformers_cache

        logger = logging.getLogger(__name__)
        logger.info(f"HF cache configured: HF_HOME={hf_home}, HF_HUB_CACHE={hf_hub_cache}")
        logger.info(f"Current TMPDIR: {os.environ.get('TMPDIR', 'not set')}")
        logger.info(f"Current XDG_CACHE_HOME: {os.environ.get('XDG_CACHE_HOME', 'not set')}")

    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.warning(f"HF cache setup warning: {e}")


# Setup cache before importing HF libraries
_setup_hf_cache()

import chromadb
from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModelForSequenceClassification, AutoModelForCausalLM, pipeline
import torch
from llama_index.llms.ollama import Ollama
from PIL import Image
import io
import numpy as np
import base64
import tarfile
import requests
import gdown
import tempfile
from typing import List, Tuple

logger = logging.getLogger(__name__)


def is_huggingface_spaces():
    """Detect if running on Hugging Face Spaces"""
    return os.environ.get('SPACE_ID') is not None or os.path.exists('/opt/conda')


def get_model_path(model_name, local_path, hf_model_id):
    """Get appropriate model path based on environment"""
    if is_huggingface_spaces():
        logger.info(f"🔄 Loading {model_name} from Hugging Face Hub: {hf_model_id}")
        return hf_model_id
    else:
        # Make path absolute relative to this file's directory
        abs_local_path = os.path.join(os.path.dirname(__file__), local_path)
        if os.path.exists(abs_local_path):
            logger.info(f"🔄 Loading {model_name} from local path: {abs_local_path}")
            return abs_local_path
        else:
            logger.warning(f"Local model not found at {abs_local_path}, downloading from Hugging Face Hub")
            return hf_model_id


class ModelManager:
    """Manages all ML models and ChromaDB collections"""

    def __init__(self):
        self.desc_encoder = None
        self.reranker = None
        self.chroma_client = None
        self.desc_collection = None
        self.critics_collection = None
        self.covers_collection = None
        self.screenshots_collection = None
        self.dinov2_model = None
        self.dinov2_processor = None
        self.llm = None
        self.agent = None

    def _download_and_extract_chromadb(self, chroma_path: str):
        """Download and extract ChromaDB from Hugging Face Hub"""
        try:
            logger.info("Downloading ChromaDB archive from Hugging Face Hub...")
            os.makedirs(chroma_path, exist_ok=True)
            temp_archive = "/tmp/chroma_db.tar.gz"    
            os.environ['TMPDIR'] = '/tmp'

            try:
                with open(temp_archive, 'w') as f:
                    f.write("test")
                os.remove(temp_archive)
                logger.info(f"Temp file creation test passed: {temp_archive}")
            except Exception as e:
                logger.error(f"Temp file creation test failed: {e}")
                raise

            # Download from Hugging Face Hub
            try:
                from huggingface_hub import hf_hub_download
                import shutil

                logger.info("Downloading from Hugging Face Hub...")
                downloaded_path = hf_hub_download(
                    repo_id="celt313/gamequest-chroma-db",
                    filename="chroma_db.tar.gz",
                    cache_dir="/tmp",
                    local_dir=None
                )

                shutil.copy2(downloaded_path, temp_archive)

                file_size = os.path.getsize(temp_archive)
                logger.info(f"Downloaded {file_size} bytes to {temp_archive}")

                with open(temp_archive, 'rb') as f:
                    header = f.read(2)
                    if header == b'\x1f\x8b':
                        logger.info("Verified: Downloaded file is a valid gzip archive")
                    else:
                        raise Exception(f"Downloaded file is not gzip (header: {header})")

            except Exception as e:
                logger.error(f"Hugging Face download failed: {e}")
                raise Exception(f"Failed to download ChromaDB from Hugging Face: {e}")

            logger.info("Examining archive structure...")
            with tarfile.open(temp_archive, "r:gz") as tar:
                members = tar.getmembers()
                logger.info(f"Archive contains {len(members)} items")
                root_dirs = set()
                for member in members:
                    parts = member.name.split('/')
                    if len(parts) > 0:
                        root_dirs.add(parts[0])

                logger.info(f"Root directories/files in archive: {root_dirs}")

                # find and extract data
                data_found = False

                # Files directly in archive root
                if "chroma.sqlite3" in root_dirs or any("chroma.sqlite3" in member.name for member in members):
                    logger.info("Found ChromaDB files at archive root, extracting...")
                    tar.extractall(path=chroma_path)
                    data_found = True

                # Files in a subdirectory
                else:
                    for root_dir in root_dirs:
                        if any(member.name.startswith(f"{root_dir}/") and 
                               "chroma.sqlite3" in member.name for member in members):
                            logger.info(f"Found ChromaDB files in '{root_dir}' directory, extracting...")
                            for member in members:
                                if member.name.startswith(f"{root_dir}/"):
                                    # Extract removing the prefix
                                    member.name = member.name.replace(f"{root_dir}/", "")
                                    tar.extract(member, path=chroma_path)
                            data_found = True
                            break

                if not data_found:
                    logger.info("Could not identify ChromaDB structure in archive. Extracting everything...")
                    tar.extractall(path=chroma_path)

            os.remove(temp_archive)

            logger.info("Checking ChromaDB directory contents:")
            for root, dirs, files in os.walk(chroma_path):
                logger.info(f"Directory: {root}")
                logger.info(f"  Files: {files}")
                if files:
                    break

            logger.info("ChromaDB downloaded and extracted successfully!")
        except Exception as e:
            logger.error(f"Failed to download ChromaDB: {e}")
            raise

    def load_models(self):
        """Load all ML models and initialize ChromaDB"""
        logger.info("🔄 Loading ML models and Agent...")

        try:
            # Load description encoder
            desc_path = get_model_path(
                "Description Encoder", 
                'all-MiniLM-L6-v2', 
                'sentence-transformers/all-MiniLM-L6-v2'
            )
            logger.info(f"🔄 Loading Description Encoder from: {desc_path}")
            self.desc_encoder = SentenceTransformer(desc_path)
            logger.info("Description encoder loaded")

            # Load reranker
            reranker_path = get_model_path(
                "Reranker", 
                'bge-reranker-base-crossencoder', 
                'BAAI/bge-reranker-base'
            )
            logger.info(f"🔄 Loading Reranker from: {reranker_path}")
            self.reranker = AutoModelForSequenceClassification.from_pretrained(reranker_path)
            self.reranker_tokenizer = AutoTokenizer.from_pretrained(reranker_path)
            logger.info("Reranker loaded")

            # Initialize ChromaDB
            logger.info("Loading ChromaDB collections...")
            if is_huggingface_spaces():
                chroma_path = "/data/chroma_db"
                os.makedirs(chroma_path, exist_ok=True)
                if not os.path.exists(os.path.join(chroma_path, "chroma.sqlite3")):
                    logger.info("ChromaDB not found, downloading from Google Drive...")
                    self._download_and_extract_chromadb(chroma_path)
            else:
                chroma_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "chroma_db")
                os.makedirs(chroma_path, exist_ok=True)
            self.chroma_client = chromadb.PersistentClient(
                path=chroma_path,
                settings=ChromaSettings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )

            # Get collections
            self.desc_collection = self.chroma_client.get_collection("desc_embeddings")
            self.critics_collection = self.chroma_client.get_collection("critics_embeddings")

            try:
                self.covers_collection = self.chroma_client.get_collection("cover_embeddings")
                self.screenshots_collection = self.chroma_client.get_collection("screenshot_embeddings")
                logger.info("ChromaDB collections loaded (including image collections)")
            except Exception as e:
                logger.warning(f"Image collections not found: {e}")
                self.covers_collection = None
                self.screenshots_collection = None
                logger.info("ChromaDB collections loaded (text only)")

            # Load DINOv2 for image embeddings
            logger.info("Loading DINOv2 model...")
            try:
                from transformers import AutoImageProcessor, AutoModel
                dinov2_path = get_model_path(
                    "DINOv2", 
                    'dinov2-base', 
                    'facebook/dinov2-base'
                )
                logger.info(f"🔄 Loading DINOv2 from: {dinov2_path}")
                self.dinov2_processor = AutoImageProcessor.from_pretrained(dinov2_path)
                self.dinov2_model = AutoModel.from_pretrained(dinov2_path)
                logger.info("DINOv2 model loaded successfully")
            except Exception as e:
                logger.warning(f"DINOv2 model not available: {e}")
                self.dinov2_model = None
                self.dinov2_processor = None

            # Load LLM based on environment
            if is_huggingface_spaces():
                # Hugging Face Transformers for Spaces
                logger.info("Loading Hugging Face Transformers LLM (Qwen3-0.6B)...")
                cuda_available = torch.cuda.is_available()
                if cuda_available:
                    logger.info(f"CUDA available! GPU: {torch.cuda.get_device_name(0)}")
                    logger.info(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
                    device = "cuda"
                else:
                    logger.warning("CUDA not available, using CPU")
                    device = "cpu"

                model_name = "Qwen/Qwen3-4B"
                logger.info(f"Loading {model_name}...")

                self.llm = pipeline(
                    "text-generation",
                    model=model_name,
                    tokenizer=model_name,
                    torch_dtype=torch.float16 if device == "cuda" else torch.float32,
                    device=device,
                    max_new_tokens=1024,
                    do_sample=True,
                    temperature=0.1,
                    top_p=0.9,
                    return_full_text=False,
                )
                logger.info("Hugging Face Transformers LLM loaded successfully")

            else:
                # Ollama for local development
                from llama_index.llms.ollama import Ollama

                logger.info("Loading Ollama LLM (Qwen3 0.6B)...")

                cuda_available = torch.cuda.is_available()
                if cuda_available:
                    logger.info(f"CUDA available! GPU: {torch.cuda.get_device_name(0)}")
                    logger.info(f"GPU Memory: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.1f} GB")
                else:
                    logger.warning("CUDA not available, using CPU")

                if cuda_available:
                    os.environ["OLLAMA_HOST"] = "0.0.0.0:11434"
                    os.environ["OLLAMA_GPU_LAYERS"] = "-1"
                    logger.info("Configured Ollama to use GPU")
                else:
                    logger.info("Ollama will use CPU")

                self.llm = Ollama(
                    model="qwen3:0.6b",
                    request_timeout=60.0,
                    temperature=0.1,
                    top_p=0.9,
                    max_tokens=2048
                )
                logger.info("Ollama LLM (Qwen3 0.6B) loaded with optimized settings")

            self.agent = True
            logger.info("ReActAgent created with reasoning capabilities")

            logger.info("All models loaded successfully!")
            return True

        except Exception as e:
            logger.error(f"Error loading models: {e}")
            return False

    def encode_query(self, query: str) -> list:
        """Encode a query using the description encoder"""
        if not self.desc_encoder:
            raise RuntimeError("Description encoder not loaded")
        return self.desc_encoder.encode(query).tolist()

    def rerank_results(self, query: str, passages: List[str], scores: List[float]) -> Tuple[List[str], List[float]]:
        """Rerank search results using cross-encoder"""
        if not self.reranker or not self.reranker_tokenizer:
            raise RuntimeError("Reranker not loaded")
        if not passages:
            return [], []
        pairs = [(query, passage) for passage in passages]

        # tokenize and encode pairs
        try:
            inputs = self.reranker_tokenizer(pairs, padding=True, truncation=True, 
                                           return_tensors='pt', max_length=512)
            with torch.no_grad():
                outputs = self.reranker(**inputs)
                if outputs.logits.dim() == 2:
                    if outputs.logits.size(1) >= 2:
                        rerank_scores = torch.softmax(outputs.logits, dim=-1)[:, 1].cpu().numpy().astype(float)
                    else:
                        rerank_scores = torch.sigmoid(outputs.logits[:, 0]).cpu().numpy().astype(float)
                else:
                    rerank_scores = scores

            # Combine with original scores and sort
            combined_scores = []
            for i, (orig_score, rerank_score) in enumerate(zip(scores, rerank_scores)):
                combined_scores.append((i, orig_score * 0.7 + rerank_score * 0.3))

            # Sort by combined score
            combined_scores.sort(key=lambda x: x[1], reverse=True)
            reranked_passages = [passages[i] for i, _ in combined_scores]
            reranked_scores = [score for _, score in combined_scores]
            return reranked_passages, reranked_scores

        except Exception as e:
            logger.warning(f"Reranking failed, using original order: {e}")
            return passages, scores

    def search_descriptions(self, query: str, num_results: int = 10) -> Tuple[List[int], List[float]]:
        """Search game descriptions using ChromaDB"""
        if not self.desc_collection:
            raise RuntimeError("Description collection not loaded")
        
        query_embedding = self.encode_query(query)
        results = self.desc_collection.query(
            query_embeddings=[query_embedding],
            n_results=num_results,
            include=['metadatas', 'distances']
        )

        game_ids = [int(metadata['game_id']) for metadata in results['metadatas'][0]]
        # Convert L2 distances to similarity scores
        max_distance = max(results['distances'][0]) if results['distances'][0] else 1.0
        scores = [float(1 - (distance / max_distance)) for distance in results['distances'][0]]

        return game_ids, scores

    def search_critics(self, query: str, num_results: int = 10) -> Tuple[List[int], List[float]]:
        """Search critic reviews using ChromaDB"""
        if not self.critics_collection:
            raise RuntimeError("Critics collection not loaded")

        query_embedding = self.encode_query(query)
        results = self.critics_collection.query(
            query_embeddings=[query_embedding],
            n_results=num_results,
            include=['metadatas', 'distances']
        )

        game_ids = [int(metadata['game_id']) for metadata in results['metadatas'][0]]
        scores = [float(1 - distance) for distance in results['distances'][0]]  # Convert distance to similarity

        return game_ids, scores

    def search_covers(self, query: str, num_results: int = 10) -> Tuple[List[int], List[float]]:
        """Search game covers using ChromaDB"""
        if not self.covers_collection:
            raise RuntimeError("Covers collection not loaded")

        query_embedding = self.encode_query(query)
        results = self.covers_collection.query(
            query_embeddings=[query_embedding],
            n_results=num_results,
            include=['metadatas', 'distances']
        )

        game_ids = [int(metadata['game_id']) for metadata in results['metadatas'][0]]
        # Convert L2 distances to similarity scores
        max_distance = max(results['distances'][0]) if results['distances'][0] else 1.0
        scores = [float(1 - (distance / max_distance)) for distance in results['distances'][0]]

        return game_ids, scores

    def search_screenshots(self, query: str, num_results: int = 10) -> Tuple[List[int], List[float]]:
        """Search game screenshots using ChromaDB"""
        if not self.screenshots_collection:
            raise RuntimeError("Screenshots collection not loaded")

        query_embedding = self.encode_query(query)
        results = self.screenshots_collection.query(
            query_embeddings=[query_embedding],
            n_results=num_results,
            include=['metadatas', 'distances']
        )

        game_ids = [int(metadata['game_id']) for metadata in results['metadatas'][0]]
        # Convert L2 distances to similarity scores
        max_distance = max(results['distances'][0]) if results['distances'][0] else 1.0
        scores = [float(1 - (distance / max_distance)) for distance in results['distances'][0]]

        return game_ids, scores

    def extract_image_embedding(self, image_data) -> np.ndarray:
        """Extract DINOv2 embedding from uploaded image"""
        if not self.dinov2_model or not self.dinov2_processor:
            raise RuntimeError("DINOv2 model not loaded")

        try:
            if isinstance(image_data, bytes):
                image = Image.open(io.BytesIO(image_data))
            else:
                image = image_data
            if image.mode != 'RGB':
                image = image.convert('RGB')
            inputs = self.dinov2_processor(images=image, return_tensors="pt")

            # Extract features
            with torch.no_grad():
                outputs = self.dinov2_model(**inputs)
                # Use CLS token embedding (first token)
                embedding = outputs.last_hidden_state[:, 0, :].cpu().numpy()

            embedding = embedding.flatten()

            return embedding

        except Exception as e:
            logger.error(f"Error extracting image embedding: {e}")
            raise


# Global model manager instance
model_manager = ModelManager()
