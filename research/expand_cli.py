"""Generate the next development collection, quality report and blank review packs."""
import argparse
import hashlib
from pathlib import Path
from .cli import read, write_new
from .data import split_development, verify_splits, digest
from .expansion import generate
from .quality import report, markdown
from .reviews import export_review


def write_text_new(path, text):
    path = Path(path)
    raw = text.encode("utf-8")
    if path.exists():
        if path.read_bytes() != raw:
            raise ValueError("Refusing to overwrite different artifact: " + str(path))
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(raw)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", default="data/raw/mcpcorpus_servers.json")
    parser.add_argument("--corpus-manifest", default="data/raw/manifest.json")
    parser.add_argument("--historical", default="data/generated/scenarios-v2.json")
    parser.add_argument("--reservation", default="data/research/final-test-reservation.json")
    parser.add_argument("--dataset", default="data/generated/research-expansion-v3.json")
    parser.add_argument("--output", default=".local/research-phase2/expansion-v3-package")
    args = parser.parse_args(argv)
    try:
        historical = read(args.historical)
        dataset = generate(args.raw, args.corpus_manifest, historical)
        manifest = split_development(dataset, historical, seed=23, reservation=read(args.reservation))
        verify_splits(dataset, manifest, historical)
        quality = report(dataset, manifest)
        destination = Path(args.output)
        instructions = (Path(__file__).resolve().parents[1] / "docs/REVIEW_GUIDELINES.md").read_text(encoding="utf-8")
        write_new(args.dataset, dataset)
        write_new(destination / "splits.json", manifest)
        write_new(destination / "quality.json", quality)
        write_text_new(destination / "quality.md", markdown(quality))
        write_new(destination / "reviews-0.json", [])
        for reviewer in ("reviewer-A", "reviewer-B"):
            write_new(destination / reviewer / "review.json", export_review(dataset, reviewer, opaque_ids=True))
            write_text_new(destination / reviewer / "INSTRUCTIONS.md", instructions)
        write_new(destination / "artifact-manifest.json", {"dataset_sha256": digest(dataset),
            "splits_sha256": digest(manifest), "quality_sha256": digest(quality),
            "reviewer_instructions_sha256": hashlib.sha256(instructions.encode()).hexdigest(),
            "reviews": "UNREVIEWED", "training": "NOT RUN", "final_test": manifest["final_test"]["status"]})
        print(f"{quality['episodes']} episodes / {quality['decision_boundaries']} boundaries; "
              f"{quality['real_metadata_repositories']} metadata repositories; all labels UNREVIEWED. "
              f"Quality and blind review packages: {destination}")
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.exit(2, "Research expansion: " + str(exc) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
