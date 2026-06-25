# rl_design.md — Direction 2: the ceiling-raiser (online learning agent)

> Scoping the "RL frame-change predictor" (the 12.58% StochasticGoose approach) under THIS
> competition's real constraints. Written 2026-06-25. Decided: hold v4 (0.23-tier), build this.

## Hard constraints that shape the design (don't fight these)
1. **Eval games are NOVEL and hidden.** You cannot pre-train a model on them. A CNN pretrained on the
   25 public games will NOT transfer — different mechanics, sprites, goals. (This kills naive "train a
   CNN offline, bundle it" plans.)
2. **Learning must be ONLINE, in-game.** Whatever the agent learns, it learns within one game's action
   budget (~600 on Kaggle). So the "RL" is online per-episode adaptation, not offline policy training.
   → The StochasticGoose CNN+RL almost certainly learns frame-change prediction *during* play.
3. **Eval is offline (no internet) + CPU is fine.** No GPU benefit for a from-scratch online learner;
   a heavy CNN trained on ~600 steps won't converge anyway. Favor lightweight online models.
4. **1 LB submission / DAY.** Every submission must clear the 0.23 bar in expectation. Validate hard
   offline (deterministically, multiple games) before spending the slot.
5. **Offline metric is HIGH-VARIANCE** (~6–10/183 across trajectories). Need a stabler eval: average
   over seeds, or report per-game level counts, not a single total.

## What "frame-change prediction" actually buys (and why it beats pure graph-explore)
Our v4 already tracks per-move-type effect + reward. The RL upgrade generalizes the effect model from
"per action TYPE" to "per (action, CONTEXT-FEATURE)", so the agent predicts *which action will change
the frame / make progress* from the current observation, instead of trying each blind. That's the
exploration-efficiency win the winners got. It's a **contextual bandit / online value model**, not a CNN.

## Proposed build (incremental, each step measurable offline vs v4=7/183 deterministic)
- **v5 (online change-predictor prior):** featurize each frame cheaply (e.g. count of distinct non-bg
  colours bucketed; coarse 8×8 downsample hash; did-last-action-change flag). Maintain
  `model[(action_key, feat)] -> Beta(changed, unchanged)`. Pick among untested/live moves by Thompson
  sample of P(change) for the current feature → informative-first exploration. Keep the graph + reward.
- **v6 (progress predictor):** same but target = P(levels_completed increases), seeded by v4's reward.
  Bias execution (not just exploration) toward predicted-progress actions once the level looks mapped.
- **v7 (object-relative features for ACTION6):** featurize click targets by local patch (colour, size,
  is-it-near-the-player) so click value generalizes across positions — the big lever for the 20/25
  click games.

## Validation protocol (because of variance + 1/day)
- Run each candidate over all 25 games **deterministically** (PYTHONHASHSEED=0, per-instance RNG).
- Also run 3 seeds; compare mean per-game level counts. Only promote a change that beats v4 on the
  **mean across seeds**, not one lucky sweep.
- Submit to LB only after a candidate clears v4 offline by a margin bigger than the seed-variance.

## Open question to resolve first
Is the StochasticGoose CNN genuinely online, or pretrained on a meta-distribution of games? If the latter,
there may be transferable game-agnostic priors (e.g. "things that look like buttons are clickable") worth a
small pretrained feature extractor. Check the winner's writeup / code before over-investing in pure-online.
