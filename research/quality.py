"""Deterministic draft-data accounting, not effectiveness or human validation."""
from collections import Counter
from itertools import combinations
from .data import digest, validate, components, _descriptions, _near, _near_trace
from .observations import build_observation, canonical
from .reviews import review_status

BENIGN_CATEGORIES = {"none", "scope_ambiguity"}
AMBIGUOUS_CATEGORIES = {"ambiguous_instruction"}


def interpretation(categories):
    if any(c not in BENIGN_CATEGORIES | AMBIGUOUS_CATEGORIES for c in categories):
        return "proposed_malicious"
    if any(c in AMBIGUOUS_CATEGORIES for c in categories):
        return "proposed_ambiguous"
    return "proposed_legitimate"


def duplicate_pairs(dataset):
    episodes = sorted(dataset["episodes"], key=lambda e: e["id"])
    traces = {e["id"]: [build_observation(e, i)["current"] for i in range(len(e["events"]))] for e in episodes}
    pairs = []
    for a, b in combinations(episodes, 2):
        reasons = []
        if digest(traces[a["id"]]) == digest(traces[b["id"]]):
            reasons.append("exact_observable_trace")
        if any(x == y for x in _descriptions(a) for y in _descriptions(b)):
            reasons.append("exact_description")
        elif any(_near(x, y) for x in _descriptions(a) for y in _descriptions(b)):
            reasons.append("near_description_jaccard_0.80")
        if _near_trace(a, b):
            reasons.append("duplicate_or_near_interaction_content")
        if reasons:
            pairs.append({"episodes": [a["id"], b["id"]], "reasons": reasons})
    return pairs


def report(dataset, manifest, ledger=None):
    validate(dataset)
    episodes = dataset["episodes"]
    labels = [l for e in episodes for l in e["proposed_labels"]]
    pairs = duplicate_pairs(dataset)
    crossing = [p for p in pairs if len({manifest["assignments"][i] for i in p["episodes"]}) > 1]
    if crossing:
        raise ValueError("Duplicate-screened episodes cross development splits")
    source_records = {}
    for e in episodes:
        p = e["provenance"]
        if p["kind"] == "mcpcorpus_metadata_adaptation":
            source_records[str(p["record_id"])] = {k: p[k] for k in ("repository", "revision", "raw_sha256", "license")}
    partitions = {}
    for split in ("train", "validation"):
        es = [e for e in episodes if manifest["assignments"][e["id"]] == split]
        ls = [l for e in es for l in e["proposed_labels"]]
        partitions[split] = {"episodes": len(es), "boundaries": len(ls),
                             "decisions": dict(Counter(l["decision"] for l in ls)), "ready": False}
    return {"schema": "research-quality-v1", "dataset_version": dataset["version"], "dataset_sha256": digest(dataset),
            "episodes": len(episodes), "decision_boundaries": len(labels),
            "proposed_episode_balance": dict(Counter(interpretation([l["attack_category"] for l in e["proposed_labels"]]) for e in episodes)),
            "proposed_boundary_balance": dict(Counter(interpretation([l["attack_category"]]) for l in labels)),
            "proposed_decisions": dict(Counter(l["decision"] for l in labels)),
            "proposed_attack_categories": dict(Counter(l["attack_category"] for l in labels)),
            "tools": dict(Counter(event["tool"] for e in episodes for event in e["events"] if event["kind"] == "request")),
            "source_kinds": dict(Counter(e["provenance"]["kind"] for e in episodes)),
            "real_metadata_repositories": len({v["repository"] for v in source_records.values()}), "source_records": source_records,
            "authored_contexts_are_not_real_sources": True,
            "multi_call_episodes": sum(sum(x["kind"] == "request" for x in e["events"]) > 1 for e in episodes),
            "boundaries_with_prior_history": sum(i > 0 for e in episodes for i in range(len(e["events"]))),
            "components": components(dataset), "duplicate_analysis": {"pairs": pairs, "cross_split_pairs": crossing,
                "exact_trace_pairs": sum("exact_observable_trace" in p["reasons"] for p in pairs),
                "note": "Shared metadata is expected and grouped. Token similarity does not establish semantic independence."},
            "review_status": dict(Counter(v["status"] for v in review_status(dataset, ledger or []).values())),
            "partitions": partitions, "final_test": manifest["final_test"], "training": "NOT RUN", "drl": "NOT RUN",
            "ready_for_training": False,
            "limitations": ["All interactions and proposed labels are authored simulations, not real-world attacks or executed traces.",
                "Balance is inferred from draft category annotations, not human-reviewed intent or measured harm.",
                "Small purposive sample; repeated source descriptions and limited attack families.",
                "Prior pilot remains intact, but expanded grouping may change its development allocation.",
                "Source/fork and semantic-family adjudication remains a human responsibility.",
                "Snapshot license/reuse terms need review before redistributing source metadata.",
                "No authenticated independent labels or independently collected sealed final test yet."]}


def markdown(report):
    return "\n".join(["# Research expansion quality report", "", "DRAFT / UNREVIEWED; no training or effectiveness evaluation.", "",
        f"Episodes: {report['episodes']}; decision boundaries: {report['decision_boundaries']}; real metadata repositories: {report['real_metadata_repositories']}; multi-call episodes: {report['multi_call_episodes']}.", "",
        "## Proposed composition", "", "```json", canonical({k: report[k] for k in ("proposed_episode_balance", "proposed_boundary_balance", "proposed_decisions", "proposed_attack_categories", "source_kinds", "tools", "review_status", "partitions")}), "```", "",
        f"Exact observable-trace duplicate pairs: {report['duplicate_analysis']['exact_trace_pairs']}. Cross-split duplicate-screen pairs: {len(report['duplicate_analysis']['cross_split_pairs'])}. Full pair evidence and source provenance are in quality.json.", "",
        "Final test: " + report["final_test"]["status"] + ". Training readiness: NO.", "", "## Limitations", "",
        *["- " + item for item in report["limitations"]], ""])
