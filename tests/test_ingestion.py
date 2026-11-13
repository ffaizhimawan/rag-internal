from app.ingestion import chunk_document, split_long, split_sections

SAMPLE = """# Judul Dokumen

## Bagian Satu
Isi bagian satu.

## Bagian Dua
Isi bagian dua.
"""


def test_split_sections_membagi_per_heading():
    title, sections = split_sections(SAMPLE)
    assert title == "Judul Dokumen"
    assert [h for h, _ in sections] == ["Bagian Satu", "Bagian Dua"]
    assert sections[0][1] == "Isi bagian satu."


def test_split_long_teks_pendek_tidak_dipecah():
    assert split_long("pendek", max_chars=100) == ["pendek"]


def test_split_long_memecah_dengan_overlap():
    teks = "\n".join(f"Baris nomor {i} berisi kalimat yang cukup panjang." for i in range(30))
    potongan = split_long(teks, max_chars=200, overlap=40)
    assert len(potongan) > 1
    assert all(len(p) <= 240 for p in potongan)
    assert potongan[0][-40:] in potongan[1]  # ekor potongan 1 muncul di awal potongan 2


def test_chunk_document_menyertakan_metadata(tmp_path):
    f = tmp_path / "contoh.md"
    f.write_text(SAMPLE, encoding="utf-8")
    chunks = chunk_document(f)
    assert len(chunks) == 2
    assert chunks[0]["source"] == "contoh.md"
    assert chunks[0]["text"].startswith("Judul Dokumen - Bagian Satu")
    assert chunks[1]["chunk_index"] == 1