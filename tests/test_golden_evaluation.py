"""
Automated Golden Dataset Evaluation Test Suite (tests/test_golden_evaluation.py)
----------------------------------------------------------------------------------
Runs the GoldenDatasetEvaluator harness against data/golden_evaluation_dataset.json
and asserts >90% accuracy benchmark.
"""

import unittest
from src.evaluator import GoldenDatasetEvaluator


class TestGoldenDatasetBenchmark(unittest.TestCase):
    def setUp(self):
        self.evaluator = GoldenDatasetEvaluator()

    def test_golden_dataset_benchmark(self):
        """Asserts that agent achieves >90% accuracy against ground-truth golden dataset."""
        report = self.evaluator.run_evaluation()

        self.assertGreaterEqual(
            report["accuracy_rate_percent"],
            90.0,
            f"Expected benchmark accuracy >= 90%, got {report['accuracy_rate_percent']}%"
        )
        self.assertEqual(
            report["disclaimer_compliance_percent"],
            100.0,
            "Medical disclaimer compliance must be 100%"
        )


if __name__ == "__main__":
    unittest.main()
