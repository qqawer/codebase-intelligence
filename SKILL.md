---
name: codebase-intelligence
description: Analyze substantial software repositories through execution tracing, adaptive depth, and counterevidence. Use for evidence-backed architecture reports, technical-mechanism ranking, design-quality or learning-value assessment, and cautious originality evaluation. Do not use for narrow one-file questions or ordinary implementation and code-review tasks.
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

## Choose the analysis mode

Use **Standard** for public, ordinary repository-analysis requests. “Analyze this repository,” “research this
project,” “rank its strongest mechanisms,” and similar requests are Standard unless the user explicitly asks for the
Full protocol or its audit artifacts.

- **Focused:** answer one mechanism or execution-path question; use bounded discovery, one or two traces, and only
  targeted checks. It may remain conversational.
- **Standard (default):** produce an evidence-backed Markdown report with an architecture map, representative execution
  paths, three to five ranked mechanisms, counterevidence, weaknesses, targeted runtime validation, and evidence limits.
- **Full (advanced opt-in):** add frozen candidate/comparator ledgers, command sidecars, receipts, and indexed research
  publication. Never infer Full from a generic request, “comprehensive,” ranking, or originality interest alone. Enter
  it only when the user explicitly asks for Full/auditable/reproducible protocol or names its audit artifacts.

A Standard originality question may use bounded authoritative comparators without creating ledgers. If stronger
historical or exhaustive support would require Full, state the current evidence ceiling and offer Full rather than
silently escalating.

Do not run a large repository's complete test suite merely because it exists. Inspect CI and manifests first, run the
smallest checks capable of changing the conclusion, and add one representative end-to-end path when practical. Use a
full suite only when exhaustive validation is requested or its incremental evidence justifies the cost. Tell the user
before entering a materially long-running full mode.

For substantial analysis:

1. Discover entrypoints, modules, runtime boundaries, dependencies, tests, benchmarks, CI, and generated/vendor boundaries before deep reading.
2. Use documentation-led and independent structural discovery; do not let README quality determine the candidates.
3. Trace representative calls, ownership, data movement, failure paths, fallback, cleanup, and observable results end to end.
4. Deepen selectively from inventory through behavior, design, technical value, and—only when requested—originality.
5. Scan inside every important parent subsystem for independent mechanisms before ranking it as one highlight.
6. Seek the strongest counterevidence for each major assessment and let it lower significance, distinctiveness, outcome, or confidence.
7. Run a final recall challenge for hidden mechanisms, benchmarks, user-visible behavior, and high-learning-value upstream techniques.
8. Stop when additional work cannot change the conclusion under the evidence ceiling.

For explicitly selected Full mode, read [references/full-mode.md](references/full-mode.md) before using its protocol.

## Evidence and outcome discipline

Keep architectural enablement, tested behavior, and measured outcomes distinct:

- “designed to improve X” for mechanism-level effects
- “project tests cover X” for executed or inspected tests
- “measured to improve X” only with a recorded workload, environment, baseline, and result

Treat repeated source citations as one evidence channel. Separate originality from learning value: lower originality when precedent exists without automatically lowering implementation depth, project importance, or educational value.

## Automation boundary

Use `repository_snapshot.py` for bounded local discovery and `source_link.py` for immutable citations when helpful.
Standard mode does not create ledgers, receipts, run indexes, or invoke `research_session.py`.

Advanced scripts fix Full-mode identity, phase order, evidence sidecars, source-link invariants, and publication safety.
They do not authorize commands or decide architecture, importance, technical value, originality, or whether evidence is
semantically sufficient.

## Load supporting guidance only when needed

- Source mode, evidence combinations, confidence, or evidence ceilings: [references/evidence-confidence.md](references/evidence-confidence.md)
- Tier 3+ design quality, leverage, abstractions, and technical-value ranking: [references/design-and-value.md](references/design-and-value.md)
- Originality, innovation, or comparator claims: [references/innovation.md](references/innovation.md)
- Standard report structure or review: [references/standard-report.md](references/standard-report.md)
- Explicitly selected Full protocol: [references/full-mode.md](references/full-mode.md)
- A relevant known failure pattern or final full-report adversarial check: [references/failure-modes.md](references/failure-modes.md)

Do not load every reference by default.

## Standard delivery

For a substantial Standard analysis, write `PROJECT_INTELLIGENCE_REPORT.md` to the user's chosen or existing research
workspace, never silently into the analyzed repository or Skill directory. If no persistent destination is established,
ask before writing outside the current workspace; still provide the concise findings in chat.

Use repository-relative source locations or immutable remote links. Do not publish machine-specific paths,
credentials, private source, or raw conversations. Keep the report insight-dense: identity and evidence limits,
architecture, representative execution, three to five ranked mechanisms, counterevidence and weaknesses, targeted
runtime results, learning targets, and a calibrated verdict. It does not need Full-mode ledgers or receipts.

The final chat response links the report and summarizes its verdict, strongest findings, validation status, and
evidence limits. Focused questions may remain conversational.
