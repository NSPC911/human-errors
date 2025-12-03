import traceback
from pathlib import Path
from typing import Iterable, Union

from human_errors.base_renderer import dump

_toml_errors: list[type] = []

try:
    import tomllib

    _toml_errors.append(tomllib.TOMLDecodeError)
except ModuleNotFoundError:
    tomllib = None  # ty: ignore[invalid-assignment]

try:
    import tomli

    _toml_errors.append(tomli.TOMLDecodeError)
except ModuleNotFoundError:
    tomli = None  # ty: ignore[invalid-assignment]

try:
    import toml

    _toml_errors.append(toml.TomlDecodeError)
except ModuleNotFoundError:
    toml = None  # ty: ignore[invalid-assignment]

if not _toml_errors:
    raise ImportError(
        "No TOML library available. Install one of: tomli, toml, or use Python 3.11+"
    )

TOMLDecodeError = Union[tuple(_toml_errors)]


def toml_dump(
    exception: TOMLDecodeError,  # pyright: ignore
    doc_path: str | Path,
    context: int = 1,
    extra: Iterable | str | None = None,
    exit_now: bool = False,
) -> None:
    """
    Dump an error message for json related errors

    Args:
        exception (JSONDecodeError): the exception itself
        doc_path (str/Path): the path to the document
        context (int): the context of the document to provide
        extra (Iterable/str): extra messages/context to provide
        - Iterable (list/tuple/etc): line separated
        - str: single row
        exit_now (bool): to exit or not
        - False: don't exit
        - True: exit with code 1
    """
    # check
    if not all(hasattr(exception, attr) for attr in ("msg", "lineno", "colno")):
        # Get the caller's frame info
        import inspect

        frame = inspect.currentframe()
        if frame and frame.f_back:
            frame = frame.f_back
            assert frame
            dump(
                doc_path=doc_path,
                cause=str(exception),
                line_number=1,
                column_number=None,
                context=context,
                extra="Update to Python 3.14 for [bright_blue]tomllib[/], or use [bright_blue][link=https://pypi.org/project/tomli/]tomli[/][/] / [bright_blue][link=https://pypi.org/project/toml/]toml[/][/] to better display the exception",
            )
        else:
            print("Exception missing required attributes (msg, lineno, colno)")
            traceback.print_stack()
        exit(1)
        return
    # look ty, i already pre checked it, i don't care, im still
    # gonna ignore your errors, screw you
    dump(
        doc_path,
        cause=exception.msg,  # ty: ignore[possibly-missing-attribute]
        line_number=exception.lineno,  # ty: ignore[possibly-missing-attribute]
        column_number=exception.colno,  # ty: ignore[possibly-missing-attribute]
        context=context,
        extra=extra,
    )
    if exit_now:
        exit(1)
