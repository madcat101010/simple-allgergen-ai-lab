"""
Unit tests for Structured Telemetry, OpenTelemetry Tracing, and PII Redaction (src/telemetry.py)
"""

import unittest
from src.telemetry import TelemetryManager, PIIRedactorFilter, OpenTelemetrySpan


class TestTelemetryAndPIIRedaction(unittest.TestCase):
    def setUp(self):
        self.telemetry = TelemetryManager()

    def test_pii_redaction_filter(self):
        filter_obj = PIIRedactorFilter()

        # Email redaction test
        email_input = "Contact customer at john.doe@example.com for allergy query."
        redacted_email = filter_obj.redact_text(email_input)
        self.assertNotIn("john.doe@example.com", redacted_email)
        self.assertIn("[REDACTED_EMAIL]", redacted_email)

        # Phone number redaction test
        phone_input = "Call emergency contact at 555-123-4567 immediately."
        redacted_phone = filter_obj.redact_text(phone_input)
        self.assertNotIn("555-123-4567", redacted_phone)
        self.assertIn("[REDACTED_PHONE]", redacted_phone)

        # Nested dictionary data redaction test
        data = {
            "user_email": "alice@test.com",
            "phone": "800-555-0199",
            "safe_field": "Big Mac"
        }
        redacted_dict = filter_obj.redact_data(data)
        self.assertEqual(redacted_dict["user_email"], "[REDACTED_EMAIL]")
        self.assertEqual(redacted_dict["phone"], "[REDACTED_PHONE]")
        self.assertEqual(redacted_dict["safe_field"], "Big Mac")

    def test_opentelemetry_span_generation(self):
        span = OpenTelemetrySpan(name="TestSpan", trace_id="1234567890abcdef1234567890abcdef")
        span.set_attribute("item", "Egg McMuffin")
        span.add_event("tool_call", {"status": "SUCCESS"})

        span_data = span.finish()
        self.assertEqual(span_data["name"], "TestSpan")
        self.assertEqual(len(span_data["trace_id"]), 32)
        self.assertEqual(len(span_data["span_id"]), 16)
        self.assertTrue(span_data["w3c_traceparent"].startswith("00-"))
        self.assertIn("01", span_data["w3c_traceparent"])

    def test_record_trace_with_intent_outcome_tracking(self):
        trace = self.telemetry.record_trace(
            prompt="Is Big Mac safe for john.doe@example.com?",
            user_allergies=["Gluten"],
            status="UNSAFE",
            evaluated_item="Big Mac",
            user_intent="INTENT_EVALUATE_ALLERGEN_SAFETY"
        )

        # Assert PII prompt was redacted
        self.assertNotIn("john.doe@example.com", trace["prompt"])
        self.assertIn("[REDACTED_EMAIL]", trace["prompt"])

        # Assert intent-outcome tracking
        self.assertEqual(trace["user_intent"], "INTENT_EVALUATE_ALLERGEN_SAFETY")
        self.assertEqual(trace["final_outcome"], "OUTCOME_UNSAFE")

        # Assert OpenTelemetry spans attached
        self.assertGreater(len(trace["opentelemetry_spans"]), 0)
        self.assertIn("w3c_traceparent", trace)


if __name__ == "__main__":
    unittest.main()
