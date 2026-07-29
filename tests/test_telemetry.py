"""
Unit tests for Telemetry & Observability (src/telemetry.py)
"""

import unittest
from src.telemetry import TelemetryManager


class TestTelemetryManager(unittest.TestCase):
    def setUp(self):
        self.telemetry = TelemetryManager(max_buffer_size=5)

    def test_record_trace(self):
        trace = self.telemetry.record_trace(
            prompt="Is Big Mac safe?",
            user_allergies=["Gluten"],
            status="UNSAFE",
            evaluated_item="Big Mac",
            execution_time_ms=12.5,
            tool_calls=[{"tool": "evaluate_allergen_safety"}]
        )

        self.assertIn("trace_id", trace)
        self.assertEqual(trace["status"], "UNSAFE")
        self.assertEqual(len(self.telemetry.get_recent_traces()), 1)

    def test_ring_buffer_limit(self):
        for i in range(10):
            self.telemetry.record_trace(
                prompt=f"Query {i}",
                user_allergies=["Dairy"],
                status="SAFE",
                evaluated_item="Coca-Cola",
                execution_time_ms=5.0,
                tool_calls=[]
            )

        traces = self.telemetry.get_recent_traces()
        self.assertEqual(len(traces), 5)
        self.assertEqual(traces[0]["prompt"], "Query 9")


if __name__ == "__main__":
    unittest.main()
