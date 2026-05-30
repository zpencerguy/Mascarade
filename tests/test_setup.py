import unittest

from mascarade_sim.config import load_ontology
from mascarade_sim.engine import setup_game


class SetupTests(unittest.TestCase):
    def test_setup_loads_dynamic_ontology_and_requires_judge(self):
        ontology = load_ontology()
        state = setup_game(6, seed=1, ontology=ontology)

        self.assertEqual(len(state.players), 6)
        self.assertEqual(len(state.positions), 6)
        self.assertIn("Judge", state.card_by_position.values())
        self.assertEqual(ontology.handler_for("Queen"), "queen")

    def test_setup_rejects_missing_judge(self):
        with self.assertRaisesRegex(ValueError, "Judge"):
            setup_game(6, characters=["Bishop", "King", "Queen", "Witch", "Cheat", "Thief"])


if __name__ == "__main__":
    unittest.main()
