# AI Service Dokumen Internal (Prototype RAG)

Prototype layanan tanya jawab berbasis dokumen internal perusahaan. Pegawai mengirim pertanyaan, sistem mencari bagian dokumen yang relevan secara semantik, lalu LLM menyusun jawaban **hanya** dari bagian tersebut. Jika dokumen tidak memuat jawabannya, sistem menolak menjawab dan tidak mengarang.

Prototype ini mendemonstrasikan: API (FastAPI), embedding, vector database, semantic retrieval, LLM, dan pipeline end-to-end, termasuk penanganan pertanyaan yang tidak punya dasar di dokumen.

## Arsitektur

```
INGESTION
 data/documents/*.md -> parsing -> chunking per heading (+overlap)
   -> embedding (multilingual-e5-small) -> ChromaDB (cosine)

QUERY
 pertanyaan -> embedding -> top-5 chunk terdekat
   -> filter skor >= 0.835
        |-- tidak ada yang lolos -> "tidak ditemukan" (LLM TIDAK dipanggil)   [Lapis 1]
        |-- ada yang lolos       -> LLM (Gemini) dengan prompt "hanya dari konteks"
                                      |-- LLM menolak -> "tidak ditemukan"    [Lapis 2]
                                      |-- LLM menjawab -> answer + sources + grounded=true
```

### Struktur Project
```
app/
  config.py         # konfigurasi dari .env
  ingestion.py      # baca dokumen + chunking + metadata
  embedding.py      # model embedding (awalan "passage: " / "query: ")
  vector_store.py   # ChromaDB, upsert idempotent (ID dari hash isi)
  retriever.py      # top-k + skor cosine
  generator.py      # prompt + pemanggilan Gemini (retry + model cadangan)
  pipeline.py       # ask(): orkestrasi end-to-end + logging
  schemas.py        # model request/response (Pydantic)
  main.py           # endpoint FastAPI
  evaluate.py       # evaluasi otomatis 15 pertanyaan -> tests/hasil_evaluasi.md
data/documents/     # 6 dokumen sampel (dummy)
tests/              # unit test + daftar pertanyaan uji + hasil evaluasi
```

## Teknologi

| Komponen | Pilihan |
|---|---|
| Bahasa | Python 3.14 |
| API | FastAPI + Uvicorn |
| Embedding | `intfloat/multilingual-e5-small` (lokal, 384 dimensi) |
| Vector DB | ChromaDB (embedded, penyimpanan lokal) |
| LLM | Google Gemini API (free tier), `gemini-3.1-flash-lite` dengan cadangan `gemini-3.5-flash` |
| Pengujian | pytest |

Versi library yang diuji:
chromadb                                 1.5.9
fastapi                                  0.162.4
google-genai                             3.2.0
sentence-transformers                    6.3.0
uvicorn                                  0.54.0

## Cara Menjalankan (Windows)

1. **Siapkan environment**
   ```powershell
   py -3.14 -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   ```
2. **Buat API key** di https://aistudio.google.com/apikey, lalu buat file `.env`:
   ```
   GEMINI_API_KEY=isi-key-anda
   GEMINI_MODEL=gemini-3.1-flash-lite
   GEMINI_FALLBACK_MODELS=gemini-3.5-flash
   ```
   Nama model dapat berbeda di tiap akun. Daftar model yang tersedia: `python -m app.list_models`.
3. **Jalankan API**
   ```powershell
   uvicorn app.main:app
   ```
   Pemuatan model embedding pertama kali mengunduh sekitar 470 MB.
4. **Ingest dokumen**, lalu coba lewat Swagger UI di http://localhost:8000/docs (`POST /ingest`, kemudian `POST /ask`).

Docker tidak disertakan pada prototype ini (lihat Keterbatasan).

## Endpoint

| Endpoint | Fungsi |
|---|---|
| `GET /health` | Status API dan jumlah chunk terindeks |
| `POST /ingest` | Baca semua dokumen di `data/documents`, simpan ke vector DB (aman dijalankan berulang) |
| `POST /ask` | Terima pertanyaan, kembalikan jawaban, sumber, dan status `grounded` |

### Contoh: pertanyaan yang ada jawabannya
```json
POST /ask
{"question": "Berapa hari cuti tahunan pegawai tetap?"}
```
```json
{
  "answer": "Setiap pegawai tetap berhak atas 12 hari kerja cuti tahunan per tahun.\n\nSumber: kebijakan_cuti.md",
  "sources": [
    {"document": "kebijakan_cuti.md", "section": "Cuti Tahunan", "chunk_id": "33d6499352d7c79a", "score": 0.917}
  ],
  "grounded": true,
  "top_score": 0.917,
  "latency_ms": 1298
}
```
(`sources` pada respons nyata berisi semua chunk yang dikirim ke LLM, bukan hanya satu.)

### Contoh: pertanyaan di luar dokumen
```json
{"question": "Kapan THR dibayarkan?"}
```
```json
{
  "answer": "Maaf, informasi tersebut tidak ditemukan dalam dokumen yang tersedia.",
  "sources": [],
  "grounded": false,
  "top_score": 0.833,
  "latency_ms": 77
}
```
Input yang tidak valid (misalnya pertanyaan kurang dari 3 karakter) ditolak dengan status 422. Jika vector DB masih kosong, `/ask` mengembalikan 409. Jika LLM tidak tersedia, 503.

## Keputusan Desain

- **Chunking per heading**, maksimal 700 karakter dengan overlap 100 karakter untuk bagian yang panjang. Dokumen sampel berstruktur heading, sehingga satu chunk umumnya memuat satu topik. Tiap chunk diawali judul dokumen dan heading agar tidak kehilangan konteks. Hasilnya 31 chunk dari 6 dokumen.
- **Embedding multilingual lokal.** Dokumen berbahasa Indonesia, sehingga model multilingual diperlukan. Model `small` dipilih karena ringan untuk laptop. Model E5 mewajibkan awalan `passage: ` untuk dokumen dan `query: ` untuk pertanyaan.
- **ChromaDB** dipilih karena paling sederhana dan tanpa server terpisah. Untuk skala produksi, Qdrant atau pgvector layak dipertimbangkan.
- **ID chunk dari hash isi** dan `upsert`, sehingga ingestion berulang tidak menggandakan data (diverifikasi: 31 chunk setelah dijalankan dua kali).
- **Pipeline ditulis sendiri**, tanpa framework orkestrasi, agar setiap tahap terlihat jelas.
- **Temperature 0** pada LLM untuk jawaban yang konsisten.
- **Ketahanan terhadap gangguan API**: retry bertahap pada error 503/429 dan pindah ke model cadangan.

### Penentuan Threshold (0.835)
Skor kemiripan model E5 mengumpul di rentang sempit (kisaran 0.75 sampai 0.93), sehingga threshold tidak bisa ditebak dan ditentukan dari eksperimen pada 15 pertanyaan uji:

| Kelompok | Skor tertinggi per pertanyaan |
|---|---|
| Ada jawabannya (11 pertanyaan) | 0.843 sampai 0.926 |
| Tidak ada jawabannya (4 pertanyaan) | 0.756 sampai 0.827 |

Threshold diambil di titik tengah celah antara skor valid terendah (0.843) dan skor tolak tertinggi (0.827), yaitu sekitar 0.835. Nilainya dapat diubah lewat variabel `SCORE_THRESHOLD` di `.env`.

### Penanganan "Informasi Tidak Ditemukan" (dua lapis)
1. **Lapis 1, retrieval:** jika tidak ada chunk dengan skor di atas threshold, sistem langsung menolak tanpa memanggil LLM (hemat biaya dan cepat, sekitar 77 ms).
2. **Lapis 2, LLM:** prompt melarang memakai pengetahuan di luar konteks dan mewajibkan kalimat penolakan baku. Jika LLM menolak, kode membuang teks tambahan dan daftar sumber, karena pada pengujian LLM pernah menambahkan baris `Sumber:` pada jawaban penolakan.

Dua lapis diperlukan karena pertanyaan yang dekat topik tetapi tidak ada datanya (gaji manajer, THR) mendapat skor yang nyaris sama dengan pertanyaan valid. Pada pengujian API, skor THR tercatat 0.833 pada satu percobaan dan 0.824 pada evaluasi, hanya selisih tipis di bawah threshold.

## Hasil Evaluasi

Dijalankan dengan `python -m app.evaluate` pada 15 pertanyaan (tabel lengkap di `tests/hasil_evaluasi.md`):

| Metrik | Hasil |
|---|---|
| Lulus keseluruhan | 15/15 |
| Jawaban benar (pemeriksaan kata kunci) | 11/11 |
| Sumber dokumen tepat | 11/11 |
| Pertanyaan di luar dokumen ditolak | 4/4 |
| Rata-rata latensi | sekitar 6,1 detik |
| Unit test (`python -m pytest -q`) | 9 lulus |

Komposisi pertanyaan: 6 satu dokumen, 3 lintas dokumen, 2 bahasa tidak baku, dan 4 di luar dokumen (2 dekat topik, 2 jauh dari topik).

## Keterbatasan

- **Evaluasi kecil dan dibuat oleh pembuat sistem.** 15 pertanyaan pada 6 dokumen dummy. Threshold dikalibrasi dari kumpulan yang sama, sehingga hasil 15/15 kemungkinan terlalu optimistis dibanding pertanyaan baru.
- **Margin threshold tipis.** Selisih antara skor valid terendah dan skor tolak tertinggi hanya sekitar 0.016. Pertanyaan baru bisa jatuh di sisi yang salah. Lapis 2 mengurangi, tetapi tidak menghilangkan, risiko ini.
- **Pemeriksaan "jawaban benar" berbasis kata kunci**, bukan penilaian manusia atau metrik semantik.
- **Jawaban lintas dokumen bisa kurang lengkap.** Misalnya, jawaban untuk "apa saja yang diterima pegawai baru" tidak menyebut kewajiban mengganti password sementara. Reranking atau `top_k` lebih besar dapat membantu.
- **`sources` memuat semua chunk yang dikirim ke LLM**, bukan hanya yang benar-benar dikutip dalam jawaban.
- **Latensi didominasi LLM free tier** dan bervariasi, termasuk error 503 saat server Google sibuk. Free tier juga memiliki batas pemakaian dan, menurut ketentuan Google, data yang dikirim dapat dipakai untuk meningkatkan produk Google. **Jangan memakai dokumen rahasia asli** dengan konfigurasi ini.
- **Hanya format Markdown.** Parsing PDF dan DOCX belum diimplementasikan.
- **Penghapusan dokumen tidak ditangani.** Mengubah isi dokumen meninggalkan chunk lama di DB. Untuk prototype, hapus folder `chroma_db` lalu ingest ulang.
- **Tanpa autentikasi, rate limiting, dan riwayat percakapan.**
- **Docker belum disertakan.** Prototype diuji dan dijalankan langsung di Windows tanpa container.

## Pengembangan Lanjutan
Parsing PDF/DOCX, reranking dengan cross-encoder, hybrid search (BM25 + vektor), filter metadata per departemen, evaluasi dengan kumpulan pertanyaan yang lebih besar dan terpisah dari kalibrasi threshold, autentikasi API key, serta kontainerisasi.
