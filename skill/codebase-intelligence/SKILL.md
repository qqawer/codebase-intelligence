---
name: codebase-intelligence
description: Analyze software repositories to explain architecture, execution paths, important modules, design decisions, engineering strengths, technical difficulty, technical value, distinctive mechanisms, and plausible innovation using evidence-driven repository tracing, adaptive analysis depth, counterevidence, and calibrated confidence. Use when Codex needs to deeply understand, evaluate, document, compare, or extract technical insights from a source-code repository or substantial codebase.
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

## Supporting references

Read these only when needed:

- `references/evidence-confidence.md`
- `references/design-and-value.md`
- `references/innovation.md`
- `references/failure-modes.md`
- `references/report-format.md`

## Final output

Prioritize insight density.

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
