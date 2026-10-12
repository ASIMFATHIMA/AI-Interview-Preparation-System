"""Build the persisted job chunk vector index using FAISS and sentence-transformers."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "backend"))

from app.services.job_chunker import chunk_job_document
from app.services.job_document_builder import build_record_document
from app.services.vector_store import build_index


def main():
    dataset_file = ROOT / "data" / "jobs_dataset.json"
    if not dataset_file.exists():
        print(f"Error: {dataset_file} not found. Run generate_jobs_dataset.py first.")
        sys.exit(1)

    records = json.loads(dataset_file.read_text(encoding="utf-8"))
    chunks = []
    for record in records:
        document = build_record_document(record)
        job_metadata = {
            "job_id": record["job_id"],
            "job_title": record["job_title"],
            "company": record["company"],
        }
        record_chunks = chunk_job_document(document, job_metadata)
        chunks.extend(record_chunks)

    print(f"Building index for {len(records)} jobs ({len(chunks)} total section chunks)...")
    result = build_index(chunks)
    print(f"Jobs indexed: {len(records)}")
    print(f"Chunks indexed: {result['chunks']}")
    print(f"Embedding dimension: {result['dimension']}")
    print(f"Index stored at: {result['path']}")
    print("Vector index built successfully.")


if __name__ == "__main__":
    main()
