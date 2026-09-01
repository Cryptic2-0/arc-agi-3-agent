"""Build Kochi Loki v14 / v15 notebooks from the shipped v1 (= duck v13 runtime).

Both candidates share ONE capability lever that the whole leaderboard moved on in
August 2026: the base model swaps from Qwen3.6-27B-FP8 to Qwen3.8-27B-FP8. They
differ only in cell 12's graft flags.

  v14 = Kochi v1 + Qwen3.8 model pin + upstream fork bundle repoint.
        Graft flags unchanged (our v5 set). Isolates the model lever.
  v15 = v14 + the upstream v30 graft set (goalkeep/hudmask/clickmap/searchmap/
        clockwatch/lawbook/winframe/carryover/undo/untried/tally/bandlevel).

Every edit is anchored on an exact string and asserted, so a drifted base notebook
fails here rather than 4.5h into a GPU session.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BASE = REPO / "external" / "kochi_loki" / "kochi-loki-arc-agi-3.ipynb"
OUT_DIR = REPO / "external" / "kochi_loki"

UPSTREAM_BUNDLE = "thtennant/taaf-kaggle-source-share-fork"
WHEELHOUSE = "driessmit1/arc3-vllm-h100-wheelhouse-v3"
QWEN_MODEL_SOURCE = "foysalemonshanto/qwen3-8-27b-fp8-repacked-v1/PyTorch/hf-fp8/1"

# --- cell 6: dataset sources + Qwen3.8 model pin ------------------------------

OLD_SOURCES = (
    '# Kaggle inputs attached to this notebook, plus bookkeeping paths used below.\n'
    'DATASET_SOURCES = ["soumyacryptic/taaf-kaggle-source-share-fork-mirror", '
    '"driessmit1/arc3-vllm-h100-wheelhouse-v3", "driessmit1/vrfai-qwen3-6-27b-fp8-hf-snapshot"]\n'
    'KERNEL_SOURCES = []\n'
)

NEW_SOURCES = '''# Kaggle inputs attached to this notebook, plus bookkeeping paths used below.
DATASET_SOURCES = ["thtennant/taaf-kaggle-source-share-fork", "driessmit1/arc3-vllm-h100-wheelhouse-v3"]
# --- v14: Qwen3.8-27B-FP8 model pin -------------------------------------------
# The base model is the one axis this project never varied: every version from v1
# to v13 served the Qwen 3.6 27B FP8 weights the June-30 duck shipped with.
# Qwen3.8-27B-FP8 landed on 2026-08-14 and the field moved on it within days --
# the public LB top went 1.86 -> 7.51 and the whole top-20 re-formed above 2.9
# while our 1.46 sat still. Same dense-27B active-parameter class (so the v7
# MoE lesson does not apply), same FP8 serving path, same 96GB card.
# The Qwen3.6 weights dataset is dropped from DATASET_SOURCES: the weights now
# arrive as a Kaggle *Model*, which mounts elsewhere (see below).
QWEN_MODEL_OWNER = "foysalemonshanto"
QWEN_MODEL_SLUG = "qwen3-8-27b-fp8-repacked-v1"
QWEN_MODEL_REF = f"{QWEN_MODEL_OWNER}/{QWEN_MODEL_SLUG}"
QWEN_MODEL_FRAMEWORK = "pytorch"
QWEN_MODEL_VARIATION = "hf-fp8"
QWEN_MODEL_VERSION = "1"
QWEN_SERVED_MODEL_NAME = "Qwen/Qwen3.8-27B-FP8"

# Keep the whole run offline: the weights are mounted, nothing may be fetched.
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"


# A Kaggle *Model* does not mount where a Kaggle *dataset* does. The documented
# layout is /kaggle/input/models/<owner>/<slug>/<framework>/<variation>/<version>,
# but the framework segment's case has been seen both ways and some images drop
# the "models" prefix, so probe every shape rather than hard-code one and find
# out 4.5h into a GPU session.
def _model_mount_candidates() -> list:
    roots = [
        Path("/kaggle/input/models") / QWEN_MODEL_OWNER / QWEN_MODEL_SLUG,
        Path("/kaggle/input/models") / QWEN_MODEL_SLUG,
        Path("/kaggle/input") / QWEN_MODEL_SLUG,
    ]
    frameworks = [QWEN_MODEL_FRAMEWORK, QWEN_MODEL_FRAMEWORK.capitalize(), "PyTorch"]
    seen, out = set(), []
    for root in roots:
        for framework in frameworks:
            candidate = root / framework / QWEN_MODEL_VARIATION / QWEN_MODEL_VERSION
            if str(candidate) not in seen:
                seen.add(str(candidate))
                out.append(candidate)
    return out


_qwen_candidates = _model_mount_candidates()
QWEN_MODEL_PATH = next((c for c in _qwen_candidates if c.is_dir()), None)
if QWEN_MODEL_PATH is None:
    raise FileNotFoundError(
        "Qwen3.8 Kaggle Model is not attached. Tried:\\n  "
        + "\\n  ".join(str(c) for c in _qwen_candidates)
        + "\\nAttach: Qwen3.8 27B FP8 Repacked -> PyTorch -> hf-fp8 -> Version 1"
    )

# Fail before the wheelhouse install rather than inside vLLM: a half-mounted
# checkpoint otherwise costs a whole GPU session to discover.
_qwen_required = [
    "config.json",
    "model.safetensors.index.json",
    "tokenizer.json",
    "tokenizer_config.json",
]
_qwen_missing = [n for n in _qwen_required if not (QWEN_MODEL_PATH / n).is_file()]
if _qwen_missing:
    raise FileNotFoundError(
        f"Qwen3.8 mount {QWEN_MODEL_PATH} is incomplete; missing: " + ", ".join(_qwen_missing)
    )
_qwen_shards = sorted(QWEN_MODEL_PATH.glob("*.safetensors"))
if not _qwen_shards:
    raise RuntimeError(f"No safetensors shards under {QWEN_MODEL_PATH}.")
print(f"TAAF_V14 QWEN38 MOUNT OK: {QWEN_MODEL_PATH} ({len(_qwen_shards)} shards)")
# ------------------------------------------------------------------------------
KERNEL_SOURCES = []
'''

# --- cell 6 (second edit): publish the model mount into the setup env --------
# The bundled setup resolves the weights with resolve_kaggle_dataset_path(OWNER, SLUG),
# which looks in TAAF_KAGGLE_INPUT_PATHS first and then probes the two *dataset* mount
# shapes. A Kaggle Model mounts at /kaggle/input/models/<owner>/<slug>/... which is
# neither, so without this line the setup falls through to a non-existent path and
# vLLM dies ~10 minutes into the session with the weights sitting right there.

OLD_SETUP_ENV = """# Published to setup commands and the solver via the environment:
setup_env = {
    # JSON {ref: mount_path} so they can locate every attached dataset / utility script.
    "TAAF_KAGGLE_INPUT_PATHS": json.dumps(kaggle_input_paths, sort_keys=True),
    # The attached dataset refs in order (index 0 is this source bundle).
    "TAAF_KAGGLE_DATASET_SOURCES": json.dumps(DATASET_SOURCES),
    # The attached utility-script / kernel refs.
    "TAAF_KAGGLE_KERNEL_SOURCES": json.dumps(KERNEL_SOURCES),
}"""

NEW_SETUP_ENV = """# The bundled setup resolves weights by owner/slug through THIS map first, so
# mapping the model ref to its mounted directory is the whole path fix -- a Kaggle
# Model does not mount at either of the two dataset shapes the setup probes.
kaggle_input_paths[QWEN_MODEL_REF] = str(QWEN_MODEL_PATH)

# Published to setup commands and the solver via the environment:
setup_env = {
    # JSON {ref: mount_path} so they can locate every attached dataset / utility script.
    "TAAF_KAGGLE_INPUT_PATHS": json.dumps(kaggle_input_paths, sort_keys=True),
    # The attached dataset refs in order (index 0 is this source bundle).
    "TAAF_KAGGLE_DATASET_SOURCES": json.dumps(DATASET_SOURCES),
    # The attached utility-script / kernel refs.
    "TAAF_KAGGLE_KERNEL_SOURCES": json.dumps(KERNEL_SOURCES),
    "TAAF_QWEN_MODEL_PATH": str(QWEN_MODEL_PATH),
    "TAAF_QWEN_SERVED_MODEL_NAME": QWEN_SERVED_MODEL_NAME,
    "HF_HUB_OFFLINE": "1",
    "TRANSFORMERS_OFFLINE": "1",
}"""


# --- cell 8: repoint the bundled setup command at Qwen3.8 --------------------

OLD_SETUP_LOOP = (
    "# Solver setup commands (wheels, vLLM server startup, ...) run before the benchmark loads.\n"
    "env = _command_env()\n"
    'for command in json.loads((BUNDLE_DIR / "setup_commands.json").read_text()):\n'
)

NEW_SETUP_LOOP = '''# --- v14: rewrite the bundled setup's model identity --------------------------
# The bundle ships ONE setup command: a here-doc Python script that starts vLLM.
# Rather than fork it (and inherit the job of keeping a 10KB copy in step), we
# rewrite exactly the three top-level string assignments that name the model, and
# raise if any is missing -- a bundle that has drifted must fail loudly, never
# serve Qwen3.6 under the Qwen3.8 label and hand us a silently unchanged draw.
import re as _re


def _replace_python_assignment(command: str, variable_name: str, value: str):
    pattern = rf"(?m)^{_re.escape(variable_name)}\\s*=\\s*(['\\"])[^\\r\\n]*?\\1\\s*$"
    return _re.subn(pattern, f"{variable_name} = {value!r}", command, count=1)


def _patch_qwen38_setup_commands(commands: list) -> list:
    replacements = {
        "MODEL_OWNER": QWEN_MODEL_OWNER,
        "MODEL_SLUG": QWEN_MODEL_SLUG,
        "SERVED_MODEL_NAME": QWEN_SERVED_MODEL_NAME,
    }
    counts = {name: 0 for name in replacements}
    env_patches = 0
    patched = []
    for raw in commands:
        command = str(raw)
        for name, value in replacements.items():
            command, n = _replace_python_assignment(command, name, value)
            counts[name] += n
        # Make the offline pins explicit in the vLLM child process too.
        if "def vllm_env()" in command and "'VLLM_NO_USAGE_STATS': '1'," in command:
            command = command.replace(
                "'VLLM_NO_USAGE_STATS': '1',",
                "'VLLM_NO_USAGE_STATS': '1',\\n"
                "            'HF_HUB_OFFLINE': '1',\\n"
                "            'TRANSFORMERS_OFFLINE': '1',",
                1,
            )
            env_patches += 1
        patched.append(command)
    missing = [name for name, n in counts.items() if n == 0]
    if missing:
        raise RuntimeError(
            "Could not repoint the bundled setup at Qwen3.8; missing assignment(s): "
            + ", ".join(missing)
            + ". The attached source bundle's setup_commands.json has changed."
        )
    print(
        f"TAAF_V14 QWEN38 SETUP PATCHED: {counts} offline_env_patches={env_patches} "
        f"served_as={QWEN_SERVED_MODEL_NAME}"
    )
    return patched


# Solver setup commands (wheels, vLLM server startup, ...) run before the benchmark loads.
env = _command_env()
_setup_commands = _patch_qwen38_setup_commands(
    json.loads((BUNDLE_DIR / "setup_commands.json").read_text())
)
for command in _setup_commands:
'''

# --- cell 12: graft flags (v15 only) -----------------------------------------

OLD_FLAGS_BLOCK = '''# Make one-off changes to `bm`, `bm.games`, or `bm.solver` here before the run starts.
#
# Composite graft install (taaf_grafts from the attached share-fork source bundle).
# Enabled here: banking (win-then-replay of the pruned winning trace on a fresh play
# of the same card; score is the max over plays), transfer (cross-clone replay via
# the process-global family store; degrades to a no-op on a non-clone set),
# shortcircuit (skips provably no-op repeated batch actions), recovery (un-sticks
# GAME_OVER spirals and hypothesis lock-in), retry_guard (bounded retry + vLLM
# health probe). efficiency is left OFF so the model prompts stay verbatim stock.
# install() restores the original bm.solver on ANY error; the extra try/except here
# means even an import failure of composite leaves bm.solver untouched (stock).
try:
    from taaf_grafts.composite import install

    install(
        bm,
        flags={
            "banking": True,
            "transfer": True,
            "shortcircuit": True,
            "recovery": True,
            "retry_guard": True,
            "efficiency": False,
        },
    )
except Exception as exc:  # noqa: BLE001 — any graft failure must fall back to stock
    print(f"[taaf_grafts] cell-12 graft failed, running stock: {type(exc).__name__}: {exc}")
'''

NEW_FLAGS_BLOCK = '''# Make one-off changes to `bm`, `bm.games`, or `bm.solver` here before the run starts.
#
# v15: adopt the upstream v30 graft set wholesale, in place of our v5 set.
#
# What changed and why. Our set was {banking, transfer, shortcircuit, recovery,
# retry_guard}. Two of those five have never paid: banking has fired 0 times in
# 104 runs (it needs a full WIN, which we have never had), and transfer's replay
# has never published on a live card. Upstream dropped recovery deliberately at
# their v14 and has not brought it back. What upstream ADDED since is a world-model
# stack, each piece with a measured prequential score in their notebook:
#   goalkeep   carries the world model across game-over/level change (the stock
#              harness carried a non-empty model on 33 of 481 turns) and injects a
#              per-turn digest of MEASURED outcomes.
#   hudmask    masks the status/timer band out of the change signal -- board_changed
#              is a whole-frame diff, so on 10 of 25 public games it was true 100%
#              of the time and the action table carried zero bits.
#              (bandlevel = hudmask's per-level tracker variant.)
#   clickmap   splits the single MOUSE bucket by what was under the cursor
#              (Brier 0.1414 -> 0.0627 over 291 real clicks).
#   searchmap  reports action-space STRUCTURE, which the reward channel cannot:
#              reward fired once in 375 actions on their commit run.
#   clockwatch / lawbook / winframe / carryover / undo / untried / tally: the
#              v23-v30 additions riding on goalkeep.
#   efficiency + retry_guard + shortcircuit: upstream's "v12 floor".
# efficiency flips ON here, which is a prompt-margin change and therefore against
# our n=3 rule -- it is in because it is load-bearing for the whole upstream stack
# (four of the flags above are nested under it or under goalkeep) and because
# splitting it out costs a GPU session we do not have before Sept 30.
#
# install() restores the original bm.solver on ANY error; the extra try/except here
# means even an import failure of composite leaves bm.solver untouched (stock).
try:
    from taaf_grafts.composite import install

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
            "clockwatch": True,
            "lawbook": True,
            "winframe": True,
            "carryover": True,
            "undo": True,
            "untried": True,
            "tally": True,
            "bandlevel": True,
        },
    )
except Exception as exc:  # noqa: BLE001 — any graft failure must fall back to stock
    print(f"[taaf_grafts] cell-12 graft failed, running stock: {type(exc).__name__}: {exc}")
'''

MODEL_ROW_OLD = (
    "| Model | Qwen3.6-27B-FP8, served locally by vLLM on one RTX Pro 6000 (96 GB) | "
    "27B **active** params; no API, no rate limits, no per-token cost |"
)
MODEL_ROW_NEW = (
    "| Model | **Qwen3.8-27B-FP8** (v14+; Qwen3.6-27B-FP8 through v13), served locally by "
    "vLLM on one RTX Pro 6000 (96 GB) | 27B **active** params; no API, no rate limits, no "
    "per-token cost |"
)

HEADER_OLD = "**Team:** Kochi Loki  ·  **Competition:** ARC Prize 2026 — ARC-AGI-3  ·  **Best public LB draw: 1.46**"


def header_new(version: str) -> str:
    return (
        "**Team:** Kochi Loki  ·  **Competition:** ARC Prize 2026 — ARC-AGI-3  ·  "
        f"**Best public LB draw: 1.46**  •  **Build: {version}**\n\n"
        "> **{v} — base-model swap.** Every version through v13 served Qwen3.6-27B-FP8, the\n"
        "> model the June-30 duck shipped with. Qwen3.8-27B-FP8 was released 2026-08-14; the\n"
        "> public leaderboard top went 1.86 → 7.51 over the following two weeks and the whole\n"
        "> top-20 re-formed above 2.9, while our score did not move. v14 swaps the model and\n"
        "> holds our graft flags fixed; v15 swaps the model AND adopts the upstream v30 graft\n"
        "> set. Our ACTION7 executability fix is kept in both — the upstream bundle still has\n"
        "> no ACTION7 entry in its reverse map.".replace("{v}", version)
    )


def _cell_text(cell: dict) -> str:
    return "".join(cell["source"])


def _set_cell(cell: dict, text: str) -> None:
    cell["source"] = text.splitlines(keepends=True)


def _replace_once(text: str, old: str, new: str, what: str) -> str:
    if text.count(old) != 1:
        raise SystemExit(f"BUILD FAIL: anchor for {what} found {text.count(old)} times (want 1)")
    return text.replace(old, new, 1)


def build(version: str, with_v30_grafts: bool) -> Path:
    nb = json.loads(BASE.read_text(encoding="utf-8"))
    cells = nb["cells"]
    if len(cells) != 17:
        raise SystemExit(f"BUILD FAIL: base notebook has {len(cells)} cells, expected 17")

    base_texts = [_cell_text(c) for c in cells]

    # cell 0 -- header note + the spec table's model row
    text0 = _replace_once(base_texts[0], HEADER_OLD, header_new(version), "header")
    text0 = _replace_once(text0, MODEL_ROW_OLD, MODEL_ROW_NEW, "spec-table model row")
    _set_cell(cells[0], text0)

    # cell 6 -- dataset sources + model pin + model mount published to the setup env
    text6 = _replace_once(base_texts[6], OLD_SOURCES, NEW_SOURCES, "cell 6 sources")
    text6 = _replace_once(text6, OLD_SETUP_ENV, NEW_SETUP_ENV, "cell 6 setup env")
    _set_cell(cells[6], text6)

    # cell 8 -- setup-command model rewrite
    _set_cell(cells[8], _replace_once(base_texts[8], OLD_SETUP_LOOP, NEW_SETUP_LOOP, "cell 8 setup loop"))

    # cell 12 -- graft flags (v15 only)
    if with_v30_grafts:
        _set_cell(cells[12], _replace_once(base_texts[12], OLD_FLAGS_BLOCK, NEW_FLAGS_BLOCK, "cell 12 flags"))

    # --- mechanical diff assertions -------------------------------------------
    changed = [i for i, c in enumerate(cells) if _cell_text(c) != base_texts[i]]
    expected = [0, 6, 8, 12] if with_v30_grafts else [0, 6, 8]
    if changed != expected:
        raise SystemExit(f"BUILD FAIL: changed cells {changed}, expected {expected}")

    text_all = "\n".join(_cell_text(c) for c in cells)
    code_all = "\n".join(_cell_text(c) for c in cells if c["cell_type"] == "code")

    # The ACTION7 fix must survive verbatim in both builds.
    if 'MODEL_TO_ENGINE_ACTION["ACTION7"] = "ACTION7"' not in code_all:
        raise SystemExit("BUILD FAIL: the v10 ACTION7 reverse-map fix is gone")
    # The old model must be named nowhere in the code path.
    for stale in ("vrfai-qwen3-6-27b-fp8-hf-snapshot", "Qwen3.6-27B-FP8"):
        if stale in code_all:
            raise SystemExit(f"BUILD FAIL: stale model reference {stale!r} still in a code cell")
    if "Qwen/Qwen3.8-27B-FP8" not in code_all:
        raise SystemExit("BUILD FAIL: Qwen3.8 served-model name missing")
    # Without this the bundled setup cannot find the weights (Model != dataset mount).
    if "kaggle_input_paths[QWEN_MODEL_REF] = str(QWEN_MODEL_PATH)" not in code_all:
        raise SystemExit("BUILD FAIL: the model mount is not published into TAAF_KAGGLE_INPUT_PATHS")
    if "hours=8, minutes=20" not in code_all and "hours=8,minutes=20" not in code_all:
        raise SystemExit("BUILD FAIL: the 8h20m soft-end guard is gone (9h organizer wall)")
    if not with_v30_grafts and '"banking": True' not in code_all:
        raise SystemExit("BUILD FAIL: v14 must keep the v5 graft flags unchanged")
    if with_v30_grafts and '"goalkeep": True' not in code_all:
        raise SystemExit("BUILD FAIL: v15 must carry the v30 graft flags")
    del text_all

    out = OUT_DIR / f"kochi-loki-arc-agi-3.{version}.ipynb"
    out.write_text(json.dumps(nb, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"OK {version}: cells changed {changed} -> {out.relative_to(REPO)}")
    return out


def write_metadata(version: str) -> Path:
    meta = {
        "id": "soumyacryptic/kochi-loki-arc-agi-3",
        "title": "Kochi Loki - ARC-AGI-3",
        "code_file": "kochi-loki-arc-agi-3.ipynb",
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
    build("v14", with_v30_grafts=False)
    build("v15", with_v30_grafts=True)
    write_metadata("v14")
    write_metadata("v15")
    sys.exit(0)
