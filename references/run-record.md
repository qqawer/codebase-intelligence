# Research Run Record

Read this reference when creating a full report, executing runtime validation, or validating a completed report.

`run-record.json` is the machine-readable evidence sidecar for one report. Markdown remains the human-readable analysis; the sidecar records identities, commands, unavailable checks, artifacts, and the protocol verdict without requiring a rigid report heading template.

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

The recorder captures exit status, duration, redacted argv, stdout/stderr logs, and a combined output hash. It deliberately does not capture environment variables or the absolute execution directory. `recorder_environment` describes the machine creating the sidecar; command-specific tool versions should be recorded by explicit commands. Common secret-bearing options, URL userinfo, query strings, and fragments are removed from the published argv, but callers must still avoid passing secrets on command lines.

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
