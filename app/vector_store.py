import hashlib
import chromadb

from app.embedding import embed_passages
from app.ingestion import load_all_chunks

DB_PATH = "chroma_db"
COLLECTION_NAME = "dokumen_internal"


def get_collection():
    client = chromadb.PersistentClient(path=DB_PATH)
    return client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def make_id(chunk) -> str:
    raw = f"{chunk['source']}|{chunk['text']}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def index_chunks(chunks) -> int:
    """Simpan chunk ke vector DB. Aman dijalankan berulang (upsert)."""
    collection = get_collection()
    collection.upsert(
        ids=[make_id(c) for c in chunks],
        embeddings=embed_passages([c["text"] for c in chunks]).tolist(),
        documents=[c["text"] for c in chunks],
        metadatas=[
            {
                "source": c["source"],
                "section": c["section"],
                "chunk_index": c["chunk_index"],
            }
            for c in chunks
        ],
    )
    return collection.count()


if __name__ == "__main__":
    chunks = load_all_chunks()
    print(f"Chunk dari dokumen : {len(chunks)}")
    total = index_chunks(chunks)
    print(f"Jumlah data di DB  : {total}")