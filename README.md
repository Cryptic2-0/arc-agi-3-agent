# ARC-AGI-3 Agent — GraphExplorer

A no-LLM agent for the [ARC Prize 2026 — ARC-AGI-3](https://www.kaggle.com/competitions/arc-prize-2026-arc-agi-3)
interactive-reasoning competition. Agents must explore novel hidden games, figure out the rules with no
instructions, and clear levels efficiently.

## Result
- **Leaderboard: 0.23 public** (v2), beats the random baseline (~0). Frontier LLMs score ~0.2–0.4%; the
  best preview agent was 12.58%.
- Offline on the 25 public games: clears levels on 6–8 games (vs random's ~0).

## Approach (`agent/`)
Recon ([docs/recon.md](docs/recon.md)) showed the winning agents are grounded **explorers, not LLMs**.
`GraphExplorer` mirrors them:
1. **State = hash of the 64×64 grid** (discrete node id).
2. **Transition graph** `state → move → next_state`, built online as it acts.
3. **Moves:** simple actions (1–5,7) *and* each ACTION6 click target as its own move (object pixels from
   colour-segmentation, small-first) — so click games get genuinely explored, not one random click.
4. **Learn effects:** track which moves change the frame; prune persistent no-ops.
5. **Reward signal:** when a move increases `levels_completed`, boost that move-type's priority.
6. **Online change-predictor** (experimental): Thompson-sampled P(frame-change) per (action, context),
   incl. object-relative click features. See [docs/rl_design.md](docs/rl_design.md).
7. **Policy:** untested move → else BFS to the nearest frontier state with untested moves → else most
   productive move. Fully deterministic (per-instance RNG + sorted tiebreak) for trustworthy A/B.

## Files
- `agent/graph_explorer.py` — the agent (drops into [ARC-AGI-3-Agents](https://github.com/arcprize/ARC-AGI-3-Agents) `agents/templates/`).
- `agent/my_agent.py` — same logic as `MyAgent` for the [ARC-AGI-3-Kaggle-Starter](https://github.com/arcprize/ARC-AGI-3-Kaggle-Starter) submission.
- `agent/run_offline.py` — offline runner: plays the bundled public games locally (no API/quota) using the real scorecard.
- `PROJECT.md` / `LOG.md` / `REPORT.md` / `PLAN.md` — three-layer project memory (state / history / corrected model) + the gated plan.
- `docs/recon.md` — prior-art survey. `docs/rl_design.md` — the next-gen online-learning design.

## Notes
- Eval runs **offline (no internet)** against hidden games, so the agent learns **online, in-game** — no
  pretraining transfers (the games are novel). That rules out a bundled CNN and favours lightweight online learning.
- The two upstream framework repos are gitignored; only the authored files are vendored here under `agent/`.
