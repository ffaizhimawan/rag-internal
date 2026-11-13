import logging
import time

from app.config import SCORE_THRESHOLD, TOP_K
from app.generator import NOT_FOUND, generate_answer
from app.retriever import retrieve
from pathlib import Path

# logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
Path("logs").mkdir(exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("logs/rag.log", encoding="utf-8"),
    ],
)

log = logging.getLogger("rag")


def ask(question: str) -> dict:
    start = time.perf_counter()
    question = question.strip()

    hits = retrieve(question, top_k=TOP_K)
    top_score = hits[0]["score"] if hits else 0.0
    relevant = [h for h in hits if h["score"] >= SCORE_THRESHOLD]

    if not relevant:
        # Lapis 1: skor terlalu rendah, LLM tidak dipanggil
        answer, grounded, sources, reason = NOT_FOUND, False, [], "below_threshold"
    else:
        answer = generate_answer(question, relevant)
        if answer.startswith(NOT_FOUND):
            # Lapis 2: LLM menolak, buang teks tambahan dan sumber
            answer, grounded, sources, reason = NOT_FOUND, False, [], "llm_refused"
        else:
            grounded, reason = True, "answered"
            sources = [
                {
                    "document": h["source"],
                    "section": h["section"],
                    "chunk_id": h["id"],
                    "score": round(h["score"], 3),
                }
                for h in relevant
            ]

    latency_ms = round((time.perf_counter() - start) * 1000)
    # log.info(
    #     "q=%r | top_score=%.3f | retrieved=%d | used=%d | reason=%s | %dms",
    #     question, top_score, len(hits), len(relevant), reason, latency_ms,
    # )

    retrieved = ", ".join(f"{h['source']}>{h['section']}:{h['score']:.3f}" for h in hits)
    log.info(
        "q=%r | top_score=%.3f | used=%d/%d | reason=%s | %dms | retrieved=[%s]",
        question, top_score, len(relevant), len(hits), reason, latency_ms, retrieved,
    )

    return {
        "answer": answer,
        "sources": sources,
        "grounded": grounded,
        "top_score": round(top_score, 3),
        "latency_ms": latency_ms,
    }