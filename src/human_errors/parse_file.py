import argparse
import json
from pathlib import Path
from typing import Callable

from human_errors import dump, json_dump, toml_dump, utils

try:
    import orjson  # type: ignore[import-not-found]

    HAS_ORJSON = True
except ImportError:
    HAS_ORJSON = False

try:
    import toml  # type: ignore[import-not-found]

    HAS_TOML = True
except ImportError:
    HAS_TOML = False

try:
    import yaml  # type: ignore

    from human_errors import yaml_dump

    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def _parse_json(doc_path: Path) -> None:
    """Parse JSON file; on failure, render via human_errors.json_dump.

    Args:
        doc_path: Path to the JSON document
    """
    try:
        if HAS_ORJSON:
            _ = orjson.loads(doc_path.read_bytes())
        else:
            _ = json.loads(doc_path.read_text(encoding="utf-8"))
    except Exception as exc:
        if (HAS_ORJSON and isinstance(exc, orjson.JSONDecodeError)) or isinstance(
            exc, json.JSONDecodeError
        ):
            json_dump(exc, doc_path, exit_now=True)
        else:
            raise


def _parse_toml(doc_path: Path) -> None:
    """Parse TOML file; on failure, render via human_errors.toml_dump.

    Args:
        doc_path: Path to the TOML document
    """
    text = doc_path.read_text(encoding="utf-8")
    try:
        if HAS_TOML:
            _ = toml.loads(text)
        else:
            import tomllib

            _ = tomllib.loads(text)
    except Exception as exc:
        toml_dump(exc, doc_path, exit_now=True)


def _parse_yaml(doc_path: Path) -> None:
    """Parse YAML file; on failure, render via human_errors.yaml_dump.

    Args:
        doc_path: Path to the YAML document
    """
    if not HAS_YAML:
        dump(__file__, "[blue]pyyaml[/] is not installed!", 80, context=2)
        exit(1)

    text = doc_path.read_text(encoding="utf-8")
    try:
        _ = yaml.safe_load(text)
    except yaml.YAMLError as exc:  # type: ignore[attr-defined]
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
        choices=["default", "miette"],
        default=None,
        help="Renderer style for error output (overrides config)",
    )

    args = parser.parse_args()

    if args.renderer is not None:
        utils.renderer_type = args.renderer  # type: ignore[assignment]

    doc_path = Path(args.path)

    if not doc_path.exists():
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

    parse_fn(doc_path)
    print(f"Parsed successfully: {doc_path}")


if __name__ == "__main__":
    main()
