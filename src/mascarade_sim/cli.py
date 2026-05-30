from __future__ import annotations

import argparse
import json

from mascarade_sim.agents import STRATEGIES
from mascarade_sim.simulation import play_random_game, play_strategy_game, run_random_games, run_strategy_lineup


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

    experiment = subparsers.add_parser("experiment", help="Run named bot strategies against each other")
    experiment.add_argument("--seats", nargs="+", required=True, help=f"Strategy per seat. Options: {', '.join(sorted(STRATEGIES))}")
    experiment.add_argument("--games", type=int, default=1000)
    experiment.add_argument("--seed", type=int)
    experiment.add_argument("--verbose", action="store_true")
    experiment.add_argument("--rotate-seats", action="store_true", help="Rotate the listed strategies through seats across games")

    args = parser.parse_args()
    if args.command == "single":
        result = play_random_game(args.players, seed=args.seed, verbose=args.verbose)
    elif args.command == "run":
        result = run_random_games(args.players, args.games, seed=args.seed)
    elif args.games == 1:
        result = play_strategy_game(args.seats, seed=args.seed, verbose=args.verbose)
    else:
        result = run_strategy_lineup(args.seats, args.games, seed=args.seed, rotate_seats=args.rotate_seats)
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
