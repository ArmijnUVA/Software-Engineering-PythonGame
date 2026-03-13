# Game State - beheert de volledige staat van een match.
#
# De GameState houdt bij:
#   - Welke spelers er zijn en welk character ze spelen
#   - In welke fase de game zit (lobby, character_select, playing, game_over)
#   - De platforms op het speelveld

from entities.base_character import BaseCharacter
from entities.warrior import Warrior
from entities.mage import Mage
from entities.ninja import Ninja
from entities.platform import Platform
from config import STAGE_PLATFORMS, SPAWN_POSITIONS, MAX_PLAYERS


# Koppeling van character-naam naar de bijbehorende class
CHARACTER_CLASSES = {
    "Warrior": Warrior,
    "Mage": Mage,
    "Ninja": Ninja,
}


class PlayerData:
    # Slaat alle informatie van één speler op.

    def __init__(self, player_id):
        self.player_id = player_id
        self.character = None        # Character-object (pas aangemaakt na character select)
        self.character_type = "Warrior"
        self.ready = False
        self.wins = 0
        self.connected = True


class GameState:
    # Centrale game-state voor server en client.
    # Kan omgezet worden naar een dictionary voor netwerkverzending.

    def __init__(self):
        self.players = {}           # player_id -> PlayerData
        self.platforms = [Platform.from_tuple(p) for p in STAGE_PLATFORMS]
        self.phase = "lobby"        # "lobby", "character_select", "playing", "game_over"
        self.round_number = 1
        self.winner = None          # Player ID van de winnaar
        self.max_players = MAX_PLAYERS
        self.stocks_per_player = 3
        self.game_timer = 0         # Frames sinds game start

    # -------------------------------------------------------------------------
    # SPELER BEHEER
    # -------------------------------------------------------------------------

    def add_player(self, player_id):
        # Voeg een nieuwe speler toe. Geeft False terug als de game vol is.
        if len(self.players) >= self.max_players:
            return False

        if player_id in self.players:
            self.players[player_id].connected = True
            return True

        self.players[player_id] = PlayerData(player_id)
        return True

    def remove_player(self, player_id):
        # Markeer een speler als verbroken.
        if player_id in self.players:
            self.players[player_id].connected = False

    def select_character(self, player_id, character_type):
        # Stel het character-type in voor een speler.
        if player_id not in self.players:
            return False
        if character_type not in CHARACTER_CLASSES:
            return False
        self.players[player_id].character_type = character_type
        return True

    def set_player_ready(self, player_id, ready=True):
        # Zet de ready-status van een speler.
        if player_id in self.players:
            self.players[player_id].ready = ready

    def all_players_ready(self):
        # True als alle verbonden spelers ready zijn (minimaal 2).
        connected = [p for p in self.players.values() if p.connected]
        return len(connected) >= 2 and all(p.ready for p in connected)

    # -------------------------------------------------------------------------
    # GAME FLOW
    # -------------------------------------------------------------------------

    def start_game(self):
        # Start de game: spawn alle characters op hun startpositie.
        self.phase = "playing"
        self.game_timer = 0
        self.winner = None

        for i, (player_id, player_data) in enumerate(self.players.items()):
            if not player_data.connected:
                continue
            spawn = SPAWN_POSITIONS[i % len(SPAWN_POSITIONS)]
            char_class = CHARACTER_CLASSES.get(player_data.character_type, Warrior)
            player_data.character = char_class(spawn[0], spawn[1], player_id)
            player_data.character.stocks = self.stocks_per_player
            player_data.ready = False

    def update(self):
        # Update de game-state voor één frame. Geeft events terug.
        if self.phase != "playing":
            return []

        events = []
        self.game_timer += 1

        # Controleer of er een winnaar is
        alive = [
            p for p in self.players.values()
            if p.connected and p.character and p.character.stocks > 0
        ]

        if len(alive) <= 1 and len(self.get_connected_players()) >= 2:
            if alive:
                self.winner = alive[0].player_id
            self.phase = "game_over"
            events.append({"type": "game_over", "winner": self.winner})

        return events

    def reset_round(self):
        # Reset alles voor een nieuwe ronde.
        self.round_number += 1
        self.winner = None
        self.game_timer = 0

        for i, player_data in enumerate(self.players.values()):
            if player_data.character:
                spawn = SPAWN_POSITIONS[i % len(SPAWN_POSITIONS)]
                player_data.character.x = spawn[0]
                player_data.character.y = spawn[1]
                player_data.character.vel_x = 0
                player_data.character.vel_y = 0
                player_data.character.damage_percent = 0
                player_data.character.stocks = self.stocks_per_player

    # -------------------------------------------------------------------------
    # HULPFUNCTIES
    # -------------------------------------------------------------------------

    def get_connected_players(self):
        # Geef een lijst van alle verbonden spelers.
        return [p for p in self.players.values() if p.connected]

    def get_characters(self):
        # Geef een lijst van alle actieve character-objecten.
        return [
            p.character for p in self.players.values()
            if p.connected and p.character is not None
        ]

    def get_player(self, player_id):
        # Haal PlayerData op voor een speler-ID, of None als niet gevonden.
        return self.players.get(player_id)

    # -------------------------------------------------------------------------
    # SERIALISATIE (netwerk)
    # -------------------------------------------------------------------------

    def to_dict(self):
        # Zet de volledige game-state om naar een dictionary.
        return {
            "phase": self.phase,
            "round_number": self.round_number,
            "winner": self.winner,
            "game_timer": self.game_timer,
            "players": {
                pid: {
                    "player_id": p.player_id,
                    "character_type": p.character_type,
                    "ready": p.ready,
                    "wins": p.wins,
                    "connected": p.connected,
                    "character_state": p.character.get_state() if p.character else None,
                }
                for pid, p in self.players.items()
            }
        }

    def from_dict(self, data):
        # Herstel de game-state vanuit een dictionary (ontvangen van server).
        self.phase = data["phase"]
        self.round_number = data["round_number"]
        self.winner = data["winner"]
        self.game_timer = data["game_timer"]

        for pid_str, pdata in data["players"].items():
            pid = int(pid_str)

            if pid not in self.players:
                self.players[pid] = PlayerData(pid)

            player = self.players[pid]
            player.character_type = pdata["character_type"]
            player.ready = pdata["ready"]
            player.wins = pdata["wins"]
            player.connected = pdata["connected"]

            if pdata["character_state"]:
                if player.character is None:
                    char_class = CHARACTER_CLASSES.get(player.character_type, Warrior)
                    player.character = char_class(0, 0, pid)
                player.character.set_state(pdata["character_state"])
