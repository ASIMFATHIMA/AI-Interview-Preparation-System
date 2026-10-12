"""Section-aware chunking for job documents."""
import re


def chunk_job_document(document, metadata):
    chunks = []
    job_id = metadata.get("job_id", "JOB")
    matches = list(re.finditer(r"(?m)^([A-Za-z /]+):\s*$", document))
    for index, match in enumerate(matches):
        section = match.group(1).strip()
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(document)
        text = document[start:end].strip()
        if len(text) < 8:
            continue
        clean_section = re.sub(r"[^a-zA-Z0-9]+", "_", section.strip().lower()).strip("_")
        chunk_id = f"{job_id}_{clean_section}"
        chunks.append({
            "job_id": metadata.get("job_id"),
            "chunk_id": chunk_id,
            "job_title": metadata.get("job_title"),
            "company": metadata.get("company"),
            "section": section,
            "text": f"{section}:\n{text}",
        })
    return chunks
