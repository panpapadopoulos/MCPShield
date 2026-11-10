"""New comparison interfaces; historical experiments are not imported or rewritten."""
from .sequential import ACTIONS, rollout
from shield.core import Rules

METHODS = ("no_defense", "rules", "pretrained_qwen", "supervised", "drl")


def rules_policy(observation):
    current = observation["current"]
    payload = {**current["arguments"], "_tool_description": current["description"]} if current["phase"] == "request" else current["response"]
    verdict = Rules().inspect(current["tool"], payload, current["phase"])
    return ACTIONS.index(verdict.decision.value)


def diagnostic_comparison(policies=None, *, seeds=(11, 23, 37)):
    """Optional synthetic diagnostics only; NOT a dataset/model efficacy study.

    Learned/model policies are opt-in objects supplied by the caller. Each receives
    the same allowlisted observation and the same external authorization arbiter.
    """
    supplied = {"no_defense": lambda observation: 0, "rules": rules_policy, **(policies or {})}
    if set(supplied) - set(METHODS):
        raise ValueError("Unknown research comparison method")
    methods = {}
    for name in METHODS:
        if name not in supplied:
            methods[name] = {"status": "NOT RUN", "reason": "No explicitly supplied model/policy"}
            continue
        records = []
        for seed in seeds:
            for variant in ("clean", "poisoned", "consent", "unauthorized"):
                result = rollout(supplied[name], seed=seed, options={"variant": variant})
                records.append({"seed": seed, "fixture_variant": variant, **result})
        methods[name] = {"status": "SYNTHETIC_DIAGNOSTIC_ONLY", "records": records}
    return {"evidence_kind": "synthetic_environment_checks", "methods": methods,
            "mandatory_authorization": "Same independent arbiter for every method; no_defense means authorization-only",
            "classification_metrics": "NOT RUN: no independently reviewed phase labels for these fixtures",
            "historical_undefended_baseline": "Unchanged in shield.experiments"}
