"""GraphExplorer — no-LLM graph-based exploration agent for ARC-AGI-3.

Strategy (recon: docs/recon.md). Winning preview agents were grounded explorers, not LLMs.

  1. State = hash of the 64x64 grid (discrete node id).
  2. Transition graph: graph[state][move] -> next_state, built as we act.
  3. A "move" is either a simple action id (1-5,7) OR an ACTION6 click target ("6",(x,y)).
     ACTION6 is NOT one action: each distinct object pixel is its own move, so click games
     get genuinely explored instead of one random click.
  4. Learn move effects: track which moves change the frame; prune persistent no-ops.
  5. Policy: prefer an UNTESTED move in the current state (biased to productive ones) -> else BFS
     to the nearest state with untested moves and take the first move on that path -> else the most
     productive live move.
  6. ACTION6 targets = representative cells of non-background colour-segments (small-first, capped):
     likely buttons/objects, not the full 4096-pixel grid.
  7. On NOT_PLAYED / GAME_OVER: RESET, keeping the learned graph across resets.
"""

import hashlib
import random
from collections import deque
from typing import Any, Optional, Union

from arcengine import FrameData, GameAction, GameState

from agents.agent import Agent

DEAD_AFTER = 4          # simple action is a no-op after this many tries with zero change
ACTION6_DEAD_AFTER = 12  # give clicks more rope before declaring ACTION6 useless for a game
MAX_CLICK_TARGETS = 24   # cap ACTION6 branching per state (smallest segments first)

# A move: an int action id, or ("6", (x, y)) for an ACTION6 click target.
Move = Union[int, tuple[str, tuple[int, int]]]


class MyAgent(Agent):
    """Graph-based exploration agent. No LLM; pure interaction + search."""

    MAX_ACTIONS = 600

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        # Per-instance RNG: agents run as parallel threads, so a shared module-global
        # random.* is non-deterministic. Own Random(seed) => reproducible, thread-safe A/B.
        self.rng = random.Random(0)
        self.graph: dict[str, dict[Move, str]] = {}
        self.untested: dict[str, set[Move]] = {}
        # effect stats: key is a simple action id, or the literal 6 for the ACTION6 aggregate.
        self.effect: dict[int, list[int]] = {}
        # reward[move_key] = how often this move-type immediately preceded a levels_completed increase.
        self.reward: dict[int, int] = {}
        self.prev_levels: int = 0
        # cmodel[ctx_key] = [changed, unchanged] — online contextual frame-change predictor.
        # ctx_key for a click = (6, frame_feat, target_colour, target_size_bucket) so the agent learns
        # which KIND of click is productive (object-relative), not just "ACTION6" lumped together.
        self.cmodel: dict[tuple, list[int]] = {}
        self.targets_cache: dict[str, list[tuple[int, int]]] = {}
        # tfeat_by_state[state][(x,y)] = (colour, size_bucket) for each click target.
        self.tfeat_by_state: dict[str, dict[tuple[int, int], tuple[int, int]]] = {}
        self.prev_state: Optional[str] = None
        self.prev_move: Optional[Move] = None
        self.cur_feat: tuple = ()
        self.cur_state: Optional[str] = None
        self.prev_ctxkey: Optional[tuple] = None

    @property
    def name(self) -> str:
        return f"{super().name}.{self.MAX_ACTIONS}"

    # --- frame / state helpers ---------------------------------------------------
    @staticmethod
    def _grid_of(frame: FrameData) -> Optional[list[list[int]]]:
        if not frame.frame:
            return None
        return frame.frame[-1]

    @staticmethod
    def _hash(grid: list[list[int]]) -> str:
        flat = bytes(c & 0xFF for row in grid for c in row)
        return hashlib.blake2b(flat, digest_size=16).hexdigest()

    @staticmethod
    def _action_ids(frame: FrameData) -> list[int]:
        ids = []
        for a in frame.available_actions or []:
            ids.append(int(a) if not isinstance(a, int) else a)
        return [i for i in ids if i != 0]  # drop RESET (0)

    # --- ACTION6 click targets: representative cells of non-bg colour-segments ----
    def _click_targets(self, state: str, grid: list[list[int]]) -> list[tuple[int, int]]:
        cached = self.targets_cache.get(state)
        if cached is not None:
            return cached
        h = len(grid)
        w = len(grid[0]) if h else 0
        counts: dict[int, int] = {}
        for row in grid:
            for c in row:
                counts[c] = counts.get(c, 0) + 1
        background = max(counts, key=lambda k: counts[k]) if counts else 0

        seen = [[False] * w for _ in range(h)]
        segments: list[tuple[int, tuple[int, int]]] = []  # (size, representative (x,y))
        for sy in range(h):
            for sx in range(w):
                if seen[sy][sx] or grid[sy][sx] == background:
                    continue
                color = grid[sy][sx]
                q = deque([(sx, sy)])
                seen[sy][sx] = True
                cells = []
                while q:
                    x, y = q.popleft()
                    cells.append((x, y))
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < w and 0 <= ny < h and not seen[ny][nx] and grid[ny][nx] == color:
                            seen[ny][nx] = True
                            q.append((nx, ny))
                # representative = cell nearest the centroid (guaranteed on the object)
                cx = sum(p[0] for p in cells) / len(cells)
                cy = sum(p[1] for p in cells) / len(cells)
                rep = min(cells, key=lambda p: (p[0] - cx) ** 2 + (p[1] - cy) ** 2)
                segments.append((len(cells), rep, color))

        # buttons/markers tend to be small -> prioritise smaller segments, cap the count
        segments.sort(key=lambda s: s[0])
        chosen = segments[:MAX_CLICK_TARGETS]
        targets = [rep for _, rep, _ in chosen]
        self.tfeat_by_state[state] = {
            rep: (color, self._size_bucket(size)) for size, rep, color in chosen
        }
        self.targets_cache[state] = targets
        return targets

    @staticmethod
    def _size_bucket(size: int) -> int:
        # log-ish buckets: 1, 2-4, 5-16, 17-64, 65+ → 0..4
        if size <= 1:
            return 0
        if size <= 4:
            return 1
        if size <= 16:
            return 2
        if size <= 64:
            return 3
        return 4

    def _ctx_key(self, move: Move) -> tuple:
        if isinstance(move, tuple):  # ACTION6 click target
            tf = self.tfeat_by_state.get(self.cur_state or "", {}).get(move[1], (0, 0))
            return (6, self.cur_feat, tf[0], tf[1])
        return (move, self.cur_feat)

    # --- effect / pruning --------------------------------------------------------
    @staticmethod
    def _effect_key(move: Move) -> int:
        return 6 if isinstance(move, tuple) else move

    def _is_dead(self, move: Move) -> bool:
        key = self._effect_key(move)
        tried, changed = self.effect.get(key, [0, 0])
        limit = ACTION6_DEAD_AFTER if key == 6 else DEAD_AFTER
        return tried >= limit and changed == 0

    def _change_rate(self, move: Move) -> float:
        tried, changed = self.effect.get(self._effect_key(move), [0, 0])
        return (changed / tried) if tried else 1.0

    def _moves_for(self, state: str, grid: list[list[int]], avail: list[int]) -> set[Move]:
        moves: set[Move] = set()
        for a in avail:
            if a == 6:
                if not self._is_dead(6):
                    for t in self._click_targets(state, grid):
                        moves.add(("6", t))
            else:
                moves.add(a)
        return moves

    def _bfs_first_move(self, start: str, live: set[Move]) -> Optional[Move]:
        q: deque[str] = deque([start])
        parent: dict[str, tuple[Optional[str], Optional[Move]]] = {start: (None, None)}
        while q:
            s = q.popleft()
            if s != start and (self.untested.get(s, set()) & live):
                cur = s
                while parent[cur][0] is not None and parent[cur][0] != start:
                    cur = parent[cur][0]  # type: ignore[assignment]
                return parent[cur][1]
            for move, nxt in self.graph.get(s, {}).items():
                if nxt not in parent:
                    parent[nxt] = (s, move)
                    q.append(nxt)
        return None

    @staticmethod
    def _feat(grid: list[list[int]]) -> tuple:
        # Cheap, coarse context feature so the change-predictor generalizes across similar frames.
        counts: dict[int, int] = {}
        total = 0
        for row in grid:
            for c in row:
                counts[c] = counts.get(c, 0) + 1
                total += 1
        if total == 0:
            return (0, 0)
        bg = max(counts.values())
        nonbg_frac = (total - bg) / total
        return (min(len(counts), 8), min(int(nonbg_frac * 8), 7))

    def _pchange(self, move: Move) -> float:
        # Thompson sample of P(this move changes the frame) in the current object-relative context.
        ch, un = self.cmodel.get(self._ctx_key(move), [0, 0])
        return self.rng.betavariate(ch + 1, un + 1)

    def _score(self, m: Move) -> tuple:
        # 1) move-types that have caused level-ups, 2) contextual change-prediction (Thompson),
        # 3) lifetime change-rate as a stable backstop. Fully deterministic via per-instance rng.
        return (self.reward.get(self._effect_key(m), 0), self._pchange(m), self._change_rate(m))

    def _best(self, pool: set[Move]) -> Move:
        # sort first so the rng tiebreak is assigned in a stable order (set iteration order is
        # PYTHONHASHSEED-dependent); with per-instance rng this makes selection fully deterministic.
        return max(sorted(pool, key=repr), key=self._score)

    def _choose_move(self, state: str, grid: list[list[int]], avail: list[int]) -> Move:
        moves = self.untested.get(state)
        if moves is None:
            moves = self._moves_for(state, grid, avail)
            self.untested[state] = set(moves)
        live = {m for m in moves if not self._is_dead(m)} or set(moves)
        if live:
            return self._best(live)
        nxt = self._bfs_first_move(state, set(self._all_live_moves()))
        if nxt is not None:
            return nxt
        # nothing untested reachable -> most productive currently-available move
        allm = self._moves_for(state, grid, avail) or {a for a in avail}
        return self._best(allm)

    def _all_live_moves(self) -> set[Move]:
        live: set[Move] = set()
        for s, ms in self.untested.items():
            live |= {m for m in ms if not self._is_dead(m)}
        return live

    # --- Agent interface ---------------------------------------------------------
    def is_done(self, frames: list[FrameData], latest_frame: FrameData) -> bool:
        return latest_frame.state is GameState.WIN

    def choose_action(
        self, frames: list[FrameData], latest_frame: FrameData
    ) -> GameAction:
        grid = self._grid_of(latest_frame)
        state = self._hash(grid) if grid is not None else None
        self.cur_feat = self._feat(grid) if grid is not None else ()
        self.cur_state = state

        # Reward signal: did the previous move just clear a level? (the strongest signal there is)
        lvl = latest_frame.levels_completed or 0
        if self.prev_move is not None and lvl > self.prev_levels:
            k = self._effect_key(self.prev_move)
            self.reward[k] = self.reward.get(k, 0) + (lvl - self.prev_levels)
        self.prev_levels = lvl

        if self.prev_state is not None and self.prev_move is not None and state is not None:
            changed = state != self.prev_state
            st = self.effect.setdefault(self._effect_key(self.prev_move), [0, 0])
            st[0] += 1
            if changed:
                st[1] += 1
            if self.prev_ctxkey is not None:
                cm = self.cmodel.setdefault(self.prev_ctxkey, [0, 0])
                cm[0 if changed else 1] += 1
            self.graph.setdefault(self.prev_state, {})[self.prev_move] = state
            self.untested.setdefault(self.prev_state, set()).discard(self.prev_move)

        if latest_frame.state in (GameState.NOT_PLAYED, GameState.GAME_OVER) or state is None:
            self.prev_state = None
            self.prev_move = None
            action = GameAction.RESET
            action.reasoning = "reset: not in a playable state"
            return action

        avail = self._action_ids(latest_frame)
        if not avail:
            self.prev_state = None
            self.prev_move = None
            return GameAction.RESET

        move = self._choose_move(state, grid, avail)
        if isinstance(move, tuple):
            x, y = move[1]
            action = GameAction.from_id(6)
            action.set_data({"x": x, "y": y})
            action.reasoning = {"strategy": "graph-explore", "click": f"({x},{y})"}
        else:
            action = GameAction.from_id(move)
            action.reasoning = f"graph-explore: action {move}"

        self.prev_state = state
        self.prev_move = move
        self.prev_ctxkey = self._ctx_key(move)
        return action
