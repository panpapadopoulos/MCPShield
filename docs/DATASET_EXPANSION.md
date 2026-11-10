# Research development expansion

Current reproducible generator version: `research-expansion-v3`. This extends the
16-episode Phase2A pilot without changing that pilot, the158 historical scenarios,
the application, or previous model results. V1/V2 local artifacts are earlier drafts;
use the V3 package below. No training or model inference is performed.

## Coverage and composition

The pilot lacked real metadata lineage, varied native argument schemas, explicitly
authorized writes, recipient/destination scope, nested directives and delayed
attacks in multi-call tasks. The expansion adds22 deliberately authored examples,
not a Cartesian product of attacks and tools. The resulting collection has:

| Draft measure | Count |
| --- | ---: |
| Episodes / decision boundaries |38 /68|
| Retained pilot / new metadata-backed episodes |16 /22|
| Proposed legitimate / malicious / ambiguous episodes |19 /18 /1|
| Proposed legitimate / malicious / ambiguous boundaries |49 /18 /1|
| ALLOWED / BLOCKED / WARNING proposals |47 /18 /3|
| Distinct observed tool names / real metadata repositories |15 /8|
| Multi-call episodes |4|
| Independent grouping components |20|
| Exact observable-trace duplicate pairs |0|
| Metadata/content duplicate-screen candidate pairs |16|
| Candidate pairs crossing splits |0|
| Real human reviews received |0|

The legitimate/malicious/ambiguous counts are **interpretations of proposed category
annotations**, not verified intent or effects. `scope_ambiguity` is a legitimate
consent question; `ambiguous_instruction` remains uncertain. WARNING is not
automatically a malicious label. The source is never itself labeled malicious.

Boundary categories: none47, prompt injection4, tool poisoning3, malicious
response3, unauthorized file access2, command injection2, excessive permissions2,
scope ambiguity2, ambiguous instruction1, unauthorized internal-resource access1,
and unauthorized transfer1. Labels remain provisional and entirely UNREVIEWED.

The new examples cover authorized publishing, escaped code in HTML, a publication
verification pretext, public structured extraction, an excluded internal URL,
poisoned metadata, an authorized email, hidden copy recipients, scoped copy consent,
browser task creation/polling with benign and poisoned outcomes, aggregate analytics,
non-grantable administrative permissions, a fictional service token, document OCR
and restricted-file access, instructions inside scanned text, route-to-ETA history,
shell text in a route identifier, benign security advice, domain arrays and a nested
credential-transfer directive. No email, deployment, command, network access or
file read actually occurs. These are authored interaction records, not attack logs.

## Real metadata provenance

Uses the already downloaded, checksum-verified MCPCorpus snapshot:

- Repository: https://github.com/Snakinya/MCPCorpus
- Revision: `295fe37cd972ea9aa1b48578b2d7bcc40a72ee12`
- File: `Website/mcpso_servers_cleaned.json`
- SHA-256: `cc14fc4fe5c68b73e77cbaa3e64fc2b58616a8e61d0e96d92b8fd861702b9e20`

| Record | Metadata repository | Tools represented |
| --- | --- | --- |
|7029|TencentEdgeOne/edgeone-pages-mcp|deploy-html|
|2415|tinyfish-io/agentql-mcp|extract-web-data|
|9122|railsware/mailtrap-mcp|send-email|
|7611|302ai/302_browser_use_mcp|createBrowserAgentTask, getBrowserAgentTaskResult|
|13514|microsoft/clarity-mcp-server|get-clarity-data|
|9246|intsig-textin/textin-mcp|recognition_text, doc_to_markdown|
|8070|kennyfong19931/mcp-hk-transport-eta|get-route, get-eta|
|3273|bingal/FastDomainCheck-MCP-Server|check_domains|

These eight repositories are outside the historical benchmark's selected source
set. This is purposive selection, not representative random sampling. Original
names, descriptions and input schemas are preserved with hashes in provenance;
poisoned description suffixes, tasks, arguments, responses, permissions extensions
and labels are authored adaptations. Upstream commands/configuration are never
executed. Source schema properties are not claims that our historical sandbox
implements those tools. Generic native-tool resource enforcement is not integrated
into the application; these new tools are data only.

The snapshot manifest notes missing repository-wide reuse terms. Metadata-backed
dataset exports and review packs stay in Git-ignored generated/local directories.
Check applicable reuse terms before publishing/distributing excerpts. The generator
and documentation contain the lineage needed to reproduce them from the snapshot.

## Features and duplicate isolation

`mcp-observation-v1` remains unchanged: tool/description, arguments, current returned
data at response time, actual requested permissions, trusted task/scope, phase and
bounded prior observed history. Native arguments now include arrays, recipient
lists, numeric metrics, task handles, nested returned objects and file paths. No
additional feature is needed. Proposed labels, provenance IDs, split fields and
future responses remain outside the feature projection.

Splitting keeps connected source/fork groups, near descriptions, template groups,
derivation families and ancestry together. Related publication-verification and
metadata-directive attacks are conservatively grouped with the related pilot
families, even across repositories. Content duplicate screening now also compares
arguments/responses independent of descriptions for matching tool/phase sequences:
equal token sets, or Jaccard>=0.80 with at least8 tokens, are grouped. Full trace
equality and description screens remain. Token screens are conservative lexical
checks, not proof of semantic independence. Fork lineage and semantic families
still need human review. Shared original descriptions are expected duplicates,
not additional independent observations.

Seed23 gives a draft allocation of33 train episodes/55 boundaries and5 validation
episodes/13 boundaries. Components, not rows, are allocated, so the nominal80/20
group ratio is not an80/20 episode ratio. Train proposals:38 ALLOWED,15 BLOCKED,
2 WARNING; validation:9 ALLOWED,3 BLOCKED,1 WARNING. Small category/source support
means this is not an adequate final generalization study. The old pilot split
manifest remains preserved; expansion has its own manifest and allocation.

## Reproduction and review locations

From the repository root, with the pinned raw corpus and historical dataset present:

```powershell
.\.venv\Scripts\python.exe -m research.expand_cli
```

Outputs (all generated files remain ignored):

- `data/generated/research-expansion-v3.json`: development interactions/proposals.
- `.local/research-phase2/expansion-v3-package/splits.json`: grouped manifest.
- `quality.json` and `quality.md` in that package: full counts, source evidence,
  duplicate candidate pairs, partitions, review status and limitations.
- `reviewer-A/` and `reviewer-B/`: separate blind form plus instructions.
- `reviews-0.json`: empty real review ledger; no attestations are filled.
- `artifact-manifest.json`: dataset, splits, report and instruction hashes.

Give each reviewer **only their individual reviewer directory**, not the expanded
dataset or quality report containing proposals. The full standalone
[review guidelines](REVIEW_GUIDELINES.md) explain definitions, prefix visibility,
ambiguous cases, import commands and disagreement handling. Opaque identifiers
avoid hints from scenario names. Blind forms reject `accept`; reviewers use
`modify` to supply their own decision/category/rationale or `reject` with a reason.
The importer maps opaque identifiers back to audit IDs without exposing labels.

Re-running the generator is deterministic and refuses to overwrite changed files.
Multi-tool scopes are sorted explicitly; regeneration is checked across independent
Python hash seeds as well as repeated runs in one process.
Do not edit a returned form in its exported package and rerun generation over it;
keep completed submissions separately. Run status/import with
`--dataset data/generated/research-expansion-v3.json`; the generic CLI's default
still targets the original pilot for backward compatibility. Preparation must use
this collection's `splits.json`, not the pilot's manifest.

## Readiness and external actions

**All68 labels are UNREVIEWED. Scientific training on this collection is NOT RUN.**
Separate synthetic PPO development training is complete; see
[current status](../PROJECT_STATUS.md) and the [report](RESEARCH_REPORT.md).
This small collection
has limited WARN support, only four multi-call examples, shared metadata, invented
fixture values, and possible wording/token shortcuts. No independently verified
attack success or real-agent behavior is measured. Automated tests establish
mechanical contracts only.

**Final test remains NOT_COLLECTED.** No exposed development example can become an
untouched test by changing its split flag. Before model selection, appoint a
separate custodian to collect and independently label new interactions, enforce
source/fork/family separation, seal the content/labels with a hash and access log,
and register exclusion commitments through a new reservation version. Do not give
developers the final examples/labels during tuning. The review guide details this
procedure; an empty reservation is not available test data.

Next human actions: assign two independent reviewers and share the separate packs;
receive and import their actual submissions; adjudicate disagreements without
erasing original votes; appoint the final-test custodian. Expand underrepresented
classes, families and multi-step tasks after review feedback. We are ready for
that data-review milestone, **not supervised training**. Phase2B training requires
those scientific prerequisites and explicit user authorization.
