"""
Unit tests for Memory, History Compaction & Async Background Storage (src/memory.py)
"""

import os
import time
import unittest
from src.memory import SessionMemoryManager, SESSIONS_DIR


class TestSessionMemoryManager(unittest.TestCase):
    def setUp(self):
        self.memory = SessionMemoryManager(max_turns=4)
        self.test_session_id = "test_unit_session"

    def tearDown(self):
        path = self.memory._get_session_path(self.test_session_id)
        if os.path.exists(path):
            try:
                os.remove(path)
            except Exception:
                pass

    def test_load_and_save_session(self):
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

    def test_async_background_memory_save(self):
        updated = self.memory.append_turn_and_compact(
            session_id=self.test_session_id,
            user_prompt="Can I eat Big Mac?",
            assistant_response="UNSAFE: Contains Gluten.",
            allergies=["Gluten"]
        )

        self.assertGreater(len(updated["history"]), 0)
        time.sleep(0.1)  # Allow background thread worker to complete write
        self.assertTrue(os.path.exists(self.memory._get_session_path(self.test_session_id)))


if __name__ == "__main__":
    unittest.main()
