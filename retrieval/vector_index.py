import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import polars as pl
import chromadb
from chromadb.config import Settings
from tqdm import tqdm
from utils.logging_utils import setup_logging

logger = setup_logging(log_name="indexing", with_timestamp=True)

# Load metadata and embeddings
metadata = pl.read_ndjson('data/mobygames_index.jsonl')
desc_emb = pl.read_ndjson('embeddings/desc_embeddings.jsonl')
cover_emb = pl.read_ndjson('embeddings/cover_embeddings.jsonl')
screenshot_emb = pl.read_ndjson('embeddings/screenshot_embeddings.jsonl')
critics_emb = pl.read_ndjson('embeddings/critics_embeddings.jsonl')

# Initialize ChromaDB client with local storage
client = chromadb.Client(Settings(
    persist_directory="chroma_db"
))

# Create collections
desc_collection = client.get_or_create_collection("desc_embeddings")
cover_collection = client.get_or_create_collection("cover_embeddings")
screenshot_collection = client.get_or_create_collection("screenshot_embeddings")
critics_collection = client.get_or_create_collection("critics_embeddings")

BATCH_SIZE = 1000


# Add embeddings to collections
def batch_add(collection, df, emb_col, id_col, label):
    embeddings, ids, metadatas = [], [], []
    total = df.height
    logger.info(f"Indexing {total} entries for {label}...")
    for i, row in enumerate(tqdm(df.iter_rows(named=True), total=total, desc=f"Indexing {label}")):
        embeddings.append(row[emb_col])
        ids.append(str(row[id_col]))
        metadatas.append({})
        if (i + 1) % BATCH_SIZE == 0 or (i + 1) == total:
            collection.add(
                embeddings=embeddings,
                ids=ids,
                metadatas=metadatas
            )
            embeddings, ids, metadatas = [], [], []
    logger.info(f"Finished indexing {label}.")


batch_add(desc_collection, desc_emb, 'embedding', 'game_id')
batch_add(cover_collection, cover_emb, 'cover_embedding', 'game_id')
batch_add(screenshot_collection, screenshot_emb, 'screenshot_embedding', 'game_id')
batch_add(critics_collection, critics_emb, 'embedding', 'game_id')

client.persist()
print("All embeddings indexed!")
