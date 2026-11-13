from pydantic import BaseModel, ConfigDict, Field


class AskRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    question: str = Field(..., min_length=3, max_length=500,
                          examples=["Berapa hari cuti tahunan pegawai tetap?"])


class Source(BaseModel):
    document: str
    section: str
    chunk_id: str
    score: float


class AskResponse(BaseModel):
    answer: str
    sources: list[Source]
    grounded: bool
    top_score: float
    latency_ms: int


class IngestResponse(BaseModel):
    documents: int
    chunks: int
    total_in_db: int


class HealthResponse(BaseModel):
    status: str
    indexed_chunks: int