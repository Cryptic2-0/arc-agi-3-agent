# LOG.md — Append-Only Log

> Everything: what / why / result / time. Never edit past entries; only append.
> Readers: anyone reconstructing how we got here. (Layer 1 of 3.)

Format per entry:
```
## YYYY-MM-DD HH:MM — <short title>
- **What:** ...
- **Why:** ...
- **Result:** ...
- **Next:** ...
```

---

## 2026-06-23 — Project scaffolded
- **What:** Created three-layer memory (PROJECT.md / LOG.md / REPORT.md) + PLAN.md (10-step gated plan) + EXPORT_RULES.md (playbook copy) in empty ARC-AGI dir.
- **Why:** Apply the export playbook to this project; start from corrected understanding instead of relearning (Rule 13, step C).
- **Result:** Structure in place. Objective intentionally left as TODO (user: "just scaffold the structure"). No git, no code yet.
- **Next:** When work begins — run PLAN step 1 (define objective exactly), then step 2 (map/measure binding constraint), then step 3 (recon prior art) BEFORE building.

## 2026-06-23 — PLAN step 1 done: objective defined
- **What:** User pasted official ARC-AGI-3 (Kaggle 2026) spec. Pinned THE number = total 0–100% score:
  level = `min(human_actions/agent_actions,1.0)²`, game = level-index-weighted avg, total = mean over games.
  Eval = 110 unseen private games (55 public LB / 55 private LB); 25 public games local. Grounded
  platform meta + agent contract in repo code (agent.py, random_agent.py, README changelog). Wrote
  objective+meta into PROJECT.md & REPORT.md (cited); constraint hypothesis (in-context skill
  acquisition) marked UNMEASURED.
- **Why:** Step 1 gate = "state the number and how it's computed" — now satisfiable.
- **Result:** PLAN step 1 ✅, step 2 🟡. GATE met.
- **Next:** Step 2 — run random baseline on a public game (e.g. `ls20`) to observe the failure mode
  (never-solves vs solves-inefficiently); needs `ARC_API_KEY` + `uv`. Then step 3 recon prior art.

## 2026-06-23 — First baseline: random agent, ls20, OFFLINE (PLAN steps 4 + 5)
- **What:** Stood up the harness and ran the random agent on `ls20` locally.
  - Env: no `uv`/deps initially → `pip install uv`; `uv` fetched CPython 3.12.13 + 86 pkgs into `.venv`.
  - Online attempt FAILED: user-supplied key `KGAT_…` → `three.arcprize.org/api/games` returns **401
    unauthorized** (wrong key type — that's a Kaggle-style token, not an arcprize key).
  - Pivoted to OFFLINE: set `OPERATION_MODE=offline` + `ENVIRONMENTS_DIR=<abs path to environment_files>`
    in `.env`. `main.py` is hardwired to the online `/api/games`, so wrote `run_offline.py` (builds game
    list from locally-scanned `metadata.json`, drives `Swarm` directly). No API, no quota.
- **Why:** Get one real score through the WHOLE pipeline (step 4) and stand up the fast local feedback
  loop (step 5) before building any solver.
- **Result:** ✅ Pipeline runs. Random on `ls20`: **score 0.0, levels_completed 0/7, 81 actions**,
  `level_scores=[0×7]`. ~0.65 s for 80 actions (124 fps). Local scorecard emits `level_scores` +
  `level_baseline_actions=[22,123,73,84,96,192,186]` — i.e. the exact competition metric, computed
  offline. **The local scorer IS the true metric, not a proxy.** Binding-constraint datapoint: random
  clears 0 levels → the gate is *completion / skill acquisition*, not efficiency (squaring is moot
  until level 1 is solvable).
- **Next:** Step 3 — recon prior art (ARC-AGI-3 forum / winning agents / TTT-style approaches). Then
  step 7/8 — first real solver hypotheses. Consider raising `MAX_ACTIONS` (default 80) for games whose
  human baseline exceeds it (ls20 levels need up to 192 human actions). Get a real arcprize key only
  when an online/leaderboard submission is needed.

## 2026-06-23 — Recon prior art (PLAN step 3) → build decision
- **What:** Web recon on ARC-AGI-3 approaches. Wrote [docs/recon.md](docs/recon.md) with cited methods + scores.
- **Why:** Don't re-derive published answers; pick reuse-vs-build before coding (Rule 5/6).
- **Result:** Clear picture. **Frontier LLMs score ~0.2–0.4%** (Gemini 3.1 Pro 0.37%, Claude Opus 4.6
  0.2%) → naive LLM agent ≈ 0. **Best preview agent 12.58%** (StochasticGoose, CNN+RL predicting
  frame-changing actions; 18 levels but 255k actions). Other winners: Blind Squirrel "Smart Random +
  Rules" (state graph + prune non-productive actions) 6.71%; Fluxonian DSL+LLM 8.04%; frame-graph 3.64%.
  **Graph-Based Exploration paper (arxiv 2512.24156):** frame→connected-component segmentation + status-bar
  mask + hash = state id; transition graph; hierarchical exploration (untested action → shortest-path to
  frontier state → raise priority); ACTION6 pixels stratified into 5 interactivity tiers. Scored **19
  levels vs random 6 vs LLM+DSL 5** at a 4000-action budget. GATE met (≥3 cited approaches, decision made).
- **Decision:** Build a **no-LLM graph-based exploration agent** (frame-hash state graph + action-effect
  learning + frontier search; priority pixels for ACTION6). Reuse the harness, skip the LLM templates.
- **Next:** Steps 7–8 — implement v1 agent as `agents/templates/`; raise `MAX_ACTIONS`; run via
  `run_offline.py` and compare to random's 0/7 on ls20. Riskiest unknown first: can it clear ls20 L1 at all?

## 2026-06-24 — v1 GraphExplorer built, measured, + first Kaggle submission pushed (steps 7–8, 6)
- **What:** Built no-LLM graph-exploration agent and shipped it through the real Kaggle pipeline.
  - Agent: `agents/templates/graph_explorer.py` (`GraphExplorer`) — frame-hash state graph,
    action-effect learning (prune no-ops), BFS-to-frontier, ACTION6 priority pixels. Registered via
    `agents/__init__.py`. `MAX_ACTIONS` 80→2000 (local) / 600 (Kaggle).
  - Measured offline on all 25 public games: **3/183 levels** — sp80 2/6, ft09 1/6 (random = 0).
    ls20 still 0 (hard alignment puzzle; not hash fragmentation — ACTION1 cycles 6 clean states).
  - **KGAT_ token is the Kaggle access token** (not arcprize) — that's why it 401'd online earlier.
  - Cloned `ARC-AGI-3-Kaggle-Starter`, ported agent → `agent/my_agent.py` (`MyAgent`), set
    `ACCELERATOR=cpu`, token → `.kaggle/access_token`. No `make` on Windows → ran scripts directly:
    `python scripts/build_notebook.py`; `KAGGLE_API_TOKEN=$(cat .kaggle/access_token) python -m kaggle kernels push -p notebooks/`.
  - Username auto-detected from existing kernels: **soumyacryptic**.
- **Result:** **Phase A pushed + COMPLETE.** Kernel: https://www.kaggle.com/code/soumyacryptic/arc-prize-2026-arc-agi-3-starter
  `submission.parquet` produced; log clean (only benign pip-resolver warning). NOT yet on leaderboard —
  Phase B (the actual hidden-game scoring) needs the manual **Submit to Competition** click (1 of 5/day).
- **Next:** User clicks Submit to Competition for the leaderboard score. Then iterate: ACTION6/click
  games are the weak spot (ACTION6 treated as one action — should track tried pixel-buckets per state).

## 2026-06-24 — First leaderboard score landed: 0.17 (public)
- **What:** User submitted Phase B; competition rerun scored the GraphExplorer kernel.
- **Result:** **publicScore = 0.17** (private hidden), submission `53990547`, status COMPLETE. Non-zero →
  full pipeline validated against the HIDDEN games, not just local. ~0.17 on the 0–100 scale ≈ frontier-LLM
  tier (Gemini/GPT/Grok 0.2–0.4%); best preview agent was 12.58% — big headroom.
- **Why it's low:** v1 only clears a couple game types (sp80/ft09 locally); most games (esp. click/ACTION6)
  unsolved. THE number is now real and measured — this is the baseline to beat.
- **Next:** improve agent → re-push. Highest-leverage fix = ACTION6/click games (7 of 25): treat ACTION6
  as many distinct targets (track tried pixel-buckets per state), not one action.

## 2026-06-24 — v2 (ACTION6 click-target expansion) built, measured, pushed (kernel v2)
- **What:** Generalized the agent's "move" space: ACTION6 is no longer one action — each non-background
  colour-segment's representative cell is its own move ("6",(x,y)), tracked per-state like simple actions
  (small-segments-first, capped at 24, ACTION6 pruned if globally dead after 12 no-ops). Mirrored into both
  `graph_explorer.py` (GraphExplorer) and the Kaggle `agent/my_agent.py` (MyAgent).
- **Result (offline, 25 games):** **7/183 levels across 6 games** — vc33 2/7, ar25 1/8, lf52 1/10, m0r0 1/6,
  r11l 1/6, sp80 1/6. vs v1's **3/183 across 2** → 2.3× levels, 3× games. Gained 5 click/keyboard_click games.
  REGRESSION: sp80 2→1, ft09 1→0 — adding many ACTION6 targets crowds out simple-action exploration on
  keyboard-leaning games (v3 fix: balance simple vs click move budgets, or down-weight ACTION6 targets).
- **Shipped:** `python scripts/build_notebook.py` + `kaggle kernels push` → **kernel version 2, Phase A COMPLETE.**
  User submitting Phase B for the v2 leaderboard score (v1 was 0.17).
- **Next:** record v2 LB score when it lands; v3 = fix the sp80/ft09 regression (don't let ACTION6 starve
  simple-action exploration); consider per-game move-budget balancing.

## 2026-06-24 — v2 submitted to competition via CLI (no manual UI click needed)
- **What:** Corrected earlier belief that Phase B requires a manual "Submit to Competition" click. The
  Kaggle CLI submits code-comp kernels directly:
  `python -m kaggle competitions submit arc-prize-2026-arc-agi-3 -k soumyacryptic/arc-prize-2026-arc-agi-3-starter -v 2 -f submission.parquet -m "..."`
- **Result:** v2 submission entered — ref `54007751`, status PENDING (Phase B rerun). v1 still 0.17.
  Polling for the v2 score in background.
- **Next:** record v2 publicScore; if it beats 0.17, v3 (fix sp80/ft09 regression) for a 3rd submission.

## 2026-06-24 — v2 leaderboard score: 0.23 (up from v1 0.17)
- **What:** v2 Phase B rerun completed. **publicScore = 0.23** (sub `54007751`), vs v1 0.17 (+35% rel).
- **Why it worked:** ACTION6 click-target expansion (per-object moves) generalized to the hidden games,
  matching the offline gain (7/183 vs 3/183). Confirms the offline scorer predicts LB direction.
- **Standing:** v1 0.17 → v2 0.23. Best preview agent = 12.58% (far). Trajectory positive.
- **Next (v3):** fix the sp80/ft09 regression (ACTION6 targets starve simple-action exploration — e.g.
  interleave simple-action and click exploration, or cap ACTION6 share of the move budget per state).

## 2026-06-24 — v3 (simple-actions-first) REGRESSED offline → reverted, NOT pushed
- **What:** Tried "try untested simple actions before ACTION6 click targets per state" to fix the
  sp80/ft09 regression.
- **Result:** **5/183 (5 games)** vs v2's 7/183 (6 games) — WORSE. vc33 2→1, lost ar25/lf52/m0r0,
  gained cd82/su15, sp80 still 1 (not restored), ft09 still 0. Reverted both `graph_explorer.py` and
  `agent/my_agent.py` to v2. Did NOT push → offline scorer saved a daily submission. v2 (0.23) stays best.
- **Why it backfired:** forcing all simple actions first starved click-game progress more than it helped
  keyboard games. The "simple starved" hypothesis was wrong/overcorrected.
- **MEASUREMENT CONFOUND (important):** the 25 games run as parallel THREADS sharing Python's global
  `random` (each agent calls `random.seed(0)` but they interleave) → offline sweeps are **non-deterministic**.
  Part of the v2/v3 delta is noise. FIX before further A/B: give each agent its own `random.Random(seed)`
  instead of the module-global, and/or run single-game comparisons. Until then, treat small deltas as noise.
- **Next:** (1) per-instance RNG for trustworthy A/B; (2) then root-cause sp80/ft09 properly (likely the
  600/2000 action budget eaten by 24 click targets/state on mixed games), not a blanket simple-first rule.

## 2026-06-24 — RNG fix → clean baseline: deterministic v2 = 10/183 (8 games)
- **What:** Replaced module-global `random.*` with per-instance `random.Random(0)` in both
  `graph_explorer.py` and `agent/my_agent.py` (agents run as parallel threads → global RNG was
  non-deterministic). Re-ran the full sweep deterministically.
- **Result:** **10/183 across 8 games** — r11l 2/6, vc33 2/7, ar25 1/8, g50t 1/7, lf52 1/10, m0r0 1/6,
  sp80 1/6, su15 1/9. The earlier noisy runs UNDERCOUNTED (v1 3, v2 7, v3 5 were all noise-corrupted).
  So **v3's "regression" was largely phantom**, and the real agent is stronger than the 0.23 LB suggested.
- **Key judgment:** deterministic RNG fixes MEASUREMENT, not POLICY — it's the same agent already pushed
  (0.23). NOT worth a fresh submission alone (would just be a different fixed trajectory). Use 10/183 as the
  trustworthy A/B reference; only push a change that beats it deterministically.
- **Observation:** 6 of 8 games stuck at exactly 1 level → either action budget exhausted on L1, or the
  agent can't solve L2 (needs strategy). Next: probe by raising MAX_ACTIONS to see if depth increases.

## 2026-06-24 — Budget probe: MORE ACTIONS DON'T HELP → the lever is strategy, not budget
- **What:** Ran the 6 stuck games (ar25,g50t,lf52,m0r0,sp80,su15) at MAX_ACTIONS=6000 (vs 2000).
- **Result:** total 5 levels @6000 vs 6 @2000 — flat (diff = noise). **Budget is NOT binding.** Games
  stall at level 1 because pure exploration can't *solve* L2+, which needs goal-directed reasoning.
  Reverted MAX_ACTIONS to 2000.
- **Also found:** residual nondeterminism — `max()` over a `set` of str/tuple moves depends on Python
  set-iteration order (PYTHONHASHSEED), so the RNG tiebreak still varies run-to-run. The per-instance
  RNG fix was PARTIAL. True determinism needs sorted iteration or PYTHONHASHSEED=0.
- **Conclusion / direction:** tweaks (simple-first, budget) won't move the needle. Real gains need a
  smarter agent: goal acquisition / reward from `levels_completed` increases / frame-change-prediction
  (cf. the 12.58% CNN+RL winner) — a bigger build. Current best LB = v2 0.23; pipeline solid. Decision
  point for the user: invest in the larger goal-seeking upgrade, or hold at 0.23.

## 2026-06-25 — v4: reward-from-level-ups + full determinism (sorted tiebreak). Clean A/B.
- **What:** (a) reward signal — when a move increases `levels_completed`, boost that move-type's selection
  priority (so the agent reuses what makes progress). (b) determinism fix — `_best()` sorts the move set by
  `repr` before the rng tiebreak, removing PYTHONHASHSEED/set-iteration dependence. User chose directions
  1 (goal-seeking) + 2 (RL) — this is direction 1.
- **A/B (deterministic, isolated):** reward-ON **7/183** (r11l reaches L2) vs reward-OFF **6/183** → reward
  is a small genuine positive. KEEP it.
- **Big lesson:** the deterministic truth is ~6-7/183; the earlier **"10/183" was a lucky hash-seed
  trajectory (noise)**. Offline metric is HIGH-VARIANCE (6→10 across trajectories) — single sweeps aren't
  precise comparators; treat deltas <~3 levels as noise. The pushed 0.23 was itself one noisy trajectory.
- **Next:** push v4 (cleanest version: deterministic + reward) as a consolidation submission; expect ~0.23±
  (offline variance high). Then direction 2 = the RL frame-change predictor (the real ceiling-raiser, big build).

## 2026-06-25 — v4 pushed (kernel v3) but BLOCKED: daily submission limit = 1/day (not 5)
- **What:** Pushed v4 (kernel version 3, Phase A COMPLETE). Tried to submit → 400.
- **Root cause (real error body via Python API):** "Your team has used its daily Submission allowance (1)
  today, please try again tomorrow UTC." **The competition's daily LB-submission limit is 1, NOT 5** (the
  starter README's "5/day" is wrong for this comp). Resets at UTC midnight.
- **Implication:** every submission must count. Don't burn the 1/day on a marginal change. v4 is only
  ~0.23± vs v2's 0.23 (offline variance high), so submitting it has low expected value.
- **Decision pending (user):** (a) auto-submit v4 after UTC reset to test it, or (b) HOLD the daily
  submission for a genuinely better agent (direction 2, the RL build). Recommend (b).
- **Note:** Phase A push is unlimited + free; only `competitions submit` (Phase B) consumes the 1/day.

## 2026-06-25 — Direction 2 scoped (docs/rl_design.md) + v5 (contextual predictor) = wash → PLATEAU
- **Scoping:** wrote [docs/rl_design.md](docs/rl_design.md). Key constraint: eval games are NOVEL/hidden →
  no pretraining transfers → a literal bundled CNN won't work; the winner's "CNN+RL" must be ONLINE per-game.
  So the feasible build = lightweight ONLINE contextual change/progress predictor, not a GPU CNN.
- **v5:** generalized v4's per-action-type effect into per-(action, frame-context) with Thompson-sampled
  P(frame-change). Frame-context feature = (distinct-colour-count, non-bg-fraction bucket).
- **Result:** **7/183, 6 games** — SAME total as v4, different mix (gained su15/tr87, lost g50t/sp80). A
  LATERAL move within noise. The coarse context feature doesn't predict useful change.
- **PLATEAU CONCLUSION:** tried reward (v4=7), simple-first (v3=5 worse), budget (no help), contextual
  predictor (v5=7). Exploration agent is stuck ~6–8/183 ≈ 0.23 LB; metric variance ±2–3 means these are
  noise-indistinguishable. Micro-tweaks are exhausted.
- **Remaining real lever:** OBJECT-RELATIVE ACTION6 features (v7 in the design doc) — 20/25 games are click
  games, and v5 lumps all clicks together (key=6). Featurizing click targets by their own colour/size so
  "clicking small bright things changes the frame" generalizes — the one untried high-value bet.
- **Discipline note:** with 1/day LB + high offline variance, must validate any candidate over MULTIPLE
  SEEDS (mean, not one sweep) before spending the submission. Best staged = v4≈v5 (7/183, ≈0.23).

## 2026-06-25 — v4 LB score: 0.24 (new best) + published to GitHub
- **v4 submitted** (kernel v3, sub `54035711`) → **publicScore 0.24** (v2 was 0.23). New best, marginal +0.01
  (within noise, but technically ahead). Trajectory: v1 0.17 → v2 0.23 → v4 0.24.
- **GitHub:** published the project → **https://github.com/Cryptic2-0/arc-agi-3-agent** (private, gh user
  `Cryptic2-0`). Clean repo at ARC-AGI root: docs + `agent/{graph_explorer,my_agent,run_offline}.py`. Excludes
  the two arcprize clones, wheels, venvs, `.env`, `.kaggle/`. Token verified NOT committed.
- **v7 (object-relative ACTION6 features):** implemented; click targets now carry (colour, size-bucket) and
  the change-predictor keys clicks by those features so the agent learns WHICH click-type is productive.
  Sweep keeps dying on session teardown (slower run); result still pending — running foreground.
- **Today's 1/day submission USED on v4.** v7 (if it wins) → tomorrow.

## 2026-06-25 — v7 = 8/183 (best yet) → submitting
- **v7 result (deterministic):** **8/183, 6 games** — r11l 2, vc33 2, cd82 1, lf52 1, sp80 1, tr87 1. Beats
  v4=7. Object-relative click features pushed vc33 to 2 levels. Best deterministic result so far.
- **Mirrored v7 → Kaggle `my_agent.py`** (copied graph_explorer verbatim; only class name + import +
  MAX_ACTIONS=600 differ). Pushed **kernel version 4**, Phase A polling. User confirmed a submission slot
  is free today → submitting v7 (version 4).
- **Note:** sweeps kept dying on session teardown; final v7 number came from a foreground run that survived.

## 2026-07-07 — v7 LB CRASHED (0.06); milestone-1 winners open-sourced; PIVOT to duck harness
- **What:** Session resumed after 11-day gap. Checked submissions: **v7 scored 0.06 on LB**
  (sub `54087945`, 2026-06-26) — catastrophic vs v4's 0.24, despite v7 being the best offline
  (8/183). Likely kernel crash/timeout on hidden games — never diagnosed; moot now (see pivot).
  ~10 daily submission slots went unused since 6/26.
- **LB state:** exploded since milestone 1 (June 30). Top = **1.56** (Mathurin Ache); top-20 all
  ≥1.30. Our 0.24 is far off the pace. Cause: milestone-1 winner **open-sourced** (required by
  rules) and everyone forked it — a verbatim fork (`caoyupeng/1-21-from-great-team-tufa-labs`)
  scores **1.21**.
- **Winner (Tufa Labs "duck harness", Jeroen Cottaar et al., 1.21):** LLM agent after all —
  but LOCAL: Qwen3.6-27B-FP8 on vLLM, Kaggle RTX Pro 6000 (96GB). Agent = "duck": gets ASCII
  grid + connected-component segmentation (raw grid hidden), a fresh Python sandbox per call,
  calls `action(...)` from code; keeps a persistent "world model" note across turns; 64k context
  with oldest-message eviction; 28 concurrent games, 7920s/game cap. Writeup:
  kaggle discussion 717133. Key insights from writeup: hand-crafted tools HURT (let the model
  write its own analysis code); prompt engineering against hallucination mattered; better base
  model + multimodal drove gains; variance is large (±0.4 across runs).
- **Action taken:** pulled winner source (dataset `jeroencottaar/taaf-kaggle-source-share` →
  `external/taaf_source/`), pulled the 1.21 notebook, pushed a verbatim private fork:
  **`soumyacryptic/taaf-duck-harness-fork` v1** (3 datasets attached, machine_shape
  NvidiaRtxPro6000, no internet). Status QUEUED. Save&Run plays the 25 offline games first
  (hours of GPU).
- **Next:** when version 1 completes → submit: `kaggle competitions submit arc-prize-2026-arc-agi-3
  -k soumyacryptic/taaf-duck-harness-fork -v 1 -f submission.parquet` (today's slot FREE, last
  used 6/26). Expected ~1.2±0.4 vs current 0.24. Then improve: prompts/context-compaction/model
  swap via the customization hook; consider graph-explorer as cheap fallback layer.

## 2026-07-07 (later) — fork v1 scored LB 1.07; v2 (game-over fix) in flight
- **Result:** sub `54414740` (verbatim duck fork) = **1.07 public LB** (offline mean 1.11 on the
  25 public games; 0 games fully won, 14/25 scored 0). 4.5x our GraphExplorer best (0.24).
  Consistent with the 1.21 fork ± the authors' stated ±0.4 variance.
- **Failure-mode analysis (v1 transcripts):** biggest visible pathology = **post-game-over
  paralysis**. The harness auto-resets the level after GAME_OVER (solver.py:276) but the next
  prompt only says "The game is over." (tool_agent.py:1209-1210). Model writes "game is over,
  stop acting" into its persistent world-model note and refuses to act for the rest of the run:
  ls20 wasted 20/61 turns, ft09 14/66, sc25/tn36/cn04 also affected. Each turn ≈ 80-130s of
  shared GPU → up to ~1/3 of a game's budget burned idle.
- **Other findings:** deployed analyzer context = **32k** (not 64k; vLLM serves 64k max_model_len);
  concurrency 28, 7920s/game cap, unlimited tool steps, temp 0.6, prefix caching on. All games
  run concurrently for the full window → binding constraint = aggregate GPU decode (~222 tok/s
  split 25-28 ways ≈ 9 tok/s/game, ~70k tokens/game). Request errors: 1/game (terminal timeout
  at budget end) — not systemic.
- **v2 shipped (kernel version 2):** customization-hook patches only (no source-dataset fork):
  (1) user-prompt line "The game is over." → explicit "environment ALREADY auto-reset; GAME_OVER
  is never permanent; do NOT stop playing / do NOT write game-over into world model";
  (2) system-prompt "Game-over handling" addendum (auto-reset semantics + treat each death as
  information, change plan);
  (3) `bm.n_passes = 3` offline only (rerun branch forces 1) → 75 runs for lower-variance eval,
  ~7h fits the ~8.7h soft deadline.
- **Decision rule for tomorrow's slot:** submit v2 only if 3-pass mean ≥ v1's 1.11 AND the
  game-over-affected games (ls20/ft09/sc25/cn04/m0r0/r11l) don't regress. Monitor:
  `external/my_duck_fork/monitor_v2.sh` (poll only, no auto-submit).

## 2026-07-08 — v2 offline validated (paralysis fix works); SUBMITTED (sub 54446049)
- **v2 3-pass offline (75 runs, 6h36m):** mean 1.01, median **0.17** (v1: 0.00), **16/25 games
  scoring >0** (v1: 11). Mean vs v1''s single-pass 1.11 = flat within ±0.4 variance; v1''s edge
  was two jackpot passes (re86 8.33, sp80 4.76) that regressed toward true means.
- **Fix target validated:** game-over set improved, zero regressions there. r11l 0→**3.80**
  (cleared L1 every pass), ka59 0→1.12, s5i5 0→0.69, wa30 0→0.35, ls20 0→0.04, m0r0 0→0.02.
  Transcript check: "You have not acted yet" refusal turns = **0** across ls20/ft09/sc25/r11l
  all passes (v1: ls20=20, ft09=14). Model now retries after every death.
- **Submitted v2** (kernel version 2, sub `54446049`, 2026-07-08 01:47 UTC). Rationale: LB keeps
  best score → downside bounded at 1.07; breadth+median up; fix verified. PENDING.
- **Next:** check publicScore when resolved. Next levers (PROJECT.md): dc22-style indecision,
  context compaction, tool-output budget, temperature, base-model swap.
