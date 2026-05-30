from __future__ import annotations

from random import Random
from typing import Callable

from mascarade_sim.agents.base import Agent
from mascarade_sim.agents.random_bot import RandomBot
from mascarade_sim.config import Ontology
from mascarade_sim.engine import legal_swap_targets
from mascarade_sim.models import Action, ActionKind, GameState


class AlwaysSwapBot(RandomBot):
    def choose_action(self, state: GameState, ontology: Ontology) -> Action:
        actor_id = state.active_player_id
        kind = ActionKind.FORCED_SWAP if state.turn_number <= 4 else ActionKind.SWAP
        return Action(
            kind=kind,
            actor_id=actor_id,
            target_position_id=self.rng.choice(legal_swap_targets(state, actor_id)),
            actually_swap=self.rng.choice([True, False]),
        )


class NeverChallengeBot(RandomBot):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(challenge_probability=0.0, *args, **kwargs)


class ChallengeHeavyBot(RandomBot):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(challenge_probability=0.65, *args, **kwargs)


class EarlyBlufferBot(RandomBot):
    def __init__(self, early_real_turns: int = 8, *args, **kwargs) -> None:
        super().__init__(challenge_probability=0.18, *args, **kwargs)
        self.early_real_turns = early_real_turns
        self.claim_priority = ["Cheat", "King", "Queen", "Judge", "Bishop", "Witch", "Thief", "Fool"]

    def choose_action(self, state: GameState, ontology: Ontology) -> Action:
        if state.turn_number <= 4:
            return super().choose_action(state, ontology)
        if state.turn_number <= 4 + self.early_real_turns:
            action = _claim_first_available(self, state, self.claim_priority)
            if action is not None:
                return action
        return super().choose_action(state, ontology)


class MoneyClaimBot(RandomBot):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(challenge_probability=0.12, *args, **kwargs)
        self.claim_priority = ["Widow", "King", "Queen", "Peasant", "Fool", "Judge", "Bishop", "Thief"]

    def choose_action(self, state: GameState, ontology: Ontology) -> Action:
        if state.turn_number <= 4:
            return super().choose_action(state, ontology)
        action = _claim_first_available(self, state, self.claim_priority)
        if action is not None:
            return action
        return super().choose_action(state, ontology)


class PeekThenClaimBot(RandomBot):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(challenge_probability=0.22, *args, **kwargs)
        self.known_character: str | None = None

    def choose_action(self, state: GameState, ontology: Ontology) -> Action:
        actor_id = state.active_player_id
        if state.turn_number <= 4:
            self.known_character = None
            return super().choose_action(state, ontology)
        blocked = state.revealed_last_turn_by_player.get(actor_id)
        if self.known_character is None or blocked == self.known_character:
            self.known_character = state.card_for_player(actor_id)
            return Action(kind=ActionKind.PEEK, actor_id=actor_id)
        return Action(
            kind=ActionKind.ANNOUNCE,
            actor_id=actor_id,
            character=self.known_character,
            context=self._power_context(state, actor_id, self.known_character),
        )


def create_agent(name: str, rng: Random | None = None) -> Agent:
    try:
        return STRATEGIES[name](rng=rng)
    except KeyError as exc:
        options = ", ".join(sorted(STRATEGIES))
        raise ValueError(f"Unknown strategy {name!r}. Available strategies: {options}") from exc


STRATEGIES: dict[str, Callable[..., Agent]] = {
    "random": RandomBot,
    "always_swap": AlwaysSwapBot,
    "never_challenge": NeverChallengeBot,
    "challenge_heavy": ChallengeHeavyBot,
    "early_bluffer": EarlyBlufferBot,
    "money_claim": MoneyClaimBot,
    "peek_then_claim": PeekThenClaimBot,
}


def _claim_first_available(bot: RandomBot, state: GameState, priority: list[str]) -> Action | None:
    actor_id = state.active_player_id
    blocked = state.revealed_last_turn_by_player.get(actor_id)
    available = set(state.character_set)
    for character in priority:
        if character in available and character != blocked:
            return Action(
                kind=ActionKind.ANNOUNCE,
                actor_id=actor_id,
                character=character,
                context=bot._power_context(state, actor_id, character),
            )
    return None
