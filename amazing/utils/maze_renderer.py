import os
from typing import List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from mazegen.generator import MazeGenerator


class MazeRenderer:
    """Render a bitmask maze in the terminal using ANSI styling."""

    # ANSI style constants
    RESET = "\033[0m"
    BOLD = "\033[1m"
    ENTRY_MARKER = "S "
    EXIT_MARKER = "E "
    PATH_MARKER = ".."
    EMPTY_MARKER = "  "
    PATTERN_MARKER = "::"

    def __init__(self) -> None:
        """Initialize renderer toggles and default color profile."""
        self.wall_color_code = "90"
        self.show_path = False
        self.show_42 = True

    def clear_terminal(self) -> None:
        """Clear the terminal screen in a cross-platform way."""
        os.system('cls' if os.name == 'nt' else 'clear')

    def set_wall_color(self, ansi_code: str) -> bool:
        """Set wall color when an accepted ANSI code is provided."""
        normalized = ansi_code.strip()
        allowed_codes = {str(code) for code in range(30, 38)}
        allowed_codes.update({str(code) for code in range(90, 98)})
        if normalized in allowed_codes:
            self.wall_color_code = normalized
            return True
        return False

    def clear_screen(self) -> None:
        """Backward-compatible wrapper around clear_terminal()."""
        self.clear_terminal()

    def _get_cell_content(self, x: int, y: int, gen_obj: "MazeGenerator",
                          path_set: set[Tuple[int, int]]) -> str:
        """Determines the 2-character string to display inside a cell."""
        if (x, y) == gen_obj.entry:
            return MazeRenderer.ENTRY_MARKER
        elif (x, y) == gen_obj.exit_:
            return MazeRenderer.EXIT_MARKER
        elif self.show_42 and (x, y) in gen_obj.pattern_cells:
            return f"\033[46m{MazeRenderer.PATTERN_MARKER}\033[0m"
        elif self.show_path and (x, y) in path_set:
            return MazeRenderer.PATH_MARKER
        else:
            return MazeRenderer.EMPTY_MARKER

    def render(self, gen_obj: "MazeGenerator",
               path: List[Tuple[int, int]]) -> None:
        """
        Renders the maze using the generator's grid and the solver's path.
        gen_obj: An instance of MazeGenerator
        path: The list of tuples from the BFS solver
        """
        self.clear_terminal()
        w, h = gen_obj.width, gen_obj.height
        path_set: set[Tuple[int, int]] = set(path)

        wall_glyph = f"\033[{self.wall_color_code}m██\033[0m"
        empty_glyph = MazeRenderer.EMPTY_MARKER

        # 1. Top Border
        print(wall_glyph * (w * 2 + 1))

        for y in range(h):
            # 2. Row Line: [West Wall] [Content] [East Wall] ...
            # We assume the far-left border is always a wall
            line = wall_glyph
            for x in range(w):
                # Add Cell Content
                line += self._get_cell_content(x, y, gen_obj, path_set)

                # Add East Wall (Bit flag 2: E)
                if gen_obj.grid[y][x] & 2:
                    line += wall_glyph
                else:
                    line += empty_glyph
            print(line)

            # 3. Floor Line: [West Wall] [South Wall] [Corner] ...
            floor = wall_glyph
            for x in range(w):
                # Add South Wall (Bit flag 4: S)
                if gen_obj.grid[y][x] & 4:
                    floor += wall_glyph
                else:
                    floor += empty_glyph

                # Add Junction Corner (Always solid for visual structure)
                floor += wall_glyph
            print(floor)
