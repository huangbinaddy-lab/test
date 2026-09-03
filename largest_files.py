"""Find the largest files below a directory.

The module can be used as a small library or invoked with ``python -m
largest_files``.
"""

from __future__ import annotations

import argparse
import heapq
import os
import sys
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FileInfo:
    """The path and size of a regular file."""

    path: Path
    size: int


def _walk_files(
    directory: Path, on_error: Callable[[OSError], None] | None = None
) -> Iterator[FileInfo]:
    """Yield regular files recursively without following symbolic links."""

    def handle_error(error: OSError) -> None:
        if on_error is not None:
            on_error(error)

    try:
        with os.scandir(directory) as entries:
            for entry in entries:
                try:
                    if entry.is_dir(follow_symlinks=False):
                        yield from _walk_files(Path(entry.path), on_error)
                    elif entry.is_file(follow_symlinks=False):
                        yield FileInfo(Path(entry.path), entry.stat(follow_symlinks=False).st_size)
                except OSError as error:
                    handle_error(error)
    except OSError as error:
        handle_error(error)


def find_largest_files(
    directory: str | os.PathLike[str],
    count: int = 10,
    *,
    on_error: Callable[[OSError], None] | None = None,
) -> list[FileInfo]:
    """Return at most *count* largest files recursively below *directory*.

    Results are ordered by descending size and then by path. Symbolic links are
    ignored. Errors encountered while traversing are reported through
    ``on_error`` when supplied; otherwise inaccessible entries are skipped.
    """

    if count < 0:
        raise ValueError("count must be non-negative")

    root = Path(directory)
    if not root.is_dir():
        raise NotADirectoryError(f"not a directory: {root}")
    if count == 0:
        return []

    # Include the path in the heap key to make equal-sized results deterministic.
    largest = heapq.nlargest(
        count,
        _walk_files(root, on_error),
        key=lambda item: (item.size, str(item.path)),
    )
    return sorted(largest, key=lambda item: (-item.size, str(item.path)))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="List the largest files in a directory tree."
    )
    parser.add_argument("directory", nargs="?", default=".", help="directory to scan")
    parser.add_argument(
        "-n", "--count", type=int, default=10, help="number of files to show (default: 10)"
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command-line interface."""

    args = _parser().parse_args(argv)
    if args.count < 0:
        _parser().error("--count must be non-negative")

    def warn(error: OSError) -> None:
        print(f"warning: {error}", file=sys.stderr)

    try:
        files = find_largest_files(args.directory, args.count, on_error=warn)
    except (NotADirectoryError, PermissionError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    for item in files:
        print(f"{item.size}\t{item.path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
