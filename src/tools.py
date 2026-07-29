"""
McDonald's Allergen Agent Tools
-------------------------------
Provides structured data lookup and safety evaluation functions for reading
the simple table file (`data/mcdonalds_allergens.json`).
"""

import json
import os
from typing import List, Dict, Any, Optional

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


def load_allergen_dataset(data_path: str = DEFAULT_DATA_PATH) -> List[Dict[str, Any]]:
    """Loads the McDonald's simple allergen table file into memory."""
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
    Look up a McDonald's menu item by name in the simple allergen table file.
    Performs case-insensitive fuzzy/exact matching.
    """
    dataset = load_allergen_dataset(data_path)
    clean_query = item_name.strip().lower()

    # 1. Exact match by item_id or name
    for item in dataset:
        if item["item_id"].lower() == clean_query or item["name"].lower() == clean_query:
            return {"found": True, "match_type": "exact", "item": item}

    # 2. Substring match (e.g. "fries" -> "World Famous Fries", "big mac" -> "Big Mac")
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
    Evaluates all items within a matched category or generic term (e.g., 'burgers', 'shakes', 'breakfast').
    Returns structured safety results for each item in that category.
    """
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
    Filters menu items that are safe for the user's allergen profile.
    Considers 'gluten', 'dairy', and 'nuts' (peanuts/tree nuts).
    """
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
    Evaluates whether a specific menu item is safe for a user given their list of allergies.
    Returns a detailed verdict containing status (SAFE, UNSAFE, WARNING), matched allergens,
    and cross-contamination notes.
    """
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
