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

Never promote one level automatically into the next.

## 1. Declare source mode

Classify available evidence:

- `local-pinned`
- `remote-pinned`
- `indexed-snapshot`
- `docs-only`

Do not claim exhaustive source coverage when the available mode cannot support it.

Record the repository identity, exact revision, analysis date, and worktree state when available. Also record material
source gaps such as unavailable submodules, Git LFS objects, generated sources, or excluded extensions.

A local checkout is not `local-pinned` merely because it is on disk. If the revision or local modifications are unknown,
state that limitation and do not present cross-run differences as methodology regressions.

For a local checkout, resolve `scripts/repository_snapshot.py` relative to this `SKILL.md` and run it once before manual
discovery:

```bash
python3 <skill-directory>/scripts/repository_snapshot.py <repository-path> --format markdown
```

Use `--format json` when machine-readable evidence is more useful. The script is read-only, has bounded output, and
collects repository identity, worktree state, language and extension counts, manifests, candidate entry points, tests,
benchmarks, documentation, CI, submodules, LFS patterns, and likely generated/vendor boundaries. Treat every path
classification as a discovery hint. Verify ambiguous cases in source, and continue manually if Python or Git metadata is
unavailable.

## 2. Discover broadly before analyzing deeply

Build a repository coverage map.

Identify:

- entry points
- modules
- runtime boundaries
- important dependencies
- data/control flow
- tests
- benchmarks
- build and deployment structure
- generated/vendor boundaries

Prefer complete discovery with selective depth.

Use staged, bounded discovery: inventory the tree and test/benchmark clusters first, then refine searches and read
representative implementations. Exclude generated and vendor trees unless they are directly relevant. Do not flood the
analysis context with unfiltered repository-wide matches and mistake search volume for coverage.

## 3. Run dual candidate discovery

Use two partially independent discovery channels.

### Documentation-led

Use architecture documentation, internals documentation, ADRs, README material,
design notes and comments.

### Independent structural discovery

Use:

- repository structure
- execution centrality
- dependency boundaries
- benchmarks
- test clusters
- named algorithms
- custom data structures
- change/history signals when available

Do not let documentation quality determine the candidate set.

## 4. Trace representative behavior

Follow important scenarios end to end.

Prefer observed calls, data movement and runtime behavior over architecture
assumed from folder names.

## 5. Assign adaptive analysis depth

Use progressively deeper investigation:

- Tier 0: inventory
- Tier 1: structural
- Tier 2: behavioral
- Tier 3: design
- Tier 4: technical-value deep dive
- Tier 5: originality / innovation investigation

Do not analyze every subsystem equally.

## 6. Run nested candidate discovery

For every Tier 3+ parent subsystem, perform a bounded internal mechanism scan
before final ranking.

Look for:

- named algorithms
- custom data structures
- specialized execution states
- research-paper references
- benchmark-specific paths
- spill/cache/compression/index mechanisms
- concurrency protocols
- non-obvious invariants
- unusual persistence or scheduling behavior

Do not allow a parent label such as `optimizer`, `storage`, `runtime`, or
`execution engine` to hide independently valuable mechanisms.

## 7. Analyze design quality

Evaluate:

- depth
- mechanism leverage
- system leverage
- user/product leverage
- locality
- information hiding
- contract burden
- invariants
- failure behavior
- lifecycle
- trade-offs

Complexity alone is not technical value.

## 8. Evaluate technical value

Consider independently:

- problem difficulty
- project importance
- implementation sophistication
- design leverage
- practical impact
- learning value
- originality
- evidence strength

Do not average these into fake-precision numeric scores.

Use calibrated categories.

## 9. Build comparator ledgers

Before strong originality or innovation claims, record:

- baseline approach
- closest peer or precedent
- upstream dependency
- acknowledged inspiration
- meaningful difference
- demonstrated outcome difference
- counterevidence

Custom implementation does not imply innovation.

## 10. Guard outcome language

Do not claim that a mechanism is faster, more memory efficient, more reliable,
or superior without appropriate empirical or architectural evidence.

Distinguish:

- designed to improve X
- structurally enables X
- measured to improve X

## 11. Seek counterevidence

For every major technical-value or originality candidate, actively search for
evidence that weakens the conclusion.

Counterevidence must be allowed to change the final classification.

## 12. Separate originality from learning value

A published or upstream algorithm may still be one of the most technically
valuable mechanisms in a repository.

Downgrade originality when precedent exists.

Do not automatically downgrade:

- technical significance
- implementation depth
- learning value
- project importance

## 13. Run a highlight recall challenge

Before final synthesis, ask:

1. Which selected parent subsystem could contain multiple independent highlights?
2. Which mechanisms appear in benchmarks or design material but not in the highlight list?
3. Which user-visible behavior requires a non-obvious internal mechanism?
4. Which adapted or published techniques are still exceptional learning targets?
5. Which technically important mechanism was hidden by a broad subsystem label?

Perform bounded follow-up analysis when this challenge reveals a credible omission.

## 14. Stop deliberately

Stop deepening a candidate when:

- its mechanism is understood,
- evidence is sufficient for the intended classification,
- comparator research no longer changes the conclusion,
- counterevidence has been considered,
- additional work cannot change the result under the current evidence ceiling.

Do not confuse endless research with rigor.

## 15. Record execution and validate the report

For a full Project Intelligence Report, create a `run-record.json` sidecar before runtime validation. Record executed,
unavailable, and intentionally skipped checks instead of collapsing partial validation into a boolean. Before delivery,
run the report validator and resolve every error; review warnings against the evidence ceiling rather than deleting them
mechanically.

Read [references/run-record.md](references/run-record.md) for the schema and commands. These scripts record and validate
already authorized work; they do not authorize commands, infer safe project instructions, or judge technical value and
originality on the model's behalf.

## Supporting references

Load references progressively instead of reading all of them by default:

- Read `references/evidence-confidence.md` when setting the source mode, combining evidence channels, assigning
  confidence, or describing evidence ceilings and missing source material.
- Read `references/design-and-value.md` for Tier 3+ design analysis, deep-abstraction assessment, leverage, locality,
  invariants, and technical-value ranking.
- Read `references/innovation.md` only for Tier 5 originality or innovation investigation and comparator-ledger work.
- Read `references/failure-modes.md` when a known failure pattern appears and for the final adversarial check on a full
  analysis.
- Read `references/report-format.md` when producing or reviewing a full Project Intelligence Report; do not force the
  complete template onto a narrow question.
- Read `references/run-record.md` when executing validation for or delivering a full Project Intelligence Report.

## Final output

Prioritize insight density.

### Delivery contract

For a full Project Intelligence Report, a persistent Markdown artifact is required. Resolve its destination before
final synthesis, using the user's explicit path or an existing dedicated research/report workspace when available. Do
not place generated reports in this Skill directory or modify the analyzed repository unless the user explicitly asks
for that location. If no safe durable destination is available, ask for one rather than silently returning only chat
text or writing into the target repository.

Use a reproducible path such as:

```text
<report-workspace>/reports/<owner>-<repository>/<short-revision>/PROJECT_INTELLIGENCE_REPORT.md
```

Write the complete report to the Markdown artifact before claiming completion. The final chat response should link the
artifact and summarize the verdict, strongest findings, evidence limits, and validation status instead of duplicating
the entire report. Keep repository identity, exact revision, analysis date, worktree state, source mode, and material
evidence gaps inside the artifact. Avoid machine-specific absolute source paths in report content intended for
publication; use repository-relative paths with line numbers or immutable remote links.

Store `run-record.json` beside the report and preserve command logs under that report directory. A full report is not
complete until `scripts/validate_report.py` reports no errors. Warnings must be disclosed or resolved when material.

A focused repository question, preliminary candidate ledger, or interactive exploration may remain chat-only unless
the user requests a file. Clearly label snapshots and intermediate ledgers so they cannot be mistaken for the final
report.

Explain:

- what the system does
- how the architecture works
- core execution paths
- important modules
- strongest technical mechanisms
- why those mechanisms matter
- what is conventional
- what is distinctive
- what may be innovative
- what is worth learning
- weaknesses and trade-offs
- evidence and uncertainty

Never call something innovative merely because it is complicated, custom,
fast, written in a systems language, or unusual.
