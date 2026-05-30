# Mascarade Monte Carlo Simulator, Codex Project Brief

## Goal
Build a Python simulation engine for the Repos edition of **Mascarade** using the physical rulebook as the source of truth. The first milestone is a correct rules engine that can run many automated games. The second milestone is Monte Carlo analysis of different player strategies, memory models, and bluffing/challenge behavior.

## Source of Truth
The user uploaded photos of the full Repos rulebook in ChatGPT. Key extracted rules:

- Game supports 2 to 13 players, but first implementation should focus on the regular **4 to 13 player rules**.
- Each player starts with **6 gold coins**.
- Remaining money is the **bank**.
- The **courthouse** holds fines.
- Game ends immediately when:
  - any player reaches **13 or more gold**, that player wins.
  - any player reaches **0 gold**, the richest player wins.
  - tied victories are possible.
- The **Judge must always be in play**.
- For 4 or 5 players, use 6 character cards and place unused cards face-up in the middle during setup, then face-down after players study them.
- For 6 to 13 players, use as many cards as players unless optional middle cards are added.
- First four turns are forced preparation turns: active player takes their own face-down card and one other face-down card, then secretly swaps or does not swap, without looking.
- From the fifth turn onward, a player chooses exactly one action:
  1. swap their card, or not, with another player or middle card, under the table, without looking.
  2. secretly look at their own card.
  3. announce a character and attempt to use that character power.
- Important restriction: if a player revealed their card during the immediately previous player’s turn, they cannot announce that same revealed character on their next turn. They must swap, or pretend to swap, with another player.

## Announce / Challenge Resolution
When active player announces a character:

1. Other players, in clockwise order starting from active player’s left, may also claim that same character.
2. If nobody else claims it, the active player applies that character power without revealing their card.
3. If one or more others claim it, all claimants reveal their cards.
4. If one claimant really has the announced character, that player immediately uses the character power, even if it is not their turn.
5. All false claimants pay **1 gold coin to the courthouse**.
6. Cards are turned face-down again.
7. Play continues clockwise from the active player.
8. If nobody revealed the announced character, all claimants pay the fine and no power is resolved.

## Characters and Powers
Implement these character cards for the regular 4 to 13 player game.

### Judge
Mandatory in every game. Takes all coins currently on the courthouse board. If players falsely claimed Judge and must pay fines, those fines are paid **after** the Judge power resolves, so they are not collected by the Judge during that same action.

### Bishop
Takes 2 gold coins from the richest other player. If tied, Bishop chooses which richest player to take from.

### King
Receives 3 gold coins from the bank.

### Queen
Receives 2 gold coins from the bank.

### Fool
Receives 1 gold coin from the bank, then swaps or does not swap the cards of two other players, under the table, without looking.

### Thief
Takes 1 gold coin from the player to their left and 1 gold coin from the player to their right.

### Witch
Can swap all of their fortune with that of another player of their choice. False Witch claim fines are paid after the Witch power resolves.

### Spy
Secretly looks at their own card and another player’s card, or a card in the middle of the table, before swapping those two cards or not.

### Peasant x2
Requires at least 8 players and both Peasants must always be played as a pair. A Peasant receives 1 gold from the bank. If both Peasants are revealed during a turn, they both receive 2 gold from the bank.

### Cheat
If they have 10 gold coins or more, the Cheat wins the game.

### Inquisitor
Requires at least 8 players. Inquisitor points at another player. That player announces what they believe their character is, then reveals their card. If wrong, they pay 4 gold to the Inquisitor. If correct, nothing happens.

### Widow
Receives coins from the bank to bring their fortune up to 10 total. If already at 10 or more, receives nothing and loses nothing.

## Suggested Basic Character Configuration
Implement a configurable setup table. From the visible rulebook photo, the basic configuration appears to include these possibilities by player count:

- 4: Judge, Bishop, King, Queen, Cheat, plus extra card for middle setup.
- 5: Judge, Bishop, King, Queen, Witch, Cheat.
- 6+: use player-count-specific basic configuration from the photographed rulebook.

Important: the photo table is hard to read. Do not hard-code uncertain rows without confirming. Instead create a config file where character sets can be edited easily.

Recommended first playable config for development:

```python
DEFAULT_6_PLAYER_CHARACTERS = [
    "Judge", "Bishop", "King", "Queen", "Witch", "Cheat"
]
```

Then extend once the user verifies all player-count configurations.

## Scope Milestones

### Milestone 1, deterministic rules engine
Build a pure Python rules engine with no AI strategy yet.

Required objects:

```python
GameState
Player
CardPosition
Character
Action
ActionResult
```

State should track:

```python
players
seat_order
card_at_position
coins_by_player
bank_coins
courthouse_coins
turn_index
turn_number
revealed_last_turn_by_player
history
winner
```

Design principle: actions should mutate state through explicit methods and return structured events.

Example methods:

```python
setup_game(player_count: int, characters: list[str], seed: int | None) -> GameState
perform_forced_swap(state, actor_id, target_position, actually_swap: bool)
perform_swap_action(state, actor_id, target_position, actually_swap: bool)
perform_peek_action(state, actor_id)
perform_announce_action(state, actor_id, character, challengers)
resolve_character_power(state, actor_id, character, policy_context)
check_terminal_state(state)
```

### Milestone 2, random legal bot
Create a bot that chooses legal actions randomly.

Random choices:

- during first four turns: pick random target and random swap/no-swap.
- after first four turns:
  - random legal action among swap, peek, announce.
  - random announced character from available character set.
  - random challengers based on configured probability.
  - random target selection for powers.

This should allow thousands of games to complete.

### Milestone 3, simulation runner
Create CLI commands:

```bash
python -m mascarade_sim run --players 6 --games 10000 --seed 42
python -m mascarade_sim single --players 6 --seed 1 --verbose
```

Outputs:

- winner distribution by seat
- average turns per game
- average ending gold
- bankruptcy endings vs 13-gold endings
- most used announced character
- challenge success rate
- false claim fine count

### Milestone 4, belief-state agents
Add imperfect-memory agents.

Each agent should maintain a private belief model:

```python
beliefs[player_id][character] = probability
beliefs[middle_position_id][character] = probability
```

Inputs to belief updates:

- initial revealed setup
- observed swap/no-swap action, with uncertainty
- direct peek action
- challenge reveals
- Spy reveals
- Inquisitor reveals
- Fool swaps between others

Parameters:

```python
memory_accuracy
swap_tracking_accuracy
bluff_frequency
challenge_threshold
risk_tolerance
greed_factor
```

### Milestone 5, Monte Carlo experiments
Run experiments comparing agent types:

- RandomBot
- HonestBot
- AggressiveBluffer
- ConservativeChallenger
- MemoryBot
- ChaosBot
- GreedyBot

Initial research questions:

1. How much does memory accuracy affect win rate?
2. Which characters produce the highest expected coin swing?
3. How often is bluffing positive expected value?
4. How often should players challenge claims?
5. Does first-player or seat order matter?
6. How volatile is the Witch?
7. How strong is the Spy for high-memory agents?

## Recommended Project Structure

```text
mascarade-sim/
├── pyproject.toml
├── README.md
├── src/
│   └── mascarade_sim/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── engine.py
│       ├── models.py
│       ├── characters.py
│       ├── agents/
│       │   ├── __init__.py
│       │   ├── base.py
│       │   ├── random_bot.py
│       │   ├── memory_bot.py
│       │   └── strategies.py
│       ├── simulation.py
│       └── analysis.py
├── tests/
│   ├── test_setup.py
│   ├── test_turns.py
│   ├── test_challenges.py
│   ├── test_character_powers.py
│   └── test_end_conditions.py
└── notebooks/
    └── analysis.ipynb
```

## Data Model Sketch

Use dataclasses or Pydantic models. Keep it simple at first.

```python
from dataclasses import dataclass, field
from enum import Enum

class CharacterName(str, Enum):
    JUDGE = "Judge"
    BISHOP = "Bishop"
    KING = "King"
    QUEEN = "Queen"
    FOOL = "Fool"
    THIEF = "Thief"
    WITCH = "Witch"
    SPY = "Spy"
    PEASANT = "Peasant"
    CHEAT = "Cheat"
    INQUISITOR = "Inquisitor"
    WIDOW = "Widow"

@dataclass
class Player:
    id: int
    coins: int = 6
    eliminated: bool = False

@dataclass
class Position:
    id: str
    owner_player_id: int | None
    is_middle: bool = False

@dataclass
class GameState:
    players: list[Player]
    positions: list[Position]
    card_by_position: dict[str, CharacterName]
    courthouse: int = 0
    bank: int = 194
    turn_index: int = 0
    turn_number: int = 1
    history: list[dict] = field(default_factory=list)
    winner_ids: list[int] | None = None
```

## Testing Priorities

Write tests before expanding agents.

High-value tests:

1. King gives +3 from bank.
2. Queen gives +2 from bank.
3. Judge takes courthouse coins before false Judge fines are added.
4. False claimants pay 1 to courthouse.
5. If nobody is the announced character after reveal, all claimants pay and no power resolves.
6. Witch swaps coin totals before false claimant fines.
7. Widow raises player to exactly 10 if below 10.
8. Cheat immediately wins if Cheat has at least 10 coins.
9. Game ends when player reaches 13.
10. Game ends when player reaches 0, richest player wins.
11. Peasant solo reveal gives +1.
12. Both Peasants revealed gives +2 to each Peasant.
13. Inquisitor correct guess has no effect.
14. Inquisitor wrong guess transfers 4 gold to Inquisitor.
15. First four turns only allow forced swap/no-swap.
16. A player cannot announce the same character they revealed during the immediately previous player’s turn.

## Codex Instructions

Start with a clean Python package. Prioritize correctness and testability over UI. Do not build a web app yet.

First task for Codex:

1. Create the project skeleton.
2. Implement `models.py`, `engine.py`, and `characters.py`.
3. Implement deterministic unit tests for all character powers and challenge resolution.
4. Implement `RandomBot` only after the tests pass.
5. Add a CLI only after the engine can complete one random game.

Avoid over-engineering belief models in the first pass. The first working version should be a correct simulator with random decisions.

## Open Questions for User Verification

1. Confirm the exact basic character configuration for each player count from the rulebook table.
2. Confirm whether to support 2-player and 3-player variants in v1 or defer them.
3. Confirm whether bank can run out or should be treated as effectively infinite in simulations.
4. Confirm whether payments are capped by available coins or can drive a player below zero. Rulebook says game ends if a player loses their last coin, so implement payments as moving available coins only and trigger terminal when coins reach 0.
5. Confirm whether optional middle cards should be included for more than 5 players.

