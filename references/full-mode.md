# Full Mode: Advanced Auditable Research

Read this reference only when the user explicitly selects Full mode, asks for an auditable/reproducible research
protocol, or requests its artifacts such as candidate/comparator ledgers, a run record, validation receipt, or indexed
research publication.

Full mode is a public advanced capability and a maintainer regression path. It is not the default user experience.
Do not enter it merely because a request says “analyze,” “research,” “comprehensive,” “rank,” or asks a bounded
originality question.

Full adds evidence protocol, not automatic exhaustiveness. It still runs the smallest runtime checks that can change
the conclusion; a complete project test suite is optional and requires a justified evidence benefit.

When Full is selected:

1. Read [candidate-ledger.md](candidate-ledger.md), freeze candidates before project-public explanations or comparator
   research, and preserve the frozen JSON plus optional rendering.
2. Read [comparator-ledger.md](comparator-ledger.md) and cover every Tier 3+ candidate or record an explicit exclusion.
3. Read [run-record.md](run-record.md), use `research_session.py` for a clean local checkout, and preserve command
   evidence and unavailable/skipped checks.
4. Use [report-format.md](report-format.md), write the persistent report, run strict validation, generate the receipt,
   finalize the record, and refresh the compatible research index.
5. Run publication safety before receipt generation. `research_session.py publish` handles path redaction, published
   output rehashing, residual checks, validation, finalization, and indexing; it never commits or pushes.

The standard Full artifact set is:

```text
<report-workspace>/reports/<owner>-<repository>/<short-revision>/
├── PROJECT_INTELLIGENCE_REPORT.md
├── candidate-ledger.json
├── candidate-ledger.md
├── comparator-ledger.json
├── comparator-ledger.md
├── run-record.json
└── validation-receipt.json
```

Disclose that Full was selected, why it was justified, and any expected material latency before beginning expensive
runtime or comparator work.
