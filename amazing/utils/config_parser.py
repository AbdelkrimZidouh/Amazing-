import sys
from collections import deque
from typing import Any, List


class ConfigError(Exception):
    """Custom exception for configuration file errors."""
    pass


class ConfigLoader:
    """Read, validate, and normalize project configuration values."""
    pattern_42: List[List[int]] = [
        [1, 0, 0, 0, 1, 1, 1],
        [1, 0, 0, 0, 0, 0, 1],
        [1, 1, 1, 0, 1, 1, 1],
        [0, 0, 1, 0, 1, 0, 0],
        [0, 0, 1, 0, 1, 1, 1],
    ]

    REQUIRED_KEYS: list[str] = ["WIDTH", "HEIGHT", "ENTRY", "EXIT",
                                "OUTPUT_FILE", "PERFECT"]
    OPTIONAL_KEYS: list[str] = ["SEED"]
    ALLOWED_KEYS: list[str] = REQUIRED_KEYS + OPTIONAL_KEYS

    @classmethod
    def _pattern_cells_for_size(cls, width: int,
                                height: int) -> set[tuple[int, int]]:
        """Return absolute coordinates occupied by the centered 42 pattern."""
        pattern_height = len(cls.pattern_42)
        pattern_width = len(cls.pattern_42[0])
        start_x = (width - pattern_width) // 2
        start_y = (height - pattern_height) // 2

        blocked: set[tuple[int, int]] = set()
        for row_idx, row in enumerate(cls.pattern_42):
            for col_idx, bit in enumerate(row):
                if bit != 1:
                    continue
                blocked.add((start_x + col_idx, start_y + row_idx))
        return blocked

    @staticmethod
    def _coords_connected(entry: tuple[int, int], exit_: tuple[int, int],
                          width: int, height: int,
                          blocked: set[tuple[int, int]]) -> bool:
        """Check if ENTRY and EXIT can connect via 4-neighbor open cells."""
        if entry in blocked or exit_ in blocked:
            return False

        pending: deque[tuple[int, int]] = deque([entry])
        visited: set[tuple[int, int]] = {entry}

        while pending:
            x, y = pending.popleft()
            if (x, y) == exit_:
                return True

            for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
                if not (0 <= nx < width and 0 <= ny < height):
                    continue
                if (nx, ny) in blocked or (nx, ny) in visited:
                    continue
                visited.add((nx, ny))
                pending.append((nx, ny))

        return False

    def __init__(self, file_path: str) -> None:
        """Store the path of the configuration file to be parsed."""
        self.file_path: str = file_path

    @staticmethod
    def _collect_pairs(raw_lines: list[str]) -> dict[str, str]:
        """Build a dictionary from KEY=VALUE lines.

        Empty lines and comment lines are ignored.
        """
        parsed_pairs: dict[str, str] = {}

        for raw_line in raw_lines:
            if raw_line == "=":
                raise ConfigError("Invalid line format (expected KEY=VALUE): ")

            stripped_line = raw_line.strip()
            if not stripped_line or stripped_line.startswith("#"):
                continue

            try:
                key_part, value_part = stripped_line.split("=", 1)
                normalized_key = key_part.strip().upper()
                normalized_value = value_part.strip()

                if not normalized_key:
                    raise ConfigError("Invalid line format (missing key): "
                                      f"{stripped_line}")
                if not normalized_value:
                    raise ConfigError(f"Missing value for key: "
                                      f"{normalized_key}")

                if normalized_key in parsed_pairs:
                    raise ConfigError(
                        f"Duplicated key found: {normalized_key}"
                    )
                parsed_pairs[normalized_key] = normalized_value
            except ValueError:
                raise ConfigError(f"Invalid line format (expected KEY=VALUE): "
                                  f"{stripped_line}")

        missing = [key for key in ConfigLoader.REQUIRED_KEYS
                   if key not in parsed_pairs]
        if missing:
            raise ConfigError(f"Missing required keys: {', '.join(missing)}")

        unexpected = [key for key in parsed_pairs
                      if key not in ConfigLoader.ALLOWED_KEYS]
        if unexpected:
            raise ConfigError(
                "Unexpected keys found: "
                f"{', '.join(unexpected)}. "
                "Allowed keys are: "
                f"{', '.join(ConfigLoader.ALLOWED_KEYS)}"
            )

        return parsed_pairs

    @staticmethod
    def _parse_coordinates(raw_value: str, key_name: str, max_width: int,
                           max_height: int) -> tuple[int, int]:
        """Parse and validate coordinates in x,y format."""
        try:
            x_raw, y_raw = raw_value.split(",", 1)
            coord_x = int(x_raw.strip())
            coord_y = int(y_raw.strip())
        except ValueError as err:
            raise ConfigError(f"Invalid {key_name} format (expected x,y): "
                              f"{err}")

        if (coord_x < 0 or coord_y < 0 or coord_x >= max_width or
                coord_y >= max_height):
            raise ConfigError(
                f"{key_name} ({coord_x},{coord_y}) is out of bounds "
                f"(0..{max_width - 1}, 0.. {max_height - 1})"
            )

        return coord_x, coord_y

    @staticmethod
    def _validate_and_cast(raw_dict: dict[str, str]) -> dict[str, Any]:
        """Convert string values to proper Python types with full
            validation."""
        config: dict[str, Any] = {}

        try:
            config["WIDTH"] = int(raw_dict["WIDTH"])
            config["HEIGHT"] = int(raw_dict["HEIGHT"])
            if config["WIDTH"] <= 0 or config["HEIGHT"] <= 0:
                raise ConfigError("WIDTH and HEIGHT must be positive integers")
            if (config["HEIGHT"] < 2 and config["WIDTH"] < 2):
                raise ConfigError("cannot generate a valid maze with these "
                                  "dimensions")
            if (config["HEIGHT"] > 500 or config["WIDTH"] > 500):
                raise ConfigError("these dimensions are too big to be shown in"
                                  " the terminal")
        except ValueError as e:
            raise ConfigError(f"Invalid WIDTH or HEIGHT "
                              f"(must be integers): {e}")

        config["ENTRY"] = ConfigLoader._parse_coordinates(
            raw_dict["ENTRY"],
            "ENTRY",
            config["WIDTH"],
            config["HEIGHT"]
        )
        config["EXIT"] = ConfigLoader._parse_coordinates(
            raw_dict["EXIT"],
            "EXIT",
            config["WIDTH"],
            config["HEIGHT"]
        )

        pattern_height = len(ConfigLoader.pattern_42)
        pattern_width = len(ConfigLoader.pattern_42[0])
        if (config["WIDTH"] >= pattern_width and
                config["HEIGHT"] >= pattern_height):
            blocked_cells = ConfigLoader._pattern_cells_for_size(
                config["WIDTH"], config["HEIGHT"]
            )
            if (config["ENTRY"] in blocked_cells or
                    config["EXIT"] in blocked_cells):
                raise ConfigError("ENTRY and EXIT cannot be placed inside the "
                                  "42 pattern walls")

            if not ConfigLoader._coords_connected(
                    config["ENTRY"],
                    config["EXIT"],
                    config["WIDTH"],
                    config["HEIGHT"],
                    blocked_cells):
                raise ConfigError(
                    "ENTRY and EXIT are separated by the 42 pattern for these "
                    "dimensions. Choose coordinates in the same open region "
                    "or increase WIDTH/HEIGHT."
                )

        if config["ENTRY"] == config["EXIT"]:
            raise ConfigError("ENTRY and EXIT must be different cells")

        perfect_str = raw_dict["PERFECT"].strip().upper()
        if perfect_str == "TRUE":
            config["PERFECT"] = True
        elif perfect_str == "FALSE":
            config["PERFECT"] = False
        else:
            raise ConfigError("PERFECT must be True or False")

        config["OUTPUT_FILE"] = raw_dict["OUTPUT_FILE"].strip()
        if not config["OUTPUT_FILE"]:
            raise ConfigError("OUTPUT_FILE cannot be empty")

        if "SEED" in raw_dict:
            try:
                config["SEED"] = int(raw_dict["SEED"])
            except ValueError as e:
                raise ConfigError(f"SEED must be an integer: {e}")
        else:
            config["SEED"] = None

        return config

    def parse(self) -> dict[str, Any]:
        """Parse the configured file and return validated config values."""
        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                lines = f.readlines()
            raw_dict = self._collect_pairs(lines)
            return self._validate_and_cast(raw_dict)

        except ConfigError as e:
            print(f"Config Error: {e}")
            sys.exit(1)
        except FileNotFoundError:
            print(f"Config Error: File not found → {self.file_path}")
            sys.exit(1)
        except PermissionError:
            print(f"Config Error: Permission denied → {self.file_path}")
            sys.exit(1)
        except IsADirectoryError:
            print(f"Config Error: Expected a file, got a directory → "
                  f"{self.file_path}")
            sys.exit(1)
        except UnicodeDecodeError:
            print("Config Error: File must be UTF-8 text")
            sys.exit(1)
        except OSError as e:
            print(f"Config Error: Unable to read file → {e}")
            sys.exit(1)
        except Exception as e:
            print(f"Unexpected error while parsing config: {e}")
            sys.exit(1)

    def parse_config_file(self) -> dict[str, Any]:
        """Backward-compatible wrapper around parse()."""
        return self.parse()


AmazeingConfigParser = ConfigLoader


if __name__ == "__main__":
    if len(sys.argv) > 1:
        parser = ConfigLoader(sys.argv[1])
        config = parser.parse()
        print("Parsed successfully:")
        for k, v in config.items():
            print(f"  {k}: {v}")
    else:
        print("Usage: python3 parser.py <config.txt>")
