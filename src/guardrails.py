"""
McDonald's Allergen Agent Policy Guardrails & Self-Evaluation Engine
----------------------------------------------------------------------
Provides dedicated policy plugins and an autonomous self-evaluation /
self-correction reflection loop to guarantee safety compliance.
"""

from typing import List, Dict, Any, Optional


class MedicalDisclaimerPolicy:
    """Policy Plugin enforcing mandatory medical cross-contamination disclaimers."""

    DISCLAIMER_TEXT = "Warning: McDonald's kitchen operations involve shared preparation areas, fryers, and equipment. Cross-contact may occur."

    def validate(self, response_text: str) -> str:
        if "Medical Disclaimer" not in response_text and "shared preparation areas" not in response_text:
            return f"{response_text}\n\n> **Medical Disclaimer**: {self.DISCLAIMER_TEXT}"
        return response_text


class AllergenStrictnessPolicy:
    """Policy Plugin verifying strict safety logic compliance."""

    def validate(self, evaluation_details: Dict[str, Any]) -> Dict[str, Any]:
        if not evaluation_details:
            return {"valid": True}

        status = evaluation_details.get("status")
        matched = evaluation_details.get("matched_allergens", [])

        # Strict Policy Rule: If trigger allergens are matched, status MUST be UNSAFE
        if matched and status == "SAFE":
            evaluation_details["status"] = "UNSAFE"
            evaluation_details["safety_badge"] = "❌ UNSAFE"
            evaluation_details["verdict"] = f"UNSAFE: Policy guardrail overridden status to UNSAFE due to matched allergens: {', '.join(matched)}."
            return {"valid": False, "violation": "Status mismatch corrected to UNSAFE"}

        return {"valid": True}


class SelfEvaluationEngine:
    """
    Self-Evaluation & Self-Reflection Engine.
    Executes a verification pass over candidate responses before returning them to users.
    """

    def __init__(self):
        self.disclaimer_policy = MedicalDisclaimerPolicy()
        self.strictness_policy = AllergenStrictnessPolicy()

    def evaluate_and_reflect(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs self-reflection and policy plugins over generated result.

        Args:
            result (Dict[str, Any]): Candidate agent result dictionary.

        Returns:
            Dict[str, Any]: Verified and self-corrected agent result dictionary.
        """
        self_reflection = {
            "passed_self_eval": True,
            "policy_checks": [],
            "corrections_made": []
        }

        # 1. Check Strictness Policy
        details = result.get("details", {})
        policy_res = self.strictness_policy.validate(details)
        self_reflection["policy_checks"].append({"policy": "AllergenStrictnessPolicy", "passed": policy_res["valid"]})
        if not policy_res["valid"]:
            self_reflection["passed_self_eval"] = False
            self_reflection["corrections_made"].append(policy_res["violation"])
            result["status"] = details.get("status")
            result["safety_badge"] = details.get("safety_badge")

        # 2. Check Disclaimer Policy
        original_response = result.get("response", "")
        validated_response = self.disclaimer_policy.validate(original_response)
        if validated_response != original_response:
            result["response"] = validated_response
            self_reflection["corrections_made"].append("Appended mandatory medical disclaimer")

        self_reflection["verified_status"] = result.get("status")
        result["self_evaluation"] = self_reflection
        return result


# Global Singleton Guardrail Manager
guardrails = SelfEvaluationEngine()
