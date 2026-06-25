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
