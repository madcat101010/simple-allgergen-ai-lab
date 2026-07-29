"""
McDonald's Allergen AI Agent Core Orchestration
------------------------------------------------
Implements Native LLM Function Calling, Dedicated Secret Manager, Multi-Model Routing,
Policy Guardrails with Self-Evaluation, HITL Confirmation Hooks, and Persistent Memory.
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
    format_tool_error,
    GENERIC_CATEGORY_MAP
)
from src.memory import memory_manager, SessionMemoryManager
from src.model_router import model_router
from src.guardrails import guardrails
from src.hitl import hitl_manager
from src.secret_manager import secret_manager

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
        self.api_key = api_key or secret_manager.get_secret("gemini-api-key")

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
    Main Orchestrator Agent featuring Dedicated Secret Manager, Multi-Model Routing, Native LLM Function Calling,
    Policy Guardrails with Self-Reflection, HITL Confirmation Hooks, and Persistent Memory.
    """

    SYSTEM_INSTRUCTION = """
    You are the official McDonald's Allergen Safety AI Assistant.
    Your primary mission is to protect customers with food allergies—specifically Gluten, Dairy, and/or Nut allergies—by analyzing McDonald's menu items against their specific allergy profile.

    NATIVE LLM TOOL CALLING & GUARDRAILS INSTRUCTIONS:
    1. ALWAYS call your declared tool functions (`evaluate_allergen_safety`, `evaluate_category_safety`, `search_safe_items`, `lookup_item_allergens`) to retrieve official menu data.
    2. NEVER guess or hallucinate allergen content or ingredients.
    3. If a tool returns status 'UNKNOWN', 'UNKNOWN_CATEGORY', or 'found: false', read and follow the returned `recovery_instructions` and `suggested_actions` to correct your execution path (e.g. try lookup_item_allergens with broader terms, evaluate_category_safety, or search_safe_items).
    4. MANDATORY MEDICAL DISCLAIMER: Always include a medical disclaimer in your final response warning that McDonald's kitchens use shared preparation areas, fryers, and equipment where cross-contact may occur.
    """

    def __init__(self, data_path: Optional[str] = None):
        self.data_path = data_path
        self.api_key = secret_manager.get_secret("gemini-api-key")
        self.extractor_subagent = AllergyExtractorAgent(api_key=self.api_key)
        self.memory = memory_manager
        self.router = model_router
        self.guardrails = guardrails
        self.hitl = hitl_manager

    def process_query(
        self,
        prompt: str,
        user_allergies: List[str],
        session_id: str = "default_session"
    ) -> Dict[str, Any]:
        """
        Orchestration pipeline:
        1. Evaluates multi-model routing based on query complexity.
        2. Extracts allergy intent via sub-agent.
        3. Executes LLM tool calling loop with selected model.
        4. Applies Policy Plugins & Self-Evaluation reflection.
        5. Computes Human-in-the-Loop (HITL) confirmation hooks.
        6. Appends to persistent session storage asynchronously.
        """
        model_selection = self.router.select_model(prompt, user_allergies)
        selected_model = model_selection["model_name"]

        session_state = self.memory.load_session(session_id)
        compacted_summary = session_state.get("compacted_summary", "")

        subagent_emitted_allergies = self.extractor_subagent.run(prompt)
        combined_set = set([a.strip().title() for a in user_allergies if a.strip()])
        combined_set.update(subagent_emitted_allergies)
        normalized_allergies = list(combined_set)

        result = None
        if self.api_key and HAS_GENAI_SDK:
            try:
                result = self._execute_native_llm_tool_loop(prompt, normalized_allergies, compacted_summary, selected_model)
                if result:
                    result["adk_subagent_emitted_allergies"] = subagent_emitted_allergies
            except Exception:
                pass

        if not result:
            result = self._execute_local_tool_loop(prompt, normalized_allergies, subagent_emitted_allergies)

        result["model_routing"] = model_selection

        result = self.guardrails.evaluate_and_reflect(result)

        matched_allergens = result.get("details", {}).get("matched_allergens", [])
        hitl_data = self.hitl.evaluate_hitl_requirement(
            status=result["status"],
            item_name=result.get("evaluated_item"),
            user_allergies=normalized_allergies,
            matched_allergens=matched_allergens
        )
        result["hitl_confirmation"] = hitl_data

        self.memory.append_turn_and_compact(
            session_id=session_id,
            user_prompt=prompt,
            assistant_response=result["response"],
            allergies=normalized_allergies
        )

        result["session_id"] = session_id
        result["compacted_summary"] = compacted_summary
        return result

    def _execute_native_llm_tool_loop(
        self,
        prompt: str,
        normalized_allergies: List[str],
        compacted_summary: str,
        model_name: str
    ) -> Optional[Dict[str, Any]]:
        """Executes LLM Tool Calling loop using the model selected by ModelRouter."""
        client = genai.Client(api_key=self.api_key)
        tool_list = [evaluate_allergen_safety, evaluate_category_safety, lookup_item_allergens, search_safe_items]

        context_prefix = f"Compacted History Summary: {compacted_summary}\n\n" if compacted_summary else ""
        chat_content = f"{self.SYSTEM_INSTRUCTION}\n{context_prefix}User Allergy Profile: {normalized_allergies}\nUser Query: \"{prompt}\""

        response = client.models.generate_content(
            model=model_name,
            contents=chat_content,
            config=types.GenerateContentConfig(
                tools=tool_list,
                temperature=0.2
            )
        )

        if response.function_calls:
            function_call = response.function_calls[0]
            func_name = function_call.name
            func_args = function_call.args

            if func_name in AVAILABLE_TOOLS:
                tool_fn = AVAILABLE_TOOLS[func_name]
                try:
                    tool_output = tool_fn(**func_args)
                except Exception as err:
                    tool_output = format_tool_error(func_name, str(err), func_args)

                status = tool_output.get("status", "UNKNOWN")
                safety_badge = tool_output.get("safety_badge", "❓ UNKNOWN")
                verdict = tool_output.get("verdict", tool_output.get("message", ""))

                if status in ["UNKNOWN", "UNKNOWN_CATEGORY", "ERROR"]:
                    recovery_instructions = tool_output.get("recovery_instructions", "")
                    response_text = f"### {safety_badge}: {tool_output.get('item_name', prompt)}\n\n**Verdict**: {verdict}\n\n**Path Recovery Guidance**: {recovery_instructions}\n\n> **Medical Disclaimer**: McDonald's kitchens use shared prep areas. Cross-contact may occur."
                else:
                    response_text = f"### {safety_badge}: {tool_output.get('item_name', prompt)}\n\n**Verdict**: {verdict}\n\n> **Medical Disclaimer**: McDonald's kitchens use shared prep areas. Cross-contact may occur."

                return {
                    "prompt": prompt,
                    "user_allergies": normalized_allergies,
                    "evaluated_item": tool_output.get("item_name", prompt),
                    "status": status,
                    "safety_badge": safety_badge,
                    "response": response_text,
                    "details": tool_output,
                    "recovery_instructions": tool_output.get("recovery_instructions"),
                    "suggested_actions": tool_output.get("suggested_actions"),
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
                if cat_eval and cat_eval.get("found", True) and "evaluations" in cat_eval:
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

        # Step 4: Error Recovery Fallback
        recovery = (
            f"Query '{prompt}' could not be matched to a known McDonald's menu item or food category. "
            "Path Recovery Instructions for AI Agent:\n"
            "1. Prompt the customer for a specific menu item name (e.g. 'Big Mac', 'Egg McMuffin', 'World Famous Fries').\n"
            "2. Try searching by generic category term (e.g. 'burgers', 'breakfast', 'fries', 'drinks').\n"
            "3. Execute `search_safe_items(user_allergies=...)` to retrieve menu items verified safe for customer's allergy profile."
        )
        response_text = f"❓ UNKNOWN ITEM: I couldn't identify a specific item or menu category in your query ('{prompt}'). Please try asking about specific items like 'Big Mac', 'Egg McMuffin', 'World Famous Fries', or generic menu categories like 'burgers', 'shakes', 'breakfast', or ask 'What can I eat?'."
        return {
            "prompt": prompt,
            "adk_subagent_emitted_allergies": subagent_emitted_allergies,
            "user_allergies": normalized_allergies,
            "status": "UNKNOWN",
            "safety_badge": "❓ UNKNOWN",
            "response": response_text,
            "recovery_instructions": recovery,
            "suggested_actions": [
                "Prompt customer for exact menu item name",
                "Execute search_safe_items for allergy profile recommendations",
                "Execute evaluate_category_safety for menu category analysis"
            ],
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
