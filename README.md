# Codebase Intelligence

An evidence-driven Codex skill for understanding and evaluating software repositories.

It analyzes:

- architecture and execution paths
- important modules and mechanisms
- design decisions and trade-offs
- engineering strengths and technical difficulty
- technical and learning value
- originality and plausible innovation
- evidence quality, counterevidence, and uncertainty

Its central question is:

> What is technically meaningful in this repository, why does it matter, and how strong is the evidence?

## Why this skill is different

Codebase Intelligence keeps the following claims separate:

1. observed implementation
2. behavioral interpretation
3. design assessment
4. technical value
5. originality
6. innovation

It does not treat complexity, custom code, performance-oriented language, or unusual technology as evidence of innovation. Strong originality claims require comparison with conventional approaches, peers, upstream dependencies, or published techniques.

## Status

The current tagged release is **v0.2**. The main branch contains post-v0.2 evidence and reproducibility hardening that
has passed:

- a targeted DuckDB regression
- a blind cross-domain analysis of ripgrep
- a behavior-validated blind analysis of GJSON, including focused tests, allocation benchmarks, and the Go race detector

The skill remains experimental: validation supports the method, but does not establish exhaustive performance or recall
across every repository type.

## Repository layout

```text
skill/codebase-intelligence/
├── SKILL.md
├── agents/
│   └── openai.yaml
└── references/
    ├── design-and-value.md
    ├── evidence-confidence.md
    ├── failure-modes.md
    ├── innovation.md
    └── report-format.md
```

The complete installable skill is contained in `skill/codebase-intelligence/`.

## Install

Copy the skill directory into your Codex skills directory:

```bash
cp -R skill/codebase-intelligence ~/.codex/skills/codebase-intelligence
```

Restart Codex if the skill is not discovered immediately.

Validate a checkout before installing:

```bash
python3 /path/to/skill-creator/scripts/quick_validate.py skill/codebase-intelligence
```

The validator is bundled with Codex's `skill-creator` system skill; its absolute path depends on the local Codex
installation.

## Use

Invoke it explicitly:

```text
Use $codebase-intelligence to analyze this repository.
```

Or ask Codex for a deep, evidence-driven repository analysis. The skill supports automatic discovery when the request matches its scope.

Useful requests include:

```text
Analyze this repository's architecture and core execution paths.

Identify the most technically valuable mechanisms and explain why they matter.

Separate strong engineering, distinctive design, unusual adaptation, and plausible innovation.

Tell me what an experienced engineer should study in this codebase, with code evidence.
```

## Output principles

The skill favors:

- complete discovery with selective analysis depth
- execution traces over architecture inferred from folder names
- mechanism-level highlights over broad subsystem labels
- calibrated qualitative judgments over fake-precision scores
- explicit counterevidence and source limitations
- insight density over report length

Historical research reports, validation runs, working archives, and conversation transcripts are intentionally maintained outside this repository.

## License

No open-source license has been selected yet. Add one before making the repository public; until then, the source is not
licensed for general reuse.
