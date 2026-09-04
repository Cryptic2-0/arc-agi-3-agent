# REPORT.md — Corrected Mental Model

> What we now believe is TRUE about the problem, the platform, and the binding constraint —
> *after* results overruled earlier guesses. Distinct from PROJECT.md (status) and LOG.md (history).
> Rule 14: fix this the moment the model changes. A confidently-wrong report is worse than none.
> (Layer 3 of 3.)

---

## How to use this file
- Write claims only once a **measured result** or a **community source** backs them. Cite it.
- When a belief flips, do not delete the old one silently — move it to "Superseded" with the date and what overruled it. Future-you needs to know the trap existed.

## Current model
<!-- Empty until first real datapoint. Do NOT fill with armchair theory (anti-pattern D). -->
Objective + platform = backed by official spec & repo code (cited). **First measured datapoint
(2026-06-23):** random agent on ls20 = score 0.0, 0/7 levels, 81 actions. Two facts established:
1. **The local OFFLINE scorecard computes the real competition metric** — it returns `level_scores`
   and `level_baseline_actions` per level using the same formula. So the dev feedback loop is the
   true metric, free and offline, not a correlated proxy. (Source: live run + `arc_agi/base.py`.)
2. **Completion is the binding constraint, not efficiency** — random never clears level 1, so the
   `min(human/agent,1)²` efficiency term is moot until a solver can win at all. (n=1; widen later.)
3. **Leaderboard datapoints (2026-06-24): v1 0.17 → v2 0.23.** GraphExplorer on the hidden games.
   v2 (ACTION6 expanded into per-object click targets) gained +35% rel, matching its offline gain
   (7/183 vs 3/183) — so **the offline scorer predicts leaderboard direction.** Pipeline sound; agent
   generalizes to unseen games. Best preview agent = 12.58% (far). Each LB submission = 5/day, CLI-submittable.
4. **Prior art says LLMs lose; graph-exploration wins** (recon 2026-06-23, [docs/recon.md](docs/recon.md)).
   Frontier LLMs ~0.2–0.4%; best preview agent 12.58% (CNN+RL frame-change prediction); a graph-based
   explorer cleared 19 levels vs random's 6 at a 4000-action budget. Pattern across all winners: hash
   frames → discrete state graph, learn action→frame-change effects, prune no-ops, explore the frontier
   systematically. **Build target = no-LLM graph-based exploration agent.** Don't use the repo LLM templates.

### The objective (sourced understanding)
Source: ARC-AGI-3 Kaggle competition page + scoring methodology (pasted 2026-06-23).
- Agent plays interactive grid games. Per game: states NOT_FINISHED / WIN / GAME_OVER; multiple
  levels of rising difficulty. Frame = grid ≤64×64, cell values 0–15, (0,0) top-left.
- Actions: RESET, ACTION1–5 + ACTION7 (simple), ACTION6 (complex, needs x,y). Meaning of each is
  game-specific and must be *discovered* — no labelled examples. (Code: [agent.py:186-196](ARC-AGI-3-Agents/agents/agent.py#L186-L196), [random_agent.py:34-59](ARC-AGI-3-Agents/agents/templates/random_agent.py#L34-L59).)
- **Score:** level = `min(human_actions/agent_actions, 1.0)²`; game = level-index-weighted avg;
  total = mean over games; capped 0–100%. 100% = beat every game matching human action counts.
- Eval: 110 private unseen games (55 public LB / 55 private LB). 25 public games local for dev.
- Agent contract: implement `is_done(frames, latest)` + `choose_action(frames, latest)`; a Swarm
  runs instances across games in parallel ([agent.py](ARC-AGI-3-Agents/agents/agent.py)).

### The binding constraint (MEASURED n=1, widen later)
**Completion / in-context skill acquisition on a novel game is the gate.** Random clears 0/7 ls20
levels → efficiency (the squaring) is a *second-order* concern that only bites after a solver can
win. Possible secondary limits once solving: LLM latency/token budget per action, per-game action
cap (default `MAX_ACTIONS=80` < ls20's human baselines up to 192 — raise it). API rate limits N/A
offline. Rule 3/12: don't pre-optimize efficiency; spend effort on *solving level 1* first.

### Platform meta
Source: competition page + repo README/changelog.
- **Two operation modes** (`arc_agi/base.py` `OperationMode`): `online` (API only, three.arcprize.org),
  `offline` (local `environment_files/` only, local scorecard, NO network), `normal` (download+local).
  Dev = **offline** (free, unlimited, exact metric). Supplied `KGAT_…` key 401s online (wrong type).
  `main.py` only does online; offline play needs the custom `run_offline.py` runner (built 2026-06-23).
- **Submission:** auto-calculated — "as long as the agent takes action on any game, a submission
  file for all games is created." No hand-transcription.
- **Deadlines:** entry/team-merge **2026-10-26**; final submission **2026-11-02**; winners **2026-12-04**.
- **Harness:** `arc-agi` pkg + `ARC-AGI-3-Agents` repo. Local env execution OR `ONLINE_ONLY=True`
  for online API/replays (README changelog 0.9.3). API key `ARC_API_KEY` via `.env`.
- **Frame fields** (changelog 0.9.3, breaking): `score`→`levels_completed`, `win_score`→`win_levels`;
  `available_actions` per frame (0.9.2). Run: `uv run main.py --agent=random --game=ls20`.
- UNKNOWN still: real per-run quotas/time budget and rate limits on the *scoring* harness.

### The milestone-1 reality check (2026-07-07)
5. **"LLMs lose" is now FALSE at the harness level.** Milestone-1 winner (Tufa Labs duck
   harness, 1.21 LB; forks reproduce 1.21) IS an LLM agent — but grounded: local Qwen3.6-27B-FP8
   (vLLM, RTX Pro 6000 96GB), sees ASCII grid + connected-component segmentation (raw grid
   hidden), writes Python in a per-call-fresh sandbox, executes `action(...)` from code, keeps a
   persistent world-model note, 64k context with eviction. The preview-era "LLMs score ~0.3%"
   datapoint was about naive API-driven LLM loops, not about a code-tool harness around a local
   model. (Source: kernel `jeroencottaar/tufa-labs-duck-harness-june-30-milestone-winner`,
   writeup discussion 717133, source in `external/taaf_source/`.)
6. **Open-sourcing milestones reset the LB.** Rules force winners to open-source at each
   milestone → post-June-30, top-20 = duck forks (1.30–1.56). Competing = fork the frontier +
   add deltas, not build from scratch. Same will happen at milestone 2 (Sept 30).
7. **Offline-best ≠ LB-safe:** v7 (best offline, 8/183) scored **0.06** on LB — a crash/timeout
   profile, not a performance profile. Any submission needs a full clean Save&Run on Kaggle
   hardware first; offline wins don't transfer if the kernel dies on hidden games.

### The base model is a first-order lever, and it moves without us (2026-09-02)
8. **A base-model release re-ranks the whole leaderboard in about two weeks.**
   `Qwen3.8-27B-FP8` shipped 2026-08-14. Between 07-28 and 09-01 the public top went
   **1.86 → 7.51** and the #20 cutoff went **1.46 → 2.97**, while our score sat at 1.46 and
   32 consecutive daily draws came back in 0.50–1.35. Nothing about our agent got worse;
   the reference frame moved. **Rule: check for a new base checkpoint on the same cadence
   as the leaderboard, and treat "the model we serve" as a tracked config axis, not a
   constant.** Corollary to the v7 lesson — that one said capability tracks *active*
   params (a 3B-active MoE failed); this one says the dense-27B slot itself gets refilled.
9. **A public recipe is calibrated by its authors' LB rows, not by its notebook title.**
   `lb-9-arc3-duck-v12-with-qwen-3-8-27b` has 268 votes; its author's team scores **2.23**.
   thtennant, who wrote the graft stack everyone forks, scores **1.93**. keithtyser, running
   NVFP4 + MTP, scores **2.36**. Each is a *max over 41–99 draws*. So the entire public
   Qwen3.8 recipe is worth a ~2.0–2.4 best-draw — while the top of the board is 7.51.
   **Cloning the public frontier is the entry ticket, not the win.**
10. **Kaggle *Models* do not mount where Kaggle *datasets* do.** A Model lands at
    `/kaggle/input/models/<owner>/<slug>/<framework>/<variation>/<version>`. The TAAF bundle's
    `resolve_kaggle_dataset_path()` probes only `TAAF_KAGGLE_INPUT_PATHS`, `/kaggle/input/<slug>`
    and `/kaggle/input/datasets/<owner>/<slug>`, then falls through to a non-existent path —
    vLLM dies ~10 min in with the weights mounted and unreachable. The fix is one line in the
    notebook (publish the model ref into `TAAF_KAGGLE_INPUT_PATHS`), and it is testable
    offline by exec'ing the patched setup command's resolver against the real
    `setup_commands.json`. Do that before every model swap.
11. **`maxDailySubmissions = 1` for this track** (competitions API). Public write-ups quoting
    "5/day" are describing ARC-AGI-2. There is no submission-count lever; the only way to
    raise the max draw is to raise the draw distribution.

### The scoring formula, read from the shipped wheel (2026-09-04)
12. **The authoritative scorer is `arc_agi/scorecard.py` inside
    `arc_agi_3_wheels/arc_agi-0.9.8-py3-none-any.whl`** — the wheel the notebook actually
    pip-installs. Verified verbatim:

    ```
    per completed level i:   s_i = min( (baseline_i / actions_i)**2 * 100 , 115 )
    per failed level i:      s_i = 0
    weight_i = level_index (1-based)
    raw       = sum(s_i * w_i) / sum(w_i)          # over ALL levels of the game
    max_score = sum(w_i where s_i > 0) / sum(w_i) * 100
    game      = min(raw, max_score)
    ```

    **Do NOT read `ARC-AGI-3-Agents/.venv/.../arc_agi/scorecard.py`** — that venv holds
    **0.9.1**, which computes a *linear* `(baseline/actions)*100`, caps at **100**, and takes a
    *plain* average with no level weighting. It is three behaviours wrong and it is the copy an
    editor opens first.
13. **On every game we actually score, the CAP binds, not the efficiency term.** Verified against
    the v14 run: `ft09 = 28.57 = 100*(1+2+3)/21` (3 of 6 levels), `ka59 = 10.71 = 100*(1+2)/28`
    (2 of 7), `vc33 = 10.71` (2 of 7) — each equals its cap exactly, which can only happen when
    raw >= cap, i.e. when efficiency is already saturated. **Consequence: efficiency is a solved
    problem for us and depth is the entire remaining score.** A level cleared in <= its baseline
    saturates its contribution; there is no reward for going faster still, and every action
    beyond baseline costs quadratically.
14. **RESET does NOT refund the scored action count — measured, not assumed.** In every
    `benchmark.json` game run, `sum(actions_per_level) == len(history)` exactly, *including* the
    runs that contain a RESET (tn36 96 actions / 1 reset, dc22 98 / 1, tu93 36 / 1). Actions
    accumulate across resets within a level. `deathclock`'s "RESET bought the budget back on 134
    of 134" refers to the **engine's** per-level action limit (`base_game.level_reset` sets
    `_action_count = 0`), which is a different counter from the scorer's. **So exploration is
    never free: an "explore, RESET, then execute cleanly" policy does not clear the denominator,
    and any plan that assumes it does is wrong.** This also explains tn36: 96 actions spent on a
    level with baseline 32 means that even a successful clear would have scored
    (32/96)^2*100 = 11.1, not 115.

## Superseded beliefs
<!-- date | belief we held | what overruled it (result/source) -->
- 2026-07-07 | "Build no-LLM graph exploration; LLM agents are the wrong path (~0.3%)" |
  Milestone-1 winner = LLM+Python-tool harness on a LOCAL 27B model, 1.21 LB vs our graph 0.24.
  The graph-vs-LLM dichotomy was wrong; the real variable is grounding (code tool + segmentation
  + world-model memory) and a strong local model, not LLM-vs-no-LLM.
- 2026-07-07 | "Offline scorer predicts LB direction" (REPORT §3) | v7: offline best (8/183) →
  LB 0.06 (crash). Offline predicts direction only when the kernel survives; runtime robustness
  on Kaggle is a separate, gating axis.
- 2026-07-29 | "Scored-run wall budget is 12h (soft-end 11h20m protects it)" | Organizer
  statement (discussion 729985): v3 scored-run limit is **9 hours**; the 12h figure was a
  docs inconsistency they said they'd fix. An 11h20m soft end can never fire; v12 moves it
  to 8h20m.
- 2026-07-29 | "ACTION7 semantics are unknown/game-specific" | Official ARC-AGI-3-Agents
  repo documents ACTION7 = "Undo" (multimodal.py human_actions: 1=Up 2=Down 3=Left 4=Right
  5=Perform 6=Click 7=Undo); ar25 game code implements it as saved-state pop/restore.
  Games may still deviate, but Undo is the designed convention.
- 2026-07-29 | "Per-level score caps at 1.0 (can never beat baseline)" | arc_agi package
  source (via discussion 728299): per-level = `min((baseline/actions)^2*100, 115)` — an
  agent beating the human baseline pays up to 115. Efficiency above par counts; depth
  still dominates (weighted mean by level index).
- 2026-07-30 | "A single offline Save&Run mean is a reliable promotion gate (n=1)" |
  Two runs of **byte-identical code** (duck v13 and the Kochi Loki rebrand, same hardware,
  same 26 games x 2 passes, 30 min apart) scored **2.49** and **1.71** (medians 0.41 /
  0.31). Per-game: `sk48-dup` = 0.00 in one, 2.78 in the other. Mechanism: analyzer
  read-timeouts against the local vLLM reshuffle which games get budget, and several games
  sit on a give-up/clear coin flip at level 1. **Offline single-run noise is ~0.8 wide —
  larger than any lever we have measured except the ACTION7 fix.** Therefore: a mean delta
  under ~0.8 from one run each is NO EVIDENCE, in either direction. v12's 1.81-vs-2.21
  "failure" was a draw from this distribution, not a measured regression. Promotion now
  needs paired runs or a same-session A/B; live LB evidence (v11's 0.55/0.61) is unaffected
  because that was two independent live draws.
- 2026-07-29 | "Semantic action labels are free capability (ACTION7 renamed UNDO should
  help)" | v12 offline: mean 1.81 vs v10's 2.21, zeros 7→9, sk48 (ACTION7 game) still
  0.00 across 3 runs. The neutral "ACTION7" label already let the model discover usage
  by experiment; naming it "UNDO" changed behavior for the worse (possibly biased the
  model toward undo-probing). Structural-mapping ≠ automatically good — the v10 win was
  about EXECUTABILITY (broken reverse map), not naming.
- 2026-09-02 | "Our stack is at the frontier; the gap to the top is a few tenths of graft
  tuning" | The 07-28 snapshot (top 1.86, #20 cutoff 1.46 = us) was true and is now stale.
  On 09-01 the top is 7.51 and #20 is 2.97 — we are rank 488 of 2694. The whole delta
  arrives from an axis we never varied (the base checkpoint), not from the graft/prompt
  axes this log spent twelve versions on.
- 2026-09-04 | "Completion-at-any-action-cost is a viable fallback (cf. StochasticGoose 12.58%
  in the 2025 preview)" | The preview metric rewarded completion; RHAE squares the efficiency
  ratio. StochasticGoose cleared 18 levels in 255,964 actions ~ 14,000 per level against
  baselines of 20-256, which under the shipped 0.9.8 scorer is s_i ~ 0.000005 per level. Any
  brute-force explorer is structurally worth ~0 here, no matter how many levels it clears.
