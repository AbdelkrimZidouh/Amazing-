from typing import Any, Dict, List, Optional, Set, Tuple
from collections import deque
import random

NORTH, EAST, SOUTH, WEST = 1, 2, 4, 8

# Backward-compatible direction aliases.
N, E, S, W = NORTH, EAST, SOUTH, WEST


class GenerationError(Exception):
    """Raised when maze generation or export fails."""
    pass


class MazeGenerator:
    """
    Generate and solve bitmask-based 2D mazes.

    Attributes:
        grid (List[List[int]]): The generated maze structure represented as
            a 2D grid of bitmask integers.
        width (int): Width of the maze.
        height (int): Height of the maze.
        entry (Tuple[int, int]): Entry coordinates (x, y).
        exit_ (Tuple[int, int]): Exit coordinates (x, y).

    Example:
        >>> from mazegen import MazeGenerator
        >>> config = {
        ...     "WIDTH": 10, "HEIGHT": 10, "PERFECT": True,
        ...     "ENTRY": (0, 0), "EXIT": (9, 9), "OUTPUT_FILE": "maze.txt",
        ...     "SEED": 42
        ... }
        >>> gen = MazeGenerator(config)
        >>> maze_matrix = gen.generate()
        >>> print(maze_matrix)  # Print the matrix of the maze in HexaDecimal
        >>> solution = gen.solve() # return a list of tuples showing the path
        >>> from entry to exit
        >>> print(solution) # print the solution
        >>> gen.height = 15 # change the height of the maze
    """
    FORTY_TWO_PATTERN: List[List[int]] = [
        [1, 0, 0, 0, 1, 1, 1],
        [1, 0, 0, 0, 0, 0, 1],
        [1, 1, 1, 0, 1, 1, 1],
        [0, 0, 1, 0, 1, 0, 0],
        [0, 0, 1, 0, 1, 1, 1],
    ]

    @classmethod
    def pattern_dimensions(cls) -> Tuple[int, int]:
        """Return the (width, height) required to display the 42 pattern."""
        return len(cls.FORTY_TWO_PATTERN[0]), len(cls.FORTY_TWO_PATTERN)

    def __init__(self, settings: Dict[str, Any]) -> None:
        """
        Instantiate the generator with a configuration dictionary.

        Args:
            settings (dict): Must contain:
                - WIDTH (int): Horizontal size.
                - HEIGHT (int): Vertical size.
                - PERFECT (bool): If True, no loops; if False, adds
                    random paths.
                - ENTRY (tuple): (x, y) start point.
                - EXIT (tuple): (x, y) end point.
                - OUTPUT_FILE (str): Path to save the hex output.
                - SEED (int, optional): Random seed for reproducibility.
        """
        self.width: int = settings["WIDTH"]
        self.height: int = settings["HEIGHT"]
        self.perfect: bool = settings["PERFECT"]
        self.entry: Tuple[int, int] = settings["ENTRY"]
        self.exit_: Tuple[int, int] = settings["EXIT"]
        self.output_file: str = settings["OUTPUT_FILE"]

        # Start with all walls closed
        self.grid: List[List[int]] = [
            [NORTH | EAST | SOUTH | WEST for _ in range(self.width)]
            for _ in range(self.height)
        ]

        seed = settings.get("SEED")
        if seed is not None:
            random.seed(str(seed))

        self.pattern_cells: Set[Tuple[int, int]] = set()

    def _is_inside(self, x: int, y: int) -> bool:
        """Return True when coordinates are inside maze boundaries."""
        return 0 <= x < self.width and 0 <= y < self.height

    def _carve_passage_between(self, x1: int, y1: int,
                               x2: int, y2: int) -> None:
        """Open the shared wall between two neighboring cells."""
        dx, dy = x2 - x1, y2 - y1
        if dx == 1:
            self.grid[y1][x1] &= ~EAST
            self.grid[y2][x2] &= ~WEST
        elif dx == -1:
            self.grid[y1][x1] &= ~WEST
            self.grid[y2][x2] &= ~EAST
        elif dy == 1:
            self.grid[y1][x1] &= ~SOUTH
            self.grid[y2][x2] &= ~NORTH
        elif dy == -1:
            self.grid[y1][x1] &= ~NORTH
            self.grid[y2][x2] &= ~SOUTH
        else:
            raise ValueError("the coordinates are invalid!")

    def _available_neighbors(self, x: int, y: int,
                             locked: List[List[bool]]
                             ) -> List[Tuple[int, int]]:
        """Return in-bounds neighbors that are not locked."""
        candidates = [(x, y - 1), (x + 1, y), (x, y + 1), (x - 1, y)]
        return [
            (nx, ny) for nx, ny in candidates
            if self._is_inside(nx, ny) and not locked[ny][nx]
        ]

    def _is_open_3x3_block(self, x0: int, y0: int) -> bool:
        """Return True when the 3x3 block at (x0, y0) is fully open."""
        if x0 < 0 or y0 < 0 or x0 + 2 >= self.width or y0 + 2 >= self.height:
            return False

        for yy in range(y0, y0 + 3):
            for xx in range(x0, x0 + 3):
                if (xx, yy) in self.pattern_cells:
                    return False

        for yy in range(y0, y0 + 3):
            for xx in range(x0, x0 + 2):
                if self.grid[yy][xx] & EAST:
                    return False

        for yy in range(y0, y0 + 2):
            for xx in range(x0, x0 + 3):
                if self.grid[yy][xx] & SOUTH:
                    return False

        return True

    def _would_create_open_3x3(self, x1: int, y1: int,
                               x2: int, y2: int) -> bool:
        """Return True if carving would create a forbidden 3x3 open area."""
        original_first = self.grid[y1][x1]
        original_second = self.grid[y2][x2]

        self._carve_passage_between(x1, y1, x2, y2)

        min_x = min(x1, x2) - 2
        max_x = max(x1, x2)
        min_y = min(y1, y2) - 2
        max_y = max(y1, y2)

        found_open_3x3 = False
        for y0 in range(min_y, max_y + 1):
            for x0 in range(min_x, max_x + 1):
                if self._is_open_3x3_block(x0, y0):
                    found_open_3x3 = True
                    break
            if found_open_3x3:
                break

        self.grid[y1][x1] = original_first
        self.grid[y2][x2] = original_second
        return found_open_3x3

    def _connect_all_open_cells(self, visited: List[List[bool]],
                                locked: List[List[bool]]) -> None:
        """Ensure all non-locked cells become connected to the entry region."""
        for y in range(self.height):
            for x in range(self.width):
                if locked[y][x] or visited[y][x]:
                    continue

                connectors = [
                    (nx, ny)
                    for (nx, ny) in self._available_neighbors(x, y, locked)
                    if visited[ny][nx]
                ]

                if not connectors:
                    raise GenerationError(
                        "Impossible maze parameters: 42 pattern disconnects "
                        "the maze"
                    )

                cx, cy = random.choice(connectors)
                self._carve_passage_between(x, y, cx, cy)
                self._run_backtracker((x, y), visited, locked)

    def _run_backtracker(
            self, start: Tuple[int, int],
            visited: List[List[bool]], locked: List[List[bool]]) -> None:
        """Iterative recursive-backtracker implementation."""
        stack: List[Tuple[int, int]] = [start]
        visited[start[1]][start[0]] = True

        while stack:
            x, y = stack[-1]
            nbrs = [
                n for n in self._available_neighbors(x, y, locked)
                if not visited[n[1]][n[0]]
            ]
            if not nbrs:
                stack.pop()
                continue
            nx, ny = random.choice(nbrs)
            self._carve_passage_between(x, y, nx, ny)
            visited[ny][nx] = True
            stack.append((nx, ny))

    def _locate_pattern_cells(self) -> List[Tuple[int, int]]:
        """Compute the coordinates occupied by the centered 42 pattern."""
        pat_h = len(MazeGenerator.FORTY_TWO_PATTERN)
        pat_w = len(MazeGenerator.FORTY_TWO_PATTERN[0])
        start_x = (self.width - pat_w) // 2
        start_y = (self.height - pat_h) // 2
        cells: List[Tuple[int, int]] = []
        for ry in range(pat_h):
            for rx in range(pat_w):
                if MazeGenerator.FORTY_TWO_PATTERN[ry][rx] == 1:
                    gx, gy = start_x + rx, start_y + ry
                    if self._is_inside(gx, gy):
                        cells.append((gx, gy))
        return cells

    def can_display_42_pattern(self) -> bool:
        """Return True when maze dimensions are large enough for 42."""
        pattern_width, pattern_height = MazeGenerator.pattern_dimensions()
        return self.width >= pattern_width and self.height >= pattern_height

    def _open_extra_walls(self, loop_count: int) -> None:
        """Add loops when PERFECT=False."""
        possible: List[Tuple[int, int, int, int]] = []
        for y in range(self.height):
            for x in range(self.width):
                if x + 1 < self.width and (self.grid[y][x] & EAST):
                    if ((x, y) not in self.pattern_cells and
                            (x + 1, y) not in self.pattern_cells):
                        possible.append((x, y, x + 1, y))
                if y + 1 < self.height and (self.grid[y][x] & SOUTH):
                    if ((x, y) not in self.pattern_cells and
                            (x, y + 1) not in self.pattern_cells):
                        possible.append((x, y, x, y + 1))
        random.shuffle(possible)

        opened = 0
        for x1, y1, x2, y2 in possible:
            if opened >= loop_count:
                break
            if self._would_create_open_3x3(x1, y1, x2, y2):
                continue

            self._carve_passage_between(x1, y1, x2, y2)
            opened += 1

    def _generate_plain_maze(self) -> List[List[int]]:
        """Generate a plain perfect maze (no 42 pattern) using recursive
            backtracker."""
        visited = [[False] * self.width for _ in range(self.height)]
        locked = [[False] * self.width for _ in range(self.height)]

        self._run_backtracker(self.entry, visited, locked)
        self._connect_all_open_cells(visited, locked)

        if not self.perfect:
            num_loops = (self.width * self.height) // 10
            self._open_extra_walls(num_loops)

        return self.grid

    def generate(self) -> List[List[int]]:
        """Main generation entry point."""

        # Reset the grid so we start with a solid block of walls
        self.grid = [
            [NORTH | EAST | SOUTH | WEST for _ in range(self.width)]
            for _ in range(self.height)
        ]
        self.pattern_cells = set()

        if not self.can_display_42_pattern():
            return self._generate_plain_maze()

        pattern_cells = self._locate_pattern_cells()
        if self.entry in pattern_cells or self.exit_ in pattern_cells:
            raise GenerationError(
                "the entry or the exit sits in the 42 pattern")

        locked = [[False] * self.width for _ in range(self.height)]
        visited = [[False] * self.width for _ in range(self.height)]

        self.pattern_cells = set(pattern_cells)
        for gx, gy in pattern_cells:
            locked[gy][gx] = True
            visited[gy][gx] = True
            self.grid[gy][gx] = NORTH | EAST | SOUTH | WEST

        self._run_backtracker(self.entry, visited, locked)
        self._connect_all_open_cells(visited, locked)
        if not self.perfect:
            num_loops = (self.width * self.height) // 10
            self._open_extra_walls(num_loops)

        return self.grid

    def solve(self) -> List[Tuple[int, int]]:
        """Find the shortest path from the generator's entry to exit
        using BFS."""

        pending: deque[Tuple[int, int]] = deque([self.entry])
        visited: Set[Tuple[int, int]] = {self.entry}
        parent: Dict[Tuple[int, int], Optional[Tuple[int, int]]] = {
            self.entry: None
        }

        directions = {
            NORTH: (0, -1),
            EAST: (1, 0),
            SOUTH: (0, 1),
            WEST: (-1, 0)
        }

        while pending:
            x, y = pending.popleft()
            if (x, y) == self.exit_:
                break

            for wall_flag, (dx, dy) in directions.items():
                nx, ny = x + dx, y + dy
                # 1. Check bounds
                if not (0 <= nx < self.width and 0 <= ny < self.height):
                    continue
                # 2. Check if the wall is open using bitwise AND
                is_open = not (self.grid[y][x] & wall_flag)
                if is_open and (nx, ny) not in visited:
                    visited.add((nx, ny))
                    parent[(nx, ny)] = (x, y)
                    pending.append((nx, ny))

        path: List[Tuple[int, int]] = []
        current: Optional[Tuple[int, int]] = self.exit_
        while current:
            if current not in parent:
                return []  # No path found
            path.append(current)
            current = parent[current]
        return path[::-1]  # Return reversed path

    def write_output(self, solved_path: List[Tuple[int, int]]) -> None:
        """Write the maze in the exact format required by the subject.."""
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                # 1. Hex grid (row by row)
                for y in range(self.height):
                    line = ''.join(format(self.grid[y][x], 'x')
                                   for x in range(self.width))
                    f.write(line + '\n')

                # 2. Empty line separator
                f.write('\n')

                # 3. Entry and Exit
                f.write(f"{self.entry[0]},{self.entry[1]}\n")
                f.write(f"{self.exit_[0]},{self.exit_[1]}\n")

                # 4. Path String Conversion
                directions_out: List[str] = []
                for i in range(len(solved_path) - 1):
                    curr_x, curr_y = solved_path[i]
                    next_x, next_y = solved_path[i + 1]

                    dx = next_x - curr_x
                    dy = next_y - curr_y

                    if dy == -1:
                        directions_out.append("N")
                    elif dx == 1:
                        directions_out.append("E")
                    elif dy == 1:
                        directions_out.append("S")
                    elif dx == -1:
                        directions_out.append("W")
                f.write(''.join(directions_out) + '\n')
        except OSError as err:
            raise GenerationError(f"failed to write output file: {err}")
