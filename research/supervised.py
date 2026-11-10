"""Reviewed-data supervised interfaces. Optional SetFit backend is never imported at load time."""
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from importlib.metadata import version, PackageNotFoundError
import argparse
import hashlib
import json
import os
from pathlib import Path
import random
from .cli import read, write_new, prepare_rows
from .data import digest
from .observations import OBSERVATION_VERSION, build_observation, canonical

LABELS = ("ALLOWED", "WARNING", "BLOCKED")
CLASSIFICATION_TARGET = {
    "version": "normative-boundary-decision-v1",
    "timing": "Recommendation before mandatory authorization enforcement",
    "ALLOWED": "Benign operation/content consistent with the trusted task and scope",
    "WARNING": "Concrete unresolved risk or a consentable permission requiring approval",
    "BLOCKED": "Unsafe instruction/content or operation outside authorized scope",
    "limits": "BLOCKED is not synonymous with a malicious actor; labels describe this boundary, not future hidden effects"
}
REPRESENTATION_VERSION = "canonical-windowed-document-v2"


@dataclass(frozen=True)
class ModelConfig:
    model_id: str = "sentence-transformers/all-MiniLM-L6-v2"
    seed: int = 11
    batch_size: int = 8
    body_learning_rate: float = 2e-5
    epochs: int = 1
    head_c: float = 1.0
    max_iter: int = 1000
    max_tokens: int = 256
    max_steps: int = 64

    def validate(self):
        if type(self.seed) is not int or self.seed < 0 or self.batch_size < 1 or self.epochs < 1 or not 0 < self.body_learning_rate < 1 or self.head_c <= 0 or self.max_tokens < 8 or type(self.max_steps) is not int or self.max_steps<1:
            raise ValueError("Invalid model configuration")


def load_partitions(dataset, splits, historical, ledger):
    """No IDs, provenance or evaluator fields in X; y is returned separately."""
    partitions = {}
    for split in ("train", "validation"):
        x, y = prepare_rows(dataset, splits, historical, ledger, split)
        partitions[split] = {"text": [canonical(observation) for observation in x], "label": y}
    if set(partitions["train"]["text"]) & set(partitions["validation"]["text"]):
        raise ValueError("Identical model observations cross partitions")
    for split in partitions:
        if set(partitions[split]["label"]) != set(LABELS):
            raise ValueError("All three classes need support in train and validation")
    if any(partitions["train"]["label"].count(label) < 2 for label in LABELS):
        raise ValueError("Contrastive training requires at least two examples per class")
    return partitions


def load_encoded_partitions(dataset, splits, historical, ledger, encoder=None):
    """Matched-representation control for a future supervised head versus PPO.

    Still requires real agreeing reviews. The encoder has no fit operation and
    never sees targets. This prepares vectors only; it does not train a model.
    """
    from .encoding import HashEncoder
    encoder = encoder or HashEncoder()
    partitions = load_partitions(dataset, splits, historical, ledger)
    return {name: {"features": [encoder.encode(json.loads(text)) for text in rows["text"]],
                   "labels": list(rows["label"]), "encoder": encoder.config()}
            for name, rows in partitions.items()}


def readiness_report(dataset, splits, historical, ledger):
    """Count actual reconciled support; never count proposed labels or train."""
    from collections import Counter
    from .data import verify_splits
    from .reviews import review_status
    verify_splits(dataset,splits,historical)
    status=review_status(dataset,ledger)
    counts={name:{label:0 for label in LABELS} for name in ('train','validation')}
    states=Counter()
    for (identifier,index),item in status.items():
        states[item['status']]+=1
        if item['status']=='AGREED_ATTESTED':
            counts[splits['assignments'][identifier]][item['label']['decision']]+=1
    support=all(counts['train'][label]>=2 and counts['validation'][label]>=1 for label in LABELS)
    resolved=states['AGREED_ATTESTED']==len(status)
    return {'classification_target':CLASSIFICATION_TARGET,'review_states':dict(states),
        'reviewed_support':counts,'all_boundaries_reconciled':resolved,'three_class_minimum_support':support,
        'minimum_support_scope':'2 train and1 validation per class are software minima, not evidence of statistical adequacy',
        'data_gates_pass':resolved and support,'training':'NOT RUN; custody and explicit approval still required',
        'dataset_sha256':digest(dataset),'splits_sha256':digest(splits),'reviews_sha256':digest(ledger),
        'binary_alternative':{'status':'PROPOSAL_ONLY_NOT_IMPLEMENTED_NOT_APPROVED',
            'target':'ALLOWED versus BLOCKED normative boundary decision; not malicious-source identity',
            'warning_handling':'Exclude only reconciled WARNING boundaries from both splits; never relabel as safe or unsafe. Retain separate approval evaluation.',
            'gates':'Resolve every boundary first; preserve original grouped allocations and historical exclusions; require both reviewed classes in both splits and separate frozen binary protocol/run approval',
            'comparison_limit':'Declare two-action model coverage and approval abstentions; do not pool binary and three-class metrics'}}


def metrics(expected, predictions):
    if not expected or len(expected) != len(predictions) or any(x not in LABELS for x in [*expected, *predictions]):
        raise ValueError("Nonempty paired three-class predictions required")
    matrix = [[0] * 3 for _ in LABELS]
    for truth, prediction in zip(expected, predictions):
        matrix[LABELS.index(truth)][LABELS.index(prediction)] += 1
    per_class = {}
    for i, name in enumerate(LABELS):
        tp = matrix[i][i]
        actual, predicted = sum(matrix[i]), sum(row[i] for row in matrix)
        per_class[name] = {"support": actual, "precision": tp / predicted if predicted else None,
                           "recall": tp / actual if actual else None,
                           "f1": 2 * tp / (actual + predicted) if actual + predicted else None}
    f1 = [v["f1"] for v in per_class.values() if v["f1"] is not None]
    return {"labels": list(LABELS), "confusion_matrix": matrix, "per_class": per_class,
            "accuracy": sum(matrix[i][i] for i in range(3)) / len(expected),
            "macro_f1": sum(f1) / len(f1) if f1 else None,
            "scope": "Phase decisions only; attack success requires separate episode effects"}


def tree_hash(directory):
    root = Path(directory).resolve(strict=True)
    if not root.is_dir():
        raise ValueError("Local model directory required")
    sha = hashlib.sha256()
    for path in sorted(root.rglob("*")):
        if path.is_symlink():
            raise ValueError("Model snapshots must not contain symbolic links")
        if path.is_file():
            sha.update(path.relative_to(root).as_posix().encode() + b"\0")
            with path.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1_048_576), b""):
                    sha.update(chunk)
    return sha.hexdigest()


def packages():
    result = {}
    for package in ("setfit", "sentence-transformers", "transformers", "torch", "datasets", "scikit-learn"):
        try:
            result[package] = version(package)
        except PackageNotFoundError:
            result[package] = "NOT INSTALLED"
    return result


def train(dataset, splits, historical, ledger, output, local_model, revision,
          config=ModelConfig(), *, approved=False, custody_record=None):
    """Explicit future-run entry point. Requires reviews AND separate run approval.

    No download fallback. Complete overlapping windows are pooled once per
    document; labels are never replicated as chunk-level targets.
    """
    if approved is not True:
        raise PermissionError("An actual supervised run requires explicit approval")
    config.validate()
    partitions = load_partitions(dataset, splits, historical, ledger)
    if not custody_record or custody_record.get("status") != "SEALED_ATTESTED_NOT_INSPECTED" or custody_record.get("development_sha256") != digest(dataset):
        raise ValueError("Register a custodian-sealed final collection before model-selection runs")
    if len(revision) != 40 or any(c not in "0123456789abcdef" for c in revision):
        raise ValueError("Pin the actual model repository commit")
    snapshot = Path(local_model).resolve(strict=True)
    if not (snapshot / "modules.json").is_file():
        raise ValueError("Complete locally provisioned SentenceTransformer snapshot required")
    model_hash = tree_hash(snapshot)
    destination = Path(output)
    destination.mkdir(parents=True, exist_ok=False)
    provenance = {"status": "NOT RUN", "evidence_kind": "supervised_experiment", "config": asdict(config),
        "model_revision": revision, "initial_model_tree_sha256": model_hash,
        "dataset_sha256": digest(dataset), "splits_sha256": digest(splits), "reviews_sha256": digest(ledger),
        "custody_sha256": digest(custody_record),
        "code_sha256": digest({p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(Path(__file__).parent.glob("*.py"))}),
        "schema": OBSERVATION_VERSION, "representation": REPRESENTATION_VERSION,
        "classification_target": CLASSIFICATION_TARGET,
        "train_features_sha256": digest(partitions["train"]["text"]),
        "validation_features_sha256": digest(partitions["validation"]["text"]),
        "packages": packages(), "started_utc": datetime.now(timezone.utc).isoformat()}
    write_new(destination / "provenance.json", provenance)
    try:
        from .setfit_backend import fit
        result = fit(partitions, destination, snapshot, config, evidence_kind="REVIEWED_SUPERVISED_RUN")
        scores = result["metrics"]
        write_new(destination / "completion.json", {"status": "COMPLETED", "model_tree_sha256": result["model_tree_sha256"],
            "provenance_sha256": digest(provenance), "reload_verified": result["reload_verified"],
            "finished_utc": datetime.now(timezone.utc).isoformat()})
    except Exception as exc:
        write_new(destination / "completion.json", {"status": "ERROR", "error_type": type(exc).__name__,
            "reason": "No efficacy result is valid without completed model evaluation"})
        raise
    return scores


class Predictor:
    """Small shared interface for a trained classifier, with no evaluator input."""
    def __init__(self, model):
        self.model = model

    def predict(self, episode, event_index):
        observation = build_observation(episode, event_index)
        values = self.model.predict([canonical(observation)])
        values = values.tolist() if hasattr(values,"tolist") else list(values)
        value = values[0]
        if value not in LABELS:
            raise ValueError("Unknown model label")
        return value


def main():
    parser = argparse.ArgumentParser(description="Inspect reviewed supervised data readiness; never trains")
    parser.add_argument("--dataset", required=True)
    parser.add_argument("--splits", required=True)
    parser.add_argument("--ledger", required=True)
    parser.add_argument("--historical", default="data/generated/scenarios-v2.json")
    parser.add_argument("--readiness-report",action="store_true",help="Count reconciled classes without training")
    args = parser.parse_args()
    try:
        if args.readiness_report:
            print(json.dumps(readiness_report(read(args.dataset),read(args.splits),read(args.historical),read(args.ledger))))
            return
        rows = load_partitions(read(args.dataset), read(args.splits), read(args.historical), read(args.ledger))
        print(json.dumps({"status": "DATA_LOADED_NOT_TRAINED", "counts": {k: len(v["label"]) for k,v in rows.items()}, "packages": packages()}))
    except ValueError as exc:
        parser.exit(2, str(exc) + "\n")


if __name__ == "__main__":
    main()
