"""
McDonald's Allergen AI Agent Telemetry & Observability
------------------------------------------------------
Provides structured logging, execution latency metrics, tool call tracing,
and inspectable event history.
"""

import json
import logging
import os
import time
from typing import List, Dict, Any, Optional

LOGS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
TRACE_LOG_PATH = os.path.join(LOGS_DIR, "agent_traces.jsonl")


class TelemetryManager:
    """Manages structured event logging, tool call tracing, and metrics."""

    def __init__(self, max_buffer_size: int = 50):
        self.max_buffer_size = max_buffer_size
        self.recent_traces: List[Dict[str, Any]] = []
        os.makedirs(LOGS_DIR, exist_ok=True)
        
        # Configure standard python logger
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s"
        )
        self.logger = logging.getLogger("AllergenAgentTelemetry")

    def record_trace(
        self,
        prompt: str,
        user_allergies: List[str],
        status: str,
        evaluated_item: Optional[str],
        execution_time_ms: float,
        tool_calls: List[Dict[str, Any]],
        details: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Records a completed agent execution trajectory."""
        trace = {
            "trace_id": f"trace_{int(time.time() * 1000)}",
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "prompt": prompt,
            "user_allergies": user_allergies,
            "status": status,
            "evaluated_item": evaluated_item or "N/A",
            "execution_time_ms": execution_time_ms,
            "tool_calls": tool_calls,
            "details": details or {}
        }

        # Append to in-memory ring buffer
        self.recent_traces.append(trace)
        if len(self.recent_traces) > self.max_buffer_size:
            self.recent_traces.pop(0)

        # Log to file in JSONL format
        try:
            with open(TRACE_LOG_PATH, "a", encoding="utf-8") as f:
                f.write(json.dumps(trace) + "\n")
        except Exception as e:
            self.logger.warning(f"Failed to write trace log file: {e}")

        self.logger.info(f"Recorded trace {trace['trace_id']} - Status: {status} ({execution_time_ms}ms)")
        return trace

    def get_recent_traces(self) -> List[Dict[str, Any]]:
        """Returns recent in-memory trace history for observability UI."""
        return list(reversed(self.recent_traces))


# Global Singleton Telemetry Manager instance
telemetry = TelemetryManager()
