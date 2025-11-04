from pathlib import Path
from types import FrameType


def _is_inside_dir(directory: Path, file_path: Path) -> bool:
    """
    Return True if "file_path" is inside "directory" (or equals it).

    Args:
        directory (Path): The directory to check containment against.
        file_path (Path): The file path to evaluate.

    Returns:
        bool: True if file_path is inside or equal to directory, False otherwise.
    """
    directory = directory.resolve()
    file_path = file_path.resolve()
    return file_path == directory or directory in file_path.parents


def external_caller_frame(
    package_dir: str | Path | None = None,
    start_frame: FrameType | None = None,
) -> FrameType | None:
    """
    Find the first stack frame whose file is outside this package.

    This is useful when public APIs (like an error dumper) can be called
    directly or via internal helpers/wrappers. Instead of guessing a fixed
    number of frames to skip, this walks the stack until it exits the
    package directory and returns that frame.

    Args:
        package_dir (str | Path | None): The package directory to consider
            as "internal". If None, defaults to the directory containing
            this module (i.e., the human_errors package root).
        start_frame (FrameType | None): The frame to begin from. If None,
            begins from the caller of the function that invokes this helper.

    Optional Args:
        None

    Returns:
        FrameType | None: The first frame that is outside the package
        directory. Returns None if no such frame is found.
    """
    import inspect

    try:
        pkg_dir = (
            Path(package_dir).resolve()
            if package_dir is not None
            else Path(__file__).resolve().parent
        )
    except Exception:
        pkg_dir = Path(__file__).resolve().parent

    frame = start_frame or inspect.currentframe()
    if frame is not None:
        frame = frame.f_back

    while frame is not None:
        try:
            frame_path = Path(frame.f_code.co_filename).resolve()
        except Exception:
            return frame

        if not _is_inside_dir(pkg_dir, frame_path):
            return frame

        frame = frame.f_back

    return None


def external_caller_info(
    package_dir: str | Path | None = None,
    start_frame: FrameType | None = None,
) -> tuple[str, int] | None:
    """
    Convenience wrapper that returns (filename, lineno) for the external frame.

    Args:
        package_dir (str | Path | None): See `external_caller_frame`.
        start_frame (FrameType | None): See `external_caller_frame`.

    Optional Args:
        None

    Returns:
        tuple[str, int] | None: (absolute_file, line_number) if found, else None.
    """
    frame = external_caller_frame(package_dir=package_dir, start_frame=start_frame)
    if frame is None:
        return None
    return (frame.f_code.co_filename, frame.f_lineno)
