# Network - client-side netwerkcommunicatie.
#
# Beheert de TCP-socketverbinding met de server.
# Alle data wordt geserialiseerd met pickle.

import socket
import pickle
import threading

from config import SERVER_IP, SERVER_PORT, BUFFER_SIZE, CONNECTION_TIMEOUT


class Network:
    # Verbindt de client met de game-server en verstuurt/ontvangt data.

    def __init__(self, server_ip=None):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.settimeout(CONNECTION_TIMEOUT)

        self.server = server_ip or SERVER_IP
        self.port = SERVER_PORT
        self.addr = (self.server, self.port)

        self.player_id = None
        self.connected = False
        self._lock = threading.Lock()   # Voorkom dat twee threads tegelijk versturen

    def connect(self):
        # Verbind met de server. Geeft True terug als het lukt.
        try:
            self.client.connect(self.addr)
            data = self.client.recv(BUFFER_SIZE)
            self.player_id = pickle.loads(data)
            self.connected = True
            print(f"Verbonden met server als Player {self.player_id}")
            return True

        except socket.timeout:
            print("Verbinding timeout - server niet bereikbaar")
            return False
        except socket.error as e:
            print(f"Verbindingsfout: {e}")
            return False

    def send(self, data):
        # Stuur data naar de server en wacht op een antwoord.
        # Geeft de ontvangen data terug, of None bij een fout.
        if not self.connected:
            return None

        with self._lock:
            try:
                self.client.sendall(pickle.dumps(data))
                response = self.client.recv(BUFFER_SIZE)
                return pickle.loads(response)
            except socket.timeout:
                print("Timeout bij communicatie met server")
                return None
            except socket.error as e:
                print(f"Socket error: {e}")
                self.connected = False
                return None

    def send_no_response(self, data):
        # Stuur data naar de server zonder op een antwoord te wachten.
        if not self.connected:
            return False

        with self._lock:
            try:
                self.client.sendall(pickle.dumps(data))
                return True
            except socket.error as e:
                print(f"Fout bij verzenden: {e}")
                self.connected = False
                return False

    def receive(self):
        # Ontvang data van de server (blokkerend).
        if not self.connected:
            return None

        try:
            data = self.client.recv(BUFFER_SIZE)
            if data:
                return pickle.loads(data)
            return None
        except socket.timeout:
            return None
        except socket.error as e:
            print(f"Fout bij ontvangen: {e}")
            self.connected = False
            return None

    def disconnect(self):
        # Verbreek de verbinding met de server.
        self.connected = False
        try:
            self.client.close()
        except:
            pass
        print("Verbinding met server verbroken")

    def is_connected(self):
        return self.connected

    def get_player_id(self):
        return self.player_id


class NetworkMessage:
    # Helperklasse voor het standaardiseren van netwerknachrichten.

    # Berichttypen
    CONNECT = "connect"
    DISCONNECT = "disconnect"
    PLAYER_INPUT = "input"
    GAME_STATE = "state"
    CHARACTER_SELECT = "char_select"
    READY = "ready"

    def __init__(self, msg_type, data=None, player_id=None):
        self.type = msg_type
        self.data = data
        self.player_id = player_id

    def to_dict(self):
        return {
            "type": self.type,
            "data": self.data,
            "player_id": self.player_id,
        }

    @classmethod
    def from_dict(cls, data):
        return cls(
            msg_type=data["type"],
            data=data.get("data"),
            player_id=data.get("player_id"),
        )
