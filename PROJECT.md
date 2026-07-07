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

## Status  (rewritten 2026-07-07 — STRATEGY PIVOT)
- **Phase:** GraphExplorer line RETIRED (plateaued 0.24; v7 crashed on LB = 0.06). **Pivoted to
  the open-sourced milestone-1 winner: Tufa Labs "duck harness"** (LLM agent, local Qwen3.6-27B-FP8
  on vLLM, RTX Pro 6000). A verbatim public fork scores **1.21** — 5× our best.
- **LB context (2026-07-07):** top = **1.56**; top-20 ≥ 1.30, nearly all duck-harness forks.
  Ours: v4 = 0.24 (sub `54035711`). v7 = 0.06 (crashed; never diagnosed, moot).
- **In flight:** private fork **`soumyacryptic/taaf-duck-harness-fork` version 1** pushed
  (verbatim 1.21 notebook; datasets: `driessmit1/arc3-vllm-h100-wheelhouse-v3`,
  `jeroencottaar/taaf-kaggle-source`, `driessmit1/vrfai-qwen3-6-27b-fp8-hf-snapshot`;
  `machine_shape: NvidiaRtxPro6000`; internet OFF). Save&Run takes hours (plays 25 offline games).
  **When complete → submit** (1/day slot, free as of 2026-07-07):
  `kaggle competitions submit arc-prize-2026-arc-agi-3 -k soumyacryptic/taaf-duck-harness-fork -v 1 -f submission.parquet`
- **Winner source code:** `external/taaf_source/` (TAAF framework + ARC3-Inference "duck").
  Writeup: Kaggle discussion 717133. Improvement levers named by authors: context
  compaction/memory, better visual perception, better base model. Variance ±0.4 — don't
  over-read single LB results.
- **Pipeline (dev, old graph line):** `cd ARC-AGI-3-Agents && python -m uv run run_offline.py --agent=graphexplorer`.
  Still useful as cheap baseline/fallback layer.
- **Token:** `KGAT_…` = Kaggle access token at `ARC-AGI-3-Kaggle-Starter/.kaggle/access_token`.
  CLI: `export KAGGLE_API_TOKEN=$(cat .kaggle/access_token)`. User=`soumyacryptic`.
- **GitHub:** https://github.com/Cryptic2-0/arc-agi-3-agent (private).
- **Next actions:** (1) submit fork v1 when run completes → establish ~1.2 baseline;
  (2) study `external/taaf_source/` deeply (prompts.py, tool_agent.py, solver.py);
  (3) iterate via the notebook's customization hook (cell "6. Customization hook"): prompt
  tweaks, per-game budget, context compaction — validate on the 25 offline games before each
  submit; (4) milestone 2 = Sept 30 ($37.5K pool), final = Nov 2.

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
