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

## 2026-07-09 — v2 LB = 0.57 (v1's 1.07 stands); v3 = thinking-off + act-bias, in flight
- **v2 publicScore = 0.57** (sub 54446049) vs v1's 1.07. LB keeps best → standing unchanged at
  1.07. Read: offline said v2 ≈ v1 on mean (1.01 vs 1.11, 75 runs vs 1 pass) with better median;
  a 1-pass LB draw at ±0.4 stated variance can land 0.57 without the fix being net-negative.
  v1's 1.07 itself is one draw — true mean likely ~0.8-1.0 for both. Conclusion: prompt-margin
  tweaks won't reliably beat 1.07; need a lever that shifts expected score, not variance.
- **v2 transcript profiling (39/75 transcripts):** ~64 turns/game/pass, avg action batch 1-2,
  **thinking ≈ 250K chars/game/pass ≈ ~85% of the ~70k generated-token budget** → only ~150 env
  actions/game. Completion gates score; action throughput is the binding constraint, and it's
  being spent on chain-of-thought. Yield=60s is a max-turn-duration (not a floor) → nothing
  caps faster turns.
- **v3 shipped (kernel version 3, pushed 2026-07-09 10:23 UTC):** hook-cell-only again:
  (1) `_ta._LOCAL_ANALYZER_ENABLE_THINKING = False` (Qwen3 no-think; read at request time in
  `_chat_completion`, tool_agent.py:1297; smoke test in kaggle.py already exercises
  enable_thinking=False against this vLLM config);
  (2) no-think recommended sampling: temp 0.6→0.7, top_p 0.95→0.8;
  (3) system addendum "Action-throughput policy": 2-4 sentence replies, act every turn,
  batched probes while mechanics unknown (batches auto-stop at level change/game-over),
  exact planned sequence once confident (no padding — efficiency metric);
  (4) v2 game-over fix kept verbatim; (5) `bm.n_passes=3` offline, rerun forces 1.
  Expected effect: 3-5× action throughput; risk: no-think Qwen reasons worse per turn.
- **Decision rule:** submit v3 only if 3-pass mean clearly > 1.01 (target ≥1.2) or median/breadth
  jump without mean loss. Monitor: `monitor_v2.sh` (bg). Today's submit slot unused → can submit
  tonight if run validates (~17:30 UTC ETA).

## 2026-07-09 (later) — v3 offline WORSE (0.86); thinking-off rejected; v4 (thinking on + act-bias) in flight
- **v3 3-pass offline (75 runs, 6h36m):** mean **0.86** / median **0.08** vs v2's 1.01 / 0.17.
  Decision rule failed → v3 NOT submitted; v1's 1.07 still stands.
- **Why no-think lost:** actions rose only **1.48×** (20103 vs 13564), not the predicted 3-5×.
  Generated tok/s DROPPED 224→178 — with short replies, wallclock overhead (sandbox exec, env
  stepping, per-request overhead) becomes the binder, not GPU decode. Meanwhile per-turn
  reasoning got worse: planning-gated games collapsed (ka59 1.12→0.16, lp85 2.78→1.39,
  su15 2.22→1.02, s5i5 0.69→0, wa30 0.35→0).
- **What no-think won (keep for later):** exploration-gated games jumped — ar25 0.72→**3.33**,
  ls20 0.04→**1.09**, ft09 0→0.72, cd82 0→0.36, cn04 0→0.58 (first-ever nonzero for cd82/cn04);
  zeros 8→6, 19/25 games scoring. Split suggests the act-bias/batching prompts (bundled in v3)
  drive breadth, thinking drives depth → want both.
- **v4 shipped (kernel version 4, pushed 2026-07-09 17:38 UTC):** thinking back ON, default
  sampling restored (temp 0.6/top_p 0.95); act-bias/batching addendum KEPT (+ "keep private
  reasoning to a few hundred words" line); v2 game-over fix kept. `bm.n_passes=2` (not 3):
  fits GPU-quota headroom AND finishes ~22:45 UTC → today's unused submit slot still usable
  if it validates. v4 vs v2 isolates the act-bias addendum under thinking.
- **Decision rule:** submit v4 tonight if 2-pass mean > 1.01 or breadth/median up without mean
  loss; else hold 1.07 and design v5 (candidates: per-turn output cap ~3k to cut thinking tail,
  partial thinking, compaction quality).

## 2026-07-10 — v4 offline BEST (1.35/0.30, 20 of 25 scoring); SUBMITTED (sub 54515519)
- **v4 2-pass offline (50 runs, 4h24m):** mean **1.35** / median **0.30** / **20/25 games
  scoring** — best offline result of the fork line (v2: 1.01/0.17/17; v1: 1.11/0.00/11).
  tok/s back to 235 (GPU decode binds again with thinking on); actions/game 181→218 (+20%).
- **Read:** act-bias/batching addendum under thinking = the win. Depth kept (ka59 1.12→3.24,
  tu93 4.11, re86 2.37) AND breadth gained (ft09 0→2.12, cd82 0→1.85, sc25 0→**1.17** first
  nonzero ever, ls20 0.04→0.96; zeros 8→5). Regressions minor: wa30 0.35→0, s5i5 0.69→0.14,
  sp80 0.38→0.17.
- **Note:** 07-09 slot expired unused (v4 finished 22:11 UTC but session was idle overnight;
  submitted on the 07-10 slot at 04:25 UTC instead — no loss, slots don't accumulate).
- **Submitted v4** (kernel version 4, sub `54515519`, PENDING). Downside bounded at 1.07
  (LB keeps best). Caveat: 2-pass mean, noisier than 3-pass; and v2 taught us offline≈LB
  correlation is loose (1.01 offline → 0.57 LB draw).
- **Next:** check publicScore when resolved. Remaining zeros dc22/g50t/sk48/tr87/wa30 = next
  study targets (sk48 721 actions/0 levels + wa30 578/0 = flailing, dc22 94 = indecision).
  Other levers: per-turn output cap (~3k) to cut thinking tail, compaction quality, model swap.

## 2026-07-10 (later) — v4 LB = 0.78; offline-LB inversion 2-for-2; pivot to recon before more prompt tweaks
- **Sub 54515519 resolved: publicScore 0.78.** Below v1 verbatim's 1.07. Best stays 1.07.
- **Pattern:** v2 offline 1.01 → LB 0.57; v4 offline 1.35 → LB 0.78; v1 offline 1.11 → LB 1.07.
  Both prompt-mod versions beat verbatim offline and lost on LB. Hypotheses: (a) prompt mods
  overfit 25 public games / hurt hidden 55; (b) both draws unlucky at ±0.4 variance. n=2 can't
  separate — but expected value of further prompt-only tweaks is now questionable.
- **Decision: stop stacking prompt tweaks blind. Recon top forks (1.30-1.56) for their deltas,
  diagnose the inversion, then design v5 around a structural lever, not prompt margin.**

## 2026-07-11 — Recon: LB = max over noisy draws; Tufa graft line found (CC0); v5 = graft adoption
- **LB structure decoded:** top public kernel by score-sort = `rokaiyasomapti/taaf-duck-harness-kaggle-share-resubmission`
  = VERBATIM readable duck harness, empty hook, 14 votes. LB tie-clusters (1.56x3, 1.46x3,
  1.44x3, 1.33/1.32...) = many teams resubmitting the same verbatim notebook daily; Kaggle LB
  keeps each team's max draw. Top 1.56 ~= max of ~10 draws at mean~1.1-1.2, sd~0.25.
  **Implication 1: submit EVERY day — an unused slot is a wasted free max-draw.**
  **Implication 2: raise the draw mean structurally; prompt-margin tweaks don't move it.**
- **Tufa's own post-milestone dev line found (CC0):** `thtennant/arc3-duck-v7` kernel +
  `thtennant/taaf-kaggle-source-share-fork` dataset = readable share bundle + `src/taaf-grafts`
  (11 modules, ~140KB, updated 07-08). Cell-12 composite installer, all flags default-off,
  every graft fail-to-stock guarded. Flags: `banking` (replay pruned winning trace on a fresh
  play of same card — score is MAX over plays — direct attack on quadratic efficiency term),
  `transfer` (hidden runs are clone families; first clone publishes pruned per-level actions
  to a process-global store, siblings replay = skip cold starts; degrades to no-op on
  non-clone sets), `recovery` (R1 clear-history refresh on GAME_OVER spirals, R2 bounded
  scripted probe on lock-in, R3 cross-level notes handoff — built from m0r0/sk48 forensics =
  exactly our zero-game failure modes), `shortcircuit` (skip provably-no-op repeated batch
  actions; monotonically non-decreasing), `retry_guard` (bounded retry + vLLM health probe),
  `efficiency` (report-only per-turn budget note in the user prompt).
- **Bundle compat:** share-fork dataset = share bundle + grafts ONLY (file-list diff clean).
  Our kernel's bundle (`jeroencottaar/taaf-kaggle-source`, the original 1.21 line) DIFFERS
  from the share bundle (tool_agent.py 98KB vs 89KB, runtime_state 2x) → grafts must run on
  the share bundle they were written for. v5 therefore adopts thtennant's whole stack.
- **v5 design:** our kernel slug, notebook = v7 copy with (a) cell 12 flags
  {banking, transfer, shortcircuit, recovery, retry_guard} ON / efficiency OFF (prompts stay
  verbatim — our prompt mods are 2-for-2 LB losers), (b) run cell offline branch = ALL 25
  games + one dup of games[0] (exercises transfer publish/replay) instead of v7's [:4] commit
  gate, (c) n_passes 2 interactive / 1 rerun, (d) keep v7's 11h20m rerun soft-end safety cap,
  (e) docker image + dataset sources = v7's pins. GPU quota 9.5h free, run ~5h. Decision
  rule: submit on 07-11 slot if no crash + graft banners print + 25-game mean >= ~1.0.

## 2026-07-11 (later) — v4 zero-game forensics: all end on wall-budget timeout at level 1
- All five zero games (dc22/g50t/sk48/tr87/wa30) end with `request_error: Read timed out`
  against local vLLM — the 7920s/game budget expiring mid-request (timeout clamp shrinks:
  353s→136s→43s). No crashes, no give-ups: full budget spent without clearing level 1.
- Profiles: wa30 837 actions/0 deaths = deathless flailing (recovery R2 probe case);
  sk48 447 actions/5 game-overs = death loop (R1 refresh case); dc22 52 actions in 21
  mega-turns = analysis paralysis; g50t 214/tr87 235 = mid flail. v5's recovery graft was
  built from exactly these failure modes (its docstring cites sk48/m0r0) → no extra prompt
  work; measure recovery's effect in the v5 offline run.

## 2026-07-11 (later) — v5 offline 1.60/0.96 BEST; submitted (sub 54561696)
- **v5 offline (26 games incl. sk48-dup, 2 passes, 4h25m): mean 1.60 / median 0.96 / 17-of-25
  scoring.** Best of line (v4 1.35/0.30, v2 1.01/0.17, v1 1.11/0.00). 25-game mean ~1.66
  (dup scored 0, drags the 26-game mean).
- **Graft evidence:** banner `TAAF_GRAFTS FEATURES={banking,recovery,retry_guard,shortcircuit,
  transfer} API_VERSION=1` + `[banking] armed` + `[recovery] armed`. Recovery fired 8
  refreshes (6 death_spiral, 1 post_death_stall, 1 more) + 24 cross-level handoffs. Banking
  idle: 0 full WINs in 52 runs (banking only fires on a full game win). Transfer machinery
  exercised but never published (dup = sk48, which never cleared a level; next validation
  should dup a RELIABLY-SCORING game, e.g. ar25 or tu93, to see a real replay).
- **Per-game:** big efficiency wins ar25 6.46 / ft09 4.76 / tu93 4.14 / sc25 3.58 / tn36 3.57
  / vc33 3.36; zeros now cn04, dc22, g50t, ls20, m0r0, sk48, tr87, wa30 (8 vs v4's 5 —
  ls20/m0r0/cn04 regressed to 0; wa30/sk48/dc22/g50t/tr87 stay stuck). Median 0.30→0.96.
  Bundle switch (original→readable-share) confounds per-game deltas.
- **Submitted version 5** (sub `54561696`, 05:53 UTC, PENDING; description records offline
  numbers). Floor stays 1.07 (LB keeps best). Slot cadence: submit EVERY day from now on.

## 2026-07-12 — v5 LB = 1.20 (NEW BEST); env moved to new machine; 07-12 slot = v5 resubmit
- **v5 publicScore = 1.20** (sub `54561696`) — new best, up from v1's 1.07. First modified
  version to BEAT verbatim on LB (inversion pattern broken at n=3: the losers were prompt
  mods; the winner is structural grafts + verbatim prompts). Offline 1.60 → LB 1.20 is
  consistent with ±0.4 draw noise around a mean near ~1.2-1.4.
- **LB context:** top still 1.56×3 (Mathurin Ache / anngle / NoOneAhead); top-20 cutoff 1.36.
  Our 1.20 is below top-20 but within ~2-3 good draws of the leaders.
- **Environment moved:** project now on a new Windows machine/profile (`C:\Users\user`, was
  `C:\Users\ASUS`) — old uv venvs broke (trampoline → missing interpreter). Restored minimal
  tooling: uv 0.11.28 → `~\.local\bin`, CPython 3.12.13, `uv tool install kaggle` (CLI 2.2.3).
  Auth via `KAGGLE_API_TOKEN` env var from `ARC-AGI-3-Kaggle-Starter\.kaggle\access_token`
  still works. NOTE: PowerShell now (not bash); harness venv in ARC-AGI-3-Agents still broken —
  recreate with `uv sync` if local offline runs are needed again.
- **07-12 slot used (07:04 UTC): resubmitted kernel version 5 verbatim** (sub `54598846`,
  PENDING) — zero-risk daily max-draw per the LB-keeps-max strategy; version 5 already
  survived Phase A+B cleanly (no new code = no timeout/crash risk).
- **Next:** recon upstream (thtennant graft line updates, top-fork deltas) → design v6 as a
  structural lever; validate offline on Kaggle GPU before ever submitting.

## 2026-07-12 (later) — Upstream recon → v6 = v11 wall-budget slack-filler; pushed (version 6)
- **Upstream line decoded (thtennant):** v8 = v7 + shortcircuit; v9/v9b = + recovery +
  banking (never transfer); **v10 = byte-identical REVERT to v7** (flags back to
  {efficiency, retry_guard} — his heavy-graft experiments discarded, reason unknown);
  **v11 (pushed 07-12 00:20 UTC) = v10 + wall-budget slack-filler**, the only delta.
  Grafts dataset (`taaf-kaggle-source-share-fork`) unchanged since 07-08 — all deltas are
  notebook-side. Same dataset + docker pins as ours.
- **The v11 lever (adopted):** a real rerun plays 110 hidden games / 28-way concurrency at
  the stock 7920s/game ≈ 8.6h of play in the 12h kernel → last ~2.5-3h sit idle. v11 scales
  `bm.solver.max_runtime_s_per_game` to `clamp(avail·conc/n_games, 7920, 9900)` where avail
  = 11h20m soft cap − elapsed − 30min drain margin. For 110 games ⇒ ~9600s (+21%/game).
  Fail-safe (try/except → stock budget); prompts untouched. Directly attacks our measured
  #1 failure mode: all five v4 zero-games died on wall-budget timeout at level 1
  (07-11 forensics).
- **Local state gotcha:** the machine-move left a STALE v4 notebook in
  `external/my_duck_fork/`; our real v5 only existed on Kaggle. Pulled kernel latest
  (= v5 exactly as LOG describes), diffed vs upstream v7 to confirm (3 hunks: header,
  graft flags, dup-gate/n_passes). Kernel pull also DROPS `machine_shape` from metadata —
  re-added `NvidiaRtxPro6000` by hand before push (else the run lands on the wrong GPU).
- **v6 built + pushed (kernel version 6, RUNNING since ~07:50 UTC, ETA ~14:00 UTC):**
  v5 + v11 block verbatim + offline dup game switched games[0](sk48, never cleared) →
  ar25 (v5's best scorer, 6.46) so transfer publish/replay finally gets a real test;
  dup change is TRUE_SUBMISSION-guarded = inert on LB. Built via scripted JSON transform
  (5 replacements, each asserted exactly-once); text-diff verified = intended delta only.
  Offline cost: 27 games × 2 passes at 9900s ≈ 5.5h play + setup.
- **Decision rule (07-13 slot):** submit v6 iff run COMPLETE + `TAAF_V11 BUDGET` banner +
  `TAAF_GRAFTS FEATURES={banking,recovery,retry_guard,shortcircuit,transfer}` banner +
  no crash/timeout + 25-game mean ≳ 1.6 − noise; watch the 8 zero games (budget was their
  binding constraint) and the ar25-dup transfer replay. Else resubmit v5 for the daily draw.

## 2026-07-12 (evening) — v6 offline VALIDATED (1.50/0.03, clean, transfer replay works) → submitting on 07-13 slot
- **v6 offline (26 games incl. ar25-dup × 2 passes, 5h30m54s): mean 1.50 / median 0.03 /
  16-of-26 rows scoring / 0 full wins.** Run COMPLETE, **zero errors in the whole kernel log**
  (no Traceback, and — first time ever — not even terminal `request_error` timeouts; the
  budget's 30-min drain margin absorbed them). All banners fired:
  `TAAF_GRAFTS FEATURES={banking,recovery,retry_guard,shortcircuit,transfer}`,
  `TAAF_V11 BUDGET per_game=9900s n_games=26 concurrency=28`, banking/recovery armed.
- **Transfer graft validated end-to-end (the v6 dup-swap did its job):** 9×
  `[transfer] replayed levels 0..N` events (dup replayed ar25's published L0 in 5 actions;
  pass-2 runs replayed pass-1 publishes). ar25-dup scored 1.59 vs ar25's 0.44. On the hidden
  clone-family games this machinery is now proven live, not just armed.
- **Sober read on the budget lever OFFLINE:** +25% wall (7920→9900s) flipped NO stuck game —
  persistent zeros (sk48/wa30/dc22/g50t/tr87) all stayed 0, and cd82/sc25/ls20/m0r0/cn04
  flip-flopped by draw, not budget. Mean 1.50 vs v5's 1.60 = within noise (per-pass mean sd
  ≈ 0.45); median 0.96→0.03 is draw noise on a fat-tailed distribution (jackpots: re86 8.33,
  vc33 7.45, ft09 7.14). Extra time also barely adds tokens offline (~78.8k/run vs ~70k;
  GPU decode still splits 26 ways). Conclusion: stuck games are capability-bound (perception/
  planning), NOT time-bound — the timeout forensics hypothesis was about where they DIE, not
  what would save them. Budget lever's real value is on the 110-game rerun (+21%/game there,
  strictly additive: no game gets less time, behavior unchanged, drain margins proven).
- **DECISION: submit v6 on the 07-13 slot.** Mechanistic downside ≈ 0 (v6 = v5 + strictly
  more time + validated transfer), Phase A clean. Armed `external/my_duck_fork/submit_v6.ps1`
  (idempotent: skips if a 07-13 UTC submission already exists) as a background job; if the
  session dies before 00:05 UTC, run it manually.
- **Next lever candidates (v7):** the zeros need capability, not time — context compaction
  quality (evict→summarize into world-model note), per-turn output cap (~3k) A/B, base-model
  swap (Tufa: historically biggest gains). Banking still never fires (0 full wins in 104
  logged runs) — worth checking whether hidden games are shorter/winnable.

## 2026-07-12 (afternoon) — v7 = base-model swap to Qwen3.6-35B-A3B FP8 MoE; pushed (version 7)
- **Deployed-stack facts learned (share-fork bundle, `setup_commands.json` + configs):**
  vLLM 0.19.0 / torch 2.10.0 / flashinfer 0.6.6 wheelhouse; model constants live at the top
  of ONE self-contained setup script (MODEL_OWNER/MODEL_SLUG/SERVED_MODEL_NAME); served name
  `vrfai/Qwen3.6-27B-FP8` feeds env + requests. **The deployed duck is ALREADY multimodal:**
  `MULTIMODAL_CONTEXT=current_grid` + `MULTIMODAL_UPSCALE=4` send the current grid as a PNG
  image part every prompt (vision_context.py); the 27B config.json is
  `Qwen3_5ForConditionalGeneration` WITH vision_config (arch family "qwen3_5" ≠ marketing
  name 3.6). Also found: `LOCAL_ANALYZER_MAX_OUTPUT` env = clean per-turn max_tokens knob
  (currently 0 = uncapped) — future output-cap lever needs no code patch.
- **v7 lever chosen: model swap** to `cmechevalier/face-of-agi-qwen36-35b-fp8-weights` =
  Qwen3.6-35B-A3B FP8 — `Qwen3_5MoeForConditionalGeneration`, SAME vision-language family
  (vision_config present, identical chat_template.jinja), ~3B active params → directly
  attacks the measured binding constraint (aggregate decode ~206 tok/s split 26-28 ways).
  vLLM 0.19.0 registry lists the MoE arch (checked v0.19.0 tag on GitHub). Snapshot is
  complete (safetensors index + tokenizer + preprocessor configs; 40 layer shards ≈ 30.7GB;
  24 downloads → other competitors likely already on it). Weights 31GB < dense's 36GB →
  VRAM fine. Residual risk: MoE-VL loading quirks in the pinned wheelhouse (e.g. the extra
  mtp.safetensors) — if load fails, kernel errors within ~25min, costing <1h GPU; v6 stays
  the safe submittable.
- **Implementation:** notebook-level string-patch of the setup command right before
  execution (MODEL_OWNER/MODEL_SLUG swapped; SERVED_MODEL_NAME kept verbatim so solver.pkl/
  env/request references still match; raises loudly if constants missing so we can never
  silently validate the wrong weights). Metadata: model dataset attachment swapped.
  Built via scripted transform (4 replacements, asserted exactly-once); diff verified.
- **Pushed version 7, RUNNING since ~14:20 UTC, ETA ~20:30 UTC.** GPU quota: 24.3h remaining
  before this run (resets 07-18) — v7 uses ~6h, fine. Key validation metrics: `TAAF_V7 MODEL
  SWAP` banner, vLLM smoke test passes, generated tok/s (expect ≫206), 25-game mean vs
  v6 1.50 / v5 1.60, zeros count, per-game token counts (expect ≫80k).
- **07-13 slot decision unchanged:** v6 auto-submit stays armed (safe, proven). If v7
  validates spectacularly before 00:05 UTC, submitting v7 instead is the user's call —
  kill the bg job / edit submit_v6.ps1 to -v 7 in that case.

## 2026-07-12 (17:40 UTC) — v5 resubmit draw = **1.31 NEW BEST**; max-draw strategy validated
- **Sub `54598846` (v5 verbatim resubmit) resolved: publicScore 1.31** — new best (draws so
  far on the identical notebook: 1.20, 1.31). The LB-keeps-max/daily-resubmit strategy is
  paying exactly as modeled; top-20 cutoff (1.36) is within ~1-2 good draws.
- v7 (MoE swap) passed the model-load window (3h20m in, still RUNNING) → vLLM 0.19.0 loads
  Qwen3.6-35B-A3B FP8 fine. ETA ~20:30 UTC.
- Session had restarted → both background jobs died; re-armed submit_v6.ps1 (07-13 slot,
  still v6 by default) + v7 watcher.

## 2026-07-12 (18:00 UTC) — Paradigm survey written (recon.md addendum); teammate facts; v8 = sidecar-explorer design
- **Research findings written to [docs/recon.md](docs/recon.md) ADDENDUM 2026-07-12:** six
  action-interface paradigms vs the duck's code-as-actuator; strongest public-set result =
  executable world models (GPT-5.5, 15/25) but frontier-API-gated; the exploitable insight
  for US = **max-over-plays portfolio**: card score = max over plays (banking's mechanism)
  → a CPU-only bounded GraphExplorer play alongside the duck's play is strictly additive
  and costs zero GPU. Chosen as **v8**.
- **Teammate verified (read-only, his token):** `satadruhalder` sees the SAME team
  submission list (1.31/1.20/0.78) → same Kaggle team. Therefore NO extra daily slot
  exists (limit is per-team; 07-12 already used). His real asset: **untouched 30h/week GPU
  quota** → use his account for parallel Phase-A validation runs (team-internal kernel
  sharing = rules-legal). Do NOT push private kernels to non-team accounts, ever.
- **Constraint noted:** v7 still RUNNING — do not push v8 to our kernel until v7 completes
  (a concurrent push could contend for GPU session/quota); v8 validation should go to the
  teammate's account anyway.

## 2026-07-12 (18:50 UTC) — v8 (sidecar explorer) built + RUNNING on teammate's account
- **v8 = v6 base (27B, isolates the sidecar delta) + INLINE sidecar-explorer graft**, pushed
  as `satadruhalder/arc3-duck-v8-sidecar` v1 (RUNNING ~18:45 UTC, ETA ~00:30 UTC, on HIS
  fresh 30h GPU quota; ours untouched for the v7 line).
- **Design (from banking/shortcircuit source study, see scratchpad sharefork):**
  - Card score = MAX over plays; within a play completed levels are monotone and per-level
    scores freeze at completion ⇒ continuing a FAILED play can only add score.
  - `SidecarSessionMixin._finish_if_needed` (session_class seam, composed over the installed
    transfer→banking→shortcircuit chain, pickle-by-reference like shortcircuit): when the
    duck's session ends un-won, run our GraphExplorer policy (my_agent.py port: frame-hash
    graph, untested-move frontier, no-op pruning, level-up reward, object-relative clicks,
    GAME_OVER→RESET) directly via `env.step` — banking's exact primitive.
  - Bounds: ≤150s / ≤1200 actions / soft-cap margin 45s / stop_event; the notebook budget
    block RESERVES the slice (`per_game −= sidecar+30s`) so wall packing is unchanged.
    Skips when duck won (banking's territory) or final_score already set. Stops dead on WIN
    (never RESETs from WIN — that's banking's new-play trick, not ours).
  - Greppable evidence: `[sidecar] armed` + per-game `[sidecar] game=… actions=… levels a->b`.
- **Validation gates (decide next slot use):** run clean; `[sidecar] armed`; sidecar lines
  present on failed games; **levels a->b strictly greater on ≥1 stuck game** (the whole
  point); mean ≥ v6's 1.50 − noise; duck-side per-game scores not degraded (reserve slice
  is the only interaction).
- Tonight's pipeline: v7 (ours, MoE) ETA ~20:30 → v8 (his, sidecar) ETA ~00:30; 07-13 slot
  stays v6 (armed); 07-14 slot goes to the best validated of {v6 again, v7, v8}.

## 2026-07-12 (21:55 UTC) — v7 (MoE swap) VALIDATED = REJECTED; 07-13 slot confirmed v6
- **v7 result (Qwen3.6-35B-A3B FP8 MoE, 2-pass, 5h31m): mean 0.40, median 0.00 — REJECTED.**
  vs v6 1.50 / v5 1.60. Only 8/26 games scored (best: lp85 3.51, sp80 2.41, r11l 1.44).
- **The speed hypothesis was RIGHT, the capability hypothesis was WRONG:** 412 generated
  tok/s (exactly ~2× the 27B's 206) and ~150k tokens/game (vs ~80k) — the model played
  MORE turns and still scored 4× worse. A3B = ~3B active params; duck-grade grid reasoning
  tracks ACTIVE params, not total. Swap-in confirmed real (banner `TAAF_V7 MODEL SWAP`,
  model path `/kaggle/input/face-of-agi-qwen36-35b-fp8-weights` in log) so the rejection
  is attributable to the model, not a mis-run.
- **Lesson recorded:** "stronger base model" (Tufa's lever #3) means stronger REASONER, not
  faster/bigger-total. Next model candidates must have ≥27B active params or proven
  ARC-grid reasoning. Token throughput was never the binding constraint — capability is.
- **07-13 slot decision: v6 (kernel version 6) — FINAL.** Auto-submit re-armed twice after
  session restart killed job b30t0z8wd: background job ba0mkaxhw + DETACHED process PID
  5280 (survives session death; log external/my_duck_fork/submit_v6_detached.log). Script
  idempotent (re-checks list each retry) so double-arm is safe.
- v8 (sidecar) still RUNNING on teammate account at 21:50 UTC — on pace for ~00:30 ETA;
  decides the 07-14 slot vs v6-again.

## 2026-07-13 (07:20 UTC) — 07-13 slot SUBMITTED late (v6, ref 54637379); auto-submit process died with machine sleep
- **Near-miss:** both the background job AND the detached submit process died overnight
  (machine sleep/reboot — detached log empty, PID gone). Caught at 07:18 UTC; ran
  submit_v6.ps1 manually → **v6 submitted, ref `54637379` at 07:20 UTC, confirmed
  registered.** LESSON: a detached process does NOT survive machine sleep; the only
  reliable arm is running the script right when checking in, or a Windows scheduled
  task. Submission still lands well before the day ends (UTC) — nothing lost.

## 2026-07-13 (07:45 UTC) — v8 verdict: sidecar RETIRED; discovery: MAX-OVER-PLAYS is the big unexploited lever → v9
- **v8 (sidecar) result (2-pass, 5h25m, clean): mean 1.34 / median 0.05** — within draw
  noise of v6's 1.50. `[sidecar] armed` + per-game lines all present; explorer ran on
  every failed play (1200-action cap hit every time), advanced a level on 3 plays
  (g50t 0→1!, vc33 0→1, sp80 0→1). **BUT the level-ups were NOT credited**: run records
  (benchmark.json) show levels_completed/actions_per_level from the DUCK only — raw
  env.step actions bypass the run-record pathway. And even where the card pathway sees
  them, a ~1000-action clear scores (h/1000)² ≈ 0. **Sidecar RETIRED** (also observed:
  recovery-created second sessions re-ran the sidecar — once-flag is per session object).
- **Dead ends measured en route:** LOCAL_ANALYZER_MAX_OUTPUT cap pointless (tool outputs
  already ≤5k chars, tool_output_tokens=1024 server-side); retry-on-give-up pointless
  (all 52 runs consumed the full ~9750s budget; "gave_up" = budget exhaustion);
  compaction demoted (history/transitions are fully exposed in the sandbox — eviction
  only loses model reasoning, and history_messages oscillates at ~35 from turn ~10).
- **THE DISCOVERY (from pass-vs-pass variance):** the scorecard scores a card as the
  MAX over plays, but our rerun plays each hidden game ONCE (`bm.n_passes = 1 if
  TRUE_SUBMISSION else 2`). Offline mean-over-games of max(2 plays) vs single play:
  **v6 data 2.27 vs 0.83; v8 data 1.65 vs 1.14; v7 data 0.68 vs 0.12** — consistent,
  huge. Mechanisms: per-play draws are wildly variant (vc33: 0.00 and 10.71 on the
  same game); level-ups land in the first ~third of a play (events analysis), so
  half-budget plays keep most strength; and the transfer graft replays play-1 cleared
  levels into play 2 at ~zero action cost (L2@analysis_step=0 events, many games).
- **v9 = v6 + two-pass rerun** (`satadruhalder/arc3-duck-v9-twopass` v1, RUNNING since
  ~07:45 UTC, teammate quota): `bm.n_passes = 2` unconditionally; budget block divides
  wall budget by RUNS (floor 3600s, cap 9900s; offline capped 4700s to rehearse the
  rerun's ~4670s/run). No sidecar. ETA ~11:00 UTC (52 runs × 4700s / 28 ≈ 2.4h + load).
- **Validation gates:** banner `TAAF_V9 BUDGET per_run=4700s ... n_runs=52`; run clean
  ~3.2h; from benchmark.json mean-of-MAX ≥ ~1.6 (v6 baseline: mean-of-max 2.27 at
  9900s/run; the 4700s halving discount is what we're measuring) and mean-of-max must
  beat v6's single-play 0.83 by a wide margin; transfer L2@0 events present in p1.
- 07-14 slot decision: v9 (if gates pass) vs v6-again (offline 1.50, LB score of today's
  sub 54637379 pending).

## 2026-07-13 (17:15 UTC) — v6 LB = 0.55 (bad draw); v9 VALIDATED (all gates) → ported to our kernel as version 8, RUNNING; 07-14 slot armed via scheduled task
- **v6 LB resolved: 0.55** (sub `54637379`) vs offline 1.50. Best stays **1.31** (v5 draw).
  Read: same fat-tail draw noise as v2 (0.57) / v4 (0.78); v6 = v5 + strictly-additive
  budget + inert dup-swap, so a structural regression is implausible — but the budget
  filler is now 0-for-1 on LB and provably ~0 EV offline (zeros are capability-bound).
  Learning applied: stop spending slots on single-play variants; the max-over-plays
  lever (v9) directly raises the DRAW distribution, not just the offline mean.
- **v9 (`satadruhalder/arc3-duck-v9-twopass` v1) COMPLETE + ALL GATES PASS** (ran
  09:09–11:46 UTC, benchmark 2h37m, 52/52 runs, zero Traceback/request_error):
  banner `TAAF_V9 BUDGET per_run=4700s n_games=26 n_runs=52 concurrency=28`; grafts
  banner + banking/recovery armed; transfer fully live across plays (`published` →
  `replayed`/`adopted` lines, incl. L0 replays at 4-59 actions).
- **v9 offline numbers (25 core games): MEAN-OF-MAX 2.71** (gate was ≥1.6; v6 baseline
  2.27 at 9900s/run), median-of-max 0.72, 14/25 scoring, zeros 11. **pass0 mean 0.88 at
  4700s ≈ v6 single-play 0.83 at 9900s → the budget-halving discount is ~nil.**
  Killer pattern: **pass1 ≥ pass0 on ALL 25 games** (pass1 mean 2.71 vs pass0 0.88) —
  transfer warm-start + fresh-draw compounding, e.g. ft09 0→28.57 (3 levels), tu93
  0→3.97, ls20 0→3.57, ar25 0→2.78, ka59 0→1.94, vc33 2.73→4.99. (ft09 28.57 is a
  jackpot; without it mean-of-max ≈ 1.63, still ≫ any single-play mean.)
  NOTE: `final_wallclock_seconds` in benchmark.json is cumulative from benchmark start
  (p1 rows show ~9400 = 2×4700), not per-run duration — don't misread it next time.
- **Ported v9 → our kernel as version 8** (`soumyacryptic/taaf-duck-harness-fork` v8,
  pushed 17:04 UTC, RUNNING; ETA ~20:15 UTC). Byte-identical to the validated v9
  notebook except a title-only markdown header (asserted scripted transform; local v7
  copy backed up as `taaf-duck-harness-fork.v7.bak.ipynb`). Metadata: weights dataset
  swapped back MoE → stock `driessmit1/vrfai-qwen3-6-27b-fp8-hf-snapshot`; machine_shape
  kept. Gotcha: `kaggle kernels push` needs `PYTHONUTF8=1` on this machine (cp1252
  decode error on the em-dashes otherwise).
- **07-14 slot armed the RELIABLE way (07-13 lesson: detached processes die with
  machine sleep): Windows scheduled task `ARC-submit-v8-0714`** at 05:35 local
  (=00:05 UTC), WakeToRun + StartWhenAvailable, running
  `external/my_duck_fork/submit_v8.ps1` — idempotent, waits for the slot, submits
  **v8 if its Save&Run is COMPLETE, else falls back to v5** (LB 1.20/1.31); transcript
  → `submit_v8_task.log`. Manual fallback unchanged: run the script at first check-in.
- **Next:** verify v8 run completes clean (banner + mean-of-max from its benchmark.json);
  after 07-14 LB resolves, consider n_passes=3 A/B (level-ups land early in plays;
  validate on teammate quota first) and the remaining capability levers for the zeros.

## 2026-07-14 (07:30 UTC) — v8 run clean; SUBMITTED on 07-14 slot (ref 54676947); scheduled task fired late + died → manual submit
- **v8 Save&Run COMPLETE** (benchmark 18:05–20:43 UTC 07-13, 2h37m, 52/52 runs,
  `TAAF_V9 BUDGET per_run=4700s n_games=26 n_runs=52` + grafts banners, zero errors).
- **Scheduled-task postmortem:** machine was asleep at 05:35 local; StartWhenAvailable
  fired the task at 12:49 local (07:19 UTC) on wake, but it was killed mid-run
  (LastTaskResult 0xC000013A, no transcript footer; its first `kaggle kernels status`
  call returned empty). No submission resulted. LESSON: even scheduled tasks need the
  machine awake at trigger time (WakeToRun requires wake timers enabled); the morning
  check-in remains the reliable submit path. Task unregistered after manual submit.
- **Submitted v8 manually: ref `54676947` (07:26 UTC), PENDING.** Description records
  both validation draws.
- **Our v8 offline draw (independent of teammate's v9 draw, same notebook):
  MEAN-OF-MAX 1.04 / median-of-max 0.28 / 13-of-25 scoring** (pass0 mean 0.47,
  pass1 mean 1.04). vs teammate draw: mean-of-max 2.71 (his had ft09 28.57 jackpot;
  ours drew ft09 0.00). **Mechanism replicated: pass1 ≥ pass0 on ALL 25 games in BOTH
  draws** (this run: r11l 0→4.76, sp80 1.57→4.76, sc25 0→1.83, ar25 0.43→2.78;
  ar25-dup replayed to 2.78). Two mean-of-max draws {2.71, 1.04} → fat-tailed, mean
  ~1.9; single-play means {0.88, 0.47} — the max lever roughly doubles the expected
  draw. LB expectation: card = max over 2 plays; v5-line draws were 1.20/1.31.
- **Next:** record 07-14 LB score when resolved (v8 line vs v5's 1.20/1.31 decides
  whether two-pass becomes the default submit); candidates after: n_passes=3 A/B on
  teammate quota, capability levers for the 11 zero-games.

## 2026-07-14 (13:00 UTC) — v8 LB = 0.00 (COMPLETE, resolved <5h). ROOT CAUSE FOUND: competition cards allow ONE RUN PER GAME ID → max-over-plays across runs is an OFFLINE-ONLY MIRAGE. 07-15 = v5 resubmit (armed).
- **v8 (two-pass) publicScore 0.00** (sub `54676947`, COMPLETE). Resolved in <5h vs
  ~9-10h for v5/v6 reruns → the rerun collapsed early; best stays 1.31.
- **Root cause (from framework source, not speculation):**
  [competition_arcade.py:66](external — share-fork bundle) states it outright:
  *"arc_agi competition scorecards can only create one run per game ID."* Mechanics:
  benchmark.py opens ALL passes of ALL games via `start_game()` UP FRONT (before the
  solver plays; benchmark.py:149-155) → on the live gateway v8 tried 220 session opens
  incl. a duplicate of every game_id on the one shared card
  (game_api.py:184-204 — competition mode shares ONE scorecard; offline mode uses
  per-game scorecards, which is why 3 clean offline validations never saw it).
  Second opens illegal → sessions dead/corrupt → runs died fast (retry_guard bails)
  → kernel completed early with a zeroed card, 0.00 COMPLETE.
- **The 07-13 "max-over-plays" discovery is hereby CORRECTED: it is real for scoring
  (scorecard.py:466-489 takes the best play per game) but plays can only multiply
  WITHIN the single legal run — full RESET opens a new play ONLY from WIN state
  (arcengine base_game.py:311-316; banking's exact primitive) or at action_count 0.
  An un-won game can NEVER get a fresh play — not concurrently (v8's death), not
  sequentially (one run per game ID), not via a second card ("submission-style
  Arcades allow only one scorecard"). Offline n_passes=2 worked because OFFLINE mode
  runs per-game scorecards with no such constraint. The 2.71/1.04 mean-of-max numbers
  measured a mechanism the live gateway forbids.**
- **What survives untouched:** banking (WIN-only fresh-play replay — legal, still
  idle), transfer across clone families within the one run (live-proven), recovery,
  wall-budget filler. The pass1≥pass0 offline effect was mostly transfer warm-start —
  live, that value is already captured by clone-family transfer.
- **PROCESS FIX — competition_sim (R11.13):** the bundle ships
  `CompetitionArcadeServer.official_110()` + `competition_sim` ArcadeSpec: a local
  submission-shaped arcade (one shared scorecard, one run per game ID, hidden
  baselines, 110 cloned IDs) — built by Tufa exactly to reproduce these failures
  pre-submission. Our offline validations never used it; v8 would have failed in it.
  **RULE: any change that touches rerun behavior (passes, budget, scorecard, session
  lifecycle) must validate against competition_sim before a slot is spent on it.**
- **07-15 slot armed: v5 verbatim resubmit** (`submit_v5.ps1` + scheduled task
  `ARC-submit-v5-0715`, 05:35 local backstop; morning check-in primary — 07-14's task
  fired late after sleep and was killed mid-run; manual submit landed v8 at 07:26 UTC).
- **Slot ledger:** 07-13 v6 0.55, 07-14 v8 0.00 — two slots on failed structural bets;
  v5 resubmits (the boring max-draw play) remain the only line that ever beat 1.07.
- **Next levers (capability, not plays):** zero-games study (11 zeros offline),
  context-compaction quality at 32k, base-model ≥27B-active candidates; validate any
  rerun-shaped change in competition_sim first.

## 2026-07-14 16:50 UTC — Forum + code-section recon sweep (user-directed)
- **Method:** kernels via Kaggle CLI (dateRun + voteCount sorts), 9 kernels pulled and
  diffed in scratchpad `recon0714/`; forum threads readable ONLY via r.jina.ai proxy on
  individual thread URLs (list page never renders; IDs found via DDG-html/Bing).
  Full findings + ranked queue: [docs/recon.md](docs/recon.md) ADDENDUM 2026-07-14.
- **Upstream duck line:** v12=+shortcircuit, v13=+recovery, **v14 (today) drops recovery
  ("deliberately OFF") and turns ON transfer(+banking)** → first external evidence against
  recovery (our v5 runs it ON). A/B candidate, not a blind swap.
- **Liftable ops patterns:** (a) v9b fork "safety pack": live soft_end = start+11h20m
  (stock duck live = NO soft deadline; drain before 12h hard kill) + 3-games+dup-family
  fast offline commit gate; (b) maxingkong733 "fast-save": all cells guarded by
  KAGGLE_IS_COMPETITION_RERUN + dummy parquet → Save&Run in minutes, solver only in the
  hidden rerun (use ONLY for configs pre-validated in competition_sim/offline).
- **Zero-games candidate:** dead-signature guard (exact-state repeat-failure blocker,
  threshold 4, refusal payload redirects the model). Measure loop pathology on our 11
  zeros offline before shipping.
- **Duck env-knob surface enumerated (hydra kernel):** LOCAL_ANALYZER_CONTEXT_WINDOW /
  TEMPERATURE / TOP_P / TOP_K / ENABLE_THINKING, MULTIMODAL_UPSCALE — context lever is
  env-only; hydra's 8-way/49k does NOT fit live (55 games × 2.2h / 8 ≈ 15h > 12h wall).
- **Forum facts:** Tufa best LB 1.21 with a RETRACTED 1.30; public 1.6 ±0.45; draws to
  0.77 on the same notebook → our 1.31 already exceeds their best counted draw; daily
  v5 resubmits stay correct. Games are deterministic/stable-seeded (Kamradt) → underwrites
  banking/transfer replay. Known rerun killer: resource.setrlimit(RLIMIT_AS) (not ours).
  Milestone 2 = Sept 30 final.
- **Slot policy unchanged:** 07-15 = v5 verbatim (armed); queue = safety pack →
  fast-save cadence → dead-signature offline study → recovery-OFF A/B → context/
  concurrency env A/B; every rerun-shaped change through competition_sim first.

## 2026-07-14 17:15 UTC — v9 pushed: v5-live-identical + competition_sim commit gate
- **v5 notebook RECOVERED:** Kaggle API cannot pull old kernel versions (403/400 on
  version param) and the local file held v8; found a verbatim v5 copy in the
  ae40551e session scratchpad (`ours_latest/`, title cell "v5", flags match) →
  preserved as `external/my_duck_fork/taaf-duck-harness-fork.v5.ipynb`.
  **Rule: keep a local .vN backup of every pushed version from now on.**
- **Found in v5 cell 14: the 11h20m live soft-end "safety pack" is ALREADY there**
  (same lineage as Yin Li's v9b fork) — recon queue item (a) was half-shipped;
  only the fast commit gate was missing.
- **v9 built by asserted transform of v5** (build_v9.py; anchors must match exactly
  once; cells 1-13/15/16 asserted byte-identical; live anchors asserted intact):
  - Cell 14 offline branch: after the stock offline game list, a guarded block
    starts `taaf.competition_arcade.CompetitionArcadeServer(game_ids=[ar25,ka59,tu93],
    total_runs=4, environments_dir=<bundled env files>)` → ONE shared scorecard,
    one run per game ID, games k000-k003 (k003 = ar25 clone; family_store
    fingerprints key on initial state, not env name → transfer publish→replay is
    exercised ON the shared card). Sets n_passes=1 when gate active; stock dup
    block skipped; ANY fault → stock v5 offline validation (25+dup × 2 passes).
  - LIVE path byte-identical to v5 (diff verified: every added line behind
    `not TRUE_SUBMISSION`) → a v9 submission IS a v5 draw.
- **Pushed 17:10 UTC → kernel version 9, Save&Run RUNNING.** Expected ~2-3h
  (9-10h means the gate fell back). Validation gates: `TAAF_V9 COMMIT_GATE` +
  `TAAF_GRAFTS` banners; 4 clean game_runs in benchmark.json; transfer replay
  evidence on k003; no dead-session errors on the shared card.
- **If clean:** v9 replaces v5 as the daily submit (zero draw-risk — live path
  identical) and becomes the fast-iteration template for queue items (b)-(e).
  07-15 slot stays v5 (already armed; v9 result lands after the slot anyway).

## 2026-07-21 12:33 UTC — Session resumed after 7-day gap; 07-21 slot SUBMITTED (v5, ref 54877376); 5 slots (07-16..07-20) MISSED
- **What:** Resumed after a 7-day gap (last LOG entry 07-14). Checked Kaggle state,
  submitted the 07-21 daily slot: **kernel version 5 (v5), ref `54877376`, 12:32 UTC,
  PENDING.** Direct CLI submit (`-v 5`); did NOT use `submit_v5.ps1` (its slotDay is
  hardcoded to 07-15 → it would false-positive on the existing 07-15 sub and exit).
- **State found:**
  - **Best LB still 1.31** (v5, sub `54598846`, 07-12). Unchanged.
  - **07-15 slot:** v5 resubmit landed **0.55** (sub `54720755`, COMPLETE) — another
    fat-tail bad draw (cf. v2 0.57, v4 0.78, v6 0.55); best stays 1.31.
  - **07-16 through 07-20: FIVE slots MISSED (no submissions).** Machine was asleep /
    no morning check-in and no reliable daily auto-submit fired. Five wasted free
    max-draws — the single biggest recurring loss in this project. Unrecoverable.
  - **Kernel latest version = v9 (competition_sim commit-gate)** and it is COMPLETE:
    Save&Run output holds the `k000..k001` (ar25/ka59/tu93/ar25-clone) commit-gate
    runs → the fast gate ran (not the 9-10h fallback). v9's live path is byte-identical
    to v5, so a v9 submission would be an equivalent v5 draw; chose v5 anyway as the
    strictly-proven notebook (v5 is the exact one that cleared Phase A+B and drew 1.31;
    v9-live is asserted-identical but has never gone through Phase B).
- **Why v5:** zero-risk proven max-draw per standing discipline (never submit an
  unvalidated version; resubmit the best-known clean notebook every day; LB keeps max).
- **RELIABILITY PROBLEM (root cause of the 5 missed slots) — must fix:** there is still
  no dependable unattended daily submit. Scheduled tasks don't fire when the machine
  sleeps (07-14 postmortem), detached processes die on sleep (07-13 postmortem), and a
  7-day unattended stretch dropped 5 slots. The only reliable path so far is a human
  morning check-in, which didn't happen for a week. Options to evaluate next: a cloud
  cron (Kaggle-side scheduled notebook that self-submits, or a GitHub Action with the
  Kaggle token as a secret) that does not depend on this machine being awake.
- **Next:** record 07-21 LB score when it resolves; decide whether to make v9 the daily
  default (verify its Save&Run log banners `TAAF_V9 COMMIT_GATE` + `TAAF_GRAFTS` and the
  4 clean k00x game_runs first); stand up a machine-independent daily submit so slots
  stop leaking; remaining capability levers for the 11 zero-games unchanged.

## 2026-07-23 14:50 UTC — ACTION7 capability hole found (fix = 1 line); 07-23 slot = v5 (ref 54930226); v10 pushed, Save&Run in flight

- **Trigger:** user flagged that submissions aren't yielding good results; asked to check
  the competition page for changes and for improvement info.
- **Slot bookkeeping:** 07-21 v5 draw resolved **0.65** (sub `54877376`) — 4th v5 draw
  (1.20 / 1.31 / 0.55 / 0.65, mean ≈0.93). **07-22 slot MISSED (6th leak).** 07-23 slot
  **SUBMITTED = v5, ref `54930226`, 14:37 UTC, PENDING** (direct CLI `-v 5`).
- **LB moved hard (07-23 snapshot):** top = **1.86 YUTO KOJIMA** (was 1.56 on 07-12);
  top-20 cutoff ≈ **1.44** (was 1.36) → **our 1.31 is now OUT of the top 20**. Band
  1.44–1.61 is dense; Tufa Labs themselves at 1.45; 星际黑AGI at 1.47 running a PUBLIC
  **stock-baseline** kernel (`boristown/agi-duck-harness-fast-eval`, 138 votes — all
  patches explicitly disabled). Read: most of the band is daily-resubmit max-draw
  compounding on the stock duck; teams that never miss a slot out-draw us. Our 6 leaked
  slots are the main relative loss; no rules/timeline changes found (milestone 2 still
  Sept 30, grand prize $700K @100%).
- **THE FINDING — ACTION7 is visible but unexecutable in the deployed duck:**
  - [action_names.py:7-15](external/taaf_source/src/ARC3-Inference/inference/agent/action_names.py#L7-L15)
    maps only ACTION1–6 + RESET. `to_model_action("ACTION7")` passes the label through
    (line 22) → the model SEES `ACTION7` in `valid_actions`; `to_engine_action("ACTION7")`
    returns **None** (lines 25–31).
  - [solver.py:520-525](external/taaf_source/src/ARC3-Inference/inference/framework/solver.py#L520-L525):
    every model attempt → `Unknown action at index N: 'ACTION7'`. The button exists,
    can never be pressed. Wasted turns at best; ACTION7-gated levels unreachable.
  - **6/25 public games (24%) handle ACTION7 in step logic:** ar25, bp35, lf52, sb26,
    sk48, su15 — **sk48 is our never-cleared transfer dup**. Extrapolate ~13/55 hidden
    LB games. Engine supports it (ARC-AGI-3-Agents README changelog 0.9.2: "ACTION7 as
    possible GameAction"; official spec: RESET, ACTION1–5+7 simple, ACTION6 x,y).
  - Public prior art: `kevin250304/arc3-duck-minimal-action7-reproducible` (07-18) —
    converged after a rollback to the SAME minimal form: one reverse-map dict entry,
    prompts/solver verbatim. (Their v1 also added animation-frame metadata to
    last_action_result — rolled back for score stability; noted as a later lever.)
- **v10 BUILT + PUSHED 14:45 UTC (Save&Run RUNNING):** = v5 byte-identical except
  cell-12 prepend: verify `arcengine.GameAction.from_name("ACTION7")`, then
  `MODEL_TO_ENGINE_ACTION["ACTION7"] = "ACTION7"` + asserts; fail-safe try/except
  keeps stock mapping and prints `TAAF_V10 ACTION7 FAILED` on any error. Model-facing
  label set unchanged (valid_actions already showed ACTION7) → zero prompt drift; fits
  the proven rule "structural levers + verbatim prompts win". Offline path = v5's full
  2-pass / 25-game benchmark → directly comparable to v5's 1.60/0.96 baseline.
  Backup: `external/my_duck_fork/taaf-duck-harness-fork.v10.ipynb`.
- **Validation gates for v10 (check ~20:30 UTC):** (1) log banner
  `TAAF_V10 ACTION7 OK`; (2) no `ACTION7 FAILED` banner; (3) offline mean/median ≥
  v5's 1.60/0.96 (esp. watch ar25/bp35/lf52/sb26/sk48/su15 deltas); (4) clean finish
  ≤11h20m soft end. If clean → 07-24 slot = v10 (first candidate beyond v5 since the
  two-pass line closed).
- **Ops:** kaggle CLI briefly died with `ImportError: DLL load failed while importing
  _socket: An Application Control policy has blocked this file` — transient (worked on
  retry minutes later); REST (`Invoke-RestMethod` + Bearer) is the reliable fallback.
  User authorized Kaggle GPU test runs this session.
- **Next:** check v10 Save&Run gates; if clean submit v10 on 07-24; still open = the
  machine-independent daily auto-submit (6 leaked slots now); later lever = animation
  metadata (kevin's rolled-back half) behind an offline A/B.

## 2026-07-23 21:40 UTC — v10 VALIDATED: offline 2.21/0.88 (mean +38%, best legal-mode run); 07-24 slot armed = v10

- **v10 Save&Run COMPLETE, all gates pass:** banner `TAAF_V10 ACTION7 OK: reverse mapping
  installed (engine action verified)` at t=551s + `TAAF_GRAFTS FEATURES={banking,recovery,
  retry_guard,shortcircuit,transfer}` — both mechanisms live. No FAILED banner. Clean
  **4h 24m 27s** (vs v5's 4h25m — no runtime cost), 26 games × 2 passes = 52 runs, 0 won,
  7,937 actions, 3.15M tokens, 198 tok/s.
- **Score: mean 2.21 / median 0.88** vs v5 baseline 1.60/0.96 → mean **+38%**, median −8%
  (within draw noise). Best legal-mode offline of the entire line (v1 1.11, v2 1.01,
  v4 1.35, v6 1.50, v5 1.60).
- **Per-game vs v5:** zeros 8 → 7 unique — **cn04 0→3.46, m0r0 0→1.06 flipped positive**;
  sc25 3.58→0 regressed (it flip-flopped by draw before, cf. v6 postmortem); dc22/g50t/
  ls20/sk48(+dup)/tr87/wa30 stay stuck. Efficiency wins up across the board: vc33
  3.36→8.57, tu93 4.14→5.95, ar25 6.46→7.17, ft09 4.76→5.16, cd82 4.76, cn04 3.46,
  tn36 3.57 flat. ACTION7-game scorecard: ar25 up, sb26 2.78, su15 2.22, bp35 0.28 /
  lf52 0.33 nonzero, sk48 still 0 (its wall isn't ACTION7 alone).
- **Read:** the fix pays twice — (a) two capability zeros flipped, (b) fewer wasted turns
  on `Unknown action` errors → more productive actions per token budget everywhere.
- **07-24 slot ARMED (persistent monitor, this session):** at 00:02 UTC submit kernel
  **version 10**, verify via REST list, retry ×3. v10 passes the standing validation rule
  (full Save&Run offline, both banners, mean ≥ baseline). v10 becomes the daily default.
- 07-23 slot (v5, ref `54930226`) still PENDING at time of writing.

## 2026-07-24 08:30 UTC — 07-24 slot SUBMITTED = v10 (ref 54953277); 07-23 v5 drew 0.97; armed monitor DIED with session

- **07-23 (v5, ref `54930226`) resolved 0.97** — sub-best draw, best stays 1.31. v5 draw
  history now: 1.20, 1.31, 0.55, 0.55, 0.65, 0.97.
- **The 00:02 UTC auto-submit monitor never fired** — Claude Code session exited before
  midnight, monitor died with it, no output file. Lesson repeated: ANY submit path tied to
  a live session/machine is unreliable. Slot was still open at 08:12 UTC check-in.
- **07-24 slot = kernel version 10** (first v10 live draw; validated 2.21/0.88 offline,
  see 07-23 entry) → ref `54953277`, 2026-07-24 ~08:25 UTC (Kaggle lists 14:25 local-ish
  timestamp), PENDING. Verified via REST list.
- Machine-independent daily auto-submit remains TOP priority — now 3 distinct failure
  modes witnessed (scheduled task sleep-kill, morning check-in gap, session-tied monitor).

## 2026-07-25 19:50 UTC — v10 LB = 1.46 NEW BEST (+0.15); 07-25 slot = v10 resubmit (ref 54983628)

- **v10 first live draw (ref `54953277`) = 1.46 — NEW BEST**, up from v5's 1.31 ceiling
  (6 v5 draws never beat 1.31; v10's FIRST draw did). At/above the 07-23 top-20 cutoff
  (≈1.44). The ACTION7 reverse-map fix transfers to the hidden set — consistent with the
  offline read (+38% mean via flipped zeros + fewer wasted turns).
- **Structural-lever rule holds (n=2):** v5 grafts 1.07→1.31, v10 ACTION7 fix 1.31→1.46.
  Both = engine-level fixes, prompts verbatim.
- **07-25 slot = v10 resubmit** (daily max-draw discipline) → ref `54983628`, 19:48 UTC,
  PENDING. Caught with ~4h to spare — again a manual catch; auto-submit still unbuilt.
- Next: GPU levers from the recon queue (dead-signature guard / recovery-OFF A/B /
  context bump) — v11 candidate builds tonight.

## 2026-07-25 20:20 UTC — dead-sig guard KILLED by measurement; v11 (context 40k) PUSHED, Save&Run in flight

- **Dead-signature guard deprioritized on data.** Parsed v10 events.jsonl for all 7 zero
  games + 3 controls: exact-state 4+ repeat loops (the guard's trigger) fire 0-3×/run,
  zeros and controls alike (worst streak 12, ls20 p1). Zeros DO waste 40-55% of actions
  on no-ops — but VARIED ones, not exact-state loops. Guard would refuse ~1-8 actions per
  100-475. Queue rule "ship only if it'd flip ≥1 game" → it wouldn't. Killed pre-build;
  measurement cost 0 GPU hours. Analysis: scratchpad/analyze_loops.py.
- **v11 PUSHED (kernel version 11) = v10 + `LOCAL_ANALYZER_CONTEXT_WINDOW` 32768→40960 +
  `bm.solver.concurrency` 28→20.** Queue lever #5 (winner-named: context/memory; Hydra
  Scout precedent 49152@8-way — not live-safe; ours is). Mechanism: cell-12 hook patches
  `tool_agent._LOCAL_ANALYZER_CONTEXT_WINDOW` (module constant, read in
  ToolAgent.__init__; instances created per-game after the hook) + solver attr; vLLM
  max_model_len 64k unchanged. Fail-safe try/except → stock 32768/28. Prompts/grafts/
  ACTION7 fix untouched. Live math: 55 games / 20-way = 3 waves × 7920s ≈ 6.6h < 11h20m.
- **Gates when Save&Run completes (~5-7h; monitor armed):** banner `TAAF_V11 CONTEXT OK`;
  mean ≥ v10's 2.21 − noise AND median ≥ 0.88 to become daily default; watch wall time
  (3 waves vs v10's 2) and tok/s (KV pressure at 40k).
- 07-25 slot (v10 resubmit, ref `54983628`) PENDING.

## 2026-07-26 08:55 UTC — v11 VALIDATED (1.99/0.95, zeros 7→5) → daily default; 07-26 slot = v11 (ref 54995834); GitHub Actions auto-submit LIVE

- **07-25 v10 resubmit resolved 0.89** (ref `54983628`) — v10 draws now 1.46 / 0.89; best
  stays **1.46**. LB 07-26 snapshot: top 1.86 (YUTO KOJIMA), cutoff #20 = 1.45 → our 1.46
  is INSIDE the top 20, tied 4-way (Biubiu / MLRush / Arunodhayan / Kochi Loki).
- **v11 Save&Run COMPLETE + CLEAN (all gates pass):** banners `TAAF_V11 CONTEXT OK:
  analyzer context 32768->40960, concurrency 28->20` + `TAAF_V10 ACTION7 OK` +
  `TAAF_GRAFTS {banking,recovery,retry_guard,shortcircuit,transfer}`. Wall 6h36m
  (20:04→02:40 UTC; 3 waves at conc 20, as designed; v10 was 4h24m). Zero real errors
  (only code-echo matches in log). 26 games × 2 passes = 52 runs, 0 won.
- **Score: mean 1.99 / median 0.95** vs v10's 2.21/0.88 → mean −0.22 (within ±0.45
  per-pass noise, passes the pre-registered "≥ 2.21 − noise" gate), median +0.07 ✓.
  **Unique zeros 7 → 5** (sk48, m0r0, s5i5, tr87, g50t): flipped TO scoring = dc22 0.43,
  ls20 **0.93 both passes** (first stable ls20 ever), wa30 2.22/0, sc25 0.70/0; flipped
  to zero = m0r0, s5i5. Fat tail: ft09 12.52/14.29 jackpot; efficiency top-end softer
  (vc33 8.57→0.72 avg, ar25 7.17→0.97) — draw noise on a fat-tailed metric.
  tok/s 156 vs v10's 198 (−21%: KV pressure at 40k + 20-way batching) but wall is longer
  so total tokens similar (~3.7M); live math unchanged (55/20 = 3 waves × 7920s ≈ 6.6h).
- **v11 = daily default per the pre-registered gate. 07-26 slot = v11 first live draw**
  (ref `54995834`, 08:22 UTC, PENDING) — first live test of the context lever.
- **AUTO-SUBMIT BUILT AND LIVE (top-priority fix; 7 slots leaked to date):** GitHub
  Actions cron in the private repo (`Cryptic2-0/arc-agi-3-agent`):
  - `.github/workflows/daily-submit.yml` — cron 00:20 UTC daily + workflow_dispatch;
    ubuntu runner, python 3.12, `pip install kaggle`.
  - `scripts/daily_submit.py` — idempotent: lists submissions via REST, exits if
    today's UTC slot is already used (manual submits always win), else submits the
    kernel/version in `submit_config.json` and verifies it landed.
  - `submit_config.json` — current daily default (kernel, version 11, message).
    **To change the default: edit version+message, push. To pause: disable the
    workflow in the repo's Actions tab.**
  - Secret `KAGGLE_API_TOKEN` set via REST sealed-box (gh CLI rejected the stored
    `gho_` token for missing `read:org`, but its scopes gist/repo/workflow suffice
    over raw REST; pynacl via `uv run --with pynacl`, VIRTUAL_ENV must be unset —
    broken venv poisons uv).
  - Machine can now sleep indefinitely; the three witnessed failure modes (sleep-killed
    task, missed check-in, session-tied monitor) are all bypassed.
- **Next:** record v11 draw (if clearly bad → revert submit_config.json to version 10);
  verify tomorrow's cron run fired (Actions tab / submissions list); remaining queue:
  recovery-OFF A/B, fast-save cadence, capability levers for the 5 zeros
  (sk48/m0r0/s5i5/tr87/g50t).

## 2026-07-27 — v11 LIVE = BAD (0.55 / 0.61) → REVERTED to v10; gate rule fixed; cron verified

- **v11 live draws:** 07-26 first draw (ref `54995834`) = **0.55**; 07-27 cron draw
  (ref `55017907`, submitted 04:03 UTC by the Actions cron — first autonomous fire,
  ~3.7h GitHub cron lag, slot still claimed) = **0.61**. v10 lineage drew 1.46 / 0.89.
  Two consecutive low draws + offline mean already lower (1.99 vs 2.21) = context
  lever (40960/20) fails live. **v11 DEMOTED; `submit_config.json` reverted to
  version 10.** Best LB stays **1.46**.
- **Root cause of the bad promotion (approach fix, n=1 lesson):** the pre-registered
  gate accepted a mean drop "within ±0.45 noise" because median improved. But the LB
  metric IS a mean over games — median-favoring trades fat-tail games (vc33 8.57→0.72,
  ar25 7.17→0.97 in the v11 run) for breadth, which the LB punishes. tok/s −21% (KV
  pressure) also cut turns/game live. **NEW PROMOTION GATE: offline mean must be
  ≥ incumbent mean (median = tiebreak only); prefer 2 independent Save&Run passes
  before promoting a new daily default.**
- **Auto-submit system: first real-world PASS.** Cron fired without the machine
  awake, submitted the configured version, idempotency held (exactly one submission
  on 07-27). Slot-leak fix confirmed working end-to-end.
- **Next:** push revert; tomorrow's cron submits v10 automatically (max-draw
  farming resumes on the proven version); lever queue unchanged — recovery-OFF A/B,
  fast-save cadence, capability levers for the 5 zeros (sk48/m0r0/s5i5/tr87/g50t).

## 2026-07-28/29 — Full competition recon; ACTION7=UNDO discovered; v12 pushed (Save&Run in flight); source bundle mirrored

- **Slot check 07-28:** cron submitted v10 (ref `55044246`), drew **0.79**. v10 draws now
  1.46 / 0.89 / 0.79. Best LB stays 1.46. LB snapshot 07-28: top **1.86** (YUTO KOJIMA),
  #2 1.61, #20 cutoff = **1.46 = us** — we sit exactly ON the cutoff; mean lift needed.
- **Discussion sweep (headless-Edge ID harvest + r.jina.ai per-thread; ListTopics API now
  404s, DDG/Bing scrapes empty):**
  - **729985 — ORGANIZER: scored-run wall limit is 9 HOURS, not 12** ("For v3 it is 9hrs…
    we should switch that" re docs inconsistency). Our 11h20m live soft-end could NEVER
    fire before a 9h kill. Also: private LB scores are from the original run, never
    recalculated; only 50% of public tasks are on the public LB.
  - **728299 — scoring formula from the arc_agi package:** per-level
    `min((baseline/actions)^2*100, 115)` — a level can pay up to **115** (better than
    baseline pays above par); game = weighted mean capped. Depth >> marginal efficiency.
  - 728220: arc-agi 0.9.8 vs 0.9.9 gives "significantly different agent performance";
    competition pins 0.9.8. 728934: Claude Opus 5 scores 30% (off-hardware); commenters
    note it can't run under the 9h/RTX6000 constraint. Nothing else load-bearing.
- **Kernel recon (9 pulled):** two independent kernels (prvsiyan decision-ledger +
  action7-shadow) map **ACTION7 -> model label "UNDO"** calling it the documented round
  trip. **VERIFIED against official sources: ARC-AGI-3-Agents
  `agents/templates/multimodal.py:166` maps `GameAction.ACTION7: "Undo"` (full map:
  1=Up 2=Down 3=Left 4=Right 5=Perform 6=Click 7=Undo), and ar25's game code implements
  ACTION7 as pop-saved-state-and-restore.** Our v10 exposed it as opaque "ACTION7" —
  semantic label = free capability, same structural-mapping class as the v10 fix
  (1.31→1.46, n=2 rule). 暗黑AGI (1.47 LB, 175-vote kernel) runs near-stock duck live =
  verbatim+daily-farm meta confirmed. obirdy "verified world-model"/"state ledger" =
  prompt-addendum class (our n=3 rule: loses live) — skipped. deep-reasoning-agent
  (temp 0.2/top_k 3) and "179/183 levels" claims = not credible. cognitive-duck (3.6k-line
  cognition patch) = unproven, high risk — skipped.
- **UPSTREAM GONE: `kaggle kernels list --user thtennant` → "Not found"** (account deleted
  or renamed). Their dataset `thtennant/taaf-kaggle-source-share-fork` (our kernel's
  source bundle!) still resolves but is orphaned → **mirrored byte-identical to
  `soumyacryptic/taaf-kaggle-source-share-fork-mirror`** (CC0; 87 files, src/ structure
  verified extracted) and repointed the kernel at the mirror.
- **v12 BUILT + PUSHED (kernel version 12, Save&Run RUNNING since ~18:5x UTC 07-28):**
  v12 = v10 (v11 context lever reverted) + three changes:
  1. **ACTION7 model-facing label "UNDO"** — `ENGINE_TO_MODEL_ACTION["ACTION7"]="UNDO"`,
     `MODEL_TO_ENGINE_ACTION["UNDO"]="ACTION7"`, legacy `"ACTION7"` spelling kept as
     fallback. Mapping-only; prompts byte-verbatim. Banner: `TAAF_V12 UNDO OK`.
  2. **Live soft-end 11h20m → 8h20m** (9h organizer limit; typical live wall ~5h, tail
     insurance only). Offline branch unchanged.
  3. **Source bundle = our mirror** (cell 6 DATASET_SOURCES + kernel-metadata).
  Grafts/flags/context (32768/28) all v10-verbatim. Local backups: .v11.ipynb (pulled),
  .v12.ipynb staged; machine_shape re-verified in metadata.
- **Gates when Save&Run completes (~4.5-5h; background monitor armed):** banner
  `TAAF_V12 UNDO OK` + `TAAF_GRAFTS` banners; wall ~4.5h (2 waves at conc 28); **NEW GATE
  RULE: offline mean ≥ v10's 2.21** (median tiebreak only). UNDO-relevant games to watch:
  ar25, bp35, lf52, sb26, su15 + zero sk48 (6 ACTION7 games). If pass → submit_config.json
  version 12 + push (cron takes over); if fail → v10 stays default, mirror-repoint still
  wanted (re-cut v13 = v10 + mirror only, revalidate).
- **Queue after v12 decision:** recovery-OFF A/B (upstream v14 evidence), fast-save
  cadence, capability levers for remaining zeros (sk48/m0r0/s5i5/tr87/g50t).

## 2026-07-29 03:5x UTC — v12 VALIDATED CLEAN BUT GATE-FAILED (1.81 < 2.21) → NOT promoted; v10 stays default; 07-29 slot = cron v10

- **v12 Save&Run COMPLETE (20:12 UTC 07-28 → 00:37 UTC 07-29, wall 4h24m50s — identical
  to v10's pace; conc 28 confirmed):** banners clean (`TAAF_V12 UNDO OK` + `TAAF_GRAFTS`
  all five), **source bundle loaded from OUR MIRROR** (`/kaggle/input/taaf-kaggle-source-
  share-fork-mirror`) — mirror path fully proven end-to-end. 52 runs, 0 won, 0 errors,
  204.79 tok/s, 3.25M tokens.
- **Score: mean 1.81 / median 0.46 → GATE FAIL (rule: mean ≥ incumbent v10's 2.21).**
  Median up (0.46 vs 0.88? — v10 median was 0.88, so BOTH down); unique zeros ~9
  (dc22/g50t/ka59/m0r0/sk48/sp80/tn36/tr87/wa30) vs v10's 7. **UNDO label did NOT lift:
  sk48 (ACTION7 game, zero target) stayed 0.00 both passes + dup; ka59/wa30 flipped to 0.**
  Fat tail: ft09 14.29, ar25 6.72 (ACTION7 game, decent), tu93 6.37. Within ±0.45 noise
  of 2.21 − 0.40, but the v11 lesson stands: no rationalizing mean drops. **v12 NOT
  promoted. UNDO-label lever: 0-for-1 offline, shelved (semantic labels ≠ free capability
  on this stack; the v10 neutral mapping already let the model discover usage).**
- **07-29 slot: cron fired 03:42 UTC (ref `55071144`, v10, PENDING) — 3rd autonomous
  fire, idempotency proven again (our manual submit 2 min later correctly 400'd).**
- **Carry-forwards from the v12 run (validated, want them in the next default):**
  (a) **mirror repoint** — upstream thtennant deleted; mirror proven by this clean run;
  (b) **live soft-end 8h20m** (9h organizer limit) — live-only, no offline signal, low
  risk. → **Next: v13 = v10 exactly + mirror + 8h20m soft-end (NO UNDO)**, one clean
  Save&Run as regression check (bundle bytes identical, expect ~2.2 ± noise), then
  promote v13 to daily default on pass (it IS v10 live).
- Queue unchanged: recovery-OFF A/B, fast-save cadence, zero-game capability levers.

## 2026-07-29 17:1x UTC — 07-29 draw = 1.03; v13 BUILT + PUSHED (kernel version 13, Save&Run running)

- **07-29 draw resolved: `55071144` = 1.03** (v10, cron submit). v10 draw sequence now
  **1.46 / 0.89 / 0.79 / 1.03** (mean 1.04, best 1.46). Draw spread confirms the ±0.4-0.5
  fat tail; LB keeps the max, so daily resubmit stays the right play. v11 draws (0.55/0.61)
  remain the worst pair on the board — revert was correct.
- **v13 built = v10 EXACTLY + two risk-reducers, no capability change.** Build asserted
  mechanically (`build_v13.py`): diff vs v10 = cells **[0, 6, 14]** only —
  0 = header text, 6 = `DATASET_SOURCES` mirror repoint, 14 = live soft-end
  `hours=11,minutes=20` → `hours=8,minutes=20`. Cell 12 restored to v10's ACTION7
  reverse-map fix byte-for-byte (banner back to `TAAF_V10 ACTION7 OK`); asserted
  **no "UNDO" anywhere in the code cells**. Context/concurrency stay 32768/28.
- **Pushed: kernel version 13, Save&Run RUNNING (17:14 UTC).** Backup at
  `external/my_duck_fork/taaf-duck-harness-fork.v13.ipynb`. Expect wall ~4.5h.
- **Gate (regression check, not a lever test):** v13 IS v10 mechanically, so expect
  **mean ≈ 2.21 ± noise**; promotion rule = mean ≥ 2.21 with the usual noise read — a
  large drop would mean the MIRROR BUNDLE differs from upstream (the only offline-visible
  change), which is the thing this run exists to falsify. On pass → `submit_config.json`
  version 13 + GitHub push so the cron submits it (survives upstream deletion + the 9h
  wall). On fail → investigate mirror bytes; v10 stays default.

## 2026-07-29 17:42 UTC — TEAM REBRAND: `soumyacryptic/kochi-loki-arc-agi-3` pushed (PRIVATE, version 1, Save&Run running)

- **New kernel = Kochi Loki branding + our full writeup, runtime byte-identical to v13.**
  Build (`build_kochi.py`) asserts: all 8 code cells byte-equal to the v13 notebook, no
  "UNDO" anywhere, mirror bundle in cell 6, `hours=8, minutes=20` in cell 14. Only the
  header markdown is new (one cell replaces the old header; sections 1-8 kept verbatim).
- **Writeup content (all our work, in the notebook itself):** agent spec table; full LB
  draw table (20 submissions, 06-23 graph 0.17 through 07-29 v10 1.03, best 1.46);
  offline table by version (v3 0.86 / v4 1.35 / v5 1.60 / v6 1.50 / v7 0.40 / v8 1.34 /
  v10 2.21 / v11 1.99 / v12 1.81); three levers that worked (graft set, ACTION7
  executability, mirror + 8h20m); ten negative results with the cost of each (prompt-margin
  rule n=3, offline-best-as-crash-profile, one-run-per-game-ID 0.00, active-params>
  throughput, context lever, semantic-label failure, budget filler, sidecar, thinking
  off, draw variance); six operating rules; where score is lost (7 zeros, banking never
  fired in 104 runs) + next levers.
- **Attribution:** framed as inspiration + credit to the Tufa Labs public release
  (discussion 717133) — kept because the runtime loads their publicly shared solver
  bundle at execution time; the word "fork" is gone, our levers are foregrounded.
- **PRIVACY VERIFIED SERVER-SIDE** via `kaggle kernels pull -m`: `"is_private": true`,
  `enable_gpu: true`, `enable_internet: false`, `competition_sources:
  ["arc-prize-2026-arc-agi-3"]`, `machine_shape: NvidiaRtxPro6000` = submission-eligible
  profile. NOTE: the `kernels/list` REST endpoint reports `isPrivate:false` /
  `enableGpu:false` even for the known-private duck kernel — **those list fields are
  stubs, do not trust them**; pull metadata to check privacy.
- **Eligibility path:** a kernel can only be submitted after a completed Save&Run version,
  so this run IS the eligibility proof. Two GPU sessions now run in parallel (duck v13 +
  kochi v1, ~4.5h each, ~13.4h of the 30h weekly quota used this week). On both passing:
  point `submit_config.json` at `soumyacryptic/kochi-loki-arc-agi-3` version 1 and let the
  cron take over; the duck kernel stays as history/fallback (its accepted submissions and
  the 1.46 LB draw are unaffected by the rebrand).
- Local copy: `external/kochi_loki/` (notebook + kernel-metadata.json).

## 2026-07-30 15:00 UTC — v13 GATE PASS (2.49) + Kochi Loki run clean (1.71) → **IDENTICAL CODE, 0.78 SPREAD**; Kochi promoted to daily default

- **v13 Save&Run COMPLETE (07-29 17:22 → 21:46 UTC, wall 4h24m39s):** mean **2.49** /
  median 0.41, 26 games x 2 passes = 52 runs, 0 won, 195.74 tok/s, 3.11M tokens.
  Banners `TAAF_V10 ACTION7 OK` + `TAAF_GRAFTS` (all five) + `source bundle =
  /kaggle/input/taaf-kaggle-source-share-fork-mirror`. **GATE PASS: 2.49 >= v10's 2.21.**
  Mirror repoint + 8h20m soft-end both validated.
- **Kochi Loki v1 Save&Run COMPLETE (07-29 17:51 → 22:15 UTC, wall 4h24m31s):** mean
  **1.71** / median 0.31, same 52 runs, 203.34 tok/s, 3.23M tokens, same banners, bundle
  mounted at `/kaggle/input/datasets/soumyacryptic/taaf-kaggle-source-share-fork-mirror`.
- **THE FINDING — offline single-run noise is ~0.8, larger than most levers we grade.**
  The two runs above execute **byte-identical code** (build asserted all 8 code cells
  equal) on identical hardware and games, ~30 min apart: **2.49 vs 1.71, median 0.41 vs
  0.31.** Per-game whiplash in the same pair: `sk48-dup` = **0.00** in one run, **2.78**
  in the other; `lp85` 2.78, `su15` 2.22, `bp35` 0.44 in the Kochi run vs zeros/timeouts
  in the other. Cause: analyzer read-timeouts against the local vLLM (both logs) shuffle
  which games get budget, and gave_up-at-level-1 is a coin flip on several games.
  **Consequence: every single-run offline verdict in this log carries +/-0.4 (1 sigma-ish)
  and the n=1 promotion gate has been grading noise.** v12's "1.81 < 2.21 = fail" is NOT
  a proven regression -- it is one draw from this distribution. (v12 stays shelved: no
  positive evidence either, and it costs a slot to test.) **v11's demotion STANDS** --
  that was live LB evidence (0.55/0.61), not offline.
- **GATE RULE v2 (supersedes the 07-27 rule):** promote on **paired evidence** -- either
  2 Save&Run passes of the candidate vs the incumbent's known distribution, or a
  same-session A/B. A single-run mean delta below ~0.8 is indistinguishable from noise;
  treat it as "no evidence", not as a pass or a fail. Cheap levers (no capability change)
  may still ship on a clean run + mechanical diff proof, which is what v13/Kochi did.
- **07-30 slot: cron fired 03:30 UTC with v10, ref `55098418` = 0.90.** v10 draws now
  1.46 / 1.03 / 0.90 / 0.89 / 0.79 (5 draws, mean 1.01, best 1.46 unchanged).
- **PROMOTED: `submit_config.json` -> `soumyacryptic/kochi-loki-arc-agi-3` version 1.**
  Rationale: its runtime is v13 (= v10 + mirror + soft-end) proven by a clean 4h24m run,
  it carries the team branding, and it removes the deleted-upstream dependency. The duck
  kernel stays untouched as fallback; all accepted submissions and the 1.46 best draw are
  unaffected. Next cron fire (07-31 00:20 UTC) submits Kochi v1 -- first live draw of the
  branded kernel.

## 2026-07-31 03:0x UTC — 07-31 slot claimed MANUALLY with Kochi Loki v1 (FIRST branded draw); auto-submit hardened to 5 fires/day

- **First Kochi Loki draw submitted: ref `55124569` (PENDING)**, kernel
  `soumyacryptic/kochi-loki-arc-agi-3` version 1, via `scripts/daily_submit.py`.
  The submit endpoint accepted the new kernel => **eligibility proven end-to-end**
  (private notebook + GPU + internet off + competition source + completed Save&Run).
- **Correction to an in-session claim: the cron was NOT skipped.** I first read the
  missing 07-31 run as GitHub silently dropping the schedule and committed that in
  `44e6aa6`. Wrong. **Real UTC at the time was 03:0x, not 15:0x** - verified against the
  GitHub API `Date` header (`Fri, 31 Jul 2026 03:03:42 GMT`) after a dispatched run came
  back stamped `03:01:52Z`. The previous working session ran 12h earlier (07-30 15:00
  UTC), and I carried its wall-clock into this one. Every past fire landed 03:30-04:03
  UTC (00:20 cron + GitHub's usual 3.2-3.7h lag), so at 03:0x the 07-31 run simply had
  not fired yet. **Actions history is clean: 5 runs, 5 successes, workflow state active.**
- **Consequence of the manual submit: none bad.** It claimed the slot ~30 min ahead of
  the cron with the kernel the cron would have used anyway (Kochi v1); the later
  scheduled fire no-ops via the idempotency check. **Ops lesson: derive "now" from a
  server Date header before concluding a scheduler missed - a stale local clock reading
  looks exactly like a dropped run.**
- **Hardening KEPT, on its real justification (not the false one): 5 cron fires per UTC
  day** - 00:20, 04:37, 10:43, 16:53, 21:47, off-the-hour minutes. GitHub's scheduler
  genuinely lags 3-4h and can drop runs under load; `daily_submit.py` is idempotent
  (lists today's submissions, skips if used), so extra fires are free no-ops and a manual
  submit still wins. Cost of the insurance is zero; cost of one genuinely lost slot is a
  whole day of draw.
- **Also confirmed:** 07-30 draw = **0.90** (ref `55098418`, v10 via cron).

## 2026-09-02 — MONTH-GAP RECON: the field swapped base model and we did not. v14/v15 built + pushed (Qwen3.8-27B-FP8)

- **Where we actually stand: rank 488 / 2694, score 1.46** — the same 1.46 drawn on
  2026-07-24 (v10). The daily cron never missed: 32 consecutive draws 07-31 → 09-01, all
  Kochi Loki v1, **range 0.50–1.35, mean ~0.84, max 1.35** — not one beat the July best.
  Ops were fine; the agent stopped being competitive.
- **The leaderboard re-formed while we stood still.** 07-12 top was 1.56, 07-28 top 1.86,
  #20 cutoff 1.46 = us. **09-01: top = 7.51 (cstl), then 4.99, Tufa Labs 4.71, 4.52, 4.45,
  4.05 … #20 cutoff = 2.97.** Our 1.46 is now ~250 places below the top-20 line.
- **Cause found: a new base model. `Qwen3.8-27B-FP8` was released 2026-08-14 (Apache 2.0).**
  Every version we ever shipped (v1…v13, Kochi v1) serves **Qwen3.6-27B-FP8**, the weights
  the June-30 duck came with. The base model is the one axis this project has never varied.
  The field moved within days: the top public kernels all pin the same Kaggle Model
  `foysalemonshanto/qwen3-8-27b-fp8-repacked-v1/PyTorch/hf-fp8/1` —
  `foysalemonshanto/lb-9-arc3-duck-v12-with-qwen-3-8-27b` (268 votes),
  `keithtyser/duck-qwen3-8-27b-fp8`, and thtennant's own `arc3-duck-v21` … `v30`.
  Same dense-27B **active**-parameter class, so the v7 MoE lesson does not apply.
- **Calibration on what the model swap is worth — measured from the swappers' own LB rows,
  not from their titles:** thtennant (`Beyond Good and Eval`) **1.93**, FOYSAL **2.23**,
  keithtyser **2.36**. Each is a max over 41–99 draws. **So the public recipe is worth
  roughly a 2.0–2.4 best-draw, i.e. ~1.6× our current 1.46 — it is the entry ticket to the
  race, not a 5.** The 7.51 and 4.71 at the top are doing something not published.
- **`maxDailySubmissions = 1`, verified against the Kaggle competitions API** (`userRank`
  488 came from the same call). Web sources quoting "5/day" are describing the ARC-AGI-2
  track. There is no extra-draws lever: 1 draw/day, **28 draws left to milestone 2
  (Sept 30), 61 to final (Nov 2)**.
- **Upstream is back and has moved on.** `thtennant/taaf-kaggle-source-share-fork` was
  re-published (2026-09-01, 613 KB vs our 07-28 mirror's 449 KB) and now ships
  `src/taaf-grafts` with 13 new flags on top of our five: goalkeep, hudmask, clickmap,
  searchmap, clockwatch, lawbook, winframe, carryover, undo, untried, tally, bandlevel,
  deathclock. All default OFF with a stated all-flags-off byte-identity guarantee.
  His v30 runs `{efficiency, retry_guard, shortcircuit, goalkeep, hudmask, clickmap,
  searchmap, clockwatch, lawbook, winframe, carryover, undo, untried, tally, bandlevel}`.
- **Our ACTION7 fix is still ours.** `grep -r ACTION7 src/ARC3-Inference/` on the fresh
  upstream bundle returns nothing — the reverse map still has no ACTION7 entry. The v10
  lever (1.31 → 1.46) survives into both new builds.
- **BUILT + PUSHED (`scripts/build_v14.py`, anchored edits, asserted diffs):**
  - **v14** = Kochi v1 + Qwen3.8 pin + upstream-fork bundle repoint. Graft flags unchanged
    (our v5 set). Changed cells `[0, 6, 8]`. Pushed as **kernel version 2** of
    `soumyacryptic/kochi-loki-arc-agi-3`, Save&Run RUNNING.
  - **v15** = v14 + the upstream v30 graft set. Changed cells `[0, 6, 8, 12]`; **v14 vs v15
    differ in cells [0, 12] only** — a clean same-lever A/B. Pushed as new kernel
    `soumyacryptic/kochi-loki-arc-agi-3-v15` version 1, Save&Run RUNNING. Server-side
    metadata verified by `kernels pull -m`: `is_private true`, GPU on, internet off,
    `NvidiaRtxPro6000`, competition source, Qwen3.8 model attached.
- **A bug caught offline that would have cost a GPU session.** The bundled setup resolves
  weights with `resolve_kaggle_dataset_path(MODEL_OWNER, MODEL_SLUG)`, which checks
  `TAAF_KAGGLE_INPUT_PATHS` and then the two *dataset* mount shapes. A Kaggle **Model**
  mounts at `/kaggle/input/models/<owner>/<slug>/<framework>/<variation>/<version>` — neither
  of those — so the setup would have fallen through to a non-existent path and vLLM would
  have died ~10 min in with the weights sitting right there. Fix: cell 6 publishes
  `kaggle_input_paths[QWEN_MODEL_REF] = str(QWEN_MODEL_PATH)` before `setup_env` is built.
  **Verified offline by executing the patched setup command's resolver against the real
  `setup_commands.json`:** `MODEL_PATH -> /kaggle/input/models/foysalemonshanto/…/hf-fp8/1`,
  `SERVED_MODEL_NAME -> Qwen/Qwen3.8-27B-FP8`, all three assignments rewritten 1×.
- **Deferred: the mirror re-push.** `kaggle datasets version` on
  `soumyacryptic/taaf-kaggle-source-share-fork-mirror` was blocked by the local sandbox, so
  v14/v15 attach **upstream's** bundle directly. Upstream deleted it once before (07-28), so
  this is a live single point of failure. A byte copy of the 09-01 snapshot is saved at
  `external/fork_bundle/` (gitignored) — re-mirroring is one command once the push is allowed.
- **Gates when the two runs land (~4.5h):** banners `TAAF_V14 QWEN38 MOUNT OK` +
  `TAAF_V14 QWEN38 SETUP PATCHED` + `TAAF_V10 ACTION7 OK` + `TAAF_GRAFTS FEATURES={…}`;
  bundle line = `taaf-kaggle-source-share-fork`; wall ~4.5h. **Read the means against GATE
  RULE v2 (offline single-run noise ≈ 0.8): v14-vs-v15 is a legitimate same-session A/B, but
  either one against v10's 2.21 is a single draw and proves little on its own.** The load-
  bearing question this pair answers is not "which is better" but "does the Qwen3.8 path
  run clean end to end" — the LB, not the offline mean, decides the rest.
- **Honest read on the 5.0 target:** 5.0 is 2nd place today and above Tufa Labs. The public
  recipe tops out near 2.4. Model swap + v30 grafts + our ACTION7 fix is the credible path
  to **~2.5–3.5 best-draw over the remaining 28–61 draws**; 5 needs a lever nobody has
  published. Named candidates, in EV order: (a) **throughput** — keithtyser serves
  `RadixArk/Qwen3.8-Flash-Next-NVFP4` with 3-token MTP speculative decoding; our own
  measurement says thinking eats ~85% of the token budget and only ~150 env actions/game get
  taken, so tokens/s converts almost linearly into actions, the one thing we know is binding;
  (b) the 7 zero games, which are capability-bound, not time-bound; (c) `analyzer_timeout`
  (keithtyser pins 900 s) — our own logs blame analyzer read-timeouts for the ±0.8 offline
  noise, so this may be a variance lever as much as a mean lever.

## 2026-09-02 — v14 + v15 BOTH CLEAN; Qwen3.8 path proven; v14 mean 3.61 → promoted to daily default

- **Both Save&Run runs COMPLETE and clean.** Banners in both:
  `TAAF_V14 QWEN38 MOUNT OK: /kaggle/input/models/foysalemonshanto/qwen3-8-27b-fp8-repacked-v1/pytorch/hf-fp8/1 (18 shards)`,
  `TAAF_V14 QWEN38 SETUP PATCHED: {'MODEL_OWNER': 1, 'MODEL_SLUG': 1, 'SERVED_MODEL_NAME': 1}`,
  vLLM served `Qwen/Qwen3.8-27B-FP8` at `max_model_len 65536`, smoke test
  `Generated: 2 + 2 equals 4.` The Kaggle-Model mount fix worked exactly as simulated —
  the one bug that would have cost a session did not fire.
- **Scores (26 runs each = 25 public games + sk48 dup):**

  | | incumbent Qwen3.6 | **v14** (model swap only) | **v15** (+ v30 grafts) |
  |---|---|---|---|
  | mean | 2.49 / 1.71 | **3.61** | 2.80 |
  | median | 0.41 / 0.31 | 1.51 | 2.04 |
  | levels cleared | — | **22.0** | 19.5 |
  | zeros | 7 | 7 | 8 |
  | tok/s | 195–203 | 246 | 287 |
  | mean actions/game | — | 66 | 62 |

- **v14 = 3.61 exceeds the incumbent's best-ever offline draw (2.49) by +1.12, wider than the
  ±0.8 noise band.** First lever since the ACTION7 fix to clear that bar. Second-order win:
  the agent now clears 22 levels at 66 actions/game where the old stack averaged 149 actions
  and far fewer clears — Qwen3.8 is both faster (246 vs ~200 tok/s) and more action-efficient,
  which is what a completion-capped score actually pays for.
- **v15 did NOT pay: 2.80 vs 3.61.** Legitimate same-session paired A/B, but the 0.81 delta sits
  right on the noise threshold → read as **no evidence**, not "worse". v15's median is HIGHER
  (2.04 vs 1.51); v14's mean leans on `ft09 = 28.57`. The upstream v30 graft stack does not
  transfer to our stack as-is. Shelved, not rejected — re-test if a lever needs it.
- **sk48 still the noise canary:** v14 `sk48 = 0.00` / `sk48-dup = 1.39`; v15 both 0.00.
- **PROMOTED: `submit_config.json` → version 2 (= v14).** Daily default was Kochi v1 (Qwen3.6),
  which the whole field abandoned in August; leaving it in place costs a draw per day. Revert is
  one edit back to `"version": 1`.
- **09-02 slot already spent before the runs landed:** ref `55953236`, Kochi v1, 03:51 UTC
  (manual run of `scripts/daily_submit.py`; server Date header confirmed 2026-09-02 03:51 UTC
  per the stale-clock ops lesson). **First live Qwen3.8 draw = the 09-03 cron fire.**
- **Leaderboard mechanics confirmed (arxiv 2603.24621 + Kaggle API):** 25 public demo /
  55 semi-private (API) / 55 fully private (official competition). ARC Prize state they
  "will never report public set scores of any system on the official leaderboard".
  Kaggle submission records carry both `publicScore` and `privateScore`; every one of ours has
  `privateScore` empty → the private half is withheld until the 2026-11-02 deadline and
  decides final standing. Scoring confirmed as RHAE: `S = min(1.0, h/a)²` with the human
  baseline = **second-best** human's action count, level-index weighted (level 1 = 1/15,
  level 5 = 5/15 of a 5-level game), averaged over environments.
- **Next:** (1) watch the 09-03 draw — first live Qwen3.8 number; (2) `deathclock` is still the
  highest-value unflagged graft (not in v30, not in v15); (3) the MTP head ships in the
  checkpoint we already mount and is still unused by the vLLM launch; (4) confirm whether
  final ranking needs explicit submission selection before 11-02.

## 2026-09-03 — v14 LIVE = 2.26 (NEW BEST, rank 216); v16/v17 pushed; step-6 arithmetic corrected by source read

- **FIRST LIVE Qwen3.8 DRAW = 2.26** (ref `55974448`, 09-03 04:35 UTC, kernel version 2).
  Previous best was **1.46** set 07-24; the whole 33-draw August series topped out at 1.35.
  **Rank 216 / 2752**, up from 488. Roadmap step 1 GATE PASSED (draw >= 1.46), so the model
  swap is confirmed live, not just offline. Board above us: 7.51 / 5.53 / 5.49 / 5.43 / 4.99.
- Sanity on the offline gate: v14 offline 3.61 -> live 2.26. The ordering held this time
  (unlike v7, whose best-ever offline became LB 0.06), but the ~1.35 gap between offline mean
  and live draw is worth remembering when reading future offline numbers.
- **SESSION 1 PUSHED, both Save&Run RUNNING** (`scripts/build_v16_v17.py`, anchored + asserted):
  - **v16** = v14 + `goalkeep` + `deathclock`, cell 12 only (changed cells `[0, 12]`).
    `deathclock` is the lever; `goalkeep` is only its carrier — composite.py gates it as
    `if active.get("goalkeep") and flags.get("deathclock")` and goalkeep's digest is the sole
    channel to the agent. Pushed as kernel version **3** of `kochi-loki-arc-agi-3`.
    Target: tn36 / sc25 / sp80, our three non-starved zeros.
  - **v17** = v14 + MTP speculative decoding + `LOCAL_ANALYZER_TIMEOUT=900`, cell 8 only
    (changed cells `[0, 8]`). MTP is **probed** (`--help` for `--speculative-config`) and has a
    **stock fallback** (kill + relaunch without) because neither the flag spelling nor the
    method name is confirmed for the pinned vLLM 0.19.0. Banners to grep:
    `TAAF_V17 MTP PROBE`, `TAAF_V17 MTP ACTIVE=`. Pushed as version **2** of
    `kochi-loki-arc-agi-3-v15`.
  - Verified offline before pushing: both notebooks' code cells parse; v17's patch was executed
    against the real `setup_commands.json` and the resulting here-doc body **parses as valid
    Python** (`launch=1 timeout=1`).
  - `submit_config.json` still pins version **2** (v14), so the daily default is untouched by
    either experiment.

### CORRECTION to roadmap step 6 — from reading the scheduler, not from arithmetic

The 09-02 roadmap claimed "~4 games' worth of budget does not exist" by dividing an 8h20m soft
end across 110 games. **That framing was wrong.** What the source actually says:

- **The pool assumption is CONFIRMED.** `HarnessSolver._worker_pool` is a `ThreadPoolExecutor`
  sized to `self.concurrency` ("Custom pool sized to self.concurrency: asyncio.to_thread routes
  onto Python's default executor, capped at min(32, cpu+4) — which would silently cap real
  concurrency below self.concurrency"). A freed slot does admit the next queued game.
- **`runtime_limit_reached()` reads ONLY the fixed `max_runtime_s_per_game`** — no awareness of
  how much global wall remains. Every game burns its full 7920 s; our run records confirm all 25
  offline games end `gave_up` at ~7920 s.
- **The 8h20m "safety pack" does far less than its own comment claims.**
  `soft_time_remaining_seconds()` is consumed by exactly one caller — `request_timeout_seconds()`
  — where it clamps an individual HTTP request timeout. **It does not stop scheduling, does not
  drain the pool, and does not reallocate per-game budget.** It cannot protect the tail of a run.
- **Where 7920 came from:** `_max_runtime_minutes_per_game()` derives it as
  `max_experiment_runtime / waves`, and `_wave_count = ceil(runs / concurrency)`. For the OFFLINE
  shape (26 games x 2 passes = 52 runs / 28 = **2 waves**) that is 2 x 132 min = 4.4 h — exactly
  our observed 4h24m wall. **It was sized for a 2-wave offline run and is applied unchanged live.**
- **The live shape is 110 runs, not 55.** Tufa's own grafts say so:
  `competition_arcade.py: OFFICIAL_110_RUN_COUNT = 110`, `family_store.py: "All 110 competition
  runs share ONE process and ONE ThreadPoolExecutor"`, `transfer_solver.py: "the 110 competition
  runs"`. **Our cell-14 comment claiming "55 games / 28-way = 2 waves, typical live wall ~5h" is
  therefore wrong and should be corrected.**
- **Real live arithmetic:** ceil(110/28) = **4 waves** x 7920 s = 31,680 s = 8 h 48 m, plus ~7 min
  vLLM boot (measured: server ready at t=394 s, smoke test done t=417 s) = **~8 h 55 m against
  Kaggle's 9 h hard wall. Margin ~5 minutes** — and the soft end cannot save the tail.
- **Status: MECHANISM CONFIRMED, EXPOSURE UNMEASURED.** We have no live wall-clock telemetry
  (competition reruns emit no log), so whether wave 4 is actually being truncated is unproven.
  It is consistent with the August draw distribution but not evidence for it.
- **Cheap mitigation, for a later version:** set `bm.solver.max_runtime_s_per_game = 7200` on the
  TRUE_SUBMISSION branch only. 4 x 7200 = 28,800 s = 8 h + boot = 8 h 07 m, ~50 min margin, at a
  9% per-game budget cut. Alternative: raise live concurrency to 38 so 110/38 = 3 waves, but that
  cuts tok/s per game and throughput is our measured bottleneck — prefer the budget cut.
- **GATE unchanged:** reproduce in `competition_sim` (110 cloned IDs, one shared card) before
  shipping. That rule exists because v8 drew 0.00 on a scorecard mechanic offline could not see.

## 2026-09-04 — SESSION 1 RESULTS: both levers NO-EVIDENCE; MTP works and buys nothing → decode is not the bottleneck

- **Both runs clean.** v16 banners `[goalkeep] armed` + `[deathclock] armed`; v17 banners
  `TAAF_V17 MTP PROBE: --speculative-config present=True` and **`TAAF_V17 MTP ACTIVE=True`**
  (no fallback fired — vLLM 0.19.0 accepts `--speculative-config {"method":"mtp",
  "num_speculative_tokens":3}` against this checkpoint's bundled MTP head on the first try).

  | | v14 | **v16** goalkeep+deathclock | **v17** MTP+timeout |
  |---|---|---|---|
  | mean | 3.61 | 3.94 | 3.26 |
  | median | 1.51 | 1.81 | **2.30** |
  | zeros | 7 | **11** | 8 |
  | levels cleared | 22.0 | 23.0 | 22.0 |
  | tok/s | 246 | 257 | 255 |
  | actions/game | 66 | 62 | 60 |

- **v16: NO EVIDENCE, and it missed its own target.** +0.33 mean is well inside the ±0.8 band.
  Worse, the three games it was aimed at — **tn36, sc25, sp80 — are all still exactly 0.00**.
  Unique zeros went **7 → 11**. Median and levels moved up slightly; nothing here is separable
  from noise. deathclock's mechanism is real (upstream measured it on 150 levels) but on OUR
  stack it did not convert. Not promoted. Not rejected — one draw.
- **v17: NO EVIDENCE on the mean** (-0.35, inside noise), **but the highest median of any run
  to date (2.30 vs v14's 1.51).**

### THE FINDING — MTP works perfectly at the engine and is worth ~nothing end to end

From `vllm-openai-server.log` (fetched from the kernel output, 1.16 MB, 1,586 `SpecDecoding`
metric lines):

```
SpecDecoding metrics: Mean acceptance length: 3.30, Accepted throughput: 352.41 tokens/s,
                      Drafted throughput: 459.01 tokens/s
                      ... 3.17 / 245.00 / 338.70
                      ... 3.27 / 243.69 / 322.48
```

**Mean acceptance length ~3.2–3.3.** The engine is emitting roughly three tokens per forward
step instead of one — speculative decoding is doing exactly what it is supposed to.

**And job-level throughput moved 246 → 255 tok/s (+3.7%), which is inside the run-to-run spread
we already see from graft changes alone (v14 246 vs v15 287, no serving change at all).**

**Therefore: GPU decode is NOT the binding constraint.** If tokens-per-forward-step triples and
end-to-end token rate does not move, the wall-clock is being spent elsewhere — prefill of a 32k
context re-sent every turn across 28 concurrent games, the Python sandbox round-trip, and harness
per-turn overhead. This independently corroborates the v3 finding from 2026-07-09: *"tok/s dropped
224→178 when replies were short: wallclock overhead binds when replies are short, not GPU decode."*
We had that written down and then spent roadmap step 3 on decode anyway.

- **Consequence for roadmap step 3:** premise refuted. MTP is not a throughput lever on this
  workload. Keep it on (it is free and slightly positive) but stop treating it as the answer.
- **Consequence for roadmap step 4:** re-aim. The scheduler knobs worth testing are the
  **prefill** ones — `--enable-prefix-caching` (currently ON; keithtyser's measured winner has it
  **OFF**), `--max-num-batched-tokens`, chunked prefill — not decode batch size. Note keithtyser
  pairs MTP with `max_num_seqs=8`, i.e. he *lowers* concurrency to make speculation pay; testing
  MTP at our 28-way concurrency in isolation may have been the wrong split.
- **New candidate, now the highest-value throughput idea:** cut prompt bytes per turn. The
  analyzer context is 32768 and the whole history is re-sent every turn; if prefill dominates,
  prompt size converts to wall-clock more directly than anything on the decode side.
- **Also recorded:** vLLM warned `Enabling num_speculative_tokens > 1 will run multiple times of
  forward on same MTP layer, which may result in lower acceptance` — acceptance came out at 3.3
  regardless, so the warning did not bite here.

- **Live:** 09-03 draw = **2.26** (new best, rank 216/2752). 09-04 draw `56004733` submitted
  04:37 UTC, PENDING. Daily default unchanged (`submit_config.json` version 2 = v14) — neither
  session-1 candidate earned promotion.

## 2026-09-04 — prior-year recon: mostly dead, but it forced a read of the REAL scorer

**Asked: can the previous year's solution help? Short answer: no, and the arithmetic says why.**

- **"Previous year" is two different competitions.**
  - **ARC-AGI-2 / ARC Prize 2025** (Mar–Nov 2025, 1,455 teams, 15,154 entries). Winner **NVARC**
    (Ivan Sorokin + Jean-Francois Puget, NVIDIA) at **27.64% public / 24% private**: a fine-tuned
    **4B** model + heavy **synthetic data generation** + **test-time training**, building on the
    2024 ARChitects entry. Different task entirely — static input→output grid pairs, no actions,
    no levels, no efficiency term. Direct evidence it does not port: **Abstraction Lab & MindsAI**,
    an ARC-AGI-2 heavyweight, sits at **2.94** on our board. Sorokin's artifact
    (`sorokin/qwen3_4b_grids15_sft139`) is on Kaggle but is 4B and grid-SFT — our v7 rule
    (capability tracks active params) plus the VL requirement rule it out.
  - **ARC-AGI-3 agent preview 2025** — same task, and its winner is our ancestor.
    **StochasticGoose 12.58%** (CNN+RL frame-change prediction) cleared 2 games / 18 levels in
    **255,964 actions** ≈ 14,000 per level against baselines of 20–256. Under the shipped scorer
    that is `s_i = (100/14000)^2*100 ≈ 0.000005` per level. **Structurally worth ~0 here.** The
    preview metric rewarded completion; RHAE squares the efficiency ratio.
  - The **graph-exploration paper** (19 levels @ 4000-action budget) contributes two ideas —
    priority-tiered click targets and an untested-action frontier — and **both are already in the
    bundle** as `clickmap`, `searchmap` and `untried`. Nothing new to import.
  - **Sensi** (arxiv 2603.17683, 2026) is the only modern paper actually on ARC-AGI-3:
    **v1 solved 2 levels, v2 solved 0.** Its value is a negative finding worth keeping —
    *"the architectural bottleneck has shifted from learning efficiency to perceptual grounding …
    a self-consistent hallucination cascade originating in the perception layer."*

### THE ACTUAL PAYOFF — the scoring formula, verified from the wheel we install

Read out of `arc_agi_3_wheels/arc_agi-0.9.8-py3-none-any.whl`, the wheel cell 4 pip-installs:

```
per completed level i:  s_i = min( (baseline_i / actions_i)**2 * 100 , 115 )
per failed level i:     s_i = 0
weight_i = level_index (1-based)
raw       = sum(s_i * w_i) / sum(w_i)          # over ALL levels of the game
max_score = sum(w_i where s_i > 0) / sum(w_i) * 100
game      = min(raw, max_score)
```

- **The copy in `ARC-AGI-3-Agents/.venv/` is 0.9.1 and is WRONG in three ways** — linear instead
  of squared, cap 100 instead of 115, plain average instead of level-index weighted. It is also
  the copy an editor opens first. Flagged in REPORT.md.
- **Verified against the v14 run:** `ft09 = 28.57 = 100*(1+2+3)/21`, `ka59 = 10.71 = 100*(1+2)/28`,
  `vc33 = 10.71`. Each equals its cap **exactly**, which happens only when raw >= cap — i.e. when
  efficiency is already saturated.
- **So: on every game we score, the cap binds. Efficiency is a solved problem for us; DEPTH is the
  entire remaining score.** Clearing a level in <= baseline saturates its contribution; going
  faster still gains nothing; every action past baseline costs quadratically.

### RESET does not refund the scored action count — MEASURED

`sum(actions_per_level) == len(history)` **exactly** in every game run of `out_v14/benchmark.json`,
*including* runs containing a RESET (tn36 96 actions / 1 reset, dc22 98 / 1, tu93 36 / 1).
Actions accumulate across resets within a level.

`deathclock`'s "RESET bought the budget back on 134 of 134" is about the **engine's** limit
(`base_game.level_reset` → `_action_count = 0`) — a **different counter** from the scorer's.

**Consequence: exploration is never free, and the "explore → RESET → execute cleanly" policy I
sketched on 09-03 does not work as described.** It buys engine budget, not score. It also explains
tn36: 96 actions on a level with baseline 32 means even a successful clear scores
`(32/96)^2*100 = 11.1`, not 115.

- **Roadmap consequence:** the prompt-procedure lever (step 5) must be re-aimed. "Explore in life
  one, execute in life two" is still right for *surviving* the engine's action clock, but it does
  NOT reset the score denominator — so the instruction has to be **"reach the clear inside the
  baseline action count"**, not "use the second life freely".
- **Still open (zero GPU):** whether `actions_per_level` is what the *competition gateway* reports
  or only what our offline scorecard computes. `add_level` is defined in the wheel and never
  called there — the caller is server-side.
