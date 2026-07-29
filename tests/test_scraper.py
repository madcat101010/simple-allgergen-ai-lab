"""
Unit tests for McDonald's Allergen Data Scraper
Compatible with standard unittest and pytest.
"""

import json
import csv
import os
import unittest
from src.scraper import harvest_allergen_data, DATA_DIR, JSON_PATH, CSV_PATH


class TestScraper(unittest.TestCase):
    def test_harvest_allergen_data(self):
        """Verify that harvest_allergen_data creates JSON and CSV files with valid structure."""
        harvest_allergen_data()

        self.assertTrue(os.path.exists(JSON_PATH), "JSON table file was not created")
        self.assertTrue(os.path.exists(CSV_PATH), "CSV table file was not created")

        # Verify JSON content
        with open(JSON_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 20, f"Expected at least 20 menu items, got {len(data)}")

        # Check key fields in each item
        for item in data:
            self.assertIn("item_id", item)
            self.assertIn("name", item)
            self.assertIn("category", item)
            self.assertIn("allergens", item)
            self.assertIn("contains_gluten", item)
            self.assertIn("contains_dairy", item)
            self.assertIn("contains_nuts", item)
            self.assertIn("ingredients_summary", item)

        # Verify CSV content
        with open(CSV_PATH, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        self.assertEqual(len(rows), len(data))
        self.assertIn("item_id", reader.fieldnames)
        self.assertIn("contains_gluten", reader.fieldnames)


if __name__ == "__main__":
    unittest.main()
