# PPO infrastructure and supervised feature control

Approved trained development ablation completed: see
[actual results](TRAINED_DEVELOPMENT_RESULTS.md). Earlier NOT RUN statements below
describe their specific readiness milestones, not the subsequently executed run.

Current status: nine64-step models and the three-seed30,720-step development run
completed. The first matched always-ALLOW; the longer run exposed initial-block/
recovery exploitation in seeds11/23 and always-ALLOW in seed37. See the
[report](RESEARCH_REPORT.md) and [authoritative status](../PROJECT_STATUS.md).
Readiness statements later in this guide describe earlier, explicitly scoped
milestones. They are not the current experiment status. No independently validated
PPO effectiveness or scientific training on reviewed data is claimed.

Expanded developer task suite and current validation are described at the end of
this guide. The original fixture suite and previous smoke artifacts are preserved.

This milestone implements software infrastructure, not a research result. Human
review/custodian work is separate. The original datasets, rule detector, Qwen,
historical hybrid, React/FastAPI application and old reports are unchanged.

## What runs and what cannot run

`research.ppo` supports only an explicitly opted-in `synthetic-smoke` mode, using
the existing small branching virtual tasks. It never loads the38-episode research
collection, proposed labels or a final test. `--mode research` always refuses,
even with the smoke opt-in flag. There is no final-test evaluation path.

A smoke run initializes a small random MLP and performs at most64 cumulative CPU
environment steps, two PPO epochs per rollout, one Torch thread and a30-second
training/validation wall-time budget. Rollout/minibatch divisibility is checked so
SB3 cannot silently round training beyond the requested step cap. The configuration
also limits network width, feature dimensions, horizons and seed-pool sizes.
Dependencies/model initialization happen before the callback budget; this is not
an operating-system time/memory sandbox. It is not full research training.

## Components

- `encoding.py`: deterministic signed character-ngram hashing of the allowlisted
  canonical observation;256 dimensions by default, unit-normalized. No fitted
  vocabulary, pretrained weights, label fields, seed IDs or evaluator info. All
  input text is processed; no silent suffix truncation. Hash collisions and weak
  long-range semantic representation are known limitations, not security guarantees.
- `ppo_env.py`: Gymnasium Box-vector wrapper sharing that encoder. Train and
  developer-validation episode-seed pools must be nonempty, unique and disjoint.
  This seed separation is **not source/attack-family generalization**: both pools
  use the same small synthetic task generator.
- `ppo.py`: SB3 PPO configuration, explicit run gates, CPU seeds, periodic/final
  checkpoints, CSV/JSON optimizer logs, episode utility/harm/approval/override logs,
  package/source/config hashes, separately instantiated validation environment,
  final model save/reload check and interrupted/error completion records.
- `PPOPolicy`: explicitly trusted-local checkpoint loader with observation-only
  inference for the synthetic comparison interface. No evaluator info is encoded.
  All diagnostic comparisons remain labeled synthetic; the application is not
  wired to these checkpoints.
- `supervised.load_encoded_partitions`: prepares the same hashed vectors for a
  future supervised-head control after the existing review/split gates. Features
  and labels remain separate. This does not train a classifier. SetFit's existing
  text pipeline is preserved as a distinct representation/model comparison.

The shared independent authorization gate remains in the episode engine, outside
every learned policy. Trace rows separate recommended/effective actions, policy
overrides, approvals and simulated effects. The new authorization-only comparator
is not the historical fully undefended baseline.

The sequential environment is versioned `sequential-task-foundation-v2`: on a
time-limit truncation it now returns the actual post-transition observation for
value-function bootstrapping. True task termination and irreversible harm remain
separate. No historical simulation or experiment runner was changed.

## Isolated installation

Use a separate Python3.13 environment; the application environment is untouched.
Install CPU Torch first, wait for it to finish, then install the pinned PPO packages:

```powershell
py -3.13 -m venv .local/ppo-venv
.\.local\ppo-venv\Scripts\python.exe -m pip install torch==2.6.0 --index-url https://download.pytorch.org/whl/cpu
.\.local\ppo-venv\Scripts\python.exe -m pip install -r research/requirements-ppo.txt
```

This installs software libraries, not pretrained models. The exact tested Windows/
Python3.13 transitive versions are in `research/requirements-ppo-lock.txt` (use that
file instead of the shorter requirements file for the tested version set). Other
platforms have not been verified. Each smoke records core runtime versions; the
app lock is unchanged.
The backend follows [SB3 PPO](https://stable-baselines3.readthedocs.io/en/master/modules/ppo.html)
and [callback interfaces](https://stable-baselines3.readthedocs.io/en/master/guide/callbacks.html).

## Technical smoke commands (never scientific runs)

```powershell
.\.local\ppo-venv\Scripts\python.exe -m research.ppo --allow-synthetic-smoke --steps 32 --output .local/ppo-check-parent
.\.local\ppo-venv\Scripts\python.exe -m research.ppo --allow-synthetic-smoke --steps 64 --resume-from .local/ppo-check-parent --output .local/ppo-check-resumed
```

Resumption verifies the parent archive, manifest hashes, source/runtime versions,
encoder and configuration before restoring optimizer/model state. Only the total
target steps may change; the total remains capped at64 across the chain. It starts
fresh environment episodes and does **not** claim an exact trajectory/RNG resume.
No completed run directory may be overwritten. A checkpoint is a trusted local
artifact, not a supported upload/import format for arbitrary pickle content.

Outputs stay under the selected ignored local directory:

- `provenance.json`, initial status and completion/error/interruption record.
- `checkpoint-N.zip` intermediate snapshots and final `policy.zip`.
- `logs/progress.csv`, `logs/progress.json`, episode Monitor CSV.
- `episode-outcomes.json`, `validation-smoke.json` with SYNTHETIC_SMOKE_ONLY tags.
- `artifacts.json` and completion-record manifest hashes.

Intermediate snapshots are taken at environment-step callbacks and may precede
that rollout's optimizer update; final `policy.zip` is saved after updates. A
completed smoke must show changed weights and a matching save/reload prediction.
Incomplete/error/interrupted runs have no valid performance conclusion. None of
these files is exported into the dashboard or historical evaluation report.

## Tests

Standard tests cover mode/budget/seed gates, label/future-field exclusion, shared
supervised features and correct truncation state. Real PPO integration tests are
explicit opt-in and only use temporary synthetic fixtures:

```powershell
$env:MCPSHIELD_PPO_INTEGRATION='1'
.\.local\ppo-venv\Scripts\python.exe -m unittest discover -s tests -p test_ppo.py -v
```

They exercise real Gym/SB3 checks, optimizer changes, logs, save/reload, bounded
resumption, deterministic repeated weights, interruption status and tamper rejection.
An app-only invocation skips optional backend tests; skipped tests are not passes.

Prior infrastructure verification:128 app/runtime tests passed, with7 optional PPO tests skipped
there; the separate isolated PPO suite passed all14 tests, including those7 real
backend checks. Across both environments all135 distinct tests passed. A persistent
64-step check is in `.local/research-phase2/ppo-smoke-v1/`: optimizer weights changed,
reload matched and its completion record is SMOKE_COMPLETED. Its curves/outcomes
are synthetic debugging evidence only. No security efficacy is inferred.

## Before research experiments

Still required: completed independent reviews/adjudication; a reviewed and versioned
population of branching tasks with source/derivation-disjoint development panels;
validated rewards/consent behavior and encoder ablations; sealed independent final
collection before model selection; an approved experimental protocol and run budget.
The static38-episode dataset is not automatically a branching RL environment.
Hashing versus a semantic encoder and a supervised head on matched inputs must be
compared without assuming PPO will improve security.

For SetFit: independent labels, local MiniLM snapshot/pinned dependencies and
validated token-budget/chunking behavior remain open. No SetFit experiment runs as
part of this milestone. No unreviewed labels support scientific conclusions.

## Expanded sequential task validation

Current verification:145 app/Gym tests passed with8 optional backend tests skipped
there; the isolated real PPO suite passed15/15 (including those8 checks). Across
both runtimes all153 distinct tests passed. No remote CI run or scientific training
is claimed.

`task_suite.py` and `branching_env.py` add the separately selectable
`branching-development-v1` generator. It has eight declared operational families:
two legitimate multi-tool orderings; split instructions across search/database
responses; a poisoned tool description with later consequences; non-grantable
permissions; an unauthorized file redirect; an authorized confidential input
followed by a delayed transfer attempt; and scoped archive consent. Normal tasks
need eight successful boundaries across four virtual tools. A blocked interaction
can lead to an alternate public source and a final notice read.

Task success requires delivered notice, rows and forecast evidence, not a reward
for choosing a label or merely reaching a favorable node. Only execution of a
virtual secret-bearing external search records disclosure; a response block or
later request block can prevent it. An authorized confidential read is not itself
treated as harm. The shared authorization gate remains outside the policy.

WARN now pauses at the same boundary, with an observable pending flag and no tool
execution. A later action can receive the simulated user response or cancel the
request. Approved scoped permissions are verified before execution; rejected
warnings can recover. Two consecutive warnings at the same boundary deny/recover
rather than creating an infinite approval loop. Approval preference is independent
of attack labels and can approve an unsafe directive: this is not an oracle.

Observations use a compatible extension, `mcp-sequential-observation-v1`, adding only
known runtime fields: approval pending/result, remaining external step budget and
recoveries already used. IDs, family/split, graph nodes, future responses, hidden
effects and rewards remain evaluator-only. Existing static datasets keep their
original schema. Both encoders and the supervised feature interface can process
the extension; a reviewed trajectory loader/control is still needed before a
matched supervised-vs-RL experiment.

The generator reads checksum-pinned inert MCPCorpus metadata, never historical
labels or independent-test files. Train source anchors are records2415
(tinyfish-io/agentql-mcp) and13514(microsoft/clarity-mcp-server); developer-validation
anchors are9246(intsig-textin/textin-mcp) and8070(kennyfong19931/mcp-hk-transport-eta).
Native descriptions/schema and raw revision/hash remain in provenance; authored
graphs map the workflows onto the four fixture tools. Native servers are not
executed or labeled malicious. All graph scenarios remain synthetic/UNREVIEWED.
Source/family assignments are reproducible, but declared disjoint group names do
not prove semantic attack independence. Common fixture tools/recovery logic are
intentionally shared. This developer panel is not the independent final test.

### Rewards and checks

| Event | Default reward | Rationale |
| --- | ---: | --- |
| Each decision/approval wait | -0.02 | Discourage needless delay |
| Block | -0.20 | Charge interruption; avoid blanket blocking |
| Warning step | -0.25 | Charge approval burden, including repeated WARN |
| Completed task with no harm | +5 | Preserve useful task behavior |
| First irreversible virtual harm | -10 | Outweigh task utility |
| Terminal failure without harm | -3 | Penalize abandoning the task |

No per-block true-positive bonus or expected-decision reward exists. Terms and
cumulative totals are logged and checked exactly. Completion prevents replaying
terminal rewards. External truncation returns the next state without inventing a
terminal failure penalty, enabling proper bootstrapping. Long-horizon/deadline
policies still need a separate validation study; timeout rates must be reported.

`python -m research.validate_tasks` writes480 deterministic diagnostic rollouts
across eight families, two seeds, both user preferences, five controllers and three
predeclared weight configurations. Those are repeated engineering checks, **not
480 independent attack examples**. Controllers include the three constants, WARN
followed by approval resolution, and a fixture-specific observable-history sanity
controller. None is a trained model or a replacement for the retained rule baseline.

For the32 default-weight cases per controller, ALLOW completed20 tasks and incurred
12 unsafe outcomes. BLOCK and repeated-WARN completed none and incurred no harm.
WARN-with-resolution incurred six unsafe outcomes: approvals are not perfect
security judgments. The fixture history controller completed32 with no harm. These
are simulator-mechanics observations only. Doubling the harm penalty made constant
BLOCK score above constant ALLOW, while the history controller remained positive;
therefore the reward is sensitive and is **not claimed scientifically validated**.
No weight was tuned or selected using independent final-test information.

### Encoder checks and smoke command

The original256-dimensional char-trigram encoder is retained. A concrete order
collision (`aaabaa` versus `aabaaa` in the same argument) produces identical old
vectors. The selectable512-dimensional `field-position-hash-v1` encoder tags field
paths, history positions and within-field positions, with dedicated observable
phase/approval/context slots. It distinguishes that collision and tested scope,
phase and history changes. It contains no attack-keyword rules or expected labels.

On32 sampled developer observations, bucket-collision fractions were approximately
56–64% for old character features and29–56% for the new field features. Feature
sets differ, so these are diagnostics, not comparable accuracy estimates. Both
hashings remain lossy. No probe establishes semantic sufficiency for a neural
policy. Semantic encoders, dimension/history ablations and benign counterfactuals
remain necessary.

```powershell
.\.local\ppo-venv\Scripts\python.exe -m research.ppo --allow-synthetic-smoke --steps 64 --task-suite branching-development-v1 --encoder field-position-hash-v1 --output .local/NEW-UNUSED-SMOKE-PATH
```

The source/seed/task manifests identify train and developer-validation tasks;
research mode remains disabled. Existing output directories are never overwritten.
Current saved outputs:

- `.local/research-phase2/branching-validation-v2.json`: diagnostics and collision probes.
- `.local/research-phase2/ppo-branching-smoke-v1/`:64-step technical check, updated
  weights and matching final checkpoint reload; no efficacy conclusion.

### Remaining risks and next work

The small graph grammar and repeated recovery path can be memorized. Credential
fixtures and explicit phrase fields can create shortcuts. Source descriptions and
topic distribution may create spurious cues. Fixed per-episode approval preferences
are not a validated human model. A finite positive reference-policy return does
not prove absence of reward hacking; arbitrary shorter horizons could favor timeout
avoidance, and changed weights can favor blanket defenses. Hash collisions and
history clipping may hide critical context. These issues remain scientific blockers.

Next: add counterfactual benign/unsafe matched contexts, more independently reviewed
branching mechanisms, and encoder/history/reward ablations on developer data. Keep
human review/custody separate, but obtain reviewed task/protocol manifests before
research optimization. Do not promote these diagnostic curves into security results.

## Matched counterfactual and ablation readiness

`counterfactuals.py` adds six synthetic/UNREVIEWED pair types. With two generation
seeds there are12 matched pair instances,24 member tasks, all developer data:

| Pair | Controlled security factor |
| --- | --- |
| file_scope | Same file request; only exact resource grant changes |
| permission_scope | Same permission request; only granted permission changes |
| instruction_override | Same response data; authorized instruction versus task override |
| terminology | Security explanation versus actionable instruction using similar terminology |
| followup_scope | Same reference lookup; only explicit sharing grant changes |
| history_classification | Same current request and authorization; earlier public/confidential classification changes |

For instruction pairs the changed response drives its corresponding follow-up
transition; that is an operational consequence of the directive, not a second
unrelated factor. Tests restrict task differences to the declared fields. Proposed
ALLOWED/BLOCKED decisions are evaluator metadata, never policy inputs. Scope pairs
are stopped by the shared authorization gate; they do not demonstrate learned
protection. Reference sharing is assessed from actual grants/previous delivered
classification rather than a pair's proposed label. The user explicitly delegates
classification authority to the registry in the history pair; compromised registry
classification is outside this controlled probe.

Pairs and all their seed variants remain in one declared group/partition. No new
final-test examples exist. These tasks extend the existing inert fixture tool
semantics without modifying old task generators, datasets or reports.

`ablations.py` implements A original hashing, B field/position hashing, C field
without history, and D field with available history. B and D are explicitly
recorded aliases. All use512 output dimensions and the same proposed32/32 PPO
architecture, seeds and64-step smoke ceiling; A uses the original hashing algorithm
at matched dimensionality, not the older256-dimensional setting. C removes history,
omission count and prior-approval/recovery summaries, retaining current scope,
phase and time budget. The Gym adapter exposes identical spaces for all conditions.

On these12 finite probes, A/B/D distinguish12 pairs; C distinguishes10. Its two
history-classification pairs intentionally collapse to identical vectors. These
are distinguishability checks, **not classification accuracy or evidence of
semantic sufficiency**. Existing hashing collision examples remain valid. Repeated
fixture tokens, limited scope language and common graph grammar remain shortcuts.

### Predeclaration and sensitivity findings

Run `python -m research.counterfactual_checks` to write a plan before diagnostic
scoring, then immutable diagnostics and artifact hashes under
`.local/research-phase2/counterfactual-v2/`. The earlier v1 files remain preserved;
v2 completes configuration metadata without changing weights or diagnostic cases.
The plan records case/environment/observation versions and hashes, dependency lock,
encoder, rewards, horizon, optimizer seeds versus episode seeds, model parameters,
budget and metrics. `training_status` remains NOT RUN. Scientific run budget and
approval are absent; there is no automatic training executor for this plan.

Primary hypotheses remain step -.02, block -.20, warning -.25, task completion +5,
irreversible harm -10, terminal failure -3, horizon24. Seven predeclared settings
vary one factor at a time: primary; harm20; block.8; failure6; warning1; completion2;
and horizon4. No weights are selected from final-test or model-performance results.
The diagnostic seed is11; representation probes use11/23; proposed optimizer
initialization seeds are11/23/37. All conditions use the same cases/preferences.

There are672 deterministic policy/weight runs (not672 independent examples),
including constants and WARN followed by approval resolution. For24 primary cases:

| Controller | Task completions | Virtual unsafe outcomes |
| --- | ---: | ---: |
| Always ALLOW |16|8|
| Always WARN |0|0|
| Always BLOCK |0|0|
| WARN then resolve |8|4|

Mandatory overrides are counted separately in the raw report. Doubling harm cost
changes the raw-return ranking of ALLOW versus BLOCK, demonstrating sensitivity,
not a superior reward choice. With horizon4, ALLOW has20 truncated/incomplete cases,
four harms and no completions. A warning-only timeout can have a higher observed
return than terminal failure. Therefore **reward-only model selection is forbidden
by the proposed protocol**, and timeout/no-harm is not successful prevention.
External truncation still preserves correct bootstrapping; adding an intrinsic
user deadline requires a separate explicit task-failure model.

Current verification:159 app/Gym tests passed,8 optional PPO tests skipped there;
the isolated PPO suite passed15/15, including those8 checks. All167 distinct tests
passed across the two runtimes. Counterfactual diagnostics perform no optimization;
the regression PPO tests remain bounded synthetic checks on existing suites.

The environment now supports controlled engineering study of scope, history and
decision-dependent utility/harm. It cannot yet support a real-world efficacy or
generalization conclusion: labels/semantics are unreviewed, tasks are few and
templated, approval behavior is simplified, token/field shortcuts remain, and
horizon/reward exploitation is not resolved. A trained policy's ability to use
these distinctions has not been measured. Next is an explicitly approved bounded
synthetic developer ablation; it need not wait for independent reviews, but its
outputs remain engineering evidence only. Reviewed task/protocol manifests are
required before scientific conclusions. Independently collected final evaluation
and full scientific training remain separate, blocked milestones.
