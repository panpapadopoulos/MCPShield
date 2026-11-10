"""Validation, historical exclusion and reproducible development split manifests."""
from collections import Counter
import hashlib
import re
from urllib.parse import urlparse
from .observations import build_observation, canonical, authorized_task


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def validate(dataset):
    if dataset.get("schema") != "research-dataset-v1" or not dataset.get("episodes"):
        raise ValueError("Nonempty research-dataset-v1 required")
    ids = set()
    for episode in dataset["episodes"]:
        if episode.get("schema") != "research-episode-v1" or not episode.get("id") or episode["id"] in ids:
            raise ValueError("Invalid or duplicate episode ID")
        ids.add(episode["id"])
        authorized_task(episode["authorized"])
        provenance = episode["provenance"]
        for key in ("kind", "author", "generator", "origin", "template_group", "derivation_family", "license"):
            if not isinstance(provenance.get(key), str) or not provenance[key]:
                raise ValueError("Missing provenance: " + key)
        if not isinstance(provenance.get("source_groups"), list) or not provenance["source_groups"] or not isinstance(provenance.get("parent_ids"), list):
            raise ValueError("Explicit source and derivation provenance required")
        if any(not isinstance(x, str) or not x for x in provenance["source_groups"] + provenance["parent_ids"]):
            raise ValueError("Invalid provenance group")
        if provenance["kind"] == "mcpcorpus_metadata_adaptation":
            originals = provenance.get("original_tools")
            if not originals or provenance.get("original_tools_sha256") != digest(originals):
                raise ValueError("Missing or changed original tool metadata")
            if not all(provenance.get(k) for k in ("revision", "raw_sha256", "repository", "record_id", "adaptation")):
                raise ValueError("Immutable metadata provenance required")
        if type(episode.get("development_exposed")) is not bool:
            raise ValueError("Exposure status required")
        events = episode.get("events", [])
        labels = episode.get("proposed_labels", [])
        if not events or len(labels) != len(events):
            raise ValueError("Every decision boundary needs its own draft label")
        for i, label in enumerate(labels):
            build_observation(episode, i)
            if label.get("event_index") != i:
                raise ValueError("Labels must reference decision boundaries in order")
            validate_label(label)
    return True


def validate_label(label):
    if set(label) != {"event_index", "decision", "attack_category", "rationale"}:
        raise ValueError("Unexpected label fields")
    if type(label["event_index"]) is not int or label["event_index"] < 0:
        raise ValueError("Invalid label boundary")
    if label["decision"] not in {"ALLOWED", "WARNING", "BLOCKED"}:
        raise ValueError("Invalid label decision")
    if any(not isinstance(label[k], str) or not label[k].strip() for k in ("attack_category", "rationale")):
        raise ValueError("Labels need category and justification")


def historical_guard(dataset, historical):
    """Fail closed on known IDs/ancestry/sources and exact interaction reuse.

    Semantic paraphrase detection still needs human derivation review. This does
    not imply that lexical checks prove independent attack families.
    """
    if not historical:
        raise ValueError("Historical exclusion collection is mandatory")
    ids = {c["id"] for c in historical}
    sources = {_source_group(c["server"]) for c in historical}
    templates = {c.get("template") for c in historical}
    original_requests = []
    signatures = set()
    for case in historical:
        args = {k: v for k, v in case["request"].items() if k != "_tool_description"}
        if args:
            original_requests.append((case["tool"], args))
        signatures.add(digest([case["tool"], args]))
        if case.get("response") is not None:
            signatures.add(digest([case["tool"], args, case["response"]]))
    for episode in dataset["episodes"]:
        p = episode["provenance"]
        if {episode["id"], *p["parent_ids"]} & ids:
            raise ValueError("Historical ID or derivation cannot enter new training development")
        if p["template_group"] in templates or p["derivation_family"] in templates:
            raise ValueError("Historical template derivations belong in the regression collection")
        if {_source_group(x) for x in p["source_groups"]} & sources:
            raise ValueError("Historical source reuse needs a separate regression-only collection")
        for i in range(len(episode["events"])):
            current = build_observation(episode, i)["current"]
            signature = [current["tool"], {k: v for k, v in current["arguments"].items() if k != "_tool_description"}]
            if any(current["tool"] == tool and all(k in signature[1] and signature[1][k] == v for k, v in args.items())
                   for tool, args in original_requests):
                raise ValueError("Historical request reused with extra fields")
            if digest(signature) in signatures or (current["phase"] == "response" and digest(signature + [current["response"]]) in signatures):
                raise ValueError("Exact historical interaction reuse")


def _tokens(text):
    return set(re.findall(r"[\w]+", text.casefold()))


def _source_group(value):
    value = value.casefold().rstrip("/")
    parsed = urlparse(value if "://" in value else "https://" + value)
    if parsed.hostname in {"github.com", "www.github.com"}:
        return "github.com/" + "/".join(parsed.path.strip("/").removesuffix(".git").split("/")[:2])
    return value


def _descriptions(episode):
    return [e["description"] for e in episode["events"] if e["kind"] == "request" and e["description"].strip()]


def _near(a, b):
    x, y = _tokens(a), _tokens(b)
    return bool(x and y) and (x == y or len(x & y) / len(x | y) >= .8)


def _near_trace(a, b):
    """Conservative lexical content screen independent of tool descriptions.

    Match tool/phase sequence, then compare arguments/response tokens. Different
    task authorizations do not excuse a copied trace crossing development splits.
    """
    def trace(e):
        rows = [build_observation(e, i)["current"] for i in range(len(e["events"]))]
        return [(r["tool"], r["phase"]) for r in rows], canonical([
            {"arguments": r["arguments"], **({"response": r["response"]} if "response" in r else {})} for r in rows])
    shape_a, text_a = trace(a)
    shape_b, text_b = trace(b)
    return shape_a == shape_b and (_tokens(text_a) == _tokens(text_b) or
                                   (min(len(_tokens(text_a)), len(_tokens(text_b))) >= 8 and _near(text_a, text_b)))


def components(dataset):
    """Transitive union across sources/forks (curated source group), templates,
    derivation families, ancestry, descriptions and duplicate interaction traces.
    """
    validate(dataset)
    episodes = sorted(dataset["episodes"], key=lambda e: e["id"])
    parents = list(range(len(episodes)))

    def root(i):
        while parents[i] != i:
            parents[i] = parents[parents[i]]
            i = parents[i]
        return i

    def keys(e):
        p = e["provenance"]
        return {*("source:" + _source_group(s) for s in p["source_groups"]),
                "template:" + p["template_group"], "family:" + p["derivation_family"],
                "origin:" + p["origin"], "ancestor:" + e["id"],
                *("ancestor:" + s for s in p["parent_ids"])}

    for i, a in enumerate(episodes):
        for j, b in enumerate(episodes[:i]):
            # Match full observable traces as well as metadata descriptions.
            duplicate = digest([build_observation(a, k)["current"] for k in range(len(a["events"]))]) == digest([build_observation(b, k)["current"] for k in range(len(b["events"]))])
            if keys(a) & keys(b) or duplicate or _near_trace(a, b) or any(_near(x, y) for x in _descriptions(a) for y in _descriptions(b)):
                parents[root(i)] = root(j)
    groups = {}
    for i, episode in enumerate(episodes):
        groups.setdefault(root(i), []).append(episode["id"])
    return sorted(sorted(v) for v in groups.values())


def split_development(dataset, historical, seed=23, reservation=None):
    validate(dataset)
    historical_guard(dataset, historical)
    reservation = reservation or {"status": "NOT_COLLECTED", "source_groups": [],
                                  "template_groups": [], "derivation_families": [], "description_texts": []}
    if reservation.get("status") not in {"NOT_COLLECTED", "RESERVED_EXTERNAL"}:
        raise ValueError("Unknown final-test reservation status")
    if reservation["status"] == "RESERVED_EXTERNAL" and not all(reservation.get(k) for k in
            ("custodian", "commitment_sha256", "source_groups", "template_groups", "derivation_families")):
        raise ValueError("External reservation needs custody, commitment and exclusion groups")
    if reservation["status"] == "RESERVED_EXTERNAL" and not re.fullmatch(r"[0-9a-f]{64}", reservation["commitment_sha256"]):
        raise ValueError("Invalid sealed-test SHA-256 commitment")
    for episode in dataset["episodes"]:
        p = episode["provenance"]
        if {_source_group(s) for s in p["source_groups"]} & {_source_group(s) for s in reservation["source_groups"]} or p["template_group"] in reservation["template_groups"] or p["derivation_family"] in reservation["derivation_families"]:
            raise ValueError("Development content overlaps the reserved final test")
        if any(_near(x, y) for x in _descriptions(episode) for y in reservation.get("description_texts", [])):
            raise ValueError("Description overlaps reserved final test")
    groups = components(dataset)
    if len(groups) < 2:
        raise ValueError("Too few independent components; do not break leakage groups to fill splits")
    ordered = sorted(groups, key=lambda g: digest([seed, g]))
    n_val = max(1, round(len(ordered) * .2))
    assignments = {identifier: "validation" if i < n_val else "train"
                   for i, group in enumerate(ordered) for identifier in group}
    return {"schema": "research-splits-v1", "dataset_sha256": digest(dataset),
            "historical_sha256": digest(historical), "seed": seed, "components": groups,
            "assignments": assignments, "counts": dict(Counter(assignments.values())),
            "final_test": reservation,
            "scope": "Development allocation only; pilot exposed, unreviewed, not an independent final test"}


def verify_splits(dataset, manifest, historical):
    expected = split_development(dataset, historical, manifest["seed"], manifest["final_test"])
    if expected != manifest:
        raise ValueError("Split manifest altered or dataset/exclusion mismatch")
    return True
