# PLAN.md — The 10-Step Plan (instantiated for ARC-AGI)

> From EXPORT_RULES §C. Each step: principle → action → the failure it prevents → **GATE**
> (the condition that must be true before moving on). Loop steps 7–9 each iteration.
> Revisit 1–2 whenever a result contradicts the model.
>
> Status legend: ⬜ not started · 🟡 in progress · ✅ done

---

### ✅ 1. Define the objective exactly  *(Rule 1)*  — done 2026-06-23
- **Action:** Write the scoring/success formula + platform meta (aggregation, idempotency, quotas, deadlines) into REPORT.md and PROJECT.md.
- **Prevents:** optimizing the wrong thing.
- **GATE:** you can state "the number" and exactly how it is computed.
- **ARC-AGI note:** if ARC Prize — objective is % of hidden eval tasks solved (exact-match grids, usually 2 attempts/task); if local research — solve rate on public eval. Pin down which.

### 🟡 2. Map constraints; identify the binding one  *(Rule 3, 12)*
- **Action:** List every hard limit (compute, wall-clock, token/$ budget, attempts). Hypothesize which bites. Plan to MEASURE it.
- **Prevents:** silent blow-ups on an unmodeled axis.
- **GATE:** binding-constraint hypothesis written in PROJECT.md, marked UNMEASURED.

### ✅ 3. Recon prior art before building  *(Rule 5, 6)*  — done 2026-06-23 → see [docs/recon.md](docs/recon.md)
- **Conclusion:** build a **no-LLM graph-based exploration agent** (frame-hash state graph + action-effect
  learning + frontier exploration; priority-tier pixels for ACTION6). LLMs score ~0.2–0.4%, best preview
  agent 12.58%, graph method 19 levels vs random 6. Reuse the repo harness, NOT the LLM templates.
- **Action:** ARC Prize forums, winning solutions/notebooks, papers (DSL search, LLM program synthesis, TTT), repos. Capture findings + sources in a `docs/recon.md`.
- **Prevents:** re-deriving published answers. (Biggest single jump in the source project came from external intel.)
- **GATE:** ≥3 cited prior approaches summarized; reuse-vs-build decision made.

### ✅ 4. Minimal end-to-end baseline  *(Rule 7)*  — done 2026-06-23
- **Action:** One trivial solver (e.g. identity / most-common-output) through the WHOLE pipeline: load task → predict → score → record.
- **Prevents:** late integration surprises; anchors all later comparisons.
- **GATE:** one real score number recorded in LOG.md.

### ✅ 5. Feedback loop that correlates with the true metric — and validate it  *(Rule 8)*  — done 2026-06-23
- **NOTE:** the offline local scorecard *is* the true metric (same formula, `level_scores` +
  `level_baseline_actions`), so the proxy = the real thing. Validation trivially holds (random=0 both ways).
- **Action:** Fast local proxy that models the BINDING constraint, not just correctness. Check proxy vs the baseline's real result.
- **Prevents:** false-green proxies (local test passes, real run blanks).
- **GATE:** proxy and real result agree on ≥1 datapoint.

### ⬜ 6. Reproducible + verified shipping  *(Rule 9, 16)*
- **Action:** Deterministic build, checksum/verify-before-submit, no hand-transcription. Secrets out of VCS from day one.
- **Prevents:** silent corruption costing a full slow cycle; leaks.
- **GATE:** build script + checksum verify in place; `.gitignore` covers secrets.

### ⬜ 7. Form hypotheses; test the riskiest first  *(Rule 4)*
- **Action:** For each big unknown, the cheapest experiment that could falsify it. Hold beliefs as falsifiable.
- **Prevents:** confident-wrong direction.
- **GATE:** riskiest unknown has a planned cheap experiment.

### ⬜ 8. Iterate with hedged, parallel experiments; spend attempts deliberately  *(Rule 10, 11)*
- **Action:** Resolve gating unknowns in ONE cycle with 2+ variants. Track what is free (retryable/max-over-attempts) vs irreversible.
- **Prevents:** slow serial guessing; burning scarce slots.
- **GATE:** each iteration ships a hedged pair when an unknown gates it.

### ⬜ 9. Maintain durable memory continuously  *(Rule 13, 14)*
- **Action:** Append LOG.md, update PROJECT.md, rewrite REPORT.md when the model flips.
- **Prevents:** relearning; re-injecting disproven assumptions.
- **GATE:** every iteration leaves all three files current.

### ⬜ 10. Manage risk, resources, security to the end  *(Rule 12, 15, 16)*
- **Action:** Conservative on the RIGHT axis then scale; de-risk irreversible/outward actions; respect quotas; rotate secrets; keep a rollback.
- **Prevents:** expensive irreversible mistakes and leaks.
- **GATE:** rollback path exists before any irreversible action.

---

## Anti-patterns to watch (EXPORT_RULES §D)
- Armchair-modeling the constraint, then shipping into a slow feedback cycle.
- Trusting our own theory over the forum and over real results.
- Treating a passing local test as proof the real run passes.
- Letting REPORT.md drift until it misleads.
- Scaling the visible knob while the real cost goes unmodeled.
- Burning attempts serially on single guesses.

## Where we are
**Steps 1, 3, 4, 5 ✅; step 2 measured (n=1).** Objective = ARC-AGI-3. Offline harness runs the real
metric for free. Random agent = 0/7 levels on ls20 → completion is the gate. Recon done → prior art
says build a **no-LLM graph-based exploration agent** (see [docs/recon.md](docs/recon.md)).
**Next: steps 7–8** — implement v1 exploration agent (frame-hash state graph + action-effect learning
+ frontier search; ACTION6 priority pixels), raise `MAX_ACTIONS`, measure on the offline scorer vs the
random 0/7 baseline. Riskiest unknown to test first: does frame-hashing + untested-action exploration
clear ls20 level 1 at all within a few-thousand-action budget?
Skipped for now: step 6 (shipping/secrets — `.env` already gitignored; revisit before online submit).
