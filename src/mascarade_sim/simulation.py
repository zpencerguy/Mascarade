from __future__ import annotations

from collections import Counter
from random import Random
from statistics import mean
from typing import Any

from mascarade_sim.agents import RandomBot, create_agent
from mascarade_sim.agents.base import Agent
from mascarade_sim.config import load_ontology
from mascarade_sim.engine import perform_action, setup_game, summarize_history
from mascarade_sim.models import ActionKind


def play_random_game(
    player_count: int,
    seed: int | None = None,
    max_turns: int = 500,
    verbose: bool = False,
) -> dict[str, Any]:
    ontology = load_ontology()
    rng = Random(seed)
    state = setup_game(player_count, seed=seed, ontology=ontology)
    bot = RandomBot(rng=rng)
    while state.winner_ids is None and state.turn_number <= max_turns:
        action = bot.choose_action(state, ontology)
        if action.kind == ActionKind.ANNOUNCE and action.character is not None:
            action.challengers = [
                player.id
                for player in state.players
                if player.id != action.actor_id and bot.choose_challenge(state, action.actor_id, action.character)
            ]
        perform_action(state, action, ontology)

    if state.winner_ids is None:
        richest = max(player.coins for player in state.players)
        state.winner_ids = [player.id for player in state.players if player.coins == richest]
        state.terminal_reason = "max_turns"

    summary = summarize_history(state)
    if verbose:
        summary["history"] = state.history
        summary["cards"] = dict(state.card_by_position)
    return summary


def run_random_games(player_count: int, games: int, seed: int | None = None) -> dict[str, Any]:
    summaries = [play_random_game(player_count, seed=None if seed is None else seed + idx) for idx in range(games)]
    return summarize_games(summaries)


def play_strategy_game(
    strategy_names: list[str],
    seed: int | None = None,
    max_turns: int = 500,
    verbose: bool = False,
) -> dict[str, Any]:
    ontology = load_ontology()
    player_count = len(strategy_names)
    rng = Random(seed)
    state = setup_game(player_count, seed=seed, ontology=ontology)
    agents = [create_agent(name, rng=Random(rng.randrange(1_000_000_000))) for name in strategy_names]

    while state.winner_ids is None and state.turn_number <= max_turns:
        actor_id = state.active_player_id
        action = agents[actor_id].choose_action(state, ontology)
        if action.kind == ActionKind.ANNOUNCE and action.character is not None:
            action.challengers = _choose_challengers(agents, state, actor_id, action.character)
        perform_action(state, action, ontology)

    if state.winner_ids is None:
        richest = max(player.coins for player in state.players)
        state.winner_ids = [player.id for player in state.players if player.coins == richest]
        state.terminal_reason = "max_turns"

    summary = summarize_history(state)
    summary["strategies_by_seat"] = {seat: name for seat, name in enumerate(strategy_names)}
    if verbose:
        summary["history"] = state.history
        summary["cards"] = dict(state.card_by_position)
    return summary


def run_strategy_games(strategy_names: list[str], games: int, seed: int | None = None) -> dict[str, Any]:
    return run_strategy_lineup(strategy_names, games, seed=seed, rotate_seats=False)


def run_strategy_lineup(
    strategy_names: list[str],
    games: int,
    seed: int | None = None,
    rotate_seats: bool = False,
) -> dict[str, Any]:
    summaries = [
        play_strategy_game(
            _rotate(strategy_names, idx) if rotate_seats else strategy_names,
            seed=None if seed is None else seed + idx,
        )
        for idx in range(games)
    ]
    result = summarize_games(summaries)
    result["strategies_by_seat"] = {seat: name for seat, name in enumerate(strategy_names)}
    result["seat_rotation"] = rotate_seats
    strategy_win_credit = _strategy_win_credit(summaries)
    result["strategy_win_credit"] = strategy_win_credit
    result["strategy_raw_wins"] = _strategy_raw_wins(summaries)
    result["strategy_win_rate_per_seat"] = _strategy_win_rate_per_seat(
        strategy_names,
        strategy_win_credit,
        games,
    )
    return result


def summarize_games(summaries: list[dict[str, Any]]) -> dict[str, Any]:
    winner_counter: Counter[int] = Counter()
    for summary in summaries:
        for winner_id in summary["winner_ids"]:
            winner_counter[winner_id] += 1

    terminal_reasons = Counter(summary["terminal_reason"] for summary in summaries)
    announcements = Counter(
        summary["most_announced_character"]
        for summary in summaries
        if summary["most_announced_character"] is not None
    )
    return {
        "games": len(summaries),
        "winner_distribution_by_seat": dict(sorted(winner_counter.items())),
        "average_turns": mean(summary["turns"] for summary in summaries),
        "average_ending_gold": _average_gold(summaries),
        "terminal_reasons": dict(terminal_reasons),
        "most_used_announced_character": announcements.most_common(1)[0][0] if announcements else None,
        "average_challenge_success_rate": mean(summary["challenge_success_rate"] for summary in summaries),
        "false_claim_fine_count": sum(summary["false_claim_fine_count"] for summary in summaries),
    }


def _choose_challengers(agents: list[Agent], state, actor_id: int, character: str) -> list[int]:
    return [
        player.id
        for player in state.players
        if player.id != actor_id and agents[player.id].choose_challenge(state, actor_id, character)
    ]


def _strategy_win_credit(summaries: list[dict[str, Any]]) -> dict[str, float]:
    credit: Counter[str] = Counter()
    for summary in summaries:
        winners = summary["winner_ids"]
        if not winners:
            continue
        share = 1 / len(winners)
        for winner_id in winners:
            credit[summary["strategies_by_seat"][winner_id]] += share
    return dict(sorted(credit.items()))


def _strategy_raw_wins(summaries: list[dict[str, Any]]) -> dict[str, int]:
    wins: Counter[str] = Counter()
    for summary in summaries:
        for winner_id in summary["winner_ids"]:
            wins[summary["strategies_by_seat"][winner_id]] += 1
    return dict(sorted(wins.items()))


def _strategy_win_rate_per_seat(
    strategy_names: list[str],
    strategy_win_credit: dict[str, float],
    games: int,
) -> dict[str, float]:
    seat_counts = Counter(strategy_names)
    return {
        strategy: strategy_win_credit.get(strategy, 0.0) / seat_counts[strategy] / games
        for strategy in sorted(seat_counts)
    }


def _rotate(items: list[str], offset: int) -> list[str]:
    if not items:
        return []
    offset = offset % len(items)
    return [*items[offset:], *items[:offset]]


def _average_gold(summaries: list[dict[str, Any]]) -> dict[int, float]:
    seats = sorted(summaries[0]["ending_gold"])
    return {
        seat: mean(summary["ending_gold"][seat] for summary in summaries)
        for seat in seats
    }
