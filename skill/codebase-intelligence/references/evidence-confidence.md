# Evidence and Confidence

Use this reference to calibrate claims and prevent unsupported conclusions.

## Evidence depth

### E0 — Structural signal

Examples:

- file or directory names
- LOC
- dependency counts
- naming conventions
- package layout

Use E0 for discovery only.

Do not use structural signals alone to support strong behavioral or design claims.

### E1 — Direct implementation evidence

Examples:

- function bodies
- type definitions
- branches
- imports
- explicit configuration
- concrete call sites

Use E1 for factual implementation claims.

### E2 — Behavioral trace

Connect multiple implementation points into an observed execution path.

Use E2 for claims about:

- runtime behavior
- data flow
- control flow
- lifecycle
- failure propagation

### E3 — Corroborated repository evidence

Require multiple independent repository signals, such as:

- implementation + tests
- implementation + benchmarks
- implementation + documentation
- implementation + history
- implementation + configuration

Use E3 for stronger architectural and design conclusions.

### E4 — Comparative evidence

Compare the mechanism against:

- conventional implementations
- upstream dependencies
- peer projects
- published techniques
- acknowledged inspirations

Require E4 before strong originality claims.

### E5 — Outcome evidence

Use empirical or architectural evidence demonstrating an actual advantage.

Examples:

- benchmark improvement
- reduced memory use
- lower latency
- improved reliability
- smaller caller burden
- smaller change surface
- simpler extension
- stronger correctness property

Strong innovation claims should normally require E4 and preferably E5.

## Evidence diversity

Do not confuse multiple citations from the same evidence channel with independent confirmation.

Useful independent channels include:

- source implementation
- tests
- benchmarks
- documentation or ADRs
- Git history
- issue or PR history
- runtime configuration
- external comparative sources

Prefer at least two independent channels for major findings when available.

## Source authority

Evaluate whether the source is appropriate for the claim.

Prefer:

1. direct implementation
2. project-authored tests and benchmarks
3. project-authored architecture or internals documentation
4. project history and design discussions
5. upstream documentation
6. peer-reviewed or primary external sources
7. secondary commentary

Do not let a polished secondary explanation override contradictory implementation evidence.

## Source freshness

Check whether evidence corresponds to the repository revision being analyzed.

When exact revision matching is unavailable:

- state the limitation
- reduce confidence where appropriate
- avoid pretending that current documentation proves historical behavior

## Confidence

Report confidence separately from technical significance.

Use:

- **High** — multiple strong signals agree and important counterevidence has been checked
- **Medium** — evidence is meaningful but incomplete or partially inferential
- **Low** — plausible interpretation with important missing evidence

Confidence is not the same as evidence depth.

## Source modes and evidence ceilings

### local-pinned

A local repository is available at a known revision.

This is the strongest mode for source-level coverage.

Record:

- repository identity
- exact commit or immutable revision
- branch or tag when useful
- whether tracked files are modified
- missing submodules, LFS objects, generated sources, or other material gaps

`Local` describes access; `pinned` describes reproducibility. A checkout with an unknown revision or unrecorded local
changes is not fully pinned.

### remote-pinned

A specific remote revision can be inspected reliably.

Good for reproducible analysis but potentially less efficient than local access.

### indexed-snapshot

Search/indexed source is available but complete revision coverage is not guaranteed.

Do not claim exhaustive source coverage.

When history is unavailable, use explicit fallback signals:

- benchmark directories
- project-authored internals/design documents
- changelog or release engineering notes
- test clusters
- source comments naming papers or algorithms

### docs-only

Only documentation is available.

Use documentation for architecture hypotheses and stated intent.

Do not present source-level implementation conclusions as verified.

## Semantic verification

A valid file and line reference does not prove that a claim is correct.

Separate:

1. reference validity
2. evidence relevance
3. semantic entailment
4. confidence

For every important claim ask:

> Does this evidence actually support the wording of the claim?

## Counterevidence

Before finalizing a major finding, actively search for evidence that could weaken it.

Examples:

- the custom mechanism delegates to a standard upstream implementation
- a supposedly deep abstraction leaks significant caller knowledge
- benchmark evidence contradicts a performance assumption
- project documentation credits an external technique
- an unusual subsystem is peripheral rather than central

Counterevidence must be allowed to change the final classification.

## Outcome-language gate

Distinguish carefully:

### Designed to improve X

The structure or intent suggests a goal.

### Structurally enables X

Architecture provides a mechanism that can support the outcome.

### Measured to improve X

Empirical evidence demonstrates the outcome.

Do not move from the first two categories to the third without measurement evidence.
