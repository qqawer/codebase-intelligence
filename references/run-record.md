# Research Run Record

Read this reference when creating a full report, executing runtime validation, or validating a completed report.

`run-record.json` is the machine-readable evidence sidecar for one report. Markdown remains the human-readable analysis; the sidecar records identities, commands, unavailable checks, artifacts, and the protocol verdict without requiring a rigid report heading template.

## Orchestrate a new local session

For a clean local Git checkout, initialize the standard directory, repository snapshot, run record, and candidate
ledger together:

```bash
python3 scripts/research_session.py init \
  --checkout <target-checkout> \
  --research-root <research-workspace>
```

The command resolves and records the remote, full commit, shallow/full state, clean worktree, and current Skill
identity. It creates `reports/<owner>-<repository>/<short-revision>/` with candidate and comparator ledgers in a
temporary staging directory and publishes it only after initialization and inventory succeed. It finishes in
`inventoried`; it does not run target commands, choose candidates, comparators, or report conclusions.

At any point, inspect the next legal phase and its current gate failures:

```bash
python3 scripts/research_session.py status <report-directory>
```

After the candidate ledger is frozen, runtime evidence and comparator review are recorded, the report exists, and the
run has advanced to `synthesized`, publish it with an explicit protocol verdict:

```bash
python3 scripts/research_session.py publish <report-directory> \
  --research-root <research-workspace> \
  --target-checkout <target-checkout> \
  --verdict "PASS WITH EVIDENCE LIMITATIONS"
```

`publish` first redacts machine-local checkout, home, temporary, and common toolchain roots from publication artifacts.
When command output changes, it preserves the original digest as `raw_output_sha256`, stores the redacted digest as
`output_sha256`, and marks `output_redacted`. It then performs strict report validation, writes the report-bound
receipt, advances and finalizes the record, regenerates the workspace index, validates index consistency, and runs a
workspace validator when one is present. It does not commit or push Git changes. A residual known local-root pattern
or validation warning stops publication. Use the lower-level commands below for remote-only evidence, historical
migration, or workflows that do not fit the standard local layout.

## Create the record

Resolve scripts relative to the Skill directory.

```bash
python3 scripts/research_run.py init \
  --output <report-directory>/run-record.json \
  --run-id <stable-id> \
  --run-class <protocol-class> \
  --target-repository <sanitized-url> \
  --target-revision <full-revision> \
  --skill-ref <skill-revision-or-content-hash> \
  --source-mode <mode> \
  --worktree-state <clean-or-described-dirty-state>
```

Do not place secrets, private source, raw conversations, or machine-specific checkout paths in arguments intended for publication.

## Generate immutable source links

For a local Git checkout, generate citations instead of manually assembling repository, revision, path, and line
fragments:

```bash
python3 scripts/source_link.py \
  --checkout <target-checkout> \
  --path src/example.py \
  --lines 10:24 \
  --label "representative implementation"
```

The default `HEAD` mode refuses a dirty target file. Pass an explicit full or symbolic `--revision` to cite committed
historical content independently of the current worktree. The generator supports GitHub HTTPS and SSH remotes and
validates line bounds against the selected commit.

## Record commands

Run only commands already authorized by the user's task. The recorder does not authorize commands and must not discover or execute project instructions automatically.

```bash
python3 scripts/research_run.py exec \
  --record <report-directory>/run-record.json \
  --category test \
  --cwd <target-checkout> \
  --cwd-label . \
  --timeout 600 \
  -- npm test
```

The recorder captures exit status, duration, redacted argv, stdout/stderr logs, and a combined output hash. It deliberately does not capture environment variables or the absolute execution directory. `recorder_environment` describes the machine creating the sidecar; command-specific tool versions should be recorded by explicit commands. Common secret-bearing options, URL userinfo, query strings, and fragments are removed from the published argv, but callers must still avoid passing secrets on command lines. For standard local publication, let `research_session.py publish` run the deterministic artifact sanitizer; for custom workflows, run `publication_safety.py <report-directory> --target-checkout <target-checkout>` before receipt generation.

Record unavailable or externally observed evidence explicitly:

```bash
python3 scripts/research_run.py note \
  --record <report-directory>/run-record.json \
  --category rust-tests \
  --status unavailable \
  --reason "cargo is not installed"
```

Use `--evidence-origin retrospective-migration` when preserving a result from an earlier run whose exact command timestamps or logs were not captured. Do not reconstruct details that were not observed.

## Advance, validate, and finalize

Advance exactly one phase at a time. The examples below assume the immediately preceding phases have already passed;
supply the artifact required by each next gate:

```bash
python3 scripts/research_run.py advance \
  --record <report-directory>/run-record.json \
  --to candidates-frozen \
  --artifact candidate_ledger=<report-directory>/candidate-ledger.json

python3 scripts/research_run.py advance \
  --record <report-directory>/run-record.json \
  --to synthesized \
  --artifact report=<report-directory>/PROJECT_INTELLIGENCE_REPORT.md

python3 scripts/validate_report.py \
  <report-directory>/PROJECT_INTELLIGENCE_REPORT.md \
  --run-record <report-directory>/run-record.json \
  --candidate-ledger <report-directory>/candidate-ledger.json \
  --target-checkout <target-checkout> \
  --write-receipt <report-directory>/validation-receipt.json

python3 scripts/research_run.py advance \
  --record <report-directory>/run-record.json \
  --to report-validated \
  --artifact validation_receipt=<report-directory>/validation-receipt.json

python3 scripts/research_run.py finalize \
  --record <report-directory>/run-record.json \
  --report PROJECT_INTELLIGENCE_REPORT.md \
  --candidate-ledger candidate-ledger.json \
  --verdict "PASS WITH EVIDENCE LIMITATIONS"
```

Validation errors are violated reproducibility or publication invariants. Warnings identify missing evidence or review prompts. Use `--strict` in CI when warnings should fail the check.

## Research phases

Schema version 2 records a forward-only state machine:

```text
initialized -> inventoried -> candidates-frozen -> runtime-validated
-> comparators-reviewed -> synthesized -> report-validated -> finalized
```

Advance one phase at a time with `research_run.py advance`. Each transition checks its required artifact or evidence.
For historical reports only, `--retrospective --reason <why>` permits a missing historical artifact while preserving
the bypass in `phase_history`; never use it to bypass a gate in a new run.

`validate_report.py --write-receipt validation-receipt.json` creates a receipt bound to the current report SHA-256.
The `report-validated` gate rejects receipts with errors or a stale report hash.

## Schema version 2

Required top-level fields:

- `schema_version`
- `run_id`
- `run_class`
- `analysis_date`
- `source_mode`
- `target.repository`, `target.revision`, `target.worktree_state`
- `skill.revision`
- `entries`
- `phase`, `phase_history`

After finalization the record also contains `artifacts`, `verdict`, `completed_at`, and a granular `runtime_summary`. `runs.json` in a research workspace remains a compact cross-run index and should link to this sidecar rather than duplicating command evidence.

If the research workspace uses the standard `runs.json` and README generated markers, refresh both after finalization:

```bash
python3 scripts/build_research_index.py <research-workspace> --write
python3 scripts/build_research_index.py <research-workspace>
```

The first command merges finalized records while preserving legacy runs and non-canonical annotation fields. The
second command fails when either generated output has drifted.
