import unittest

from mascarade_sim.engine import perform_announce_action, setup_game


def challenge_state():
    state = setup_game(6, characters=["Judge", "Bishop", "King", "Queen", "Witch", "Cheat"], seed=1)
    state.turn_number = 5
    state.turn_index = 0
    return state


class ChallengeTests(unittest.TestCase):
    def test_judge_takes_courthouse_before_false_judge_fines_are_added(self):
        state = challenge_state()
        state.card_by_position["player:0"] = "Judge"
        state.card_by_position["player:1"] = "Bishop"
        state.courthouse_coins = 5

        perform_announce_action(state, 0, "Judge", challengers=[1])

        self.assertEqual(state.player(0).coins, 11)
        self.assertEqual(state.player(1).coins, 5)
        self.assertEqual(state.courthouse_coins, 1)

    def test_false_claimants_pay_one_to_courthouse(self):
        state = challenge_state()
        state.card_by_position["player:0"] = "King"
        state.card_by_position["player:1"] = "Bishop"

        perform_announce_action(state, 0, "King", challengers=[1])

        self.assertEqual(state.player(1).coins, 5)
        self.assertEqual(state.courthouse_coins, 1)

    def test_no_revealed_announced_character_means_all_claimants_pay_and_no_power(self):
        state = challenge_state()
        state.card_by_position["player:0"] = "Queen"
        state.card_by_position["player:1"] = "Bishop"

        perform_announce_action(state, 0, "King", challengers=[1])

        self.assertEqual(state.player(0).coins, 5)
        self.assertEqual(state.player(1).coins, 5)
        self.assertEqual(state.bank_coins, 194)
        self.assertEqual(state.courthouse_coins, 2)

    def test_witch_swaps_fortune_before_false_fines(self):
        state = challenge_state()
        state.card_by_position["player:0"] = "Witch"
        state.card_by_position["player:1"] = "Bishop"
        state.player(0).coins = 2
        state.player(1).coins = 10
        state.player(2).coins = 8

        perform_announce_action(state, 0, "Witch", challengers=[1], policy_context={"target_player_id": 2})

        self.assertEqual(state.player(0).coins, 8)
        self.assertEqual(state.player(1).coins, 9)
        self.assertEqual(state.player(2).coins, 2)
        self.assertEqual(state.courthouse_coins, 1)


if __name__ == "__main__":
    unittest.main()
