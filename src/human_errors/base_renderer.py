from os import path
from pathlib import Path
from typing import Iterable

from rich.console import Console

console = Console()


def dump(
    doc_path: str | Path,
    cause: str,
    line_number: int,
    column_number: int | None = None,
    context: int = 2,
    extra: Iterable | str | None = None,
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
    import inspect

    from rich import box
    from rich.padding import Padding
    from rich.syntax import Syntax
    from rich.table import Table
    from rich.text import Text

    if doc_path == "<string>":
        console.print(
            "[red]Cannot point an exception stemming from inline code execution ([bright_blue]python -c[/] was most likely used)."
        )
        console.print("")
        console.print(f"[red]Initial error:\n  {cause}[/]")
        exit(1)
    frame = inspect.currentframe()
    if frame and frame.f_back:
        frame = frame.f_back
    assert frame
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

    import linecache

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
        dump(
            frame.f_code.co_filename,
            f"[bright_blue]line_number[/] must be larger than or equal to 1. ([red]{line_number}[/] < 1)",
            frame.f_lineno,
        )
        exit(1)
    elif line_number > len(code_lines):
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
    start_line = max(line_number - context, 1)
    doc_lines_count = len(code_lines)
    end_line = min(line_number + context, doc_lines_count)

    has_past: bool = False
    rjust = len(str(end_line))

    # Calculate available width for code
    prefix_width = rjust + 6  # "╭╴NNN │ "
    max_code_width = max(console.width - prefix_width, 40)

    syntax = Syntax(
        code,
        Syntax.guess_lexer(str(doc_path)),
        theme="ansi_dark",
        line_numbers=False,
        line_range=(start_line, end_line),
        highlight_lines={line_number},
        word_wrap=False,
        code_width=max_code_width,
        background_color="default",
    )

    error_color = "bright_magenta" if is_meta_error else "bright_red"
    separator_color = "bright_magenta" if is_meta_error else "bright_blue"
    arrow_color = "bright_magenta" if is_meta_error else "bright_blue"

    console.print(
        rjust * " "
        + f"  [{arrow_color}]-->[/] [white]{path.realpath(doc_path)}:{line_number}{':' + str(column_number) if column_number is not None else ''}[/]"
    )

    segments = list(console.render(syntax, console.options))

    current_line_segments = []
    rendered_text_lines = []

    for segment in segments:
        if segment.text == "\n":
            line_text = Text()
            for seg in current_line_segments:
                line_text.append(seg.text, style=seg.style)
            rendered_text_lines.append(line_text)
            current_line_segments = []
        else:
            current_line_segments.append(segment)

    if current_line_segments:
        line_text = Text()
        for seg in current_line_segments:
            line_text.append(seg.text, style=seg.style)
        rendered_text_lines.append(line_text)

    line_idx = 0
    for line_idx, source_line_num in enumerate(range(start_line, end_line + 1)):
        if line_idx >= len(rendered_text_lines):
            break

        rendered_line = rendered_text_lines[line_idx]
        line_idx += 1

        if source_line_num == line_number:
            # Error line
            startswith = "╭╴"
            has_past = True
            prefix = Text()
            prefix.append(startswith, style=error_color)
            prefix.append(str(source_line_num).rjust(rjust), style=error_color)
            prefix.append(" │ ", style=separator_color)
            console.print(prefix, rendered_line, sep="")
            # if column
            if column_number is not None:
                prefix = Text()
                prefix.append("│ ", style=error_color)
                prefix.append(" " * rjust)
                prefix.append(" │ ", style=separator_color)
                prefix.append(" " * (column_number - 1) + "↑", style=error_color)
                console.print(prefix)
        else:
            # Context line
            startswith = "│ " if has_past else "  "
            prefix = Text()
            prefix.append(startswith, style=error_color)
            prefix.append(str(source_line_num).rjust(rjust), style="bright_blue")
            prefix.append(" │ ", style=separator_color)
            console.print(prefix, rendered_line, sep="")

    console.print(f"[{error_color}]╰─{'─' * rjust}─❯[/] {cause}")
    if extra:
        to_print = Table(
            box=box.ROUNDED,
            border_style="yellow" if is_meta_error else "bright_blue",
            show_header=False,
            expand=True,
            show_lines=True,
        )
        to_print.add_column()
        if isinstance(extra, str):
            extra = [extra]
        for string in extra:
            to_print.add_row(string)
        console.print(Padding(to_print, (0, 4, 0, 4)))
