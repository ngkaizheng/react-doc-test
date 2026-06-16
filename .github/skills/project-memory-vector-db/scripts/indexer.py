"""
Stop hook script for Project Memory Vector DB system.

Scans docs/ for markdown files, chunks by H2/H3 headings,
generates embeddings via sentence-transformers, and stores
in Chroma vector database. Tracks changes via manifest.json
so only modified files are re-indexed.

Runs automatically at the end of every agent session.
"""

import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone

REPO_ROOT = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "../../../.."
    )
)
PROJECT_DIR = os.path.join(REPO_ROOT, "project-memory-vector-db")
DOCS_DIR = os.path.join(PROJECT_DIR, "docs")
FEATURES_DIR = os.path.join(DOCS_DIR, "features")
VECTOR_DB_DIR = os.path.join(PROJECT_DIR, "vector-db")
MANIFEST_PATH = os.path.join(PROJECT_DIR, "manifest.json")

HEADING_RE = re.compile(r'^(#{2,3})\s+(.+)$')


def hash_file(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text)
    return text.strip('-')


def load_manifest() -> dict:
    if os.path.exists(MANIFEST_PATH):
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"files": {}}


def save_manifest(manifest: dict):
    manifest["last_updated"] = datetime.now(timezone.utc).isoformat()
    os.makedirs(PROJECT_DIR, exist_ok=True)
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)


def find_markdown_files() -> list[str]:
    files = []
    if os.path.exists(DOCS_DIR):
        for f in os.listdir(DOCS_DIR):
            if f.endswith(".md"):
                files.append(os.path.join(DOCS_DIR, f))
    if os.path.exists(FEATURES_DIR):
        for f in os.listdir(FEATURES_DIR):
            if f.endswith(".md"):
                files.append(os.path.join(FEATURES_DIR, f))
    return sorted(files)


def chunk_markdown(filepath: str) -> list[dict]:
    """Split a markdown file into chunks by H2 and H3 headings."""
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    lines = [line.rstrip('\n\r') for line in lines]

    rel_path = os.path.relpath(filepath, REPO_ROOT)
    chunks = []
    current_key = None
    current_heading = None
    current_level = 0
    start_line = 1
    content_lines: list[str] = []
    parent_heading = None

    def flush():
        if current_key and current_heading and content_lines:
            text = "\n".join(content_lines).strip()
            if text:
                chunks.append({
                    "id": current_key,
                    "content": text,
                    "metadata": {
                        "file": rel_path,
                        "heading": current_heading,
                        "parent_heading": parent_heading or "",
                        "line_start": start_line,
                        "line_end": start_line + len(content_lines) - 1,
                        "section_key": current_key,
                        "level": current_level
                    }
                })

    for idx, line in enumerate(lines, start=1):
        m = HEADING_RE.match(line)
        if m:
            flush()
            level = len(m.group(1))
            heading_text = m.group(2).strip()
            current_level = level
            current_heading = heading_text
            current_key = f"{slugify(heading_text)}-{idx}"
            start_line = idx + 1
            content_lines = []

            if level == 3 and chunks:
                for c in reversed(chunks):
                    if c["metadata"]["level"] == 2:
                        parent_heading = c["metadata"]["heading"]
                        break
                else:
                    parent_heading = None
            elif level == 2:
                parent_heading = None
        else:
            content_lines.append(line)

    flush()
    return chunks


def get_or_create_collection():
    import logging
    logging.getLogger("sentence_transformers").setLevel(logging.ERROR)

    import chromadb
    from chromadb.utils import embedding_functions

    os.makedirs(VECTOR_DB_DIR, exist_ok=True)
    client = chromadb.PersistentClient(path=VECTOR_DB_DIR)

    ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name="all-MiniLM-L6-v2"
    )

    collection = client.get_or_create_collection(
        name="project-memory",
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"}
    )
    return collection


def index_file(filepath: str, collection) -> int:
    chunks = chunk_markdown(filepath)
    if not chunks:
        return 0

    ids = []
    documents = []
    metadatas = []

    file_slug = slugify(os.path.basename(filepath).replace('.md', ''))
    for chunk in chunks:
        ids.append(f"{file_slug}-{chunk['id']}")
        documents.append(chunk["content"])
        metadatas.append(chunk["metadata"])

    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
    return len(chunks)


def remove_file_from_index(file_key: str, collection):
    collection.delete(where={"file": file_key})


def main():
    os.makedirs(DOCS_DIR, exist_ok=True)
    os.makedirs(FEATURES_DIR, exist_ok=True)

    manifest = load_manifest()
    previous_files = set(manifest.get("files", {}).keys())
    current_files_set = set()

    md_files = find_markdown_files()
    if not md_files:
        print("[indexer] No markdown files found in docs/. Nothing to index.")
        save_manifest(manifest)
        sys.exit(0)

    print(f"[indexer] Found {len(md_files)} markdown files")

    collection = get_or_create_collection()
    total_chunks = 0
    indexed_files = 0
    skipped_files = 0

    for filepath in md_files:
        rel_path = os.path.relpath(filepath, REPO_ROOT)
        current_files_set.add(rel_path)
        file_hash = hash_file(filepath)

        prev_hash = manifest.get("files", {}).get(rel_path, {}).get("hash")
        if prev_hash == file_hash:
            print(f"  ⏩ {rel_path} — unchanged, skipped")
            skipped_files += 1
            continue

        print(f"  🏗️  {rel_path} — indexing...")
        chunk_count = index_file(filepath, collection)
        total_chunks += chunk_count
        indexed_files += 1

        if "files" not in manifest:
            manifest["files"] = {}
        manifest["files"][rel_path] = {
            "hash": file_hash,
            "chunks": chunk_count,
            "indexed_at": datetime.now(timezone.utc).isoformat()
        }

    deleted_files = previous_files - current_files_set
    for rel_path in deleted_files:
        print(f"  🗑️  {rel_path} — removed, deleting from index")
        remove_file_from_index(rel_path, collection)
        manifest["files"].pop(rel_path, None)

    save_manifest(manifest)

    print(f"\n[indexer] Done: {indexed_files} indexed, {skipped_files} skipped, "
          f"{len(deleted_files)} removed, {total_chunks} total chunks")
    print(f"[indexer] Chroma collection size: {collection.count()} chunks")
    sys.exit(0)


if __name__ == "__main__":
    main()
