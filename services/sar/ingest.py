import json
import re
from pathlib import Path

from pypdf import PdfReader


SOURCE_DIR = Path("data/fincen/source_documents")
CHUNK_DIR = Path("data/fincen/chunks")

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200


def clean_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def chunk_text(text: str) -> list[str]:
    chunks = []
    start = 0

    while start < len(text):
        end = start + CHUNK_SIZE
        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        start = end - CHUNK_OVERLAP

    return chunks


def parse_pdf(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))

    pages = []

    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(text)

    return clean_text("\n".join(pages))


def ingest_documents() -> None:
    CHUNK_DIR.mkdir(parents=True, exist_ok=True)

    all_chunks = []

    pdf_files = sorted(SOURCE_DIR.glob("*.pdf"))

    if not pdf_files:
        raise FileNotFoundError(
            f"No PDF files found in {SOURCE_DIR}"
        )

    for pdf_path in pdf_files:
        print(f"Processing: {pdf_path.name}")

        text = parse_pdf(pdf_path)
        chunks = chunk_text(text)

        for index, chunk in enumerate(chunks):
            all_chunks.append(
                {
                    "chunk_id": f"{pdf_path.stem}_{index:04d}",
                    "source_file": pdf_path.name,
                    "chunk_index": index,
                    "content": chunk,
                }
            )

        print(f"  Extracted {len(chunks)} chunks")

    output_path = CHUNK_DIR / "fincen_chunks.json"

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2, ensure_ascii=False)

    print()
    print(f"Total chunks: {len(all_chunks)}")
    print(f"Saved to: {output_path}")


if __name__ == "__main__":
    ingest_documents()