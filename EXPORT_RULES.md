# EXPORT_RULES — a portable playbook for doing any project much better

> Distilled from the JED "AI Agent Security" Kaggle project, but written to be
> **project-agnostic**. The point of this file is to *export* the hard-won lessons
> so the next project starts from the corrected understanding instead of relearning it.
>
> Read top-to-bottom once. Then keep §C (the 10-step plan) open while working.
> This project's instantiation of §C lives in [PLAN.md](PLAN.md).

---

## A. The rules (generalized principles)

### Understand before you build
1. **Write the objective function down first.** Know exactly what is measured, how it is computed, and how partial results aggregate. If you cannot write the scoring formula, you are not ready to build.
2. **Learn the platform meta, not just the per-run score.** Idempotency, max-over-attempts vs latest-wins, quotas, rate limits, deadlines, retry cost, "is a failure free or penalized." The meta often changes strategy more than the per-run rules.
3. **Find the *binding* constraint and measure it.** Only one or two limits actually bite. Instrument and measure — don't assume which.
4. **Hold assumptions as falsifiable hypotheses.** Distrust elegant theories that have not produced a measured result. When an external claim conflicts, go back to ground truth.

### Use what exists
5. **Search prior art FIRST — reuse beats rebuild.** Budget a recon pass *before* writing code. Cite the source.
6. **Community/empirical signal outranks your own armchair analysis.** A result on the real system cannot lie.

### Build a loop that tells the truth
7. **Get one real end-to-end datapoint early.** A minimal baseline through the *whole* pipeline anchors every later comparison.
8. **Build a fast proxy that *correlates* with the true metric — and validate it.** A local test that doesn't model the binding constraint gives false confidence.
9. **Make every action reproducible and verified.** Deterministic builds, checksums, verify-before-ship, no hand-transcription.

### Iterate deliberately
10. **Resolve key unknowns with parallel, hedged experiments.** Run 2+ variants in the same cycle to settle a gating uncertainty.
11. **Spend scarce attempts on purpose.** Know what is free (retryable, max-over-attempts) vs irreversible.
12. **Be conservative on the *right* axis, then scale.** Caution on the wrong variable wastes the slot without buying safety.

### Keep durable memory
13. **Three memory layers:** an append-only **log**, a **state map** (current truth), a **report** (corrected mental model).
14. **Fix stale docs the moment the model changes.** A confidently-wrong doc re-injects disproven assumptions into future-you.

### Manage risk and security
15. **De-risk irreversible and outward-facing actions.** Confirm before publishing/deleting. Have a rollback.
16. **Secrets hygiene from day one.** Credentials out of VCS, never printed, rotated when done.

---

## B. Concrete → general (source-project lessons)

| What happened | General lesson |
|---|---|
| Mapped scoring from the SDK but got the dominant lever wrong 3×. | Source-reading ≠ truth; a measured result + community can overrule it (4, 6). |
| Days spent deriving what a forum thread + competitor notebook already stated. | Recon the community FIRST (5). |
| Versions timed out: modeled constraint as candidate-count, real cost was tokens-per-candidate under per-phase budgets. | Find and MEASURE the binding constraint (3). |
| More-conservative versions still failed (conservative on N, not on token cost). | Conservatism on the wrong axis is not safety (12). |
| `local_test` passed even for runs that blanked on the real system. | A proxy not modeling the binding constraint gives false green (8). |
| "Blank is free" (max over submissions) inverted the risk profile. | Learn the platform meta (2). |
| Byte-exact build + sha-verify killed silent deploy-corruption bugs. | Reproducible + verified deploys (9). |
| Hedged pair shipped together to settle a gating unknown in one cycle. | Hedged parallel experiments (10). |
| Three memory files carried context across sessions; the report went stale. | Three-layer memory works but must be maintained (13, 14). |
| A live API token sat in a config file and surfaced in output once. | Secrets hygiene + rotation (16). |

---

## C. The 10-step plan
1. Define the objective exactly. *(gate: you can state the number and how it's computed.)*
2. Map constraints; identify the binding one.
3. Recon prior art before building.
4. Stand up a minimal end-to-end baseline.
5. Build a feedback loop that correlates with the true metric — and validate it.
6. Make shipping reproducible and verified.
7. Form explicit hypotheses; test the riskiest first.
8. Iterate with hedged, parallel experiments; spend scarce attempts deliberately.
9. Maintain durable memory continuously.
10. Manage risk, resources, and security to the end.

> Loop 7–9 every iteration. Revisit 1–2 whenever a result contradicts your model.
> See [PLAN.md](PLAN.md) for this project's gated instantiation.

---

## D. Anti-patterns
- Armchair-modeling the constraint, then shipping into a slow feedback cycle.
- Trusting your own theory over the forum and over real results.
- Treating a passing local test as proof the real run will pass.
- Letting the report drift until it actively misleads.
- Scaling the visible knob while the real cost goes unmodeled.
- Burning attempts serially on single guesses.

---

## E. One-line version
> Know the exact objective and its meta; find and *measure* the binding constraint; steal the
> community's answer before building; baseline early; make your feedback loop tell the truth;
> ship reproducibly; resolve unknowns with cheap hedged experiments; keep three layers of
> corrected memory; and spend scarce, irreversible resources on purpose.
