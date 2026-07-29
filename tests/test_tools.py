"""
Unit tests for McDonald's Allergen Agent Tools (src/tools.py)
"""

import unittest
from src.tools import (
    load_allergen_dataset,
    lookup_item_allergens,
    search_safe_items,
    evaluate_allergen_safety
)


class TestAgentTools(unittest.TestCase):
    def test_load_dataset(self):
        dataset = load_allergen_dataset()
        self.assertGreater(len(dataset), 0)

    def test_lookup_item_exact_and_fuzzy(self):
        # Exact lookup
        res_exact = lookup_item_allergens("Big Mac")
        self.assertTrue(res_exact["found"])
        self.assertEqual(res_exact["item"]["name"], "Big Mac")

        # Case insensitive fuzzy lookup
        res_fuzzy = lookup_item_allergens("fries")
        self.assertTrue(res_fuzzy["found"])
        self.assertIn("Fries", res_fuzzy["item"]["name"])

        # Non-existent item
        res_none = lookup_item_allergens("Sushi")
        self.assertFalse(res_none["found"])

    def test_evaluate_allergen_safety_gluten(self):
        # Big Mac contains Gluten -> Should be UNSAFE for Gluten allergy
        eval_big_mac = evaluate_allergen_safety("Big Mac", ["Gluten"])
        self.assertEqual(eval_big_mac["status"], "UNSAFE")
        self.assertIn("Gluten / Wheat", eval_big_mac["matched_allergens"])

    def test_evaluate_allergen_safety_dairy(self):
        # Cheeseburger contains Dairy -> Should be UNSAFE for Dairy allergy
        eval_cheeseburger = evaluate_allergen_safety("Cheeseburger", ["Dairy"])
        self.assertEqual(eval_cheeseburger["status"], "UNSAFE")
        self.assertIn("Dairy / Milk", eval_cheeseburger["matched_allergens"])

        # Hamburger does NOT contain Dairy -> Should be SAFE for Dairy allergy
        eval_hamburger = evaluate_allergen_safety("Hamburger", ["Dairy"])
        self.assertEqual(eval_hamburger["status"], "SAFE")

    def test_evaluate_allergen_safety_nuts(self):
        # McFlurry with M&M'S contains Nut warning -> Should be UNSAFE for Nut allergy
        eval_mcflurry = evaluate_allergen_safety("McFlurry with M&M'S Candies", ["Nuts"])
        self.assertEqual(eval_mcflurry["status"], "UNSAFE")
        self.assertIn("Peanuts / Tree Nuts", eval_mcflurry["matched_allergens"])

        # Apple Slices does NOT contain Nuts -> Should be SAFE for Nut allergy
        eval_apples = evaluate_allergen_safety("Apple Slices", ["Nuts"])
        self.assertEqual(eval_apples["status"], "SAFE")

    def test_search_safe_items(self):
        # Items safe for Gluten allergy (e.g. Apple Slices, Coca-Cola)
        safe_gluten = search_safe_items(["Gluten"])
        item_names = [i["name"] for i in safe_gluten]
        self.assertIn("Apple Slices", item_names)
        self.assertIn("Coca-Cola", item_names)
        self.assertNotIn("Big Mac", item_names)


if __name__ == "__main__":
    unittest.main()
