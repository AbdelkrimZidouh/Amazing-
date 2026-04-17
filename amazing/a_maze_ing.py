from utils.config_parser import ConfigLoader
from mazegen.maze_generator import MazeGenerator
from utils.maze_renderer import MazeRenderer
import sys


def run_cli(config_path: str = "config.txt") -> None:
    """Run the interactive maze generation and rendering loop."""
    # 1. Setup
    config_values = ConfigLoader(config_path).parse()
    maze_engine = MazeGenerator(config_values)
    renderer = MazeRenderer()

    # 2. Initial State
    maze_engine.generate()
    shortest_path = maze_engine.solve()
    maze_engine.write_output(shortest_path)

    pattern_notice_shown = False

    def maybe_print_small_maze_notice() -> None:
        """Inform the user when 42 overlay is enabled but maze is too small."""
        nonlocal pattern_notice_shown
        if renderer.show_42 and not maze_engine.can_display_42_pattern():
            if not pattern_notice_shown:
                pattern_width, pattern_height = maze_engine.pattern_dimensions()
                print(
                    "42 pattern cannot be displayed: "
                    f"maze is too small (minimum {pattern_width}x{pattern_height})."
                )
                pattern_notice_shown = True
        else:
            pattern_notice_shown = False

    # 3. Interaction Loop
    while True:
        renderer.render(maze_engine, shortest_path)
        maybe_print_small_maze_notice()
        print("\n[G] New Maze | [P] Toggle Path | [4] Toggle 42 | "
              "[C] Color | [Q] Quit")
        try:
            command = input(">> ").strip().lower()
        except EOFError:
            break

        if command == 'g':
            maze_engine.generate()
            shortest_path = maze_engine.solve()
            maze_engine.write_output(shortest_path)
            maybe_print_small_maze_notice()
        elif command == 'p':
            renderer.show_path = not renderer.show_path
        elif command == '4':
            renderer.show_42 = not renderer.show_42
            maybe_print_small_maze_notice()
        elif command == 'c':
            candidate = input("Enter ANSI code (30-37 or 90-97): ")
            if not renderer.set_wall_color(candidate):
                print("Invalid ANSI code. Keeping previous color.")
        elif command == 'q':
            break


def a_maze_ing() -> None:
    """Backward-compatible wrapper around run_cli()."""
    run_cli()


if __name__ == "__main__":
    try:
        config_arg = sys.argv[1] if len(sys.argv) > 1 else "config.txt"
        run_cli(config_arg)
    except KeyboardInterrupt:
        print("Exiting the maze, GoodBye!!")
        sys.exit(0)
    except Exception as e:
        print("Unexpected Error...:", e)
