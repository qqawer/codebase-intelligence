# Codebase Intelligence

An evidence-driven Codex skill that turns unfamiliar software repositories into source-grounded architecture and
technical-value reports.

It traces how a system actually executes, identifies the mechanisms that matter most, and separates strong engineering
from originality and plausible innovation.

## What it produces

Depending on the question and available evidence, Codebase Intelligence can produce:

- a repository and runtime architecture map
- representative end-to-end execution traces
- ranked technical highlights at mechanism level
- design-quality and technical-value analysis
- conventional versus distinctive implementation classification
- upstream, precedent, and inspiration attribution
- counterevidence, confidence, and source limitations
- weaknesses, trade-offs, and recommended learning targets

The default is an insight-dense report shaped by the repository—not a fixed inventory of every directory.

## Why it is different

Codebase Intelligence keeps six kinds of claim separate:

```text
Observed implementation
        ↓
Behavioral interpretation
        ↓
Design assessment
        ↓
Technical value
        ↓
Originality
        ↓
Innovation
```

A mechanism can be technically exceptional without being original. Conversely, custom or complicated code is not
automatically valuable or innovative.

The skill therefore requires:

- source-mode and revision disclosure
- execution tracing instead of architecture inferred from folder names
- independent documentation-led and structural discovery
- nested scans inside important parent subsystems
- comparator and upstream attribution before originality claims
- active counterevidence and a final highlight-recall challenge
- measured language only when runtime or benchmark evidence supports it

## Quick start

Clone the repository into the Codex skills directory:

```bash
git clone https://github.com/qqawer/codebase-intelligence.git \
  ~/.codex/skills/codebase-intelligence
```

Restart Codex if the skill is not discovered immediately.

To update an existing installation:

```bash
git -C ~/.codex/skills/codebase-intelligence pull
```

## Use

Invoke it explicitly:

```text
Use $codebase-intelligence to analyze this repository.
```

Example requests:

```text
Trace this repository's core execution paths and explain its architecture.

Rank its strongest technical mechanisms and explain why they matter.

Separate conventional engineering, distinctive adaptation, and plausible innovation.

Tell me what an experienced engineer should study in this codebase, with evidence and counterevidence.
```

The skill supports normal implicit discovery when a request clearly calls for deep repository understanding. It is
currently Codex-first; compatibility with other agent harnesses has not been validated.

## Example finding shape

A major finding is reported at mechanism level rather than as generic praise:

```text
Mechanism: <what the system actually does>
Problem: <the difficult constraint it solves>
Why it matters: <system, product, and learning leverage>
Difficulty: Exceptional | High | Moderate | Routine | Unknown
Distinctiveness: Conventional | Strong | Distinctive | Unusual | Innovation candidate
Attribution: repository-original | adapted | upstream | published | conventional | unknown
Counterevidence: <strongest reason not to overstate the finding>
Evidence: <implementation, tests, runtime, history, docs, comparators>
Confidence: High | Medium | Low
```

## Validation status

The current main branch is a post-v0.2 release candidate. The methodology and Skill have been exercised through:

- a targeted DuckDB regression covering previously missed nested mechanisms
- a blind cross-domain ripgrep analysis that recovered all four project-public performance themes without false
  innovation promotion
- a behavior-validated GJSON analysis with the project test suite, focused lifecycle and numeric tests, allocation
  benchmarks, and the Go race detector

These runs support the method's cross-project usefulness; they do not prove exhaustive recall or performance across all
repository types. Full research artifacts and conversation archives are intentionally maintained outside this Skill
repository.

## Repository layout

```text
codebase-intelligence/
├── SKILL.md
├── README.md
├── LICENSE
├── agents/
│   └── openai.yaml
└── references/
    ├── design-and-value.md
    ├── evidence-confidence.md
    ├── failure-modes.md
    ├── innovation.md
    └── report-format.md
```

The repository root is the complete installable Skill. It intentionally contains no historical reports, generated
analyses, or conversation transcripts.

## Reference loading

`SKILL.md` is the entry point. Supporting references are loaded only when their decisions are needed:

- evidence and confidence for source modes, confidence, and evidence ceilings
- design and value for deeper design-quality and technical-value analysis
- innovation for comparator-led originality investigation
- failure modes for relevant corrections and final adversarial review
- report format for full Project Intelligence Reports

## Limitations

- Findings are bounded by the source, revision, history, generated files, dependencies, and runtime evidence available.
- Static structure alone does not prove runtime behavior or measured performance.
- Originality conclusions depend on accessible upstream, peer, and historical evidence.
- Large or polyglot repositories require selective depth; complete discovery does not mean reading every file equally.
- Validation has been performed with Codex, not every agent or model that may understand the Skill format.

## Development

Validate the Skill structure with the validator bundled in Codex's `skill-creator` system skill:

```bash
python3 ~/.codex/skills/.system/skill-creator/scripts/quick_validate.py .
```

The validator checks structure and metadata. Behavioral confidence comes from realistic repository analyses, not from
schema validation alone.

## License

Codebase Intelligence is available under the [MIT License](LICENSE).
