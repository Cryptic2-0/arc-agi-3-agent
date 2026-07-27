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

## Status  (updated 2026-07-27 — **v11 LIVE DRAWS BAD: 0.55 (07-26, ref 54995834) + 0.61 (07-27 cron, ref 55017907) vs v10 lineage 1.46/0.89 → v11 DEMOTED, daily default REVERTED to v10** (`submit_config.json` version 10). Best LB stays **1.46, inside top 20**. Auto-submit cron VERIFIED live: 07-27 run fired at 04:03 UTC (GitHub cron lag ~3.7h — normal, slot still claimed). **GATE FIX (n=1 lesson): old gate accepted mean drop "within noise" on median gain — wrong; LB metric IS the mean. New promotion rule: offline mean must be ≥ incumbent mean (median = tiebreak only), and prefer 2 independent Save&Run passes before promoting.** Remaining queue: recovery-OFF A/B, fast-save cadence, capability levers for 5 zeros (sk48/m0r0/s5i5/tr87/g50t).)
- **Phase:** duck-harness fork line. **Best LB = 1.46 (v10 = v5 + ACTION7 reverse-map
  fix, first draw)**. v5 draw ceiling was 1.31 over 6 draws. GraphExplorer retired
  (0.24). Stack = Tufa grafts (banking/transfer/shortcircuit/recovery/retry_guard ON,
  prompts VERBATIM, efficiency OFF) on the readable-share bundle + ACTION7 fix (v10)
  + context 40960/concurrency 20 (v11, offline 1.99/0.95). Structural-lever rule n=2:
  grafts 1.07→1.31, ACTION7 1.31→1.46.
- **Inversion pattern RESOLVED (n=3):** v2/v4 (prompt mods) beat verbatim offline, lost on
  LB (0.57/0.78); v5 (structural grafts, verbatim prompts) beat offline AND LB (1.20>1.07).
  Working rule: prompt-margin tweaks = LB losers; structural levers + verbatim prompts win.
- **LB context (2026-07-12):** top = **1.56** (×3: Mathurin Ache/anngle/NoOneAhead); top-20
  cutoff 1.36; tie clusters = teams resubmitting the same notebook daily (LB keeps each
  team's max draw) → **submit every day**. 07-12 slot: v5 resubmitted verbatim
  (sub `54598846`, PENDING).
- **Upstream recon (2026-07-12, extended 07-14):** thtennant kept iterating: v8 = +shortcircuit,
  v9/v9b = +recovery+banking (never transfer), **v10 = REVERT to v7 flags**
  {efficiency, retry_guard}, **v11 (07-12) = v10 + wall-budget slack-filler**: rerun plays
  110 games / 28-way at 7920s/game ≈ 8.6h of a 12h kernel → scale per-game budget to
  min(9900s, avail·conc/n_games) to fill the idle ~2.5-3h; fail-safe try/except keeps stock.
  **07-14 sweep:** v12=+shortcircuit, v13=+recovery, **v14 (07-14)=transfer(+banking),
  "recovery deliberately OFF" after one day** — first external evidence against recovery
  (our v5 runs it ON) → A/B candidate. Full sweep (safety pack, fast-save, dead-signature
  guard, duck env-knob surface, forum facts): [docs/recon.md](docs/recon.md) ADDENDUM
  2026-07-14. Key forum numbers: Tufa best LB 1.21 (their 1.30 was RETRACTED), public
  1.6 ±0.45, same-notebook draws to 0.77 → our 1.31 exceeds their best counted draw.
  Games are deterministic/stable-seeded (Kamradt) → banking/transfer replay is sound.
- **v6 LB = 0.55 (sub `54637379`, resolved 07-13) — bad draw; best stays 1.31.** Offline
  v6 was 1.50/0.03 (clean, transfer replay proven). Read: fat-tail draw noise (cf. v2
  0.57, v4 0.78); mechanistically v6 ⊇ v5, but the budget filler is 0-for-1 on LB and
  ~0 EV offline (zeros are capability-bound). Learning: raise the DRAW distribution
  structurally (max-over-plays), don't spend slots on single-play variants.
- **v7 REJECTED (validated 2026-07-12 20:07 UTC): mean 0.40 / median 0.00** (vs v6 1.50,
  v5 1.60; 8/26 games scored). The swap was real (banner + model path in log) and the
  speed thesis held — 412 tok/s (~2× the 27B's 206), ~150k tokens/game — but the MoE's
  ~3B ACTIVE params can't do duck-grade grid reasoning. **Rule: model capability tracks
  active params, not total/throughput; throughput was never the binding constraint.**
  Next model candidates need ≥27B active or proven ARC-grid reasoning. The deployed duck
  is ALREADY multimodal (grid PNG per prompt) — do NOT swap to a text-only model, ever.
  Also discovered: `LOCAL_ANALYZER_MAX_OUTPUT` env = per-turn output cap knob (0 =
  uncapped today) for a future A/B. NOTE: kernel version 7 = rejected MoE; the good v6
  notebook = kernel **version 6** (what submit_v6.ps1 pins with `-v 6`).
- **v8 (sidecar) RETIRED (validated 2026-07-13): mean 1.34** (noise-level vs v6 1.50);
  explorer ran on every failed play and advanced a level on 3 (incl. g50t 0→1) but
  raw env.step level-ups are NOT credited to run records, and sloppy ~1000-action
  clears score (h/1000)²≈0 anyway. Paradigm survey: [docs/recon.md](docs/recon.md)
  ADDENDUM 2026-07-12. Also measured dead: analyzer output cap (outputs already ≤5k),
  retry-on-give-up (gave_up = budget exhaustion, zero residual time), compaction
  demoted (history/transitions fully exposed in sandbox; eviction loses only
  reasoning).
- **v8/v9 two-pass line CLOSED (07-14): LB 0.00 (sub `54676947`, resolved <5h — rerun
  collapsed early).** Root cause from framework source: **competition scorecards allow
  ONE run per game ID** (competition_arcade.py:66) and one card per submission;
  benchmark.py opens every pass of every game up front → v8's 220 opens put a duplicate
  of each game_id on the shared card → dead sessions → fast-dying runs → zeroed card.
  Offline never sees this (OFFLINE mode = per-game scorecards). **The mean-of-max
  numbers (2.71 / 1.04, pass1 ≥ pass0 everywhere) measured an offline-only mechanism:
  a fresh play is only legal from WIN (banking's primitive) — an un-won game can never
  get a second play on the live card (not concurrent, not sequential, no second card).**
- **NEW VALIDATION RULE:** the bundle ships `CompetitionArcadeServer.official_110()` /
  `competition_sim` (game_api.py, competition_arcade.py) — a local submission-shaped
  arcade (one card, one run per game ID, hidden baselines, 110 cloned IDs) built to
  reproduce exactly these failures. Any rerun-shaped change (passes, budget, scorecard,
  session lifecycle) validates there BEFORE a slot is spent. v8 would have failed it.
- **Ops lessons:** scheduled task fires late after machine sleep (WakeToRun needs wake
  timers) and can be killed on wake → morning check-in is the reliable submit path;
  `PYTHONUTF8=1` required for `kaggle kernels push`.
- **TEAM facts (2026-07-12):** teammate = `satadruhalder` (same Kaggle team — his token
  sees our submission list). Daily submission limit is PER TEAM (1/day) — a teammate has
  NO extra slot. His value = separate 30h/week GPU quota for parallel Phase-A validation.
  Never push private kernels to non-team accounts.
- **Later candidates (zeros need capability, not time):** context compaction quality
  (evict→summarize), per-turn output cap ~3k A/B (`LOCAL_ANALYZER_MAX_OUTPUT` env knob
  exists). Banking has never fired (0 full wins in 104 runs).
- **v5 graft evidence (offline):** recovery fired 8 refreshes + 24 level handoffs; banking
  idle (0 full wins in 52 runs); transfer machinery live but never published (dup sk48
  never cleared). Zeros 5→8 (ls20/m0r0/cn04 flipped to 0) but mean/median way up; bundle
  switch confounds per-game deltas.
- **Env note (2026-07-12):** project moved to a new Windows machine (`C:\Users\user`,
  PowerShell). Old venvs dead (pointed at `C:\Users\ASUS`). Tooling now: `uv` at
  `~\.local\bin\uv.exe`, kaggle CLI 2.2.3 (`uv tool install kaggle`), auth =
  `$env:KAGGLE_API_TOKEN` from `ARC-AGI-3-Kaggle-Starter\.kaggle\access_token`; Kaggle REST
  via `Authorization: Bearer <token>` also works. Harness venv (ARC-AGI-3-Agents) broken;
  `uv sync` to rebuild if local offline runs are needed. LOCAL notebook copy was STALE (v4)
  — canonical source of truth = `kaggle kernels pull`; local
  `external/my_duck_fork/taaf-duck-harness-fork.ipynb` now holds v6.
- **Key measurement (v2 transcripts):** thinking eats ~85% of the ~70k generated-token budget
  per game → only ~150 env actions/game, avg batch 1-2. Completion gates score → **action
  throughput is THE binding constraint**. Yield 60s = max turn duration, not a floor.
- **v3 (thinking OFF) offline = 0.86/0.08 — REJECTED, not submitted.** Actions only 1.48× up
  (tok/s dropped 224→178: wallclock overhead binds when replies are short, not GPU decode);
  planning games collapsed (ka59/lp85/su15 down) while exploration games jumped (ar25 3.33,
  ls20 1.09, cd82/cn04 first nonzero; zeros 8→6). Lesson: act-bias prompts → breadth,
  thinking → depth; need both.
- **v4 (thinking ON + act-bias/batching addendum) offline = 1.35/0.30/20-of-25 — best offline
  of the line. LB = 0.78 (sub `54515519`, resolved 2026-07-10).** Depth kept (ka59 3.24,
  tu93 4.11) + breadth gained (ft09 0→2.12, cd82 0→1.85, sc25 first nonzero 1.17; zeros 8→5)
  — but LB below v1's 1.07. See CRITICAL PATTERN above.
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
- **v9 PUSHED 2026-07-14 17:10 UTC (Save&Run RUNNING):** = v5 with the LIVE path
  byte-identical (diff asserted: every new line behind `not TRUE_SUBMISSION`) +
  offline Save&Run swapped to the **competition_sim commit gate**: 4 cloned runs
  (k000=ar25, k001=ka59, k002=tu93, k003=ar25-clone) on ONE shared card, one run
  per game ID, n_passes=1, ~2-3h. k000/k003 share the initial-frame fingerprint →
  transfer publish→replay exercised ON the shared card. Fault → stock v5 offline
  validation. NOTE: the 11h20m live soft-end "safety pack" was ALREADY in v5
  (cell 14) — queue item (a) was half-done all along. Validation gates when it
  completes: `TAAF_V9 COMMIT_GATE` + `TAAF_GRAFTS` banners in the log; 4 clean
  game_runs in benchmark.json; wall ~2-3h (9-10h = gate fell back); transfer
  replay evidence on k003. If clean → v9 becomes the default daily submit (it IS
  a v5 draw live) and the template for all future levers. v5 notebook preserved
  at `external/my_duck_fork/taaf-duck-harness-fork.v5.ipynb` (recovered from the
  ae40551e session scratchpad — Kaggle API cannot pull old versions; keep local
  .vN backups from now on).
- **Next actions:** (1) DONE 07-27: v11 draws 0.55/0.61 = bad → `submit_config.json`
  reverted to version 10 (v11 KILLED as default; context lever failed live);
  cron verified fired (04:03 UTC run claimed the 07-27 slot); (2) apply NEW GATE
  RULE to all future promotions: offline mean ≥ incumbent mean (median tiebreak
  only), 2 Save&Run passes preferred; (3) remaining queue from
  [docs/recon.md](docs/recon.md) ADDENDUM 2026-07-14: (d) recovery-OFF A/B (upstream
  v14 dropped recovery "deliberately"), (b) fast-save pattern for pre-validated
  configs → same-day cadence; (4) capability levers for the 5 remaining zeros
  (sk48/m0r0/s5i5/tr87/g50t) — compaction quality, per-turn output cap A/B; (5) any
  rerun-shaped experiment → competition_sim first; (6) milestone 2 = Sept 30
  ($37.5K pool), final = Nov 2.

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
