from __future__ import annotations

from abc import ABC, abstractmethod
from random import Random

from mascarade_sim.config import Ontology
from mascarade_sim.models import Action, GameState


class Agent(ABC):
    def __init__(self, rng: Random | None = None) -> None:
        self.rng = rng or Random()

    @abstractmethod
    def choose_action(self, state: GameState, ontology: Ontology) -> Action:
        """Choose one legal action for the current active player."""

    def choose_challenge(self, state: GameState, actor_id: int, character: str) -> bool:
        """Decide whether this agent contests another player's character claim."""
        return False
