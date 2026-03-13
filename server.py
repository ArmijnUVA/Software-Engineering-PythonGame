# Game Server - centrale multiplayer-server.
#
# Start met: python server.py
#
# De server:
#   - Accepteert verbindingen van maximaal 4 spelers
#   - Beheert de gedeelde game-state (server is de baas, niet de clients)
#   - Draait de game-simulatie op een vaste tick-rate (60 fps)
#   - Stuurt de bijgewerkte state terug naar elke client

import socket
import pickle
import sys
import threading
import time

from game_state import GameState
from config import SERVER_PORT, BUFFER_SIZE, MAX_PLAYERS, FPS
from systems.collision import CollisionSystem


class PlayerInputState:
    # Houdt de laatste bekende input van één speler bij.
    # Movement-toetsen worden direct overschreven.
    # Eenmalige acties (springen, aanvallen) blijven bewaard tot de server ze verwerkt.

    def __init__(self):
        self.left = False
        self.right = False
        self.jump = False
        self.dash = False
        self.light_attack = False
        self.heavy_attack = False
        self.special_attack = False

    def update_from_payload(self, payload):
        # Werk de input bij vanuit een ontvangen pakket.
        self.left = bool(payload.get("left", False))
        self.right = bool(payload.get("right", False))
        # Eenmalige acties worden vastgehouden totdat ze verwerkt zijn
        self.jump = self.jump or bool(payload.get("jump", False))
        self.dash = self.dash or bool(payload.get("dash", False))
        self.light_attack = self.light_attack or bool(payload.get("light_attack", False))
        self.heavy_attack = self.heavy_attack or bool(payload.get("heavy_attack", False))
        self.special_attack = self.special_attack or bool(payload.get("special_attack", False))

    def consume_for_tick(self):
        # Geef de huidige input terug en wis de eenmalige acties.
        current = {
            "left": self.left,
            "right": self.right,
            "jump": self.jump,
            "dash": self.dash,
            "light_attack": self.light_attack,
            "heavy_attack": self.heavy_attack,
            "special_attack": self.special_attack,
        }
        # Wis eenmalige acties na gebruik
        self.jump = False
        self.dash = False
        self.light_attack = False
        self.heavy_attack = False
        self.special_attack = False
        return current


class GameServer:
    # Multiplayer game-server.
    # Beheert verbindingen en synchroniseert de game-state.

    def __init__(self, ip="", port=SERVER_PORT):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        self.ip = ip
        self.port = port
        self.game_state = GameState()
        self.player_count = 0
        self.connections = {}        # player_id -> socket
        self.state_lock = threading.Lock()
        self.collision = CollisionSystem()
        self.input_states = {}       # player_id -> PlayerInputState
        self.running = True
        self.tick_interval = 1.0 / FPS

        try:
            self.socket.bind((ip, port))
        except socket.error as e:
            print(f"Kon niet binden aan port {port}: {e}")
            sys.exit(1)

        self.socket.listen(MAX_PLAYERS)
        print(f"Server gestart op port {port}")
        print(f"\n{'='*50}")
        print(f"Deel dit IP-adres met andere spelers:")
        print(f"  {self._get_local_ip()}")
        print(f"{'='*50}\n")

    def _get_local_ip(self):
        # Zoek het lokale IP-adres op via een nep-verbinding.
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "localhost"

    def start(self):
        # Start de server: begin met luisteren naar verbindingen.
        threading.Thread(target=self._game_loop, daemon=True).start()

        while True:
            try:
                conn, addr = self.socket.accept()
                print(f"Nieuwe verbinding van {addr}")

                # Wijs een uniek speler-ID toe
                player_id = self.player_count
                self.player_count += 1
                self.connections[player_id] = conn

                if self.game_state.add_player(player_id):
                    print(f"Speler {player_id} toegevoegd")
                else:
                    print(f"Kon speler {player_id} niet toevoegen (spel vol?)")

                self.input_states[player_id] = PlayerInputState()

                # Stuur het toegewezen ID naar de client
                conn.sendall(pickle.dumps(player_id))

                # Start een aparte thread voor deze client
                threading.Thread(
                    target=self._handle_client,
                    args=(conn, player_id),
                    daemon=True
                ).start()

            except socket.error as e:
                print(f"Socket error: {e}")
                break
            except KeyboardInterrupt:
                print("\nServer gestopt")
                break

        self.shutdown()

    def _handle_client(self, conn, player_id):
        # Verwerk alle berichten van één client in een aparte thread.
        print(f"Thread gestart voor speler {player_id}")

        while True:
            try:
                data = conn.recv(BUFFER_SIZE)

                if not data:
                    print(f"Speler {player_id} heeft verbinding verbroken")
                    break

                message = pickle.loads(data)
                response = self._process_message(player_id, message)
                conn.sendall(pickle.dumps(response))

            except socket.error as e:
                print(f"Socket error voor speler {player_id}: {e}")
                break
            except Exception as e:
                print(f"Fout voor speler {player_id}: {e}")
                break

        # Opruimen bij disconnect
        print(f"Speler {player_id} verwijderd")
        with self.state_lock:
            self.game_state.remove_player(player_id)
            if player_id in self.connections:
                del self.connections[player_id]
            if player_id in self.input_states:
                del self.input_states[player_id]
        conn.close()

    def _process_message(self, player_id, message):
        # Verwerk één bericht van een client en stuur de bijgewerkte state terug.
        msg_type = message.get("type", "")
        data = message.get("data", {})

        with self.state_lock:
            if msg_type == "input":
                # Sla de input op; de game-loop verwerkt het
                payload = data.get("input_state", {})
                input_state = self.input_states.setdefault(player_id, PlayerInputState())
                input_state.update_from_payload(payload)

            elif msg_type == "char_select":
                # Stel character-type in voor deze speler
                char_type = data.get("character_type", "Warrior")
                self.game_state.select_character(player_id, char_type)

            elif msg_type == "ready":
                # Zet ready-status en start game als iedereen klaar is
                ready = data.get("ready", True)
                self.game_state.set_player_ready(player_id, ready)

                if self.game_state.all_players_ready():
                    self.game_state.start_game()
                    print("Game gestart!")

            # Bij elk bericht sturen we de volledige game-state terug
            return {
                "type": "state",
                "game_state": self.game_state.to_dict(),
            }

    def _game_loop(self):
        # Draai de game-simulatie op een vaste 60 fps tick-rate.
        while self.running:
            frame_start = time.perf_counter()

            with self.state_lock:
                if self.game_state.phase == "playing":
                    self._tick_game()

            # Wacht tot het volgende frame
            elapsed = time.perf_counter() - frame_start
            sleep_time = self.tick_interval - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    def _tick_game(self):
        # Voer één game-frame uit op de server.
        # 1. Verwerk input van alle spelers
        for player_id, player in self.game_state.players.items():
            if not player.connected or not player.character:
                continue
            input_state = self.input_states.setdefault(player_id, PlayerInputState())
            player.character.apply_input_state(input_state.consume_for_tick())

        # 2. Update physics voor alle characters
        characters = self.game_state.get_characters()
        for character in characters:
            character.update(self.game_state.platforms)

        # 3. Detecteer treffers
        self.collision.update(characters)

        # 4. Update game-state (winner check etc.)
        self.game_state.update()

    def shutdown(self):
        # Sluit de server netjes af.
        print("Server afsluiten...")
        self.running = False
        for conn in self.connections.values():
            try:
                conn.close()
            except:
                pass
        self.socket.close()
        print("Server afgesloten")


def main():
    print("="*50)
    print("  BRAWL ARENA - Game Server")
    print("="*50)
    print()

    # Optioneel: geef een ander poortnummer mee via de command line
    port = SERVER_PORT
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print(f"Ongeldige port: {sys.argv[1]}")
            sys.exit(1)

    server = GameServer(port=port)
    server.start()


if __name__ == "__main__":
    main()
