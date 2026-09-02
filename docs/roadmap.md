# roadmap.md — 10 improvement steps (cut 2026-09-02)

> Ordered by **expected value ÷ cost**, not by ambition. Every claim here is backed by a
> measurement in [LOG.md](../LOG.md) or by source read out of the attached bundle; where a
> claim is unverified it says so.
>
> Budget reality: **1 submission/day** (API-verified `maxDailySubmissions=1`), **30 h/week GPU**
> (~6 Save&Run passes of 4.4 h, 2 runnable in parallel), **28 days to milestone 2 (Sept 30)**,
> **61 to final (Nov 2)**. Offline single-run noise is **±0.8** — nothing gets promoted on one
> unpaired run (GATE RULE v2).
>
> Status: ⬜ not started · 🟡 in flight · ✅ done

---

## Where we are

| | value | source |
|---|---|---|
| public LB | **1.46**, rank 488 / 2694 | leaderboard CSV 09-01 |
| LB top / #20 cutoff | 7.51 / 2.97 | same |
| offline mean, v14 (Qwen3.8) | **3.61** (median 1.51, 22 levels, 7 zeros) | `out_v14/summary.txt` |
| offline mean, incumbent (Qwen3.6) | 2.49 / 1.71 on byte-identical code | LOG 07-30 |
| daily default | Kochi Loki **kernel version 2 = v14** | `submit_config.json` |
| first live Qwen3.8 draw | **09-03 cron** | pending |

**The diagnosis that reorders everything.** Using the real per-level human baselines in
`environment_files/*/*/metadata.json`, the 7 zero-scoring games split in two:

```
ACTION-STARVED (took fewer actions than the level-1 human baseline —
                could not have cleared level 1 playing perfectly):
  m0r0   23 actions vs baseline  30      wa30   28 vs 71
  sk48   35              vs 61           g50t   57 vs 78

REAL FAILURES (had 2.5–3.4x the baseline and still never cleared):
  sc25  121 vs 36        sp80  104 vs 39        tn36   79 vs 32
```

**4 of 7 zeros are throughput failures, not capability failures.** That is why steps 3, 4 and 6
below — all pure plumbing — outrank every "make the agent smarter" idea.

---

## ⬜ 1. Confirm v14 live before building on it  *(cost: 0)*

The 09-03 cron fires the first Qwen3.8 draw. Do nothing until it resolves.

- **Why:** our own rule — *offline-best ≠ LB-safe*. v7 was the best offline agent we ever had
  and drew **0.06** live, because offline never sees a kernel that dies on hidden games.
  A 3.61 offline mean is not a live result.
- **GATE:** draw ≥ 1.46 (our best-ever) → the model swap is confirmed and steps 2–5 build on
  solid ground. Draw < 1.0 → stop and diff the live path; something in the Qwen3.8 route
  behaves differently on the 110-game competition arcade than on the 25-game offline set.

## ⬜ 2. Turn on `deathclock`  *(cost: 1 flag + 1 paired Save&Run)*

Single highest-value unflagged lever. It is already in the bundle we mount, and it is in
**no** flag set — not upstream's v30, not our v15.

- **Evidence:** upstream probed all 150 public levels — **134 of 150 end themselves within 400
  actions** (median limit 100, range 20–256), and **RESET refunded the budget on 134 of 134**.
  13 of 52 archived passes hit `GAME_OVER`. On tn36 it lands on action **61 in eleven passes of
  eleven**. When it fires, non-RESET actions no-op, the runner auto-RESETs, the level's opening
  board is restored, everything built on it is discarded, and the level counter does not move.
  The agent is told none of it — `current_frame.step` counts the whole run, never the level.
- **Why it should pay for us:** tn36 is one of our three *real* zeros, and level 0 of it is
  clearable in 18–34 actions. Nine archived passes burned an entire life exploring; the one that
  treated life two as an execution run scored **8.646**.
- **Safety:** it only reports (the restart, the measured limit as a countdown, the offline census
  as a prior, and the falsification when a level outruns the longest known limit). It never
  suppresses an action or recommends RESET — deliberately, citing the 08-22 finding that an
  inert-action suppressor would have killed the only fresh-level clear in the archive.
- **GATE:** paired same-session A/B vs v14. Watch tn36, sc25, sp80 specifically.

## ⬜ 3. Enable MTP speculative decoding  *(cost: setup-command edit + 1 run)*

`mtp.safetensors` (477 MB) **ships inside the checkpoint we already mount**, and our vLLM launch
ignores it — no `--speculative-config`, no `--num-speculative-tokens`.

- **Why:** throughput is 4 of our 7 zeros (see diagnosis above). keithtyser serves 3-token NEXTN
  MTP and is the **best public swapper on the board (2.36)** against thtennant 1.93 / FOYSAL 2.23.
  Tokens/s converts near-linearly into actions/game, and actions convert near-linearly into
  cleared levels while we sit below the human baseline on 4 games.
- **Unverified:** whether vLLM 0.19.0 in the pinned wheelhouse drives this MTP head for this
  architecture. Check that **before** spending a session.
- **GATE:** tok/s up ≥25% (baseline: v14 = 246) with no mean regression beyond noise.

## ⬜ 4. Tune the vLLM scheduler  *(cost: setup-command edit, pair with step 3)*

Every scheduler knob is currently a vLLM default, driving 28 concurrent games. keithtyser tunes
five and measured a winning profile (`kv5-bf16-mtp3-c8-cg32`):

```
prefix caching        OFF   (ours: --enable-prefix-caching, ON)
kv cache memory       5 GB
max_num_seqs          8
max_num_batched_tokens 8192
max cudagraph capture 32
OMP threads           1
```

- **Note:** his profile was measured on a different checkpoint and his own runtime, so it is a
  starting point, not a drop-in. Prefix-caching OFF is the single most surprising entry and the
  first to test.
- **GATE:** same as step 3; these two share a run.

## ⬜ 5. Re-open the prompt lever on Qwen3.8 — "explore then execute"  *(cost: 1 paired run)*

Our `REPORT.md` rule *"prompt-margin tweaks = LB losers"* is **n=3, and all three datapoints were
measured on Qwen3.6** (v2 → 0.57, v4 → 0.78, v3 rejected offline). We no longer run that model.

- **Why it is now live again:** the entire Qwen3.6 → 3.8 delta is post-training for
  instruction-following and agentic behaviour — **DeepSWE 13.3 → 42.2**. A model that got ~3×
  better at following multi-step procedural instruction is precisely the case where "the prompt
  didn't stick" stops being true. Treat the rule as **expired until re-measured**.
- **What to put in:** the one concrete game-agnostic procedure we have evidence for —
  explore in life one, execute in life two (tn36: the only pass that did this scored 8.646);
  a mandated one-time sweep of every base action before hypothesising; fill the 7-field world
  model every turn (it is currently non-empty on **33 of 481 turns**); shorter reasoning per
  action (97.6–98.3% of generated tokens are reasoning).
- **This step also settles the fine-tune question.** If the procedure can be *told*, there is no
  reason to train it in. If it does not stick, that is the first real evidence that it has to go
  in the weights — and only then is a LoRA line justified.
- **GATE:** paired vs v14 in the same session so the ±0.8 noise cancels.

## ⬜ 6. Close the wall-budget deficit  *(cost: arithmetic + `competition_sim`; possibly 0 GPU)*

Possibly the largest free win on this list, and it is invisible offline because the offline set is
25 games and concurrency is 28 — everything runs in one wave.

```
game-seconds NEEDED     110 games × 7920 s        = 871,200
game-seconds AVAILABLE   28 slots × 30,000 s      = 840,000    (our 8h20m soft end)
deficit                                           ≈  31,200    ≈ 4 games' worth
```

**Roughly four games' worth of budget does not exist on every live run.** A game that never gets
played is a guaranteed zero — strictly worse than any failure mode we have been diagnosing.

- **Unverified, and it gates everything here:** that the solver schedules as a pool where a freed
  slot admits the next queued game. That matches `concurrency=28` semantics but the scheduler has
  not been read.
- **Fixes, cheapest first:** raise the soft end toward the 9 h organizer limit (currently 8h20m,
  chosen as tail insurance when the wall was believed to be 12 h); or lower
  `max_runtime_s_per_game` below 7920 so 110 games fit; or let games that provably cannot clear
  level 1 release their slot early.
- **GATE:** reproduce the deficit in `competition_sim` (110 cloned IDs, one shared card) before
  changing anything live. Any rerun-shaped change goes through the sim — that rule exists because
  v8 drew **0.00** on a scorecard mechanic offline could not see.

## ⬜ 7. Re-mirror the upstream bundle  *(cost: 1 command — currently blocked)*

v14/v15 attach `thtennant/taaf-kaggle-source-share-fork` **directly**. He deleted it once already,
on 07-28, which is why the mirror exists at all.

- A byte copy of the 09-01 snapshot is saved at `external/fork_bundle/` (gitignored).
- `kaggle datasets version` was refused by the local sandbox during the v14 build. Needs a Bash
  permission rule, then it is one command.
- Same exposure on the weights: `foysalemonshanto/qwen3-8-27b-fp8-repacked-v1` is a third-party
  upload that the entire top of the leaderboard depends on. `mikedan7/qwen3-8-27b-fp8-official`
  is an unmodified mirror of the same revision — worth pinning as a documented fallback.
- **GATE:** `kaggle datasets version` succeeds; `submit_config.json` still points at a kernel
  whose Save&Run passed.

## ⬜ 8. Set `LOCAL_ANALYZER_TIMEOUT`  *(cost: 1 env line)*

It is **not set** → defaults to `0.0` → `self._timeout = None` → **HTTP requests to vLLM have no
client-side timeout.** The only guard is `bm.solver.analyzer_timeout = 900.0` at the solver layer.

- **Why:** our 07-30 finding blamed exactly this — analyzer read-timeouts against the local vLLM
  reshuffling which games get budget — for the ±0.8 offline noise that has been grading our levers
  as noise. keithtyser pins his at 900 s explicitly.
- Cutting variance is worth less than raising the mean when the LB keeps the max draw, but a
  stalled request loses **whole games**, and those are guaranteed zeros.
- **GATE:** ships alongside step 3/4 (same setup-command edit); watch run-to-run spread across the
  next two paired sessions.

## ⬜ 9. Build the diagnosis toolchain  *(cost: 0 GPU)*

Replace the hand-maintained zero list with something reproducible. We are sitting on data we have
barely used:

- **Full Python source of all 25 public games** (`environment_files/<game>/<hash>/<game>.py`,
  3.9 MB, real `arcengine` code — sprites, levels, win/lose conditions; identifiers obfuscated,
  logic intact).
- **Per-level human baselines** in each `metadata.json` (`baseline_actions`), plus tags
  (`keyboard` / `click` / `keyboard_click`).
- **Two fresh full runs**, 267 MB each: 52 transcripts, 52 prompt logs, 104 artifacts
  (`_events.jsonl` + `_viewer_data.json`), 102 movies, 52 solver-analysis HTMLs.

Build: (a) a classifier over `benchmark.json` bucketing every game into *starved / flailing /
never-understood* using `actions ÷ L1_baseline`; (b) our own re-derivation of the per-level
action-limit census from the game source, so `deathclock`'s prior is verified rather than
inherited; (c) a check of whether baselines are readable **at runtime** — that decides whether any
projection rule can ever ship live.

- **Standing rule:** use the game source as a **microscope, never an answer key.** The eval set is
  55 semi-private + 55 fully private games we will never see; anything tuned to these 25 does not
  transfer. What transfers is game-agnostic structure discovered from them — the way `deathclock`
  found "levels sit on an action clock" rather than "tn36 dies at 61".

## ⬜ 10. Settle final-ranking mechanics before Nov 2  *(cost: 0, deadline-critical)*

**The private leaderboard decides.** 25 public demo / 55 semi-private (→ the public LB we watch) /
55 fully private (→ final standing). ARC Prize state they *"will never report public set scores of
any system on the official leaderboard."* Every one of our submissions has `privateScore: ''` —
withheld until 2026-11-02, revealed 2026-12-04.

**Open and unresolved:** whether final ranking uses submissions we explicitly *select*, or whether
Kaggle auto-picks our best. Our entire strategy is max-over-daily-draws on the **public** half —
and the best public draw is not necessarily the best private one. If selection is required and
left unset, the default is "best public", which may not be what we want.

- **GATE:** answer documented in PROJECT.md with a source, well before the deadline. If selection
  exists, decide the policy (likely: pick the two draws from the most *mechanically* sound kernel,
  not the two highest public scores, since public score at our noise level is partly luck).

---

## Sequencing (GPU-aware)

Two Save&Run passes fit in parallel; ~6 per week at 30 h.

| Session | Pair A | Pair B | Unblocks |
|---|---|---|---|
| 1 | **v16 = v14 + deathclock** | **v17 = v14 + MTP + scheduler + analyzer timeout** | steps 2, 3, 4, 8 |
| 2 | winner of session 1 + prompt procedure | winner of session 1 (control) | step 5 → the fine-tune decision |
| — | *no GPU* | steps 6, 7, 9, 10 in parallel with the above | the free wins |

Steps 6, 7, 9 and 10 need **no GPU at all** and should run alongside, not after.

## Explicitly deferred

- **LoRA / fine-tuning.** Blocked behind step 5 by design. Current evidence against: the two teams
  publicly fine-tuning score **2.02** and **2.10** — inside the same band as people who changed
  nothing but the checkpoint — while #1 (7.51) and #3 (4.71) run stock weights. Also, no LoRA
  serving is wired (`grep lora` over `setup_commands.json` and the framework returns nothing; the
  launch has no `--enable-lora`), and our positive-example pool is thin: 52 passes, 3,428 actions,
  30 runs clearing ≥1 level, only **3** clearing ≥3. Cloning our own rollouts caps us at our own
  behaviour, and at ±0.8 noise, selecting rollouts by score partly selects luck.
- **The v30 graft set (v15).** 2.80 vs v14's 3.61 — a same-session paired A/B, but 0.81 sits on
  the noise threshold, so it is recorded as **no evidence**, not "worse". Its median was *higher*
  (2.04 vs 1.51). Shelved, re-testable if a later lever needs it.
- **Early game abandonment.** Token-burn as a kill signal is **refuted** — measured on 25 games,
  scorers median tok@10 = 8249 (range 4337–17052) vs zeros 7569 (1752–21962); the zeros' range
  strictly contains the scorers'. Every non-trivial threshold loses score. The projected-actions
  variant is more promising (`proj@10 < 1.25 × L1_baseline` killed 3 of 25 for zero score cost)
  but rides on a bad estimator (proj/actual median 0.58×, range 0.06–2.60×) and would have killed
  sk48, which scored 2.78 in a different run of identical code. **Measure it, do not ship it.**
