"""
McDonald's Allergen AI Agent Core Orchestration
------------------------------------------------
Orchestrates system prompts, user allergen profiles, tool invocations,
and safety verdicts reading from `data/mcdonalds_allergens.json`.
"""

import os
import json
from typing import List, Dict, Any, Optional
from src.tools import (
    lookup_item_allergens,
    search_safe_items,
    evaluate_allergen_safety,
    evaluate_category_safety,
    load_allergen_dataset,
    GENERIC_CATEGORY_MAP
)

SYSTEM_PROMPT = """
You are the official McDonald's Allergen Safety AI Assistant.
Your primary mission is to protect customers with food allergies—specifically Gluten, Dairy, and/or Nut allergies—by analyzing McDonald's menu items against their specific allergy profile.

GUIDELINES & CONSTRAINTS:
1. ALWAYS read allergen data from the official McDonald's allergen table file using your tools.
2. NEVER guess or hallucinate allergen content or ingredients.
3. Explicitly state the safety verdict:
   - ✅ SAFE: Item contains no matching allergen ingredients.
   - ❌ UNSAFE: Item directly contains one or more specified allergens.
   - ❓ UNKNOWN / AMBIGUOUS: Item not found or prompt is ambiguous.
4. MANDATORY MEDICAL DISCLAIMER: Always remind users that McDonald's kitchens use shared preparation areas, fryers, and equipment where cross-contamination may occur.
"""


class AllergenAgent:
    def __init__(self, data_path: Optional[str] = None):
        self.data_path = data_path
        self.api_key = os.environ.get("GEMINI_API_KEY", "")
        self.session_history: List[Dict[str, str]] = []

    def process_query(self, prompt: str, user_allergies: List[str]) -> Dict[str, Any]:
        """
        Main orchestration loop:
        1. Parses prompt for menu items, generic categories, or safe recommendation requests.
        2. Executes allergen lookup & safety evaluation tools.
        3. Formulates a structured safety verdict response.
        """
        # Save prompt into session history
        self.session_history.append({"role": "user", "content": prompt})

        # Normalize user allergy profile
        normalized_allergies = [a.strip().title() for a in user_allergies if a.strip()]
        clean_prompt = prompt.lower()
        words = clean_prompt.replace("?", "").replace("!", "").replace(",", "").split()

        # Load dataset
        dataset = load_allergen_dataset(self.data_path) if self.data_path else load_allergen_dataset()
        matched_item = None

        # 1. First check if a specific menu item is explicitly mentioned in prompt
        for item in dataset:
            if item["name"].lower() in clean_prompt or item["item_id"].lower() in clean_prompt:
                matched_item = item["name"]
                break

        # 2. If a specific item was found, evaluate its allergen safety directly
        if matched_item:
            evaluation = evaluate_allergen_safety(matched_item, normalized_allergies, data_path=self.data_path) if self.data_path else evaluate_allergen_safety(matched_item, normalized_allergies)
            response_text = self._format_evaluation_response(evaluation)
            result = {
                "prompt": prompt,
                "user_allergies": normalized_allergies,
                "evaluated_item": matched_item,
                "status": evaluation["status"],
                "safety_badge": evaluation["safety_badge"],
                "response": response_text,
                "details": evaluation,
                "disclaimer": evaluation["disclaimer"]
            }
            self.session_history.append({"role": "assistant", "content": response_text})
            return result

        # 3. Check if the query contains generic category terms (e.g., 'burger', 'burgers', 'shake', 'milkshake', 'breakfast')
        for word in words:
            if word in GENERIC_CATEGORY_MAP:
                cat_eval = evaluate_category_safety(word, normalized_allergies, data_path=self.data_path) if self.data_path else evaluate_category_safety(word, normalized_allergies)
                if cat_eval:
                    response_text = self._format_category_response(cat_eval, normalized_allergies)
                    badge = "✅ SAFE CATEGORY" if cat_eval["unsafe_count"] == 0 else "ℹ️ CATEGORY BREAKDOWN"
                    result = {
                        "prompt": prompt,
                        "user_allergies": normalized_allergies,
                        "status": "CATEGORY",
                        "safety_badge": badge,
                        "response": response_text,
                        "category_details": cat_eval,
                        "disclaimer": "Warning: McDonald's kitchen operations involve shared preparation areas. Cross-contact may occur."
                    }
                    self.session_history.append({"role": "assistant", "content": response_text})
                    return result

        # 4. Check if user is asking for safe options/recommendations in general
        if "safe" in clean_prompt or "what can i eat" in clean_prompt or "recommend" in clean_prompt or "options" in clean_prompt:
            safe_items = search_safe_items(normalized_allergies, data_path=self.data_path) if self.data_path else search_safe_items(normalized_allergies)
            response_text = self._format_safe_items_response(safe_items, normalized_allergies)
            
            result = {
                "prompt": prompt,
                "user_allergies": normalized_allergies,
                "status": "RECOMMENDATION",
                "safety_badge": "ℹ️ RECOMMENDATION",
                "response": response_text,
                "safe_items_count": len(safe_items),
                "disclaimer": "Warning: McDonald's kitchen operations involve shared preparation areas. Cross-contact may occur."
            }
            self.session_history.append({"role": "assistant", "content": response_text})
            return result

        # 5. Fallback when query item or term is unknown
        response_text = f"❓ UNKNOWN ITEM: I couldn't identify a specific item or menu category in your query ('{prompt}'). Please try asking about specific items like 'Big Mac', 'Egg McMuffin', 'World Famous Fries', or generic menu categories like 'burgers', 'shakes', 'breakfast', or ask 'What can I eat?'."
        result = {
            "prompt": prompt,
            "user_allergies": normalized_allergies,
            "status": "UNKNOWN",
            "safety_badge": "❓ UNKNOWN",
            "response": response_text,
            "disclaimer": "Warning: McDonald's kitchen operations involve shared preparation areas. Cross-contact may occur."
        }
        self.session_history.append({"role": "assistant", "content": response_text})
        return result

    def _format_evaluation_response(self, eval_data: Dict[str, Any]) -> str:
        badge = eval_data["safety_badge"]
        item = eval_data["item_name"]
        allergies = ", ".join(eval_data["user_allergies_evaluated"]) or "None specified"
        verdict = eval_data["verdict"]
        ingredients = eval_data.get("ingredients_summary", "N/A")
        all_allergens = ", ".join(eval_data.get("all_allergens_in_item", [])) or "None listed"

        return f"""### {badge}: {item}

**Allergy Profile Evaluated**: {allergies}  
**Verdict**: {verdict}  

**Item Ingredients**: {ingredients}  
**Allergens Present**: {all_allergens}  

> **Medical Disclaimer**: McDonald's kitchen operations involve shared preparation areas, fryers, and equipment. Cross-contact may occur during prep."""

    def _format_category_response(self, cat_data: Dict[str, Any], user_allergies: List[str]) -> str:
        category = cat_data["category"]
        allergies_str = ", ".join(user_allergies) or "None specified"
        lines = [f"### 📋 Category Safety Breakdown: **{category}**"]
        lines.append(f"**Allergy Profile Evaluated**: {allergies_str}\n")

        for item in cat_data["evaluations"]:
            badge = item["safety_badge"]
            name = item["item_name"]
            matched = ", ".join(item["matched_allergens"])
            if item["status"] == "SAFE":
                lines.append(f"- {badge} **{name}**: Safe for your profile.")
            else:
                lines.append(f"- {badge} **{name}**: Contains {matched}.")

        lines.append("\n> **Medical Disclaimer**: McDonald's kitchen operations involve shared preparation areas, fryers, and equipment. Cross-contact may occur during prep.")
        return "\n".join(lines)

    def _format_safe_items_response(self, safe_items: List[Dict[str, Any]], user_allergies: List[str]) -> str:
        allergies_str = ", ".join(user_allergies) or "None specified"
        if not safe_items:
            return f"No items in the McDonald's menu table file were found to be completely safe for the profile: {allergies_str}."

        lines = [f"### 🥗 Menu Items Safe for Profile: **{allergies_str}**\n"]
        categories: Dict[str, List[str]] = {}
        for item in safe_items:
            cat = item["category"]
            categories.setdefault(cat, []).append(item["name"])

        for cat, items in categories.items():
            lines.append(f"**{cat}**:")
            for name in items:
                lines.append(f"- ✅ {name}")
            lines.append("")

        lines.append("> **Medical Disclaimer**: McDonald's kitchen operations involve shared preparation areas, fryers, and equipment. Cross-contact may occur during prep.")
        return "\n".join(lines)
