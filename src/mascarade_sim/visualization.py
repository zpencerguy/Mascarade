from __future__ import annotations

import html
import json
from pathlib import Path
from random import Random
from typing import Any

from mascarade_sim.agents import RandomBot, create_agent
from mascarade_sim.config import load_ontology
from mascarade_sim.engine import perform_action, setup_game
from mascarade_sim.models import Action, ActionKind, GameState
from mascarade_sim.simulation import _choose_challengers


DEFAULT_VISUALIZATION_PATH = Path("visualizations") / "game.html"


def write_game_visualization(
    output_path: str | Path = DEFAULT_VISUALIZATION_PATH,
    player_count: int = 4,
    seed: int | None = 42,
    strategy_names: list[str] | None = None,
    max_turns: int = 500,
) -> Path:
    trace = record_game_trace(
        player_count=player_count,
        seed=seed,
        strategy_names=strategy_names,
        max_turns=max_turns,
    )
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_visualization_html(trace), encoding="utf-8")
    return path


def record_game_trace(
    player_count: int = 4,
    seed: int | None = 42,
    strategy_names: list[str] | None = None,
    max_turns: int = 500,
) -> dict[str, Any]:
    ontology = load_ontology()
    rng = Random(seed)
    state = setup_game(player_count, seed=seed, ontology=ontology)
    if strategy_names is None:
        strategy_names = ["random"] * player_count
    if len(strategy_names) != player_count:
        raise ValueError("Strategy count must match player count")

    agents = [create_agent(name, rng=Random(rng.randrange(1_000_000_000))) for name in strategy_names]
    frames = [_frame(state, step=0, active_player_id=state.active_player_id, action=None, events=state.history[-1:])]

    while state.winner_ids is None and state.turn_number <= max_turns:
        actor_id = state.active_player_id
        action = agents[actor_id].choose_action(state, ontology)
        if action.kind == ActionKind.ANNOUNCE and action.character is not None:
            action.challengers = _choose_challengers(agents, state, actor_id, action.character)
        result = perform_action(state, action, ontology)
        frames.append(
            _frame(
                state,
                step=len(frames),
                active_player_id=actor_id,
                action=action,
                events=result.events,
            )
        )

    if state.winner_ids is None:
        richest = max(player.coins for player in state.players)
        state.winner_ids = [player.id for player in state.players if player.coins == richest]
        state.terminal_reason = "max_turns"
        frames.append(_frame(state, step=len(frames), active_player_id=state.active_player_id, action=None, events=[]))

    return {
        "seed": seed,
        "playerCount": player_count,
        "strategiesBySeat": {seat: name for seat, name in enumerate(strategy_names)},
        "characters": sorted(set(state.character_set)),
        "frames": frames,
        "winnerIds": state.winner_ids or [],
        "terminalReason": state.terminal_reason,
    }


def render_visualization_html(trace: dict[str, Any]) -> str:
    payload = json.dumps(trace, separators=(",", ":"))
    title = f"Mascarade {trace['playerCount']}-player simulation"
    return HTML_TEMPLATE.replace("__TITLE__", html.escape(title)).replace("__TRACE_JSON__", payload)


def _frame(
    state: GameState,
    step: int,
    active_player_id: int,
    action: Action | None,
    events: list[dict[str, Any]],
) -> dict[str, Any]:
    revealed_players = {
        event["player_id"]: event["character"]
        for event in events
        if event.get("kind") == "reveal"
    }
    return {
        "step": step,
        "turn": state.turn_number,
        "activePlayerId": active_player_id,
        "action": _action_payload(action),
        "events": events,
        "players": [{"id": player.id, "coins": player.coins} for player in state.players],
        "positions": [
            {
                "id": position.id,
                "ownerPlayerId": position.owner_player_id,
                "isMiddle": position.is_middle,
                "card": state.card_by_position[position.id],
                "revealed": position.owner_player_id in revealed_players if position.owner_player_id is not None else False,
            }
            for position in state.positions
        ],
        "bankCoins": state.bank_coins,
        "courthouseCoins": state.courthouse_coins,
        "winnerIds": state.winner_ids or [],
        "terminalReason": state.terminal_reason,
    }


def _action_payload(action: Action | None) -> dict[str, Any] | None:
    if action is None:
        return None
    return {
        "kind": action.kind.value,
        "actorId": action.actor_id,
        "targetPositionId": action.target_position_id,
        "character": action.character,
        "challengers": action.challengers,
        "actuallySwap": action.actually_swap,
        "context": action.context,
    }


HTML_TEMPLATE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>__TITLE__</title>
  <style>
    :root {
      color-scheme: dark;
      --bg: #11110f;
      --panel: #1d1b17;
      --panel-2: #26231d;
      --line: #504839;
      --text: #f3ead8;
      --muted: #b9ab91;
      --gold: #d8a441;
      --red: #ba4a3f;
      --blue: #5e88b6;
      --green: #6f9d71;
    }

    * { box-sizing: border-box; }

    body {
      margin: 0;
      min-height: 100vh;
      background: radial-gradient(circle at 50% 10%, #2a241b 0, var(--bg) 45rem);
      color: var(--text);
      font-family: ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
    }

    .app {
      display: grid;
      grid-template-columns: minmax(38rem, 1fr) 22rem;
      min-height: 100vh;
    }

    .stage {
      position: relative;
      min-height: 44rem;
      padding: 1.5rem;
      overflow: hidden;
    }

    .table {
      position: absolute;
      inset: 5rem 5rem 6rem;
      border: 2px solid #655437;
      border-radius: 50%;
      background:
        radial-gradient(circle, rgba(141, 99, 47, 0.55), rgba(57, 41, 24, 0.9) 62%, rgba(22, 17, 12, 0.95)),
        repeating-radial-gradient(circle, rgba(255,255,255,0.04) 0 2px, transparent 2px 16px);
      box-shadow: inset 0 0 5rem rgba(0,0,0,0.55), 0 2rem 5rem rgba(0,0,0,0.35);
    }

    .center {
      position: absolute;
      left: 50%;
      top: 50%;
      width: 16rem;
      transform: translate(-50%, -50%);
      display: grid;
      gap: 0.75rem;
      text-align: center;
    }

    .bank, .court {
      border: 1px solid var(--line);
      border-radius: 0.5rem;
      background: rgba(23, 21, 18, 0.82);
      padding: 0.8rem;
    }

    .label {
      color: var(--muted);
      font-size: 0.75rem;
      text-transform: uppercase;
      letter-spacing: 0.08em;
    }

    .value {
      color: var(--gold);
      font-size: 1.6rem;
      font-weight: 800;
    }

    .middle-cards {
      display: flex;
      justify-content: center;
      gap: 0.5rem;
      min-height: 5.7rem;
    }

    .player {
      position: absolute;
      width: 13.5rem;
      transform: translate(-50%, -50%);
      border: 1px solid var(--line);
      border-radius: 0.5rem;
      background: rgba(29, 27, 23, 0.95);
      padding: 0.8rem;
      box-shadow: 0 1rem 2rem rgba(0,0,0,0.25);
      transition: border-color 180ms ease, transform 180ms ease;
    }

    .player.active {
      border-color: var(--gold);
      transform: translate(-50%, -50%) scale(1.04);
    }

    .player.winner {
      border-color: var(--green);
      box-shadow: 0 0 0 2px rgba(111,157,113,0.25), 0 1rem 2rem rgba(0,0,0,0.25);
    }

    .player-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 0.75rem;
      margin-bottom: 0.65rem;
    }

    .seat {
      font-weight: 800;
    }

    .strategy {
      color: var(--muted);
      font-size: 0.75rem;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .coins {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 2.5rem;
      height: 2.5rem;
      border-radius: 50%;
      background: #b37b24;
      color: #1a1005;
      font-weight: 900;
      box-shadow: inset 0 -0.25rem 0 rgba(0,0,0,0.22);
    }

    .card {
      height: 5.2rem;
      border-radius: 0.45rem;
      border: 1px solid #6f6049;
      background: linear-gradient(145deg, #312b22, #15130f);
      display: grid;
      place-items: center;
      padding: 0.45rem;
      text-align: center;
      color: var(--muted);
      font-size: 0.85rem;
      font-weight: 750;
      transition: transform 180ms ease, background 180ms ease, color 180ms ease;
    }

    .card.revealed, .show-cards .card {
      background: linear-gradient(145deg, #f0d9a3, #966a2c);
      color: #22170a;
      transform: rotateY(0deg);
    }

    .card.middle {
      width: 4.2rem;
      height: 5.6rem;
      font-size: 0.72rem;
    }

    aside {
      border-left: 1px solid var(--line);
      background: rgba(17, 16, 14, 0.96);
      padding: 1rem;
      display: grid;
      grid-template-rows: auto auto 1fr;
      gap: 1rem;
      min-height: 100vh;
    }

    h1 {
      margin: 0;
      font-size: 1.2rem;
      line-height: 1.2;
    }

    .meta {
      color: var(--muted);
      font-size: 0.85rem;
      line-height: 1.4;
      margin-top: 0.35rem;
    }

    .controls {
      display: grid;
      gap: 0.75rem;
      padding: 0.85rem;
      border: 1px solid var(--line);
      border-radius: 0.5rem;
      background: var(--panel);
    }

    .buttons {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 0.5rem;
    }

    button {
      border: 1px solid var(--line);
      border-radius: 0.45rem;
      background: var(--panel-2);
      color: var(--text);
      min-height: 2.35rem;
      font-weight: 800;
      cursor: pointer;
    }

    button:hover { border-color: var(--gold); }

    input[type="range"] {
      width: 100%;
      accent-color: var(--gold);
    }

    .check {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      color: var(--muted);
      font-size: 0.85rem;
    }

    .event-panel {
      min-height: 0;
      overflow: auto;
      border: 1px solid var(--line);
      border-radius: 0.5rem;
      background: var(--panel);
    }

    .event-header {
      position: sticky;
      top: 0;
      padding: 0.85rem;
      background: var(--panel-2);
      border-bottom: 1px solid var(--line);
    }

    .event-title {
      font-weight: 900;
      margin-bottom: 0.35rem;
    }

    .event-list {
      list-style: none;
      padding: 0.75rem;
      margin: 0;
      display: grid;
      gap: 0.55rem;
    }

    .event-list li {
      color: var(--muted);
      line-height: 1.35;
      padding: 0.55rem;
      border-radius: 0.4rem;
      background: rgba(255,255,255,0.035);
    }

    .winner-banner {
      position: absolute;
      left: 50%;
      bottom: 1.5rem;
      transform: translateX(-50%);
      min-width: 18rem;
      text-align: center;
      border: 1px solid var(--green);
      border-radius: 0.5rem;
      padding: 0.85rem 1rem;
      background: rgba(34, 57, 36, 0.92);
      color: #e7f3df;
      font-weight: 900;
      opacity: 0;
      transition: opacity 180ms ease;
    }

    .winner-banner.visible { opacity: 1; }

    @media (max-width: 920px) {
      .app { grid-template-columns: 1fr; }
      aside { min-height: auto; border-left: 0; border-top: 1px solid var(--line); }
      .stage { min-height: 42rem; }
      .table { inset: 4rem 1rem 6rem; }
      .player { width: 11rem; padding: 0.65rem; }
      .center { width: 12rem; }
    }
  </style>
</head>
<body>
  <div class="app">
    <main class="stage" id="stage">
      <div class="table"></div>
      <section class="center">
        <div class="bank">
          <div class="label">Bank</div>
          <div class="value" id="bank">0</div>
        </div>
        <div class="court">
          <div class="label">Courthouse</div>
          <div class="value" id="courthouse">0</div>
        </div>
        <div class="middle-cards" id="middleCards"></div>
      </section>
      <div id="players"></div>
      <div class="winner-banner" id="winnerBanner"></div>
    </main>
    <aside>
      <header>
        <h1>__TITLE__</h1>
        <div class="meta" id="meta"></div>
      </header>
      <section class="controls">
        <div class="buttons">
          <button id="back" title="Previous frame">Back</button>
          <button id="play" title="Play or pause">Play</button>
          <button id="next" title="Next frame">Next</button>
          <button id="reset" title="Reset">Reset</button>
        </div>
        <label>
          <span class="label">Timeline</span>
          <input id="timeline" type="range" min="0" max="0" value="0">
        </label>
        <label>
          <span class="label">Speed</span>
          <input id="speed" type="range" min="180" max="1600" value="850">
        </label>
        <label class="check">
          <input id="showCards" type="checkbox">
          Show all cards
        </label>
      </section>
      <section class="event-panel">
        <div class="event-header">
          <div class="event-title" id="eventTitle">Setup</div>
          <div class="meta" id="eventMeta"></div>
        </div>
        <ul class="event-list" id="eventList"></ul>
      </section>
    </aside>
  </div>
  <script>
    const TRACE = __TRACE_JSON__;
    const stage = document.getElementById("stage");
    const playersEl = document.getElementById("players");
    const middleCardsEl = document.getElementById("middleCards");
    const bankEl = document.getElementById("bank");
    const courthouseEl = document.getElementById("courthouse");
    const metaEl = document.getElementById("meta");
    const eventTitleEl = document.getElementById("eventTitle");
    const eventMetaEl = document.getElementById("eventMeta");
    const eventListEl = document.getElementById("eventList");
    const timelineEl = document.getElementById("timeline");
    const speedEl = document.getElementById("speed");
    const showCardsEl = document.getElementById("showCards");
    const winnerBannerEl = document.getElementById("winnerBanner");
    const playButton = document.getElementById("play");
    let frameIndex = 0;
    let timer = null;

    timelineEl.max = String(TRACE.frames.length - 1);
    metaEl.textContent = `${TRACE.playerCount} players, seed ${TRACE.seed ?? "none"}, ${TRACE.frames.length} frames`;

    document.getElementById("back").addEventListener("click", () => setFrame(frameIndex - 1));
    document.getElementById("next").addEventListener("click", () => setFrame(frameIndex + 1));
    document.getElementById("reset").addEventListener("click", () => { pause(); setFrame(0); });
    playButton.addEventListener("click", () => timer ? pause() : play());
    timelineEl.addEventListener("input", () => setFrame(Number(timelineEl.value)));
    showCardsEl.addEventListener("change", () => stage.classList.toggle("show-cards", showCardsEl.checked));

    function play() {
      playButton.textContent = "Pause";
      timer = window.setInterval(() => {
        if (frameIndex >= TRACE.frames.length - 1) {
          pause();
          return;
        }
        setFrame(frameIndex + 1);
      }, Number(speedEl.value));
    }

    function pause() {
      if (timer) window.clearInterval(timer);
      timer = null;
      playButton.textContent = "Play";
    }

    function setFrame(index) {
      frameIndex = Math.max(0, Math.min(TRACE.frames.length - 1, index));
      timelineEl.value = String(frameIndex);
      render(TRACE.frames[frameIndex]);
    }

    function render(frame) {
      bankEl.textContent = frame.bankCoins;
      courthouseEl.textContent = frame.courthouseCoins;
      renderPlayers(frame);
      renderMiddleCards(frame);
      renderEvents(frame);
      if (frame.winnerIds.length) {
        winnerBannerEl.textContent = `Winner: seat ${frame.winnerIds.join(", ")} (${frame.terminalReason})`;
        winnerBannerEl.classList.add("visible");
      } else {
        winnerBannerEl.classList.remove("visible");
      }
    }

    function renderPlayers(frame) {
      playersEl.innerHTML = "";
      const radiusX = Math.min(stage.clientWidth, stage.clientHeight) * 0.39;
      const radiusY = Math.min(stage.clientWidth, stage.clientHeight) * 0.32;
      const centerX = stage.clientWidth / 2;
      const centerY = stage.clientHeight / 2;
      frame.players.forEach((player, idx) => {
        const angle = -Math.PI / 2 + idx * (Math.PI * 2 / frame.players.length);
        const card = frame.positions.find(pos => pos.ownerPlayerId === player.id);
        const el = document.createElement("article");
        el.className = "player";
        if (player.id === frame.activePlayerId) el.classList.add("active");
        if (frame.winnerIds.includes(player.id)) el.classList.add("winner");
        el.style.left = `${centerX + Math.cos(angle) * radiusX}px`;
        el.style.top = `${centerY + Math.sin(angle) * radiusY}px`;
        const strategy = TRACE.strategiesBySeat[player.id] || "random";
        el.innerHTML = `
          <div class="player-head">
            <div>
              <div class="seat">Seat ${player.id}</div>
              <div class="strategy">${escapeHtml(strategy)}</div>
            </div>
            <div class="coins">${player.coins}</div>
          </div>
          ${renderCard(card, false)}
        `;
        playersEl.appendChild(el);
      });
    }

    function renderMiddleCards(frame) {
      middleCardsEl.innerHTML = "";
      frame.positions.filter(pos => pos.isMiddle).forEach(pos => {
        const holder = document.createElement("div");
        holder.innerHTML = renderCard(pos, true);
        middleCardsEl.appendChild(holder.firstElementChild);
      });
    }

    function renderCard(position, middle) {
      if (!position) return "";
      const face = position.revealed ? position.card : "Face down";
      return `<div class="card ${position.revealed ? "revealed" : ""} ${middle ? "middle" : ""}" data-card="${escapeHtml(position.card)}">${escapeHtml(face)}</div>`;
    }

    function renderEvents(frame) {
      eventTitleEl.textContent = frame.action ? actionTitle(frame.action) : "Setup";
      eventMetaEl.textContent = `Frame ${frame.step + 1} of ${TRACE.frames.length} - turn ${frame.turn}`;
      eventListEl.innerHTML = "";
      const lines = frame.events.length ? frame.events.map(eventText) : ["Game reached the maximum turn cap."];
      lines.forEach(line => {
        const li = document.createElement("li");
        li.textContent = line;
        eventListEl.appendChild(li);
      });
    }

    function actionTitle(action) {
      if (action.kind === "announce") return `Seat ${action.actorId} announces ${action.character}`;
      if (action.kind === "peek") return `Seat ${action.actorId} peeks`;
      if (action.kind === "forced_swap") return `Seat ${action.actorId} prepares a swap`;
      if (action.kind === "swap") return `Seat ${action.actorId} swaps or bluffs`;
      return `Seat ${action.actorId} acts`;
    }

    function eventText(event) {
      if (event.kind === "setup") return `Setup: ${event.player_count} players are seated.`;
      if (event.kind === "swap") return `Seat ${event.actor_id} ${event.actually_swap ? "swapped with" : "pretended to swap with"} ${event.target_position_id}.`;
      if (event.kind === "peek") return `Seat ${event.actor_id} secretly looked at their card.`;
      if (event.kind === "announce") {
        const challengers = event.challengers.length ? `; challenged by ${event.challengers.join(", ")}` : "; no challenges";
        return `Seat ${event.actor_id} claimed ${event.character}${challengers}.`;
      }
      if (event.kind === "reveal") return `Seat ${event.player_id} revealed ${event.character}.`;
      if (event.kind === "power") return powerText(event);
      if (event.kind === "fine") return `Seat ${event.player_id} paid ${event.amount} coin to the courthouse for falsely claiming ${event.character}.`;
      if (event.kind === "terminal") return `Game ended by ${event.reason}; winner seat(s): ${event.winner_ids.join(", ")}.`;
      return JSON.stringify(event);
    }

    function powerText(event) {
      const actor = event.actor_id;
      if (event.character === "King" || event.character === "Queen" || event.character === "Widow" || event.character === "Peasant") {
        return `Seat ${actor} used ${event.character} and gained ${event.amount} coin(s).`;
      }
      if (event.character === "Judge") return `Seat ${actor} used Judge and collected ${event.amount} courthouse coin(s).`;
      if (event.character === "Bishop") return `Seat ${actor} used Bishop on seat ${event.target_id} for ${event.amount} coin(s).`;
      if (event.character === "Witch") return `Seat ${actor} used Witch and swapped fortune with seat ${event.target_id}.`;
      if (event.character === "Thief") return `Seat ${actor} used Thief and took ${event.amount} coin(s) from neighbors.`;
      if (event.character === "Cheat") return `Seat ${actor} used Cheat${event.won ? " and won" : " but did not win"}.`;
      if (event.character === "Spy") return `Seat ${actor} used Spy${event.swapped ? " and swapped cards" : " and kept cards in place"}.`;
      if (event.character === "Fool") return `Seat ${actor} used Fool, gained ${event.amount}, and ${event.swapped ? "swapped two other cards" : "left two other cards in place"}.`;
      if (event.character === "Inquisitor") return `Seat ${actor} used Inquisitor on seat ${event.target_id}; guess was ${event.correct ? "correct" : "wrong"}.`;
      return `Seat ${actor} used ${event.character}.`;
    }

    function escapeHtml(value) {
      return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;");
    }

    setFrame(0);
  </script>
</body>
</html>
"""
