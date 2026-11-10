# Trained PPO development ablation

This document preserves the first nine-model64-step development experiment.
The later three-seed10,240-step run and recovery-shortcut findings are documented
in [RESEARCH_REPORT.md](RESEARCH_REPORT.md). Both sets of findings remain valid
within their separate synthetic protocols; do not pool their scores. Reviewed-data
MiniLM training and independently validated PPO performance are still pending.

Executed November9,2026 under explicit user approval for development diagnostics.
This is actual PPO optimization on synthetic tasks, **not independent validation**.
No human reviews or final-test contents were used. Completion deadline is now
November23,2026; optional infrastructure expansion is deferred.

## Frozen protocol and actual execution

Used the existing `counterfactual-v2/plan.json` unchanged: source/environment and
case hashes verified before training. Three distinct representations A/B/C,
optimizer seeds11/23/37,64 steps per model, CPU/one thread,32/32 networks,16-step
rollouts,16-example minibatches,2 epochs and the primary reward/horizon24.
D is identical to B and reuses B's results; it is not an independent replication.
Nine distinct trained models performed576 environment steps in27.065seconds of
runner time. Each changed weights and passed save/reload prediction verification.

The essential execution adapter is `research/development_ablation.py`. It records
the exact protocol before scoring. Training uses a seed-shuffled cyclic bank of
24 declared training cases; case order is matched per optimizer seed across
representations. Trajectories and completed training cases remain action-dependent.
At this tiny budget15–17 unique cases were assigned per model (the last reset may
not receive an action), so coverage/convergence must not be assumed.

Evaluation uses the same24 developer-validation episodes per model:12 legitimate
and12 unsafe members, including both simulated approval preferences. Pair groups
and source panels are separate from training; all were previously developer
inspected. This is neither an untouched test nor evidence of real-world generalization.

## Results

Trained rows below are identical across all three optimizer seeds. Counts are per
24 evaluation episodes, not independent samples aggregated over repeated seeds.

| Policy / representation | Legitimate completion | Unsafe outcomes | FP probes | Warning steps | Truncations | Mean reward |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Trained A: original hash |12/12|12/24|0/6|0%|0|-2.617|
| Trained B/D: field + history |12/12|12/24|0/6|0%|0|-2.617|
| Trained C: field, no history |12/12|12/24|0/6|0%|0|-2.617|
| Constant ALLOW |12/12|12/24|0/6|0%|0|-2.617|
| Constant WARN |0/12|0/24|6/6|100%|0|-4.080|
| Constant BLOCK |0/12|0/24|6/6|0%|0|-3.440|

All12 unsafe members resulted in harm under each trained model/ALLOW baseline:
the unsafe-member outcome rate is100%. The overall episode harm rate is50%.
WARN repeatedly requests review rather than resolving it; it made48 approval
requests across96 warning steps and completed no work. Constant BLOCK made none.

**FP probes are provisional**, defined as a non-ALLOW recommendation at six fixed
legitimate decision pivots with authored, unreviewed target decisions. They are
scored separately from action-dependent trajectories, avoiding early-block coverage
bias. They are not an independently validated false-positive rate. Episode-level
interventions, approval counts, overrides, fixed-pivot decisions and episode outcomes are also
retained. No authorization overrides occurred in these developer-validation cases;
the common gate remained active for every policy.

Conclusion limited to this run: the trained policies behave like always-ALLOW on
all measured cases. There is **no observed security improvement and no evidence
favoring one representation at64 steps**. Weight updates prove execution, not useful
learning. Zero FP probes is not success when all unsafe cases succeed. No weights,
budget or reward were tuned after observing these results.

## Artifacts and verification

Ignored run directory:
`.local/research-phase2/trained-development-ablation-v1/`

- `protocol.json`, `frozen-plan.json`, `report.json`, `completion.json`.
- `A_original/{11,23,37}/`, `B_field/{11,23,37}/`, `C_field_no_history/{11,23,37}/`:
  actual final/periodic checkpoints, optimizer logs, assigned cases, raw episode
  evaluation and fixed-pivot predictions. Report records checkpoint hashes.
- Completion status: COMPLETED_DEVELOPMENT_ONLY. No automatic dashboard import.

Re-running requires a fresh output directory and explicit development flag; the
runner rejects changed frozen configurations and limits total steps to576. It has
no independent-test loader or scientific-training mode. No reviewed-data supervised
model has been trained; SetFit has passed separate synthetic optimizer checks.

The November23 minimum delivery must contain actual saved SetFit and PPO models,
the five-method shared-policy comparison, provenance/raw results, application
integration with clear evidence labels, reproducible setup/tests and a report with
negative findings and validity limits. Independently validated final results depend
on real reviews and authorized custodian release, not the deadline alone.
