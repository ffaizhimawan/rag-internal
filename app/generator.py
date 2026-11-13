import time

from google import genai
from google.genai import errors, types

from app.config import FALLBACK_MODELS, GEMINI_API_KEY, LLM_MODEL

NOT_FOUND = "Maaf, informasi tersebut tidak ditemukan dalam dokumen yang tersedia."

SYSTEM_PROMPT = f"""Kamu adalah asisten internal perusahaan yang menjawab pertanyaan pegawai.

ATURAN:
1. Jawab HANYA berdasarkan KONTEKS yang diberikan. Jangan memakai pengetahuan di luar konteks.
2. Jika konteks tidak memuat jawaban yang jelas, jawab persis dengan kalimat ini dan tidak ada tambahan:
   "{NOT_FOUND}"
3. Jangan menebak, berasumsi, atau melengkapi angka yang tidak tertulis di konteks.
4. Jika pertanyaan hanya sebagian terjawab, jawab bagian yang ada di konteks dan sebutkan bagian mana yang tidak ditemukan.
5. Jawab singkat, jelas, dan dalam bahasa Indonesia.
6. Akhiri jawaban dengan baris "Sumber: [nama_file]" untuk file yang kamu pakai."""

_client = None


def get_client():
    global _client
    if _client is None:
        _client = genai.Client(api_key=GEMINI_API_KEY)
    return _client


def build_context(hits) -> str:
    blocks = []
    for h in hits:
        blocks.append(f"[{h['source']} | {h['section']}]\n{h['text']}")
    return "\n\n---\n\n".join(blocks)


# def generate_answer(question: str, hits) -> str:
#     user_message = (
#         f"KONTEKS:\n{build_context(hits)}\n\n"
#         f"PERTANYAAN: {question}"
#     )
#     response = get_client().models.generate_content(
#         model=LLM_MODEL,
#         contents=user_message,
#         config=types.GenerateContentConfig(
#             system_instruction=SYSTEM_PROMPT,
#             temperature=0,
#             max_output_tokens=1024,
#         ),
#     )
#     return (response.text or "").strip()

def generate_answer(question: str, hits) -> str:
    user_message = (
        f"KONTEKS:\n{build_context(hits)}\n\n"
        f"PERTANYAAN: {question}"
    )
    config = types.GenerateContentConfig(
        system_instruction=SYSTEM_PROMPT,
        temperature=0,
        max_output_tokens=1024,
    )

    last_error = None
    for model in [LLM_MODEL] + FALLBACK_MODELS:
        for attempt in range(3):
            try:
                response = get_client().models.generate_content(
                    model=model, contents=user_message, config=config
                )
                return (response.text or "").strip()
            except errors.ServerError as e:  # 5xx: server sibuk
                last_error = e
                print(f"[retry] {model} gagal ({e.code}), percobaan {attempt + 1}/3")
                time.sleep(2 ** (attempt + 1))  # tunggu 2, 4, 8 detik
            except errors.ClientError as e:
                last_error = e
                if e.code == 429:  # batas pemakaian
                    print(f"[retry] {model} kena batas (429), percobaan {attempt + 1}/3")
                    time.sleep(10)
                elif e.code == 404:  # nama model salah: langsung ganti model
                    print(f"[skip] {model} tidak ditemukan")
                    break
                else:
                    raise
    raise RuntimeError(f"Semua model gagal. Error terakhir: {last_error}")