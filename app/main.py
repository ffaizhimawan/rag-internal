from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from app.embedding import get_model
from app.ingestion import load_all_chunks
from app.pipeline import ask
from app.schemas import (AskRequest, AskResponse, HealthResponse,
                         IngestResponse)
from app.vector_store import get_collection, index_chunks


@asynccontextmanager
async def lifespan(app: FastAPI):
    get_model()  # muat model embedding saat start, bukan saat request pertama
    yield


app = FastAPI(
    title="AI Service Dokumen Internal",
    description="RAG: tanya jawab berdasarkan dokumen internal perusahaan.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok", indexed_chunks=get_collection().count())


@app.post("/ingest", response_model=IngestResponse)
def ingest():
    chunks = load_all_chunks()
    if not chunks:
        raise HTTPException(status_code=404,
                            detail="Tidak ada dokumen di data/documents.")
    total = index_chunks(chunks)
    return IngestResponse(
        documents=len({c["source"] for c in chunks}),
        chunks=len(chunks),
        total_in_db=total,
    )


@app.post("/ask", response_model=AskResponse)
def ask_question(req: AskRequest):
    if get_collection().count() == 0:
        raise HTTPException(status_code=409,
                            detail="Belum ada data. Jalankan POST /ingest dulu.")
    try:
        return ask(req.question)
    except RuntimeError as e:
        raise HTTPException(status_code=503,
                            detail=f"Layanan LLM sedang tidak tersedia: {e}")