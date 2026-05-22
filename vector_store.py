#!/usr/bin/env python3
"""
Vector Store — ChromaDB-backed persistent semantic search.
Seeds from BRAIN-KB/ markdown files, provides engine-level search API.
"""
import re
from pathlib import Path

ROOT = Path(__file__).parent.resolve()

class VectorStore:
    """ChromaDB persistent vector store for BRAIN-KB content."""

    def __init__(self, persist_dir: str = None):
        self._chroma = None
        self._collection = None
        persist_dir = persist_dir or str(ROOT / "BRAIN-KB" / ".chroma_db")
        self._persist_dir = persist_dir
        self._ensure_chromadb()
        self._seed_from_brain_kb()

    def _ensure_chromadb(self):
        try:
            import chromadb
            self._client = chromadb.PersistentClient(path=self._persist_dir)
            self._collection = self._client.get_or_create_collection(
                name="brain_kb",
                metadata={"hnsw:space": "cosine"}
            )
        except ImportError:
            raise ImportError("ChromaDB required: pip install chromadb")

    def _seed_from_brain_kb(self):
        """Seed from BRAIN-KB/ markdown INDEX files if collection is empty."""
        if self._collection.count() > 0:
            return
        kb_root = ROOT / "BRAIN-KB"
        sections = {
            "knowledge": self._parse_index_md(kb_root / "knowledge" / "INDEX.md"),
            "decisions": self._parse_index_md(kb_root / "decisions" / "INDEX.md"),
            "patterns": self._parse_index_md(kb_root / "patterns" / "INDEX.md"),
            "limitations": self._parse_index_md(kb_root / "limitations" / "INDEX.md"),
        }
        docs, ids, metadatas = [], [], []
        for section, entries in sections.items():
            for i, entry in enumerate(entries):
                docs.append(entry["text"])
                ids.append(f"{section}_{i}")
                metadatas.append({
                    "section": section,
                    "title": entry.get("title", ""),
                    "source": entry.get("source", ""),
                })
        if docs:
            self._collection.add(documents=docs, ids=ids, metadatas=metadatas)

    def _parse_index_md(self, md_path: Path) -> list:
        """Parse INDEX.md structure into text entries."""
        if not md_path.exists():
            return []
        text = md_path.read_text(encoding="utf-8", errors="ignore")
        entries = []
        # Split by ## headings (each entry)
        blocks = re.split(r"\n## ", text)
        for block in blocks:
            lines = block.strip().split("\n")
            title = lines[0].strip("# ")
            if not title or title.startswith("BRAIN") or title.startswith("Structure"):
                continue
            body_lines = [l for l in lines[1:] if not l.startswith("|") and not l.startswith("|---")]
            body = "\n".join(body_lines).strip()
            entry_text = f"{title}: {body}" if body else title
            source = ""
            for line in lines:
                m = re.search(r"\*\*來源\*\*:\s*(.+)", line)
                if m:
                    source = m.group(1).strip()
            entries.append({"title": title, "text": entry_text, "source": source})
        return entries

    def search(self, query: str, top_k: int = 5) -> list:
        """Semantic search over BRAIN-KB content."""
        if not self._collection or self._collection.count() == 0:
            return []
        results = self._collection.query(query_texts=[query], n_results=min(top_k, self._collection.count()))
        items = []
        for i in range(len(results["ids"][0])):
            items.append({
                "id": results["ids"][0][i],
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i] if results.get("distances") else None,
            })
        return items

    def add_entry(self, entry_id: str, text: str, metadata: dict = None):
        """Add a single entry to the vector store."""
        self._collection.add(
            documents=[text],
            ids=[entry_id],
            metadatas=[metadata or {}]
        )

    def count(self) -> int:
        return self._collection.count() if self._collection else 0

    def stats(self) -> dict:
        if not self._collection:
            return {"error": "collection not initialized"}
        return {
            "total_entries": self._collection.count(),
            "persist_dir": self._persist_dir,
            "collection": "brain_kb",
        }
