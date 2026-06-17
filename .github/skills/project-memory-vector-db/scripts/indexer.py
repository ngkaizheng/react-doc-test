"""
Stop hook script for Project Memory Vector DB system.

Scans docs/ for markdown files, splits into chunks using a recursive
size-aware strategy (headings → paragraphs → sentences → hard split),
generates embeddings via sentence-transformers, and stores in Chroma
vector database. Tracks changes via manifest.json so only modified
files are re-indexed.

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

#
# ── Chunking Configuration ────────────────────────────────────────────
#
MAX_TOKENS = 768        # Target max tokens per chunk
OVERLAP_CHARS = 512     # ~128 tokens overlap at ~4 chars/token


def estimate_tokens(text: str) -> int:
    """Estimate token count using content-aware heuristic.

    - English prose: ~4 chars/token
    - Code-heavy content (many braces): ~6 chars/token
    - Dense CJK/Unicode text: ~2 chars/token
    """
    # Heuristic: if content has many code-like characters, it's denser
    brace_count = text.count('{') + text.count('}') + text.count('(') + text.count(')')
    lines = max(1, text.count('\n') + 1)
    is_code_heavy = brace_count > lines * 2

    # Check for CJK characters
    cjk_count = sum(1 for c in text if '\u4e00' <= c <= '\u9fff' or '\u3040' <= c <= '\u30ff')
    is_cjk_dense = cjk_count > len(text) * 0.1

    if is_cjk_dense:
        return max(1, len(text) // 2)
    if is_code_heavy:
        return max(1, len(text) // 6)
    return max(1, len(text) // 4)


def _split_text_recursive(text: str, max_tokens: int = MAX_TOKENS) -> list[str]:
    """Recursively split text until all pieces fit within max_tokens.

    Splitting priority (toughest → easiest to break):
      1. Double newlines (paragraphs)
      2. Single newlines
      3. Sentence boundaries (. ! ?)
      4. Hard character split (last resort)
    """
    if estimate_tokens(text) <= max_tokens:
        return [text]

    # Level 1–2: paragraphs (double then single newline)
    for sep in ['\n\n', '\n']:
        if sep in text:
            parts = [p for p in text.split(sep) if p.strip()]
            if len(parts) > 1:
                chunks = _combine_to_chunks(parts, sep, max_tokens)
                result = []
                for chunk in chunks:
                    if estimate_tokens(chunk) > max_tokens:
                        result.extend(_split_text_recursive(chunk, max_tokens))
                    else:
                        result.append(chunk)
                return result

    # Level 3: sentence boundaries
    # Protect against abbreviations (Mr., Dr., U.S.A.), decimals (3.14),
    # and CJK punctuation (。！？) — use a broader lookahead
    # Look behind for sentence-ending punctuation; look ahead for
    # uppercase letter, digit, quote, bracket, brace, hash, or CJK char
    _sent_pattern = re.compile(
        r'(?<=[.!?\u3002\uff01\uff1f])\s+(?=["\'A-Z0-9($\[{#\u4e00-\u9fff])'
    )
    sentences = _sent_pattern.split(text)
    if len(sentences) > 1:
        chunks = _combine_to_chunks(sentences, ' ', max_tokens)
        result = []
        for chunk in chunks:
            if estimate_tokens(chunk) > max_tokens:
                result.extend(_split_text_recursive(chunk, max_tokens))
            else:
                result.append(chunk)
        return result

    # Level 4: hard character split
    max_chars = max_tokens * 4
    return [text[i:i + max_chars] for i in range(0, len(text), max_chars)]


def _combine_to_chunks(parts: list[str], separator: str, max_tokens: int) -> list[str]:
    """Greedily combine parts into chunks not exceeding max_tokens."""
    chunks = []
    current_parts: list[str] = []
    current_tokens = 0

    for part in parts:
        part_tokens = estimate_tokens(part)
        sep_cost = estimate_tokens(separator) if current_parts else 0

        if current_tokens + sep_cost + part_tokens > max_tokens and current_parts:
            chunks.append(separator.join(current_parts))
            current_parts = []
            current_tokens = 0

        current_parts.append(part)
        current_tokens += part_tokens + (sep_cost if len(current_parts) > 1 else 0)

    if current_parts:
        chunks.append(separator.join(current_parts))

    return chunks


def _apply_overlap(chunks: list[str]) -> list[str]:
    """Prepend tail of previous chunk to each subsequent chunk for context continuity."""
    if len(chunks) <= 1:
        return chunks

    result = [chunks[0]]
    for i in range(1, len(chunks)):
        prev = chunks[i - 1]
        curr = chunks[i]
        overlap = prev[-OVERLAP_CHARS:] if len(prev) > OVERLAP_CHARS else prev
        result.append(overlap + '\n' + curr)

    return result


def hash_file(filepath: str) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def slugify(text: str) -> str:
    """Convert text to a URL-safe slug, preserving Unicode characters."""
    text = text.strip()
    # Replace any sequence of whitespace/punctuation with a single hyphen
    text = re.sub(r'[\s\W_]+', '-', text)
    return text.strip('-').lower()


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


def _find_md_files(dir_path: str) -> list[str]:
    """Recursively find all .md files under a directory."""
    files = []
    if not os.path.exists(dir_path):
        return files
    for root, _dirs, filenames in os.walk(dir_path):
        for f in filenames:
            if f.endswith(".md"):
                files.append(os.path.join(root, f))
    return files


def find_markdown_files() -> list[str]:
    """Find all markdown files in docs/ and docs/features/ (recursive)."""
    files = []
    files.extend(_find_md_files(DOCS_DIR))
    files.extend(_find_md_files(FEATURES_DIR))
    return sorted(set(files))


def chunk_markdown(filepath: str) -> list[dict]:
    """Split a markdown file into chunks using recursive, size-aware strategy.

    Strategy:
      1. Primary split by H2/H3 headings (semantic document structure)
      2. If a heading section exceeds MAX_TOKENS (768), recursively split by:
         a. Paragraphs (double newline, then single newline)
         b. Sentences (. ! ? boundary)
         c. Hard character boundary (last resort)
      3. Add 512-char overlap (~128 tokens) between consecutive sub-chunks
      4. Preserve heading hierarchy metadata across all fragments
    """
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
    lines = [line.rstrip('\n\r') for line in lines]

    rel_path = os.path.relpath(filepath, REPO_ROOT).replace(os.sep, '/')
    chunks = []
    current_key = None
    current_heading = None
    current_level = 0
    start_line = 1
    content_lines: list[str] = []
    parent_heading = None

    def flush():
        nonlocal start_line
        if current_key and current_heading and content_lines:
            text = "\n".join(content_lines).strip()
            if text:
                sub_chunks = _split_text_recursive(text)
                if len(sub_chunks) > 1:
                    sub_chunks = _apply_overlap(sub_chunks)

                total_lines = len(content_lines)
                total_chars = len(text)
                for i, sub_text in enumerate(sub_chunks):
                    # Approximate line range for sub-chunk based on char proportion
                    char_ratio = len(sub_text) / max(total_chars, 1)
                    sub_line_count = max(1, int(total_lines * char_ratio))
                    sub_end = start_line + sub_line_count - 1

                    chunk_id = f"{current_key}-{i}" if i > 0 else current_key
                    chunks.append({
                        "id": chunk_id,
                        "content": sub_text,
                        "metadata": {
                            "file": rel_path,
                            "heading": current_heading,
                            "parent_heading": parent_heading or "",
                            "line_start": start_line,
                            "line_end": sub_end,
                            "section_key": current_key,
                            "level": current_level
                        }
                    })
                    start_line = sub_end + 1

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
        model_name="BAAI/bge-m3"
    )

    # Check if collection already exists with matching dimensions
    target_dim = None
    try:
        target_dim = ef._embedding_dim
    except AttributeError:
        pass

    existing = client.list_collections()
    for col in existing:
        if col.name == "project-memory":
            existing_dim = col.metadata.get("embedding_dimensions") if col.metadata else None
            # Only delete if dimensions actually mismatch (model changed)
            if target_dim is not None and existing_dim is not None and existing_dim != target_dim:
                try:
                    client.delete_collection("project-memory")
                    print(f"[indexer] Deleted old collection (dimensions changed: {existing_dim} -> {target_dim})")
                    manifest = load_manifest()
                    manifest["files"] = {}
                    save_manifest(manifest)
                    print("[indexer] Reset manifest — will re-index all files")
                except Exception:
                    pass
            break

    collection = client.get_or_create_collection(
        name="project-memory",
        embedding_function=ef,
        metadata={"hnsw:space": "cosine"}
    )
    return collection


def index_file(filepath: str, collection) -> int:
    """Index a single markdown file into Chroma.

    First deletes ALL existing chunks for this file (to remove orphaned
    data from deleted sections), then upserts the new chunks.

    Uses rel_path from chunk metadata (not filepath) as the Chroma filter
    key for reliable cross-platform matching.
    """
    # Derive the rel_path the same way chunk_markdown does, normalized to forward-slash
    rel_path = os.path.relpath(filepath, REPO_ROOT).replace(os.sep, '/')

    # Delete ALL existing chunks for this file first — this removes
    # stale/orphaned data from sections that were deleted or renamed.
    try:
        collection.delete(where={"file": rel_path})
    except Exception:
        pass  # No existing chunks to delete — first time indexing

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
    """Remove all chunks for a file from the Chroma index."""
    collection.delete(where={"file": file_key})


def run_incremental_index(collection=None) -> dict:
    """Run incremental indexing of docs/ files.

    Scans all markdown files, compares hashes against manifest.json,
    and only re-indexes changed/new files. Removes deleted files from index.

    Args:
        collection: Optional Chroma collection to reuse.
                    If None, creates a new one (loads model).

    Returns:
        dict with keys: indexed, skipped, removed, total_chunks, collection
    """
    import logging
    logging.getLogger("sentence_transformers").setLevel(logging.ERROR)

    os.makedirs(DOCS_DIR, exist_ok=True)
    os.makedirs(FEATURES_DIR, exist_ok=True)

    manifest = load_manifest()
    previous_files = set(manifest.get("files", {}).keys())
    current_files_set = set()

    md_files = find_markdown_files()

    result = {
        "indexed": 0,
        "skipped": 0,
        "removed": 0,
        "total_chunks": 0,
        "total_files": len(md_files),
        "collection": collection
    }

    if not md_files:
        save_manifest(manifest)
        return result

    # Use provided collection or create one
    col = collection if collection is not None else get_or_create_collection()
    result["collection"] = col

    for filepath in md_files:
        rel_path = os.path.relpath(filepath, REPO_ROOT).replace(os.sep, '/')
        current_files_set.add(rel_path)
        file_hash = hash_file(filepath)

        prev_hash = manifest.get("files", {}).get(rel_path, {}).get("hash")
        if prev_hash == file_hash:
            result["skipped"] += 1
            continue

        chunk_count = index_file(filepath, col)
        result["total_chunks"] += chunk_count
        result["indexed"] += 1

        if "files" not in manifest:
            manifest["files"] = {}
        manifest["files"][rel_path] = {
            "hash": file_hash,
            "chunks": chunk_count,
            "indexed_at": datetime.now(timezone.utc).isoformat()
        }

    deleted_files = previous_files - current_files_set
    for rel_path in deleted_files:
        remove_file_from_index(rel_path, col)
        manifest["files"].pop(rel_path, None)
        result["removed"] += 1

    save_manifest(manifest)
    return result


def main():
    """CLI entry point for indexer."""
    result = run_incremental_index()
    col = result["collection"]

    print(f"[indexer] Found {result['total_files']} markdown files")
    print(f"[indexer] Done: {result['indexed']} indexed, {result['skipped']} skipped, "
          f"{result['removed']} removed, {result['total_chunks']} total chunks")
    if col:
        print(f"[indexer] Chroma collection size: {col.count()} chunks")
    sys.exit(0)


if __name__ == "__main__":
    main()
