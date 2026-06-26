# PROJECT.md — State Map

> The current truth. Goal, status, key decisions. Overwrite freely as reality changes.
> Readers: future-me at the start of any session. Keep it short and *current*.
> (Layer 2 of 3 — see [LOG.md](LOG.md) for history, [REPORT.md](REPORT.md) for the corrected mental model.)

---

## Goal
<!-- Rule 1: state THE number and how it is computed. -->
**ARC-AGI-3 (ARC Prize 2026, Kaggle).** Build an agent that plays unseen interactive grid
games and completes levels in few actions.

THE number = **Total score (0–100%)**, computed:
- Per-level: `min(human_actions / agent_actions, 1.0)`, then **squared**. (0.5 raw → 0.25.)
  Unsolved level = 0. Squaring punishes action-inefficiency hard.
- Per-game: level-score average **weighted by level index** (1-indexed → later levels worth more).
- Total: plain mean across all games.
- Eval set: **110 private games, never seen** (55 → public LB, 55 → private LB). 25 public
  games shipped locally (`environment_files/`) for dev only.

## Status
- **Phase:** steps 1,3,4,5 ✅; step 2 measured; **v1 solver built + measured (steps 7–8)**;
  **first Kaggle submission pushed (step 6, Phase A).**
- **Pipeline (dev):** OFFLINE harness — `cd ARC-AGI-3-Agents && python -m uv run run_offline.py --agent=graphexplorer`
  (`.env`: `OPERATION_MODE=offline`, `ENVIRONMENTS_DIR=<abs>/environment_files`). Local scorecard = real metric.
- **Pipeline (submit):** `ARC-AGI-3-Kaggle-Starter/` — edit `agent/my_agent.py` → `python scripts/build_notebook.py`
  → `KAGGLE_API_TOKEN=$(cat .kaggle/access_token) python -m kaggle kernels push -p notebooks/` → manual
  "Submit to Competition". No `make` on Windows (call scripts directly). `ACCELERATOR=cpu`. User=`soumyacryptic`.
- **Last result (offline):** **v2 = 7/183 levels across 6 games** (vc33 2, ar25/lf52/m0r0/r11l/sp80 1 each)
  vs v1's 3/183 across 2. v2 generalizes ACTION6 into per-object click targets. Regression: sp80 2→1, ft09 1→0
  (ACTION6 targets crowd out simple-action exploration — v3 fix). Recon ([docs/recon.md](docs/recon.md)):
  no-LLM graph exploration is right (LLMs ~0.2–0.4%; best preview 12.58%).
- **Kaggle LB:** v1 **0.17** → v2 **0.23** → **v4 = 0.24** (best; sub `54035711`). Submit via CLI (LIMIT 1/DAY,
  resets UTC midnight): `kaggle competitions submit ... -k <kernel> -v <N> -f submission.parquet`.
  Kernel `soumyacryptic/arc-prize-2026-arc-agi-3-starter`. Today's slot used on v4.
- **GitHub:** https://github.com/Cryptic2-0/arc-agi-3-agent (private; repo root = `c:/Users/ASUS/Desktop/ARC-AGI`).
- **Token:** `KGAT_…` = the **Kaggle access token** (valid). Not an arcprize key. Or use Kaggle MCP next time.
- **Iterations:** v3 (simple-first) regressed → reverted. v4 = **reward-from-level-ups + full determinism**
  (per-instance RNG + sorted tiebreak). Deterministic A/B: reward-ON 7/183 vs OFF 6/183 (small genuine +).
  Pushed as **kernel version 3** (auto-submitting). Budget probe: more actions ≠ more depth (strategy-bound).
- **Measurement caveat:** offline metric is HIGH-VARIANCE (~6–10/183 across trajectories before the
  determinism fix). Treat deltas <~3 levels as noise. Now deterministic → trustworthy going forward.
- **Next action:** record v4 LB score. Direction 2 = **RL frame-change predictor** (the 12.58%-winner approach;
  CNN+RL, needs training/GPU on Kaggle) — the real ceiling-raiser, a big multi-session build to scope next.
  Exploration agent appears plateaued ~6–10/183 offline; ls20-type alignment puzzles still need reasoning.

## Key decisions
| Date | Decision | Why |
|------|----------|-----|
| 2026-06-23 | Scaffold three-layer memory + 10-step plan before writing code | Playbook Rule 13 / step C; avoid relearning across sessions |
| 2026-06-23 | Defer objective definition | User chose "just scaffold the structure" |
| 2026-06-23 | Objective set = ARC-AGI-3 (interactive games, action-efficiency score) | User pasted official Kaggle competition spec |

## Binding constraint (current hypothesis)
<!-- Rule 3: only one or two limits actually bite. Name the suspect, mark it UNMEASURED. -->
**Hypothesis (UNMEASURED): in-context skill acquisition on a novel game = the gate, not compute.**
Reasoning: an unsolved level scores 0, so completion dominates. Each game has *unknown* action
semantics (ACTION1–7 meaning differs per game; ACTION6 needs x,y) — the agent must *discover*
the rules by exploration, with no training examples. Secondary gate: action-efficiency vs human
(the squaring), which only matters *after* a level is solvable. Suspected secondary limits if
using LLM-driven agents: per-action latency / token budget (long games × many frames), and
API rate limits. Default code cap `MAX_ACTIONS=80` ([agent.py:22](ARC-AGI-3-Agents/agents/agent.py#L22))
— a code default to tune, NOT a contest rule.
→ MEASURE in step 2: where do random/LLM baselines actually fail — never solving, or solving but inefficiently?
**MEASURED (n=1, 2026-06-23):** random agent clears **0/7** levels on ls20 → failure = *never solving*,
NOT inefficiency. Confirms completion is the gate; efficiency/squaring is irrelevant until a solver
can clear level 1. Still UNMEASURED across more games + with a smarter (LLM/search) agent.

## Open unknowns
- ~~What is the goal / objective function?~~ ✅ defined above.
- Per-game action limit & per-run time/$ budget on the real eval harness (not just code default 80).
- Local (`arc_agi`) vs `ONLINE_ONLY` API: which does Kaggle scoring use? Rate limits?
- What prior art already solves most of this? (PLAN step 3 not yet run)
- Are the 25 public games representative of the 110 private ones? (over-fitting risk)
