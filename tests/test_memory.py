"""
Unit tests for Memory, History Compaction, Dedicated SQLite Database & Vector Store (src/memory.py & src/db.py)
"""

import os
import time
import unittest
from src.db import DatabaseSessionStore
from src.memory import SessionMemoryManager


class TestSessionMemoryManager(unittest.TestCase):
    def setUp(self):
        self.test_db_path = os.path.join(os.path.dirname(__file__), "test_sessions.db")
        if os.path.exists(self.test_db_path):
            try:
                os.remove(self.test_db_path)
            except Exception:
                pass

        self.db = DatabaseSessionStore(db_path=self.test_db_path)
        self.memory = SessionMemoryManager(db=self.db, max_turns=4)
        self.test_session_id = "test_unit_session"

    def tearDown(self):
        if os.path.exists(self.test_db_path):
            try:
                os.remove(self.test_db_path)
            except Exception:
                pass

    def test_load_and_save_session_sqlite(self):
        session = self.memory.load_session(self.test_session_id)
        self.assertEqual(session["session_id"], self.test_session_id)

        session["user_allergies"] = ["Gluten"]
        self.memory.save_session_sync(self.test_session_id, session)

        reloaded = self.memory.load_session(self.test_session_id)
        self.assertEqual(reloaded["user_allergies"], ["Gluten"])

    def test_history_compaction_mechanism(self):
        # Create a session with 10 turns (exceeding max_turns=4)
        session = self.memory.load_session(self.test_session_id)
        for i in range(10):
            session["history"].append({"role": "user", "content": f"User prompt {i}"})
            session["history"].append({"role": "assistant", "content": f"Assistant response {i}"})

        compacted = self.memory.compact_history(session)

        # Recent history should be capped at max_turns (4)
        self.assertEqual(len(compacted["history"]), 4)

        # Executive summary of older turns should be populated
        self.assertIn("Prior Context", compacted["compacted_summary"])
        self.assertIn("User prompt 0", compacted["compacted_summary"])

    def test_vector_store_semantic_search(self):
        # Add turns into memory and test vector store retrieval
        self.memory.append_turn_and_compact(
            session_id=self.test_session_id,
            user_prompt="Does the Big Mac contain Gluten or Dairy?",
            assistant_response="UNSAFE: Big Mac contains Wheat Gluten and Dairy cheese.",
            allergies=["Gluten", "Dairy"]
        )
        time.sleep(0.1)  # Allow background thread worker to complete write

        # Perform vector similarity search
        results = self.memory.search_semantic_memory(self.test_session_id, query="Big Mac gluten risk", top_k=2)
        self.assertGreater(len(results), 0)
        self.assertIn("Big Mac", results[0]["snippet"])

    def test_async_background_memory_save(self):
        updated = self.memory.append_turn_and_compact(
            session_id=self.test_session_id,
            user_prompt="Can I eat Big Mac?",
            assistant_response="UNSAFE: Contains Gluten.",
            allergies=["Gluten"]
        )

        self.assertGreater(len(updated["history"]), 0)
        time.sleep(0.1)  # Allow background thread worker to complete write
        
        reloaded = self.memory.load_session(self.test_session_id)
        self.assertGreater(len(reloaded["history"]), 0)

    def test_database_stats(self):
        stats = self.db.get_stats()
        self.assertIn("SQLite Database", stats["database_type"])
        self.assertEqual(stats["db_path"], self.test_db_path)


if __name__ == "__main__":
    unittest.main()
