# 🎮 Brawl Arena - Python Multiplayer Platform Fighter

Een Brawlhalla-geïnspireerde 2D platform fighter voor 2-4 spelers, gebouwd met Python en Pygame.

![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)
![Pygame](https://img.shields.io/badge/Pygame-2.0+-green.svg)
![License](https://img.shields.io/badge/License-MIT-yellow.svg)

## 🎯 Speloverzicht

**Brawl Arena** is een lokale/netwerk multiplayer vechtspel waarin spelers elkaar van het platform proberen te slaan. Hoe meer schade je oploopt, hoe verder je vliegt bij elke hit!

### Features
- **2-4 spelers** via netwerk multiplayer
- **3 unieke character classes** met verschillende stats en abilities
- **Polymorphic attack system** - elk character heeft unieke moves
- **Knockback systeem** - schade verhoogt knockback (zoals Smash Bros)
- **Animated sprites** - ondersteuning voor sprite sheets
- **Special effects** - screen shake, hit particles, trails

## 🚀 Installatie

### Vereisten
- Python 3.8 of hoger
- pip (Python package manager)

### Stappen

1. **Clone de repository**
   ```bash
   git clone https://github.com/[username]/brawl-arena.git
   cd brawl-arena
   ```

2. **Installeer dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Start de server** (op één computer)
   ```bash
   python server.py
   ```

4. **Start de client** (op elke computer)
   ```bash
   python client.py
   ```

## 🎮 Besturing

| Actie | Toets |
|-------|-------|
| Bewegen | `A` / `D` of `←` / `→` |
| Springen | `W` / `SPACE` of `↑` |
| Light Attack | `J` |
| Heavy Attack | `K` |
| Special Attack | `L` |
| Dash | `SHIFT` |

## 🏗️ Projectstructuur

```
brawl_game/
├── README.md              # Dit bestand
├── requirements.txt       # Python dependencies
├── server.py              # Multiplayer server
├── client.py              # Game client (start dit)
├── network.py             # Netwerk communicatie
├── game_state.py          # Gedeelde game state
├── config.py              # Game configuratie
│
├── entities/
│   ├── __init__.py
│   ├── base_character.py  # Abstract base class (polymorphism)
│   ├── warrior.py         # Warrior character
│   ├── mage.py            # Mage character
│   ├── ninja.py           # Ninja character
│   ├── platform.py        # Platform class
│   └── attack.py          # Attack/projectile classes
│
├── systems/
│   ├── __init__.py
│   ├── physics.py         # Physics engine
│   ├── collision.py       # Collision detection
│   ├── animation.py       # Sprite animation system
│   └── effects.py         # Visual effects (particles, shake)
│
├── ui/
│   ├── __init__.py
│   ├── menu.py            # Main menu
│   ├── hud.py             # In-game HUD
│   └── character_select.py # Character selection screen
│
└── assets/
    ├── sprites/           # Character sprite sheets
    ├── icons/             # Skill icons
    └── sounds/            # Sound effects (optional)
```

## 🔧 Configuratie

Edit `config.py` om game settings aan te passen:

```python
# Server settings
SERVER_IP = "192.168.1.100"  # Pas aan naar jouw IP
SERVER_PORT = 5555
MAX_PLAYERS = 4

# Game settings
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
```

## 👥 Multiplayer Setup

### Lokaal Netwerk (LAN)
1. Vind je IP-adres:
   - **Windows**: Open CMD → typ `ipconfig` → kopieer IPv4 Address
   - **Mac/Linux**: Open Terminal → typ `ifconfig` of `ip addr`

2. Pas `SERVER_IP` aan in `config.py`

3. Zorg dat alle computers op hetzelfde WiFi-netwerk zitten

4. Start de server op één computer, clients op de anderen

## 🎨 Custom Sprites Toevoegen

1. Download sprite sheets van [CraftPix](https://craftpix.net/)
2. Plaats PNG bestanden in `assets/sprites/`
3. Pas `SPRITE_CONFIG` aan in `config.py`:

```python
SPRITE_CONFIG = {
    "warrior": {
        "idle": {"file": "warrior_idle.png", "frames": 4, "width": 64, "height": 64},
        "run": {"file": "warrior_run.png", "frames": 6, "width": 64, "height": 64},
        # etc.
    }
}
```

## 🏛️ Architectuur & Design Patterns

### Polymorphism
Alle characters erven van `BaseCharacter`:
```python
class BaseCharacter(ABC):
    @abstractmethod
    def light_attack(self) -> Attack: pass
    
    @abstractmethod
    def heavy_attack(self) -> Attack: pass
```

### Component System
Entities gebruiken composition:
- `PhysicsComponent` - beweging en gravity
- `AnimationComponent` - sprite animaties
- `CombatComponent` - attacks en damage

### Observer Pattern
Events worden gebroadcast voor effects:
```python
event_manager.emit("hit", {"attacker": p1, "target": p2, "damage": 15})
```

## 📝 Werkverdeling

| Teamlid | Verantwoordelijkheid |
|---------|---------------------|
| Persoon 1 | Server, Network, Game State |
| Persoon 2 | Characters, Combat System |
| Persoon 3 | Physics, Collision, Platforms |
| Persoon 4 | UI, Effects, Sprites |

## 📜 License

MIT License - Zie LICENSE bestand

## 🙏 Credits

- Sprite assets: [CraftPix](https://craftpix.net/)
- Geïnspireerd door: Brawlhalla, Super Smash Bros
