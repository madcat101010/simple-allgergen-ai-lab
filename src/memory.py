"""
McDonald's Allergen Agent Memory & Session Management
------------------------------------------------------
Provides persistent session state storage, automatic history compaction
(context summarization), vector memory retrieval, and asynchronous background memory operations.

Persists session state and vector embeddings using a dedicated SQLite database engine
and integrated Vector Store (src/db.py) rather than local JSON files.
"""

import asyncio
import os
import time
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Any, Optional

from src.db import db_store, DatabaseSessionStore, DB_PATH

# Background thread pool executor for non-blocking async background database I/O & compaction
_EXECUTOR = ThreadPoolExecutor(max_workers=4)
SESSIONS_DIR = os.path.dirname(DB_PATH)


class SessionMemoryManager:
    """
    Manages persistent session state, vector memory retrieval, automated history compaction,
    and async background operations using a dedicated SQLite Database & Vector Store.
    """

    def __init__(self, db: Optional[DatabaseSessionStore] = None, max_turns: int = 6, max_tokens_estimate: int = 1500):
        self.db = db or db_store
        self.max_turns = max_turns
        self.max_tokens_estimate = max_tokens_estimate

    def _get_session_path(self, session_id: str) -> str:
        """Returns the dedicated database path for reference."""
        return self.db.db_path

    def load_session(self, session_id: str = "default_session") -> Dict[str, Any]:
        """
        Loads session state from the dedicated SQLite database store.

        Args:
            session_id (str): Unique session identifier. Defaults to 'default_session'.

        Returns:
            Dict[str, Any]: Session state object containing [session_id, user_allergies, history, compacted_summary, last_updated].
        """
        return self.db.load_session(session_id)

    def save_session_sync(self, session_id: str, session_data: Dict[str, Any]) -> None:
        """Saves session state synchronously into the dedicated SQLite database."""
        session_data["last_updated"] = time.strftime("%Y-%m-%d %H:%M:%S")
        try:
            self.db.save_session(session_id, session_data)
        except Exception as e:
            print(f"[!] Warning: Failed to save session state in dedicated database: {e}")

    def save_session_async(self, session_id: str, session_data: Dict[str, Any]) -> None:
        """
        Asynchronously saves session state to the dedicated database in a background thread
        to prevent latency spikes.

        Args:
            session_id (str): Unique session identifier.
            session_data (Dict[str, Any]): Session payload.
        """
        _EXECUTOR.submit(self.save_session_sync, session_id, session_data)

    def search_semantic_memory(self, session_id: str, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Queries the integrated Vector Store for relevant semantic memory context matching the prompt query.

        Args:
            session_id (str): Session identifier.
            query (str): Search prompt text.
            top_k (int): Number of top matches to retrieve.

        Returns:
            List[Dict[str, Any]]: Top semantic matches with similarity scores.
        """
        return self.db.vector_search(session_id, query, top_k=top_k)

    def compact_history(self, session_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        History Compaction Mechanism:
        When chat turn history exceeds max_turns, older turns are compacted into an
        executive summary ('compacted_summary'), retaining only recent turns for high-density context.

        Args:
            session_data (Dict[str, Any]): Current session state.

        Returns:
            Dict[str, Any]: Updated session state with compacted history.
        """
        history = session_data.get("history", [])
        if len(history) <= self.max_turns:
            return session_data

        # Slice older turns for compaction
        turns_to_compact = history[:-self.max_turns]
        recent_turns = history[-self.max_turns:]

        # Build executive summary of older turns
        summaries = []
        for turn in turns_to_compact:
            role = turn.get("role", "user").upper()
            content = turn.get("content", "")[:120]  # Truncate content for summary
            summaries.append(f"{role}: {content}")

        new_summary_text = " | ".join(summaries)
        existing_summary = session_data.get("compacted_summary", "")

        if existing_summary:
            session_data["compacted_summary"] = f"{existing_summary} || Prior Context: {new_summary_text}"
        else:
            session_data["compacted_summary"] = f"Prior Context: {new_summary_text}"

        session_data["history"] = recent_turns
        print(f"[+] History Compaction Executed: Compacted {len(turns_to_compact)} turns into executive summary.")
        return session_data

    def compact_history_async(self, session_id: str) -> None:
        """
        Asynchronously triggers history compaction in a background thread.

        Args:
            session_id (str): Unique session identifier.
        """
        def _bg_compact():
            session_data = self.load_session(session_id)
            compacted_data = self.compact_history(session_data)
            self.save_session_sync(session_id, compacted_data)

        _EXECUTOR.submit(_bg_compact)

    def append_turn_and_compact(
        self,
        session_id: str,
        user_prompt: str,
        assistant_response: str,
        allergies: List[str]
    ) -> Dict[str, Any]:
        """
        Appends user and assistant turns to session memory, triggers history compaction,
        stores vector embeddings in Vector Store, and saves updated state asynchronously to SQLite.

        Args:
            session_id (str): Session ID.
            user_prompt (str): User prompt text.
            assistant_response (str): Assistant verdict text.
            allergies (List[str]): Active user allergies.

        Returns:
            Dict[str, Any]: Updated session state.
        """
        session_data = self.load_session(session_id)
        session_data["user_allergies"] = allergies

        # Append turns
        session_data["history"].append({"role": "user", "content": user_prompt, "timestamp": time.time()})
        session_data["history"].append({"role": "assistant", "content": assistant_response, "timestamp": time.time()})

        # Compact history if turn count exceeds limit
        session_data = self.compact_history(session_data)

        # Trigger async background save to dedicated database & vector store
        self.save_session_async(session_id, session_data)
        return session_data


# Global Singleton Memory Manager
memory_manager = SessionMemoryManager()
