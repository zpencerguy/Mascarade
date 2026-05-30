import unittest

from mascarade_sim.engine import resolve_character_power, setup_game


def fixed_state(cards: list[str]):
    return setup_game(len(cards), characters=cards, seed=1)


class CharacterPowerTests(unittest.TestCase):
    def test_king_gives_three_from_bank(self):
        state = fixed_state(["Judge", "Bishop", "King", "Queen", "Witch", "Cheat"])

        resolve_character_power(state, 2, "King")

        self.assertEqual(state.player(2).coins, 9)
        self.assertEqual(state.bank_coins, 191)

    def test_queen_gives_two_from_bank(self):
        state = fixed_state(["Judge", "Bishop", "King", "Queen", "Witch", "Cheat"])

        resolve_character_power(state, 3, "Queen")

        self.assertEqual(state.player(3).coins, 8)
        self.assertEqual(state.bank_coins, 192)

    def test_bishop_takes_two_from_richest_other_player(self):
        state = fixed_state(["Judge", "Bishop", "King", "Queen", "Witch", "Cheat"])
        state.player(4).coins = 10

        resolve_character_power(state, 1, "Bishop", {"target_player_id": 4})

        self.assertEqual(state.player(1).coins, 8)
        self.assertEqual(state.player(4).coins, 8)

    def test_widow_raises_player_to_ten(self):
        state = fixed_state(["Judge", "Bishop", "King", "Queen", "Widow", "Cheat"])
        state.player(4).coins = 3

        resolve_character_power(state, 4, "Widow")

        self.assertEqual(state.player(4).coins, 10)

    def test_cheat_wins_at_ten_or_more(self):
        state = fixed_state(["Judge", "Bishop", "King", "Queen", "Witch", "Cheat"])
        state.player(5).coins = 10

        resolve_character_power(state, 5, "Cheat")

        self.assertEqual(state.winner_ids, [5])
        self.assertEqual(state.terminal_reason, "cheat")

    def test_peasant_solo_gets_one(self):
        state = fixed_state(["Judge", "Bishop", "King", "Queen", "Witch", "Cheat", "Thief", "Peasant"])

        resolve_character_power(state, 7, "Peasant", {"revealed_peasant_player_ids": [7]})

        self.assertEqual(state.player(7).coins, 7)

    def test_two_revealed_peasants_get_two_each(self):
        state = fixed_state(["Judge", "Bishop", "King", "Queen", "Witch", "Cheat", "Thief", "Peasant", "Peasant"])

        resolve_character_power(state, 7, "Peasant", {"revealed_peasant_player_ids": [7, 8]})

        self.assertEqual(state.player(7).coins, 8)
        self.assertEqual(state.player(8).coins, 8)

    def test_inquisitor_correct_guess_has_no_effect(self):
        state = fixed_state(["Judge", "Bishop", "King", "Queen", "Witch", "Cheat", "Thief", "Peasant", "Peasant", "Inquisitor"])
        state.card_by_position["player:2"] = "King"

        resolve_character_power(state, 9, "Inquisitor", {"target_player_id": 2, "guessed_character": "King"})

        self.assertEqual(state.player(2).coins, 6)
        self.assertEqual(state.player(9).coins, 6)

    def test_inquisitor_wrong_guess_transfers_four(self):
        state = fixed_state(["Judge", "Bishop", "King", "Queen", "Witch", "Cheat", "Thief", "Peasant", "Peasant", "Inquisitor"])
        state.card_by_position["player:2"] = "King"

        resolve_character_power(state, 9, "Inquisitor", {"target_player_id": 2, "guessed_character": "Queen"})

        self.assertEqual(state.player(2).coins, 2)
        self.assertEqual(state.player(9).coins, 10)

    def test_thief_takes_from_left_and_right(self):
        state = fixed_state(["Judge", "Bishop", "King", "Queen", "Witch", "Cheat", "Thief"])

        resolve_character_power(state, 6, "Thief")

        self.assertEqual(state.player(6).coins, 8)
        self.assertEqual(state.player(5).coins, 5)
        self.assertEqual(state.player(0).coins, 5)


if __name__ == "__main__":
    unittest.main()
