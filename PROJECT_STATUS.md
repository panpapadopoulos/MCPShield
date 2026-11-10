# MCPShield: authoritative project status

Updated November 9, 2026. **Hard deadline: November 23, 2026.**
This overview supersedes October-era status statements. Start with
[teammate setup](docs/TEAM_HANDOFF.md); verified research findings are in the
[research report](docs/RESEARCH_REPORT.md). Earlier source/status versions remain
in Git history and the existing docs/history directory.

## Purpose and architecture

MCPShield studies whether inspection of AI tool requests/responses can prevent
unsafe simulated effects while preserving legitimate task utility. React/Vite
connects to FastAPI, a resumable security gateway, four in-memory tools and a
deterministic vulnerable agent. This is a local research prototype and mock MCP
subset, not a demonstrated production upstream MCP proxy or real autonomous agent.

The historical simulator retains no defense, rules, pretrained local Qwen and
hybrid. The new research comparison adds trained SetFit/MiniLM and PPO, using
identical observable schemas, separate mandatory authorization, versioned scenario
allocation and security/utility metrics. Its no-defense row means authorization
only; it is not the historical entirely undefended baseline. No detector receives
labels, hidden effects or future tool responses as input.

## Implemented components

- React/FastAPI application, live activity, dataset explorer and JSON export.
- Request/response gateway, explicit grants, rule detector and historical hybrid.
- Real local Qwen classifier and preserved historical evaluation tools.
- Bearer authentication, same-origin controls and exact-phase one-time approvals.
- Canonical observable feature pipelines; grouped development allocations and
  historical source/derivation exclusions.
- Independent-review packages, hash-bound imports, disagreement rejection and
  custodian metadata/seal/release gates. These do not manufacture human review.
- SetFit/MiniLM loaders, full-token overlapping windows, training, checkpoint
  reload, prediction, metrics and model/data/review/source provenance.
- Gymnasium multi-step simulated environment; PPO training/checkpoints and fixed
  development protocols. Decisions affect progress, approval, harm and recovery.
- Five-method evaluator v2, separate raw recommendations/authorization overrides,
  interrupted versus uninterrupted completion and recovery utility accounting.
- Read-only five-method dashboard and approved comparison/export CLI. Missing or
  incompatible artifacts/models show NOT RUN; current publication is DEVELOPMENT_ONLY.

## Datasets and training status

| Item | Current status |
| --- | --- |
| MCPCorpus | 13,875 unlabeled metadata records at a pinned revision/checksum; raw data excluded from Git |
| Historical benchmark | 126 corpus adaptations plus32 authored controls =158;48 validation/110 inspected regression cases |
| Research expansion | 38 authored episodes/68 boundaries, all UNREVIEWED; generated metadata-derived content excluded from Git |
| Reviewed labels | No reconciled train/validation labels available; disagreements and missing reviews block fitting |
| Independent final test | NOT_COLLECTED; no seal, release or evaluation claimed |
| MiniLM | Downloaded/hash-verified on the development machine; synthetic two-step optimization/reload passed; weights not in Git |
| Reviewed-data MiniLM | NOT RUN; real labels/class support, custody registration and explicit run approval required |
| PPO | Development models trained; no independently validated attack-recognition performance |
| Reward utility v2 | PROPOSED / NOT EVALUATED, inactive; historical rewards/results unchanged |
| Scientific five-method/final comparison | NOT RUN |

The committed pilot is project-authored and distinct from the generated38-episode
expansion. Proposed labels are never independent reviews. Sparse WARNING support
may require a separately approved binary scope; no binary scientific run exists.

## Completed experiments

Historical110-case regression: rules prevented68/68 authored attacks and completed
41/42 legitimate tasks; Qwen missed one attack and completed40/42; hybrid prevented
68/68 and completed40/42. These single-pass controlled results do not establish
hybrid superiority or generalization. Preserve their historical policy/prompt.

Nine PPO development models (three representations x three seeds x64 steps) all
matched always-ALLOW, without demonstrated security improvement. A later frozen
run trained seeds11/23/37 for10,240 steps each (30,720 total;112 logged training
seconds). Seeds11/23 achieved zero simulated harm by blocking the first interaction
and taking recovery, including unnecessary blocks on all24 cases. They had zero
uninterrupted completions. Seed37 matched always-ALLOW with6 unsafe outcomes/24.
This is recovery exploitation, not reliable attack recognition. Detailed outcomes,
constant-policy comparisons, provisional FP probes and negative findings are in
[RESEARCH_REPORT.md](docs/RESEARCH_REPORT.md). Raw run artifacts/checkpoints stay local.

## Verification and application QA

- Historical combined verification:198 distinct tests passed across app/ML environments.
- Latest no-training QA:198 tests discovered;187 passed and11 optional optimizer
  integration checks skipped to avoid starting training. Those skips are not
  caused by missing scientific checkpoints; their setup explicitly optimizes fixtures.
- Backend dependency/compile/startup checks and clean locked frontend build passed.
-40 headless-browser/API assertions passed: authentication, approvals/replay,
  simulations, all five research rows, NOT RUN handling, isolated artifact loading,
  separate overrides, historical export/navigation and desktop/mobile layout.
-48 protected historical/data file hashes remained unchanged during browser QA.
- Current Docker image build/startup is NOT VERIFIED: Docker Desktop Linux engine
  was unavailable. Older image checks do not verify the changed current image.
- CI configuration exists; no successful remote run for this new branch is asserted.

## Scientific limitations

Unreviewed small templated collections, inspected historical tests, developer
adaptations, few WARNING cases, lossy feature encoders, simplified user approvals,
shortcuts in recovery dynamics and limited virtual effects restrict conclusions.
Zero harm can come from mandatory grants or unnecessary blocking. Completion alone
is insufficient; distinguish decisions, enforcement and security/utility outcomes.
Synthetic pipeline checks establish execution, not classification effectiveness.
MCPCorpus reuse terms are unresolved; do not publicly redistribute raw or generated
metadata-derived content. Source availability is not permission to relicense it.

## Remaining work to November 23

1. Owner-coordinated independent reviews/adjudication, class/group support and
   separate custodian collection/sealing; developers do not inspect final examples.
2. Explicitly approve/run reviewed SetFit training once gates pass; record real
   metrics, checkpoints, provenance and CPU time.
3. Approve/run the fixed shared development comparison with actual models. Keep
   the existing PPO negative findings; further PPO training is not required to finish.
4. Freeze models/protocol, obtain authorized final release, check released case
   compatibility and perform the locked independent evaluation without tuning.
5. Publish verified artifacts to the read-only app, complete pending report tables,
   reproduce/demo/test, and verify Docker build/startup when its engine is available.

Reviews/custody, uncertain class support, unknown learned-model performance and
limited time are the critical blockers. Do not replace missing evidence with
synthetic scores or generalization claims to meet the deadline.
