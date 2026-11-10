# MCPShield: learned security decisions for simulated MCP interactions

Report draft — verified work through November9,2026. Completion target:November23.
Pending results are explicitly marked; no independent reviews or final evaluation
are implied by this draft.

## Research question

Can a learned security policy reduce unsafe MCP tool outcomes while preserving
legitimate task completion? The project compares traditional content rules,
pretrained Qwen, supervised SetFit/MiniLM and a PPO policy in an inert controlled
simulation. No method is assumed superior. Mandatory authorization is independent
of the selected detector in the new comparison.

## Architecture and application

The original application uses React/Vite and FastAPI. Its live activity feed,
exact-payload approvals, four virtual tools, deterministic vulnerable agent and
historical no-defense/rules/Qwen/hybrid experiment runner are retained. Tool
effects occur only in memory; upstream MCP servers, shell commands and private
resources are not executed. This is a controlled simulator, not a demonstrated
secure production MCP proxy or autonomous real-LLM agent deployment.

The research path projects a boundary into an allowlisted observation, asks a
detector for ALLOW/WARN/BLOCK, and independently enforces trusted authorization
before simulated execution or response delivery. Multi-step graphs provide
approval, denial, recovery and delayed virtual effects. Evaluators receive hidden
effects and optional semantic targets separately; policies never receive them.

The dashboard now has a separate read-only five-method comparison panel. The
authenticated `/api/research-evaluation` endpoint reads a versioned, hash-checked
JSON artifact, never loads model pickle files or starts inference/training. Missing
methods are NOT RUN; incomplete identities and synthetic SetFit fixtures cannot
publish scores. Artifact errors produce no scores. This first publication format
accepts DEVELOPMENT_ONLY evidence, explicitly not independent validation. It shows
task goals alongside uninterrupted completion, unsafe effects, initial blocking
and authorization overrides. Historical four-method results and interactive
simulations remain separate. The Docker recipe includes the lightweight research
reader; training/model dependencies are not added to the application image.

## Data provenance and scenario construction

The pinned MCPCorpus source contains13,875 unlabeled metadata records, not13,875
verified attacks. Snapshot revision is295fe37cd972ea9aa1b48578b2d7bcc40a72ee12;
SHA-256 is `cc14fc4fe5c68b73e77cbaa3e64fc2b58616a8e61d0e96d92b8fd861702b9e20`.
Original metadata is preserved and upstream services are not executed. Source
repositories are never labeled malicious merely because metadata is adapted.

Historical benchmark:126 adaptations (nine templates across14 repositories) plus
32 authored regressions, totaling158 cases:48 validation and110 test/regression.
Previously inspected tests remain development evidence, not a new untouched test.
Shared templates and pending independent label verification limit interpretation.

New research collection:38 authored episodes/68 decision boundaries, including22
metadata-backed adaptations from eight additional repositories. All proposed
labels remain UNREVIEWED until actual submissions are imported. Separate branching
tasks have eight developer workflow families; matched probes add six counterfactual
pair types. Generated variants are not counted as independent real-world attacks.
Source/family grouping, provenance and checksum controls are retained. Raw source
reuse terms need verification before metadata redistribution.

## Features and observations

Models receive only tool name/description, arguments, current response when
available, actual requested permissions, trusted user task/scope and bounded prior
observable history. Sequential observations additionally expose current approval
state, remaining time budget and recoveries already used. Labels, expected actions,
split/episode IDs, hidden effects and future responses are excluded.

Original and field/position-aware hashing remain distinct versioned options. The
supervised candidate uses complete overlapping tokenizer windows, document-level
mean embeddings and one contrastive/classifier label per observation. No training
label is replicated as if every chunk independently contained an attack. Window
pooling preserves input coverage but loses global cross-window attention and can
dilute small harmful spans; validity must be evaluated rather than assumed.

## Methods

1. **No detector:** new comparisons retain the common authorization gate. Historical
   fully undefended simulations are separately preserved.
2. **Rules:** historical experiments retain their original implementation. The new
   contextual adapter reuses the content heuristics without silently imposing the
   old fixed file path/permission policy.
3. **Pretrained Qwen:** historical local Qwen2.5:3b runs are complete. A separate
   contextual prompt uses the current trusted task/scope/history; no new Qwen scores
   are claimed until actual evaluation runs. Only the local endpoint is permitted.
4. **SetFit/MiniLM:** target is sentence-transformers/all-MiniLM-L6-v2, fine-tuning
   the encoder and fitting a logistic head with three fixed decision classes.
   Reviewed-data MiniLM training is NOT RUN. The pinned MiniLM snapshot is now
   downloaded and hash-verified. Both a tiny random-transformer fixture and a
   two-step pretrained MiniLM synthetic check have exercised optimization, window
   handling, saving, loading and prediction. Their classification scores are not
   scientific project results.
5. **PPO:** discrete ALLOW/WARN/BLOCK decisions affect request execution, response
   delivery, approvals, recovery and delayed virtual effects. Reward combines
   task completion, irreversible harm, failure, interruption, warning and step costs.
   The next proposed protocol uses a common approval driver for all methods;
   old development runs retain their original driver and are not silently pooled.

## Experimental design and metrics

The supervised candidate uses three fixed classes with integer encoding in the
order ALLOWED, WARNING, BLOCKED; labels stay outside text inputs. SetFit contrastive
encoder tuning uses seed11, batch8, learning rate2e-5, one epoch capped at64
optimizer steps, followed by logistic regression (C1, maximum1000 iterations).
Complete256-token windows overlap by32 tokens and are averaged per document;
more than64 windows fails explicitly. Grouped partitions and exact-observation
overlap checks precede fitting. Validation labels are used for evaluation, not
encoder/head fitting. Seeds and package/source/data/review/model hashes are saved;
model reload must reproduce validation predictions. No scientific SetFit metrics
are available until genuine reviews, custody registration and run approval pass.

The completed bounded PPO implementation uses Stable-Baselines3 on Gymnasium,
three discrete actions, a512-dimensional field/position hash observation and
separate32/32 policy/value networks. Each seed used128-step rollouts, batch64,
four optimizer epochs/rollout, learning rate3e-4, gamma0.99, GAE0.95, clipping0.2,
entropy coefficient0.01 and horizon24 on one CPU thread. Family/episode seed
allocation was frozen before the run. Decisions change graph transitions and
recovery opportunities, so this is a sequential control experiment rather than
independent one-step classification. The simplified dynamics still permit the
documented utility shortcut.

Use grouped training/validation data, immutable model/data/protocol hashes, fixed
seeds and identical available context. The final collection must be independently
reviewed, source/derivation separated, custodian sealed before model selection,
and released only after model/evaluation freeze. Final-test status remains
NOT_COLLECTED; no final examples have been accessed by these engineering runs.

Boundary metrics: class support/confusion, precision, recall, F1, FPR/FNR and
operational failures. Episode metrics: task completion, unsafe effects, warnings,
blocks, authorization overrides, truncations and return. Record actual training
cost and inference latency. Classification proposals must not be substituted for
actual effects. Report undefined rates as null and do not infer attack prevention
from a timeout. Repeated seeds/templates are not independent population samples.

## Completed results

Historical110-case regression was a single-pass controlled simulation, with all
four original methods running: rules prevented all68 authored attacks and completed
41/42 legitimate tasks; pretrained Qwen completed40/42 and missed one attack;
historical hybrid completed40/42 and prevented68/68. These results do not prove
hybrid superiority or real-world generalization. See POLICY_V2_RESULTS.md for
metrics, provenance and the historical runtime-reporting correction.

The approved PPO development ablation trained nine models:three unique
representations xthree seeds x64 steps (576 total), with one alias condition.
All weights updated and checkpoints reloaded correctly. On the24 developer cases,
all policies matched constant ALLOW:12/12 legitimate completions,12/12 unsafe
members harmed, zero provisional legitimate pivot FPs, zero warnings/truncations,
mean return-2.617. This is a negative development finding, not final validation.
Logs show entropy nearlog(3), only eight update epochs and tiny KL changes; the
data do not establish a confident converged always-ALLOW optimum. See
TRAINED_DEVELOPMENT_RESULTS.md for raw artifacts and accounting definitions.

### Approved bounded PPO development run

The frozen `bounded-ppo-development-v2` protocol completed 10,240 steps for each
of seeds 11, 23 and 37 (30,720 total), with no reward, observation or hyperparameter
changes. Logged training seconds were 35, 45 and 32 respectively (112 total;
integer logger measurements exclude some startup/evaluation overhead). No budget
extension or parameter search followed. Each seed completed 80 rollouts and 320
optimizer epochs. All final checkpoints reloaded and reproduced every recorded
24-case comparison trajectory exactly. This protocol differs from the previous
64-step ablation and is not pooled with it.

The development-validation bank contains four authored families, three episode
seeds and two user consent preferences: 24 cases per policy. Author-defined
legitimate families are `public_itinerary` and `scoped_archive` (12 cases); the
other 12 cases contain attack paths. These roles are UNREVIEWED. All methods use
the same mandatory authorization gate and approval-response driver.

| Policy | Legitimate task completion | All task goals | Unsafe outcomes /24 | Warning steps / engine steps | Blocks | Truncations | Mean return |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Always ALLOW | 12/12 | 18/24 | 6 | 6/189 (3.17%) | 6 | 0 | 0.980 |
| Always WARN | 6/12 | 9/24 | 3 | 111/225 (49.33%) | 3 | 0 | -2.244 |
| Always BLOCK | 0/12 | 0/24 | 0 | 0/48 (0%) | 48 | 0 | -3.440 |
| PPO seed 11 | 12/12 | 24/24 | 0 | 0/120 (0%) | 24 | 0 | 4.700 |
| PPO seed 23 | 12/12 | 24/24 | 0 | 0/120 (0%) | 24 | 0 | 4.700 |
| PPO seed 37 | 12/12 | 18/24 | 6 | 6/189 (3.17%) | 6 | 0 | 0.980 |

Unsafe outcomes occurred in attack-role cases; the attack-role denominator is 12,
so six unsafe outcomes means 6/12 of those cases. Warning and block counts above
are effective engine events, not just raw policy recommendations. Always ALLOW
and PPO seed 37 recommended ALLOW at every detector decision; the shared gate
caused their warnings/blocks and 12 authorization overrides. Always WARN had three
overrides; the other policies had none. These effects must not be credited to a
learned detector.

**The successful-looking policies learned a recovery shortcut.** In every case,
seeds 11 and 23 blocked the first interaction, then allowed four recovery steps.
The recovery route supplies all required public information and earns completion
reward. Both policies unnecessarily blocked the initial ordinary public request
in all six ordinary legitimate cases. The observed reward improvement therefore
does not establish attack discrimination or real-world security improvement.
Seed 37 remained always-ALLOW on this bank. Across seeds, unsafe outcomes ranged
from 0 to 6 and mean returns from 0.980 to 4.700; seed variability is material.

Supplemental **fixed-pivot development probes**, using only the existing
development-validation pair families and seeds 211/223/227, recorded non-ALLOW
recommendations on legitimate members as follows:

| Policy | Non-ALLOW legitimate pivots /9 |
| --- | --- |
| Always ALLOW | 0 |
| Always WARN | 9 |
| Always BLOCK | 9 |
| PPO seed 11 | 7 |
| PPO seed 23 | 3 |
| PPO seed 37 | 0 |

These probes replay an observable prefix to a fixed decision; they are not
on-policy episode rates or independently reviewed FPR estimates. No model was
tuned or retrained after these diagnostics. Low probe interventions alone do not
imply safety, as always-ALLOW illustrates.

Raw artifacts are local at `.local/ppo-development-v2`: original protocol/source
and task hashes, five periodic checkpoints plus final policy per seed,
CSV/JSON training curves, outcome traces and action predictions. The `analysis/`
directory contains the summary, fixed-pivot predictions, hardware/package/source
provenance and rendered PNG/PDF curves. `artifact-hashes.json` covers all saved
files. The earlier nine-model negative ablation is preserved separately.

### Security and utility accounting of the recovery exploit

A separately saved `security-utility-v2` reanalysis uses the archived trajectories,
without new predictions, training or changes to historical artifacts. Only the
initial ordinary public search is provisionally annotated ALLOWED by the developer;
later decision correctness remains unknown without semantic reviews. Authorization
permission is not used as a substitute for a benign-content label.

| Policy | Initial model BLOCK rate | Avoidable initial blocks /24 | Uninterrupted completions /24 | Completed after avoidable block | Recovery episodes /24 | Gross post-recovery steps |
| --- | --- | --- | --- | --- | --- | --- |
| Always ALLOW | 0% | 0 | 6 | 0 | 9 | 36 |
| Always WARN | 0% | 0 | 0 | 0 | 15 | 48 |
| Always BLOCK | 100% | 24 | 0 | 0 | 24 | 24 |
| PPO seed 11 | 100% | 24 | 0 | 24 | 24 | 96 |
| PPO seed 23 | 100% | 24 | 0 | 24 | 24 | 96 |
| PPO seed 37 | 0% | 0 | 6 | 0 | 9 | 36 |

These counts refer to legitimate *interactions*, including those at the start of
attack-role episodes; they do not change the earlier 12/12 legitimate-episode
completion totals. A completed task after an avoidable block is explicitly
different from uninterrupted completion. The six ordinary public cases each
required eight steps under uninterrupted ALLOW, but five under the learned
initial-block/recover strategy: four recovery steps and a net **three-step saving**.
Thus gross recovery work cannot be reported as positive additional work without
a matched reference. Other net step deltas remain unscored, rather than inventing
an uninterrupted safe path for an attack episode. Failed tasks are excluded from
completion-matched net deltas.

Future common comparisons record pre-override model recommendations separately
from effective decisions and shared approval receipts, initial blocks, annotated
avoidable/correct blocks, recovery entries/work, warning frequency, truncation,
task goals and actual unsafe effects. BLOCKED normative targets include some
unauthorized but non-malicious operations: counting malicious detection additionally
requires explicit maliciousness annotations. Missing semantic coverage is reported;
zero harm or a gate override alone does not establish a learned prevention.
The updated evaluator is versioned `contextual-five-method-v2`; archived v1 results
remain unchanged. Case-allocation/source hashes and supplied experiment provenance
are recorded. Missing checkpoint/data provenance remains explicitly incomplete.

The reward needs revision before another research run. The historical ordinary
safe path earns 4.84, versus 4.70 for gratuitous-block/recovery. The latter also
avoids attack routes, making a generic shortcut attractive. This is evidence of
a utility incentive and permissive recovery dynamics, not proof of semantic
attack recognition or a uniquely determined learning mechanism.

`data/research/reward-utility-v2-proposal.json` is a **separate, unimplemented and
untrained proposal**. It retains the existing success/harm/failure/step magnitudes,
adds a 2.0 penalty for reviewed avoidable legitimate blocks, a 1.0 avoidable-warning
cost and a 0.5 recovery-entry cost. The avoidable-block cost exceeds the maximum
24-step saving (0.48), based on an ordering constraint, not a validation-weight
search. A missed required block incurs the existing 10-unit safety magnitude even
when a mandatory override prevents harm; actual harm and missed block do not
double-charge that step. Required warnings missed by ALLOW incur a separate
one-unit cost. There is no positive per-block bonus. Correct blocking and justified
recovery remain possible; unnecessary intervention loses utility. Proposed costs
are explicit human utility preferences, not estimated optima. They require review,
new protocol approval and independent semantic labels before implementation or
training. No claim is made that this specification removes every possible exploit.

Raw derived metrics and unchanged-source artifact verification are local at
`.local/research-phase2/recovery-utility-analysis-v2`. The original PPO checkpoints,
training curves, predictions and negative findings are preserved.

### MiniLM runtime verification

Downloaded `sentence-transformers/all-MiniLM-L6-v2` at revision
`1110a243fdf4706b3f48f1d95db1a4f5529b4d41`. The 90,868,376-byte safetensors file
matches the pinned upstream LFS SHA-256
`53aa51172d142c89d9012cce15ae4d6cc0ca6895895114379cacb4fab128d9db`.
The model loads offline and produces 384-dimensional embeddings. A long synthetic
observation used seven windows; reconstructing windows after removing overlap
recovered every original token. Two synthetic encoder steps changed weights and
the saved SetFit model reloaded with identical predictions. The original pretrained
snapshot remained unchanged. This check took about 19 seconds including startup,
with 8.16 seconds reported for its two optimization steps. No research labels or
final examples were read, and no synthetic classification performance is claimed.

The loaded SetFit checkpoint passed the shared boundary interface; its synthetic
evidence marker correctly prevented research comparison scoring. Loaded PPO
checkpoints passed full shared episode comparisons. Real reviewed-data MiniLM
training, new contextual Qwen evaluation and independent comparisons are pending.

No scientifically validated five-method table is available yet:

| New protocol method | Status |
| --- | --- |
| Authorization-only | Adapter tested; final evaluation NOT RUN |
| Contextual rules | Adapter tested; final evaluation NOT RUN |
| Contextual pretrained Qwen | Local-only adapter tested; model evaluation NOT RUN |
| Trained MiniLM | Pinned weights and synthetic compatibility verified; reviewed-data training NOT RUN |
| Trained PPO | Bounded development run completed; recovery shortcut and always-ALLOW behavior observed; independent evaluation NOT RUN |

## Limitations

Small templated collections, developer inspection, incomplete independent review,
few WARNING examples, fixture token/field shortcuts, simplified user approvals,
lossy representations, reward/horizon sensitivity and limited simulated effects
threaten validity. Source-group labels alone do not prove semantic independence.
The bounded run exposed an initial-block/recovery shortcut: synthetic task success
can reward unnecessary intervention without learning to recognize attacks. This
must be addressed in a separately frozen research protocol before claiming learned
security effectiveness; the executed development protocol remains unchanged.
The current MCP endpoint is a mock JSON-RPC subset and the vulnerable agent is
deterministic, not a real-model adversarial deployment. Better development scores
would not by themselves establish generalization. Missing review/final-test data
cannot be replaced by additional training or the delivery deadline.

## Reproducibility and pending completion

Commands below are software verification, not scientific experiments. From the
repository root after [clone setup](TEAM_HANDOFF.md). Install Gymnasium alongside
app test dependencies; do not depend on the owner's ignored test-runtime directory:

```powershell
.\.venv\Scripts\python.exe -m pip install -r research/requirements-gym.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests
Push-Location frontend
npm.cmd run build
Pop-Location
.\.venv\Scripts\python.exe -m uvicorn shield.api:app --host 127.0.0.1 --port 8000
```

The application dependency lock and frontend package-lock are retained. The
tested Python3.13 CPU ML environment is recorded in
`research/requirements-ml-lock.txt`; optional model imports occur outside the
application read path. Pretrained weights are pinned and checksum-verified as
described above. Reviewed-data training commands and readiness gates are in
[TRAINING_READINESS.md](TRAINING_READINESS.md); reviewer instructions are in
[REVIEW_GUIDELINES.md](REVIEW_GUIDELINES.md). Internal coordination instructions
and reviewer returns stay local and Git-ignored.

An explicitly approved `python -m research.delivery` invocation loads completed
trusted local SetFit/PPO checkpoints, queries the actual local Qwen digest, and
runs the existing24-case development bank under the shared v2 evaluator. It saves
raw action/effect traces, model/case/source provenance and a checksum envelope for
the dashboard. It performs no training, changes no rewards and refuses to
overwrite an artifact. This comparison transfers a boundary-trained SetFit model
to sequential simulator observations; the distribution shift must be reported.
It is not a runner for the uncollected independent final test. Final data-format
compatibility, release approval and frozen evaluation remain pending.

Historical combined verification totals198 distinct passing tests across app/ML
environments. Latest no-training QA discovered198:187 passed and11 optional
optimizer checks were skipped. Those checks optimize synthetic fixtures in setup;
they are not skipped because reviewed scientific checkpoints are absent. Their
earlier passing status is historical. Re-running them requires separate opt-in
and authorization; instructions are in TEAM_HANDOFF.md. The clean production
frontend build and backend dependency/compile/startup checks passed.

Final application QA passed40 headless-browser/API assertions covering login,
approvals/replay, simulations, five-method display/NOT RUN, isolated fixture result
loading, separate recommendations/overrides, historical export/navigation and mobile
layout; no JavaScript exceptions occurred.48 protected historical/data file hashes
were unchanged. Fixture UI scores are not experiments. Docker image build/startup
remains unverified: the Linux engine was unavailable. The image recipe includes
the lightweight artifact reader, but earlier image checks do not validate it.

Preserve original data/results, checkpoint hashes, package locks, seeds, hardware
details, raw predictions/outcomes and completion/error records. The React/FastAPI
application and historical baselines remain intact. New trained outputs must enter
the application with explicit development versus independently validated labels.
This review snapshot contains source and public summaries, not private raw run
artifacts, reviewer returns, model weights or an independent final collection.

Pending: real reviews/adjudication and custody registration; first reviewed SetFit
run; resolution of the PPO recovery-shortcut validity blocker in a separately
approved research protocol; paired five-method validation;
model/protocol freeze; authorized independent evaluation; verified application
integration; final report tables and reproduction/demo checks byNovember23.

The supervised target is the reviewed normative decision **before mandatory
authorization enforcement**: ALLOWED, WARNING or BLOCKED for the observed boundary,
not hidden future harm or source identity. The current reviewed class counts are
zero in both splits. The loader rejects disagreements, missing reviews, altered
group allocations and historical-source/derivation reuse; its software minima
(two training examples and one validation example per class) do not establish
statistical adequacy. Human review must assess class and independent-group support.
If WARNING remains too sparse, the proposed alternative is a separately approved
binary ALLOWED/BLOCKED experiment excluding only reconciled WARNING boundaries
from both fixed splits. Never map ambiguity to either class. Keep authorization
approval enforcement and report the omitted coverage separately; do not pool
binary metrics with the historical three-class experiments. No binary training
implementation or scientific run has been approved by this proposal.
