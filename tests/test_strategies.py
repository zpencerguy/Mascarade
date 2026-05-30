import unittest

from mascarade_sim.agents import STRATEGIES, create_agent
from mascarade_sim.simulation import run_strategy_lineup


class StrategyTests(unittest.TestCase):
    def test_expected_strategies_are_registered(self):
        self.assertIn("always_swap", STRATEGIES)
        self.assertIn("early_bluffer", STRATEGIES)
        self.assertIn("challenge_heavy", STRATEGIES)
        self.assertIn("peek_then_claim", STRATEGIES)

    def test_unknown_strategy_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "Unknown strategy"):
            create_agent("not_a_bot")

    def test_strategy_experiment_returns_strategy_win_credit(self):
        result = run_strategy_lineup(["early_bluffer", "random", "random", "random"], games=5, seed=1)

        self.assertEqual(result["games"], 5)
        self.assertEqual(result["strategies_by_seat"][0], "early_bluffer")
        self.assertIn("strategy_win_credit", result)
        self.assertIn("strategy_win_rate_per_seat", result)

    def test_strategy_experiment_can_rotate_seats(self):
        result = run_strategy_lineup(
            ["early_bluffer", "random", "random", "random"],
            games=5,
            seed=1,
            rotate_seats=True,
        )

        self.assertTrue(result["seat_rotation"])


if __name__ == "__main__":
    unittest.main()
