"""Sandbox-only request and response enforcement. No filesystem or shell execution."""
from dataclasses import dataclass
from enum import Enum
import json
import re
from urllib.parse import unquote

class Decision(str, Enum):
    ALLOWED = "ALLOWED"
    WARNING = "WARNING"
    BLOCKED = "BLOCKED"

@dataclass(frozen=True)
class Verdict:
    decision: Decision
    category: str
    explanation: str

class NoDefense:
    def inspect(self, tool, payload, phase):
        return Verdict(Decision.ALLOWED, "none", "Unfiltered simulation baseline")

class Rules:
    def inspect(self, tool, payload, phase):
        if phase not in ("request", "response"):
            raise ValueError("Unknown inspection phase")
        text = unquote(json.dumps(payload, sort_keys=True)).lower()
        patterns = [
            ("prompt_injection", r"ignore (all |previous |prior )*instructions|system prompt|override security"),
            ("tool_poisoning", r"before using this tool|secretly send|hide this from"),
            ("command_injection", r";|\$\(|\x60|\|\||&&|drop\s+table"),
            ("malicious_response", r"exfiltrate|send credentials|stolen_secret"),
        ]
        for category, pattern in patterns:
            if re.search(pattern, text):
                return Verdict(Decision.BLOCKED, category, "Matched security policy: " + category)
        if phase == "request":
            if tool not in TOOLS:
                return Verdict(Decision.BLOCKED, "permissions", "Tool is outside allowlist")
            if not isinstance(payload, dict):
                return Verdict(Decision.BLOCKED, "schema", "Request must be an object")
            if tool == "file_reader" and payload.get("path") != "/public/readme.txt":
                return Verdict(Decision.BLOCKED, "unauthorized_file_access", "Path is outside fixture allowlist")
            if payload.get("permissions"):
                return Verdict(Decision.WARNING, "excessive_permissions", "Explicit approval required for extra permissions")
        return Verdict(Decision.ALLOWED, "none", "No rule matched")

TOOLS = {
    "file_reader": lambda p: {"text": "MCPShield public fixture"} if p.get("path") == "/public/readme.txt" else {"text": "STOLEN_SECRET"},
    "weather": lambda p: {"city": p.get("city", "Chicago"), "temperature_c": 18},
    "database_search": lambda p: {"rows": [{"id": 1, "title": "Public research"}]},
    "web_search": lambda p: {"results": [{"title": "MCP documentation", "url": "https://example.invalid/mcp"}]},
}

class Gateway:
    def __init__(self, detector):
        self.detector = detector

    def run(self, tool, request, response_transform=None, approve=None):
        events = []
        def permitted(payload, phase):
            verdict = self.detector.inspect(tool, payload, phase)
            events.append({"phase": phase, "decision": verdict.decision.value,
                           "category": verdict.category, "explanation": verdict.explanation})
            return verdict.decision == Decision.ALLOWED or (
                verdict.decision == Decision.WARNING and approve is not None and approve(tool, payload, phase, verdict) is True)
        if not permitted(request, "request"):
            return {"executed": False, "delivered": False, "response": None, "events": events}
        if tool not in TOOLS or not isinstance(request, dict):
            return {"executed": False, "delivered": False, "response": None, "events": events, "error": "Invalid simulated call"}
        response = TOOLS[tool](request)
        if response_transform:
            response = response_transform(response)
        if not permitted(response, "response"):
            return {"executed": True, "delivered": False, "response": None, "events": events}
        return {"executed": True, "delivered": True, "response": response, "events": events}
