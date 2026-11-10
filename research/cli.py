"""Offline Phase 2A CLI. No training, downloads, tool execution or API calls."""
import argparse
from collections import Counter
import json
from pathlib import Path
from .data import digest, validate, split_development, verify_splits
from .observations import build_observation, canonical
from .pilot import generate
from .reviews import export_review, import_review, review_status, disagreement_report

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def write_new(path, value):
    """Idempotent regeneration, but never overwrite changed evidence/review history."""
    path = Path(path)
    raw = (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()
    if path.exists():
        if path.read_bytes() != raw:
            raise ValueError("Refusing to overwrite different artifact: " + str(path))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(raw)


def prepare_rows(dataset, manifest, historical, ledger, split="train"):
    """No fitting. Keep X and y separate; refuse unresolved human labels."""
    if split not in {"train", "validation"}:
        raise ValueError("Final test is not accessible through the training preparation API")
    verify_splits(dataset, manifest, historical)
    status = review_status(dataset, ledger)
    features, targets = [], []
    for episode in sorted(dataset["episodes"], key=lambda e: e["id"]):
        if manifest["assignments"][episode["id"]] != split:
            continue
        for i in range(len(episode["events"])):
            reviewed = status[(episode["id"], i)]
            if reviewed["status"] != "AGREED_ATTESTED":
                raise ValueError("Two agreeing independent human attestations per boundary required; adjudicate conflicts")
            features.append(build_observation(episode, i))
            targets.append(reviewed["label"]["decision"])
    if not features:
        raise ValueError("No eligible reviewed examples")
    return features, targets


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    make = sub.add_parser("generate")
    make.add_argument("--output", default="data/research/phase2a-pilot-v1.json")
    make.add_argument("--manifest", default="data/research/phase2a-splits-v1.json")
    make.add_argument("--historical", default="data/generated/scenarios-v2.json")
    make.add_argument("--reservation", default="data/research/final-test-reservation.json")
    make.add_argument("--seed", type=int, default=23)
    export = sub.add_parser("review-export")
    export.add_argument("--reviewer", required=True)
    export.add_argument("--show-proposals", action="store_true")
    export.add_argument("--output", required=True)
    ingest = sub.add_parser("review-import")
    ingest.add_argument("--form", required=True)
    ingest.add_argument("--ledger", required=True, help="Existing version (use [] for the first)")
    ingest.add_argument("--output", required=True, help="New append-only ledger version")
    status_parser = sub.add_parser("status")
    status_parser.add_argument("--ledger")
    conflicts = sub.add_parser("review-report")
    conflicts.add_argument("--ledger", required=True)
    conflicts.add_argument("--output", required=True)
    prepare = sub.add_parser("prepare")
    prepare.add_argument("--ledger", required=True)
    prepare.add_argument("--manifest", default="data/research/phase2a-splits-v1.json")
    prepare.add_argument("--historical", default="data/generated/scenarios-v2.json")
    prepare.add_argument("--split", choices=("train", "validation"), default="train")
    prepare.add_argument("--output", required=True, help="New output directory")
    for command in (export, ingest, status_parser, prepare, conflicts):
        command.add_argument("--dataset", default="data/research/phase2a-pilot-v1.json")
    args = parser.parse_args(argv)
    try:
        if args.command == "generate":
            dataset = generate()
            historical = read(args.historical)
            manifest = split_development(dataset, historical, args.seed, read(args.reservation))
            write_new(args.output, dataset)
            write_new(args.manifest, manifest)
            print(json.dumps({"episodes": len(dataset["episodes"]), "boundaries": sum(len(e["events"]) for e in dataset["episodes"]),
                              "dataset_sha256": digest(dataset), "splits": manifest["counts"],
                              "final_test": manifest["final_test"]["status"], "training": "NOT RUN"}))
            return 0
        dataset = read(args.dataset)
        validate(dataset)
        if args.command == "review-export":
            write_new(args.output, export_review(dataset, args.reviewer, args.show_proposals))
        elif args.command == "review-import":
            write_new(args.output, import_review(dataset, read(args.ledger), read(args.form)))
        elif args.command == "status":
            ledger = read(args.ledger) if args.ledger else []
            counts = Counter(v["status"] for v in review_status(dataset, ledger).values())
            print(json.dumps({"review_counts": dict(counts), "training": "NOT RUN", "drl": "NOT RUN",
                              "scientific_validation": "PENDING", "review_identity": "self-attested, not authenticated"}))
        elif args.command == "review-report":
            write_new(args.output, disagreement_report(dataset, read(args.ledger)))
        elif args.command == "prepare":
            x, y = prepare_rows(dataset, read(args.manifest), read(args.historical), read(args.ledger), args.split)
            destination = Path(args.output)
            if destination.exists():
                raise ValueError("Preparation output directory must be new")
            write_new(destination / "features.json", x)
            write_new(destination / "targets.json", y)
            write_new(destination / "manifest.json", {"dataset_sha256": digest(dataset), "split": args.split,
                      "features_sha256": digest(x), "targets_sha256": digest(y), "ledger_sha256": digest(read(args.ledger)),
                      "training": "NOT RUN", "examples": len(y), "review_identity": "self-attested"})
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.exit(2, "Phase 2A: " + str(exc) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
