from app.embedding import embed_query
from app.vector_store import get_collection

TOP_K = 5


def retrieve(question: str, top_k: int = TOP_K):
    """Ambil top-k chunk terdekat beserta skor kemiripan (cosine)."""
    collection = get_collection()
    result = collection.query(
        query_embeddings=[embed_query(question).tolist()],
        n_results=top_k,
    )
    hits = []
    for i in range(len(result["ids"][0])):
        hits.append({
            "id": result["ids"][0][i],
            "text": result["documents"][0][i],
            "source": result["metadatas"][0][i]["source"],
            "section": result["metadatas"][0][i]["section"],
            "score": 1 - result["distances"][0][i],
        })
    return hits