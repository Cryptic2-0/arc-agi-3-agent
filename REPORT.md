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

## Superseded beliefs
<!-- date | belief we held | what overruled it (result/source) -->
*(none yet)*
