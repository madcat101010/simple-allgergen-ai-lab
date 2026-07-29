"""
Unit tests for SecretManager Integration (src/secret_manager.py)
"""

import os
import unittest
from src.secret_manager import SecretManager, secret_manager


class TestSecretManager(unittest.TestCase):
    def test_secret_manager_fallback(self):
        sm = SecretManager()

        os.environ["GEMINI_API_KEY"] = "test_key_environment_fallback"
        key = sm.get_secret("gemini-api-key")
        self.assertEqual(key, "test_key_environment_fallback")

    def test_global_secret_manager_instance(self):
        self.assertIsNotNone(secret_manager)


if __name__ == "__main__":
    unittest.main()
