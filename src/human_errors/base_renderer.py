from os import path
from pathlib import Path
from typing import Callable, Iterable

from human_errors.renderers.default import _render_default
from human_errors.renderers.nu import _render_nu_like
from human_errors.stack_utils import external_caller_frame
from human_errors.utils import console

# Registry mapping renderer_type to renderer functions
_RENDERERS: dict[str, Callable[..., None]] = {
    "default": _render_default,
    "nu-like": _render_nu_like,
}


def dump(
    doc_path: str | Path,
    cause: str,
    line_number: int,
    column_number: int | None = None,
    context: int | None = None,
    extra: Iterable[str] | str | None = None,
) -> None:
    """
    Dump an error message for anything
    Args:
        doc_path (str): the path to the document
        cause (str): the direct cause for something to happen
        line_number (int): the line number where the error happened
    Optional Args:
        column_number (int): the column number of the error
        context (int): the number of lines of context to show
        extra (Iterable/str):
        - str: single message
        - Iterable: line separated message
    """
    import linecache

    from .utils import renderer_type

    # Get the external frame for error reporting
    frame = external_caller_frame()
    if frame is None:
        # Fallback if stack walking fails
        import inspect

        frame = inspect.currentframe()
        if frame and frame.f_back:
            frame = frame.f_back

    if frame is None:
        console.print("[red]Error: Could not determine caller frame.[/]")
        exit(1)

    if doc_path == "<string>":
        console.print(
            "[red]Cannot point an exception stemming from inline code execution ([bright_blue]python -c[/] was most likely used)."
        )
        console.print("")
        console.print(f"[red]Initial error:\n  {cause}[/]")
        exit(1)

    if isinstance(doc_path, str):
        doc_path = path.abspath(path.realpath(doc_path))
    elif isinstance(doc_path, Path):
        doc_path = Path.resolve(doc_path)
    else:
        dump(
            doc_path=frame.f_code.co_filename,
            cause=f"[salmon1]ValueError[/]: [bright_blue]doc_path[/] can only be a {type(str)} or {type(Path)} and not {type(doc_path)}",
            line_number=frame.f_lineno,
        )
        exit(1)

    code_lines = linecache.getlines(str(doc_path))
    code = "".join(code_lines)

    # Detect if error from within package
    is_meta_error = False
    try:
        doc_path_normalized = Path(doc_path).resolve()
        current_file = Path(__file__).resolve()
        human_errors_dir = current_file.parent
        is_meta_error = doc_path_normalized.parent == human_errors_dir
    except Exception:
        # If we can't determine, treat as regular error
        is_meta_error = False

    if line_number < 1:
        assert frame is not None
        dump(
            frame.f_code.co_filename,
            f"[bright_blue]line_number[/] must be larger than or equal to 1. ([red]{line_number}[/] < 1)",
            frame.f_lineno,
        )
        exit(1)
    elif line_number > len(code_lines):
        assert frame is not None
        dump(
            frame.f_code.co_filename,
            f"[bright_blue]line_number[/] must be smaller than the number of lines in the document. ([red]{line_number}[/] > {len(code_lines)})",
            frame.f_lineno,
        )
        exit(1)

    if not code:
        # File doesn't exist or is empty
        console.print("[red]Error: Could not read file.[/]")
        console.print("")
        console.print(f"[red]Initial error:\n\t{cause}[/]")
        exit(1)

    # Calculate line range
    if context is None:
        if renderer_type == "nu-like":  # noqa: SIM108
            context = 1
        else:
            context = 2
    start_line = max(line_number - context, 1)
    doc_lines_count = len(code_lines)
    end_line = min(line_number + context, doc_lines_count)

    # fix extra
    if isinstance(extra, str):
        extra = [extra]

    # Select and invoke renderer
    renderer_type = renderer_type
    renderer = _RENDERERS.get(renderer_type, _render_default)
    renderer(
        doc_path=doc_path,
        cause=cause,
        line_number=line_number,
        column_number=column_number,
        code=code,
        start_line=start_line,
        end_line=end_line,
        is_meta_error=is_meta_error,
        extra=extra,
    )
