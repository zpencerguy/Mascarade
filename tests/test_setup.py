import unittest

from mascarade_sim.config import load_ontology
from mascarade_sim.engine import setup_game


RULEBOOK_BASIC_SETUPS = {
    4: ["Judge", "Bishop", "King", "Queen", "Thief", "Cheat"],
    5: ["Judge", "Bishop", "King", "Queen", "Witch", "Cheat"],
    6: ["Judge", "Bishop", "King", "Queen", "Witch", "Cheat"],
    7: ["Judge", "Bishop", "King", "Fool", "Queen", "Thief", "Witch"],
    8: ["Judge", "Bishop", "King", "Fool", "Queen", "Witch", "Peasant", "Peasant"],
    9: ["Judge", "Bishop", "King", "Fool", "Queen", "Witch", "Peasant", "Peasant", "Cheat"],
    10: ["Judge", "Bishop", "King", "Fool", "Queen", "Witch", "Spy", "Peasant", "Peasant", "Cheat"],
    11: ["Judge", "Bishop", "King", "Fool", "Queen", "Witch", "Spy", "Peasant", "Peasant", "Cheat", "Inquisitor"],
    12: ["Judge", "Bishop", "King", "Fool", "Queen", "Witch", "Spy", "Peasant", "Peasant", "Cheat", "Inquisitor", "Widow"],
    13: ["Judge", "Bishop", "King", "Fool", "Queen", "Thief", "Witch", "Spy", "Peasant", "Peasant", "Cheat", "Inquisitor", "Widow"],
}


class SetupTests(unittest.TestCase):
    def test_setup_loads_dynamic_ontology_and_requires_judge(self):
        ontology = load_ontology()
        state = setup_game(6, seed=1, ontology=ontology)

        self.assertEqual(len(state.players), 6)
        self.assertEqual(len(state.positions), 6)
        self.assertIn("Judge", state.card_by_position.values())
        self.assertEqual(ontology.handler_for("Queen"), "queen")

    def test_rulebook_basic_setup_table_is_transcribed(self):
        ontology = load_ontology()

        for player_count, expected in RULEBOOK_BASIC_SETUPS.items():
            with self.subTest(player_count=player_count):
                self.assertEqual(list(ontology.setup_for(player_count).characters), expected)

    def test_four_and_five_player_games_use_middle_cards(self):
        self.assertEqual(sum(position.is_middle for position in setup_game(4, seed=1).positions), 2)
        self.assertEqual(sum(position.is_middle for position in setup_game(5, seed=1).positions), 1)

    def test_six_plus_games_use_no_middle_cards_by_default(self):
        for player_count in range(6, 14):
            with self.subTest(player_count=player_count):
                self.assertFalse(any(position.is_middle for position in setup_game(player_count, seed=1).positions))

    def test_setup_rejects_missing_judge(self):
        with self.assertRaisesRegex(ValueError, "Judge"):
            setup_game(6, characters=["Bishop", "King", "Queen", "Witch", "Cheat", "Thief"])


if __name__ == "__main__":
    unittest.main()
