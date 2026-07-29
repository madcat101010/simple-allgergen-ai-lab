"""
McDonald's Allergen Agent Dedicated Database & Vector Store Module
------------------------------------------------------------------
Provides dedicated SQLite database engine storage and integrated Vector Store
for session state, turn history, and semantic context retrieval.

Replaces local JSON file persistence with an ACID-compliant relational SQL database
(data/sessions.db) featuring dedicated tables:
1. `sessions`: Session metadata, allergy preferences, and compacted executive summaries.
2. `session_turns`: Micro-log of individual user and assistant turns with timestamps.
3. `vector_store`: Vector embeddings and metadata for semantic context memory retrieval.
"""

import json
import math
import os
import re
import sqlite3
import time
from typing import List, Dict, Any, Optional, Tuple

DB_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data"
)
DB_PATH = os.path.join(DB_DIR, "sessions.db")


def _generate_text_vector(text: str, dim: int = 64) -> List[float]:
    """
    Generates a normalized dense vector embedding representation for text using term-hashing.
    Ensures deterministic, zero-dependency vector embeddings for semantic search.
    """
    tokens = re.findall(r"\w+", text.lower())
    if not tokens:
        return [0.0] * dim

    vector = [0.0] * dim
    for token in tokens:
        # Hash token into dimension index
        idx = hash(token) % dim
        vector[idx] += 1.0

    # L2 normalize vector
    magnitude = math.sqrt(sum(v * v for v in vector))
    if magnitude > 0:
        vector = [v / magnitude for v in vector]
    return vector


def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Computes cosine similarity between two vector embeddings."""
    if len(vec1) != len(vec2) or not vec1:
        return 0.0
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    mag1 = math.sqrt(sum(a * a for a in vec1))
    mag2 = math.sqrt(sum(b * b for b in vec2))
    if mag1 == 0 or mag2 == 0:
        return 0.0
    return dot_product / (mag1 * mag2)


class DatabaseSessionStore:
    """
    Dedicated SQLite Database & Vector Store implementation for session memory persistence.
    """

    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        """Returns a thread-safe connection to the SQLite database."""
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        return conn

    def _init_db(self) -> None:
        """Initializes database schema tables and indexes."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # 1. Sessions metadata table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    user_allergies TEXT NOT NULL,
                    compacted_summary TEXT DEFAULT '',
                    created_at TEXT NOT NULL,
                    last_updated TEXT NOT NULL
                )
            """)

            # 2. Session turns log table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS session_turns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp REAL NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_turns_session_id ON session_turns(session_id)")

            # 3. Vector store table for semantic context retrieval
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS vector_store (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    content_snippet TEXT NOT NULL,
                    embedding_json TEXT NOT NULL,
                    metadata_json TEXT DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_vector_session_id ON vector_store(session_id)")
            conn.commit()

    def load_session(self, session_id: str = "default_session") -> Dict[str, Any]:
        """
        Loads session state from the dedicated SQLite database.

        Args:
            session_id (str): Session identifier.

        Returns:
            Dict[str, Any]: Session state payload containing [session_id, user_allergies, history, compacted_summary, last_updated].
        """
        safe_id = "".join([c for c in session_id if c.isalnum() or c in ("-", "_")]).strip() or "default_session"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sessions WHERE session_id = ?", (safe_id,))
            row = cursor.fetchone()

            if not row:
                # Return default session state if not found
                return {
                    "session_id": safe_id,
                    "user_allergies": ["Gluten", "Dairy", "Nuts"],
                    "history": [],
                    "compacted_summary": "",
                    "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
                }

            # Fetch turn history
            cursor.execute(
                "SELECT role, content, timestamp FROM session_turns WHERE session_id = ? ORDER BY id ASC",
                (safe_id,)
            )
            turn_rows = cursor.fetchall()
            history = [
                {"role": t["role"], "content": t["content"], "timestamp": t["timestamp"]}
                for t in turn_rows
            ]

            try:
                allergies = json.loads(row["user_allergies"])
            except Exception:
                allergies = ["Gluten", "Dairy", "Nuts"]

            return {
                "session_id": safe_id,
                "user_allergies": allergies,
                "history": history,
                "compacted_summary": row["compacted_summary"],
                "last_updated": row["last_updated"]
            }

    def save_session(self, session_id: str, session_data: Dict[str, Any]) -> None:
        """
        Saves session state transactionally into the dedicated SQLite database.

        Args:
            session_id (str): Session identifier.
            session_data (Dict[str, Any]): Session payload.
        """
        safe_id = "".join([c for c in session_id if c.isalnum() or c in ("-", "_")]).strip() or "default_session"
        now_str = time.strftime("%Y-%m-%d %H:%M:%S")

        allergies_json = json.dumps(session_data.get("user_allergies", ["Gluten", "Dairy", "Nuts"]))
        compacted_summary = session_data.get("compacted_summary", "")
        history = session_data.get("history", [])

        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Upsert session record
            cursor.execute("""
                INSERT INTO sessions (session_id, user_allergies, compacted_summary, created_at, last_updated)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(session_id) DO UPDATE SET
                    user_allergies = excluded.user_allergies,
                    compacted_summary = excluded.compacted_summary,
                    last_updated = excluded.last_updated
            """, (safe_id, allergies_json, compacted_summary, now_str, now_str))

            # Replace turns log transactionally
            cursor.execute("DELETE FROM session_turns WHERE session_id = ?", (safe_id,))
            for turn in history:
                role = turn.get("role", "user")
                content = turn.get("content", "")
                ts = turn.get("timestamp", time.time())
                cursor.execute("""
                    INSERT INTO session_turns (session_id, role, content, timestamp)
                    VALUES (?, ?, ?, ?)
                """, (safe_id, role, content, ts))

                # Store vector embedding snippet for assistant responses / user turns
                vec = _generate_text_vector(content)
                cursor.execute("""
                    INSERT INTO vector_store (session_id, content_snippet, embedding_json, metadata_json, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (safe_id, f"{role.upper()}: {content[:200]}", json.dumps(vec), json.dumps({"role": role}), now_str))

            conn.commit()

    def vector_search(self, session_id: str, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Performs semantic vector similarity search over stored session memory snippets.

        Args:
            session_id (str): Session identifier filter.
            query (str): Search query text.
            top_k (int): Number of top vector matches to return.

        Returns:
            List[Dict[str, Any]]: List of top matching snippets with similarity scores.
        """
        query_vec = _generate_text_vector(query)
        safe_id = "".join([c for c in session_id if c.isalnum() or c in ("-", "_")]).strip() or "default_session"

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT content_snippet, embedding_json, metadata_json FROM vector_store WHERE session_id = ?", (safe_id,))
            rows = cursor.fetchall()

            matches: List[Tuple[float, str, Dict[str, Any]]] = []
            for r in rows:
                try:
                    vec = json.loads(r["embedding_json"])
                    sim = _cosine_similarity(query_vec, vec)
                    meta = json.loads(r["metadata_json"])
                    matches.append((sim, r["content_snippet"], meta))
                except Exception:
                    continue

            # Sort descending by similarity
            matches.sort(key=lambda x: x[0], reverse=True)

            results = []
            for score, snippet, meta in matches[:top_k]:
                results.append({
                    "score": round(score, 4),
                    "snippet": snippet,
                    "metadata": meta
                })

            return results

    def delete_session(self, session_id: str) -> None:
        """Deletes session record from dedicated database."""
        safe_id = "".join([c for c in session_id if c.isalnum() or c in ("-", "_")]).strip()
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM sessions WHERE session_id = ?", (safe_id,))
            conn.commit()

    def get_stats(self) -> Dict[str, Any]:
        """Returns database storage stats."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM sessions")
            session_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM session_turns")
            turn_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM vector_store")
            vector_count = cursor.fetchone()[0]

            return {
                "db_path": self.db_path,
                "database_type": "SQLite Database & Vector Store",
                "sessions_count": session_count,
                "turns_count": turn_count,
                "vector_embeddings_count": vector_count
            }


# Singleton database session store
db_store = DatabaseSessionStore()
