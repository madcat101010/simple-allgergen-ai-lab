"""
Unit tests for Explicit JSON Schemas, Pydantic Models & Strict Input Validation (src/tools.py)
"""

import unittest
from src.tools import (
    TOOL_JSON_SCHEMAS,
    LOOKUP_ITEM_ALLERGENS_JSON_SCHEMA,
    EVALUATE_ALLERGEN_SAFETY_JSON_SCHEMA,
    SEARCH_SAFE_ITEMS_JSON_SCHEMA,
    EVALUATE_CATEGORY_SAFETY_JSON_SCHEMA,
    validate_tool_input,
    evaluate_allergen_safety,
    lookup_item_allergens,
    search_safe_items
)


class TestToolSchemasAndValidation(unittest.TestCase):
    def test_explicit_json_schemas_exist_and_valid(self):
        self.assertIn("lookup_item_allergens", TOOL_JSON_SCHEMAS)
        self.assertIn("evaluate_allergen_safety", TOOL_JSON_SCHEMAS)
        self.assertIn("search_safe_items", TOOL_JSON_SCHEMAS)
        self.assertIn("evaluate_category_safety", TOOL_JSON_SCHEMAS)

        # Check required fields in JSON schemas
        self.assertEqual(LOOKUP_ITEM_ALLERGENS_JSON_SCHEMA["required"], ["item_name"])
        self.assertEqual(EVALUATE_ALLERGEN_SAFETY_JSON_SCHEMA["required"], ["item_name", "user_allergies"])
        self.assertEqual(SEARCH_SAFE_ITEMS_JSON_SCHEMA["required"], ["user_allergies"])
        self.assertEqual(EVALUATE_CATEGORY_SAFETY_JSON_SCHEMA["required"], ["category_or_generic", "user_allergies"])

    def test_strict_input_validation_missing_required_param(self):
        with self.assertRaises(ValueError):
            validate_tool_input("evaluate_allergen_safety", {"item_name": "Big Mac"})  # missing user_allergies

        with self.assertRaises(ValueError):
            lookup_item_allergens(item_name="")  # empty string minLength validation

    def test_strict_input_validation_invalid_type(self):
        with self.assertRaises(TypeError):
            validate_tool_input("evaluate_allergen_safety", {"item_name": 12345, "user_allergies": ["Gluten"]})

        with self.assertRaises(TypeError):
            validate_tool_input("search_safe_items", {"user_allergies": "Gluten"})  # string instead of list

    def test_valid_tool_invocations_pass(self):
        res = evaluate_allergen_safety(item_name="Big Mac", user_allergies=["Gluten"])
        self.assertEqual(res["status"], "UNSAFE")

        safe_items = search_safe_items(user_allergies=["Dairy"])
        self.assertIsInstance(safe_items, list)


if __name__ == "__main__":
    unittest.main()
