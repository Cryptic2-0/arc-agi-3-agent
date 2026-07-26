# recon.md — Prior Art for ARC-AGI-3 (PLAN step 3)

> Captured 2026-06-23 from web recon. Goal: don't re-derive published answers.
> Conclusion drives the reuse-vs-build decision at the bottom.

## The headline number that sets expectations
- **Humans: 100%. Frontier LLMs: ~0.2–0.4%.** (Gemini 3.1 Pro 0.37%, GPT-5.4/Grok 4.2 similar,
  Claude Opus 4.6 0.2%.) Preview-phase **best agent = 12.58%**.
- Takeaway: **a naive LLM agent scores ~0.** The repo's `llm_agents`/`reasoning_agent` templates are
  NOT the path. Winners are small, grounded, exploration-driven systems — not big language models.

## Preview leaderboard — what worked (cited)
| Rank/score | Team | Method | Lesson |
|---|---|---|---|
| 1st, **12.58%** | StochasticGoose | **CNN + RL**: predict which actions change the frame → explore efficiently. Completed 2 games / 18 levels but needed **255,964 actions** (efficiency awful, completion-first). | Learn action→frame-change effects. |
| —, 8.04% | Fluxonian | **DSL + LLM hybrid** | structured action language helps; LLM alone doesn't. |
| 2nd, 6.71% | Blind Squirrel | **"Smart Random with Rules"**: build **state graph** from frames, **prune non-productive actions**. | cheap, deterministic, beats LLMs. |
| —, 4.37% | Play Zero | Random + LLM video analysis | weak. |
| —, 3.70% | Tomas Engine | **Pure LLM** | poor, "crashed often". |
| —, 3.64% | Explore It | **Frame graph** — track state changes per action | exploration core. |

## Graph-Based Exploration paper (arxiv 2512.24156) — concrete, reusable method
Reported: at a 4000-action budget, **graph method = 19 levels** vs **random = 6** vs **LLM+DSL = 5**
(private games). Official submission 12 levels, 3rd place. Method:
1. **State = visual hash of the frame.** Segment frame into single-color connected components; **mask
   the status/UI bar** (kills spurious state churn); hash the masked image → unique state id.
2. **Build a transition graph** over hashed states as you act (state → action → next state).
3. **Hierarchical exploration (their Algorithm 1):**
   - If current state has untested actions at priority ≤ p → pick a random untested high-priority action.
   - Else if some reachable known state has untested actions → **navigate shortest path** to that frontier state.
   - Else → raise priority threshold p and recurse.
4. **Click games (ACTION6, 4096 pixels):** stratify visual segments into **5 priority tiers** by how
   likely they're interactive buttons/objects → click those first, not random pixels. Huge search cut.
5. **Goal detection: none explicit.** Rely on env feedback — level advances when (unknown) win condition
   met; otherwise reset at step limit. Binary signal: `levels_completed` ticks up, or reset.

## Cross-cutting pattern (every winner shares it)
Learn the **action→consequence** mapping by *iterative testing*, build a **discrete state graph**,
**prune no-op / non-productive actions**, and **explore the frontier systematically** (BFS/shortest-path).
Memorization and pure language understanding lose. Grounded interaction wins.

## Practical build aids
- Repo ships LangGraph templates (`langgraph_thinking`, `langgraph_functional_agent`); third-party
  walkthrough: joinplank.com/articles/arc-prize-langgraph. Useful structure, but LLM core = low ceiling.
- Our **offline local scorecard already returns `level_scores` + `level_baseline_actions`** → we can
  benchmark any exploration agent on the 25 public games for free, exactly like the papers' tables.

## DECISION (step 3 GATE): build, don't reuse the LLM templates
**Build a no-LLM graph-based exploration agent**, mirroring the paper + Blind Squirrel:
1. Hash frames (connected-component segmentation + status-bar mask) → state id.
2. Maintain transition graph + per-state untested-action set; record which actions changed the frame.
3. Exploration policy: untested action → else shortest-path to a frontier state with untested actions
   → else widen. For ACTION6, prioritize segmented object/button pixels over the 4096-pixel grid.
4. Raise `MAX_ACTIONS` well above 80 (paper uses 4000-action budgets; human baselines reach ~192/level).
5. Measure on the offline scorer vs the random baseline (currently 0/7 on ls20) as the first gate.
Why: matches the measured binding constraint (completion via exploration), is cheap/offline-iterable,
and the data says it beats both random and LLM agents by 3–4×.

## Sources
- https://arcprize.org/blog/arc-agi-3-preview-30-day-learnings
- https://arxiv.org/html/2512.24156v1  (Graph-Based Exploration for ARC-AGI-3)
- https://arxiv.org/html/2603.24621v1  (ARC-AGI-3 technical report)
- https://arcprize.org/competitions/2026/arc-agi-3
- https://www.joinplank.com/articles/arc-prize-langgraph

---

# ADDENDUM 2026-07-07 — Milestone-1 open-source recon (supersedes the DECISION above)

## What happened
Milestone 1 (June 30) forced winners to open-source. LB reset: top = 1.56, top-20 ≥ 1.30,
nearly all forks of the winner. Our graph line (0.24 best) is obsolete.

## Winner: Tufa Labs "duck harness" (1.21 LB; MIT/CC0 per comp rules)
- Kernel: `jeroencottaar/tufa-labs-duck-harness-june-30-milestone-winner` (readable) /
  `taaf-duck-harness-kaggle` v21 (the scoring run). Writeup: comp discussion **717133**.
  Source snapshot: dataset `jeroencottaar/taaf-kaggle-source-share` → local `external/taaf_source/`.
- Architecture: **LLM agent + Python tool sandbox** ("the duck"), via TAAF framework.
  - Model: **Qwen3.6-27B-FP8** served by local vLLM (wheelhouse dataset; vllm 0.19, torch 2.10),
    Kaggle **RTX Pro 6000** (96GB), 64k max-model-len, thinking on, temp 0.6.
  - The model NEVER sees the raw numeric grid. It gets: `current_frame.ascii`,
    `current_frame.segmentation` (connected components, hashes, containment, adjacency),
    `history`/`transitions`, `valid_actions`, `last_action_result` (board_changed,
    level_completed, ...). Actions: UP/DOWN/LEFT/RIGHT/SPACE/MOUSE(row,col).
  - Fresh sandbox per tool call; stdlib-allowlist imports; calls `action(...)` inline.
  - Persistent "world model" note across turns; context eviction (oldest first) for
    indefinite play. Multimodal: current grid as image, 4× upscale.
  - Runtime: 28 games concurrent, 7920s/game cap, soft notebook deadline.
- Author-named improvement levers: context compaction/memory system, better visual
  perception, stronger base model. Reported variance ±0.4 → validate over multiple runs.

## Other intel
- 2nd place: `ruichardliu/milestone1-2nd-solution`. 3rd: `mbmmurad/...-lb-0-86-...` (0.86).
- Gemma-4-31B reflection agent kernel (`ko0kip/arc-agi-3-gemma-4-31b-reflection-agent`) —
  "Gemma 4 31B QAT + LeWM/JEPA dynamics model", 0.79 public. Alternative model family to test.
- Symbolica "Agentica SDK": claims 36% on the 25 public games (blog, unverified, likely
  API-model-driven → not Kaggle-legal, but ideas may transfer).
- Papers: "Executable World Models for ARC-AGI-3" (arxiv 2605.05138), "Explore Before You
  Solve" (arxiv 2605.25931).

## NEW DECISION
Fork the duck (done: `soumyacryptic/taaf-duck-harness-fork`), replicate ~1.2, then iterate
via the customization hook + TAAF source. Offline validation stays: the notebook's
non-submission mode plays the 25 public games end-to-end.

---

# ADDENDUM 2026-07-12 — Paradigm survey: alternatives to "commands as Python"

Question explored: the duck routes game commands through a Python sandbox — what other
action-interface paradigms exist, and what do they score? (Sources cited per entry.)

| Paradigm | Best known result | Verdict for us |
|---|---|---|
| Direct action emission (LLM picks ACTION1-7, no code) | naive loops 0.2-0.4%; AERA explore→verify→plan 4/25 games ([2605.25931](https://arxiv.org/abs/2605.25931)) | Dead end — LLMs can't compute over grids in-context. |
| No-LLM graph exploration | Blind Squirrel 6.71% (preview); our GraphExplorer 0.24 LB | Plateaus at L1s; but FREE (CPU-only) → see portfolio idea below. |
| Online CNN+RL frame-change prediction | StochasticGoose 12.58% (preview) at 255k actions | Structurally punished now: metric SQUARES action-efficiency. |
| DSL + LLM hybrid | Fluxonian 8.04% (preview) | Superseded by free-form code (duck). |
| Learned world model (JEPA/dynamics) | Gemma-4-31B reflection agent 0.79 public LB | Real but below duck line (~1.2-1.6). |
| **Executable world model** (agent writes a Python SIMULATOR of the game, verifies vs observations, plans inside it) | **GPT-5.5: 15/25 public fully solved, 58% RHAE** ([2605.05138](https://arxiv.org/abs/2605.05138)) | Strongest known public-set result — but needs frontier API reasoning; our offline 27-35B can't sustain a verified simulator today. Revisit at milestone 2 (stronger local models). |
| Determinism / replay search | banking & transfer grafts (in our v5+) | Already exploited surgically. |

Cross-cutting: code-as-ACTUATOR (duck) beats code-free because the model gets exact grid
computation + batched actions + self-verification; code-as-WORLD-MODEL (simulator) is the
next paradigm up, gated on model strength. AERA paper also warns: all 25 public games are
solvable by non-intelligent strategies → public-set validation overestimates; hidden-set
draws remain the only ground truth.

## The exploitable insight: max-over-plays portfolio (v8 candidate)
The scorecard scores a game card as the **max over plays** (this is why Tufa's banking
graft exists). A CPU-only graph explorer costs ZERO GPU (the binding resource) and
historically clears level 1 on games the duck zeroes (g50t, m0r0). → Run a bounded
explorer play on each card alongside the duck's play: max(duck, explorer) ≥ duck strictly.
Budget cost ~1-4 min of the 165-min card budget; expected uplift ≈ explorer's score on
duck-zero games only (~+0.04-0.15 LB mean, more if hidden games have more duck-zeros).
Implementation surface already exists: `src/taaf-grafts` solver-wrapping pattern
(banking_solver adds plays to a card).
[07-14 NOTE: live cards allow ONE run per game ID and fresh plays only from WIN —
the cross-run version of this idea is dead (see LOG 07-14); only WIN-gated banking
and within-run mechanisms survive.]

---

# ADDENDUM 2026-07-14 — Forum + code-section sweep (post v8=0.00)

> Method: Kaggle CLI kernel list (dateRun + voteCount), pulled 9 kernels into scratchpad
> `recon0714/`, diffed the duck line, read the graft forks; forum threads via
> r.jina.ai proxy (Kaggle SPA blocks plain fetch; individual thread pages render, the
> list page does not — enumerate IDs via search engines).

## 1. Upstream duck line moved: v12→v14 flag timeline (thtennant, same share-fork bundle we run)
- v10 (07-11): {efficiency, retry_guard} — the "revert" we knew. 12 votes.
- v12 (07-12): + shortcircuit. 15 votes.
- v13 (07-13): + recovery.
- **v14 (07-14, today): {efficiency, retry_guard, shortcircuit, transfer(+banking implied)};
  comment says "recovery deliberately OFF"** — recovery lasted ONE day upstream.
- Read: the graft author now runs transfer+banking WITHOUT recovery. Our v5 (LB 1.20/1.31)
  runs recovery ON. His flags ≠ evidence of LB scores (his draws unknown), but "deliberately
  OFF" after one day suggests live evidence against recovery. → candidate A/B, never a blind swap.

## 2. Safety pack (kevin250304/arc3-duck-v9b-recovery-banking — Yin Li fork)
Two liftable ops patterns, both marked "safety pack" in cell 14:
- **Live rerun soft_end = start + 11h20m** (stock duck runs live with soft_end=None!):
  "so the solver drains and the shared scorecard closes before Kaggle's hard kill"
  (12h submission-rerun wall). Cheap insurance against end-of-run truncation.
- **Offline commit gate = 3 games + 1 dup-family game** (`external_game_id=f"{env}-dup"`,
  same arcade_spec → same transfer fingerprint family): Save&Run validates in ~1-2h
  instead of 9-10h AND exercises transfer publish→replay. Falls back to `[:4]` on any fault.

## 3. Fast-save pattern (maxingkong733/arc3-duck-dead-signature)
Cell 0 writes a dummy `submission.parquet` and every other cell is guarded by
`if _FAST_SAVE_COMPETITION_RERUN:` → **Save&Run completes in minutes; the solver runs
only in the real hidden rerun.** Breaks our "one 10h Save&Run per day" cadence limit —
but forfeits offline validation of that exact version. Safe usage for us: only for
configs already validated (competition_sim + offline) in a prior version; the deployed
bundle/datasets are identical, only cell text changes.

## 4. Dead-signature guard (same kernel) — concrete zero-games candidate
Monkey-patches `_HarnessGameSession.step_env`: key = (levels_completed, blake2b(full
board), action); after an action produced **no board change AND no reward 4× in the
exact same state**, the 5th attempt is refused with an error payload telling the model
"known ineffective action... choose a different action or hypothesis". Single-action
requests only (batches bypass); counter clears when the action works. Conservative
by design — the Gemma line found a BROAD veto suppresses identical interactive tiles;
exact-full-state conditioning avoids that. → Test offline against our 11 zero-games:
first measure how often the pathology (exact-state repeat loops) actually fires.

## 5. Gemma-4-31B reflection agent (ko0kip, 78 votes; = 2nd-place lineage, 0.79 public)
Different stack (official Agents framework + vLLM structured output, NOT TAAF). Policy
ideas with constants: reflection memory = markdown ≤1800 chars rewritten every 10
transitions (persisted per game); saliency-tiered fallback clicks (button-like first);
structural dead-click pruning DEADSIG_K=2, reset per level; FIRST_ACTION_DEADLINE 14min,
global 9h with 20min shutdown reserve, LLM request timeout 400s, MAX_HISTORY 12,
plan queue ≤4 actions. Below duck line on LB → mine for policies, don't switch stacks.

## 6. Hydra Scout (lucifer19, 11 votes) — the duck's env-var tuning surface, enumerated
Tunes the STOCK Tufa bundle purely via env: `LOCAL_ANALYZER_CONTEXT_WINDOW` 32768→49152,
concurrency 28→8, `LOCAL_ANALYZER_TEMPERATURE` 0.6→0.50, TOP_P 0.92, TOP_K 20,
`LOCAL_ANALYZER_ENABLE_THINKING=true`, `MULTIMODAL_CONTEXT=current_grid`,
`MULTIMODAL_UPSCALE=4`, tool timeout/yield 45s; hard watchdog = `asyncio.wait_for`
8h40m + 20min teardown reserve. **Caveat before copying: live = 55 games in a 12h wall;
8-way × ~2.2h/game ≈ 15h → doesn't fit.** A live-safe variant is ~16-20 concurrency at
40-48k context. This makes our "context compaction quality" lever testable as pure env
knobs (no code): fewer evictions per game at 40k+.

## 7. Forum facts (thread IDs where known)
- **Tufa writeup (717133) hard numbers:** best LB 1.21 — **a 1.30 draw was RETRACTED**;
  public-set 1.6 ± 0.4475 std; same-submission draws as low as 0.77. Confirms: our 1.31
  is already above their best counted draw; daily max-draw resubmits = correct strategy.
  Also verbatim: hand-crafted tools hurt the model, prompt engineering > tooling; models
  hallucinate classical-game priors and miss salient features.
- **Determinism (694153):** Greg Kamradt — games use stable seeds, no procedural
  randomness (one cosmetic exception: lf52 noise animation). Underwrites banking/transfer
  replay correctness.
- "Submit Error ~30min" thread (07-14): community fix = check `resource.setrlimit(RLIMIT_AS)`
  — an address-space rlimit kills vLLM early in reruns. Not our failure mode; know it exists.
- "[0.79 public] Open source code for Milestone 1" (Akhil Tolani): Gemma 4 31B QAT pruned
  vocab + LeWM/JEPA dynamics — active thread (last comment <1 day). Below our line.
- Milestone 2 = Sept 30 (final milestone; $37.5K pool per milestone-1 blog).

## RANKED CANDIDATE QUEUE (from this sweep)
1. **Ops, near-free:** adopt v9b safety pack — live soft_end 11h20m cap (+ competition_sim
   validation) and the 3+dup fast offline commit gate for Save&Run validation runs.
2. **Ops, cadence:** fast-save pattern for pre-validated configs (validate in
   competition_sim/offline on version N, fast-save as version N+1, submit same day).
3. **Score, zero-games:** dead-signature guard graft — measure loop pathology on our 11
   zeros offline first; ship only if it fires and flips ≥1 game.
4. **Score, A/B:** recovery-OFF variant (upstream v14 signal) vs our v5 — offline +
   competition_sim; only replaces v5 if it wins over ≥2 draws.
5. **Score, env-only:** context 32k→40-48k with concurrency 20→16 (live-throughput math
   first: 55 games must fit 11h saturated) — the compaction lever without code.
