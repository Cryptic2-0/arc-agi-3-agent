"""Offline baseline runner — plays bundled environment_files/ games locally, no API.

main.py is hardwired to fetch the game list from the online /api/games endpoint, so it
cannot reach offline play. This bypasses that: build the game list from the locally
scanned environments and drive the Swarm directly. Requires OPERATION_MODE=offline in .env.

Usage:  python -m uv run run_offline.py --agent=random --game=ls20
"""

import argparse
import json
import logging
import os
import sys

from dotenv import load_dotenv

load_dotenv(dotenv_path=".env.example")
load_dotenv(dotenv_path=".env", override=True)

from arc_agi import Arcade, OperationMode  # noqa: E402

from agents import AVAILABLE_AGENTS, Swarm  # noqa: E402

logger = logging.getLogger()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s",
        stream=sys.stdout,
    )

    parser = argparse.ArgumentParser(description="ARC-AGI-3 offline runner")
    parser.add_argument("-a", "--agent", default="random", choices=AVAILABLE_AGENTS.keys())
    parser.add_argument("-g", "--game", default=None, help="comma-separated game_id prefixes")
    args = parser.parse_args()

    if os.getenv("OPERATION_MODE", "").lower() != "offline":
        logger.warning("OPERATION_MODE is not 'offline' — set it in .env for pure-local play")

    # Discover locally available games (scans environment_files/ for metadata.json)
    arc = Arcade(operation_mode=OperationMode.OFFLINE)
    all_games = [e.game_id for e in arc.get_environments()]
    logger.info(f"Found {len(all_games)} local game(s)")

    games = all_games
    if args.game:
        prefixes = args.game.split(",")
        games = [g for g in all_games if any(g.startswith(p) for p in prefixes)]

    if not games:
        logger.error(f"No local game matched '{args.game}'. Available: {sorted(all_games)}")
        return

    logger.info(f"Playing: {games}")

    swarm = Swarm(args.agent, "https://three.arcprize.org", games)
    scorecard = swarm.main()
    if scorecard is not None:
        logger.info("--- LOCAL SCORECARD ---")
        logger.info(json.dumps(scorecard.model_dump(), indent=2, default=str))


if __name__ == "__main__":
    os.environ["TESTING"] = "False"
    main()
