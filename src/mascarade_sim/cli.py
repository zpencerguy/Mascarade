from __future__ import annotations

import argparse
import json

from mascarade_sim.simulation import play_random_game, run_random_games


def main() -> None:
    parser = argparse.ArgumentParser(prog="mascarade-sim")
    subparsers = parser.add_subparsers(dest="command", required=True)

    single = subparsers.add_parser("single", help="Run one random game")
    single.add_argument("--players", type=int, default=6)
    single.add_argument("--seed", type=int)
    single.add_argument("--verbose", action="store_true")

    run = subparsers.add_parser("run", help="Run many random games")
    run.add_argument("--players", type=int, default=6)
    run.add_argument("--games", type=int, default=1000)
    run.add_argument("--seed", type=int)

    args = parser.parse_args()
    if args.command == "single":
        result = play_random_game(args.players, seed=args.seed, verbose=args.verbose)
    else:
        result = run_random_games(args.players, args.games, seed=args.seed)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
