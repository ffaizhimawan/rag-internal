from app.config import SCORE_THRESHOLD, TOP_K
from app.generator import generate_answer
from app.retriever import retrieve

PERTANYAAN = [
    "Berapa hari cuti tahunan pegawai tetap?",
    "Apakah pegawai baru yang masih probation boleh WFH dan ambil cuti tahunan?",
    "Lupa password, harus gimana ya?",
    "Berapa gaji pokok seorang manajer?",
    "Kapan THR dibayarkan?",
    "Bagaimana cara memasak nasi goreng?",
]

for q in PERTANYAAN:
    hits = retrieve(q, top_k=TOP_K)
    top = hits[0]["score"]
    status = "LOLOS threshold" if top >= SCORE_THRESHOLD else "DI BAWAH threshold (lapis 1 akan menolak)"
    print(f"\nPertanyaan : {q}")
    print(f"Skor top   : {top:.3f} -> {status}")
    print("Jawaban LLM (diuji walau di bawah threshold):")
    print(generate_answer(q, hits))
    print("-" * 60)