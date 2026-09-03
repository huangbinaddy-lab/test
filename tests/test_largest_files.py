from pathlib import Path

import pytest

from largest_files import FileInfo, find_largest_files, main


def make_file(path: Path, size: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"x" * size)


def test_finds_ten_largest_files_recursively(tmp_path: Path) -> None:
    for number in range(1, 13):
        make_file(tmp_path / "nested" / f"file-{number:02}.dat", number)

    results = find_largest_files(tmp_path)

    assert [item.size for item in results] == list(range(12, 2, -1))
    assert all(isinstance(item, FileInfo) for item in results)


def test_count_and_equal_sizes_are_deterministic(tmp_path: Path) -> None:
    make_file(tmp_path / "b.txt", 4)
    make_file(tmp_path / "a.txt", 4)
    make_file(tmp_path / "small.txt", 1)

    results = find_largest_files(tmp_path, count=2)

    assert [item.path.name for item in results] == ["a.txt", "b.txt"]


def test_ignores_symbolic_links(tmp_path: Path) -> None:
    target = tmp_path / "target.bin"
    make_file(target, 10)
    (tmp_path / "link.bin").symlink_to(target)

    assert find_largest_files(tmp_path) == [FileInfo(target, 10)]


def test_rejects_invalid_directory_and_negative_count(tmp_path: Path) -> None:
    with pytest.raises(NotADirectoryError):
        find_largest_files(tmp_path / "missing")
    with pytest.raises(ValueError, match="non-negative"):
        find_largest_files(tmp_path, -1)


def test_cli_prints_size_and_path(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    small = tmp_path / "small.txt"
    large = tmp_path / "large.txt"
    make_file(small, 2)
    make_file(large, 8)

    assert main([str(tmp_path), "--count", "1"]) == 0
    captured = capsys.readouterr()
    assert captured.out == f"8\t{large}\n"
    assert captured.err == ""


def test_cli_reports_non_directory(capsys: pytest.CaptureFixture[str], tmp_path: Path) -> None:
    assert main([str(tmp_path / "missing")]) == 1
    assert "not a directory" in capsys.readouterr().err
