"""
McDonald's Allergen Agent Human-in-the-Loop (HITL) Confirmation Hooks
----------------------------------------------------------------------
Provides explicit HITL confirmation hooks for high-risk allergen warnings,
severe allergy alerts, and cross-contamination acknowledgements.
"""

import time
from typing import List, Dict, Any, Optional

# Pending in-memory HITL confirmation tokens
_PENDING_CONFIRMATONS: Dict[str, Dict[str, Any]] = {}


class HITLConfirmationManager:
    """Manages Human-in-the-Loop (HITL) confirmation hooks and user acknowledgements."""

    def evaluate_hitl_requirement(
        self,
        status: str,
        item_name: Optional[str],
        user_allergies: List[str],
        matched_allergens: List[str]
    ) -> Dict[str, Any]:
        """
        Determines whether a response requires explicit Human-in-the-Loop confirmation.

        Args:
            status (str): Verdict status ('UNSAFE', 'SAFE', 'CATEGORY', 'UNKNOWN').
            item_name (str, optional): Target item name.
            user_allergies (List[str]): User active allergies.
            matched_allergens (List[str]): Matched trigger allergens.

        Returns:
            Dict[str, Any]: HITL requirement metadata including token and confirmation message.
        """
        # Trigger HITL confirmation hook for UNSAFE items or Nut allergy queries
        requires_confirmation = (status == "UNSAFE") or ("Nuts" in user_allergies)

        if not requires_confirmation:
            return {
                "requires_human_confirmation": False,
                "hitl_status": "NOT_REQUIRED"
            }

        token = f"hitl_{int(time.time() * 1000)}"
        confirmation_data = {
            "requires_human_confirmation": True,
            "confirmation_token": token,
            "hitl_status": "PENDING_USER_ACKNOWLEDGEMENT",
            "action_type": "CONFIRM_ALLERGEN_SAFETY_WARNING",
            "item_name": item_name or "Menu Item",
            "matched_allergens": matched_allergens,
            "confirmation_prompt": f"⚠️ Human Confirmation Required: Please confirm you have reviewed the ingredient details and cross-contamination warning for {item_name or 'this menu item'}."
        }

        _PENDING_CONFIRMATONS[token] = confirmation_data
        return confirmation_data

    def confirm_hitl_action(self, token: str) -> Dict[str, Any]:
        """
        Processes a Human-in-the-Loop user confirmation acknowledgement.

        Args:
            token (str): The HITL confirmation token.

        Returns:
            Dict[str, Any]: Resolved confirmation status.
        """
        if token in _PENDING_CONFIRMATONS:
            record = _PENDING_CONFIRMATONS.pop(token)
            record["hitl_status"] = "CONFIRMED_BY_USER"
            record["confirmed_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            return record

        return {
            "requires_human_confirmation": False,
            "hitl_status": "INVALID_OR_EXPIRED_TOKEN",
            "token": token
        }


# Global Singleton HITL Manager
hitl_manager = HITLConfirmationManager()
