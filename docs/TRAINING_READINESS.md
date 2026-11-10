# Training readiness and execution

Status: November 9, 2026. Deadline: November 23, 2026.

Paths below describe the development machine's ignored artifacts. For a fresh
clone without any of those files, begin with [TEAM_HANDOFF.md](TEAM_HANDOFF.md).
Weights, reviews, custody payloads and checkpoints are not included in Git.

The pinned MiniLM model is downloaded, upstream-hash verified and passes offline
loading, full-token window coverage, two-step synthetic optimization and SetFit
checkpoint reload checks. No reviewed-data classifier has been trained. The
approved three-seed, 30,720-step PPO development run completed without changing
its frozen configuration. Its recovery-shortcut/always-ALLOW findings are in the
[research report](RESEARCH_REPORT.md). Historical results and the sealed-test
protocol remain unchanged.

## Tested runtime

Run commands from the repository root, using PowerShell:

```powershell
$py = '.\.local\ppo-venv\Scripts\python.exe'
& $py -m pip check
```

This isolated Python 3.13 CPU environment contains Torch 2.6.0+cpu, SetFit 1.1.3,
sentence-transformers 3.4.1, transformers 4.48.3, SB3 2.7.0 and Gymnasium 1.2.2.
`research/requirements-ml-lock.txt` records the complete tested dependency freeze.
The application environment is separate. No paid services are required.

## First supervised experiment

Remaining gates: real reconciled independent reviews, adequate support for all
three classes in grouped train/validation partitions, registered sealed-test
custody and explicit reviewed-data training approval. The MiniLM snapshot is ready. The current
empty review ledger cannot pass these gates. Review/test registration does not
give developers access to sealed examples.

The target is the reviewed normative boundary recommendation before authorization
overrides, not malicious-source identity or future harm. Check actual reviewed
support without starting training:

```powershell
& $py -m research.supervised `
  --dataset data/generated/research-expansion-v3.json `
  --splits .local/research-phase2/expansion-v3-package/splits.json `
  --ledger ACTUAL_RECONCILED_LEDGER.json --readiness-report
```

Currently every class has zero independently reconciled examples. The software
requires at least two training examples and one validation example per class;
these minima are not a statistically adequate sample-size claim. Disagreements,
rejects and unreviewed examples block import; a third vote does not automatically
erase dissent. Follow [review import/adjudication instructions](REVIEW_GUIDELINES.md),
preserve original votes, and re-review a new version when human resolution changes
labels/content. No training gate has been relaxed.

If reviewed WARNING support remains insufficient, a defensible **proposed** binary
target is ALLOWED versus BLOCKED, excluding reconciled WARNING examples from both
fixed partitions. Do not fold WARNING into either class, rebalance by moving
validation examples, or exclude unresolved items merely to pass gates. Declare
coverage and retain shared authorization/approval enforcement. This needs a new
frozen binary protocol and explicit approval before implementation/training.

The approved download command already ran successfully (do not repeat it into
the existing directory):

```powershell
& $py -m research.provision_minilm --approve-download
```

This downloads approximately 91 MB of weights plus tokenizer/configuration files
from `sentence-transformers/all-MiniLM-L6-v2`, revision
`1110a243fdf4706b3f48f1d95db1a4f5529b4d41`, into a new
`.local/models/minilm-pinned` directory. Model identity, revision, upstream weight
hash and checkpoint compatibility are verified; details are in
`.local/research-phase2/minilm-verification-v1`.

After actual review reconciliation and separate run approval, replace the two
`ACTUAL_...` paths below with genuine records:

```powershell
& $py -m research.train_supervised `
  --dataset data/generated/research-expansion-v3.json `
  --splits .local/research-phase2/expansion-v3-package/splits.json `
  --ledger ACTUAL_REVIEW_LEDGER.json `
  --custody ACTUAL_CUSTODY_RECEIPT.json `
  --model .local/models/minilm-pinned `
  --revision 1110a243fdf4706b3f48f1d95db1a4f5529b4d41 `
  --output .local/setfit-seed11 --seed 11 --max-steps 64 `
  --approve-reviewed-training
```

Budget estimate: 5–30 CPU minutes for this first 64-step encoder run plus classifier
fitting, not yet measured on MiniLM. Long observations increase work. No API cost.
The configuration uses 256-token windows, 32-token overlap and at most 64 windows
per document; excess length fails explicitly. Window embeddings are pooled into
one document embedding before classification. Labels, outcomes, future steps and
review metadata are excluded from canonical observable inputs. There is no silent
suffix truncation. Window pooling's security effectiveness remains unvalidated.

Outputs include the saved encoder/classifier, training log, validation metrics,
label order, chunk counts, dataset/review/source/model/package provenance and
checkpoint digest. Save/load prediction equality is checked. Use
`research.setfit_backend.SavedClassifier(run_directory, trusted_local=True)` for
local prediction; only load trusted local checkpoints.

## Approved PPO development run — completed

The command below is an execution record, not a request to rerun. All three final
checkpoints reproduced their saved comparison trajectories after reload. Logged
training time totaled 112 seconds, well below the approved 45-minute cap. Seeds 11/23
learned initial-block/recover behavior; seed 37 matched always-ALLOW. Supplemental
legitimate fixed-pivot interventions were 7/9, 3/9, 0/9 respectively (UNREVIEWED
probes). No further learning or tuning was performed. Use
`.local/ppo-development-v2/analysis/summary.json` and the report for actual metrics.

The nine earlier 64-step models and their always-ALLOW deterministic behavior are
preserved. Their near-uniform entropy and tiny approximate KL suggest very little
optimization; they do not establish that more training will improve security.
Reward scale, class/task sampling, hashing, horizon and simplified transitions
remain plausible limitations. There is no broad search proposed.

Code-based interpretation, without new training:

- **Budget/action selection:** 64 steps gave eight optimizer epochs; logged entropy
  was 1.098556–1.098602 versus log(3)=1.098612, with approximate KL around
  0.00000026–0.00000114. Deterministic argmax can consistently select ALLOW from
  nearly tied logits. No recorded initial-policy evaluation proves causality.
- **Rewards:** success +5, harm -10, failure -3, block -0.20, warning -0.25 and
  step -0.02 put terminal consequences above intervention costs. Sparse delayed
  credit remains difficult; these magnitudes do not alone demonstrate a defect.
  The proposed run keeps them fixed rather than searching reward scales.
- **Sampling:** uniform families contain one ordinary family and three attack
  families per training partition. The next protocol reweights the ordinary
  family by three; this balances author-defined episode roles, not decision-level
  classes or independently reviewed labels.
- **Representation:** the 512-dimensional field/position hash preserves some
  order and authorization fields but has collisions and no pretrained semantics.
  Failure across the three earlier representations does not isolate its effect.
- **Horizon/dynamics:** the 24-step horizon permits multi-step recovery, but WARN
  consumes a separate approval step. The shared approval driver removes repeated
  receipt decisions from the learned action loop while retaining their costs.
  Finite templated transitions and deterministic user preferences still limit
  transfer to real agents. Earlier zero truncations do not prove every future
  policy fits the horizon.

The executed protocol is saved at
`.local/research-phase2/ppo-next-protocol-v1.json`. It specifies three seeds
(11, 23, 37), 10,240 steps each, 30,720 total, one CPU thread and a 900-second
training limit per seed. It retains the primary rewards, uses separate task
families and episode seeds for training and development validation, and balances
the existing author-defined training roles by sampling. A common approval-response
driver is used by training and all comparison methods. This is a new explicitly
versioned protocol; do not pool it with historical results.

Executed under explicit approval:

```powershell
& $py -m research.ppo_next `
  --run-protocol .local/research-phase2/ppo-next-protocol-v1.json `
  --output .local/ppo-development-v2 --approve-bounded-development
```

Original estimate was 2–10 minutes per seed; actual logged times were 35/45/32
seconds. The approved hard training cap was 45 minutes total plus evaluation/startup. A time limit aborts rather than
claiming completion. No API cost. Outputs preserve protocol, scenario/source
hashes, logs, checkpoints and per-seed outcomes. ALLOW/WARN/BLOCK constant policies
are evaluated separately. Outcomes include task goals, unsafe outcomes, warnings,
blocks, authorization overrides, truncations and reward. False-positive rates
remain unscored without separately reviewed phase labels. This run is development
diagnostics, not the first independently validated PPO research result.

## Five-method comparison and report

The existing application now has a separate read-only five-method result panel.
`research.delivery` is the explicitly approved development-comparison/export CLI;
its default artifact is `.local/research-phase2/dashboard-comparison-v2.json`.
The authenticated `/api/research-evaluation` endpoint reads it without model
imports or execution. Before a compatible artifact is published, all five rows
show NOT RUN. The original four-method live simulation/evaluation is unchanged.
The current artifact format labels every published result DEVELOPMENT_ONLY;
independent final-result publication requires actual evidence and release review.

The evaluator is now `contextual-five-method-v2`, with separate pre-override
recommendations, effective decisions, interruption/recovery utility and source/case
provenance. Optional evaluator-only targets never enter model inputs. Correctness
counts require semantic annotations; authorization is not a detector ground truth.
Old v1 results/checkpoints are unchanged and must not be silently overwritten.
The separately versioned reward proposal is not active in any environment.

`research.five_methods` accepts real no-defense, rules, contextual local Qwen,
saved SetFit and PPO providers. Each receives the same canonical observable
schema, with shared mandatory authorization enforcement. Overrides are recorded
separately. Missing providers are `NOT RUN`; errors produce no efficacy score.
Synthetic tiny classifiers cannot be reported as trained MiniLM. The historical
Qwen prompt and fixed-path rules experiments remain unchanged; the new contextual
protocol requires new evaluations and actual model identity recording.

The report draft is [RESEARCH_REPORT.md](RESEARCH_REPORT.md). Its results distinguish
historical experiments, trained synthetic development diagnostics, software
fixtures and pending independent evaluations. Application result integration
awaits compatible verified experiment artifacts; the read-only integration itself
is implemented and browser/API tested. A fresh clone starts with NOT RUN rows.
