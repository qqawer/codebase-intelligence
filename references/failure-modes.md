# Failure Modes

Use this reference as an adversarial checklist during repository analysis.

Do not treat it as a generic code-review checklist. Use it to detect predictable failures in codebase intelligence.

## 1. Architecture from folder names

### Failure

Infer runtime architecture from names such as:

- controllers
- services
- repositories
- engine
- runtime
- storage

### Why it fails

Directory names communicate intent, not necessarily observed behavior.

### Correction

Verify:

- imports
- calls
- data movement
- runtime boundaries
- dependency direction
- representative execution paths

Label uncertain architecture edges as hypotheses.

---

## 2. Documentation bias

### Failure

The best-documented subsystem becomes the most important subsystem in the analysis.

### Why it fails

Documentation quality and technical importance are different variables.

### Correction

Run dual candidate discovery:

1. documentation-led discovery
2. independent structural/history/benchmark discovery

Compare the candidate sets before ranking.

---

## 3. Parent-subsystem masking

### Failure

Stop discovery after identifying a broad subsystem such as:

- optimizer
- storage
- execution engine
- scheduler
- compiler
- cache
- networking

Then treat the entire subsystem as one technical highlight.

### Why it fails

A mature subsystem may contain several independently valuable mechanisms.

Example:

`optimizer` may contain:

- join ordering
- decorrelation
- statistics propagation
- predicate pushdown
- expression rewriting

### Correction

For every Tier 3+ parent subsystem, run nested candidate discovery.

Scan for:

- named algorithms
- specialized data structures
- research references
- benchmark-specific paths
- custom execution states
- concurrency protocols
- spill/cache/compression/index mechanisms
- non-obvious invariants

This failure mode was exposed during DuckDB blind validation.

---

## 4. Premature candidate compression

### Failure

Reduce the repository to a small Top-N candidate list too early.

### Why it fails

Early compression increases precision while silently destroying recall.

### Correction

Maintain two structures:

- repository coverage ledger
- technical-highlight candidate ledger

Do not delete discovered areas merely because they are not currently top-ranked.

Run the Highlight Recall Challenge before final synthesis.

---

## 5. Complexity worship

### Failure

Treat difficult-to-read or large code as technically valuable.

### Why it fails

Complexity can be:

- accidental
- legacy
- generated
- compatibility-driven
- poorly abstracted
- inherent but not well managed

### Correction

Ask:

- what problem is solved?
- what leverage results?
- what knowledge is hidden?
- what practical value is created?
- what would callers otherwise need to understand?

---

## 6. Custom equals innovative

### Failure

Assume a custom implementation is novel.

### Correction

Build a Comparator Ledger.

Check:

- upstream dependencies
- standard algorithms
- peer implementations
- acknowledged inspirations
- research papers

Classify conservatively.

---

## 7. High performance equals innovation

### Failure

Infer novelty from benchmark results or project reputation.

### Why it fails

Performance may result from excellent implementation of established techniques.

### Correction

Identify the causal mechanism before evaluating originality.

Separate:

- measured performance
- engineering quality
- architecture
- originality

---

## 8. Citation theater

### Failure

Attach a valid source location to a claim and treat the claim as proven.

### Why it fails

Reference validity is not semantic entailment.

### Correction

Check separately:

1. does the source exist?
2. is it relevant?
3. does it actually support the wording?
4. is the conclusion observed or inferred?

---

## 9. Function-name inference

### Failure

Infer behavior from names such as:

- optimize
- cache
- retry
- validate
- parallelize

### Correction

Read implementation and representative callers.

Trace actual behavior.

---

## 10. Reversed data flow

### Failure

Describe producer/consumer direction incorrectly after reading isolated functions.

### Correction

Trace:

- creation
- mutation
- ownership
- transfer
- consumption
- lifecycle

Use end-to-end scenarios.

---

## 11. Missed execution branches

### Failure

Describe only the happy path.

### Correction

Inspect:

- error branches
- retries
- blocking/resume behavior
- fallback paths
- cache misses
- initialization
- cleanup
- transaction rollback
- concurrency states

Important engineering value often lives in exceptional paths.

---

## 12. Initialization blindness

### Failure

Analyze runtime functions without understanding setup state.

### Correction

Identify:

- initialization order
- registration
- configuration
- dependency construction
- global/singleton state
- generated tables
- startup caches

Runtime behavior may depend heavily on initialization.

---

## 13. Concurrency-context errors

### Failure

Describe code as thread-safe, parallel, lock-free, or concurrent based on local implementation alone.

### Correction

Inspect:

- ownership
- synchronization
- task scheduling
- shared state
- lifecycle
- caller guarantees
- blocking semantics

Do not infer concurrency properties from type names.

---

## 14. Metrics as conclusions

### Failure

Use LOC, coupling, churn, fan-out, or cyclomatic complexity as architectural verdicts.

### Correction

Use metrics to route attention.

Then perform semantic investigation.

Metrics generate candidates; they do not determine technical value.

---

## 15. False precision

### Failure

Produce scores such as:

- Architecture: 8.7/10
- Innovation: 9.2/10

without a defensible measurement model.

### Correction

Use calibrated categories:

- Exceptional
- High
- Moderate
- Routine
- Unknown

For originality:

- Conventional
- Strong engineering
- Distinctive design
- Unusual adaptation
- Plausible innovation
- Unverified innovation candidate

Report confidence separately.

---

## 16. Design intent hallucination

### Failure

State:

> The authors designed this specifically to achieve X.

when only implementation effects are visible.

### Correction

Prefer:

> This design has the effect of X.

or:

> The evidence suggests X was an important constraint.

Use stronger intent language only when supported by:

- ADRs
- comments
- commit history
- design documents
- issue/PR discussions

---

## 17. Originality suppresses learning value

### Failure

Downgrade an important mechanism because it comes from published research or an upstream project.

### Why it fails

Originality and learning value are different dimensions.

A published algorithm may still have:

- exceptional implementation depth
- central project importance
- difficult integration
- high system leverage
- excellent engineering value

### Correction

Lower originality when precedent exists.

Do not automatically lower:

- technical significance
- implementation depth
- project importance
- learning value

This failure mode was reinforced during DuckDB validation.

---

## 18. Product leverage mistaken for mechanism originality

### Failure

A feature creates major user value, so the underlying mechanism is described as technically novel.

### Correction

Separate:

- mechanism leverage
- system leverage
- user/product leverage

A conventional mechanism can create exceptional product leverage.

---

## 19. Outcome overclaim

### Failure

State:

- faster
- lower memory
- more scalable
- more reliable
- superior

without appropriate evidence.

### Correction

Use the outcome-language gate:

- designed to improve
- structurally enables
- measured to improve

Reserve measured language for empirical evidence.

---

## 20. Ignoring counterevidence

### Failure

Collect only evidence supporting an interesting conclusion.

### Correction

For every major technical-value or originality candidate ask:

> What is the strongest evidence that this conclusion is overstated?

Allow the answer to lower the classification.

---

## 21. Evidence-channel duplication

### Failure

Treat five source-code citations as five independent confirmations.

### Correction

Track evidence diversity.

Independent channels may include:

- source
- tests
- benchmarks
- docs/ADRs
- history
- issues/PRs
- external primary sources

---

## 22. Moving-target regression

### Failure

Compare two analysis runs against a moving branch or different repository revisions and attribute every changed finding
to the Skill or methodology.

### Why it fails

The repository itself may have added, removed, renamed, documented, or reorganized mechanisms between runs. Local
modifications, missing submodules, or incomplete LFS content can create the same distortion.

### Correction

Record the exact revision and worktree state for every run. For a strict regression, reuse the same immutable source
revision and comparable source availability. If that is impossible, classify the run as a targeted validation and
separate repository evolution from Skill behavior.

---

## 23. Source-mode overreach

### Failure

Claim exhaustive repository understanding from:

- indexed search
- documentation
- partial remote browsing

### Correction

Declare source mode before analysis.

Respect its evidence ceiling.

For `indexed-snapshot`, explicitly state that complete source coverage is not established.

---

## 24. Missing history fallback

### Failure

When Git history is unavailable, silently omit the second discovery channel.

### Correction

Use fallback signals:

- benchmark directories
- project-authored internals/design posts
- changelog/release notes
- test clusters
- paper/algorithm references in source
- subsystem-specific documentation

---

## 25. Endless deep dive

### Failure

Continue researching because more detail exists.

### Correction

Stop when:

- the mechanism is understood
- evidence supports the intended classification
- counterevidence has been checked
- comparator research no longer changes the conclusion
- additional work cannot change the result under the evidence ceiling

Rigor requires stopping rules.

---

## 26. Highlight recall failure

### Failure

Produce a polished Top Technical Highlights list without asking what was missed.

### Correction

Before final synthesis run the Highlight Recall Challenge:

1. Which parent subsystem may contain multiple highlights?
2. Which benchmarked mechanisms are absent?
3. Which design documents describe omitted mechanisms?
4. Which user-visible capability implies hidden implementation depth?
5. Which published technique remains an exceptional learning target?
6. Which broad subsystem label may be masking a specific mechanism?

Treat false negatives as seriously as false positives.

---

## 27. Context flooding mistaken for coverage

### Failure

Dump large repository-wide search results into context and treat the number of matches as evidence of complete
discovery.

### Why it fails

High-volume output hides mechanism boundaries, duplicates header and implementation signals, overweights common terms,
and consumes the context needed for semantic tracing.

### Correction

Discover in stages:

1. inventory directories and repository boundaries
2. summarize test and benchmark clusters
3. enumerate mechanism-bearing files
4. refine searches within candidate subsystems
5. read representative implementations and callers

Bound raw output, exclude generated/vendor trees by default, and record covered areas in a ledger.

---

# Final adversarial checklist

Before finishing, ask:

- Did I infer architecture from naming rather than behavior?
- Did documentation quality bias candidate selection?
- Did a parent subsystem hide important mechanisms?
- Did I compress candidates too early?
- Did I confuse complexity with value?
- Did I confuse custom code with innovation?
- Did I confuse performance with originality?
- Do citations semantically support the claims?
- Did I inspect important failure and lifecycle paths?
- Did I separate intent from observed effect?
- Did precedent incorrectly suppress learning value?
- Did product leverage inflate originality?
- Did I overclaim outcomes?
- Did I actively seek counterevidence?
- Are evidence channels genuinely independent?
- Did I record the exact revision and worktree state when available?
- Am I respecting the source-mode evidence ceiling?
- Did I run the Highlight Recall Challenge?
- Did I bound raw discovery output instead of flooding context?
- Do I have a defensible reason to stop?
