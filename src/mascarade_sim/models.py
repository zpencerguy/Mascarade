from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ActionKind(str, Enum):
    FORCED_SWAP = "forced_swap"
    SWAP = "swap"
    PEEK = "peek"
    ANNOUNCE = "announce"


class EventKind(str, Enum):
    SETUP = "setup"
    SWAP = "swap"
    PEEK = "peek"
    ANNOUNCE = "announce"
    REVEAL = "reveal"
    POWER = "power"
    COINS = "coins"
    FINE = "fine"
    TERMINAL = "terminal"


@dataclass
class Player:
    id: int
    coins: int = 6


@dataclass(frozen=True)
class CardPosition:
    id: str
    owner_player_id: int | None = None
    is_middle: bool = False


@dataclass
class Action:
    kind: ActionKind
    actor_id: int
    target_position_id: str | None = None
    character: str | None = None
    challengers: list[int] = field(default_factory=list)
    actually_swap: bool = False
    context: dict[str, Any] = field(default_factory=dict)


@dataclass
class ActionResult:
    events: list[dict[str, Any]]
    winner_ids: list[int] | None = None


@dataclass
class GameState:
    players: list[Player]
    positions: list[CardPosition]
    card_by_position: dict[str, str]
    character_set: list[str]
    bank_coins: int = 194
    courthouse_coins: int = 0
    turn_index: int = 0
    turn_number: int = 1
    revealed_last_turn_by_player: dict[int, str] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)
    winner_ids: list[int] | None = None
    terminal_reason: str | None = None

    def player(self, player_id: int) -> Player:
        return self.players[player_id]

    def player_position_id(self, player_id: int) -> str:
        return f"player:{player_id}"

    def player_position(self, player_id: int) -> CardPosition:
        return self.position(self.player_position_id(player_id))

    def position(self, position_id: str) -> CardPosition:
        for position in self.positions:
            if position.id == position_id:
                return position
        raise KeyError(f"Unknown position: {position_id}")

    def owner_for_position(self, position_id: str) -> int | None:
        return self.position(position_id).owner_player_id

    def card_for_player(self, player_id: int) -> str:
        return self.card_by_position[self.player_position_id(player_id)]

    def record(self, kind: EventKind | str, **payload: Any) -> dict[str, Any]:
        event = {"kind": kind.value if isinstance(kind, EventKind) else kind, **payload}
        self.history.append(event)
        return event

    @property
    def active_player_id(self) -> int:
        return self.turn_index % len(self.players)
