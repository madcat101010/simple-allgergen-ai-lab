"""
McDonald's Allergen AI Agent Core Orchestration (Native LLM Function Calling)
-----------------------------------------------------------------------------
Implements Native LLM Function Calling using Google Gemini API (`google-genai` SDK)
with explicit tool declarations, JSON parameter schemas, and LLM-guided error recovery.
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
    from google.genai import types
    HAS_GENAI_SDK = True
except ImportError:
    HAS_GENAI_SDK = False


# Tool definitions for LLM Function Calling
AVAILABLE_TOOLS = {
    "evaluate_allergen_safety": evaluate_allergen_safety,
    "evaluate_category_safety": evaluate_category_safety,
    "lookup_item_allergens": lookup_item_allergens,
    "search_safe_items": search_safe_items,
}


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
                    config=types.GenerateContentConfig(response_mime_type="application/json")
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

        # Deterministic Fallback Agent Logic
        clean_text = prompt.lower()
        extracted = []
        if any(w in clean_text for w in ["gluten", "wheat", "celiac", "bread", "bun", "flour"]):
            extracted.append("Gluten")
        if any(w in clean_text for w in ["dairy", "milk", "cheese", "lactose", "cream", "butter"]):
            extracted.append("Dairy")
        if any(w in clean_text for w in ["nut", "nuts", "peanut", "peanuts", "tree nut", "almond", "walnut"]):
            extracted.append("Nuts")
        return extracted


class AllergenAgent:
    """
    Main Orchestrator Agent featuring Native LLM Function Calling,
    explicit JSON tool schemas, and LLM-guided error recovery.
    """

    SYSTEM_INSTRUCTION = """
    You are the official McDonald's Allergen Safety AI Assistant.
    Your primary mission is to protect customers with food allergies—specifically Gluten, Dairy, and/or Nut allergies—by analyzing McDonald's menu items against their specific allergy profile.

    NATIVE LLM TOOL CALLING & ERROR RECOVERY INSTRUCTIONS:
    1. ALWAYS call your declared tool functions (`evaluate_allergen_safety`, `evaluate_category_safety`, `search_safe_items`, `lookup_item_allergens`) to retrieve official menu data.
    2. NEVER guess or hallucinate allergen content or ingredients.
    3. If a tool returns status 'UNKNOWN' (item not found), perform LLM-guided error recovery:
       - Attempt fuzzy lookup using `lookup_item_allergens`.
       - Or check category safety using `evaluate_category_safety`.
       - Or clearly explain to the user that the item was not found and suggest valid menu items.
    4. MANDATORY MEDICAL DISCLAIMER: Always include a medical disclaimer in your final response warning that McDonald's kitchens use shared preparation areas, fryers, and equipment where cross-contact may occur.
    """

    def __init__(self, data_path: Optional[str] = None):
        self.data_path = data_path
        self.api_key = os.environ.get("GEMINI_API_KEY", "")
        self.extractor_subagent = AllergyExtractorAgent(api_key=self.api_key)
        self.session_history: List[Dict[str, str]] = []

    def process_query(self, prompt: str, user_allergies: List[str]) -> Dict[str, Any]:
        """
        Processes user query using Native LLM Function Calling loop:
        1. Emits allergies via sub-agent.
        2. Executes LLM tool calling loop with Gemini Flash (or offline tool dispatch).
        3. Handles LLM-guided error recovery for unknown or ambiguous items.
        """
        self.session_history.append({"role": "user", "content": prompt})

        # 1. Extract allergies
        subagent_emitted_allergies = self.extractor_subagent.run(prompt)
        combined_set = set([a.strip().title() for a in user_allergies if a.strip()])
        combined_set.update(subagent_emitted_allergies)
        normalized_allergies = list(combined_set)

        # 2. Try Native LLM Function Calling if API key and SDK are available
        if self.api_key and HAS_GENAI_SDK:
            try:
                llm_result = self._execute_native_llm_tool_loop(prompt, normalized_allergies)
                if llm_result:
                    llm_result["adk_subagent_emitted_allergies"] = subagent_emitted_allergies
                    return llm_result
            except Exception as e:
                pass  # Fallback to local tool dispatch loop

        # 3. Local Tool Dispatch Loop (Ensures identical tool execution trajectory offline)
        return self._execute_local_tool_loop(prompt, normalized_allergies, subagent_emitted_allergies)

    def _execute_native_llm_tool_loop(self, prompt: str, normalized_allergies: List[str]) -> Optional[Dict[str, Any]]:
        """Executes LLM Tool Calling loop with Gemini Flash."""
        client = genai.Client(api_key=self.api_key)
        tool_list = [evaluate_allergen_safety, evaluate_category_safety, lookup_item_allergens, search_safe_items]

        # Call Gemini model with tools
        chat_content = f"{self.SYSTEM_INSTRUCTION}\nUser Allergy Profile: {normalized_allergies}\nUser Query: \"{prompt}\""
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=chat_content,
            config=types.GenerateContentConfig(
                tools=tool_list,
                temperature=0.2
            )
        )

        # Check if LLM requested function calls
        if response.function_calls:
            function_call = response.function_calls[0]
            func_name = function_call.name
            func_args = function_call.args

            if func_name in AVAILABLE_TOOLS:
                tool_fn = AVAILABLE_TOOLS[func_name]
                tool_output = tool_fn(**func_args)

                # Format LLM response
                response_text = f"### {tool_output.get('safety_badge', 'ℹ️ VERDICT')}: {tool_output.get('item_name', prompt)}\n\n**Verdict**: {tool_output.get('verdict', '')}\n\n> **Medical Disclaimer**: McDonald's kitchens use shared prep areas. Cross-contact may occur."

                return {
                    "prompt": prompt,
                    "user_allergies": normalized_allergies,
                    "evaluated_item": tool_output.get("item_name", prompt),
                    "status": tool_output.get("status", "UNKNOWN"),
                    "safety_badge": tool_output.get("safety_badge", "❓ UNKNOWN"),
                    "response": response_text,
                    "details": tool_output,
                    "disclaimer": tool_output.get("disclaimer", "Warning: Shared kitchen prep areas."),
                    "llm_function_call": {"name": func_name, "args": func_args}
                }
        return None

    def _execute_local_tool_loop(
        self,
        prompt: str,
        normalized_allergies: List[str],
        subagent_emitted_allergies: List[str]
    ) -> Dict[str, Any]:
        """Local tool dispatch loop supporting error recovery."""
        clean_prompt = prompt.lower()
        words = clean_prompt.replace("?", "").replace("!", "").replace(",", "").split()
        dataset = load_allergen_dataset(self.data_path) if self.data_path else load_allergen_dataset()

        # Step 1: Specific Item Match
        matched_item = None
        for item in dataset:
            if item["name"].lower() in clean_prompt or item["item_id"].lower() in clean_prompt:
                matched_item = item["name"]
                break

        if matched_item:
            evaluation = evaluate_allergen_safety(matched_item, normalized_allergies, data_path=self.data_path) if self.data_path else evaluate_allergen_safety(matched_item, normalized_allergies)
            response_text = self._format_evaluation_response(evaluation)
            return {
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

        # Step 2: Generic Category Match
        for word in words:
            if word in GENERIC_CATEGORY_MAP:
                cat_eval = evaluate_category_safety(word, normalized_allergies, data_path=self.data_path) if self.data_path else evaluate_category_safety(word, normalized_allergies)
                if cat_eval:
                    response_text = self._format_category_response(cat_eval, normalized_allergies)
                    badge = "✅ SAFE CATEGORY" if cat_eval["unsafe_count"] == 0 else "ℹ️ CATEGORY BREAKDOWN"
                    return {
                        "prompt": prompt,
                        "adk_subagent_emitted_allergies": subagent_emitted_allergies,
                        "user_allergies": normalized_allergies,
                        "status": "CATEGORY",
                        "safety_badge": badge,
                        "response": response_text,
                        "category_details": cat_eval,
                        "disclaimer": "Warning: McDonald's kitchen operations involve shared preparation areas. Cross-contact may occur."
                    }

        # Step 3: Safe Items Recommendation
        if "safe" in clean_prompt or "what can i eat" in clean_prompt or "recommend" in clean_prompt or "options" in clean_prompt:
            safe_items = search_safe_items(normalized_allergies, data_path=self.data_path) if self.data_path else search_safe_items(normalized_allergies)
            response_text = self._format_safe_items_response(safe_items, normalized_allergies)
            return {
                "prompt": prompt,
                "adk_subagent_emitted_allergies": subagent_emitted_allergies,
                "user_allergies": normalized_allergies,
                "status": "RECOMMENDATION",
                "safety_badge": "ℹ️ RECOMMENDATION",
                "response": response_text,
                "safe_items_count": len(safe_items),
                "disclaimer": "Warning: McDonald's kitchen operations involve shared preparation areas. Cross-contact may occur."
            }

        # Step 4: LLM-Guided Error Recovery (Item unknown fallback)
        response_text = f"❓ UNKNOWN ITEM: I couldn't identify a specific item or menu category in your query ('{prompt}'). Please try asking about specific items like 'Big Mac', 'Egg McMuffin', 'World Famous Fries', or generic menu categories like 'burgers', 'shakes', 'breakfast', or ask 'What can I eat?'."
        return {
            "prompt": prompt,
            "adk_subagent_emitted_allergies": subagent_emitted_allergies,
            "user_allergies": normalized_allergies,
            "status": "UNKNOWN",
            "safety_badge": "❓ UNKNOWN",
            "response": response_text,
            "disclaimer": "Warning: McDonald's kitchen operations involve shared preparation areas. Cross-contact may occur."
        }

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
