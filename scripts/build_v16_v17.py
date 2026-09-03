"""Build Kochi Loki v16 / v17 from the shipped v14 (kernel version 2, live LB 2.26).

Roadmap session 1 (docs/roadmap.md steps 2, 3, 8). Two independent levers, one each,
so a paired same-session read is possible against v14's known distribution.

  v16 = v14 + goalkeep + deathclock.
        deathclock is gated on goalkeep in composite.py
        (`if active.get("goalkeep") and flags.get("deathclock")`), so goalkeep rides
        along as the minimum carrier -- it is NOT an independent lever here.
        Cell 12 only.

  v17 = v14 + MTP speculative decoding (probed, with a stock fallback)
        + LOCAL_ANALYZER_TIMEOUT=900.
        Cell 8 only: both edits land inside the bundled setup command.

Every edit is anchored on an exact string and asserted; a drifted base fails here
rather than 4.5h into a GPU session.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BASE = REPO / "external" / "kochi_loki" / "kochi-loki-arc-agi-3.v14.ipynb"
OUT_DIR = REPO / "external" / "kochi_loki"
BUNDLE_SETUP = REPO / "external" / "fork_bundle" / "setup_commands.json"

UPSTREAM_BUNDLE = "thtennant/taaf-kaggle-source-share-fork"
WHEELHOUSE = "driessmit1/arc3-vllm-h100-wheelhouse-v3"
QWEN_MODEL_SOURCE = "foysalemonshanto/qwen3-8-27b-fp8-repacked-v1/PyTorch/hf-fp8/1"

# --- v16: cell 12 graft flags -------------------------------------------------

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

NEW_FLAGS = '''    # --- v16: + goalkeep + deathclock --------------------------------------
    # deathclock is the lever; goalkeep is its carrier. composite.py gates it as
    # `if active.get("goalkeep") and flags.get("deathclock")`, and goalkeep's digest
    # is the only channel by which deathclock's snapshot reaches the agent, so
    # goalkeep cannot be left off. Every other v14 flag is unchanged.
    #
    # Why deathclock. Upstream probed all 150 public levels: 134 of 150 end
    # themselves within 400 actions (median limit 100, range 20-256) and RESET
    # refunded the budget on 134 of 134. When the limit fires, non-RESET actions
    # no-op, the runner auto-RESETs, the level's opening board is restored, and
    # everything built on it is discarded -- while the level counter does not move.
    # The agent is told none of it: current_frame.step counts the whole run, never
    # the level, so it cannot locate itself inside the budget that is killing it.
    # tn36 dies on action 61 in eleven archived passes of eleven; its level 0 is
    # clearable in 18-34 actions; the single pass that treated its second life as an
    # execution run scored 8.646.
    #
    # It REPORTS ONLY -- the restart, the measured limit as a countdown, the offline
    # census as a prior, and the falsification when a level outruns the longest known
    # limit. It never chooses an action, never suppresses one, never recommends
    # RESET. That restraint is deliberate: the 08-22 finding was that an
    # inert-action suppressor would have removed the sweep that cleared the only
    # fresh level in the archive.
    #
    # tn36, sc25 and sp80 are the three games our baseline analysis classed as REAL
    # failures (2.5-3.4x the level-1 human baseline spent, still no clear) rather
    # than action-starved. They are what this run is aimed at.
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
            "deathclock": True,
        },
    )'''

# --- v17: patches applied to the bundled setup command ------------------------

OLD_LAUNCH = (
    "    print('Starting vLLM OpenAI server:', ' '.join(cmd), flush=True)\n"
    "    process = subprocess.Popen(cmd, env=vllm_env(), stdout=log_handle, "
    "stderr=subprocess.STDOUT, text=True)\n"
    "    VLLM_SERVER_PID.write_text(str(process.pid), encoding='utf-8')\n"
    "    wait_for_vllm_server()\n"
)

NEW_LAUNCH = """    # --- v17: MTP speculative decoding, probed, with a stock fallback ------
    # mtp.safetensors (477MB) ships INSIDE the checkpoint we already mount and this
    # launch has never used it. Throughput is the measured bottleneck: 4 of our 7
    # zero-scoring games took fewer actions than the level-1 human baseline, i.e.
    # they could not have cleared level 1 playing perfectly.
    # The exact flag spelling and the method name for this architecture are NOT
    # confirmed for the pinned vLLM, so: probe --help first, and if the server does
    # not come up, kill it and relaunch stock. Worst case costs ~10 min of a 9h run.
    def _speculative_supported() -> bool:
        try:
            probe = subprocess.run(
                [sys.executable, '-m', 'vllm.entrypoints.openai.api_server', '--help'],
                env=vllm_env(), capture_output=True, text=True, timeout=600,
            )
            text = (probe.stdout or '') + (probe.stderr or '')
            present = '--speculative-config' in text
            print(f'TAAF_V17 MTP PROBE: --speculative-config present={present}', flush=True)
            return present
        except Exception as exc:
            print(f'TAAF_V17 MTP PROBE FAILED: {exc!r}', flush=True)
            return False

    def _launch_vllm(extra_args):
        VLLM_SERVER_PID.unlink(missing_ok=True)
        full_cmd = cmd + list(extra_args)
        print('Starting vLLM OpenAI server:', ' '.join(full_cmd), flush=True)
        proc = subprocess.Popen(
            full_cmd, env=vllm_env(), stdout=log_handle,
            stderr=subprocess.STDOUT, text=True,
        )
        VLLM_SERVER_PID.write_text(str(proc.pid), encoding='utf-8')
        return proc

    mtp_args = []
    if _speculative_supported():
        mtp_args = [
            '--speculative-config',
            json.dumps({'method': 'mtp', 'num_speculative_tokens': 3}),
        ]
    process = _launch_vllm(mtp_args)
    try:
        wait_for_vllm_server()
        print(f'TAAF_V17 MTP ACTIVE={bool(mtp_args)}', flush=True)
    except Exception as exc:
        if not mtp_args:
            raise
        print(f'TAAF_V17 MTP LAUNCH FAILED, falling back to stock: {exc!r}', flush=True)
        try:
            process.kill()
            process.wait(timeout=60)
        except Exception:
            pass
        time.sleep(15)
        process = _launch_vllm([])
        wait_for_vllm_server()
        print('TAAF_V17 MTP ACTIVE=False (stock fallback)', flush=True)
"""

OLD_TIMEOUT = "    'LOCAL_ANALYZER_YIELD_SECONDS': '60',\n"
NEW_TIMEOUT = (
    "    'LOCAL_ANALYZER_YIELD_SECONDS': '60',\n"
    "    # v17: this key was NEVER set, so _LOCAL_ANALYZER_TIMEOUT defaulted to 0.0 and\n"
    "    # ToolAgent set self._timeout = None -- HTTP requests to vLLM had no client-side\n"
    "    # timeout at all, guarded only by bm.solver.analyzer_timeout=900 one layer out.\n"
    "    # Our 07-30 finding blamed analyzer read-timeouts reshuffling which games get\n"
    "    # budget for the +/-0.8 offline noise that has been grading our levers as noise.\n"
    "    'LOCAL_ANALYZER_TIMEOUT': '900',\n"
)

# The v17 edits are applied inside cell 8's patch function, so extend it there.
OLD_PATCH_RETURN = """        patched.append(command)
    missing = [name for name, n in counts.items() if n == 0]"""

NEW_PATCH_RETURN = '''        # --- v17: MTP speculative decoding + the missing analyzer HTTP timeout
        if OLD_LAUNCH_ANCHOR in command:
            command = command.replace(OLD_LAUNCH_ANCHOR, NEW_LAUNCH_BLOCK, 1)
            launch_patches += 1
        if OLD_TIMEOUT_ANCHOR in command:
            command = command.replace(OLD_TIMEOUT_ANCHOR, NEW_TIMEOUT_BLOCK, 1)
            timeout_patches += 1
        patched.append(command)
    if launch_patches != 1:
        raise RuntimeError(
            f"v17: expected exactly 1 vLLM launch site to patch, found {launch_patches}. "
            "The attached source bundle's setup_commands.json has changed."
        )
    if timeout_patches != 1:
        raise RuntimeError(
            f"v17: expected exactly 1 analyzer-env site to patch, found {timeout_patches}. "
            "The attached source bundle's setup_commands.json has changed."
        )
    print(f"TAAF_V17 SETUP PATCHED: launch={launch_patches} timeout={timeout_patches}")
    missing = [name for name, n in counts.items() if n == 0]'''

OLD_PATCH_INIT = """    counts = {name: 0 for name in replacements}
    env_patches = 0
    patched = []"""

NEW_PATCH_INIT = """    counts = {name: 0 for name in replacements}
    env_patches = 0
    launch_patches = 0
    timeout_patches = 0
    patched = []"""

HEADER_ANCHOR = "**Build: v14**"


def _cell_text(cell: dict) -> str:
    return "".join(cell["source"])


def _set_cell(cell: dict, text: str) -> None:
    cell["source"] = text.splitlines(keepends=True)


def _replace_once(text: str, old: str, new: str, what: str) -> str:
    if text.count(old) != 1:
        raise SystemExit(f"BUILD FAIL: anchor for {what} found {text.count(old)} times (want 1)")
    return text.replace(old, new, 1)


def _py_literal(name: str, value: str) -> str:
    return f"{name} = {value!r}\n"


def build(version: str) -> Path:
    nb = json.loads(BASE.read_text(encoding="utf-8"))
    cells = nb["cells"]
    if len(cells) != 17:
        raise SystemExit(f"BUILD FAIL: base notebook has {len(cells)} cells, expected 17")
    base_texts = [_cell_text(c) for c in cells]

    _set_cell(cells[0], _replace_once(base_texts[0], HEADER_ANCHOR, f"**Build: {version}**", "header"))

    if version == "v16":
        _set_cell(cells[12], _replace_once(base_texts[12], OLD_FLAGS, NEW_FLAGS, "cell 12 flags"))
        expected = [0, 12]
    else:
        text8 = base_texts[8]
        # Anchors live as module constants so the replacement blocks stay readable.
        preamble = (
            "# --- v17 anchors (exact strings from the bundled setup command) --------------\n"
            + _py_literal("OLD_LAUNCH_ANCHOR", OLD_LAUNCH)
            + _py_literal("NEW_LAUNCH_BLOCK", NEW_LAUNCH)
            + _py_literal("OLD_TIMEOUT_ANCHOR", OLD_TIMEOUT)
            + _py_literal("NEW_TIMEOUT_BLOCK", NEW_TIMEOUT)
            + "\n"
        )
        text8 = _replace_once(text8, "import re as _re\n", preamble + "import re as _re\n", "v17 anchors")
        text8 = _replace_once(text8, OLD_PATCH_INIT, NEW_PATCH_INIT, "patch counters")
        text8 = _replace_once(text8, OLD_PATCH_RETURN, NEW_PATCH_RETURN, "patch body")
        _set_cell(cells[8], text8)
        expected = [0, 8]

    changed = [i for i, c in enumerate(cells) if _cell_text(c) != base_texts[i]]
    if changed != expected:
        raise SystemExit(f"BUILD FAIL: changed cells {changed}, expected {expected}")

    code_all = "\n".join(_cell_text(c) for c in cells if c["cell_type"] == "code")
    # Invariants that must survive every build in this lineage.
    if 'MODEL_TO_ENGINE_ACTION["ACTION7"] = "ACTION7"' not in code_all:
        raise SystemExit("BUILD FAIL: the v10 ACTION7 reverse-map fix is gone")
    if "Qwen/Qwen3.8-27B-FP8" not in code_all:
        raise SystemExit("BUILD FAIL: Qwen3.8 served-model name missing")
    if "kaggle_input_paths[QWEN_MODEL_REF] = str(QWEN_MODEL_PATH)" not in code_all:
        raise SystemExit("BUILD FAIL: the Kaggle-Model mount fix is gone")
    if "hours=8, minutes=20" not in code_all:
        raise SystemExit("BUILD FAIL: the 8h20m soft-end guard is gone")
    if version == "v16":
        if '"deathclock": True' not in code_all or '"goalkeep": True' not in code_all:
            raise SystemExit("BUILD FAIL: v16 must carry goalkeep + deathclock")
        if "speculative" in code_all:
            raise SystemExit("BUILD FAIL: v16 must not carry the v17 MTP lever")
    else:
        if "--speculative-config" not in code_all:
            raise SystemExit("BUILD FAIL: v17 must carry the MTP flag")
        if "'LOCAL_ANALYZER_TIMEOUT': '900'" not in code_all:
            raise SystemExit("BUILD FAIL: v17 must set LOCAL_ANALYZER_TIMEOUT")
        if '"deathclock"' in code_all:
            raise SystemExit("BUILD FAIL: v17 must not carry the v16 lever")

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
    build("v16")
    build("v17")
    write_metadata("v16", "soumyacryptic/kochi-loki-arc-agi-3",
                   "Kochi Loki - ARC-AGI-3", "kochi-loki-arc-agi-3.ipynb")
    write_metadata("v17", "soumyacryptic/kochi-loki-arc-agi-3-v15",
                   "Kochi Loki - ARC-AGI-3 v15", "kochi-loki-arc-agi-3-v15.ipynb")
    sys.exit(0)
