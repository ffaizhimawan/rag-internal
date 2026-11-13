from sentence_transformers import SentenceTransformer

MODEL_NAME = "intfloat/multilingual-e5-small"
_model = None


def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model


def embed_passages(texts):
    """Embedding untuk potongan dokumen."""
    prefixed = [f"passage: {t}" for t in texts]
    return get_model().encode(prefixed, normalize_embeddings=True)


def embed_query(text):
    """Embedding untuk pertanyaan pengguna."""
    return get_model().encode(f"query: {text}", normalize_embeddings=True)


if __name__ == "__main__":
    import numpy as np

    pasangan = [
        ("hak libur tahunan pegawai", "cuti tahunan"),
        ("hak libur tahunan pegawai", "cara reset password"),
        ("ngajuin cuti harus kapan", "pengajuan cuti paling lambat 7 hari kerja"),
        ("ngajuin cuti harus kapan", "batas hadiah dari vendor"),
    ]
    for query, passage in pasangan:
        q = embed_query(query)
        p = embed_passages([passage])[0]
        skor = float(np.dot(q, p))
        print(f"{skor:.3f} | '{query}' vs '{passage}'")

    vec = embed_passages(["contoh teks"])[0]
    print(f"\nDimensi vektor: {len(vec)}")