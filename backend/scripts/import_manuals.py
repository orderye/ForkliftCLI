"""Import the generated Docssss Markdown corpus into the knowledge tables and vector index.

Examples:
    python3 -m scripts.import_manuals --dry-run
    python3 -m scripts.import_manuals --limit 5
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
DOCS = ROOT / "Docssss"
sys.path.insert(0, str(BACKEND))

from app.core.database import SessionLocal
from app.core.vector_store import ensure_collection, upsert_point
from app.models.ai import KnowledgeChunk, KnowledgeDocument
from app.services.embedding_service import get_text_embedding


def _read_index() -> list[dict]:
    path = DOCS / "index_summary.json"
    return json.loads(path.read_text(encoding="utf-8"))


def _main_markdown(directory: Path, title: str) -> Path | None:
    candidates = [directory / f"{title}.md", directory / f"{directory.name}.md"]
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    markdown = sorted(directory.glob("*.md"))
    return markdown[0] if markdown else None


def _chunks(text: str, max_chars: int = 1800) -> list[tuple[str, int | None, str]]:
    blocks = re.split(r"(?=^#{1,6}\s+)", text, flags=re.MULTILINE)
    result: list[tuple[str, int | None, str]] = []
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        heading = ""
        match = re.match(r"^#{1,6}\s+(.+)$", block)
        if match:
            heading = match.group(1).strip()
        for start in range(0, len(block), max_chars):
            piece = block[start:start + max_chars].strip()
            if piece:
                result.append((piece, None, heading))
    return result


def import_manuals(dry_run: bool = False, limit: int | None = None) -> dict[str, int]:
    entries = _read_index()
    if limit:
        entries = entries[:limit]
    stats = {"documents": 0, "chunks": 0, "skipped": 0, "failed": 0}
    db = SessionLocal()
    try:
        if not dry_run:
            ensure_collection()
        for entry in entries:
            title = entry["doc_name"]
            directory = DOCS / entry["destination"]
            markdown = _main_markdown(directory, title)
            if not markdown:
                stats["skipped"] += 1
                continue
            text = markdown.read_text(encoding="utf-8", errors="ignore").strip()
            pieces = _chunks(text)
            if not pieces:
                stats["skipped"] += 1
                continue
            stats["documents"] += 1
            stats["chunks"] += len(pieces)
            if dry_run:
                continue
            source = str(markdown.relative_to(ROOT))
            doc = db.query(KnowledgeDocument).filter(
                KnowledgeDocument.title == title,
                KnowledgeDocument.source == source,
            ).first()
            if not doc:
                doc = KnowledgeDocument(
                    title=title,
                    source=source,
                    doc_type="manual",
                    category=entry.get("category", ""),
                    file_type="markdown",
                    summary=text[:240],
                    page_count=len(pieces),
                    license_type="user_uploaded",
                    commercial_use=0,
                )
                db.add(doc)
                db.flush()
            else:
                doc.category = entry.get("category", "")
                doc.summary = text[:240]
                doc.page_count = len(pieces)
            db.query(KnowledgeChunk).filter(KnowledgeChunk.document_id == doc.id).delete()
            for index, (piece, page, section) in enumerate(pieces):
                chunk = KnowledgeChunk(
                    document_id=doc.id,
                    chunk_index=index,
                    chunk_text=piece,
                    embedding_id=f"chunk-{doc.id}-{index}",
                    page_number=page,
                    section_title=section,
                    source_locator=source,
                )
                db.add(chunk)
                db.flush()
                vector = get_text_embedding(piece)
                upsert_point(
                    point_id=f"chunk-{chunk.id}",
                    vector=vector,
                    payload={
                        "doc_id": doc.id,
                        "chunk_id": chunk.id,
                        "title": title,
                        "category": entry.get("category", ""),
                        "text": piece,
                        "url": source,
                        "page_number": page,
                        "section_title": section,
                    },
                )
            db.commit()
    except Exception:
        db.rollback()
        stats["failed"] += 1
        raise
    finally:
        db.close()
    return stats


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    print(import_manuals(dry_run=args.dry_run, limit=args.limit))


if __name__ == "__main__":
    main()
