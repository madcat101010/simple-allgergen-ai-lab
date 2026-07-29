"""
McDonald's Allergen Agent Tools & Function Schema Definitions
--------------------------------------------------------------
Provides typed tool functions, explicit JSON schema parameter definitions,
Pydantic input/output models, and strict runtime input validation.
"""

import json
import os
from typing import List, Dict, Any, Optional

# Optional Pydantic import with graceful fallback
try:
    from pydantic import BaseModel, Field, validate_call
    HAS_PYDANTIC = True
except ImportError:
    HAS_PYDANTIC = False
    BaseModel = object
    Field = lambda *args, **kwargs: None
    validate_call = lambda func: func

# Default path to simple table file
DEFAULT_DATA_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "data",
    "mcdonalds_allergens.json"
)

# Global cache for allergen dataset
_DATASET_CACHE: Optional[List[Dict[str, Any]]] = None

# Category & generic keyword mapping dictionary
GENERIC_CATEGORY_MAP = {
    "burger": "Burgers",
    "burgers": "Burgers",
    "hamburger": "Burgers",
    "hamburgers": "Burgers",
    "cheeseburger": "Burgers",
    "sandwich": "Burgers",
    "sandwiches": "Burgers",
    "chicken": "Chicken & Fish",
    "nugget": "Chicken & Fish",
    "nuggets": "Chicken & Fish",
    "mcnuggets": "Chicken & Fish",
    "fish": "Chicken & Fish",
    "breakfast": "Breakfast",
    "mcmuffin": "Breakfast",
    "burrito": "Breakfast",
    "fry": "Fries & Sides",
    "fries": "Fries & Sides",
    "sides": "Fries & Sides",
    "side": "Fries & Sides",
    "shake": "Sweets & Treats",
    "shakes": "Sweets & Treats",
    "milkshake": "Sweets & Treats",
    "milkshakes": "Sweets & Treats",
    "dessert": "Sweets & Treats",
    "desserts": "Sweets & Treats",
    "ice cream": "Sweets & Treats",
    "mcflurry": "Sweets & Treats",
    "pie": "Sweets & Treats",
    "drink": "Drinks",
    "drinks": "Drinks",
    "soda": "Drinks",
    "beverage": "Drinks",
    "coffee": "Drinks",
    "latte": "Drinks"
}

# ==============================================================================
# EXPLICIT JSON SCHEMAS FOR LLM TOOL DECLARATIONS & VALIDATION
# ==============================================================================

LOOKUP_ITEM_ALLERGENS_JSON_SCHEMA = {
    "type": "object",
    "title": "LookupItemAllergensInput",
    "description": "Explicit JSON Schema for lookup_item_allergens tool",
    "properties": {
        "item_name": {
            "type": "string",
            "minLength": 1,
            "description": "Name or partial query of the McDonald's menu item (e.g. 'Big Mac', 'fries')."
        },
        "data_path": {
            "type": "string",
            "default": DEFAULT_DATA_PATH,
            "description": "Optional file path to the allergen JSON dataset."
        }
    },
    "required": ["item_name"]
}

EVALUATE_ALLERGEN_SAFETY_JSON_SCHEMA = {
    "type": "object",
    "title": "EvaluateAllergenSafetyInput",
    "description": "Explicit JSON Schema for evaluate_allergen_safety tool",
    "properties": {
        "item_name": {
            "type": "string",
            "minLength": 1,
            "description": "Canonical or queried McDonald's menu item name."
        },
        "user_allergies": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Active customer allergies to check (e.g. ['Gluten', 'Dairy', 'Nuts'])."
        },
        "data_path": {
            "type": "string",
            "default": DEFAULT_DATA_PATH,
            "description": "Optional file path to dataset JSON file."
        }
    },
    "required": ["item_name", "user_allergies"]
}

SEARCH_SAFE_ITEMS_JSON_SCHEMA = {
    "type": "object",
    "title": "SearchSafeItemsInput",
    "description": "Explicit JSON Schema for search_safe_items tool",
    "properties": {
        "user_allergies": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Active customer food allergy profile."
        },
        "category": {
            "type": ["string", "null"],
            "default": None,
            "description": "Optional category filter (e.g. 'Breakfast', 'Burgers')."
        },
        "data_path": {
            "type": "string",
            "default": DEFAULT_DATA_PATH,
            "description": "Optional file path to dataset JSON file."
        }
    },
    "required": ["user_allergies"]
}

EVALUATE_CATEGORY_SAFETY_JSON_SCHEMA = {
    "type": "object",
    "title": "EvaluateCategorySafetyInput",
    "description": "Explicit JSON Schema for evaluate_category_safety tool",
    "properties": {
        "category_or_generic": {
            "type": "string",
            "minLength": 1,
            "description": "Generic category search query (e.g. 'burgers', 'shakes', 'fries')."
        },
        "user_allergies": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Active user food allergy profile."
        },
        "data_path": {
            "type": "string",
            "default": DEFAULT_DATA_PATH,
            "description": "Optional file path to dataset JSON file."
        }
    },
    "required": ["category_or_generic", "user_allergies"]
}

TOOL_JSON_SCHEMAS = {
    "lookup_item_allergens": LOOKUP_ITEM_ALLERGENS_JSON_SCHEMA,
    "evaluate_allergen_safety": EVALUATE_ALLERGEN_SAFETY_JSON_SCHEMA,
    "search_safe_items": SEARCH_SAFE_ITEMS_JSON_SCHEMA,
    "evaluate_category_safety": EVALUATE_CATEGORY_SAFETY_JSON_SCHEMA
}

# ==============================================================================
# PYDANTIC MODELS FOR STRICT SCHEMAS & INPUT VALIDATION
# ==============================================================================

if HAS_PYDANTIC:
    class LookupItemAllergensInputModel(BaseModel):
        item_name: str = Field(..., min_length=1, description="Menu item name")
        data_path: str = Field(default=DEFAULT_DATA_PATH, description="Dataset path")

    class EvaluateAllergenSafetyInputModel(BaseModel):
        item_name: str = Field(..., min_length=1, description="Menu item name")
        user_allergies: List[str] = Field(..., description="Active user allergies")
        data_path: str = Field(default=DEFAULT_DATA_PATH, description="Dataset path")

    class SearchSafeItemsInputModel(BaseModel):
        user_allergies: List[str] = Field(..., description="Active user allergies")
        category: Optional[str] = Field(default=None, description="Optional category filter")
        data_path: str = Field(default=DEFAULT_DATA_PATH, description="Dataset path")

    class EvaluateCategorySafetyInputModel(BaseModel):
        category_or_generic: str = Field(..., min_length=1, description="Category term")
        user_allergies: List[str] = Field(..., description="Active user allergies")
        data_path: str = Field(default=DEFAULT_DATA_PATH, description="Dataset path")


def validate_tool_input(tool_name: str, kwargs: Dict[str, Any]) -> None:
    """
    Strict Runtime Input Validator enforcing JSON schema & type constraints on tool invocations.

    Args:
        tool_name (str): Name of the tool being called.
        kwargs (Dict[str, Any]): Arguments passed to the tool.

    Raises:
        ValueError: If a required argument is missing or empty.
        TypeError: If an argument fails type validation constraints.
    """
    schema = TOOL_JSON_SCHEMAS.get(tool_name)
    if not schema:
        return

    # 1. Required field checks
    required_fields = schema.get("required", [])
    for field in required_fields:
        if field not in kwargs or kwargs[field] is None:
            raise ValueError(f"Tool '{tool_name}' missing required parameter: '{field}'.")

    # 2. Type & constraint checks
    properties = schema.get("properties", {})
    for param_name, value in kwargs.items():
        if param_name not in properties or value is None:
            continue
        expected_type = properties[param_name].get("type")
        
        if expected_type == "string":
            if not isinstance(value, str):
                raise TypeError(f"Tool '{tool_name}' parameter '{param_name}' must be a string, got {type(value).__name__}.")
            if properties[param_name].get("minLength", 0) > 0 and len(value.strip()) == 0:
                raise ValueError(f"Tool '{tool_name}' parameter '{param_name}' cannot be empty string.")
        elif expected_type == "array":
            if not isinstance(value, (list, tuple)):
                raise TypeError(f"Tool '{tool_name}' parameter '{param_name}' must be a list, got {type(value).__name__}.")


def load_allergen_dataset(data_path: str = DEFAULT_DATA_PATH) -> List[Dict[str, Any]]:
    """
    Loads and caches the McDonald's simple allergen table dataset into memory.
    """
    global _DATASET_CACHE
    if _DATASET_CACHE is not None and data_path == DEFAULT_DATA_PATH:
        return _DATASET_CACHE

    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Allergen dataset file not found at: {data_path}")

    with open(data_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    if data_path == DEFAULT_DATA_PATH:
        _DATASET_CACHE = dataset
    return dataset


def lookup_item_allergens(item_name: str, data_path: str = DEFAULT_DATA_PATH) -> Dict[str, Any]:
    """
    Looks up a McDonald's menu item by name or partial query in the simple allergen table file.
    """
    validate_tool_input("lookup_item_allergens", {"item_name": item_name, "data_path": data_path})
    dataset = load_allergen_dataset(data_path)
    clean_query = item_name.strip().lower()

    # 1. Exact match by item_id or name
    for item in dataset:
        if item["item_id"].lower() == clean_query or item["name"].lower() == clean_query:
            return {"found": True, "match_type": "exact", "item": item}

    # 2. Substring match
    matching_items = []
    for item in dataset:
        if clean_query in item["name"].lower() or clean_query in item["item_id"].lower():
            matching_items.append(item)

    if len(matching_items) == 1:
        return {"found": True, "match_type": "fuzzy", "item": matching_items[0]}
    elif len(matching_items) > 1:
        return {
            "found": True,
            "match_type": "ambiguous",
            "matches": [m["name"] for m in matching_items],
            "item": matching_items[0]  # Best candidate
        }

    return {
        "found": False,
        "query": item_name,
        "message": f"Menu item '{item_name}' was not found in the McDonald's allergen table."
    }


def evaluate_category_safety(
    category_or_generic: str,
    user_allergies: List[str],
    data_path: str = DEFAULT_DATA_PATH
) -> Optional[Dict[str, Any]]:
    """
    Evaluates safety for all menu items within a generic food category.
    """
    validate_tool_input("evaluate_category_safety", {
        "category_or_generic": category_or_generic,
        "user_allergies": user_allergies,
        "data_path": data_path
    })
    dataset = load_allergen_dataset(data_path)
    clean_term = category_or_generic.strip().lower()

    # Identify category name from GENERIC_CATEGORY_MAP or dataset categories
    target_category = GENERIC_CATEGORY_MAP.get(clean_term)
    if not target_category:
        for item in dataset:
            if clean_term in item["category"].lower():
                target_category = item["category"]
                break

    if not target_category:
        return None

    # Filter items matching category
    category_items = [item for item in dataset if item["category"].lower() == target_category.lower()]
    if not category_items:
        return None

    evaluations = []
    safe_count = 0
    unsafe_count = 0

    for item in category_items:
        item_eval = evaluate_allergen_safety(item["name"], user_allergies, data_path)
        evaluations.append(item_eval)
        if item_eval["status"] == "SAFE":
            safe_count += 1
        elif item_eval["status"] == "UNSAFE":
            unsafe_count += 1

    return {
        "category": target_category,
        "total_items": len(category_items),
        "safe_count": safe_count,
        "unsafe_count": unsafe_count,
        "evaluations": evaluations
    }


def search_safe_items(
    user_allergies: List[str],
    category: Optional[str] = None,
    data_path: str = DEFAULT_DATA_PATH
) -> List[Dict[str, Any]]:
    """
    Filters the McDonald's simple table dataset to return items safe for a specified user allergy profile.
    """
    validate_tool_input("search_safe_items", {
        "user_allergies": user_allergies,
        "category": category,
        "data_path": data_path
    })
    dataset = load_allergen_dataset(data_path)
    clean_allergies = [a.strip().lower() for a in user_allergies]

    check_gluten = any("gluten" in a or "wheat" in a for a in clean_allergies)
    check_dairy = any("dairy" in a or "milk" in a for a in clean_allergies)
    check_nuts = any("nut" in a or "peanut" in a for a in clean_allergies)

    safe_items = []
    for item in dataset:
        if category and category.lower() not in item["category"].lower():
            continue

        is_safe = True
        if check_gluten and item.get("contains_gluten", False):
            is_safe = False
        if check_dairy and item.get("contains_dairy", False):
            is_safe = False
        if check_nuts and item.get("contains_nuts", False):
            is_safe = False

        if is_safe:
            safe_items.append({
                "item_id": item["item_id"],
                "name": item["name"],
                "category": item["category"],
                "allergens": item["allergens"],
                "ingredients_summary": item["ingredients_summary"]
            })

    return safe_items


def evaluate_allergen_safety(
    item_name: str,
    user_allergies: List[str],
    data_path: str = DEFAULT_DATA_PATH
) -> Dict[str, Any]:
    """
    Evaluates whether a specific McDonald's menu item is safe for a customer given their active allergy profile.
    """
    validate_tool_input("evaluate_allergen_safety", {
        "item_name": item_name,
        "user_allergies": user_allergies,
        "data_path": data_path
    })
    lookup = lookup_item_allergens(item_name, data_path)
    if not lookup["found"]:
        return {
            "status": "UNKNOWN",
            "item_name": item_name,
            "verdict": f"Item '{item_name}' was not found in the McDonald's menu database.",
            "safety_badge": "❓ UNKNOWN"
        }

    item = lookup["item"]
    clean_allergies = [a.strip().lower() for a in user_allergies]

    matched_allergens = []
    contains_trigger = False

    # Check Gluten / Wheat
    if any("gluten" in a or "wheat" in a for a in clean_allergies):
        if item.get("contains_gluten", False):
            matched_allergens.append("Gluten / Wheat")
            contains_trigger = True

    # Check Dairy / Milk
    if any("dairy" in a or "milk" in a for a in clean_allergies):
        if item.get("contains_dairy", False):
            matched_allergens.append("Dairy / Milk")
            contains_trigger = True

    # Check Nuts (Peanuts / Tree Nuts)
    if any("nut" in a or "peanut" in a for a in clean_allergies):
        if item.get("contains_nuts", False):
            matched_allergens.append("Peanuts / Tree Nuts")
            contains_trigger = True

    # Determine status and message
    if contains_trigger:
        status = "UNSAFE"
        safety_badge = "❌ UNSAFE"
        verdict = f"UNSAFE: {item['name']} contains {', '.join(matched_allergens)}."
    else:
        status = "SAFE"
        safety_badge = "✅ SAFE"
        verdict = f"SAFE: {item['name']} does not contain ingredients matching your specified allergies ({', '.join(user_allergies)})."

    return {
        "status": status,
        "safety_badge": safety_badge,
        "item_name": item["name"],
        "category": item["category"],
        "user_allergies_evaluated": user_allergies,
        "matched_allergens": matched_allergens,
        "all_allergens_in_item": item["allergens"],
        "ingredients_summary": item["ingredients_summary"],
        "verdict": verdict,
        "disclaimer": "Warning: McDonald's kitchen operations involve shared preparation areas, fryers, and equipment. Cross-contact may occur."
    }
