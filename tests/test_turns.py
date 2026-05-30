import unittest

from mascarade_sim.engine import perform_announce_action, perform_forced_swap, perform_peek_action, setup_game


class TurnTests(unittest.TestCase):
    def test_first_four_turns_only_allow_forced_swap(self):
        state = setup_game(6, seed=1)

        with self.assertRaisesRegex(ValueError, "Peek"):
            perform_peek_action(state, 0)

        perform_forced_swap(state, 0, "player:1", actually_swap=False)
        self.assertEqual(state.turn_number, 2)

    def test_revealed_character_cannot_be_announced_by_that_player_next_turn(self):
        state = setup_game(6, seed=1)
        state.turn_number = 5
        state.turn_index = 0
        state.revealed_last_turn_by_player = {0: "King"}

        with self.assertRaisesRegex(ValueError, "cannot announce"):
            perform_announce_action(state, 0, "King")


if __name__ == "__main__":
    unittest.main()
