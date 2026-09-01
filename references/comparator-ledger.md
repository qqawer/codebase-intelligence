# Structured Comparator Ledger

Read this reference after candidate freeze when a full report, originality assessment, or major distinctiveness claim
requires upstream, peer, paper, standard, library, or common-pattern comparison.

`comparator-ledger.json` is the machine-readable source of truth. It does not decide originality. It makes the compared
sources, identity limits, differences, counterevidence, and candidate coverage auditable.

## Coverage rule

Every Tier 3+ candidate in the frozen candidate ledger must be either:

- referenced by at least one comparator entry; or
- explicitly excluded with a reason explaining why comparator research is not applicable.

A candidate cannot be both compared and excluded. Lower-tier candidates may also be reviewed when the report makes an
originality or distinctiveness claim about them.

## Initialize and record comparisons

`research_session.py init` creates an empty ledger automatically. For a manual workflow:

```bash
python3 scripts/comparator_ledger.py init \
  --output <report-directory>/comparator-ledger.json \
  --run-record <report-directory>/run-record.json \
  --scope "Tier 3+ candidates and originality claims"
```

Add one entry for a close precedent or baseline:

```bash
python3 scripts/comparator_ledger.py add \
  --ledger <report-directory>/comparator-ledger.json \
  --id <stable-kebab-id> \
  --name <comparator-name> \
  --candidate-id <candidate-id> \
  --source-type <upstream-repository|peer-repository|library|paper|standard|documentation|common-pattern> \
  --source-title <title> \
  --source-url <https-url> \
  --source-revision <full-commit-if-known> \
  --accessed-at <YYYY-MM-DD> \
  --problem <shared-constraint> \
  --baseline <conventional-baseline> \
  --shared-mechanism <what-is-similar> \
  --acknowledged-inspiration <credit-or-none-found> \
  --repository-difference <material-difference> \
  --outcome-difference <demonstrated-or-structurally-enabled-outcome> \
  --counterevidence <what-weakens-originality> \
  --classification <calibrated-classification> \
  --originality-effect <lowers|supports-distinctiveness|supports-innovation|neutral|inconclusive> \
  --confidence <high|medium|low> \
  --evidence <comparison-evidence>
```

When no immutable revision or version can be resolved, omit those fields and provide `--identity-limit` rather than
inventing precision. Source URLs must use HTTPS and cannot contain credentials.

Explicitly exclude an uncovered major candidate only with a substantive reason:

```bash
python3 scripts/comparator_ledger.py exclude \
  --ledger <report-directory>/comparator-ledger.json \
  --candidate-id <candidate-id> \
  --reason <why-comparison-is-not-applicable>
```

## Freeze and advance

Freeze only after the intended comparator scope has been reviewed:

```bash
python3 scripts/comparator_ledger.py freeze \
  --ledger <report-directory>/comparator-ledger.json \
  --candidate-ledger <report-directory>/candidate-ledger.json \
  --note "Comparator review complete"

python3 scripts/comparator_ledger.py render \
  --ledger <report-directory>/comparator-ledger.json \
  --candidate-ledger <report-directory>/candidate-ledger.json \
  --require-frozen \
  --output <report-directory>/comparator-ledger.md

python3 scripts/research_run.py advance \
  --record <report-directory>/run-record.json \
  --to comparators-reviewed \
  --artifact comparator_ledger=<report-directory>/comparator-ledger.json
```

New full reports require the frozen structured ledger at this gate. Focused non-full runs may still use a recorded
`comparator-review` note. Historical migrations may use the explicit retrospective bypass, which must disclose the
missing historical artifact.

## Entry fields

Each comparator records:

- candidate IDs affected by the comparison
- source type, title, HTTPS URL, access date, and revision/version/identity limit
- problem and conventional baseline
- shared mechanism and acknowledged inspiration
- repository-specific and outcome differences
- strongest counterevidence
- calibrated classification, originality effect, confidence, and evidence

Freezing writes a canonical SHA-256 and blocks normal mutation commands. Schema validity and complete rows do not prove
that the comparator set is representative or the originality conclusion is correct.
