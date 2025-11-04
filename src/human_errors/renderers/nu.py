from os import path
from pathlib import Path
from typing import Iterable

from human_errors.utils import console


def _render_nu_like(
    doc_path: str | Path,
    cause: str,
    line_number: int,
    column_number: int | None,
    code: str,
    start_line: int,
    end_line: int,
    is_meta_error: bool,
    extra: Iterable[str] | str | None,
) -> None:
    """
    Nushell/Pixi-like renderer: compact error format with minimal decoration.

    Args:
        doc_path (str | Path): Path to the document.
        cause (str): Error message.
        line_number (int): Line where error occurred.
        column_number (int | None): Column of error, if applicable.
        code (str): Full source code.
        start_line (int): First line of context to display.
        end_line (int): Last line of context to display.
        is_meta_error (bool): Whether this is an internal package error.
        extra (Iterable[str] | str | None): Additional help text.
    """
    from rich import box
    from rich.padding import Padding
    from rich.syntax import Syntax
    from rich.table import Table
    from rich.text import Text

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

    error_color = "bright_red bold" if is_meta_error else "bright_magenta bold"
    separator_color = "bright_red" if is_meta_error else "white"

    print()

    console.print(
        (rjust + 2) * " "
        + f"[{separator_color}]╭─\\[[/][bright_cyan][b][u]{path.realpath(doc_path)}:{line_number}{':' + str(column_number) if column_number is not None else ''}[/][/][/][{separator_color}]][/]"
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

    for line_idx, source_line_num in enumerate(range(start_line, end_line + 1)):
        if line_idx >= len(rendered_text_lines):
            break

        rendered_line = rendered_text_lines[line_idx]

        if source_line_num == line_number:
            # Error line
            prefix = Text()
            prefix.append(" ")
            prefix.append(str(source_line_num).rjust(rjust), style="dim")
            prefix.append(" │ ", style=separator_color)
            console.print(prefix, rendered_line, sep="")
            # point to message
            pointer = Text()
            pointer.append(" " * (len(str(source_line_num)) + 1))
            pointer.append(" · ", style=separator_color)
            if column_number is None:
                pointer.append("─", style=error_color)
                pointer.append("┬", style=error_color)
                pointer.append("─" * len(rendered_line), style=error_color)
                point_from = 2
            else:
                pointer.append(" " * (column_number - 1))
                pointer.append("┬", style=error_color)
                point_from = column_number
            console.print(pointer)
            # print message
            messenger = Text()
            messenger.append(" " * (len(str(source_line_num)) + 1))
            messenger.append(" · ", style=separator_color)
            messenger.append(" " * (point_from - 1))
            console.print(messenger, end="")
            console.print(f"[{error_color}]╰─❯ {cause}[/]")
        else:
            # Context line
            prefix = Text()
            prefix.append(" ")
            prefix.append(str(source_line_num).rjust(rjust), style="dim")
            prefix.append(" │ ", style=separator_color)
            console.print(prefix, rendered_line, sep="")

    console.print(
        (rjust + 2) * " "
        + f"[{separator_color}]╰────[/]"
    )

    if extra:
        to_print = Table(
            box=box.ROUNDED,
            border_style="yellow" if is_meta_error else "bright_blue",
            show_header=False,
            expand=True,
            show_lines=True,
        )
        to_print.add_column()
        for string in extra:
            to_print.add_row(string)
        console.print(Padding(to_print, (0, 4, 0, 4)))
    print()
