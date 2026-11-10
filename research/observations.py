"""Decision-time features only; no dependency on evaluator labels or split metadata."""
from copy import deepcopy
import json

OBSERVATION_VERSION = "mcp-observation-v1"
SEQUENTIAL_OBSERVATION_VERSION = "mcp-sequential-observation-v1"
MAX_HISTORY = 8
MAX_JSON_BYTES = 100_000


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False,
                      separators=(",", ":"))


def _text(value):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Expected nonempty text")
    return value


def authorized_task(task):
    """Task must originate from trusted app state, never a tool payload."""
    scope = task["scope"]
    result = {"task": _text(task["task"]), "scope": {}}
    if not isinstance(scope, dict) or not scope:
        raise ValueError("Explicit tool scopes required")
    for tool, grant in scope.items():
        _text(tool)
        result["scope"][tool] = {}
        for key in ("resources", "permissions", "consent_permissions"):
            items = grant.get(key, [])
            if not isinstance(items, list) or any(not isinstance(x, str) or not x for x in items):
                raise ValueError("Scope entries must be string lists")
            result["scope"][tool][key] = sorted(set(items))
    return result


def _request(event):
    args = event["arguments"]
    if not isinstance(args, dict):
        raise ValueError("Arguments must be a JSON object")
    permissions = args.get("permissions", [])
    if not isinstance(permissions, list) or any(not isinstance(x, str) for x in permissions):
        raise ValueError("Requested permissions must be strings")
    description = event["description"]
    if not isinstance(description, str):
        raise ValueError("Description must be text")
    return {"phase": "request", "tool": _text(event["tool"]),
            "description": description, "arguments": deepcopy(args),
            "requested_permissions": list(permissions)}


def build_observation(episode, event_index, max_history=MAX_HISTORY):
    """Project ONLY the observed prefix; future events are not even validated.

    Events are an observed trajectory, not a plan of future conditional executions.
    Labels, effects, IDs and provenance live beside it and are never projected.
    Raw tool JSON remains untrusted data, including label-like keys in actual text.
    """
    if type(event_index) is not int or not 0 <= event_index < len(episode["events"]):
        raise ValueError("Invalid decision boundary")
    if type(max_history) is not int or not 0 <= max_history <= MAX_HISTORY:
        raise ValueError("Invalid history bound")
    visible, calls = [], {}
    for event in episode["events"][:event_index + 1]:
        kind, ref = event["kind"], _text(event["call_ref"])
        if kind == "request":
            if ref in calls:
                raise ValueError("Call references cannot be reused")
            item = _request(event)
            calls[ref] = item
        elif kind == "response":
            if ref not in calls or calls[ref]["phase"] != "request":
                raise ValueError("Response needs exactly one prior request")
            item = {**deepcopy(calls[ref]), "phase": "response", "response": deepcopy(event["response"])}
            calls[ref] = item
        else:
            raise ValueError("Only actually observed request/response events supported in v1")
        visible.append(item)
    observation = {"schema": OBSERVATION_VERSION, "authorized": authorized_task(episode["authorized"]),
                   "current": visible[-1],
                   "history": visible[:-1][-max_history:] if max_history else [],
                   "history_omitted": max(0, len(visible) - 1 - max_history)}
    encoded = canonical(observation)  # Also rejects NaN and non-JSON values.
    if len(encoded.encode("utf-8")) > MAX_JSON_BYTES:
        raise ValueError("Observation exceeds size budget; no silent truncation")
    return json.loads(encoded)  # Detached plain JSON, usable by text/embedding/RL adapters.


def model_text(episode, event_index):
    return canonical(build_observation(episode, event_index))
