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

## Status  (updated 2026-07-07 evening — duck fork = 1.07 LB; v2 in flight)
- **Phase:** duck-harness fork line. **v1 (verbatim fork) = 1.07 public LB** (sub `54414740`;
  offline mean 1.11, 14/25 games at 0, 0 games fully won). GraphExplorer retired (best 0.24).
- **LB context (2026-07-07):** top = **1.56**; top-20 ≥ 1.30, nearly all duck-harness forks.
  We're at 1.07 with zero customization → headroom is real.
- **In flight:** **kernel version 2** (Save&Run started 2026-07-07, ~7h: 3 offline passes).
  v2 = customization-hook-only patches fixing the **post-game-over paralysis** found in v1
  transcripts: harness auto-resets after GAME_OVER but prompt said only "The game is over." →
  model refused to act for rest of run (ls20 20/61 turns idle, ft09 14/66). Patches: explicit
  auto-reset messaging in user prompt + system-prompt game-over addendum + `bm.n_passes=3`
  (offline only). Monitor: `external/my_duck_fork/monitor_v2.sh`.
  **Decision rule:** submit v2 only if 3-pass mean ≥ 1.11 AND ls20/ft09/sc25/cn04/m0r0/r11l
  don't regress. Submit: `kaggle competitions submit arc-prize-2026-arc-agi-3 -k soumyacryptic/taaf-duck-harness-fork -v 2 -f submission.parquet`
- **Winner source code:** `external/taaf_source/` (TAAF framework + ARC3-Inference "duck").
  Writeup: Kaggle discussion 717133. Improvement levers named by authors: context
  compaction/memory, better visual perception, better base model. Variance ±0.4 — don't
  over-read single LB results.
- **Deployed config facts (from bundle + solver.pkl):** analyzer context **32k** (vLLM
  max_model_len 64k), concurrency 28, 7920s/game, unlimited tool steps, temp 0.6, top_p 0.95,
  prefix caching on, yield 60s. All games run concurrently → binding constraint = aggregate
  GPU decode (~9 tok/s/game, ~70k tokens/game/window). Tunables all reachable from the
  notebook's customization hook (cell 8): monkey-patch `inference.agent.tool_agent` (prompts,
  `_build_system_prompt`, module constants) + `bm`/`bm.solver` fields — ToolAgent instances
  are created per-game AFTER the hook runs (solver.py:1189).
- **Pipeline (dev, old graph line):** `cd ARC-AGI-3-Agents && python -m uv run run_offline.py --agent=graphexplorer`.
  Still useful as cheap baseline/fallback layer.
- **Token:** `KGAT_…` = Kaggle access token at `ARC-AGI-3-Kaggle-Starter/.kaggle/access_token`.
  CLI: `export KAGGLE_API_TOKEN=$(cat .kaggle/access_token)`. User=`soumyacryptic`.
- **GitHub:** https://github.com/Cryptic2-0/arc-agi-3-agent (private).
- **Next actions:** (1) when v2 Save&Run completes → compare 3-pass mean vs 1.11 + per-game
  on the game-over set → submit v2 if decision rule passes (slot resets UTC midnight);
  (2) next levers, in rough order: dc22-style indecision (99 tool calls, 44 actions — model
  investigates forever), context compaction quality at 32k, tool-output budget (1024 tok),
  temperature sweep, stronger base model swap; (3) milestone 2 = Sept 30 ($37.5K pool),
  final = Nov 2.

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
