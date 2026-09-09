"""Build Kochi Loki v18 / v19 from the shipped v14 (live LB best 2.26).

Upstream shipped seven new grafts between our 09-01 snapshot and 09-07, and then
PRUNED its own flag set. thtennant's v35 runs:

    {efficiency, retry_guard, shortcircuit, goalkeep, hudmask, clickmap,
     searchmap, reach7, firstcontact}

i.e. the v22 core plus the two new keepers, having dropped clockwatch, lawbook,
winframe, carryover, undo, untried, tally and bandlevel (the v30 set our v15
measured at 2.80 vs v14's 3.61) and deathclock (our v16, no evidence). Their
pruning agrees with both of our null results, which is worth something.

The two new keepers:

  reach7       generalises our v10 ACTION7 fix: every arcengine.GameAction member
               the name map does not cover is added mapped to ITSELF, not just
               ACTION7. Their probe: ACTION7 appears in 0 of 9,772 archived
               actions, on 6 of 25 public games -- including su15, whose only
               other control is the mouse. Standalone flag, no carrier.

  firstcontact the lever. Before the model's first turn, the SOLVER presses each
               declared non-click control once (depth 2 re-presses only the silent
               ones) and hands the model the resulting table. Costs actions and
               ZERO model calls. Measured over all 150 levels of the 25 public
               games: 418 of 427 live controls found (98%) at a median 4 actions,
               and in 450 level-sweeps it never cleared a level or ended one.
               Gated on goalkeep (composite.py:564).

Why this is the right lever for us. Upstream measured a turn at a median 120 s
against a 7920 s per-game wall, so a game buys about 22 model calls. Our own
baseline analysis found 4 of 7 zero-scoring games took FEWER actions than the
level-1 human baseline. Control discovery is a fixed mechanical question that
currently costs model calls; firstcontact pays for it in actions instead, and
actions are the thing we are not short of relative to their price.

  v18 = v14 flags + goalkeep + reach7 + firstcontact.
        Minimal path to firstcontact; keeps our banking/transfer/recovery.

  v19 = upstream v35's flag set verbatim.
        Drops banking/transfer/recovery, turns efficiency ON. A wholesale adopt
        of the best-measured public configuration.

Cell 12 only in both. Anchored and asserted.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BASE = REPO / "external" / "kochi_loki" / "kochi-loki-arc-agi-3.v14.ipynb"
OUT_DIR = REPO / "external" / "kochi_loki"

UPSTREAM_BUNDLE = "thtennant/taaf-kaggle-source-share-fork"
WHEELHOUSE = "driessmit1/arc3-vllm-h100-wheelhouse-v3"
QWEN_MODEL_SOURCE = "foysalemonshanto/qwen3-8-27b-fp8-repacked-v1/PyTorch/hf-fp8/1"

OLD_FLAGS = """    install(
        bm,
        flags={
            "banking": True,
            "transfer": True,
            "shortcircuit": True,
            "recovery": True,
            "retry_guard": True,
            "efficiency": False,
        },
    )"""

V18_FLAGS = '''    # --- v18: + goalkeep + reach7 + firstcontact ---------------------------
    # firstcontact is the lever; goalkeep is its carrier (composite.py gates it as
    # `if active.get("goalkeep") and flags.get("firstcontact")`). reach7 rides along
    # because it is standalone, free, and strictly generalises the ACTION7 fix we
    # already hand-roll above -- it maps EVERY uncovered arcengine.GameAction member
    # to itself rather than just ACTION7. The two patches are idempotent; ours stays
    # in as belt-and-braces and its banner still fires.
    #
    # Why firstcontact. Upstream measured a model turn at a median 120 s against the
    # 7920 s per-game wall, so a game buys roughly 22 model calls. Working out what
    # the controls do is the agent's first job, it has a fixed mechanical answer, and
    # it currently costs those calls. firstcontact presses each declared non-click
    # control once before the model's first turn -- depth 2 re-presses only the ones
    # that showed nothing -- and hands the model the table. Zero model calls.
    # Probed over all 150 levels of the 25 public games: 418 of 427 live controls
    # found (98%) at a median 4 actions; across 450 level-sweeps it never cleared a
    # level and never ended one, so the agent gets the level it would have had plus
    # the table. Clicks are excluded (a single click says nothing about a 4096-cell
    # space, and clickmap already partitions that bucket).
    #
    # This is the cheap half of "explore cheaply, execute expensively", and it is
    # aimed squarely at our measured failure: 4 of our 7 zero-scoring games took
    # FEWER actions than the level-1 human baseline, i.e. they could not have cleared
    # level 1 playing perfectly.
    #
    # Our v14 flags are otherwise unchanged, so this isolates the new lever.
    install(
        bm,
        flags={
            "banking": True,
            "transfer": True,
            "shortcircuit": True,
            "recovery": True,
            "retry_guard": True,
            "efficiency": False,
            "goalkeep": True,
            "reach7": True,
            "firstcontact": True,
        },
    )'''

V19_FLAGS = '''    # --- v19: upstream v35's flag set, verbatim ----------------------------
    # A wholesale adopt of the best-measured public configuration rather than an
    # isolate. thtennant's v35 (2026-09-07) runs exactly these nine flags, having
    # PRUNED clockwatch, lawbook, winframe, carryover, undo, untried, tally and
    # bandlevel -- the v30 set our v15 measured at 2.80 against v14's 3.61 -- and
    # deathclock, which our v16 measured as no-evidence. Upstream's pruning agrees
    # with both of our null results independently, which is the main reason to trust
    # the rest of the set.
    #
    # Note what this DROPS relative to v14: banking (0 full wins in 104+ runs, so it
    # has never fired), transfer (never published on a live card) and recovery (which
    # upstream dropped deliberately at their v14 and has not brought back). And it
    # turns efficiency ON, which is a prompt-margin change and therefore against our
    # n=3 rule -- but that rule's three datapoints were all measured on Qwen3.6, and
    # we now serve Qwen3.8, whose whole delta is instruction-following.
    #
    # So v18 and v19 together answer two different questions: v18 asks "is
    # firstcontact worth anything on OUR stack", v19 asks "is our stack worth keeping
    # at all versus upstream's current best".
    install(
        bm,
        flags={
            "efficiency": True,
            "retry_guard": True,
            "shortcircuit": True,
            "goalkeep": True,
            "hudmask": True,
            "clickmap": True,
            "searchmap": True,
            "reach7": True,
            "firstcontact": True,
        },
    )'''

HEADER_ANCHOR = "**Build: v14**"


def _cell_text(cell: dict) -> str:
    return "".join(cell["source"])


def _set_cell(cell: dict, text: str) -> None:
    cell["source"] = text.splitlines(keepends=True)


def _replace_once(text: str, old: str, new: str, what: str) -> str:
    if text.count(old) != 1:
        raise SystemExit(f"BUILD FAIL: anchor for {what} found {text.count(old)} times (want 1)")
    return text.replace(old, new, 1)


def build(version: str, flags_block: str) -> Path:
    nb = json.loads(BASE.read_text(encoding="utf-8"))
    cells = nb["cells"]
    if len(cells) != 17:
        raise SystemExit(f"BUILD FAIL: base notebook has {len(cells)} cells, expected 17")
    base_texts = [_cell_text(c) for c in cells]

    _set_cell(cells[0], _replace_once(base_texts[0], HEADER_ANCHOR, f"**Build: {version}**", "header"))
    _set_cell(cells[12], _replace_once(base_texts[12], OLD_FLAGS, flags_block, "cell 12 flags"))

    changed = [i for i, c in enumerate(cells) if _cell_text(c) != base_texts[i]]
    if changed != [0, 12]:
        raise SystemExit(f"BUILD FAIL: changed cells {changed}, expected [0, 12]")

    code_all = "\n".join(_cell_text(c) for c in cells if c["cell_type"] == "code")
    # Invariants for this whole lineage.
    if 'MODEL_TO_ENGINE_ACTION["ACTION7"] = "ACTION7"' not in code_all:
        raise SystemExit("BUILD FAIL: the v10 ACTION7 reverse-map fix is gone")
    if "Qwen/Qwen3.8-27B-FP8" not in code_all:
        raise SystemExit("BUILD FAIL: Qwen3.8 served-model name missing")
    if "kaggle_input_paths[QWEN_MODEL_REF] = str(QWEN_MODEL_PATH)" not in code_all:
        raise SystemExit("BUILD FAIL: the Kaggle-Model mount fix is gone")
    if "hours=8, minutes=20" not in code_all:
        raise SystemExit("BUILD FAIL: the 8h20m soft-end guard is gone")
    # Both builds must carry the new levers.
    for flag in ('"reach7": True', '"firstcontact": True', '"goalkeep": True'):
        if flag not in code_all:
            raise SystemExit(f"BUILD FAIL: {version} missing {flag}")
    # Flags upstream pruned must not reappear by accident.
    for stale in ("deathclock", "bandlevel", "clockwatch", "lawbook", "winframe",
                  "carryover", '"undo"', '"untried"', '"tally"'):
        if f'"{stale}": True' in code_all or f'{stale}": True' in code_all:
            raise SystemExit(f"BUILD FAIL: {version} carries pruned flag {stale}")
    if version == "v18" and '"banking": True' not in code_all:
        raise SystemExit("BUILD FAIL: v18 must keep the v14 flag set")
    if version == "v19" and '"banking"' in code_all:
        raise SystemExit("BUILD FAIL: v19 must drop banking/transfer/recovery")

    out = OUT_DIR / f"kochi-loki-arc-agi-3.{version}.ipynb"
    out.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"OK {version}: cells changed {changed} -> {out.relative_to(REPO)}")
    return out


def write_metadata(version: str, kernel_id: str, title: str, code_file: str) -> Path:
    meta = {
        "id": kernel_id,
        "title": title,
        "code_file": code_file,
        "language": "python",
        "kernel_type": "notebook",
        "is_private": True,
        "enable_gpu": True,
        "enable_tpu": False,
        "enable_internet": False,
        "keywords": ["gpu"],
        "dataset_sources": [WHEELHOUSE, UPSTREAM_BUNDLE],
        "kernel_sources": [],
        "competition_sources": ["arc-prize-2026-arc-agi-3"],
        "model_sources": [QWEN_MODEL_SOURCE],
        "docker_image": (
            "gcr.io/kaggle-private-byod/python@sha256:"
            "57e612b484cf3df5026ee4dcc3cb176974b22b2bc0937fb1e16132a8be4cb13c"
        ),
        "machine_shape": "NvidiaRtxPro6000",
    }
    out = OUT_DIR / f"kernel-metadata.{version}.json"
    out.write_text(json.dumps(meta, indent=2) + "\n", encoding="utf-8")
    print(f"OK {version}: metadata -> {out.relative_to(REPO)}")
    return out


if __name__ == "__main__":
    build("v18", V18_FLAGS)
    build("v19", V19_FLAGS)
    write_metadata("v18", "soumyacryptic/kochi-loki-arc-agi-3",
                   "Kochi Loki - ARC-AGI-3", "kochi-loki-arc-agi-3.ipynb")
    write_metadata("v19", "soumyacryptic/kochi-loki-arc-agi-3-v15",
                   "Kochi Loki - ARC-AGI-3 v15", "kochi-loki-arc-agi-3-v15.ipynb")
    sys.exit(0)
