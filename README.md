# Codebase Intelligence

An evidence-driven Codex skill that turns unfamiliar software repositories into source-grounded architecture and
technical-value reports.

It traces how a system actually executes, identifies the mechanisms that matter most, and separates strong engineering
from originality and plausible innovation.

## What it produces

Depending on the question and available evidence, Codebase Intelligence can produce:

- a bounded, machine-readable repository discovery snapshot
- a persistent Markdown Project Intelligence Report for a full analysis
- a machine-readable run record with granular passed, failed, unavailable, and skipped checks
- a repository and runtime architecture map
- representative end-to-end execution traces
- ranked technical highlights at mechanism level
- design-quality and technical-value analysis
- conventional versus distinctive implementation classification
- upstream, precedent, and inspiration attribution
- counterevidence, confidence, and source limitations
- weaknesses, trade-offs, and recommended learning targets

The default is an insight-dense report shaped by the repository—not a fixed inventory of every directory.

For a full analysis, the report is written to a dedicated Markdown artifact before completion. The final chat response
links that file and gives a concise verdict. Focused questions may remain conversational. Generated reports belong in a
user-selected or dedicated research workspace, not in this installable Skill or the analyzed repository unless that
location is explicitly requested.

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

For a compact read-only inventory without running the full analysis:

```bash
python3 scripts/repository_snapshot.py /path/to/repository --format markdown
python3 scripts/repository_snapshot.py /path/to/repository --format json
```

The script uses only the Python standard library. It records Git identity and worktree state and identifies bounded
discovery clusters such as manifests, likely entry points, tests, benchmarks, documentation, CI, and source boundaries.
Its classifications are starting points for investigation, not architecture or quality conclusions.

Full reports use a colocated `run-record.json` to preserve runtime evidence without reducing partial validation to a
boolean. `research_run.py` records explicitly authorized commands or unavailable checks; `validate_report.py` checks
identity, immutable source links, line ranges, publication safety, evidence consistency, and protocol values. See
[`references/run-record.md`](references/run-record.md) for the workflow.

Analysis depth is adaptive. A normal repository-research request uses a standard architecture pass with targeted
runtime checks; the frozen-ledger, comparator, full-suite, and publication workflow is reserved for comprehensive,
ranked, originality-focused, or explicitly publishable work. This keeps routine analysis from paying the latency cost
of the full research protocol.

For a new clean local checkout, `research_session.py` orchestrates the mechanical boundaries without automating the
analysis itself: `init` fixes identity and creates the standard session at the inventoried phase, `status` reports the
next legal phase and gate blockers, and `publish` redacts machine-local paths, preserves raw and publication-safe
output hashes, then strictly validates, finalizes, and indexes an already synthesized report. It never selects
technical highlights, runs target commands, commits, or pushes. `publication_safety.py` exposes the same deterministic
sanitizer for custom publication workflows.

`source_link.py` generates report-ready GitHub citations from a local checkout, resolving the repository remote and
revision, validating the file and line range against committed content, and encoding the path. `build_research_index.py`
then derives finalized-run metadata from colocated records, updates `runs.json`, and regenerates the marked full-report
table in a dedicated research workspace. Running the latter without `--write` is a drift check suitable for CI.

Ranked findings use a structured `candidate-ledger.json`. `candidate_ledger.py` records coverage, representative traces,
mechanism-level candidates, evidence, counterevidence, provenance, and runtime hypotheses; freezing writes a content
hash and blocks later mutation. The run record enforces forward-only research phases so a report cannot finalize before
inventory, candidate freeze, validation, comparator review, synthesis, and report validation are accounted for.

Comparator research uses a separate `comparator-ledger.json`. `comparator_ledger.py` requires every Tier 3+ candidate
to have comparison coverage or an explicit exclusion, preserves source identity limits and access dates, records the
material difference and strongest originality counterevidence, and freezes the result before synthesis.

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
├── scripts/
│   ├── repository_snapshot.py
│   ├── candidate_ledger.py
│   ├── build_research_index.py
│   ├── comparator_ledger.py
│   ├── publication_safety.py
│   ├── research_session.py
│   ├── research_run.py
│   ├── source_link.py
│   ├── validate_report.py
│   └── test_*.py
└── references/
    ├── design-and-value.md
    ├── candidate-ledger.md
    ├── comparator-ledger.md
    ├── evidence-confidence.md
    ├── failure-modes.md
    ├── innovation.md
    ├── run-record.md
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
- run record for execution capture, report validation, and sidecar schema

The repository snapshot script is executed only for local source discovery. Its implementation does not need to be
loaded into model context during ordinary use.

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

The repository also includes a standard-library package validator for CI and environments without Codex's bundled
system skills:

```bash
python3 scripts/validate_skill_package.py .
```

Run all deterministic script tests, then smoke-test the bundled read-only inventory in both output formats:

```bash
python3 -m unittest discover -s scripts -p 'test_*.py'
python3 scripts/repository_snapshot.py . --format markdown --max-items 5
python3 scripts/repository_snapshot.py . --format json --max-items 5
```

## License

Codebase Intelligence is available under the [MIT License](LICENSE).
