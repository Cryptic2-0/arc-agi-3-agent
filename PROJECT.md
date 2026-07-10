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

## Status  (updated 2026-07-09 — v2 LB 0.57, v3 thinking-off in flight; best = 1.07)
- **Phase:** duck-harness fork line. **Best LB = 1.07 (v1, sub `54414740`)**. v2 (game-over
  prompt fix) offline mean 1.01/median 0.17/16-of-25 scoring but **LB 0.57** — 1-pass LB draw
  at ±0.4 variance; standing unaffected (LB keeps best). GraphExplorer retired (0.24).
- **LB context (2026-07-07):** top = **1.56**; top-20 ≥ 1.30, nearly all duck-harness forks.
- **Key measurement (v2 transcripts):** thinking eats ~85% of the ~70k generated-token budget
  per game → only ~150 env actions/game, avg batch 1-2. Completion gates score → **action
  throughput is THE binding constraint**. Yield 60s = max turn duration, not a floor.
- **v3 (thinking OFF) offline = 0.86/0.08 — REJECTED, not submitted.** Actions only 1.48× up
  (tok/s dropped 224→178: wallclock overhead binds when replies are short, not GPU decode);
  planning games collapsed (ka59/lp85/su15 down) while exploration games jumped (ar25 3.33,
  ls20 1.09, cd82/cn04 first nonzero; zeros 8→6). Lesson: act-bias prompts → breadth,
  thinking → depth; need both.
- **v4 (thinking ON + act-bias/batching addendum) offline = 1.35/0.30/20-of-25 — BEST of the
  line. SUBMITTED 2026-07-10 04:25 UTC (sub `54515519`, kernel version 4), PENDING.** Depth
  kept (ka59 3.24, tu93 4.11) + breadth gained (ft09 0→2.12, cd82 0→1.85, sc25 first nonzero
  1.17; zeros 8→5). Caveats: 2-pass mean (noisier); offline→LB correlation loose (v2: 1.01
  offline → 0.57 LB).
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
- **Next actions:** (1) check sub 54515519 publicScore when it resolves; (2) study remaining
  zeros dc22/g50t/sk48/tr87/wa30 (sk48 721 actions/0 levels + wa30 578/0 = flailing loops;
  dc22 94 actions = indecision) in output_v4 transcripts; (3) later levers: per-turn output
  cap (~3k) to cut thinking tail, partial thinking (needs thread-safe patch), context
  compaction quality at 32k, tool-output budget (1024 tok), base-model swap;
  (4) milestone 2 = Sept 30 ($37.5K pool), final = Nov 2.

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
