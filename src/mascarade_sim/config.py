from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_ONTOLOGY_PATH = PROJECT_ROOT / "config" / "ontology.json"


@dataclass(frozen=True)
class CharacterSpec:
    name: str
    count: int
    min_players: int
    mandatory: bool
    handler: str
    tags: tuple[str, ...]


@dataclass(frozen=True)
class SetupSpec:
    players: int
    characters: tuple[str, ...]
    middle_cards: tuple[str, ...] = ()


@dataclass(frozen=True)
class Ontology:
    version: int
    schemas: dict[str, Any]
    characters: dict[str, CharacterSpec]
    setups: dict[int, SetupSpec]

    def setup_for(self, player_count: int) -> SetupSpec:
        try:
            return self.setups[player_count]
        except KeyError as exc:
            raise ValueError(f"No setup configured for {player_count} players") from exc

    def handler_for(self, character: str) -> str:
        try:
            return self.characters[character].handler
        except KeyError as exc:
            raise ValueError(f"Unknown character in ontology: {character}") from exc

    def all_character_names(self) -> list[str]:
        return list(self.characters)


def load_ontology(path: str | Path = DEFAULT_ONTOLOGY_PATH) -> Ontology:
    data = json.loads(Path(path).read_text())
    _validate_collection(data, "characters", "character")
    _validate_collection(data, "setups", "setup")

    characters = {
        item["name"]: CharacterSpec(
            name=item["name"],
            count=int(item.get("count", 1)),
            min_players=int(item["min_players"]),
            mandatory=bool(item.get("mandatory", False)),
            handler=item["handler"],
            tags=tuple(item.get("tags", ())),
        )
        for item in data["characters"]
    }
    setups = {
        int(item["players"]): SetupSpec(
            players=int(item["players"]),
            characters=tuple(item["characters"]),
            middle_cards=tuple(item.get("middle_cards", ())),
        )
        for item in data["setups"]
    }
    ontology = Ontology(
        version=int(data["version"]),
        schemas=data.get("schemas", {}),
        characters=characters,
        setups=setups,
    )
    _validate_references(ontology)
    return ontology


def _validate_collection(data: dict[str, Any], collection: str, schema_name: str) -> None:
    schema = data.get("schemas", {}).get(schema_name, {})
    required = schema.get("required", ())
    for index, item in enumerate(data.get(collection, ())):
        missing = [key for key in required if key not in item]
        if missing:
            raise ValueError(f"{collection}[{index}] missing required fields: {missing}")


def _validate_references(ontology: Ontology) -> None:
    for setup in ontology.setups.values():
        names = [*setup.characters, *setup.middle_cards]
        if "Judge" not in names:
            raise ValueError(f"{setup.players}-player setup must include Judge")
        if len(names) < setup.players:
            raise ValueError(f"{setup.players}-player setup has fewer cards than players")
        if setup.players in {4, 5} and len(names) != 6:
            raise ValueError(f"{setup.players}-player setup must use 6 character cards")
        if setup.players >= 6 and len(names) != setup.players:
            raise ValueError(f"{setup.players}-player setup must use exactly {setup.players} character cards")
        if names.count("Peasant") not in {0, 2}:
            raise ValueError(f"{setup.players}-player setup must include both Peasants or neither")
        unknown = sorted({name for name in names if name not in ontology.characters})
        if unknown:
            raise ValueError(f"{setup.players}-player setup references unknown characters: {unknown}")
