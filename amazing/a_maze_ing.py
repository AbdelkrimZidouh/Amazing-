from utils.config_parser import ConfigLoader
from mazegen.maze_generator import GenerationError, MazeGenerator
from utils.maze_renderer import MazeRenderer
import sys


def run_cli(config_path: str) -> None:
    """Run the interactive maze generation and rendering loop."""
    # 1. Setup
    config_values = ConfigLoader(config_path).parse()
    maze_engine = MazeGenerator(config_values)
    renderer = MazeRenderer()

    def regenerate_and_persist() -> list[tuple[int, int]]:
        """Generate, solve, and persist the current maze output file."""
        maze_engine.generate()
        path = maze_engine.solve()
        maze_engine.write_output(path)
        return path

    def print_small_maze_notice_if_needed() -> None:
        """Inform when the 42 pattern is omitted due to small dimensions."""
        if maze_engine.can_display_42_pattern():
            return
        pattern_width, pattern_height = maze_engine.pattern_dimensions()
        print(
            "42 pattern omitted: "
            "maze is too small "
            f"(minimum {pattern_width}x{pattern_height})."
        )

    # 2. Initial State
    try:
        shortest_path = regenerate_and_persist()
    except GenerationError as err:
        print(f"Generation Error: {err}")
        sys.exit(1)

    print_small_maze_notice_if_needed()

    # 3. Interaction Loop
    while True:
        renderer.render(maze_engine, shortest_path)
        print("\n[G] New Maze | [P] Toggle Path | [4] Toggle 42 | "
              "[C] Color | [Q] Quit")
        try:
            command = input(">> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            print("\nInput interrupted. Exiting interactive mode.")
            break

        if command == 'g':
            try:
                shortest_path = regenerate_and_persist()
            except GenerationError as err:
                print(f"Generation Error: {err}")
                continue
            print_small_maze_notice_if_needed()
        elif command == 'p':
            renderer.show_path = not renderer.show_path
        elif command == '4':
            renderer.show_42 = not renderer.show_42
        elif command == 'c':
            print("Choose wall color:")
            for option in renderer.get_wall_color_menu():
                print(f"  {option}")

            try:
                candidate = input("Enter color number: ")
            except (EOFError, KeyboardInterrupt):
                print("\nColor selection cancelled.")
                continue

            if not renderer.set_wall_color_by_index(candidate):
                print("Invalid color number. Keeping previous color.")
        elif command == 'q':
            break
        else:
            print("Invalid command. Use G, P, 4, C, or Q.")


def a_maze_ing() -> None:
    """Backward-compatible wrapper around run_cli()."""
    run_cli("config.txt")


if __name__ == "__main__":
    try:
        if len(sys.argv) != 2:
            print("Usage: python3 a_maze_ing.py config.txt")
            sys.exit(1)

        config_arg = sys.argv[1]
        run_cli(config_arg)
    except KeyboardInterrupt:
        print("Exiting the maze, GoodBye!!")
        sys.exit(0)
    except Exception as e:
        print("Unexpected Error...:", e)
