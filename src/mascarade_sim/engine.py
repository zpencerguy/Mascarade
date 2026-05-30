from __future__ import annotations

import random
from collections import Counter
from typing import Any

from mascarade_sim.characters import registry, transfer
from mascarade_sim.config import Ontology, load_ontology
from mascarade_sim.models import Action, ActionKind, ActionResult, CardPosition, EventKind, GameState, Player


def setup_game(
    player_count: int,
    characters: list[str] | None = None,
    seed: int | None = None,
    ontology: Ontology | None = None,
) -> GameState:
    if not 4 <= player_count <= 13:
        raise ValueError("Regular Mascarade rules support 4 to 13 players")

    ontology = ontology or load_ontology()
    setup = ontology.setup_for(player_count)
    setup_deck = list(characters or setup.characters)
    if len(setup_deck) < player_count:
        raise ValueError(f"Expected at least {player_count} setup cards, got {len(setup_deck)}")
    if "Judge" not in setup_deck:
        raise ValueError("Judge must always be in play")

    rng = random.Random(seed)
    shuffled = list(setup_deck)
    rng.shuffle(shuffled)

    positions = [CardPosition(id=f"player:{idx}", owner_player_id=idx) for idx in range(player_count)]
    middle_count = len(setup_deck) - player_count
    positions.extend(CardPosition(id=f"middle:{idx}", is_middle=True) for idx in range(middle_count))
    card_by_position = {position.id: shuffled[idx] for idx, position in enumerate(positions)}
    state = GameState(
        players=[Player(id=idx) for idx in range(player_count)],
        positions=positions,
        card_by_position=card_by_position,
        character_set=setup_deck,
    )
    state.record(EventKind.SETUP, player_count=player_count, positions=[position.id for position in positions])
    return state


def legal_swap_targets(state: GameState, actor_id: int) -> list[str]:
    actor_position = state.player_position_id(actor_id)
    return [position.id for position in state.positions if position.id != actor_position]


def perform_forced_swap(
    state: GameState,
    actor_id: int,
    target_position_id: str,
    actually_swap: bool,
) -> ActionResult:
    if state.turn_number > 4:
        raise ValueError("Forced swap is only legal during the first four turns")
    if actor_id != state.active_player_id:
        raise ValueError("Action actor must be the active player")
    return _perform_swap(state, actor_id, target_position_id, actually_swap, forced=True)


def perform_swap_action(
    state: GameState,
    actor_id: int,
    target_position_id: str,
    actually_swap: bool,
) -> ActionResult:
    if state.turn_number <= 4:
        raise ValueError("Only forced swap is legal during the first four turns")
    if actor_id != state.active_player_id:
        raise ValueError("Action actor must be the active player")
    return _perform_swap(state, actor_id, target_position_id, actually_swap, forced=False)


def _perform_swap(
    state: GameState,
    actor_id: int,
    target_position_id: str,
    actually_swap: bool,
    forced: bool,
) -> ActionResult:
    own_position_id = state.player_position_id(actor_id)
    if target_position_id == own_position_id:
        raise ValueError("Cannot swap a card with itself")
    state.position(target_position_id)
    if actually_swap:
        state.card_by_position[own_position_id], state.card_by_position[target_position_id] = (
            state.card_by_position[target_position_id],
            state.card_by_position[own_position_id],
        )
    event = state.record(
        EventKind.SWAP,
        actor_id=actor_id,
        target_position_id=target_position_id,
        actually_swap=actually_swap,
        forced=forced,
    )
    _advance_turn(state)
    return ActionResult(events=[event], winner_ids=state.winner_ids)


def perform_peek_action(state: GameState, actor_id: int) -> ActionResult:
    if state.turn_number <= 4:
        raise ValueError("Peek is not legal during the first four turns")
    if actor_id != state.active_player_id:
        raise ValueError("Action actor must be the active player")
    event = state.record(EventKind.PEEK, actor_id=actor_id, character=state.card_for_player(actor_id))
    _advance_turn(state)
    return ActionResult(events=[event], winner_ids=state.winner_ids)


def perform_announce_action(
    state: GameState,
    actor_id: int,
    character: str,
    challengers: list[int] | None = None,
    policy_context: dict[str, Any] | None = None,
    ontology: Ontology | None = None,
) -> ActionResult:
    if state.turn_number <= 4:
        raise ValueError("Announce is not legal during the first four turns")
    if actor_id != state.active_player_id:
        raise ValueError("Action actor must be the active player")
    if state.revealed_last_turn_by_player.get(actor_id) == character:
        raise ValueError("A player cannot announce the same character revealed during the immediately previous turn")

    ontology = ontology or load_ontology()
    challengers = challengers or []
    policy_context = policy_context or {}
    claimants = [actor_id, *challengers]
    if len(set(claimants)) != len(claimants):
        raise ValueError("Claimants must be unique")

    events = [state.record(EventKind.ANNOUNCE, actor_id=actor_id, character=character, challengers=challengers)]
    true_claimants: list[int] = []
    revealed_by_player: dict[int, str] = {}

    if challengers:
        for claimant_id in claimants:
            revealed = state.card_for_player(claimant_id)
            revealed_by_player[claimant_id] = revealed
            events.append(state.record(EventKind.REVEAL, player_id=claimant_id, character=revealed))
            if revealed == character:
                true_claimants.append(claimant_id)
    else:
        true_claimants = [actor_id]

    if true_claimants:
        power_actor = true_claimants[0]
        context = dict(policy_context)
        if character == "Peasant":
            context["revealed_peasant_player_ids"] = true_claimants
        events.extend(resolve_character_power(state, power_actor, character, context, ontology))

    if challengers:
        for claimant_id in claimants:
            if claimant_id not in true_claimants:
                amount = transfer(state, claimant_id, None, 1)
                events.append(state.record(EventKind.FINE, player_id=claimant_id, amount=amount, character=character))
        state.revealed_last_turn_by_player = revealed_by_player
    else:
        state.revealed_last_turn_by_player = {}

    check_terminal_state(state)
    _advance_turn(state)
    return ActionResult(events=events, winner_ids=state.winner_ids)


def resolve_character_power(
    state: GameState,
    actor_id: int,
    character: str,
    policy_context: dict[str, Any] | None = None,
    ontology: Ontology | None = None,
) -> list[dict[str, Any]]:
    ontology = ontology or load_ontology()
    handler_name = ontology.handler_for(character)
    events = registry.resolve(handler_name)(state, actor_id, policy_context or {})
    check_terminal_state(state)
    return events


def check_terminal_state(state: GameState) -> list[int] | None:
    if state.winner_ids is not None:
        _record_terminal_once(state)
        return state.winner_ids

    thirteen_plus = [player.id for player in state.players if player.coins >= 13]
    if thirteen_plus:
        state.winner_ids = thirteen_plus
        state.terminal_reason = "thirteen_gold"
        _record_terminal_once(state)
        return state.winner_ids

    if any(player.coins <= 0 for player in state.players):
        richest = max(player.coins for player in state.players)
        state.winner_ids = [player.id for player in state.players if player.coins == richest]
        state.terminal_reason = "bankruptcy"
        _record_terminal_once(state)
        return state.winner_ids

    return None


def perform_action(state: GameState, action: Action, ontology: Ontology | None = None) -> ActionResult:
    if action.kind == ActionKind.FORCED_SWAP:
        return perform_forced_swap(state, action.actor_id, action.target_position_id or "", action.actually_swap)
    if action.kind == ActionKind.SWAP:
        return perform_swap_action(state, action.actor_id, action.target_position_id or "", action.actually_swap)
    if action.kind == ActionKind.PEEK:
        return perform_peek_action(state, action.actor_id)
    if action.kind == ActionKind.ANNOUNCE:
        if action.character is None:
            raise ValueError("Announce action requires a character")
        return perform_announce_action(
            state,
            action.actor_id,
            action.character,
            challengers=action.challengers,
            policy_context=action.context,
            ontology=ontology,
        )
    raise ValueError(f"Unsupported action kind: {action.kind}")


def summarize_history(state: GameState) -> dict[str, Any]:
    announced = Counter(event["character"] for event in state.history if event["kind"] == EventKind.ANNOUNCE.value)
    challenged_announcements = 0
    successful_challenges = 0
    current_announcement: dict[str, Any] | None = None
    current_reveals: list[dict[str, Any]] = []
    for event in state.history:
        if event["kind"] == EventKind.ANNOUNCE.value:
            if current_announcement and current_announcement.get("challengers"):
                challenged_announcements += 1
                if any(reveal["character"] == current_announcement["character"] for reveal in current_reveals):
                    successful_challenges += 1
            current_announcement = event
            current_reveals = []
        elif event["kind"] == EventKind.REVEAL.value:
            current_reveals.append(event)
    if current_announcement and current_announcement.get("challengers"):
        challenged_announcements += 1
        if any(reveal["character"] == current_announcement["character"] for reveal in current_reveals):
            successful_challenges += 1

    false_fines = [event for event in state.history if event["kind"] == EventKind.FINE.value]
    return {
        "turns": state.turn_number - 1,
        "winner_ids": state.winner_ids or [],
        "terminal_reason": state.terminal_reason,
        "ending_gold": {player.id: player.coins for player in state.players},
        "most_announced_character": announced.most_common(1)[0][0] if announced else None,
        "announcements": sum(announced.values()),
        "challenged_announcements": challenged_announcements,
        "challenge_success_rate": (
            successful_challenges / challenged_announcements if challenged_announcements else 0.0
        ),
        "false_claim_fine_count": len(false_fines),
    }


def _advance_turn(state: GameState) -> None:
    if state.winner_ids is not None:
        return
    state.turn_number += 1
    state.turn_index = (state.turn_index + 1) % len(state.players)


def _record_terminal_once(state: GameState) -> None:
    if not state.history or state.history[-1]["kind"] != EventKind.TERMINAL.value:
        state.record(EventKind.TERMINAL, reason=state.terminal_reason, winner_ids=state.winner_ids)
