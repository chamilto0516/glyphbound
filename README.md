# Glyphbound

A terminal-based roguelike adventure game built with Python and [Textual](https://github.com/Textualize/textual).

Explore procedurally generated dungeons, battle monsters, collect runic glyphs that grant magical abilities, and descend as deep as you dare.

## Requirements

- Python 3.9+
- A terminal that supports modern ANSI/Unicode output (iTerm2, Windows Terminal, etc.)

## Setup

```bash
# Clone the repo
git clone https://github.com/chamilto0516/glyphbound.git
cd glyphbound

# Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Running the Game

```bash
source .venv/bin/activate
python main.py
```

Press `q` or `Escape` to quit.

## Controls

| Key | Action |
|-----|--------|
| `w` / `a` / `s` / `d` | Move up / left / down / right |
| `q` / `Escape` | Quit |

Walk onto `>` to descend to the next floor. Walk onto `<` to return to the floor above.

## Project Status

Early development. The game generates a multi-room dungeon, lets you explore it, and supports descending and ascending between floors. Each floor has a randomly chosen theme. See [CLAUDE.md](CLAUDE.md) for the full feature roadmap.

## License

MIT
