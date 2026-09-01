# Structured Candidate Ledger

Read this reference for full reports, technical-highlight ranking, blind validation, or originality work. Focused architecture questions that do not rank findings may keep an informal candidate list.

`candidate-ledger.json` is the machine-readable source of truth. `candidate-ledger.md` is an optional generated view. The JSON ledger preserves coverage, representative traces, preliminary ranking, evidence, counterevidence, provenance, and runtime hypotheses before documentation/comparator review changes the analysis.

## Workflow

Initialize the ledger after repository identity is fixed:

```bash
python3 scripts/candidate_ledger.py init \
  --output <report-directory>/candidate-ledger.json \
  --run-id <run-id> \
  --target-repository <repository> \
  --target-revision <full-revision> \
  --skill-ref <skill-revision> \
  --source-mode <mode> \
  --freeze-boundary "Before project-public documentation and comparator review"
```

Record coverage areas with a status and analysis depth, record at least one representative execution trace, then add ranked mechanism-level candidates. Tier 3+ children with a parent must include a `nested_scan` note so a broad subsystem cannot hide internal mechanisms.

Every candidate records:

- stable kebab-case ID and contiguous preliminary rank
- analysis tier from 0 through 5
- problem, mechanism, and technical/product value
- evidence references and strongest counterevidence
- provenance classification
- runtime hypotheses when behavior can be tested

Freeze only after broad discovery and representative tracing:

```bash
python3 scripts/candidate_ledger.py freeze \
  --ledger <report-directory>/candidate-ledger.json \
  --note "Frozen before project documentation and external precedent review"

python3 scripts/candidate_ledger.py render \
  --ledger <report-directory>/candidate-ledger.json \
  --require-frozen \
  --output <report-directory>/candidate-ledger.md
```

Freeze writes a canonical content SHA-256. All mutation commands reject a frozen ledger, and validation detects direct post-freeze edits. Corrections, promotions, demotions, and contradictions belong in the final report—not in the frozen ledger.

Do not mistake schema completeness for analysis quality. The script cannot decide candidate importance, evidence relevance, technical value, or originality.
