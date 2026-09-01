# Report Format

Use this reference when producing the final Codebase Intelligence report.

Optimize for insight density rather than document length.

Do not force every section when evidence is insufficient.

## Artifact contract

A full Project Intelligence Report is a persistent Markdown artifact, not only a chat response. Follow the destination
and naming rules in `SKILL.md`, write the complete artifact before reporting completion, and return a clickable file
link plus a concise verdict in chat.

The artifact must be self-contained enough to interpret later. Record repository identity, exact revision, analysis
date, source mode, worktree state, material source gaps, runtime validation, and the evidence ceiling. Use
repository-relative source references with line numbers or immutable remote links. Do not publish machine-specific
absolute paths, credentials, private source, or raw conversation transcripts.

Intermediate snapshots, candidate ledgers, run records, and validation receipts are supporting artifacts. Name and
label them separately; none substitutes for the final report. For new full reports, preserve the hash-frozen
`candidate-ledger.json`, its optional Markdown rendering, `run-record.json`, and `validation-receipt.json` beside the
report.

# Project Intelligence Report

## 1. Executive Technical Summary

Explain concisely:

- what the project does
- its architectural character
- its core execution model
- the most important technical strengths
- the most important caveats

State the source mode and major evidence limitations.

When available, include the repository identity, exact revision, analysis date, worktree state, and material source
gaps. This information is required when the report will be compared with another run.

## 2. Repository and Architecture Map

Describe:

- major subsystems
- entry points
- runtime boundaries
- dependency direction
- important data/control flows

Distinguish:

- observed relationships
- strongly supported relationships
- hypotheses

Do not infer architecture solely from directory names.

## 3. Core Execution Paths

Trace representative behavior end to end.

For each important path explain:

1. entry point
2. major transformations
3. important state
4. subsystem boundaries
5. failure/blocking/fallback behavior
6. observable result

Prefer execution traces over generic architecture descriptions.

## 4. Important Modules and Mechanisms

Explain the modules that matter most.

For each:

- responsibility
- callers
- hidden knowledge
- invariants
- contract burden
- mechanism leverage
- system leverage
- user/product leverage
- why it matters

Do not confuse large modules with deep modules.

## 5. Top Technical Highlights

Rank only findings with sufficient evidence.

For every highlight include:

### Name

Use a mechanism-level name when possible.

Prefer:

> Incremental dependency propagation

over:

> Graph subsystem

### Problem

What difficult constraint does it solve?

### Mechanism

How does it actually work?

### Why it matters

Explain:

- technical significance
- project importance
- leverage
- practical impact
- learning value

### Design quality

Discuss relevant dimensions:

- depth
- locality
- information hiding
- contract burden
- lifecycle
- failure handling
- trade-offs

### Technical difficulty

Classify:

- Exceptional
- High
- Moderate
- Routine
- Unknown

Explain the classification.

### Conventional baseline

What would a simpler or common implementation do?

### Distinctiveness

Classify:

- Conventional engineering
- Strong engineering
- Distinctive design
- Unusual adaptation
- Plausible innovation
- Unverified innovation candidate

### Attribution

State whether the mechanism is:

- repository-original
- adapted
- upstream
- published research
- inspired by another project
- conventional
- unknown

### Counterevidence

State the strongest evidence against an over-strong interpretation.

### Evidence

List the strongest evidence channels.

### Confidence

Use:

- High
- Medium
- Low

Keep confidence separate from significance.

## 6. Architecture Strengths

Discuss architecture-level qualities such as:

- dependency direction
- subsystem boundaries
- information hiding
- extensibility
- testability
- runtime isolation
- locality
- lifecycle design

Avoid generic praise.

## 7. Engineering Strengths

Discuss implementation qualities such as:

- correctness discipline
- performance engineering
- failure handling
- concurrency
- resource management
- observability
- testing
- compatibility
- developer experience

Distinguish strong engineering from originality.

## 8. Algorithms and Performance-Critical Mechanisms

Include algorithms or systems mechanisms that materially affect behavior.

For each:

- identify provenance when known
- explain repository-specific adaptation
- avoid claiming measured performance without benchmark evidence

A published algorithm can still be an exceptional learning highlight.

## 9. Deep Abstractions

Identify modules with high leverage.

Explain:

- what callers learn
- what callers do not need to learn
- what knowledge is hidden
- what would spread if the abstraction were inlined
- whether responsibilities remain cohesive

## 10. Conventional vs Distinctive

Create a clear separation.

### Conventional but well executed

List important mechanisms that are established techniques.

### Distinctive adaptations

List mechanisms that meaningfully adapt known ideas.

### Plausible innovation

Include only candidates that satisfy the innovation evidence threshold.

### Unverified innovation candidates

List interesting mechanisms whose originality cannot yet be established.

This section prevents the report from turning every strength into an innovation claim.

## 11. Trade-offs and Weaknesses

Discuss meaningful limitations.

Examples:

- complexity introduced by an abstraction
- portability constraints
- memory trade-offs
- operational complexity
- migration cost
- coupling
- compatibility burden
- performance trade-offs

Do not manufacture weaknesses merely to appear balanced.

## 12. What Is Worth Learning

Answer:

> What should an experienced engineer study in this repository?

Include mechanisms with high learning value even when originality is low.

For each learning target explain why it is worth studying.

## 13. Evidence Ledger

For major claims record:

| Claim | Evidence | Depth | Diversity | Confidence | Counterevidence |
|---|---|---|---|---|---|

Do not treat repeated citations from one channel as independent evidence.

## 14. Uncertainty Ledger

List conclusions that remain uncertain because of:

- source-mode limitations
- missing history
- missing benchmarks
- incomplete external comparison
- ambiguous intent
- unavailable runtime evidence

State what evidence would resolve the uncertainty.

## 15. Coverage Ledger

For substantial repositories, record:

| Area | Discovered | Importance | Analysis depth | Status |
|---|---|---|---|---|

Use this to demonstrate broad discovery without pretending every area received equal depth.

## Highlight Recall Challenge

Before finalizing the report, check:

1. Did any Tier 3+ parent subsystem hide independent mechanisms?
2. Are important benchmark targets missing from the highlights?
3. Are mechanisms emphasized in design/internals material missing?
4. Does a user-visible capability imply hidden technical depth?
5. Did external provenance cause an important learning target to be unfairly downgraded?
6. Is the final list biased toward the best-documented subsystem?

If a credible omission appears, perform bounded follow-up analysis before finalizing.

## Writing rules

### Prefer precise claims

Good:

> The execution engine uses fixed-size column batches and supports multiple physical vector representations.

Bad:

> The engine is extremely innovative and highly optimized.

### Separate fact and inference

Good:

> The implementation performs X. This suggests Y because...

Bad:

> The authors clearly intended Y.

unless intent evidence exists.

### Avoid promotional language

Do not use:

- revolutionary
- groundbreaking
- ingenious
- cutting-edge

unless directly quoting and necessary.

### Prefer mechanism-level explanations

Do not stop at:

> The project has a sophisticated optimizer.

Explain which optimizer mechanisms are technically important.

### Preserve uncertainty

A rigorous:

> Available evidence is insufficient to establish originality.

is better than an unsupported innovation claim.

## Final quality gate

Before returning the report verify:

- the complete Markdown artifact exists at the declared destination
- the final response links the artifact and does not mislabel an intermediate snapshot as the report
- architecture claims are behavior-backed
- important execution paths were traced
- parent subsystems received nested candidate discovery
- technical value and originality remain separate
- comparator ledgers exist for strong originality claims
- counterevidence affected conclusions where appropriate
- outcome language matches evidence
- published/upstream techniques retain learning value when warranted
- the Highlight Recall Challenge was completed
- source-mode limitations are visible
- stopping rules have been satisfied
