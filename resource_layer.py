"""
Q-SpecTrum Resource Layer (Layer 1/5 in Closed-Loop Architecture)

This module implements the Resource Layer for Q-SpecTrum's 5-layer closed-loop architecture:
    【原始数据库→数据库管理→向量数据库→数据库API接口】(资源层)
    [Raw Database → DB Management → Vector Database → DB API Interface] (Resource Layer)

The Resource Layer serves as the foundational data ingestion, storage, and retrieval system:
    - Collects ALL types of user data: text, files, images, video, code, tools, skills, documents
    - Stores resources in SQLite with metadata and project associations
    - Builds TF-IDF vector indexes for semantic search (Chinese + English aware)
    - Provides a Python API for other layers to query and reingest execution results
    - Critical for closing the loop: execution results flow back into the resource layer

Architecture Position:
    - Input: Raw data from users (files, text, code, images, etc.)
    - Processing: Ingestion → Storage → Vector Indexing → Semantic Search
    - Output: Structured resource queries to higher layers + Loop-closing reingest
    - Loop-back: Execution results from other layers are reingested to improve future context

Key Features:
    - Pure Python TF-IDF (no external ML libraries)
    - Chinese text tokenization with character + bigram support
    - Incremental vector indexing (avoid full rebuilds)
    - Project-scoped resource organization
    - Graceful fallback for mounted filesystem issues
    - Full production logging and error handling

Example Usage:
    resource_layer = ResourceAPI(db_path="./qspectrum.db")

    # Ingest diverse data types
    rid = resource_layer.collect(
        type="code",
        content="def hello(): print('world')",
        title="Hello Function",
        tags=["python", "demo"],
        project_id="proj_001"
    )

    # Semantic search across all resources
    results = resource_layer.search(
        query="print hello world",
        project_filter="proj_001",
        top_k=5
    )

    # Close the loop: feed execution results back
    resource_layer.reingest_results([
        {
            "type": "execution_result",
            "content": "Function executed successfully",
            "source": "executor_layer",
            "parent_resource_id": rid
        }
    ])

    # Build context for a project
    context = resource_layer.get_project_context("proj_001", top_k=20)
"""

import hashlib
import json
import logging
import math
import sqlite3
import tempfile
import time
from collections import Counter, defaultdict
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("q-spectrum.resource-layer")


class ResourceDB:
    """
    SQLite-based resource database with project scoping and metadata.

    Handles all persistent storage for resources with graceful fallback
    to system temp directory if mounted filesystem has I/O issues.

    Database Schema:
        resources:
            - id TEXT PRIMARY KEY
            - type TEXT (text, file, image, video, code, tool, skill, document, data, config, api)
            - title TEXT
            - content TEXT
            - tags TEXT (JSON array)
            - metadata TEXT (JSON dict)
            - project_id TEXT
            - created_at REAL (unix timestamp)
            - updated_at REAL (unix timestamp)
            - source TEXT (where it came from: user, executor, tool, etc.)

        resource_vectors:
            - resource_id TEXT PRIMARY KEY
            - tfidf_vector BLOB (serialized vector as JSON)
            - terms TEXT (JSON array of (term, weight) tuples)
            - magnitude REAL (vector L2 norm)
    """

    RESOURCE_TYPES = {"text", "file", "image", "video", "code", "tool", "skill", "document", "data", "config", "api", "execution_result"}

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize the Resource Database.

        Args:
            db_path: Path to SQLite database. If None or disk I/O fails, uses system temp directory
        """
        self.db_path = Path(db_path) if db_path else Path.cwd() / "qspectrum.db"

        # Attempt to create database at specified path, fallback to /tmp on I/O error
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._verify_db_writable()
            logger.info(f"ResourceDB initialized at {self.db_path}")
        except Exception:
            fallback_path = Path(tempfile.gettempdir()) / "qspectrum_data"
            fallback_path.mkdir(parents=True, exist_ok=True)
            self.db_path = fallback_path / "qspectrum.db"
            logger.info(f"ResourceDB using portable path: {self.db_path}")

        self._init_schema()

    def _verify_db_writable(self):
        """Test database writability with actual table creation."""
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False, timeout=10)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("CREATE TABLE IF NOT EXISTS _write_test (x INTEGER)")
        conn.execute("INSERT INTO _write_test VALUES (1)")
        conn.commit()
        conn.execute("DROP TABLE IF EXISTS _write_test")
        conn.commit()
        conn.close()

    def _init_schema(self):
        """Initialize database schema if needed."""
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS resources (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    title TEXT,
                    content TEXT NOT NULL,
                    tags TEXT,
                    metadata TEXT,
                    project_id TEXT,
                    created_at REAL,
                    updated_at REAL,
                    source TEXT
                )
            """)

            conn.execute("""
                CREATE TABLE IF NOT EXISTS resource_vectors (
                    resource_id TEXT PRIMARY KEY,
                    tfidf_vector TEXT,
                    terms TEXT,
                    magnitude REAL,
                    FOREIGN KEY(resource_id) REFERENCES resources(id) ON DELETE CASCADE
                )
            """)

            # Indexes for common queries
            conn.execute("CREATE INDEX IF NOT EXISTS idx_type ON resources(type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_project ON resources(project_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_created ON resources(created_at)")

            conn.commit()

    @contextmanager
    def _get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False, timeout=10)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

    def ingest(
        self,
        type_: str,
        content: str,
        title: Optional[str] = None,
        tags: Optional[List[str]] = None,
        project_id: Optional[str] = None,
        source: str = "user",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Ingest a single resource into the database.

        Args:
            type_: Resource type (must be in RESOURCE_TYPES)
            content: Resource content/text
            title: Optional title
            tags: Optional list of tags
            project_id: Optional project ID for scoping
            source: Where the resource came from (default: "user")
            metadata: Optional metadata dictionary

        Returns:
            Resource ID

        Raises:
            ValueError: If type_ not in RESOURCE_TYPES
        """
        if type_ not in self.RESOURCE_TYPES:
            raise ValueError(f"Invalid type '{type_}'. Must be one of {self.RESOURCE_TYPES}")

        resource_id = self._generate_id(content, type_)
        now = time.time()

        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO resources
                (id, type, title, content, tags, metadata, project_id, created_at, updated_at, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    resource_id,
                    type_,
                    title or f"Untitled {type_}",
                    content,
                    json.dumps(tags or []),
                    json.dumps(metadata or {}),
                    project_id,
                    now,
                    now,
                    source,
                ),
            )
            conn.commit()

        logger.debug(f"Ingested resource {resource_id} (type={type_}, project={project_id})")
        return resource_id

    def bulk_ingest(self, items: List[Dict[str, Any]]) -> List[str]:
        """
        Ingest multiple resources efficiently.

        Args:
            items: List of dicts with keys: type, content, title, tags, project_id, source, metadata

        Returns:
            List of resource IDs
        """
        resource_ids = []
        for item in items:
            rid = self.ingest(
                type_=item["type"],
                content=item["content"],
                title=item.get("title"),
                tags=item.get("tags"),
                project_id=item.get("project_id"),
                source=item.get("source", "user"),
                metadata=item.get("metadata"),
            )
            resource_ids.append(rid)
        return resource_ids

    def get(self, resource_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single resource by ID.

        Args:
            resource_id: Resource ID

        Returns:
            Resource dict or None if not found
        """
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM resources WHERE id = ?",
                (resource_id,)
            ).fetchone()

        if not row:
            return None

        return self._row_to_dict(row)

    def list(
        self,
        type_: Optional[str] = None,
        project_id: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        List resources with optional filtering.

        Args:
            type_: Filter by resource type
            project_id: Filter by project ID
            limit: Max results
            offset: Pagination offset

        Returns:
            List of resource dicts
        """
        query = "SELECT * FROM resources WHERE 1=1"
        params = []

        if type_:
            query += " AND type = ?"
            params.append(type_)
        if project_id:
            query += " AND project_id = ?"
            params.append(project_id)

        query += " ORDER BY updated_at DESC LIMIT ? OFFSET ?"
        params.extend([limit, offset])

        with self._get_connection() as conn:
            rows = conn.execute(query, params).fetchall()

        return [self._row_to_dict(row) for row in rows]

    def update(self, resource_id: str, **kwargs) -> bool:
        """
        Update a resource's fields.

        Args:
            resource_id: Resource ID
            **kwargs: Fields to update (type, title, content, tags, metadata, etc.)

        Returns:
            True if updated, False if not found
        """
        allowed_fields = {"type", "title", "content", "tags", "metadata", "source"}
        update_fields = {k: v for k, v in kwargs.items() if k in allowed_fields}

        if not update_fields:
            return False

        update_fields["updated_at"] = time.time()

        set_clause = ", ".join(f"{k} = ?" for k in update_fields.keys())
        query = f"UPDATE resources SET {set_clause} WHERE id = ?"

        with self._get_connection() as conn:
            cursor = conn.execute(query, list(update_fields.values()) + [resource_id])
            conn.commit()
            return cursor.rowcount > 0

    def delete(self, resource_id: str) -> bool:
        """
        Delete a resource (cascades to vectors).

        Args:
            resource_id: Resource ID

        Returns:
            True if deleted, False if not found
        """
        with self._get_connection() as conn:
            cursor = conn.execute("DELETE FROM resources WHERE id = ?", (resource_id,))
            conn.commit()
            return cursor.rowcount > 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Get database statistics.

        Returns:
            Dict with counts: by_type, by_project, total, indexed
        """
        with self._get_connection() as conn:
            total = conn.execute("SELECT COUNT(*) FROM resources").fetchone()[0]
            indexed = conn.execute("SELECT COUNT(*) FROM resource_vectors").fetchone()[0]

            by_type = {}
            for row in conn.execute("SELECT type, COUNT(*) as cnt FROM resources GROUP BY type"):
                by_type[row[0]] = row[1]

            by_project = {}
            for row in conn.execute(
                "SELECT project_id, COUNT(*) as cnt FROM resources WHERE project_id IS NOT NULL GROUP BY project_id"
            ):
                by_project[row[0]] = row[1]

        return {
            "total": total,
            "indexed": indexed,
            "by_type": by_type,
            "by_project": by_project,
        }

    def _generate_id(self, content: str, type_: str) -> str:
        """Generate a deterministic resource ID from content and type."""
        hash_input = f"{type_}:{content[:1000]}".encode()
        hash_obj = hashlib.sha256(hash_input)
        return f"res_{hash_obj.hexdigest()[:16]}"

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
        """Convert database row to dictionary."""
        return {
            "id": row["id"],
            "type": row["type"],
            "title": row["title"],
            "content": row["content"],
            "tags": json.loads(row["tags"] or "[]"),
            "metadata": json.loads(row["metadata"] or "{}"),
            "project_id": row["project_id"],
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
            "source": row["source"],
        }


class VectorIndex:
    """
    TF-IDF based vector index for semantic search.

    Pure Python implementation with support for Chinese text tokenization
    (character + bigram) and English (whitespace + lowercased).

    No external ML library dependencies - uses only stdlib math.

    Terminology:
        - Document: One resource's content
        - Term: A token from Chinese text (character or bigram) or English word
        - TF: Term frequency (count in document / total terms)
        - IDF: Inverse document frequency (log(total docs / docs containing term))
        - TF-IDF Vector: [term_id] -> tf*idf score
    """

    def __init__(self, db: ResourceDB):
        """
        Initialize vector index.

        Args:
            db: ResourceDB instance for accessing content
        """
        self.db = db
        self.idf_dict = {}  # term -> idf score
        self.term_to_id = {}  # term -> unique term id
        self.id_to_term = {}  # term id -> term
        self.doc_vectors = {}  # resource_id -> {term_id: tfidf_score}
        self.next_term_id = 0

    def build_index(self):
        """
        Build TF-IDF index from all resources in database.
        This is an expensive operation - use incrementally when possible.
        """
        logger.info("Building complete vector index...")

        # Reset state
        self.idf_dict = {}
        self.term_to_id = {}
        self.id_to_term = {}
        self.doc_vectors = {}
        self.next_term_id = 0

        # Load all resources
        with self.db._get_connection() as conn:
            all_resources = conn.execute("SELECT id, content FROM resources").fetchall()

        if not all_resources:
            logger.info("No resources to index")
            return

        # First pass: tokenize and count document frequencies
        doc_terms = {}  # resource_id -> set of unique terms
        all_terms = set()

        for resource_id, content in all_resources:
            terms = set(self._tokenize(content))
            doc_terms[resource_id] = terms
            all_terms.update(terms)

        # Calculate IDF for each term
        total_docs = len(all_resources)
        for term in all_terms:
            doc_count = sum(1 for terms_set in doc_terms.values() if term in terms_set)
            idf = math.log(total_docs / max(1, doc_count))
            self.idf_dict[term] = idf
            self.term_to_id[term] = self.next_term_id
            self.id_to_term[self.next_term_id] = term
            self.next_term_id += 1

        # Second pass: compute TF-IDF vectors
        for resource_id, content in all_resources:
            self._build_vector_for_content(resource_id, content)

        logger.info(f"Index built: {total_docs} docs, {len(all_terms)} unique terms")

    def index_resource(self, resource_id: str, content: str):
        """
        Add or update a single resource in the index.
        Updates IDF dictionary incrementally.

        Args:
            resource_id: Resource ID
            content: Resource content
        """
        # Update term vocabulary and IDF
        tokens = self._tokenize(content)
        unique_tokens = set(tokens)

        with self.db._get_connection() as conn:
            total_docs = conn.execute("SELECT COUNT(*) FROM resources").fetchone()[0]

        for term in unique_tokens:
            if term not in self.term_to_id:
                self.term_to_id[term] = self.next_term_id
                self.id_to_term[self.next_term_id] = term
                self.next_term_id += 1

            # Update IDF (simplified incremental update)
            if term not in self.idf_dict:
                self.idf_dict[term] = math.log(total_docs + 1)

        self._build_vector_for_content(resource_id, content)
        logger.debug(f"Indexed resource {resource_id}")

    def search(
        self,
        query: str,
        top_k: int = 10,
        type_filter: Optional[str] = None,
        project_filter: Optional[str] = None,
    ) -> List[Tuple[str, float, str]]:
        """
        Semantic search across indexed resources.

        Args:
            query: Search query
            top_k: Number of top results to return
            type_filter: Filter by resource type
            project_filter: Filter by project ID

        Returns:
            List of (resource_id, score, snippet) tuples, highest score first
        """
        if not self.doc_vectors:
            return []

        # Tokenize and vectorize query
        query_tokens = self._tokenize(query)
        query_counter = Counter(query_tokens)
        query_vec = {}

        for term, count in query_counter.items():
            if term in self.term_to_id:
                tf = count / len(query_tokens) if query_tokens else 0
                idf = self.idf_dict.get(term, 0)
                term_id = self.term_to_id[term]
                query_vec[term_id] = tf * idf

        if not query_vec:
            return []

        # Compute query vector magnitude
        query_magnitude = math.sqrt(sum(v ** 2 for v in query_vec.values()))
        if query_magnitude == 0:
            return []

        # Score all documents
        scores = {}

        for resource_id, doc_vec in self.doc_vectors.items():
            # Filter by type and project if specified
            if type_filter or project_filter:
                resource = self.db.get(resource_id)
                if not resource:
                    continue
                if type_filter and resource["type"] != type_filter:
                    continue
                if project_filter and resource["project_id"] != project_filter:
                    continue

            # Cosine similarity: (query · doc) / (|query| * |doc|)
            dot_product = sum(
                query_vec.get(term_id, 0) * doc_vec.get(term_id, 0)
                for term_id in set(query_vec.keys()) | set(doc_vec.keys())
            )

            doc_magnitude = math.sqrt(sum(v ** 2 for v in doc_vec.values()))
            if doc_magnitude == 0:
                continue

            score = dot_product / (query_magnitude * doc_magnitude)
            if score > 0:
                scores[resource_id] = score

        # Sort by score and get top_k
        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

        # Build results with snippets
        results = []
        for resource_id, score in ranked:
            resource = self.db.get(resource_id)
            if resource:
                snippet = self._extract_snippet(resource["content"], query, length=150)
                results.append((resource_id, score, snippet))

        return results

    def get_similar(self, resource_id: str, top_k: int = 5) -> List[Tuple[str, float]]:
        """
        Find similar resources using cosine similarity of their TF-IDF vectors.

        Args:
            resource_id: Reference resource ID
            top_k: Number of similar resources to return

        Returns:
            List of (similar_resource_id, similarity_score) tuples
        """
        if resource_id not in self.doc_vectors:
            return []

        ref_vec = self.doc_vectors[resource_id]
        ref_magnitude = math.sqrt(sum(v ** 2 for v in ref_vec.values()))

        if ref_magnitude == 0:
            return []

        scores = {}

        for other_id, other_vec in self.doc_vectors.items():
            if other_id == resource_id:
                continue

            dot_product = sum(
                ref_vec.get(term_id, 0) * other_vec.get(term_id, 0)
                for term_id in set(ref_vec.keys()) | set(other_vec.keys())
            )

            other_magnitude = math.sqrt(sum(v ** 2 for v in other_vec.values()))
            if other_magnitude == 0:
                continue

            similarity = dot_product / (ref_magnitude * other_magnitude)
            if similarity > 0:
                scores[other_id] = similarity

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_k]
        return ranked

    def _tokenize(self, text: str) -> List[str]:
        """
        Tokenize text with Chinese character + bigram support.
        English text is tokenized by whitespace and lowercased.

        Args:
            text: Text to tokenize

        Returns:
            List of tokens
        """
        text = text.lower()
        tokens = []

        i = 0
        while i < len(text):
            char = text[i]

            # Chinese character (rough heuristic: CJK Unified Ideographs range)
            if ord(char) >= 0x4E00 and ord(char) <= 0x9FFF:
                tokens.append(char)

                # Add bigram (current + next)
                if i + 1 < len(text) and ord(text[i + 1]) >= 0x4E00 and ord(text[i + 1]) <= 0x9FFF:
                    tokens.append(char + text[i + 1])

                i += 1
            else:
                # English/alphanumeric: collect word
                if char.isalnum():
                    word = ""
                    while i < len(text) and text[i].isalnum():
                        word += text[i]
                        i += 1
                    if word:
                        tokens.append(word)
                else:
                    i += 1

        return tokens

    def _build_vector_for_content(self, resource_id: str, content: str):
        """
        Build and store TF-IDF vector for a resource.

        Args:
            resource_id: Resource ID
            content: Resource content
        """
        tokens = self._tokenize(content)
        if not tokens:
            self.doc_vectors[resource_id] = {}
            return

        term_counter = Counter(tokens)
        vec = {}

        for term, count in term_counter.items():
            tf = count / len(tokens)
            idf = self.idf_dict.get(term, 0)
            term_id = self.term_to_id.get(term)

            if term_id is not None:
                vec[term_id] = tf * idf

        self.doc_vectors[resource_id] = vec

    def _extract_snippet(self, content: str, query: str, length: int = 150) -> str:
        """
        Extract a snippet around the first query match.

        Args:
            content: Full content
            query: Search query
            length: Desired snippet length

        Returns:
            Snippet string
        """
        query_words = set(self._tokenize(query))
        content_lower = content.lower()

        # Find first occurrence of any query term
        earliest_pos = len(content)
        for word in query_words:
            pos = content_lower.find(word.lower())
            if pos != -1 and pos < earliest_pos:
                earliest_pos = pos

        if earliest_pos == len(content):
            # No match found, return start of content
            return content[:length].strip() + ("..." if len(content) > length else "")

        # Extract snippet centered on match
        start = max(0, earliest_pos - length // 3)
        end = min(len(content), earliest_pos + 2 * length // 3)

        snippet = content[start:end].strip()
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."

        return snippet


class ResourceAPI:
    """
    High-level Python API for the Resource Layer.

    Combines ResourceDB and VectorIndex to provide:
        - Data collection and ingestion
        - Semantic search
        - Project context building
        - Loop-closing through result reingestion
        - Status and statistics

    This is the primary interface used by higher layers (Reasoning, Execution, Feedback).
    """

    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize Resource API.

        Args:
            db_path: Path to SQLite database (None for default)
        """
        self.db = ResourceDB(db_path)
        self.index = VectorIndex(self.db)
        self.index.build_index()
        logger.info("ResourceAPI initialized")

    def collect(
        self,
        type_: str,
        content: str,
        title: Optional[str] = None,
        tags: Optional[List[str]] = None,
        project_id: Optional[str] = None,
        source: str = "user",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Collect and ingest a resource.

        Args:
            type_: Resource type
            content: Resource content
            title: Optional title
            tags: Optional tags
            project_id: Optional project ID
            source: Data source (default: "user")
            metadata: Optional metadata

        Returns:
            Resource ID
        """
        resource_id = self.db.ingest(
            type_=type_,
            content=content,
            title=title,
            tags=tags,
            project_id=project_id,
            source=source,
            metadata=metadata,
        )

        # Add to vector index
        self.index.index_resource(resource_id, content)

        return resource_id

    def search(
        self,
        query: str,
        top_k: int = 10,
        type_filter: Optional[str] = None,
        project_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Semantic search across all resources.

        Args:
            query: Search query
            top_k: Number of results
            type_filter: Filter by type
            project_filter: Filter by project

        Returns:
            List of result dicts: {resource_id, score, snippet, type, title, tags}
        """
        results = self.index.search(
            query,
            top_k=top_k,
            type_filter=type_filter,
            project_filter=project_filter,
        )

        detailed_results = []
        for resource_id, score, snippet in results:
            resource = self.db.get(resource_id)
            if resource:
                detailed_results.append({
                    "resource_id": resource_id,
                    "score": score,
                    "snippet": snippet,
                    "type": resource["type"],
                    "title": resource["title"],
                    "tags": resource["tags"],
                    "project_id": resource["project_id"],
                })

        return detailed_results

    def reingest_results(self, results: List[Dict[str, Any]]) -> List[str]:
        """
        CRITICAL LOOP-CLOSING METHOD: Reingest execution results back into resource layer.

        This method takes results from execution, reasoning, or feedback layers
        and stores them as new resources, making them available for future context.

        This implements the critical feedback loop:
            User Request → Reasoning → Execution → [Results] → Reingest → Future Context

        Args:
            results: List of result dicts with keys:
                - type: result type (execution_result, feedback, reasoning, etc.)
                - content: result content/data
                - source: where result came from (executor_layer, feedback_layer, etc.)
                - parent_resource_id: optional reference to original resource
                - project_id: optional project association
                - metadata: optional metadata

        Returns:
            List of new resource IDs
        """
        resource_ids = []

        for result in results:
            # Validate result structure
            if "content" not in result or "type" not in result:
                logger.warning("Skipping invalid result: missing content or type")
                continue

            # Create resource from result
            rid = self.collect(
                type_=result.get("type", "execution_result"),
                content=result["content"],
                title=result.get("title", f"Result from {result.get('source', 'unknown')}"),
                tags=result.get("tags", []),
                project_id=result.get("project_id"),
                source=result.get("source", "executor"),
                metadata={
                    "parent_resource_id": result.get("parent_resource_id"),
                    **result.get("metadata", {}),
                },
            )
            resource_ids.append(rid)

        logger.info(f"Reingested {len(resource_ids)} execution results for loop closure")
        return resource_ids

    def aggregate_by_project(self, project_id: str) -> Dict[str, Any]:
        """
        Get aggregated statistics and top resources for a project.

        Args:
            project_id: Project ID

        Returns:
            Dict with stats, resources by type, etc.
        """
        resources = self.db.list(project_id=project_id, limit=1000)

        by_type = defaultdict(list)
        for res in resources:
            by_type[res["type"]].append(res)

        return {
            "project_id": project_id,
            "total_resources": len(resources),
            "by_type": dict(by_type),
            "resource_count_by_type": {k: len(v) for k, v in by_type.items()},
        }

    def get_project_context(self, project_id: str, top_k: int = 20) -> str:
        """
        Build a context string from the most relevant resources in a project.

        This is used by higher layers to provide grounding for reasoning and execution.

        Args:
            project_id: Project ID
            top_k: Number of top resources to include

        Returns:
            Formatted context string
        """
        resources = self.db.list(project_id=project_id, limit=top_k)

        if not resources:
            return f"No resources found for project {project_id}"

        context_lines = [f"=== Project Context: {project_id} ===\n"]

        by_type = defaultdict(list)
        for res in resources:
            by_type[res["type"]].append(res)

        for type_, type_resources in sorted(by_type.items()):
            context_lines.append(f"\n## {type_.upper()} ({len(type_resources)})")

            for res in type_resources[:5]:  # Limit to 5 per type
                context_lines.append(f"\n### {res['title']} (ID: {res['id']})")
                if res["tags"]:
                    context_lines.append(f"Tags: {', '.join(res['tags'])}")

                # Truncate long content
                content = res["content"]
                if len(content) > 500:
                    content = content[:500] + "..."
                context_lines.append(f"\n{content}")

        return "\n".join(context_lines)

    def status(self) -> Dict[str, Any]:
        """
        Get complete Resource Layer status.

        Returns:
            Status dict with DB stats, index stats, health info
        """
        db_stats = self.db.get_stats()

        return {
            "layer": "resource",
            "status": "active",
            "database": {
                "path": str(self.db.db_path),
                "total_resources": db_stats["total"],
                "indexed_resources": db_stats["indexed"],
                "by_type": db_stats["by_type"],
                "by_project": db_stats["by_project"],
            },
            "index": {
                "total_terms": len(self.index.term_to_id),
                "total_documents": len(self.index.doc_vectors),
                "index_built": len(self.index.idf_dict) > 0,
            },
            "capabilities": [
                "collect",
                "search",
                "reingest_results",
                "get_project_context",
                "aggregate_by_project",
            ],
        }


# Module-level convenience functions
def create_resource_api(db_path: Optional[str] = None) -> ResourceAPI:
    """Create and return a ResourceAPI instance."""
    return ResourceAPI(db_path)


if __name__ == "__main__":
    # Configure logging for testing
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Example usage
    print("Q-SpecTrum Resource Layer - Example Usage\n")

    import os
    import tempfile
    api = ResourceAPI(os.path.join(tempfile.gettempdir(), "qspectrum_test.db"))

    # Collect diverse resources
    print("1. Collecting resources...")
    rid1 = api.collect(
        type_="code",
        content="def hello_world(): print('Hello, World!')",
        title="Hello World Function",
        tags=["python", "demo"],
        project_id="demo_project",
    )
    print(f"   Collected code: {rid1}")

    rid2 = api.collect(
        type_="text",
        content="This is a test document about Python programming.",
        title="Python Guide",
        tags=["python", "tutorial"],
        project_id="demo_project",
    )
    print(f"   Collected text: {rid2}")

    rid3 = api.collect(
        type_="data",
        content="user_data = {name: 'Alice', age: 30, skills: ['Python', 'ML']}",
        title="User Data",
        tags=["data", "user"],
        project_id="demo_project",
    )
    print(f"   Collected data: {rid3}")

    # Search
    print("\n2. Searching resources...")
    results = api.search("hello python", project_filter="demo_project", top_k=5)
    for i, result in enumerate(results, 1):
        print(f"   {i}. [{result['score']:.3f}] {result['title']} ({result['type']})")
        print(f"      {result['snippet']}")

    # Reingest results (loop closure)
    print("\n3. Reingesting execution results...")
    loop_results = [
        {
            "type": "execution_result",
            "content": "hello_world() executed successfully, output: Hello, World!",
            "source": "executor_layer",
            "parent_resource_id": rid1,
            "project_id": "demo_project",
        }
    ]
    new_rids = api.reingest_results(loop_results)
    print(f"   Reingested {len(new_rids)} results: {new_rids}")

    # Status
    print("\n4. Resource Layer Status:")
    status = api.status()
    print(f"   Total resources: {status['database']['total_resources']}")
    print(f"   Indexed: {status['database']['indexed_resources']}")
    print(f"   Unique terms: {status['index']['total_terms']}")

    # Project context
    print("\n5. Project Context:")
    context = api.get_project_context("demo_project", top_k=10)
    print(context[:500] + "..." if len(context) > 500 else context)
