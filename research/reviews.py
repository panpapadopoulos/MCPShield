"""Hash-bound, append-only human review records. No fabricated reviewers."""
from copy import deepcopy
from datetime import datetime, timezone
from .data import digest, validate_label


def export_review(dataset, reviewer, show_proposals=False, opaque_ids=False):
    if not isinstance(reviewer, str) or not reviewer.strip():
        raise ValueError("Reviewer identity required")
    items = []
    for episode in dataset["episodes"]:
        for label in episode["proposed_labels"]:
            item = {"episode_id": "review-" + digest(episode)[:16] if opaque_ids else episode["id"], "event_index": label["event_index"],
                    "episode_sha256": digest(episode), "authorized": deepcopy(episode["authorized"]),
                    "events": deepcopy(episode["events"]), "action": None,
                    "reviewed_label": None, "justification": ""}
            if show_proposals:
                item["proposed_label"] = deepcopy(label)
            items.append(item)
    return {"schema": "research-review-form-v1", "dataset_sha256": digest(dataset),
            "reviewer": reviewer, "human_attestation": False,
            "independent_attestation": False, "proposal_visible": show_proposals, "items": items}


def import_review(dataset, ledger, form):
    """Validate all entries before returning a new ledger; caller writes exclusively."""
    if form.get("schema") != "research-review-form-v1" or form.get("dataset_sha256") != digest(dataset):
        raise ValueError("Stale or incompatible review form")
    if form.get("human_attestation") is not True or form.get("independent_attestation") is not True:
        raise ValueError("Human and independent review attestations are required; never auto-fill")
    reviewer = form["reviewer"]
    if not isinstance(reviewer, str) or not reviewer.strip():
        raise ValueError("Reviewer required")
    validate_ledger(dataset, ledger)
    episodes = {e["id"]: e for e in dataset["episodes"]}
    output = deepcopy(ledger)
    seen = {(r["reviewer"], r["episode_id"], r["event_index"]) for r in ledger}
    if not form.get("items"):
        raise ValueError("Empty review import")
    for item in form["items"]:
        identifier = item["episode_id"]
        if identifier not in episodes:
            matches = [e for e in episodes.values() if "review-" + digest(e)[:16] == identifier]
            if len(matches) != 1:
                raise ValueError("Unknown or ambiguous opaque review identifier")
            episode = matches[0]
        else:
            episode = episodes[identifier]
        index = item["event_index"]
        if type(index) is not int or not 0 <= index < len(episode["events"]):
            raise ValueError("Unknown review boundary")
        original = episode["proposed_labels"][index]
        if reviewer == episode["provenance"]["author"] or item["episode_sha256"] != digest(episode):
            raise ValueError("Author self-review or stale episode")
        if item["authorized"] != episode["authorized"] or item["events"] != episode["events"]:
            raise ValueError("Review must display the original interaction and authorization unchanged")
        if form["proposal_visible"] and item.get("proposed_label") != original:
            raise ValueError("Review must preserve the original proposed label")
        key = (reviewer, episode["id"], index)
        if key in seen:
            raise ValueError("Duplicate review; use a new adjudication version instead of rewriting")
        seen.add(key)
        action = item["action"]
        if action == "accept" and not form["proposal_visible"]:
            raise ValueError("Blind reviewers must supply an independent label with modify, or reject")
        if action not in ("accept", "reject", "modify") or not isinstance(item["justification"], str) or not item["justification"].strip():
            raise ValueError("Accept/reject/modify and justification required")
        reviewed = deepcopy(original) if action == "accept" else deepcopy(item["reviewed_label"])
        if action == "reject":
            if reviewed is not None:
                raise ValueError("Use modify to supply a replacement label")
        else:
            validate_label(reviewed)
            if reviewed["event_index"] != index:
                raise ValueError("Review boundary mismatch")
        record = {"dataset_sha256": digest(dataset), "episode_sha256": digest(episode),
                  "episode_id": episode["id"], "event_index": index, "reviewer": reviewer,
                  "human_attestation": True, "independent_attestation": True,
                  "proposal_visible": bool(form["proposal_visible"]), "action": action,
                  "original_label": deepcopy(original), "reviewed_label": reviewed,
                  "justification": item["justification"],
                  "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                  "previous_sha256": digest(output[-1]) if output else None}
        record["record_sha256"] = digest(record)
        output.append(record)
    return output


def validate_ledger(dataset, ledger):
    episodes = {e["id"]: e for e in dataset["episodes"]}
    previous, seen = None, set()
    for record in ledger:
        if record.get("record_sha256") != digest({k: v for k, v in record.items() if k != "record_sha256"}):
            raise ValueError("Review record checksum mismatch")
        e = episodes[record["episode_id"]]
        i = record["event_index"]
        if type(i) is not int or not 0 <= i < len(e["events"]) or not isinstance(record["reviewer"], str) or not record["reviewer"].strip():
            raise ValueError("Invalid ledger identity or boundary")
        key = (record["reviewer"], e["id"], i)
        if key in seen or record["previous_sha256"] != previous or record["dataset_sha256"] != digest(dataset) or record["episode_sha256"] != digest(e) or record["original_label"] != e["proposed_labels"][i]:
            raise ValueError("Corrupt, duplicate or stale review ledger")
        if record["reviewer"] == e["provenance"]["author"] or record["human_attestation"] is not True or record["independent_attestation"] is not True:
            raise ValueError("Invalid reviewer attestation")
        if record["action"] not in {"accept", "reject", "modify"} or not record["justification"].strip():
            raise ValueError("Invalid review action")
        label = record["reviewed_label"]
        if record["action"] == "reject":
            if label is not None:
                raise ValueError("Rejected label must remain unresolved")
        else:
            validate_label(label)
            if label["event_index"] != i or (record["action"] == "accept" and label != record["original_label"]):
                raise ValueError("Corrupt reviewed label")
        previous = digest(record)
        seen.add(key)
    return True


def review_status(dataset, ledger):
    validate_ledger(dataset, ledger)
    status = {}
    for episode in dataset["episodes"]:
        for label in episode["proposed_labels"]:
            i = label["event_index"]
            rows = [r for r in ledger if r["episode_id"] == episode["id"] and r["event_index"] == i]
            values = {(r["reviewed_label"]["decision"], r["reviewed_label"]["attack_category"]) for r in rows if r["reviewed_label"] is not None}
            agreed = len(rows) >= 2 and len(values) == 1 and all(r["reviewed_label"] is not None for r in rows)
            status[(episode["id"], i)] = {"status": "AGREED_ATTESTED" if agreed else "UNREVIEWED" if not rows else "NEEDS_REVIEW_OR_ADJUDICATION",
                                         "label": rows[0]["reviewed_label"] if agreed else None}
    return status


def disagreement_report(dataset, ledger):
    """Expose unresolved votes for human adjudication; never manufacture consensus."""
    status = review_status(dataset, ledger)
    items = []
    for (identifier, index), result in status.items():
        if result["status"] != "NEEDS_REVIEW_OR_ADJUDICATION":
            continue
        rows = [r for r in ledger if r["episode_id"] == identifier and r["event_index"] == index]
        items.append({"episode_id": identifier, "event_index": index, "status": result["status"],
                      "votes": [{k: r[k] for k in ("reviewer", "action", "reviewed_label", "justification")} for r in rows]})
    return {"dataset_sha256": digest(dataset), "ledger_sha256": digest(ledger), "unresolved": items,
            "note": "Includes single reviews, disagreements and rejected/ambiguous items; human resolution required"}
