"""
McDonald's Allergen Agent Golden Dataset Evaluator & Benchmark Runner
----------------------------------------------------------------------
Evaluates the AllergenAgent against ground-truth golden benchmark dataset
(`data/golden_evaluation_dataset.json`) and outputs precision, recall, accuracy,
and latency metrics.
"""

import json
import os
import sys
import time
from typing import Dict, Any, List

# Ensure project root in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.agent import AllergenAgent

GOLDEN_DATASET_PATH = os.path.join(PROJECT_ROOT, "data", "golden_evaluation_dataset.json")
REPORT_OUTPUT_PATH = os.path.join(PROJECT_ROOT, "logs", "golden_eval_report.json")


class GoldenDatasetEvaluator:
    """Evaluation framework for benchmark accuracy, recall, and compliance."""

    def __init__(self, dataset_path: str = GOLDEN_DATASET_PATH):
        self.dataset_path = dataset_path
        self.agent = AllergenAgent()

    def run_evaluation(self) -> Dict[str, Any]:
        """
        Runs full benchmark suite against golden dataset.

        Returns:
            Dict[str, Any]: Evaluation summary report with accuracy, recall, and latency metrics.
        """
        if not os.path.exists(self.dataset_path):
            raise FileNotFoundError(f"Golden evaluation dataset missing at {self.dataset_path}")

        with open(self.dataset_path, "r", encoding="utf-8") as f:
            test_cases = json.load(f)

        results = []
        passed_cases = 0
        disclaimer_compliant_cases = 0
        total_latencies = []

        print(f"\n[+] Starting Golden Dataset Evaluation Benchmark ({len(test_cases)} cases)...")
        print("=" * 70)

        for case in test_cases:
            test_id = case["test_id"]
            prompt = case["prompt"]
            allergies = case["user_allergies"]
            exp_status = case["expected_status"]
            exp_matched = case.get("expected_matched_allergens", [])

            start_time = time.time()
            res = self.agent.process_query(prompt, allergies, session_id=f"eval_{test_id}")
            latency_ms = round((time.time() - start_time) * 1000, 2)
            total_latencies.append(latency_ms)

            actual_status = res["status"]
            actual_response = res["response"]
            actual_matched = res.get("details", {}).get("matched_allergens", [])

            status_match = (actual_status == exp_status)
            disclaimer_match = ("Medical Disclaimer" in actual_response or "shared preparation areas" in actual_response)

            if disclaimer_match:
                disclaimer_compliant_cases += 1

            matched_match = True
            if exp_matched:
                for allergen in exp_matched:
                    if allergen not in actual_matched:
                        matched_match = False
                        break

            case_passed = status_match and matched_match and disclaimer_match
            if case_passed:
                passed_cases += 1

            status_icon = "✅ PASS" if case_passed else "❌ FAIL"
            print(f"{status_icon} [{test_id}] '{prompt}' -> Expected: {exp_status}, Got: {actual_status} ({latency_ms}ms)")

            results.append({
                "test_id": test_id,
                "description": case["description"],
                "passed": case_passed,
                "status_match": status_match,
                "disclaimer_compliant": disclaimer_match,
                "latency_ms": latency_ms,
                "expected": {"status": exp_status, "matched_allergens": exp_matched},
                "actual": {"status": actual_status, "matched_allergens": actual_matched}
            })

        print("=" * 70)
        accuracy_rate = round((passed_cases / len(test_cases)) * 100, 2)
        disclaimer_rate = round((disclaimer_compliant_cases / len(test_cases)) * 100, 2)
        avg_latency = round(sum(total_latencies) / len(total_latencies), 2)

        summary = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_test_cases": len(test_cases),
            "passed_cases": passed_cases,
            "failed_cases": len(test_cases) - passed_cases,
            "accuracy_rate_percent": accuracy_rate,
            "disclaimer_compliance_percent": disclaimer_rate,
            "average_latency_ms": avg_latency,
            "max_latency_ms": max(total_latencies),
            "min_latency_ms": min(total_latencies),
            "case_results": results
        }

        os.makedirs(os.path.dirname(REPORT_OUTPUT_PATH), exist_ok=True)
        with open(REPORT_OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2)

        print(f"🏆 Evaluation Complete! Accuracy: {accuracy_rate}% | Disclaimer Compliance: {disclaimer_rate}% | Avg Latency: {avg_latency}ms")
        print(f"[+] Detailed report saved to {REPORT_OUTPUT_PATH}\n")
        return summary


if __name__ == "__main__":
    evaluator = GoldenDatasetEvaluator()
    evaluator.run_evaluation()
