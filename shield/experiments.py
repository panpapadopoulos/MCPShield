"""Identical scenarios, deterministic order rotation, explicit operational errors."""
import argparse
import hashlib
import json
import os
import platform
import statistics
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter
from .dataset import load_cases, digest
from .detectors import detector, LLM, PROMPT_VERSION
from .simulation import Agent

METHODS = ("no_defense", "rules", "llm", "hybrid")

def metrics(records):
    tp = fp = tn = fn = 0
    for row in records:
        malicious, detected = row["malicious"], row["detected"]
        tp += malicious and detected
        fp += not malicious and detected
        tn += not malicious and not detected
        fn += malicious and not detected
    div = lambda a,b: a/b if b else None
    return {"confusion_matrix": {"tp": tp,"fp": fp,"tn": tn,"fn": fn},
            "precision": div(tp,tp+fp), "recall": div(tp,tp+fn), "f1": div(2*tp,2*tp+fp+fn),
            "false_positive_rate": div(fp,fp+tn), "attack_detection_rate": div(tp,tp+fn),
            "attack_success_rate": div(sum(r["attack_success"] for r in records if r["malicious"]),tp+fn),
            "legitimate_task_success_rate": div(sum(r["task_success"] for r in records if not r["malicious"]),tn+fp),
            "mean_latency_ms": statistics.mean(r["latency_ms"] for r in records),
            "p95_latency_ms": sorted(r["latency_ms"] for r in records)[max(0, int(len(records)*.95)-1)]}

def run_experiment(cases, repeats=3, include_llm=False, factory=detector):
    if not cases or not 1 <= repeats <= 20:
        raise ValueError("Need scenarios and 1-20 repetitions")
    code_hash = hashlib.sha256()
    for path in sorted(Path(__file__).resolve().parent.glob("*.py")):
        code_hash.update(path.name.encode() + b"\0" + path.read_bytes())
    report = {"code_sha256": code_hash.hexdigest(), "suite": "corpus-adapted-simulation-v1", "scenario_sha256": digest(cases), "scenario_count": len(cases),
              "repetitions": repeats, "timestamp_utc": datetime.now(timezone.utc).isoformat(),
              "python": platform.python_version(), "prompt_version": PROMPT_VERSION,
              "llm_model": os.getenv("MCPSHIELD_LLM_MODEL") or None,
              "methodology": "Default warnings denied. Deterministic virtual agent, no training. Same scenarios per method; execution order rotates per repetition. Latency includes both boundaries and follow-up calls. Classification errors invalidate method aggregates.",
              "methods": {}}
    enabled = []
    for name in METHODS:
        if name in ("llm", "hybrid") and not include_llm:
            report["methods"][name] = {"status": "NOT RUN", "reason": "Real LLM calls require explicit --include-llm and configured model/key"}
        elif name in ("llm", "hybrid") and not LLM().configured:
            report["methods"][name] = {"status": "NOT RUN", "reason": "Model or credentials unavailable"}
        else:
            enabled.append(name)
            report["methods"][name] = {"status": "RUN", "records": []}
    for repeat in range(repeats):
        order = enabled[repeat % len(enabled):] + enabled[:repeat % len(enabled)]
        for case in cases:
            for name in order:
                method = report["methods"][name]
                start = perf_counter()
                outcome = Agent(factory(name)).run(case)
                latency = (perf_counter()-start)*1000
                events = [e for call in outcome["calls"] for e in call["events"]]
                error = any(e["category"] == "detector_error" for e in events)
                method["records"].append({"id": case["id"], "repeat": repeat, "malicious": case["malicious"],
                    "detected": any(e["decision"] != "ALLOWED" and e["category"] != "detector_error" for e in events),
                    "latency_ms": latency, "operational_error": error, **outcome})
    for name in enabled:
        method = report["methods"][name]
        errors = sum(r["operational_error"] for r in method["records"])
        if errors:
            method.update(status="ERROR", operational_errors=errors, reason="Classifier unavailable; no aggregate scores reported")
        else:
            method.update(metrics(method["records"]))
    baseline = {(r["id"],r["repeat"]): r["latency_ms"] for r in report["methods"]["no_defense"]["records"]}
    for name in enabled:
        method = report["methods"][name]
        if method["status"] == "RUN":
            differences = [r["latency_ms"] - baseline[(r["id"],r["repeat"])] for r in method["records"]]
            method["additional_latency_ms"] = statistics.mean(differences)
    return report

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--scenarios", default="data/generated/scenarios.json")
    p.add_argument("--output", default="results/evaluation.json")
    p.add_argument("--split", choices=("test","validation","all"), default="test")
    p.add_argument("--repeats", type=int, default=3)
    p.add_argument("--include-llm", action="store_true")
    args = p.parse_args()
    cases = load_cases(args.scenarios)
    if args.split != "all":
        cases = [c for c in cases if c.get("split") == args.split]
    report = run_experiment(cases,args.repeats,args.include_llm)
    output = Path(args.output)
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps({name:{k:v for k,v in result.items() if k != "records"} for name,result in report["methods"].items()},indent=2))

if __name__ == "__main__":
    main()
