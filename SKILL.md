---
name: codebase-intelligence
description: Analyze substantial software repositories through execution tracing, adaptive depth, counterevidence, and comparator research. Use for evidence-backed architecture reports, technical-mechanism ranking, design-quality or learning-value assessment, and cautious originality or innovation evaluation. Do not use for narrow one-file questions or ordinary implementation and code-review tasks.
---

# Codebase Intelligence

Analyze repositories for technical understanding and value, not merely summary.

## Core epistemic rule

Keep these claims separate:

1. observed implementation
2. behavioral interpretation
3. design assessment
4. technical value
5. originality
6. innovation

Never promote one level automatically into the next. Complexity, custom code, performance reputation, a systems language, or product leverage does not by itself establish technical value or innovation.

## Select the evidence mode

Declare one source mode: `local-pinned`, `remote-pinned`, `indexed-snapshot`, or `docs-only`. Record repository identity, exact revision, analysis date, worktree state, and material source gaps. Respect the evidence ceiling; an on-disk checkout with unknown revision or modifications is not pinned.

For a local checkout, first run the bounded read-only inventory:

```bash
python3 <skill-directory>/scripts/repository_snapshot.py <repository-path> --format json
```

Treat classifications as discovery hints, not architectural conclusions.

## Research workflow

For substantial analysis:

1. Discover entrypoints, modules, runtime boundaries, dependencies, tests, benchmarks, CI, and generated/vendor boundaries before deep reading.
2. Use documentation-led and independent structural discovery; do not let README quality determine the candidates.
3. Trace representative calls, ownership, data movement, failure paths, fallback, cleanup, and observable results end to end.
4. Deepen selectively from inventory through behavior, design, technical value, and—only when requested—originality.
5. Scan inside every important parent subsystem for independent mechanisms before ranking it as one highlight.
6. Seek the strongest counterevidence for each major assessment and let it lower significance, distinctiveness, outcome, or confidence.
7. Run a final recall challenge for hidden mechanisms, benchmarks, user-visible behavior, and high-learning-value upstream techniques.
8. Stop when additional work cannot change the conclusion under the evidence ceiling.

For full reports, ranked findings, blind validation, or originality analysis, use the structured candidate ledger and freeze it before project-public explanations or external comparator review can rewrite preliminary discovery. Read [references/candidate-ledger.md](references/candidate-ledger.md).

## Evidence and outcome discipline

Keep architectural enablement, tested behavior, and measured outcomes distinct:

- “designed to improve X” for mechanism-level effects
- “project tests cover X” for executed or inspected tests
- “measured to improve X” only with a recorded workload, environment, baseline, and result

Treat repeated source citations as one evidence channel. Separate originality from learning value: lower originality when precedent exists without automatically lowering implementation depth, project importance, or educational value.

## Automation boundary

Scripts fix identity, phase order, candidate freeze, command evidence, source-link invariants, and publication safety. They do not authorize commands or decide architecture, importance, comparators, technical value, originality, or when evidence is semantically sufficient.

For a new full report from a clean local checkout, prefer `research_session.py init`, use its `status` command while
working, and use `publish` only after synthesis. The orchestrator preserves the same forward-only phases enforced by
`research_run.py`:

```text
initialized -> inventoried -> candidates-frozen -> runtime-validated
-> comparators-reviewed -> synthesized -> report-validated -> finalized
```

Read [references/run-record.md](references/run-record.md) before executing validation. Record executed, unavailable, externally observed, and intentionally skipped checks instead of reducing partial validation to a boolean. Historical migrations may use the explicit retrospective path; new runs must not use it to bypass gates.

## Load supporting guidance only when needed

- Source mode, evidence combinations, confidence, or evidence ceilings: [references/evidence-confidence.md](references/evidence-confidence.md)
- Tier 3+ design quality, leverage, abstractions, and technical-value ranking: [references/design-and-value.md](references/design-and-value.md)
- Originality, innovation, or comparator claims: [references/innovation.md](references/innovation.md)
- Full report structure or review: [references/report-format.md](references/report-format.md)
- Full-report execution records and phase gates: [references/run-record.md](references/run-record.md)
- Ranked/frozen candidate workflow: [references/candidate-ledger.md](references/candidate-ledger.md)
- A relevant known failure pattern or final full-report adversarial check: [references/failure-modes.md](references/failure-modes.md)

Do not load every reference by default.

## Delivery

A full Project Intelligence Report requires a persistent Markdown artifact in the user's chosen or existing research workspace, never silently in the analyzed repository or Skill directory. Prefer:

```text
<report-workspace>/reports/<owner>-<repository>/<short-revision>/
├── PROJECT_INTELLIGENCE_REPORT.md
├── candidate-ledger.json
├── candidate-ledger.md
├── run-record.json
└── validation-receipt.json
```

Use repository-relative source locations or immutable remote links; do not publish machine-specific paths, credentials, private source, or raw conversations. The report should explain the system, architecture, representative execution, strongest mechanisms, value, provenance, conventional versus distinctive work, weaknesses, learning targets, evidence, coverage, and uncertainty in proportion to available evidence.

Before completion:

1. write the report artifact
2. generate target source citations with `scripts/source_link.py` when a local Git checkout is available
3. validate it with `scripts/validate_report.py --write-receipt ...`
4. advance the run through `report-validated`
5. finalize the run record
6. refresh a compatible research workspace index with `scripts/build_research_index.py --write`
7. disclose or resolve material warnings

The final chat response links the report and summarizes its verdict, strongest findings, validation status, and evidence limits. Focused questions may remain conversational.
