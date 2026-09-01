# Standard Report

Use this reference for the default public repository-analysis report. Standard reports prioritize insight density and
source-grounded conclusions without the Full audit protocol.

Recommended shape, adapted to available evidence:

1. **Executive verdict** — what the project does, architectural character, strongest findings, and main caveat.
2. **Identity and evidence boundary** — repository, revision/source mode, analysis date, worktree state, source gaps,
   and runtime limits.
3. **Architecture map** — important subsystems, boundaries, dependency direction, ownership, and data/control flow.
4. **Representative execution paths** — two or three end-to-end traces including failure, fallback, or cleanup.
5. **Ranked mechanisms** — normally three to five; for each explain problem, mechanism, value, design quality,
   attribution, strongest counterevidence, evidence, and confidence.
6. **Weaknesses and trade-offs** — concrete contract burden, coupling, lifecycle, performance, or operability costs.
7. **Runtime validation** — only checks actually run or inspected; distinguish pass, fail, unavailable, and skipped.
8. **What to learn and final verdict** — transferable lessons and a calibrated overall assessment.

Use repository-relative source locations or immutable remote links. State measured outcomes only when a recorded
workload supports them. Bounded comparator research may inform a distinctiveness or originality answer, but Standard
does not create candidate/comparator ledgers, run records, receipts, or research indexes.
