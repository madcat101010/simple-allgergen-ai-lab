"""
McDonald's Allergen Agent Multi-Model Router
-------------------------------------------
Dynamically routes agent tasks to different models based on task complexity:
- Fast / Low Complexity (e.g., single item lookup, intent extraction): gemini-2.5-flash
- High Complexity / Deep Reasoning (e.g., multi-allergy evaluation, cross-contamination analysis): gemini-2.5-pro
"""

import os
from typing import List, Dict, Any


class ModelRouter:
    """Dynamic model selection router based on query complexity."""

    MODEL_FLASH = "gemini-2.5-flash"
    MODEL_PRO = "gemini-2.5-pro"

    def select_model(self, prompt: str, user_allergies: List[str]) -> Dict[str, Any]:
        """
        Evaluates task complexity and returns optimal model selection.

        Args:
            prompt (str): User prompt text.
            user_allergies (List[str]): List of active food allergies.

        Returns:
            Dict[str, Any]: Dictionary containing model_name, complexity_tier, and reasoning.
        """
        clean_prompt = prompt.lower()
        complexity_score = 0

        # Multi-allergy requests increase complexity
        if len(user_allergies) > 1:
            complexity_score += 2

        # Complex reasoning keywords (e.g., cross-contamination, severe, ingredients breakdown)
        complex_keywords = ["severe", "anaphylaxis", "cross-contamination", "shared fryer", "oil", "ingredients", "compare"]
        for kw in complex_keywords:
            if kw in clean_prompt:
                complexity_score += 2

        # Multiple items mentioned in prompt
        if "and" in clean_prompt or "or" in clean_prompt or len(clean_prompt.split()) > 10:
            complexity_score += 1

        if complexity_score >= 3:
            return {
                "model_name": self.MODEL_PRO,
                "complexity_tier": "HIGH_COMPLEXITY_DEEP_REASONING",
                "complexity_score": complexity_score,
                "reasoning": "High complexity query requiring deep multi-allergy reasoning & ingredient verification."
            }
        else:
            return {
                "model_name": self.MODEL_FLASH,
                "complexity_tier": "LOW_COMPLEXITY_FAST_LOOKUP",
                "complexity_score": complexity_score,
                "reasoning": "Standard lookup query routed to high-speed Flash model."
            }


# Global Singleton Model Router
model_router = ModelRouter()
