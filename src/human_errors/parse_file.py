"""
Example CLI to parse config files with human-errors rendering.

Usage:
  uv run python examples/parse_file.py path/to/file.[json|toml|yaml|yml] [--renderer default|nu-like]

- Detects format from file extension
- On parse errors, delegates to the corresponding human_errors renderer
- Optional --renderer selects the output style used by human_errors
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Callable

from human_errors import dump, json_dump, toml_dump, utils


def _parse_json(doc_path: Path) -> None:
    """Parse JSON file; on failure, render via human_errors.json_dump.

    Args:
        doc_path: Path to the JSON document
    """
    try:
        try:
            import orjson  # type: ignore[import-not-found]

            _ = orjson.loads(doc_path.read_bytes())
        except ModuleNotFoundError:
            _ = json.loads(doc_path.read_text(encoding="utf-8"))
    except Exception as exc:  # Narrow to the known JSON errors
        try:
            import orjson  # type: ignore[import-not-found]

            if isinstance(exc, (json.JSONDecodeError, orjson.JSONDecodeError)):
                json_dump(exc, doc_path, exit_now=True)
                return
        except ModuleNotFoundError:
            pass
        if isinstance(exc, json.JSONDecodeError):
            json_dump(exc, doc_path, exit_now=True)
            return
        raise


def _parse_toml(doc_path: Path) -> None:
    """Parse TOML file; on failure, render via human_errors.toml_dump.

    Args:
        doc_path: Path to the TOML document
    """
    text = doc_path.read_text(encoding="utf-8")
    try:
        try:
            import toml  # type: ignore[import-not-found]

            _ = toml.loads(text)
        except ModuleNotFoundError:
            import tomllib

            _ = tomllib.loads(text)
    except Exception as exc:
        # toml_dump validates attributes and prints guidance when needed
        toml_dump(exc, doc_path, exit_now=True)


def _parse_yaml(doc_path: Path) -> None:
    """Parse YAML file; on failure, render via human_errors.yaml_dump.

    Args:
        doc_path: Path to the YAML document
    """
    # Import PyYAML lazily; if missing, import human_errors.yaml_renderer
    # which prints a helpful message and exits.
    try:
        import yaml  # type: ignore

        from human_errors import yaml_dump
    except ModuleNotFoundError:
        dump(__file__, "[blue]pyyaml[/] is not installed!", 80, context=2)
        exit(1)

    text = doc_path.read_text(encoding="utf-8")
    try:
        _ = yaml.safe_load(text)
    except yaml.YAMLError as exc:  # type: ignore[attr-defined]
        # Defer to the package's YAML renderer for location-aware output
        yaml_dump(exc, doc_path, exit_now=True)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Parse a file and render human-friendly errors."
    )
    parser.add_argument(
        "path", type=str, help="Path to file (.json, .toml, .yaml, .yml)"
    )
    parser.add_argument(
        "-r",
        "--renderer",
        choices=["default", "nu-like"],
        default=None,
        help="Renderer style for error output (overrides config)",
    )

    args = parser.parse_args()

    if args.renderer is not None:
        utils.renderer_type = args.renderer  # type: ignore[assignment]

    doc_path = Path(args.path)

    if not doc_path.exists():
        # Let human_errors explain unreadable/missing file
        dump(__file__, "File does not exist or is unreadable", line_number=117)
        raise SystemExit(1)

    parsers: dict[str, Callable[[Path], None]] = {
        ".json": _parse_json,
        ".toml": _parse_toml,
        ".yaml": _parse_yaml,
        ".yml": _parse_yaml,
    }

    ext = doc_path.suffix.lower()
    parse_fn = parsers.get(ext)
    if parse_fn is None:
        print(f"Unsupported file extension: {ext}. Try .json, .toml, .yaml, or .yml.")
        raise SystemExit(2)

    # Perform the parse. Renderer handles error exits; success prints a confirmation.
    parse_fn(doc_path)


if __name__ == "__main__":
    main()
