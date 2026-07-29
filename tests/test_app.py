"""
Unit tests for McDonald's Allergen Agent FastAPI App (src/app.py)
Supports conditional skipping if fastapi/httpx are not in current python path.
"""

import unittest

try:
    from fastapi.testclient import TestClient
    from src.app import app
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False


@unittest.skipUnless(HAS_FASTAPI, "fastapi package not installed in current Python environment")
class TestFastAPIApp(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_health_check(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "ok")

    def test_get_menu(self):
        res = self.client.get("/api/menu")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertGreaterEqual(data["count"], 20)

    def test_chat_endpoint_safe_item(self):
        payload = {"prompt": "Can I drink Coca-Cola?", "allergies": ["Gluten"]}
        res = self.client.post("/api/chat", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "SAFE")
        self.assertIn("✅ SAFE", data["safety_badge"])
        self.assertIn("trace", data)

    def test_chat_endpoint_unsafe_item(self):
        payload = {"prompt": "Can I eat a Big Mac?", "allergies": ["Gluten"]}
        res = self.client.post("/api/chat", json=payload)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "UNSAFE")
        self.assertIn("❌ UNSAFE", data["safety_badge"])

    def test_chat_empty_prompt_validation(self):
        payload = {"prompt": "", "allergies": ["Gluten"]}
        res = self.client.post("/api/chat", json=payload)
        self.assertEqual(res.status_code, 400)


if __name__ == "__main__":
    unittest.main()
