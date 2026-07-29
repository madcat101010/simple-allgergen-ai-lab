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
    "description": "Explicit JSON Schema for lookup_item_allergens tool. Resolves item names and provides recovery guidance if item is not found.",
    "properties": {
        "item_name": {
            "type": "string",
            "minLength": 1,
            "description": "Name or partial query of the McDonald's menu item (e.g. 'Big Mac', 'fries', 'egg-mcmuffin'). Must be non-empty."
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
    "description": "Explicit JSON Schema for evaluate_allergen_safety tool. Evaluates menu item against customer allergy profile with structured recovery path guidance.",
    "properties": {
        "item_name": {
            "type": "string",
            "minLength": 1,
            "description": "Canonical or queried McDonald's menu item name (e.g. 'Big Mac', 'World Famous Fries')."
        },
        "user_allergies": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Active customer food allergy list to check against item allergens (e.g. ['Gluten'], ['Dairy', 'Nuts'])."
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
    "description": "Explicit JSON Schema for search_safe_items tool. Filters menu dataset to return all items verified safe for user allergy profile.",
    "properties": {
        "user_allergies": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Active customer food allergy profile list (e.g. ['Gluten'], ['Dairy', 'Nuts'])."
        },
        "category": {
            "type": ["string", "null"],
            "default": None,
            "description": "Optional category filter (e.g. 'Breakfast', 'Burgers', 'Drinks')."
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
    "description": "Explicit JSON Schema for evaluate_category_safety tool. Evaluates food category safety with structured recovery instructions if category is unrecognized.",
    "properties": {
        "category_or_generic": {
            "type": "string",
            "minLength": 1,
            "description": "Generic category search query or keyword (e.g. 'burgers', 'shakes', 'fries', 'breakfast', 'drinks')."
        },
        "user_allergies": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Active user food allergy profile list."
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
        item_name: str = Field(..., min_length=1, description="McDonald's menu item query name or ID (e.g. 'Big Mac', 'fries')")
        data_path: str = Field(default=DEFAULT_DATA_PATH, description="File path to allergen JSON dataset")

    class EvaluateAllergenSafetyInputModel(BaseModel):
        item_name: str = Field(..., min_length=1, description="McDonald's menu item name to evaluate")
        user_allergies: List[str] = Field(..., description="Active user allergy profile list (e.g. ['Gluten', 'Dairy'])")
        data_path: str = Field(default=DEFAULT_DATA_PATH, description="File path to allergen JSON dataset")

    class SearchSafeItemsInputModel(BaseModel):
        user_allergies: List[str] = Field(..., description="Active user allergy profile list")
        category: Optional[str] = Field(default=None, description="Optional category filter (e.g. 'Burgers', 'Drinks')")
        data_path: str = Field(default=DEFAULT_DATA_PATH, description="File path to allergen JSON dataset")

    class EvaluateCategorySafetyInputModel(BaseModel):
        category_or_generic: str = Field(..., min_length=1, description="Food category or generic term (e.g. 'burgers', 'breakfast')")
        user_allergies: List[str] = Field(..., description="Active user allergy profile list")
        data_path: str = Field(default=DEFAULT_DATA_PATH, description="File path to allergen JSON dataset")


def format_tool_error(tool_name: str, error_message: str, kwargs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Constructs a structured error recovery dictionary for tool failures to guide LLM path correction.

    Args:
        tool_name (str): Name of the tool function that failed.
        error_message (str): Original error message or exception description.
        kwargs (Dict[str, Any], optional): Arguments supplied to the tool function.

    Returns:
        Dict[str, Any]: Structured error payload containing status='ERROR', original error details,
            and explicit recovery instructions and suggested actions for LLM execution path correction.
    """
    return {
        "status": "ERROR",
        "tool_name": tool_name,
        "error": error_message,
        "passed_arguments": kwargs or {},
        "recovery_instructions": (
            f"Tool '{tool_name}' failed during execution: {error_message}. "
            "To correct your path:\n"
            "1. Inspect passed parameter types and required fields matching the tool schema.\n"
            "2. Ensure required parameters (e.g. 'item_name', 'user_allergies') are non-empty strings or lists.\n"
            "3. Re-try calling the tool with corrected parameters or fallback to `search_safe_items`."
        ),
        "suggested_actions": [
            f"Verify schema requirements for {tool_name}",
            "Re-invoke tool with valid parameter formats",
            "Fallback to search_safe_items for recommendations"
        ]
    }


def validate_tool_input(tool_name: str, kwargs: Dict[str, Any]) -> None:
    """
    Strict Runtime Input Validator enforcing JSON schema & type constraints on tool invocations.

    Args:
        tool_name (str): Name of the tool being called (e.g. 'lookup_item_allergens', 'evaluate_allergen_safety').
        kwargs (Dict[str, Any]): Arguments dictionary passed to the tool function.

    Returns:
        None: Returns None if validation passes without raising exceptions.

    Raises:
        ValueError: If a required parameter is missing, None, or empty string.
        TypeError: If a parameter fails type validation constraints (e.g. string expected, got int).
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

    Args:
        data_path (str, optional): File path to allergen JSON dataset. Defaults to DEFAULT_DATA_PATH.

    Returns:
        List[Dict[str, Any]]: Complete list of menu item dictionary records.

    Raises:
        FileNotFoundError: If the specified dataset file path does not exist.
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
    Looks up a McDonald's menu item by name, item_id, or partial query in the allergen table.

    Args:
        item_name (str): Name, item ID, or partial query of the McDonald's menu item.
            Must be a non-empty string (e.g. 'Big Mac', 'fries', 'egg-mcmuffin', 'coca-cola').
        data_path (str, optional): File path to the allergen JSON dataset.
            Defaults to DEFAULT_DATA_PATH ('data/mcdonalds_allergens.json').

    Returns:
        Dict[str, Any]: Structured dictionary with search results:
            - found (bool): True if exact, substring, or fuzzy match was found; False otherwise.
            - match_type (str, optional): 'exact', 'fuzzy', or 'ambiguous' when found.
            - item (dict, optional): Menu item record when found.
            - matches (list[str], optional): List of item names if query matched multiple items.
            - query (str): Query string evaluated.
            - message (str): Detailed text summary of search outcome.
            - recovery_instructions (str, optional): Actionable steps to help LLM correct path when not found.
            - suggested_actions (list[str], optional): Suggested next tool calls or prompts.

    Raises:
        ValueError: If item_name is empty or whitespace-only.
        TypeError: If item_name is not a string.
        FileNotFoundError: If the specified dataset file does not exist.
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
            "item": matching_items[0],  # Best candidate
            "recovery_instructions": (
                f"Query '{item_name}' matched multiple menu items: {', '.join([m['name'] for m in matching_items])}. "
                "Path Recovery Instructions:\n"
                "1. If user asked about a specific item, re-query using the exact full item name from the matched list.\n"
                "2. If user asked broadly, evaluate each matched item individually using `evaluate_allergen_safety`."
            ),
            "suggested_actions": [
                "Select exact item name from matched list",
                "Execute evaluate_allergen_safety for specific matched item"
            ]
        }

    return {
        "found": False,
        "query": item_name,
        "message": f"Menu item '{item_name}' was not found in the McDonald's allergen table.",
        "recovery_instructions": (
            f"Menu item '{item_name}' was not found in the allergen dataset. "
            "Path Recovery Instructions for AI Agent:\n"
            "1. Re-try `lookup_item_allergens` using partial keywords (e.g. 'fries', 'nuggets', 'cheeseburger').\n"
            "2. If user asked about a menu category (e.g. 'burgers', 'breakfast', 'drinks'), call `evaluate_category_safety(category_or_generic=...)`.\n"
            "3. Call `search_safe_items(user_allergies=...)` to discover safe menu options for customer's allergy profile."
        ),
        "suggested_actions": [
            "Call evaluate_category_safety with generic food term",
            "Call search_safe_items to retrieve safe options",
            "Prompt user to verify menu item spelling"
        ]
    }


def evaluate_category_safety(
    category_or_generic: str,
    user_allergies: List[str],
    data_path: str = DEFAULT_DATA_PATH
) -> Dict[str, Any]:
    """
    Evaluates allergen safety for all menu items within a McDonald's menu category or generic keyword.

    Args:
        category_or_generic (str): Generic category keyword or category name (e.g. 'burgers', 'breakfast', 'shakes', 'fries').
            Must be a non-empty string.
        user_allergies (List[str]): Active customer food allergy list (e.g. ['Gluten'], ['Dairy', 'Nuts']).
            Must be a list of string allergy names.
        data_path (str, optional): File path to allergen JSON dataset. Defaults to DEFAULT_DATA_PATH.

    Returns:
        Dict[str, Any]: Category evaluation summary dictionary:
            - found (bool): True if category resolved to dataset items; False if category not recognized.
            - category (str, optional): Matched canonical category name (e.g. 'Burgers', 'Breakfast').
            - total_items (int, optional): Count of menu items in category.
            - safe_count (int, optional): Count of items in category safe for user allergy profile.
            - unsafe_count (int, optional): Count of items containing user allergen triggers.
            - evaluations (list[dict], optional): List of item evaluations within category.
            - status (str): 'CATEGORY' if category found, or 'UNKNOWN_CATEGORY' if not recognized.
            - message (str, optional): Descriptive text if category not found.
            - recovery_instructions (str, optional): Explicit steps to guide LLM path recovery when category fails.
            - suggested_actions (list[str], optional): Concrete next tool calls or prompts.

    Raises:
        ValueError: If category_or_generic is empty string or user_allergies is missing.
        TypeError: If category_or_generic is not string or user_allergies is not a list.
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

    valid_cats = list(sorted(set(GENERIC_CATEGORY_MAP.values())))
    if not target_category:
        return {
            "found": False,
            "status": "UNKNOWN_CATEGORY",
            "category_query": category_or_generic,
            "message": f"Category '{category_or_generic}' was not recognized in McDonald's menu database.",
            "available_categories": valid_cats,
            "recovery_instructions": (
                f"Category query '{category_or_generic}' was not recognized. "
                f"Recognized menu categories: {', '.join(valid_cats)}. "
                "Path Recovery Instructions for AI Agent:\n"
                "1. Re-try `evaluate_category_safety` using one of the valid keywords: 'burgers', 'breakfast', 'chicken', 'fries', 'shakes', 'drinks'.\n"
                "2. Call `search_safe_items(user_allergies=...)` to retrieve safe options across all menu categories."
            ),
            "suggested_actions": [
                "Re-call evaluate_category_safety with valid category keyword",
                "Call search_safe_items to list safe menu items across all categories"
            ]
        }

    # Filter items matching category
    category_items = [item for item in dataset if item["category"].lower() == target_category.lower()]
    if not category_items:
        return {
            "found": False,
            "status": "UNKNOWN_CATEGORY",
            "category_query": category_or_generic,
            "message": f"No items found for category '{target_category}'.",
            "available_categories": valid_cats,
            "recovery_instructions": (
                f"No items were found under category '{target_category}'. "
                "Path Recovery Instructions for AI Agent:\n"
                "1. Call `search_safe_items(user_allergies=...)` to search all available menu items."
            ),
            "suggested_actions": [
                "Call search_safe_items for customer allergy profile across all categories"
            ]
        }

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
        "found": True,
        "status": "CATEGORY",
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
    Filters the McDonald's dataset to return items safe for a specified user allergy profile.

    Args:
        user_allergies (List[str]): List of active customer food allergies (e.g. ['Gluten'], ['Dairy', 'Nuts']).
            Must be a non-empty list of string allergy names.
        category (str, optional): Category filter string (e.g. 'Burgers', 'Drinks', 'Breakfast').
            Defaults to None (searches all categories).
        data_path (str, optional): File path to allergen JSON dataset. Defaults to DEFAULT_DATA_PATH.

    Returns:
        List[Dict[str, Any]]: List of safe menu item dictionaries. Each item contains:
            - item_id (str): Unique item key.
            - name (str): Display name of menu item.
            - category (str): Food category name.
            - allergens (list[str]): Listed allergen ingredients.
            - ingredients_summary (str): Ingredient overview.
        Returns empty list if no safe items match criteria.

    Raises:
        ValueError: If user_allergies is missing.
        TypeError: If user_allergies is not a list/sequence.
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
    Evaluates whether a specific McDonald's menu item is safe for a customer given their allergy profile.

    Args:
        item_name (str): McDonald's menu item name to evaluate (e.g. 'Big Mac', 'World Famous Fries').
        user_allergies (List[str]): List of active customer food allergies (e.g. ['Gluten'], ['Dairy', 'Nuts']).
        data_path (str, optional): File path to allergen JSON dataset. Defaults to DEFAULT_DATA_PATH.

    Returns:
        Dict[str, Any]: Safety evaluation dictionary containing:
            - status (str): Safety status code ('SAFE', 'UNSAFE', or 'UNKNOWN').
            - safety_badge (str): Visual status badge ('✅ SAFE', '❌ UNSAFE', or '❓ UNKNOWN').
            - item_name (str): Canonical item name evaluated (or queried string if unknown).
            - category (str, optional): Menu category of the item.
            - user_allergies_evaluated (list[str]): Customer allergy profile evaluated.
            - matched_allergens (list[str]): Specific allergens in item matching customer profile.
            - all_allergens_in_item (list[str], optional): Full list of allergens in item.
            - ingredients_summary (str, optional): Ingredients overview string.
            - verdict (str): Human-readable verdict explanation string.
            - disclaimer (str): Mandatory fast-food cross-contact medical warning.
            - recovery_instructions (str, optional): Step-by-step guidance provided when status is 'UNKNOWN'
              to help LLM correct its path.
            - suggested_actions (list[str], optional): Suggested next tool calls or actions.

    Raises:
        ValueError: If item_name is missing or empty, or user_allergies is missing.
        TypeError: If item_name is not string or user_allergies is not a list.
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
            "safety_badge": "❓ UNKNOWN",
            "lookup_details": lookup,
            "recovery_instructions": (
                f"Unable to evaluate allergen safety because menu item '{item_name}' was not found in the database. "
                "Path Recovery Instructions for AI Agent:\n"
                "1. Check spelling or use `lookup_item_allergens` with partial item names (e.g. 'Big Mac', 'fries').\n"
                "2. If user query refers to a food category (e.g. 'burgers', 'shakes', 'breakfast'), call `evaluate_category_safety(category_or_generic=...)`.\n"
                "3. Call `search_safe_items(user_allergies=...)` to retrieve menu options safe for customer's allergy profile."
            ),
            "suggested_actions": [
                "Use lookup_item_allergens with simplified search terms",
                "Execute evaluate_category_safety for menu category assessment",
                "Execute search_safe_items to find menu items safe for user's allergy profile"
            ],
            "disclaimer": "Warning: McDonald's kitchen operations involve shared preparation areas, fryers, and equipment. Cross-contact may occur."
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

