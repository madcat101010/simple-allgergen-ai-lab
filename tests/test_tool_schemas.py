import unittest
from src.tools import (
    TOOL_JSON_SCHEMAS,
    LOOKUP_ITEM_ALLERGENS_JSON_SCHEMA,
    EVALUATE_ALLERGEN_SAFETY_JSON_SCHEMA,
    SEARCH_SAFE_ITEMS_JSON_SCHEMA,
    EVALUATE_CATEGORY_SAFETY_JSON_SCHEMA,
    validate_tool_input,
    evaluate_allergen_safety,
    evaluate_category_safety,
    lookup_item_allergens,
    search_safe_items,
    format_tool_error,
    load_allergen_dataset
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

    def test_tool_docstrings_contain_detailed_parameter_descriptions(self):
        """Asserts all core tool functions have rich docstrings with explicit Args & Returns parameters."""
        tools_to_check = [
            lookup_item_allergens,
            evaluate_allergen_safety,
            search_safe_items,
            evaluate_category_safety,
            load_allergen_dataset,
            validate_tool_input,
            format_tool_error
        ]
        for fn in tools_to_check:
            doc = fn.__doc__
            self.assertIsNotNone(doc, f"Tool function '{fn.__name__}' is missing docstring!")
            self.assertIn("Args:", doc, f"Tool function '{fn.__name__}' docstring lacks 'Args:' parameter description block.")
            self.assertIn("Returns:", doc, f"Tool function '{fn.__name__}' docstring lacks 'Returns:' description block.")

    def test_tool_error_handling_includes_explicit_recovery_instructions(self):
        """Asserts tools return structured error recovery instructions and suggested actions to guide LLM path correction."""
        # 1. Unknown item lookup
        res_lookup = lookup_item_allergens("NonExistentTaco")
        self.assertFalse(res_lookup["found"])
        self.assertIn("recovery_instructions", res_lookup)
        self.assertIn("suggested_actions", res_lookup)
        self.assertIn("Path Recovery Instructions", res_lookup["recovery_instructions"])

        # 2. Unknown item evaluation
        res_eval = evaluate_allergen_safety("NonExistentTaco", ["Gluten"])
        self.assertEqual(res_eval["status"], "UNKNOWN")
        self.assertIn("recovery_instructions", res_eval)
        self.assertIn("suggested_actions", res_eval)

        # 3. Unknown category evaluation
        res_cat = evaluate_category_safety("invalid_food_group", ["Dairy"])
        self.assertFalse(res_cat["found"])
        self.assertEqual(res_cat["status"], "UNKNOWN_CATEGORY")
        self.assertIn("recovery_instructions", res_cat)
        self.assertIn("suggested_actions", res_cat)

        # 4. Formatted tool error helper
        res_err = format_tool_error("lookup_item_allergens", "Invalid argument passed", {"item_name": 123})
        self.assertEqual(res_err["status"], "ERROR")
        self.assertIn("recovery_instructions", res_err)
        self.assertIn("suggested_actions", res_err)


if __name__ == "__main__":
    unittest.main()

