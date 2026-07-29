"""
McDonald's Allergen Agent CLI & Agent API Integration
------------------------------------------------------
Provides a command-line interface (CLI) for interacting with the McDonald's Allergen Agent,
executing queries, viewing traces, confirming HITL tokens, and running golden evaluation benchmarks.

Usage:
  python3 src/cli.py chat "Is a Big Mac safe for me?" --allergies Gluten,Dairy
  python3 src/cli.py evaluate
  python3 src/cli.py menu
  python3 src/cli.py traces
  python3 src/cli.py confirm-hitl <token>
"""

import argparse
import json
import sys
import os

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.agent import AllergenAgent
from src.evaluator import GoldenDatasetEvaluator
from src.telemetry import telemetry
from src.tools import load_allergen_dataset
from src.hitl import hitl_manager


def main():
    parser = argparse.ArgumentParser(
        prog="mcdonalds-allergen-agent",
        description="McDonald's Allergen AI Agent CLI & Agent API Interface"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available Agent CLI Commands")

    # Command: chat
    chat_parser = subparsers.add_parser("chat", help="Ask the Allergen Agent a natural language question")
    chat_parser.add_argument("prompt", type=str, help="User prompt or question (e.g. 'Is a Big Mac safe?')")
    chat_parser.add_argument("--allergies", type=str, default="Gluten,Dairy,Nuts", help="Comma-separated list of active user allergies (default: Gluten,Dairy,Nuts)")
    chat_parser.add_argument("--session-id", type=str, default="cli_session", help="Session ID for persistent conversation context")

    # Command: evaluate
    subparsers.add_parser("evaluate", help="Run the Golden Dataset Benchmark Evaluation Suite")

    # Command: menu
    subparsers.add_parser("menu", help="Inspect harvested simple table dataset records")

    # Command: traces
    subparsers.add_parser("traces", help="View recent OpenTelemetry execution traces")

    # Command: confirm-hitl
    hitl_parser = subparsers.add_parser("confirm-hitl", help="Confirm a Human-in-the-Loop warning acknowledgement token")
    hitl_parser.add_argument("token", type=str, help="HITL confirmation token string")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "chat":
        allergies_list = [a.strip() for a in args.allergies.split(",") if a.strip()]
        agent = AllergenAgent()
        result = agent.process_query(args.prompt, allergies_list, session_id=args.session_id)
        
        print("\n" + "=" * 60)
        print(f"🤖 MCDONALD'S ALLERGEN AGENT RESPONSE ({result['status']})")
        print("=" * 60)
        print(f"User Prompt: {result['prompt']}")
        print(f"Allergies Checked: {', '.join(result['user_allergies'])}\n")
        print(result["response"])
        print("=" * 60)
        
        if result.get("hitl_confirmation", {}).get("requires_human_confirmation"):
            hitl = result["hitl_confirmation"]
            print(f"\n⚠️ HITL CONFIRMATION REQUIRED!")
            print(f"Token: {hitl['confirmation_token']}")
            print(f"Action: python3 src/cli.py confirm-hitl {hitl['confirmation_token']}\n")

    elif args.command == "evaluate":
        evaluator = GoldenDatasetEvaluator()
        evaluator.run_evaluation()

    elif args.command == "menu":
        data = load_allergen_dataset()
        print(f"\n[+] Total Menu Items in Simple Table File: {len(data)}\n")
        for item in data:
            allergens = ", ".join(item["allergens"]) or "None listed"
            print(f"- [{item['item_id']}] {item['name']} ({item['category']}) -> Allergens: {allergens}")

    elif args.command == "traces":
        recent = telemetry.get_recent_traces(10)
        print(f"\n[+] Recent OpenTelemetry Execution Traces ({len(recent)}):\n")
        print(json.dumps(recent, indent=2))

    elif args.command == "confirm-hitl":
        res = hitl_manager.confirm_hitl_action(args.token)
        print(f"\n[+] HITL Confirmation Result: {res['hitl_status']}")
        print(json.dumps(res, indent=2))


if __name__ == "__main__":
    main()
