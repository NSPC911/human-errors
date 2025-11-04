import tomllib
import traceback
from pathlib import Path
from typing import Iterable, Union

from human_errors.base_renderer import dump

try:
    import toml

    TOMLDecodeError = Union[toml.TomlDecodeError, tomllib.TOMLDecodeError]
except ModuleNotFoundError:
    TOMLDecodeError = tomllib.TOMLDecodeError


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
                cause="Update to Python 3.14 for [bright_blue]tomllib[/] or use [bright_blue][link=https://pypi.org/project/toml/]toml[/][/] to display the exception",
                line_number=1,
                column_number=None,
                context=context,
                extra=f"Exception type: {type(exception).__name__}\nException: {str(exception)}",
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
