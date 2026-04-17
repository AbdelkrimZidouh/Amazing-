*This project has been created as part of the 42 curriculum by azidouh, abmahama.*

# A-Maze-ing

## Description
**A-Maze-ing** is a Python maze generator and solver with an interactive terminal renderer.

The project focuses on:
- Recursive Backtracker maze generation.
- BFS shortest path solving.
- A reusable generator module (`mazegen`).
- Configuration-driven execution with input validation.

## Instructions

### Installation
Use the Makefile targets:

```bash
make install
```

```bash
make clean
```

### Build Package

```bash
make package
```

This builds `mazegen` distributions (`.whl` and `.tar.gz`) from the project sources.

### Run

```bash
make run
```

Or manually:

```bash
python3 a_maze_ing.py config.txt
```

## Usage

### Configuration File Format
The parser reads a text file with one `KEY=VALUE` per line.

Supported keys:

| Key | Description | Format |
| :--- | :--- | :--- |
| `WIDTH` | Maze width | Positive integer |
| `HEIGHT` | Maze height | Positive integer |
| `ENTRY` | Entry cell coordinates | `x,y` |
| `EXIT` | Exit cell coordinates | `x,y` |
| `OUTPUT_FILE` | Output maze file | Filename |
| `PERFECT` | Perfect maze mode | `true`/`false` |
| `SEED` | Optional random seed | Integer |

Comments (`# ...`) and empty lines are ignored.

Example:

```ini
WIDTH=50
HEIGHT=20
ENTRY=0,0
EXIT=49,19
OUTPUT_FILE=maze_output.txt
PERFECT=true
SEED=42
```

### Runtime Controls
During execution:
- `G`: Generate a new maze
- `P`: Toggle shortest-path display
- `4`: Toggle `42` pattern highlight
- `C`: Choose a wall color from a numbered list
- `Q`: Quit

## Algorithms

### Generation
`MazeGenerator` uses an iterative **Recursive Backtracker**:
- Maintains a stack of cells.
- Carves passages by removing walls between adjacent cells.
- Produces a connected maze.

Why this algorithm:
- It is simple to implement with precise wall control.
- It naturally builds perfect mazes (single path between two cells).
- It is fast enough for interactive maze regeneration.

When `PERFECT=false`, extra walls are removed after generation to create loops.

### Solving
The shortest route from entry to exit is computed by **Breadth-First Search (BFS)**.

## Reusable Module (`mazegen`)

You can import the generator in another Python project:

```python
from mazegen import MazeGenerator

config = {
    "WIDTH": 20,
    "HEIGHT": 20,
    "PERFECT": True,
    "ENTRY": (0, 0),
    "EXIT": (19, 19),
    "OUTPUT_FILE": "maze.txt",
    "SEED": 123,
}

generator = MazeGenerator(config)
grid = generator.generate()
path = generator.solve()
generator.write_output(path)
```

Bitmask values:
- North = 1
- East = 2
- South = 4
- West = 8

## Project Structure
- `a_maze_ing.py`: Program entry point and interaction loop.
- `utils/config_parser.py`: `ConfigLoader` validation and error handling.
- `mazegen/maze_generator.py`: `MazeGenerator` and maze logic.
- `utils/maze_renderer.py`: Terminal rendering (`MazeRenderer`).

## Team & Management

### Roles
- **abmahama**: Generator logic, BFS, bitmask engine.
- **azidouh**: Parser, renderer, CLI integration.

### Planning and Evolution
- Initial estimate: 2 days generation + 1 day UI.
- Additional time was needed for preserving the centered `42` pattern while keeping maze validity.

### Retrospective
- Strong point: Bitmask representation made solving/rendering efficient.
- Possible improvement: Add viewport rendering for very large mazes.

### Tools Used
- Git and GitHub were used to split work, track progress, and review changes.
- Makefile targets and virtual environments were used to keep install, run,
  lint, and packaging steps repeatable.

## Resources
- Wikipedia: Maze generation algorithms.
- Jamis Buck: Articles on maze algorithms.
- RealPython: Python packaging guides.

### AI Usage
AI assistance was used for:
- Discussing parser validation cases.
- Reviewing bitmask manipulation edge cases.
- Improving documentation wording.
