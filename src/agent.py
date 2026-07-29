"""
McDonald's Allergen AI Agent (ADK Agentic Multi-Agent Architecture)
---------------------------------------------------------------------
Implements an agentic workflow following the Google Agent Development Kit (ADK) pattern:
1. AllergyExtractorAgent: Dedicated Sub-Agent that extracts allergen intent from natural language.
2. McDonaldsAllergenAgent: Primary Orchestrator Agent equipped with data lookup tools.
"""

import os
import json
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional

from src.tools import (
    lookup_item_allergens,
    search_safe_items,
    evaluate_allergen_safety,
    evaluate_category_safety,
    load_allergen_dataset,
    GENERIC_CATEGORY_MAP
)

# Optional google-genai SDK import
try:
    from google import genai
    HAS_GENAI_SDK = True
except ImportError:
    HAS_GENAI_SDK = False


# =====================================================================
# 1. ADK Sub-Agent: AllergyExtractorAgent
# =====================================================================
class AllergyExtractorAgent:
    """
    ADK Sub-Agent specialized in analyzing natural language prompts
    and emitting structured food allergy categories (Gluten, Dairy, Nuts).
    """

    SYSTEM_INSTRUCTION = """
    You are an ADK Sub-Agent specializing in food allergy intent extraction.
    Analyze the input text and extract any mentioned food allergies.
    Categorize into:
    - Gluten (includes wheat, celiac, bread, flour)
    - Dairy (includes milk, cheese, lactose, butter, cream)
    - Nuts (includes peanuts, tree nuts, almonds, walnuts)
    Output ONLY a JSON object: {"allergies": ["Gluten", "Dairy", "Nuts"]}
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "")

    def run(self, prompt: str) -> List[str]:
        """Executes the sub-agent loop to emit extracted allergies."""
        if self.api_key and HAS_GENAI_SDK:
            try:
                client = genai.Client(api_key=self.api_key)
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=f"{self.SYSTEM_INSTRUCTION}\n\nUser Input: \"{prompt}\"",
                    config={"response_mime_type": "application/json"}
                )
                data = json.loads(response.text)
                return [a.title() for a in data.get("allergies", []) if a.title() in ["Gluten", "Dairy", "Nuts"]]
            except Exception:
                pass

        if self.api_key:
            try:
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={self.api_key}"
                payload = {
                    "contents": [{"parts": [{"text": f"{self.SYSTEM_INSTRUCTION}\n\nUser Input: \"{prompt}\""}]}],
                    "generationConfig": {"responseMimeType": "application/json"}
                }
                req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"), headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=3) as resp:
                    result = json.loads(resp.read().decode("utf-8"))
                    text_out = result["candidates"][0]["content"]["parts"][0]["text"]
                    data = json.loads(text_out)
                    return [a.title() for a in data.get("allergies", []) if a.title() in ["Gluten", "Dairy", "Nuts"]]
            except Exception:
                pass

        # ADK Deterministic Fallback Agent Logic
        clean_text = prompt.lower()
        extracted = []
        if any(w in clean_text for w in ["gluten", "wheat", "celiac", "bread", "bun", "flour"]):
            extracted.append("Gluten")
        if any(w in clean_text for w in ["dairy", "milk", "cheese", "lactose", "cream", "butter"]):
            extracted.append("Dairy")
        if any(w in clean_text for w in ["nut", "nuts", "peanut", "peanuts", "tree nut", "almond", "walnut"]):
            extracted.append("Nuts")
        return extracted


# =====================================================================
# 2. ADK Primary Agent: McDonaldsAllergenAgent
# =====================================================================
class AllergenAgent:
    """
    ADK Main Orchestrator Agent that delegates allergy intent extraction
    to AllergyExtractorAgent, executes simple table tools, and formulates safety verdicts.
    """

    SYSTEM_INSTRUCTION = """
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

    def __init__(self, data_path: Optional[str] = None):
        self.data_path = data_path
        self.api_key = os.environ.get("GEMINI_API_KEY", "")
        self.extractor_subagent = AllergyExtractorAgent(api_key=self.api_key)
        self.session_history: List[Dict[str, str]] = []

    def process_query(self, prompt: str, user_allergies: List[str]) -> Dict[str, Any]:
        """
        ADK Agentic Pipeline:
        1. Delegate allergy intent extraction to AllergyExtractorAgent.
        2. Merge emitted allergies with user UI selections.
        3. Parse menu items, generic categories, or safe recommendations.
        4. Read simple table dataset via tools and compute safety verdict.
        """
        self.session_history.append({"role": "user", "content": prompt})

        # Step 1: Delegate to AllergyExtractorAgent sub-agent
        subagent_emitted_allergies = self.extractor_subagent.run(prompt)

        # Step 2: Combine UI toggles and sub-agent emitted allergies
        combined_set = set([a.strip().title() for a in user_allergies if a.strip()])
        combined_set.update(subagent_emitted_allergies)
        normalized_allergies = list(combined_set)

        clean_prompt = prompt.lower()
        words = clean_prompt.replace("?", "").replace("!", "").replace(",", "").split()

        dataset = load_allergen_dataset(self.data_path) if self.data_path else load_allergen_dataset()
        matched_item = None

        # Step 3: Match specific menu item
        for item in dataset:
            if item["name"].lower() in clean_prompt or item["item_id"].lower() in clean_prompt:
                matched_item = item["name"]
                break

        # Step 4: Evaluate specific item if matched
        if matched_item:
            evaluation = evaluate_allergen_safety(matched_item, normalized_allergies, data_path=self.data_path) if self.data_path else evaluate_allergen_safety(matched_item, normalized_allergies)
            response_text = self._format_evaluation_response(evaluation)
            result = {
                "prompt": prompt,
                "adk_subagent_emitted_allergies": subagent_emitted_allergies,
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

        # Step 5: Evaluate generic categories if matched
        for word in words:
            if word in GENERIC_CATEGORY_MAP:
                cat_eval = evaluate_category_safety(word, normalized_allergies, data_path=self.data_path) if self.data_path else evaluate_category_safety(word, normalized_allergies)
                if cat_eval:
                    response_text = self._format_category_response(cat_eval, normalized_allergies)
                    badge = "✅ SAFE CATEGORY" if cat_eval["unsafe_count"] == 0 else "ℹ️ CATEGORY BREAKDOWN"
                    result = {
                        "prompt": prompt,
                        "adk_subagent_emitted_allergies": subagent_emitted_allergies,
                        "user_allergies": normalized_allergies,
                        "status": "CATEGORY",
                        "safety_badge": badge,
                        "response": response_text,
                        "category_details": cat_eval,
                        "disclaimer": "Warning: McDonald's kitchen operations involve shared preparation areas. Cross-contact may occur."
                    }
                    self.session_history.append({"role": "assistant", "content": response_text})
                    return result

        # Step 6: Safe items recommendation
        if "safe" in clean_prompt or "what can i eat" in clean_prompt or "recommend" in clean_prompt or "options" in clean_prompt:
            safe_items = search_safe_items(normalized_allergies, data_path=self.data_path) if self.data_path else search_safe_items(normalized_allergies)
            response_text = self._format_safe_items_response(safe_items, normalized_allergies)
            
            result = {
                "prompt": prompt,
                "adk_subagent_emitted_allergies": subagent_emitted_allergies,
                "user_allergies": normalized_allergies,
                "status": "RECOMMENDATION",
                "safety_badge": "ℹ️ RECOMMENDATION",
                "response": response_text,
                "safe_items_count": len(safe_items),
                "disclaimer": "Warning: McDonald's kitchen operations involve shared preparation areas. Cross-contact may occur."
            }
            self.session_history.append({"role": "assistant", "content": response_text})
            return result

        # Step 7: Unknown query fallback
        response_text = f"❓ UNKNOWN ITEM: I couldn't identify a specific item or menu category in your query ('{prompt}'). Please try asking about specific items like 'Big Mac', 'Egg McMuffin', 'World Famous Fries', or generic menu categories like 'burgers', 'shakes', 'breakfast', or ask 'What can I eat?'."
        result = {
            "prompt": prompt,
            "adk_subagent_emitted_allergies": subagent_emitted_allergies,
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
