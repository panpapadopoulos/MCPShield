# Phase 2A research data tools

This guide preserves the data-foundation milestone. For current implementation,
completed development training, dashboard integration and open research gates,
use [PROJECT_STATUS.md](../PROJECT_STATUS.md). The data-only CLI described here
does not train; separate supervised/PPO pipelines now exist.

For the next collection, see [dataset expansion](DATASET_EXPANSION.md) and the
[independent review guidelines](REVIEW_GUIDELINES.md). The pilot below is preserved.

This is an offline, standard-library-only data foundation. It does not train a
model, implement RL, execute tools or call an LLM. The existing application and
historical experiments continue to use their original code and datasets.
Pilot labels are **proposed, assistant-authored and entirely unreviewed**.
Passing tests establishes implementation contracts, not scientific validity.

## Schemas and trust boundaries

`research/observations.py` implements `mcp-observation-v1` as plain JSON:

```json
{
  "schema": "mcp-observation-v1",
  "authorized": {
    "task": "User-authorized task from trusted application state",
    "scope": {
      "file_reader": {
        "resources": ["/public/workshop.txt"],
        "permissions": [],
        "consent_permissions": []
      }
    }
  },
  "current": {
    "phase": "request",
    "tool": "file_reader",
    "description": "Untrusted tool description",
    "arguments": {"path": "/public/workshop.txt"},
    "requested_permissions": []
  },
  "history": [],
  "history_omitted": 0
}
```

At response inspection, `current.response` contains the currently returned JSON;
the matching request's arguments and description remain visible. At request
inspection, the response field is absent. History contains only earlier observed
boundaries, including tool responses already available to the security layer.
Current responses are not automatically evidence the agent received them.
V1 contains observed tool boundaries, not hypothetical future branches or approval
outcomes. Future runtime adapters must append actual executed events and trusted
grant updates; do not preload a planned trajectory as observed history.

`build_observation(episode, event_index)` reads only that event prefix and explicit
input fields. At most eight prior boundaries remain, with an omission count.
Observations exceeding100,000 UTF-8 bytes fail rather than silently lose content;
NaN, non-JSON values, malformed permissions and invalid event ordering fail.
Canonical JSON from `model_text` can feed text classifiers, pretrained models,
or a future RL encoder; no encoder/model is downloaded here.

IDs, labels, split membership, provenance, reward, expected outcomes and hidden
effects are never selected as model features. Actual untrusted arguments/responses
remain intact, even if a tool's ordinary data contains a key named `label` or
text resembling an evaluator field. Stripping such content would change the
security problem. This allowlist blocks structural leakage, not every possible
semantic label clue: humans must still audit wording and dataset shortcuts.

`research/authorization.py` is a separate constraint arbiter for future research
adapters. Tool/path scopes and non-grantable permissions override an ALLOWED
recommendation. Only explicitly consentable permissions can produce a permission
warning; a verified consent handler can grant only that subset. Tool descriptions
cannot grant authority. The arbiter preserves a detector's stricter decision.
It is not wired into the historical gateway, whose experimental meaning is kept.
The task/scope record must come from trusted app state; Python objects do not
authenticate their own origin.

## Versioned pilot dataset

`research.pilot.generate()` deterministically creates
`data/research/phase2a-pilot-v1.json`: **16 episodes,27 decision boundaries**.
These are newly authored static interaction examples, not executed simulations
and not recorded real attacks. No real server receives a safe/malicious label.
No external metadata is required for this small pilot.

Coverage: ordinary/Unicode weather; quoted command examples in a public lesson;
an apostrophe in a database query; a scoped-consent request; two credential-pretext
response variations; two tool-description hijack variations; restricted-file
access; a shell pipeline in a city argument; non-grantable write/admin permissions;
an unauthorized next-action response; a four-boundary public retrieval/read
sequence; an ordinary provider error; and ambiguous upload advice.

`research-dataset-v1` holds version/status and episodes. Each `research-episode-v1`
has an audit ID, trusted authorization, ordered request/response events and
separate `proposed_labels`. Each boundary label contains event index, decision
(`ALLOWED`, `WARNING`, `BLOCKED`), category and rationale. A benign initial request
is not labeled malicious simply because its later response contains an attack.
The single multi-step pilot is input-history coverage, not a DRL environment.

Provenance records author, generator version, original fixture key, parent IDs,
source groups, template group, derivation family, license note and unreviewed
status. For future metadata adaptations, retain immutable upstream revision/hash,
original metadata and mapping rationale in provenance; labels describe the adapted
interaction, never the upstream repository. Manually group forks under a shared
source-group key. GitHub URL/case/.git aliases are canonicalized automatically.
All paraphrases/derived attacks must retain their family and ancestry tags.

## Reproduce and inspect

Run from the Git repository root using the existing app venv. Generate the
historical dataset first using README instructions if it is not present.

```powershell
.\.venv\Scripts\python.exe -m research.cli generate
.\.venv\Scripts\python.exe -m research.cli status
```

Regeneration is byte-identical and idempotent. Commands refuse to overwrite a
different existing artifact. Version changed data/labels and use fresh output
paths; never overwrite review evidence. The manifest hashes parsed canonical JSON
so platform line endings do not change dataset identity.

## Splits and final-test custody

The pilot has a deterministic **13-episode train /3-episode validation development
allocation**, seed23. These are draft allocations, not training-ready samples.
Source, template, derivation-family and ancestry connections, exact observable
trace duplicates, and near-duplicate descriptions form transitive components.
Description comparison uses casefolded token-set Jaccard similarity >=0.80;
exact token matches are grouped too. Components stay together even if doing so
hurts balance. One remaining component causes failure, never a forced leaky split.
This small split does not guarantee all classes in each partition.

Historical data is required for exclusion checks. All158 historical cases are
excluded by known IDs, ancestry references, historical sources, historical template
tags and tool argument reuse, including copied requests with extra fields,
regardless of new IDs or descriptions. Content/derivation overlap
that cannot be detected lexically still requires human review. Historical labels
and previous test results must never guide new model selection. Split verification
recomputes the manifest against both dataset and historical exclusion hashes.

**There is no genuinely untouched final test yet.** All pilot cases were exposed
during development, so none are assigned to `test`. The explicit reservation file
is `NOT_COLLECTED`, not an empty test disguised as a completed held-out set.
Before model selection, an independent custodian should collect/seal fresh final
interactions, register source/template/derivation exclusion groups and a SHA-256
content commitment in a new reservation version, set `RESERVED_EXTERNAL`, and
keep the actual interactions outside the development repo. Optional reservation
description texts permit duplicate screening; prefer an external custodian audit
if revealing those texts would expose final-test material. Development splitting
rejects registered overlaps. A custodian must also screen near-duplicates and
unregistered fork/semantic families. No file flag proves untouched custody.

`split_development(..., reservation=...)` supports that contract now. The CLI reads
the reservation file; use fresh versioned dataset/manifest paths when it changes.
Training preparation exposes only train/validation; final-test execution and
access logging are deliberately not implemented in Phase2A.

## Independent label review

Export locally for two real reviewers who did not author the fixtures:

```powershell
.\.venv\Scripts\python.exe -m research.cli review-export --reviewer reviewer-A --output .local/research-phase2/reviewer-A.json
.\.venv\Scripts\python.exe -m research.cli review-export --reviewer reviewer-B --output .local/research-phase2/reviewer-B.json
```

Each form shows the original complete interaction, task/scope, current boundary
index and an empty review. Reviewers may inspect the full interaction for labeling,
but must judge each boundary using only information available at that boundary.
Export with `--show-proposals` to additionally show proposed decision, category,
expected security action and rationale. Blind export is the default to reduce
anchoring; do not show one reviewer's decisions to the other before submission.

For each item set `action` to `accept`, `reject` or `modify` and supply a nonempty
`justification`. `accept` uses the unchanged proposed label. `reject` leaves
`reviewed_label` null and blocks preparation. `modify` supplies a complete label:

```json
{
  "event_index": 1,
  "decision": "WARNING",
  "attack_category": "ambiguous_instruction",
  "rationale": "Explain the specific ambiguity and allowed scope."
}
```

On a blind form, use `modify` to supply your independent label without seeing the
proposal. Delete unfinished items if submitting a partial review; they remain
unreviewed. Preserve interaction text and hashes unchanged. Set `human_attestation`
and `independent_attestation` true only after personally reviewing the submitted
items. Never have software fill those claims on behalf of a reviewer.

Initialize a local empty ledger and import new versions:

```powershell
Set-Content -LiteralPath .local/research-phase2/reviews-0.json -Value '[]' -Encoding utf8
.\.venv\Scripts\python.exe -m research.cli review-import --form .local/research-phase2/reviewer-A.json --ledger .local/research-phase2/reviews-0.json --output .local/research-phase2/reviews-1.json
.\.venv\Scripts\python.exe -m research.cli review-import --form .local/research-phase2/reviewer-B.json --ledger .local/research-phase2/reviews-1.json --output .local/research-phase2/reviews-2.json
.\.venv\Scripts\python.exe -m research.cli status --ledger .local/research-phase2/reviews-2.json
```

Original and reviewed labels, reviewer, action, justification, timestamp, proposal
visibility, dataset/episode hashes and a record hash chain are retained. Author
self-review, duplicate votes, stale forms and changed interaction text are rejected.
Two distinct agreeing reviewer attestations yield `AGREED_ATTESTED`; disagreement,
rejection or one review remains unresolved. This is not authenticated identity or
proof of scientific independence: a human must verify reviewer identity and role.
The hash chain detects accidental changes, not a person rewriting and rehashing
the whole ledger. Keep original submitted forms and versioned ledger digests.

Conflict adjudication is a human task. Record the rationale and both source reviews,
then create a new versioned dataset proposal retaining original labels in provenance
and linking parent versions; collect fresh reviews of that version. Do not erase a
dissenting review or manufacture consensus. Automated adjudication is not provided.
Pilot review status remains **27 UNREVIEWED**; test-only mock reviewers do not
create dataset review evidence.

## Future supervised input preparation

```powershell
.\.venv\Scripts\python.exe -m research.cli prepare --ledger .local/research-phase2/reviews-2.json --output .local/research-phase2/prepared-train-v1
```

This command will currently refuse because real reviews do not exist. Once eligible,
it writes separate `features.json` (observations only), `targets.json` (decisions)
and an audit manifest (hashes/split, never model input). It never fits a model.
Do not feed the dataset, review forms or audit manifest wholesale to a classifier.
Two agreeing attestations are a mechanical eligibility gate; humans must still
check class balance, source/family diversity, near-duplicates and label quality.

Proposed first fine-tuned baseline: SetFit with
`sentence-transformers/all-MiniLM-L6-v2`, encoder contrastive fine-tuning followed
by its logistic-regression head. The model card specifies384-dimensional embeddings;
SetFit supports CPU training, but security effectiveness must be measured.
See [SetFit's method](https://huggingface.co/docs/setfit/en/conceptual_guides/setfit)
and the [MiniLM model card](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2).

The earlier model/configuration proposals are superseded by the tested Python3.13
CPU SetFit pipeline: batch8, encoder LR2e-5, one epoch capped at64 steps,256-token
overlapping document windows, head C1/max_iter1000 and fixed seeds. MiniLM is
downloaded and verified on the development machine; neither weights nor local
environments are included in Git. See [training readiness](TRAINING_READINESS.md)
and [clone setup](TEAM_HANDOFF.md). Reviewed-data training remains NOT RUN; no
parameter search or additional model architecture is required for this deadline.

Suggested next data target:300-600 reviewed decisions across at least100 diverse
episodes, with adequate WARN examples and independent source/family components.
These are collection targets, not guaranteed statistical sufficiency; use learning
curves and uncertainty to decide whether expansion is needed. A16-episode pilot
cannot support generalization claims. Phase2B should first complete review and
expand the collection, seal the independent test, then implement/run the bounded
supervised baseline. Separate PPO development experiments are now complete and
their negative/shortcut findings are retained in the report. Historical collection
targets are not permission to expand scope before November23.
