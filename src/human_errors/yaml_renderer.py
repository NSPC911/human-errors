from pathlib import Path
from typing import Iterable

from .base_renderer import dump

try:
    import yaml

    YAMLError = yaml.YAMLError  # type: ignore[misc]
except ModuleNotFoundError:
    dump(
        __file__,
        "[bright_blue]pyyaml[/] is necessary for [light_sky_blue3]yaml_dump[/] to work.",
        line_number=7,
        extra="If you are using a module that provides proper exceptions for YAML, please [u][link=https://github.com/NSPC911/human-errors/issues/new]open an issue[/][/], and I will take a look at it.",
    )
    exit(1)


def yaml_dump(
    exception: YAMLError,  # pyright: ignore
    doc_path: str | Path,
    context: int = 2,
    extra: Iterable | str | None = None,
    exit_now: bool = False,
) -> None:
    """
    Dump an error message for yaml related errors

    Args:
        exception (YAMLError): the exception itself
        doc_path (str/Path): the path to the document
        context (int): the context of the document to provide
        extra (Iterable/str): extra messages/context to provide
        - Iterable (list/tuple/etc): line separated
        - str: single row
        exit_now (bool): to exit or not
        - False: don't exit
        - True: exit with code 1
    """
    print(exception.__dict__)
    for key, item in exception.__dict__.items():
        print()
        if hasattr(item, "__dict__"):
            print(key, item.__dict__)
        else:
            print(key, item)
    cause = str(exception)

    if hasattr(exception, "context_mark") and exception.context_mark:
        dump(
            doc_path,
            cause=exception.context,
            line_number=exception.context_mark.line + 1,
            column_number=exception.context_mark.column + 1,
            context=context,
            extra=extra,
        )
    if hasattr(exception, "problem_mark") and exception.problem_mark:
        dump(
            doc_path,
            cause=exception.problem,
            line_number=exception.problem_mark.line,
            column_number=exception.problem_mark.column,
            context=context,
            extra=extra,
        )

    cause = ""
    if hasattr(exception, "context") and exception.context:
        cause += str(exception.context)
    if hasattr(exception, "problem") and exception.problem:
        if len(cause) == 0:
            cause = str(exception.problem)
        else:
            cause += ", " + str(exception.problem)

    if exit_now:
        exit(1)
