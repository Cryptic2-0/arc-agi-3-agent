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
