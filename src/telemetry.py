"""
Structured Telemetry, OpenTelemetry Distributed Tracing & PII Redaction
-------------------------------------------------------------------------
Implements standard library JSON structured logging, OpenTelemetry-compatible
span context tracing, intent-outcome tracking, and automatic PII redaction.
"""

import json
import logging
import os
import re
import secrets
import sys
import time
from typing import List, Dict, Any, Optional

LOGS_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "logs"
)
os.makedirs(LOGS_DIR, exist_ok=True)
TELEMETRY_LOG_FILE = os.path.join(LOGS_DIR, "agent_telemetry.jsonl")


class PIIRedactorFilter(logging.Filter):
    """
    Filter that automatically scans log message text and dictionary payloads,
    redacting personally identifiable information (PII) like emails, phone numbers, and SSNs.
    """

    EMAIL_REGEX = re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+')
    PHONE_REGEX = re.compile(r'\b(?:\+?1[-. ]?)?\(?\d{3}\)?[-. ]?\d{3}[-. ]?\d{4}\b')
    SSN_REGEX = re.compile(r'\b\d{3}-\d{2}-\d{4}\b')

    @classmethod
    def redact_text(cls, text: str) -> str:
        if not isinstance(text, str):
            return text
        text = cls.EMAIL_REGEX.sub("[REDACTED_EMAIL]", text)
        text = cls.PHONE_REGEX.sub("[REDACTED_PHONE]", text)
        text = cls.SSN_REGEX.sub("[REDACTED_PII]", text)
        return text

    @classmethod
    def redact_data(cls, data: Any) -> Any:
        if isinstance(data, str):
            return cls.redact_text(data)
        elif isinstance(data, dict):
            return {k: cls.redact_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [cls.redact_data(item) for item in data]
        return data

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = self.redact_text(record.msg)
        if hasattr(record, "telemetry_payload") and isinstance(record.telemetry_payload, dict):
            record.telemetry_payload = self.redact_data(record.telemetry_payload)
        return True


class StructuredJSONFormatter(logging.Formatter):
    """Formats Python logging records as structured JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(record.created)),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "funcName": record.funcName,
            "lineNo": record.lineno
        }

        if hasattr(record, "telemetry_payload"):
            log_entry["telemetry"] = record.telemetry_payload

        return json.dumps(log_entry)


class OpenTelemetrySpan:
    """Represents an individual OpenTelemetry-compatible tracing span."""

    def __init__(self, name: str, trace_id: str, parent_span_id: Optional[str] = None):
        self.name = name
        self.trace_id = trace_id
        self.span_id = secrets.token_hex(8)  # 16-char hex
        self.parent_span_id = parent_span_id
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.attributes: Dict[str, Any] = {}
        self.events: List[Dict[str, Any]] = []

    def set_attribute(self, key: str, value: Any) -> None:
        self.attributes[key] = PIIRedactorFilter.redact_data(value)

    def add_event(self, event_name: str, payload: Optional[Dict[str, Any]] = None) -> None:
        self.events.append({
            "name": event_name,
            "timestamp": time.time(),
            "payload": PIIRedactorFilter.redact_data(payload or {})
        })

    def finish(self) -> Dict[str, Any]:
        self.end_time = time.time()
        duration_ms = round((self.end_time - self.start_time) * 1000, 2)
        
        # W3C traceparent header: version-trace_id-span_id-trace_flags
        w3c_traceparent = f"00-{self.trace_id}-{self.span_id}-01"

        return {
            "name": self.name,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "w3c_traceparent": w3c_traceparent,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": duration_ms,
            "attributes": self.attributes,
            "events": self.events
        }


class TelemetryManager:
    """
    Central Telemetry & Distributed Tracing Manager.
    Logs structured JSON, captures OpenTelemetry spans, redacts PII, and tracks intent-outcomes.
    """

    def __init__(self, max_history: int = 50):
        self.max_history = max_history
        self.recent_traces: List[Dict[str, Any]] = []
        self.redactor = PIIRedactorFilter()

        # Configure standard library logger
        self.logger = logging.getLogger("mcdonalds_allergen_telemetry")
        self.logger.setLevel(logging.INFO)
        self.logger.addFilter(self.redactor)

        # File Handler (JSONL)
        fh = logging.FileHandler(TELEMETRY_LOG_FILE)
        fh.setFormatter(StructuredJSONFormatter())
        self.logger.addHandler(fh)

    def create_trace_context(self) -> Dict[str, str]:
        """Generates OpenTelemetry W3C trace IDs."""
        trace_id = secrets.token_hex(16)  # 32-char hex
        root_span_id = secrets.token_hex(8) # 16-char hex
        return {
            "trace_id": trace_id,
            "root_span_id": root_span_id,
            "w3c_traceparent": f"00-{trace_id}-{root_span_id}-01"
        }

    def record_trace(
        self,
        prompt: str,
        user_allergies: List[str],
        status: str,
        evaluated_item: Optional[str] = None,
        execution_time_ms: float = 0.0,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        details: Optional[Dict[str, Any]] = None,
        user_intent: str = "INTENT_EVALUATE_ALLERGEN_SAFETY",
        model_routing: Optional[Dict[str, Any]] = None,
        self_evaluation: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Records a complete telemetry trace trajectory with OpenTelemetry spans and PII redaction.
        """
        clean_prompt = self.redactor.redact_text(prompt)

        ctx = self.create_trace_context()
        trace_id = ctx["trace_id"]

        root_span = OpenTelemetrySpan("AllergenAgent.process_query", trace_id=trace_id)
        root_span.set_attribute("user.prompt", clean_prompt)
        root_span.set_attribute("user.allergies", user_allergies)
        root_span.set_attribute("intent", user_intent)
        root_span.set_attribute("outcome", f"OUTCOME_{status}")

        if model_routing:
            root_span.set_attribute("model_name", model_routing.get("model_name"))
            root_span.set_attribute("complexity_tier", model_routing.get("complexity_tier"))

        if self_evaluation:
            root_span.set_attribute("passed_self_eval", self_evaluation.get("passed_self_eval"))

        root_span_data = root_span.finish()

        trace_entry = {
            "trace_id": trace_id,
            "w3c_traceparent": ctx["w3c_traceparent"],
            "timestamp": time.time(),
            "iso_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "user_intent": user_intent,
            "final_outcome": f"OUTCOME_{status}",
            "prompt": clean_prompt,
            "user_allergies": user_allergies,
            "status": status,
            "evaluated_item": evaluated_item,
            "execution_time_ms": execution_time_ms,
            "opentelemetry_spans": [root_span_data],
            "tool_calls": self.redactor.redact_data(tool_calls or []),
            "details": self.redactor.redact_data(details or {})
        }

        self.recent_traces.insert(0, trace_entry)
        if len(self.recent_traces) > self.max_history:
            self.recent_traces.pop()

        extra = {"telemetry_payload": trace_entry}
        self.logger.info(f"Trace recorded - Intent: {user_intent} -> Outcome: OUTCOME_{status} ({execution_time_ms}ms)", extra=extra)

        return trace_entry

    def get_recent_traces(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Returns recent in-memory telemetry traces."""
        return self.recent_traces[:limit]


# Global Singleton Telemetry Manager
telemetry = TelemetryManager()
