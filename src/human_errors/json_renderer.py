import json
from pathlib import Path
from typing import Iterable, Union

from .base_renderer import dump

try:
    import orjson
    JSONDecodeError = Union[json.JSONDecodeError, orjson.JSONDecodeError]
except ModuleNotFoundError:
    JSONDecodeError = json.JSONDecodeError


def json_dump(
    exception: JSONDecodeError,  # pyright: ignore
    doc_path: str | Path,
    context: int = 2,
    extra: Iterable | str | None = None,
    exit_now: bool = False
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
    dump(
        doc_path,
        cause=exception.msg,
        line_number=exception.lineno,
        column_number=exception.colno,
        context=context,
        extra=extra
    )
    if exit_now:
        exit(1)
