"""Public exclusion commitments only. Never reads or generates final-test examples."""
from .data import digest, validate, _source_group


def development_exclusions(dataset, historical):
    validate(dataset)
    return {"schema": "custodian-exclusions-v1", "development_sha256": digest(dataset),
            "historical_sha256": digest(historical),
            "source_groups": sorted({_source_group(s) for e in dataset["episodes"] for s in e["provenance"]["source_groups"]} |
                                    {_source_group(c["server"]) for c in historical}),
            "template_groups": sorted({e["provenance"]["template_group"] for e in dataset["episodes"]} |
                                      {c["template"] for c in historical}),
            "derivation_families": sorted({e["provenance"]["derivation_family"] for e in dataset["episodes"]}),
            "description_fingerprints": sorted({digest(e["description"].casefold()) for x in dataset["episodes"] for e in x["events"] if e["kind"] == "request"}),
            "semantic_review": "Custodian must independently check forks, near duplicates and related derivations; new names are not new families."}


def _sha(value):
    return isinstance(value, str) and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def register_seal(exclusions, seal):
    """Accept custodian-supplied metadata only, not labels or examples."""
    required = {"schema", "custodian", "reviewers", "payload_sha256", "labels_sha256", "reviews_sha256",
                "exclusions_sha256", "source_groups", "template_groups", "derivation_families",
                "sealed_utc", "independent_collection_attested", "semantic_separation_attested"}
    if set(seal) != required or seal["schema"] != "custodian-seal-v1":
        raise ValueError("Only the defined custody metadata is accepted; do not supply final examples")
    if not seal["custodian"] or len(set(seal["reviewers"])) < 2 or seal["custodian"] in seal["reviewers"]:
        raise ValueError("Separate custodian and two distinct independent reviewers required")
    if any(not _sha(seal[k]) for k in ("payload_sha256", "labels_sha256", "reviews_sha256", "exclusions_sha256")) or seal["exclusions_sha256"] != digest(exclusions):
        raise ValueError("Missing or stale content commitments")
    if seal["independent_collection_attested"] is not True or seal["semantic_separation_attested"] is not True:
        raise ValueError("Actual custodian attestations required")
    for key in ("source_groups", "template_groups", "derivation_families"):
        values = seal[key]
        if not isinstance(values, list) or not values or any(not isinstance(v, str) or not v for v in values):
            raise ValueError("Nonempty exclusion groups required")
        normalize = _source_group if key == "source_groups" else lambda v: v
        if {normalize(v) for v in values} & {normalize(v) for v in exclusions[key]}:
            raise ValueError("Final collection overlaps development exclusion groups")
    from datetime import datetime
    if datetime.fromisoformat(seal["sealed_utc"]).utcoffset() is None:
        raise ValueError("Timezone-aware sealing timestamp required")
    return {"status": "SEALED_ATTESTED_NOT_INSPECTED", "seal_sha256": digest(seal),
            "development_sha256": exclusions["development_sha256"],
            "exclusions_sha256": digest(exclusions), "identity": "External verification required; not cryptographically authenticated"}


def release_gate(exclusions, seal, freeze, *, approved=False):
    """No reading final data. Only verifies preconditions for a future release."""
    receipt = register_seal(exclusions, seal)
    if approved is not True:
        raise PermissionError("Final-test release needs explicit authorization after model/protocol freeze")
    if set(freeze) != {"model_sha256", "protocol_sha256", "development_sha256", "seal_sha256", "frozen_utc"}:
        raise ValueError("Freeze model, evaluation protocol, data and exact seal")
    if not all(_sha(freeze[k]) for k in ("model_sha256", "protocol_sha256", "development_sha256", "seal_sha256")):
        raise ValueError("Invalid freeze commitment")
    if freeze["development_sha256"] != exclusions["development_sha256"] or freeze["seal_sha256"] != receipt["seal_sha256"]:
        raise ValueError("Freeze does not match sealed collection")
    from datetime import datetime
    sealed, frozen = datetime.fromisoformat(seal["sealed_utc"]), datetime.fromisoformat(freeze["frozen_utc"])
    if frozen.utcoffset() is None or frozen < sealed:
        raise ValueError("Collection must be sealed before model-selection freeze")
    return {**receipt, "status": "RELEASE_AUTHORIZED_METADATA_ONLY", "freeze_sha256": digest(freeze),
            "note": "Custodian must release/verify bytes and keep an access log; this tool has not accessed test examples"}
