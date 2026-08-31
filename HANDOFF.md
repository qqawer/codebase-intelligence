# Codebase Intelligence — Project Handoff

## Repository

https://github.com/qqawer/codebase-intelligence

Branch: `main`

Current stable Skill:

`skill-v0.2`

## Goal

Build an evidence-driven Codebase Intelligence Skill for analyzing software repositories.

The Skill should identify and explain:

- architecture
- execution paths
- important modules and mechanisms
- design decisions
- engineering strengths
- technical difficulty
- technical value
- learning value
- originality
- plausible innovation

The goal is not merely codebase summarization.

The central question is:

> What is technically meaningful in this repository, why does it matter, and how strong is the evidence?

## Core Principle

Keep these claims separate:

1. observed implementation
2. behavioral interpretation
3. design assessment
4. technical value
5. originality
6. innovation

In particular:

`Technical Value != Originality != Innovation`

## Current Method

The current analysis pipeline is:

1. Declare source mode
2. Repository reconnaissance
3. Architecture mapping
4. Dual candidate discovery
5. Execution tracing
6. Adaptive analysis depth
7. Nested candidate discovery
8. Design reasoning
9. Technical-value analysis
10. Comparator Ledger
11. Originality / innovation analysis
12. Counterevidence
13. Evidence verification
14. Highlight Recall Challenge
15. Final synthesis
16. Deliberate stopping

## Research History

The methodology was developed by studying five open-source approaches:

1. codebase-analysis
2. codebase-onboarding
3. improve-codebase-architecture
4. architectural-review
5. codebase-design

The research produced an evidence-driven methodology for repository architecture, design, technical-value, and innovation analysis.

## uv Validation

The methodology was tested against Astral's `uv`.

Important findings included:

- explicit source modes
- dual candidate discovery
- mechanism/system/product leverage
- Comparator Ledgers
- outcome-language gates
- evidence ceilings
- source authority/freshness
- stopping rules

This produced `method-v0.1`.

## Skill v0.1

The validated methodology was translated into the first Codebase Intelligence Skill.

## DuckDB Blind Validation

Skill v0.1 was tested blindly against DuckDB.

Result:

`PARTIAL PASS`

The Skill performed well on:

- architecture discovery
- execution-path discovery
- technical-value reasoning
- innovation precision
- evidence discipline
- counterevidence

The main weakness was:

`Precision > Recall`

The Skill identified important parent subsystems but sometimes failed to discover important mechanisms inside them.

This failure was named:

`Parent-Subsystem Masking`

Examples included:

- arbitrary subquery decorrelation
- parallel grouped aggregation
- persistent/lazy ART
- detailed out-of-core mechanisms

## Skill v0.2

v0.2 was created to improve technical-highlight recall.

Major additions:

### Nested Candidate Discovery

Every Tier 3+ parent subsystem receives a bounded internal mechanism scan.

For example, an optimizer may contain:

- join ordering
- decorrelation
- statistics propagation
- predicate pushdown
- expression rewriting

### Highlight Recall Challenge

Before final synthesis, actively search for important mechanisms hidden by broad subsystem labels.

### Originality vs Learning Value

Published or upstream techniques may still be exceptional learning targets.

External precedent should lower originality when appropriate, but should not automatically lower:

- technical significance
- implementation depth
- project importance
- learning value

## Current Skill Layout

skill/codebase-intelligence/
- SKILL.md
- agents/openai.yaml
- references/evidence-confidence.md
- references/design-and-value.md
- references/innovation.md
- references/failure-modes.md
- references/report-format.md

## Current Status

Research
→ Methodology
→ uv Validation
→ Skill v0.1
→ DuckDB Blind Validation
→ Skill v0.2

## Next Step

Run a frozen DuckDB regression using `skill-v0.2`.

Specifically test whether v0.2 now discovers:

- arbitrary subquery decorrelation
- parallel grouped aggregation
- persistent/lazy ART
- detailed out-of-core mechanisms

Also verify that increased recall does not increase false innovation claims.

If that regression passes, proceed to multi-project benchmarking.

## Instructions for a New ChatGPT Account

Before changing the Skill:

1. Read this `HANDOFF.md`.
2. Read `skill/codebase-intelligence/SKILL.md`.
3. Read all files under `skill/codebase-intelligence/references/`.
4. Inspect Git history and tags.
5. Preserve evidence ceilings and counterevidence requirements.
6. Keep technical value, learning value, originality, and innovation separate.
7. Validate important methodology changes against real repositories.

Current milestone:

`DuckDB regression using skill-v0.2`
