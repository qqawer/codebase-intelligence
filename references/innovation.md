# Originality and Innovation Analysis

Use this reference only after the mechanism and its technical value are understood.

Innovation is a high-bar conclusion.

## Keep four concepts separate

### Strong engineering

A conventional technique implemented unusually well.

### Distinctive design

A meaningful design choice that differs from a naive or common implementation.

### Unusual adaptation

An established technique adapted or combined in a non-trivial way for the repository's constraints.

### Plausible innovation

A meaningfully novel mechanism with strong comparative evidence and a demonstrated or well-supported advantage.

Do not collapse these categories.

## Innovation decision procedure

For every candidate, answer the following questions in order.

### 1. What problem is being solved?

State the concrete engineering constraint.

Avoid generic descriptions such as:

> improves performance

Prefer:

> avoids recomputing unaffected dependency-graph regions after a localized change

### 2. What is the baseline?

Identify a plausible conventional or naive implementation.

Without a baseline, originality cannot be evaluated.

### 3. What does this repository do differently?

Describe the actual mechanism.

Require implementation or behavioral evidence.

### 4. Is the difference necessary?

Ask whether the difference:

- solves a real constraint
- removes meaningful caller burden
- improves correctness
- enables scale
- reduces resource use
- enables a capability

Complexity added without leverage is not innovation.

### 5. What is the closest precedent?

Search for:

- upstream libraries
- acknowledged inspirations
- peer projects
- research papers
- standard algorithms
- common architecture patterns

### 6. What is actually original?

Separate:

- underlying algorithm
- implementation
- adaptation
- integration
- interface
- system architecture
- domain-specific semantics

A repository may use a conventional algorithm inside a distinctive system.

### 7. What advantage results?

Classify the evidence:

- intended advantage
- structurally enabled advantage
- empirically demonstrated advantage

Do not claim measured superiority without measurements.

### 8. What counterevidence exists?

Actively look for reasons to lower the originality claim.

Examples:

- the algorithm comes from an upstream dependency
- project documentation credits another system
- the same mechanism is common in peers
- the custom code mostly adapts an existing library
- benchmark evidence does not show the expected advantage

### 9. Classify the result

Use one of:

- Conventional engineering
- Strong engineering
- Distinctive design
- Unusual adaptation
- Plausible innovation
- Unverified innovation candidate

Prefer conservative classification when evidence is incomplete.

## Comparator Ledger

Before using strong originality language, record:

| Field | Required question |
|---|---|
| Problem | What difficult constraint is addressed? |
| Baseline | What would a conventional implementation do? |
| Closest precedent | Which peer, upstream project, or paper is closest? |
| Acknowledged inspiration | Does the project credit an external source? |
| Repository difference | What is materially different here? |
| Outcome difference | What advantage is demonstrated or structurally enabled? |
| Counterevidence | What weakens the originality claim? |
| Classification | What is the calibrated conclusion? |
| Confidence | How strong is the evidence? |

Do not skip the ledger for major innovation claims.

## Attribution discipline

Do not attribute an idea to the repository merely because the repository contains it.

Distinguish:

- invented by the project
- invented by project contributors in separate research
- implemented from published research
- adapted from an upstream dependency
- inspired by another project
- conventional technique
- attribution unknown

This is especially important for research-heavy repositories.

## Custom is not innovative

Reject reasoning such as:

> The project has a custom scheduler, therefore the scheduler is innovative.

Instead ask:

- why was custom behavior necessary?
- what differs from standard schedulers?
- what practical leverage results?
- does a comparable mechanism already exist?

## Complex is not innovative

Complexity can result from:

- accidental architecture
- legacy constraints
- compatibility requirements
- poor abstractions
- generated code
- inherently difficult domains

Complexity is an investigation signal, not an originality signal.

## Fast is not innovative

Performance can come from:

- implementation quality
- language choice
- compiler optimization
- batching
- caching
- better defaults
- architecture
- a genuinely new algorithm

Determine which mechanism causes the outcome before making an originality claim.

## Published does not mean unimportant

A repository can contain an exceptional implementation of a published technique.

When precedent exists:

- lower originality appropriately
- preserve technical significance when warranted
- preserve learning value when warranted
- explain the adaptation and integration

Example:

A database may implement a published join-ordering algorithm.

Correct conclusion:

> High technical significance; implementation/adaptation of published research.

Incorrect conclusion:

> Not interesting because it is not original.

## Innovation evidence threshold

Strong innovation claims should normally require:

1. direct mechanism evidence
2. behavioral understanding
3. comparative evidence
4. meaningful difference
5. counterevidence review

Prefer empirical outcome evidence when claiming superiority.

If comparative evidence is unavailable, use:

> Unverified innovation candidate

rather than:

> Innovative.

## Final wording

Prefer precise statements such as:

> This is a distinctive integration of established mechanisms.

> The underlying algorithm is conventional, while the repository-specific adaptation is technically significant.

> The mechanism appears unusual relative to the compared implementations, but available evidence is insufficient to establish innovation.

> This is strong engineering rather than a novel algorithm.

> The technique is published, but its implementation and integration remain exceptional learning targets.

Avoid promotional language.
