"""
Unit tests for Multi-Model Router, Policy Guardrails with Self-Evaluation, and HITL Confirmation Hooks
"""

import unittest
from src.model_router import ModelRouter
from src.guardrails import SelfEvaluationEngine, MedicalDisclaimerPolicy, AllergenStrictnessPolicy
from src.hitl import HITLConfirmationManager


class TestOrchestrationComponents(unittest.TestCase):
    def setUp(self):
        self.router = ModelRouter()
        self.guardrails = SelfEvaluationEngine()
        self.hitl = HITLConfirmationManager()

    def test_model_router_low_vs_high_complexity(self):
        # Single allergy simple lookup -> Low complexity (gemini-2.5-flash)
        low = self.router.select_model("Can I eat fries?", ["Gluten"])
        self.assertEqual(low["model_name"], "gemini-2.5-flash")

        # Multi-allergy severe query -> High complexity (gemini-2.5-pro)
        high = self.router.select_model("Severe peanut allergy with cross-contamination risk and celiac gluten sensitivity", ["Gluten", "Dairy", "Nuts"])
        self.assertEqual(high["model_name"], "gemini-2.5-pro")

    def test_guardrails_medical_disclaimer_policy(self):
        policy = MedicalDisclaimerPolicy()
        response_without_disclaimer = "Big Mac contains Gluten."
        validated = policy.validate(response_without_disclaimer)
        self.assertIn("Medical Disclaimer", validated)

    def test_guardrails_self_evaluation_reflection(self):
        candidate_result = {
            "status": "SAFE",
            "safety_badge": "✅ SAFE",
            "response": "Big Mac is safe for you.",
            "details": {
                "status": "SAFE",
                "matched_allergens": ["Gluten / Wheat"]  # Contradiction: matched allergens but marked SAFE
            }
        }
        reflector_result = self.guardrails.evaluate_and_reflect(candidate_result)
        self.assertFalse(reflector_result["self_evaluation"]["passed_self_eval"])
        self.assertEqual(reflector_result["status"], "UNSAFE")  # Self-corrected to UNSAFE

    def test_hitl_confirmation_hook(self):
        hitl_req = self.hitl.evaluate_hitl_requirement(
            status="UNSAFE",
            item_name="Big Mac",
            user_allergies=["Gluten"],
            matched_allergens=["Gluten / Wheat"]
        )
        self.assertTrue(hitl_req["requires_human_confirmation"])
        self.assertEqual(hitl_req["hitl_status"], "PENDING_USER_ACKNOWLEDGEMENT")

        # Perform user confirmation
        token = hitl_req["confirmation_token"]
        confirm_res = self.hitl.confirm_hitl_action(token)
        self.assertEqual(confirm_res["hitl_status"], "CONFIRMED_BY_USER")


if __name__ == "__main__":
    unittest.main()
