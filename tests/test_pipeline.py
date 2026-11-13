from app import pipeline
from app.generator import NOT_FOUND


def hit(score, source="a.md"):
    return {"id": "x", "text": "t", "source": source, "section": "s", "score": score}


def siapkan(monkeypatch, hits, jawaban=None):
    monkeypatch.setattr(pipeline, "SCORE_THRESHOLD", 0.835)
    monkeypatch.setattr(pipeline, "retrieve", lambda q, top_k: hits)
    dikirim = []

    def palsu(q, h):
        dikirim.append(h)
        if jawaban is None:
            raise AssertionError("LLM tidak boleh dipanggil")
        return jawaban

    monkeypatch.setattr(pipeline, "generate_answer", palsu)
    return dikirim


def test_di_bawah_threshold_tidak_memanggil_llm(monkeypatch):
    siapkan(monkeypatch, [hit(0.80)])
    hasil = pipeline.ask("pertanyaan apa saja")
    assert hasil["grounded"] is False
    assert hasil["answer"] == NOT_FOUND
    assert hasil["sources"] == []


def test_lolos_threshold_menghasilkan_jawaban_dan_sumber(monkeypatch):
    siapkan(monkeypatch, [hit(0.90)], jawaban="Jawaban.\n\nSumber: a.md")
    hasil = pipeline.ask("pertanyaan apa saja")
    assert hasil["grounded"] is True
    assert hasil["sources"][0]["document"] == "a.md"


def test_skor_tepat_di_threshold_dianggap_lolos(monkeypatch):
    siapkan(monkeypatch, [hit(0.835)], jawaban="Jawaban.")
    assert pipeline.ask("pertanyaan apa saja")["grounded"] is True


def test_hanya_chunk_lolos_dikirim_ke_llm(monkeypatch):
    dikirim = siapkan(monkeypatch, [hit(0.90), hit(0.80)], jawaban="Jawaban.")
    pipeline.ask("pertanyaan apa saja")
    assert len(dikirim[0]) == 1


def test_llm_menolak_membuang_sumber_dan_teks_tambahan(monkeypatch):
    siapkan(monkeypatch, [hit(0.90)], jawaban=NOT_FOUND + "\n\nSumber: [a.md]")
    hasil = pipeline.ask("pertanyaan apa saja")
    assert hasil["grounded"] is False
    assert hasil["answer"] == NOT_FOUND
    assert hasil["sources"] == []