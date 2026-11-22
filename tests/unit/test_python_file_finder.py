from __future__ import annotations

from pathlib import Path

import pytest

from deptry.python_file_finder import get_all_python_files_in
from tests.utils import create_files, run_within_dir


def test_simple(tmp_path: Path) -> None:
    with run_within_dir(tmp_path):
        create_files([
            Path("dir/subdir/file1.py"),
            Path("dir/subdir/file2.py"),
            Path("dir/subdir/file3.py"),
            Path("other_dir/subdir/file1.py"),
            Path("other_dir/subdir/file2.py"),
        ])

        files = get_all_python_files_in(
            (Path(),),
            exclude=(".venv",),
            extend_exclude=("other_dir",),
            using_default_exclude=False,
        )

        assert sorted(files) == [
            Path("dir/subdir/file1.py"),
            Path("dir/subdir/file2.py"),
            Path("dir/subdir/file3.py"),
        ]


def test_only_matches_start(tmp_path: Path) -> None:
    """
    Test that adding 'subdir' as exclude argument does not also exclude dir/subdir.
    """
    with run_within_dir(tmp_path):
        create_files([
            Path("dir/subdir/file1.py"),
            Path("dir/subdir/file2.py"),
            Path("dir/subdir/file3.py"),
            Path("subdir/file1.py"),
            Path("subdir/file2.py"),
        ])

        files = get_all_python_files_in(
            (Path(),), exclude=("foo",), extend_exclude=("subdir",), using_default_exclude=False
        )

        assert sorted(files) == [
            Path("dir/subdir/file1.py"),
            Path("dir/subdir/file2.py"),
            Path("dir/subdir/file3.py"),
        ]


@pytest.mark.parametrize(
    ("ignore_notebooks", "expected"),
    [
        (
            False,
            [Path("dir/subdir/file1.ipynb")],
        ),
        (
            True,
            [],
        ),
    ],
)
def test_matches_ipynb(ignore_notebooks: bool, expected: list[Path], tmp_path: Path) -> None:
    with run_within_dir(tmp_path):
        create_files([Path("dir/subdir/file1.ipynb")])

        files = get_all_python_files_in(
            (Path(),), exclude=(), extend_exclude=(), using_default_exclude=False, ignore_notebooks=ignore_notebooks
        )

        assert sorted(files) == expected


@pytest.mark.parametrize(
    ("exclude", "expected"),
    [
        (
            (".*file1",),
            [
                Path(".cache/file2.py"),
                Path("dir/subdir/file2.py"),
                Path("dir/subdir/file3.py"),
                Path("other_dir/subdir/file2.py"),
            ],
        ),
        (
            (".cache|other.*subdir",),
            [
                Path("dir/subdir/file1.py"),
                Path("dir/subdir/file2.py"),
                Path("dir/subdir/file3.py"),
            ],
        ),
        (
            (".*/subdir/",),
            [
                Path(".cache/file1.py"),
                Path(".cache/file2.py"),
            ],
        ),
    ],
)
def test_regex_argument(exclude: tuple[str], expected: list[Path], tmp_path: Path) -> None:
    with run_within_dir(tmp_path):
        create_files([
            Path(".cache/file1.py"),
            Path(".cache/file2.py"),
            Path("dir/subdir/file1.py"),
            Path("dir/subdir/file2.py"),
            Path("dir/subdir/file3.py"),
            Path("other_dir/subdir/file1.py"),
            Path("other_dir/subdir/file2.py"),
        ])

        files = get_all_python_files_in((Path(),), exclude=exclude, extend_exclude=(), using_default_exclude=False)

        assert sorted(files) == expected


@pytest.mark.parametrize(
    ("exclude", "expected"),
    [
        (
            (".*file1",),
            [
                Path("dir/subdir/file2.py"),
                Path("dir/subdir/file3.py"),
                Path("other_dir/subdir/file2.py"),
            ],
        ),
        (
            (".*file1|.*file2",),
            [
                Path("dir/subdir/file3.py"),
            ],
        ),
        (
            (".*/subdir/",),
            [],
        ),
    ],
)
def test_multiple_source_directories(exclude: tuple[str], expected: list[Path], tmp_path: Path) -> None:
    with run_within_dir(tmp_path):
        create_files([
            Path("dir/subdir/file1.py"),
            Path("dir/subdir/file2.py"),
            Path("dir/subdir/file3.py"),
            Path("other_dir/subdir/file1.py"),
            Path("other_dir/subdir/file2.py"),
            Path("another_dir/subdir/file1.py"),
        ])

        files = get_all_python_files_in(
            (Path("dir"), Path("other_dir")), exclude=exclude, extend_exclude=(), using_default_exclude=False
        )

        assert sorted(files) == expected


def test_duplicates_are_removed(tmp_path: Path) -> None:
    with run_within_dir(tmp_path):
        create_files([Path("dir/subdir/file1.py")])

        files = get_all_python_files_in((Path(), Path()), exclude=(), extend_exclude=(), using_default_exclude=False)

        assert sorted(files) == [Path("dir/subdir/file1.py")]


def test_gitignore_used_in_git_project(tmp_path: Path) -> None:
    """Test that gitignore files are respected when project uses git."""
    git_project_path = tmp_path / "git_project"
    git_project_path.mkdir()

    # Simulate the presence of a gitignore outside the git project, that should not be used.
    with (tmp_path / ".gitignore").open("w") as f:
        f.write("*")

    with run_within_dir(tmp_path / git_project_path):
        # Simulate the fact that the project is a git repository.
        Path(".git").mkdir()

        create_files([
            Path("file1.py"),
            Path("file2.py"),
            Path("file3.py"),
            Path("dir1/file.py"),
            Path("dir2/file2.py"),
            Path("dir3/file3.py"),
            Path("dir3/file4.py"),
        ])

        with Path(".gitignore").open("w") as f:
            f.write("""/file1.py
/dir1/file.py
file2.py""")

        with Path("dir3/.gitignore").open("w") as f:
            f.write("/file3.py")

        files = get_all_python_files_in((Path(),), exclude=(), extend_exclude=(), using_default_exclude=True)

        assert sorted(files) == [
            Path("dir3/file4.py"),
            Path("file3.py"),
        ]


def test_gitignore_ignored_when_not_using_default_exclude(tmp_path: Path) -> None:
    """Test that gitignore files are ignored when project uses git but does not use default exclude."""
    git_project_path = tmp_path / "git_project"
    git_project_path.mkdir()

    # Simulate the presence of a gitignore outside the git project, that should not be used.
    with (tmp_path / ".gitignore").open("w") as f:
        f.write("*")

    with run_within_dir(tmp_path / git_project_path):
        # Simulate the fact that the project is a git repository.
        Path(".git").mkdir()

        create_files([
            Path("file1.py"),
            Path("file2.py"),
            Path("file3.py"),
            Path("dir1/file.py"),
            Path("dir2/file2.py"),
            Path("dir3/file3.py"),
            Path("dir3/file4.py"),
        ])

        with Path(".gitignore").open("w") as f:
            f.write("""/file1.py
/dir1/file.py
file2.py""")

        with Path("dir3/.gitignore").open("w") as f:
            f.write("/file3.py")

        files = get_all_python_files_in(
            (Path(),),
            exclude=("file3.py",),
            extend_exclude=(),
            using_default_exclude=False,
        )

        assert sorted(files) == [
            Path("dir1/file.py"),
            Path("dir2/file2.py"),
            Path("dir3/file3.py"),
            Path("dir3/file4.py"),
            Path("file1.py"),
            Path("file2.py"),
        ]


def test_gitignore_ignored_in_non_git_project(tmp_path: Path) -> None:
    """Test that gitignore files are ignored when project does not use git."""
    with run_within_dir(tmp_path):
        create_files([
            Path("file1.py"),
            Path("file2.py"),
        ])

        # This will be ignored, since project is not a git project.
        with Path(".gitignore").open("w") as f:
            f.write("/file1.py")

        files = get_all_python_files_in((Path(),), exclude=(), extend_exclude=(), using_default_exclude=True)

        assert sorted(files) == [
            Path("file1.py"),
            Path("file2.py"),
        ]


def test_single_python_file(tmp_path: Path) -> None:
    """Test that a single Python file can be passed directly."""
    with run_within_dir(tmp_path):
        create_files([Path("app.py"), Path("other.py")])

        files = get_all_python_files_in((Path("app.py"),), exclude=(), extend_exclude=(), using_default_exclude=False)

        assert files == [Path("app.py")]


def test_single_notebook_file(tmp_path: Path) -> None:
    """Test that a single notebook file can be passed directly."""
    with run_within_dir(tmp_path):
        create_files([Path("notebook.ipynb")])

        # With ignore_notebooks=False, notebook should be included
        files = get_all_python_files_in(
            (Path("notebook.ipynb"),),
            exclude=(),
            extend_exclude=(),
            using_default_exclude=False,
            ignore_notebooks=False,
        )
        assert files == [Path("notebook.ipynb")]

        # With ignore_notebooks=True, notebook should be excluded
        files = get_all_python_files_in(
            (Path("notebook.ipynb"),), exclude=(), extend_exclude=(), using_default_exclude=False, ignore_notebooks=True
        )
        assert files == []


def test_single_non_python_file_excluded(tmp_path: Path) -> None:
    """Test that a non-Python file is excluded when passed directly."""
    with run_within_dir(tmp_path):
        create_files([Path("readme.txt")])

        files = get_all_python_files_in(
            (Path("readme.txt"),), exclude=(), extend_exclude=(), using_default_exclude=False
        )

        assert files == []
