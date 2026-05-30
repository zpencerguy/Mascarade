import unittest

from mascarade_sim.engine import perform_announce_action, setup_game, summarize_history


class AnalysisTests(unittest.TestCase):
    def test_challenge_success_rate_counts_announcements_with_true_reveal(self):
        state = setup_game(6, characters=["Judge", "Bishop", "King", "Queen", "Witch", "Cheat"], seed=1)
        state.turn_number = 5
        state.card_by_position["player:0"] = "Queen"
        state.card_by_position["player:1"] = "Bishop"
        perform_announce_action(state, 0, "King", challengers=[1])

        summary = summarize_history(state)

        self.assertEqual(summary["challenged_announcements"], 1)
        self.assertEqual(summary["challenge_success_rate"], 0.0)


if __name__ == "__main__":
    unittest.main()
