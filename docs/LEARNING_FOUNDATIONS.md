# Learning interfaces and sequential environment foundation

Current execution status and commands superseding the initial readiness notes
below are in [Training readiness](TRAINING_READINESS.md). The real SetFit backend
and downloaded pinned MiniLM pass synthetic training/reload checks; reviewed-data
training remains pending. The approved bounded PPO development run is complete;
see the report for its recovery-shortcut and always-ALLOW findings.

No reviewed-data supervised or independently validated PPO experiment has run.
Bounded synthetic optimizer tests
are described in [PPO infrastructure](PPO_INFRASTRUCTURE.md). Existing38 episodes/68 boundaries remain
UNREVIEWED; independent final test remains NOT_COLLECTED. Historical data, detector
code and experiment reports are unchanged. Synthetic test fixtures below are
software checks, not model-performance evidence.

## Implemented supervised path

`research.supervised` implements reviewed train/validation loading, canonical
`mcp-observation-v1` text, separate labels, duplicate-observation exclusion,
three-class confusion/per-class/macro-F1 metrics, configuration/seeds, local
snapshot hashing, model/source/data/review/package provenance, checkpoint/loss-log
storage and a prediction interface. It rejects missing class support, unresolved
reviews, absent explicit run approval, and missing sealed-custody registration.
Its CLI checks data readiness only; it cannot start training:

```powershell
.\.venv\Scripts\python.exe -m research.supervised --dataset data/generated/research-expansion-v3.json --splits .local/research-phase2/expansion-v3-package/splits.json --ledger .local/research-phase2/expansion-v3-package/reviews-0.json
```

This currently refuses the empty real ledger. No final-test loader is provided.
`train(..., approved=True, custody_record=...)` is a future opt-in Python entry
point after human authorization/data readiness. It uses only a complete local
SentenceTransformer snapshot, a declared40-character model commit, offline flags
and CPU execution. No Hub model download fallback exists. Completion/error status
is separate from immutable initial provenance; incomplete runs yield no valid scores.

Candidate: SetFit/MiniLM (contrastive encoder tuning plus logistic head), not
training an LLM from scratch. Defaults: seed11 (repeat later with23/37), batch8,
encoder LR2e-5, one epoch capped at64 optimizer steps, head C1/max_iter1000.
The current backend covers complete observations with overlapping256-token windows
and pools window embeddings once per document. It rejects more than64 windows
instead of silently truncating. This representation has passed software checks;
its classification effectiveness remains unvalidated.

SetFit dependencies are installed and tested in the isolated Python3.13 CPU ML
environment. Actual gradient training and checkpoint reload have passed using a
tiny randomly initialized local BERT and the downloaded pinned MiniLM on synthetic
observations. MiniLM weights are verified; no reviewed-data model has been trained. See
[execution commands and gates](TRAINING_READINESS.md). Deterministic seeds are
not a cross-platform bitwise reproducibility guarantee.

## Implemented sequential prototype

`research.sequential.SequentialEnv` is a separate in-memory task engine using
the existing virtual Sandbox; it does not change historical Agent/Gateway. Minimum
new state is a task graph, observed event history, scoped grants, recovery branch,
step budget and hidden effect ledger. Request execution, response delivery and
recovery are separate transitions. No real tools/services or unsafe commands run.

- Observation: existing tool/task/scope/phase/history schema only. No node IDs,
  fixture variant, future responses, labels, reward or outcome ledger is encoded.
- Actions:0 ALLOW,1 WARN,2 BLOCK. Every recommendation passes through the same
  independent authorization arbiter before execution.
- ALLOW executes a request or delivers a response. A poisoned result can cause a
  later search request containing a virtual secret; only executing that request
  records the disclosure. Blocking the result or follow-up prevents it.
- BLOCK may select another public source; blocking the last source fails the task.
- WARN charges an approval cost. Consent depends on trusted consentable scope and
  a seeded user preference, never a hidden attack label. A generic warning does
  not receive an omniscient approval. Denial may recover via another source.
- Episodes contain multiple boundaries. In the archive-recovery fixture, an
  identical current call reappears after an alternative has failed; its history
  and remaining recovery opportunities differ. Tests exercise both continuation
  and terminal failure from that state. This goes beyond independent labeled calls.
- Reward: -0.02/step, -0.20/block, -0.25/approval, +5 terminal task success,
  -10 first irreversible virtual harm, or -3 terminal failure/truncation without
  harm. No gold-label matching rewards and no reward for each blocked call.
  These are unvalidated research hypotheses, not a proven security objective.
- Termination marks success, failure or harm; horizon exhaustion is truncation.
  Stepping after completion fails, so harm/rewards cannot be replayed away.

Deterministic tests check always-allow on clean/poisoned tasks, always-block,
always-warn, a fixture-only safe recovery policy, permission overrides, scoped
consent, same-call/different-history recovery and horizon behavior. None is a
trained policy or a claim about the development corpus.

`research.gym_env.MCPTaskEnv` is a real Gymnasium Env with Discrete(3) actions and
a Dict observation of padded UTF-8 bytes plus length. It does not truncate. Actual
Gymnasium1.2.2 `check_env` and observation-space tests passed locally. Dependencies
were installed only in ignored `.local/gym-runtime`; application dependencies are
unchanged. The byte representation is a contract/debug transport, **not a chosen
semantic PPO encoder**. A frozen text encoder and shared supervised-head control,
many more reviewed task graphs and reward sensitivity checks are still needed.
A bounded PPO integration with a separate hashing wrapper now exists; see the
PPO infrastructure guide. The38 static research episodes are not automatically converted into
valid branching RL tasks.

## New comparison and remaining experimental design

`research.comparison` defines no detection, rules, pretrained Qwen, supervised and
DRL policy interfaces. In this new comparison, "no defense" means authorization
only; historical fully undefended experiments remain separate. All methods get
identical observable context, task variants, user preferences and seeds; evaluator
info is never passed to a policy. Recommendations, effective decisions, policy
constraints/overrides, approvals and effects are recorded separately. The legacy
rule adapter retains its baseline behavior, including its own conservative checks;
the shared independent gate applies to every method regardless.

The original diagnostic runner is explicitly SYNTHETIC_DIAGNOSTIC_ONLY. The
current `research.five_methods` v2 supplies contextual Qwen, loaded SetFit/PPO and
consistent authorization/utility interfaces. Missing providers are NOT RUN.
`research.delivery` publishes explicitly approved development artifacts to the
separate read-only app panel. Synthetic fixtures cannot become independently
validated model scores. The original historical simulator remains unchanged.

Before scientific comparison: freeze approved model/data/protocol versions, use
reviewed phase labels and separately verified episode effects, pair evaluation
seeds/tasks, run at least3 training seeds, and compare source/attack-family panels.
Report precision/recall/F1/FPR/FNR for actual classification, attack success and
legitimate completion for episodes, approval burden, operational failures, mean/p95
inference and total latency, plus actual training time/losses. Report shared-policy
interceptions separately from detector-only performance. Use cluster-aware
uncertainty by source/episode, not each repeated boundary as independent evidence.
Measure latency outside the deterministic simulator; current step charges are not
wall-clock measurements. Select settings on validation only; no assumption of
supervised/RL superiority. Reward curves alone do not demonstrate security.

## Concrete independent final-test protocol

1. Name a custodian outside model development and two independent label reviewers.
   Give the custodian the development/historical exclusion manifest, annotation
   policy and task-scope schema, not instructions to paraphrase existing attacks.
2. Collect new lawful inert metadata/task examples from repositories outside all
   development/historical/fork groups. Independently design attack mechanisms
   outside registered derivation families; new wording/names are insufficient.
   Never execute unsafe tools. Preserve source versions, rights, adaptation and
   derivation lineage. The custodian checks near duplicates and semantic overlap.
3. As a collection target, aim for >=10 new source groups, >=6 distinct new
   operational derivations, benign/difficult benign and unsafe interactions, and
   >=20 genuinely reviewed WARN boundaries. Establish episode/class/source counts
   prospectively; these targets do not guarantee sufficient statistical power.
4. Two reviewers label decision-time prefixes blindly and independently, recording
   intent uncertainty separately from decisions. Adjudicate disagreements and
   preserve original votes. Developers do not see final interactions or labels.
5. Before model selection starts, seal exact interaction, label and review files
   in custodian-controlled storage. Record SHA-256 commitments, timezone-aware
   sealing time, identities, collection/semantic-separation attestations and an
   access log. Do not put final contents in this repository.
6. Register only public custody metadata against the frozen development exclusion
   hash. `research.custody.register_seal` rejects extra fields/final examples,
   overlapping group names, missing commitments or attestations. It does not
   authenticate identities, prove semantic separation or read final content.
7. Freeze model/checkpoint hashes, development hash and evaluation protocol after
   sealing. Record the freeze and exact seal hash. `release_gate` requires explicit
   release approval and compatible commitments/time ordering. Timestamps and
   attestations require external verification; hashes are not proof of independence.
8. Only then does the custodian release a read-only copy to the declared evaluation
   process (or evaluate privately), verify bytes against commitments, and record
   who accessed what/when. No tuning after scores. Fixes require a new independent
   final test or transparently labeled exploratory reanalysis.

No custodian payload, seal or human review has been fabricated. Current status
remains NOT_COLLECTED. Public exclusion export and custody functions provide only
infrastructure; human collection/review/sealing are unavoidable external actions.
