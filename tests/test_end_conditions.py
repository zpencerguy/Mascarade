import unittest

from mascarade_sim.engine import check_terminal_state, setup_game


class EndConditionTests(unittest.TestCase):
    def test_game_ends_when_player_reaches_thirteen(self):
        state = setup_game(6, seed=1)
        state.player(3).coins = 13

        check_terminal_state(state)

        self.assertEqual(state.winner_ids, [3])
        self.assertEqual(state.terminal_reason, "thirteen_gold")

    def test_game_ends_when_player_reaches_zero_and_richest_wins_with_ties(self):
        state = setup_game(6, seed=1)
        state.player(0).coins = 0
        state.player(2).coins = 9
        state.player(4).coins = 9

        check_terminal_state(state)

        self.assertEqual(state.winner_ids, [2, 4])
        self.assertEqual(state.terminal_reason, "bankruptcy")


if __name__ == "__main__":
    unittest.main()
