from __future__ import annotations

from mascarade_sim.agents.base import Agent
from mascarade_sim.config import Ontology
from mascarade_sim.engine import legal_swap_targets
from mascarade_sim.models import Action, ActionKind, GameState


class RandomBot(Agent):
    def __init__(self, challenge_probability: float = 0.18, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.challenge_probability = challenge_probability

    def choose_action(self, state: GameState, ontology: Ontology) -> Action:
        actor_id = state.active_player_id
        targets = legal_swap_targets(state, actor_id)
        if state.turn_number <= 4:
            return Action(
                kind=ActionKind.FORCED_SWAP,
                actor_id=actor_id,
                target_position_id=self.rng.choice(targets),
                actually_swap=self.rng.choice([True, False]),
            )

        legal_kinds = [ActionKind.SWAP, ActionKind.PEEK, ActionKind.ANNOUNCE]
        blocked = state.revealed_last_turn_by_player.get(actor_id)
        legal_characters = [name for name in sorted(set(state.character_set)) if name != blocked]
        if not legal_characters:
            legal_kinds.remove(ActionKind.ANNOUNCE)

        kind = self.rng.choice(legal_kinds)
        if kind == ActionKind.SWAP:
            return Action(
                kind=kind,
                actor_id=actor_id,
                target_position_id=self.rng.choice(targets),
                actually_swap=self.rng.choice([True, False]),
            )
        if kind == ActionKind.PEEK:
            return Action(kind=kind, actor_id=actor_id)

        character = self.rng.choice(legal_characters)
        return Action(
            kind=ActionKind.ANNOUNCE,
            actor_id=actor_id,
            character=character,
            context=self._power_context(state, actor_id, character),
        )

    def choose_challenge(self, state: GameState, actor_id: int, character: str) -> bool:
        return self.rng.random() < self.challenge_probability

    def _power_context(self, state: GameState, actor_id: int, character: str) -> dict:
        other_players = [player.id for player in state.players if player.id != actor_id]
        targets = legal_swap_targets(state, actor_id)
        context: dict = {}
        if character in {"Bishop", "Witch"}:
            context["target_player_id"] = self.rng.choice(other_players)
        elif character == "Fool":
            first, second = self.rng.sample(targets, 2)
            context.update(first_position_id=first, second_position_id=second, actually_swap=self.rng.choice([True, False]))
        elif character == "Spy":
            context.update(target_position_id=self.rng.choice(targets), actually_swap=self.rng.choice([True, False]))
        elif character == "Inquisitor":
            target_id = self.rng.choice(other_players)
            context.update(
                target_player_id=target_id,
                guessed_character=self.rng.choice(sorted(set(state.character_set))),
            )
        return context
