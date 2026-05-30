from __future__ import annotations

from collections import Counter
from random import Random
from statistics import mean
from typing import Any

from mascarade_sim.agents import RandomBot
from mascarade_sim.config import load_ontology
from mascarade_sim.engine import perform_action, setup_game, summarize_history


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
        "games": games,
        "winner_distribution_by_seat": dict(sorted(winner_counter.items())),
        "average_turns": mean(summary["turns"] for summary in summaries),
        "average_ending_gold": _average_gold(summaries),
        "terminal_reasons": dict(terminal_reasons),
        "most_used_announced_character": announcements.most_common(1)[0][0] if announcements else None,
        "average_challenge_success_rate": mean(summary["challenge_success_rate"] for summary in summaries),
        "false_claim_fine_count": sum(summary["false_claim_fine_count"] for summary in summaries),
    }


def _average_gold(summaries: list[dict[str, Any]]) -> dict[int, float]:
    seats = sorted(summaries[0]["ending_gold"])
    return {
        seat: mean(summary["ending_gold"][seat] for summary in summaries)
        for seat in seats
    }
