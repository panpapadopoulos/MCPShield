"""Independent constraints for future research adapters; no heuristic patterns.

This does not alter the historical Gateway. A new runtime must apply this arbiter
at every boundary using trusted grants before executing any detector decision.
"""
from copy import deepcopy
from .observations import authorized_task

DECISIONS = {"ALLOWED", "WARNING", "BLOCKED"}


def enforce(observation, recommendation):
    if recommendation not in DECISIONS:
        raise ValueError("Invalid detector recommendation")
    scope = authorized_task(observation["authorized"])["scope"]
    current = observation["current"]
    grant = scope.get(current["tool"])
    reason, required = None, None
    if grant is None:
        reason, required = "tool_not_authorized", "BLOCKED"
    elif current["tool"] == "file_reader" and current["arguments"].get("path") not in grant["resources"]:
        reason, required = "resource_not_authorized", "BLOCKED"
    else:
        extra = set(current["requested_permissions"]) - set(grant["permissions"])
        if extra - set(grant["consent_permissions"]):
            reason, required = "permission_not_grantable", "BLOCKED"
        elif extra:
            reason, required = "scoped_consent_required", "WARNING"
    rank = {"ALLOWED": 0, "WARNING": 1, "BLOCKED": 2}
    effective = max((recommendation, required or "ALLOWED"), key=rank.get)
    return {"recommended": recommendation, "effective": effective, "constraint": reason}


def grant_consent(authorized, tool, permissions):
    """Trusted consent handler only; UI acceptance cannot grant arbitrary scope."""
    result = deepcopy(authorized_task(authorized))
    grant = result["scope"].get(tool)
    if grant is None or not set(permissions) <= set(grant["consent_permissions"]):
        raise ValueError("Requested grant is outside consent scope")
    grant["permissions"] = sorted(set(grant["permissions"]) | set(permissions))
    return result
