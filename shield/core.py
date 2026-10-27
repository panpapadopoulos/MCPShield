"""Sandbox-only request and response enforcement. No filesystem or shell execution."""
from copy import deepcopy
from dataclasses import dataclass
from enum import Enum
import json
import re
from urllib.parse import unquote

POLICY_VERSION = "fixture-policy-v2"

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

class AccessPolicy:
    """Mandatory fixture access policy; independent of text heuristics."""
    def inspect(self, tool, payload, phase):
        if phase not in ("request", "response"):
            raise ValueError("Unknown inspection phase")
        if phase == "request":
            if tool not in TOOLS:
                return Verdict(Decision.BLOCKED, "permissions", "Tool is outside allowlist")
            if not isinstance(payload, dict):
                return Verdict(Decision.BLOCKED, "schema", "Request must be an object")
            if tool == "file_reader" and payload.get("path") != "/public/readme.txt":
                return Verdict(Decision.BLOCKED, "unauthorized_file_access", "Path is outside fixture allowlist")
            if payload.get("permissions"):
                return Verdict(Decision.WARNING, "excessive_permissions", "Explicit approval required for extra permissions")
        return None


class Rules:
    def inspect(self, tool, payload, phase):
        if phase not in ("request", "response"):
            raise ValueError("Unknown inspection phase")
        text = unquote(json.dumps(payload, sort_keys=True)).lower()
        patterns = [
            ("prompt_injection", r"ignore (all |previous |prior )*instructions|override security|(?:reveal|disclose|dump|print|repeat)\s+(?:the |your |hidden )*system prompt"),
            ("tool_poisoning", r"secretly send|hide this from"),
            ("command_injection", r";\s*(?:drop|rm|curl|sh|bash|powershell)\b|\$\(|\x60|\|\||&&|drop\s+table"),
            ("malicious_response", r"exfiltrate|send credentials|stolen_secret"),
        ]
        for category, pattern in patterns:
            if re.search(pattern, text):
                return Verdict(Decision.BLOCKED, category, "Matched security policy: " + category)
        policy = AccessPolicy().inspect(tool, payload, phase)
        if policy is not None:
            return policy
        if re.search(r"\bbefore using this tool\b", text):
            return Verdict(Decision.WARNING, "heuristic_context", "Tool-use prerequisite needs contextual review")
        return Verdict(Decision.ALLOWED, "none", "No rule matched")

TOOLS = {
    "file_reader": lambda p: {"text": "MCPShield public fixture"} if p.get("path") == "/public/readme.txt" else {"text": "STOLEN_SECRET"},
    "weather": lambda p: {"city": p.get("city", "Chicago"), "temperature_c": 18},
    "database_search": lambda p: {"rows": [{"id": 1, "title": "Public research"}]},
    "web_search": lambda p: {"results": [{"title": "MCP documentation", "url": "https://example.invalid/mcp"}]},
}

class Gateway:
    def __init__(self, detector, executor=None):
        self.detector = detector
        self.executor = executor or (lambda tool, request: TOOLS[tool](request))

    def transaction(self, tool, request, response_transform=None):
        """Yield immutable phase checkpoints; resume warnings only with explicit True.

        The generator retains the exact response and executor state across approval.
        Tool execution is never replayed when approving a response.
        """
        request = deepcopy(request)
        events = []
        executed = False
        response = None
        for phase in ("request", "response"):
            payload = request if phase == "request" else response
            error_code = None
            try:
                verdict = self.detector.inspect(tool, payload, phase)
                if not isinstance(verdict, Verdict) or not isinstance(verdict.decision, Decision):
                    raise ValueError("Invalid detector output")
            except Exception as exc:
                verdict = Verdict(Decision.BLOCKED, "detector_error", "Classification unavailable; execution denied")
                code = getattr(exc, "code", "detector_exception")
                error_code = code if code in {"not_configured", "unavailable", "timeout", "http_error", "transport_error", "output_limit", "invalid_output"} else "detector_exception"
            event = {"phase": phase, "decision": verdict.decision.value,
                     "category": verdict.category, "explanation": verdict.explanation}
            if error_code:
                event["error_code"] = error_code
            events.append(event)
            approved = yield {**event, "tool": tool, "payload": deepcopy(payload)}
            if verdict.decision == Decision.BLOCKED or (verdict.decision == Decision.WARNING and approved is not True):
                return {"executed": executed, "delivered": False, "response": None, "events": events}
            if phase == "request":
                if tool not in TOOLS or not isinstance(request, dict):
                    return {"executed": False, "delivered": False, "response": None, "events": events, "error": "Invalid simulated call"}
                executed = True
                try:
                    response = self.executor(tool, request)
                    if response_transform:
                        response = response_transform(response)
                    response = deepcopy(response)
                except Exception:
                    return {"executed": True, "delivered": False, "response": None, "events": events, "error": "Simulated tool failed"}
        return {"executed": True, "delivered": True, "response": response, "events": events}

    def run(self, tool, request, response_transform=None, approve=None):
        transaction = self.transaction(tool, request, response_transform)
        try:
            checkpoint = next(transaction)
            while True:
                accepted = False
                if checkpoint["decision"] == Decision.WARNING.value and approve is not None:
                    verdict = Verdict(Decision.WARNING, checkpoint["category"], checkpoint["explanation"])
                    accepted = approve(tool, checkpoint["payload"], checkpoint["phase"], verdict) is True
                checkpoint = transaction.send(accepted)
        except StopIteration as done:
            return done.value
