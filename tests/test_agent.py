"""
Unit tests for McDonald's Allergen Agent (src/agent.py)
"""

import unittest
from src.agent import AllergenAgent


class TestAllergenAgent(unittest.TestCase):
    def setUp(self):
        self.agent = AllergenAgent()

    def test_agent_evaluates_big_mac_dairy_allergy(self):
        result = self.agent.process_query("Is a Big Mac safe for me?", ["Dairy"])
        self.assertEqual(result["status"], "UNSAFE")
        self.assertIn("Big Mac", result["evaluated_item"])
        self.assertIn("UNSAFE", result["safety_badge"])
        self.assertIn("Medical Disclaimer", result["response"])

    def test_agent_evaluates_generic_category_burgers(self):
        result = self.agent.process_query("Can I eat burgers?", ["Dairy"])
        self.assertEqual(result["status"], "CATEGORY")
        self.assertIn("Burgers", result["response"])
        self.assertIn("Hamburger", result["response"])

    def test_agent_evaluates_generic_category_milkshake(self):
        result = self.agent.process_query("Are milkshakes safe for me?", ["Dairy"])
        self.assertEqual(result["status"], "CATEGORY")
        self.assertIn("Sweets & Treats", result["response"])

    def test_agent_evaluates_safe_recommendations(self):
        result = self.agent.process_query("What can I eat that is dairy free?", ["Dairy"])
        self.assertEqual(result["status"], "RECOMMENDATION")
        self.assertIn("Apple Slices", result["response"])

    def test_agent_unknown_item_query(self):
        result = self.agent.process_query("Can I eat a Lobster Roll?", ["Gluten"])
        self.assertEqual(result["status"], "UNKNOWN")
        self.assertIn("UNKNOWN ITEM", result["response"])


if __name__ == "__main__":
    unittest.main()
