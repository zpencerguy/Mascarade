from __future__ import annotations

from collections.abc import Callable
from typing import Any

from mascarade_sim.models import EventKind, GameState

PowerHandler = Callable[[GameState, int, dict[str, Any]], list[dict[str, Any]]]


class PowerRegistry:
    def __init__(self) -> None:
        self._handlers: dict[str, PowerHandler] = {}

    def register(self, name: str) -> Callable[[PowerHandler], PowerHandler]:
        def decorator(handler: PowerHandler) -> PowerHandler:
            self._handlers[name] = handler
            return handler

        return decorator

    def resolve(self, name: str) -> PowerHandler:
        try:
            return self._handlers[name]
        except KeyError as exc:
            raise ValueError(f"No character power handler registered for {name!r}") from exc


registry = PowerRegistry()


def transfer(state: GameState, source_id: int | None, target_id: int | None, amount: int) -> int:
    if amount <= 0:
        return 0
    if source_id is None:
        moved = min(amount, state.bank_coins)
        state.bank_coins -= moved
    else:
        source = state.player(source_id)
        moved = min(amount, source.coins)
        source.coins -= moved

    if target_id is None:
        state.courthouse_coins += moved
    else:
        state.player(target_id).coins += moved
    return moved


@registry.register("judge")
def judge(state: GameState, actor_id: int, context: dict[str, Any]) -> list[dict[str, Any]]:
    amount = state.courthouse_coins
    state.courthouse_coins = 0
    state.player(actor_id).coins += amount
    return [state.record(EventKind.POWER, character="Judge", actor_id=actor_id, amount=amount)]


@registry.register("bishop")
def bishop(state: GameState, actor_id: int, context: dict[str, Any]) -> list[dict[str, Any]]:
    target_id = context.get("target_player_id")
    others = [player for player in state.players if player.id != actor_id]
    richest = max(player.coins for player in others)
    legal_targets = [player.id for player in others if player.coins == richest]
    if target_id not in legal_targets:
        target_id = legal_targets[0]
    amount = transfer(state, target_id, actor_id, 2)
    return [state.record(EventKind.POWER, character="Bishop", actor_id=actor_id, target_id=target_id, amount=amount)]


@registry.register("king")
def king(state: GameState, actor_id: int, context: dict[str, Any]) -> list[dict[str, Any]]:
    amount = transfer(state, None, actor_id, 3)
    return [state.record(EventKind.POWER, character="King", actor_id=actor_id, amount=amount)]


@registry.register("queen")
def queen(state: GameState, actor_id: int, context: dict[str, Any]) -> list[dict[str, Any]]:
    amount = transfer(state, None, actor_id, 2)
    return [state.record(EventKind.POWER, character="Queen", actor_id=actor_id, amount=amount)]


@registry.register("fool")
def fool(state: GameState, actor_id: int, context: dict[str, Any]) -> list[dict[str, Any]]:
    amount = transfer(state, None, actor_id, 1)
    first = context.get("first_position_id")
    second = context.get("second_position_id")
    swapped = bool(context.get("actually_swap", False) and first and second and first != second)
    if swapped:
        state.card_by_position[first], state.card_by_position[second] = (
            state.card_by_position[second],
            state.card_by_position[first],
        )
    return [
        state.record(
            EventKind.POWER,
            character="Fool",
            actor_id=actor_id,
            amount=amount,
            first_position_id=first,
            second_position_id=second,
            swapped=swapped,
        )
    ]


@registry.register("thief")
def thief(state: GameState, actor_id: int, context: dict[str, Any]) -> list[dict[str, Any]]:
    left_id = (actor_id - 1) % len(state.players)
    right_id = (actor_id + 1) % len(state.players)
    left_amount = transfer(state, left_id, actor_id, 1)
    right_amount = transfer(state, right_id, actor_id, 1)
    return [
        state.record(
            EventKind.POWER,
            character="Thief",
            actor_id=actor_id,
            left_id=left_id,
            right_id=right_id,
            amount=left_amount + right_amount,
        )
    ]


@registry.register("witch")
def witch(state: GameState, actor_id: int, context: dict[str, Any]) -> list[dict[str, Any]]:
    target_id = context.get("target_player_id")
    if target_id is None or target_id == actor_id:
        target_id = next(player.id for player in state.players if player.id != actor_id)
    actor = state.player(actor_id)
    target = state.player(target_id)
    actor.coins, target.coins = target.coins, actor.coins
    return [state.record(EventKind.POWER, character="Witch", actor_id=actor_id, target_id=target_id)]


@registry.register("spy")
def spy(state: GameState, actor_id: int, context: dict[str, Any]) -> list[dict[str, Any]]:
    own_position = state.player_position_id(actor_id)
    other = context.get("target_position_id")
    swapped = bool(context.get("actually_swap", False) and other and other != own_position)
    if swapped:
        state.card_by_position[own_position], state.card_by_position[other] = (
            state.card_by_position[other],
            state.card_by_position[own_position],
        )
    return [state.record(EventKind.POWER, character="Spy", actor_id=actor_id, target_position_id=other, swapped=swapped)]


@registry.register("peasant")
def peasant(state: GameState, actor_id: int, context: dict[str, Any]) -> list[dict[str, Any]]:
    revealed_peasants = context.get("revealed_peasant_player_ids", [actor_id])
    amount_each = 2 if len(set(revealed_peasants)) >= 2 else 1
    events = []
    for player_id in sorted(set(revealed_peasants)):
        amount = transfer(state, None, player_id, amount_each)
        events.append(state.record(EventKind.POWER, character="Peasant", actor_id=player_id, amount=amount))
    return events


@registry.register("cheat")
def cheat(state: GameState, actor_id: int, context: dict[str, Any]) -> list[dict[str, Any]]:
    won = state.player(actor_id).coins >= 10
    if won:
        state.winner_ids = [actor_id]
        state.terminal_reason = "cheat"
    return [state.record(EventKind.POWER, character="Cheat", actor_id=actor_id, won=won)]


@registry.register("inquisitor")
def inquisitor(state: GameState, actor_id: int, context: dict[str, Any]) -> list[dict[str, Any]]:
    target_id = context["target_player_id"]
    guessed_character = context["guessed_character"]
    actual_character = state.card_for_player(target_id)
    correct = guessed_character == actual_character
    amount = 0 if correct else transfer(state, target_id, actor_id, 4)
    return [
        state.record(
            EventKind.POWER,
            character="Inquisitor",
            actor_id=actor_id,
            target_id=target_id,
            guessed_character=guessed_character,
            actual_character=actual_character,
            correct=correct,
            amount=amount,
        )
    ]


@registry.register("widow")
def widow(state: GameState, actor_id: int, context: dict[str, Any]) -> list[dict[str, Any]]:
    needed = max(0, 10 - state.player(actor_id).coins)
    amount = transfer(state, None, actor_id, needed)
    return [state.record(EventKind.POWER, character="Widow", actor_id=actor_id, amount=amount)]
