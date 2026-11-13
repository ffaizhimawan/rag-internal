from pathlib import Path

DOCS_DIR = Path("data/documents")
MAX_CHARS = 700
OVERLAP = 100


def read_document(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def split_sections(text: str):
    """Pecah teks markdown menjadi (judul_dokumen, [(heading, isi), ...])."""
    title = ""
    sections = []
    heading = ""
    lines = []

    def flush():
        body = "\n".join(lines).strip()
        if body:
            sections.append((heading, body))

    for line in text.splitlines():
        if line.startswith("# "):
            title = line[2:].strip()
        elif line.startswith("## "):
            flush()
            heading = line[3:].strip()
            lines = []
        else:
            lines.append(line)
    flush()
    return title, sections


def split_long(text: str, max_chars: int = MAX_CHARS, overlap: int = OVERLAP):
    """Pecah teks panjang per baris, dengan overlap antar potongan."""
    if len(text) <= max_chars:
        return [text]

    pieces = []
    current = ""
    for line in text.splitlines():
        while len(line) > max_chars:  # baris tunggal yang terlalu panjang
            if current:
                pieces.append(current)
                current = ""
            pieces.append(line[:max_chars])
            line = line[max_chars - overlap:]
        if current and len(current) + len(line) + 1 > max_chars:
            pieces.append(current)
            current = current[-overlap:] + "\n" + line
        else:
            current = (current + "\n" + line) if current else line
    if current:
        pieces.append(current)
    return pieces


def chunk_document(path: Path):
    text = read_document(path)
    title, sections = split_sections(text)
    chunks = []
    for heading, body in sections:
        for piece in split_long(body):
            chunks.append({
                "text": f"{title} - {heading}\n{piece}".strip(),
                "source": path.name,
                "section": heading,
                "chunk_index": len(chunks),
            })
    return chunks


def load_all_chunks(docs_dir: Path = DOCS_DIR):
    all_chunks = []
    for path in sorted(docs_dir.glob("*.md")):
        all_chunks.extend(chunk_document(path))
    return all_chunks


if __name__ == "__main__":
    chunks = load_all_chunks()
    print(f"Total chunk: {len(chunks)}\n")
    for c in chunks[:5]:
        print(f"[{c['source']} | {c['section']} | #{c['chunk_index']}]")
        print(c["text"])
        print("-" * 50)