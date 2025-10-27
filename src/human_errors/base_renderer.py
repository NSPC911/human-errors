from os import path
from pathlib import Path
from typing import Iterable


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
    from rich.console import Console
    from rich.padding import Padding
    from rich.syntax import Syntax
    from rich.table import Table
    from rich.text import Text

    console = Console()
    if doc_path == "<string>":
        console.print("[red]Cannot point an exception stemming from inline code execution ([bright_blue]python -c[/] was most likely used).")
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
            line_number=frame.f_lineno
        )
        exit(1)

    import linecache
    code_lines = linecache.getlines(str(doc_path))
    code = "".join(code_lines)

    if line_number < 1:
        dump(
            frame.f_code.co_filename,
            f"[bright_blue]line_number[/] must be larger than or equal to 1. ([red]{line_number}[/] < 1)",
            frame.f_lineno
        )
        exit(1)
    elif line_number > len(code_lines):
        dump(
            frame.f_code.co_filename,
            f"[bright_blue]line_number[/] must be larger than the number of lines in the document. ([red]{line_number}[/] > {len(code_lines)})",
            frame.f_lineno
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

    # Use Rich's approach: pass the ENTIRE file to Syntax with line_range
    # This preserves all syntax context (like Rich does in lines 817-831)
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

    console.print(
        rjust * " "
        + f"  [bright_blue]-->[/] [white]{path.realpath(doc_path)}:{line_number}:{column_number if column_number else ''}[/]"
    )

    # Render the syntax object and extract segments

    segments = list(console.render(syntax, console.options))

    # Group segments by line
    current_line_segments = []
    rendered_text_lines = []

    for segment in segments:
        if segment.text == "\n":
            # End of line - convert segments to Text
            line_text = Text()
            for seg in current_line_segments:
                line_text.append(seg.text, style=seg.style)
            rendered_text_lines.append(line_text)
            current_line_segments = []
        else:
            current_line_segments.append(segment)

    # Don't forget the last line if it doesn't end with newline
    if current_line_segments:
        line_text = Text()
        for seg in current_line_segments:
            line_text.append(seg.text, style=seg.style)
        rendered_text_lines.append(line_text)

    # Print each line with custom borders
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
            prefix.append(startswith, style="bright_red")
            prefix.append(str(source_line_num).rjust(rjust), style="bright_red")
            prefix.append(" │ ", style="bright_blue")
            console.print(prefix, rendered_line, sep="")
            # if column
            if column_number:
                prefix = Text()
                prefix.append("│ ", style="bright_red")
                prefix.append(" " * rjust)
                prefix.append(" │ ", style="bright_blue")
                prefix.append(" " * (column_number - 1) + "↑", style="bright_red")
                console.print(prefix)
        else:
            # Context line
            startswith = "│ " if has_past else "  "
            prefix = Text()
            prefix.append(startswith, style="bright_red")
            prefix.append(str(source_line_num).rjust(rjust), style="bright_blue")
            prefix.append(" │ ", style="bright_blue")
            console.print(prefix, rendered_line, sep="")

    console.print(f"[bright_red]╰─{'─' * rjust}─❯[/] {cause}")
    if extra:
        to_print = Table(
            box=box.ROUNDED,
            border_style="bright_blue",
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
