from __future__ import annotations

from pathlib import Path

from deptry.rust import find_python_files


def get_all_python_files_in(
    paths: tuple[Path, ...],
    exclude: tuple[str, ...],
    extend_exclude: tuple[str, ...],
    using_default_exclude: bool,
    ignore_notebooks: bool = False,
) -> list[Path]:
    """Find all Python files in the given paths.

    Args:
        paths: Tuple of paths to search. Either a single Python file (.py or .ipynb)
               or one or more directories (which are walked recursively).
        exclude: Regex patterns for paths to exclude.
        extend_exclude: Additional regex patterns to exclude.
        using_default_exclude: Whether to use default excludes (respects .gitignore, etc.).
        ignore_notebooks: If True, .ipynb files are excluded.

    Returns:
        List of paths to Python files found.
    """
    return [Path(f) for f in find_python_files(paths, exclude, extend_exclude, using_default_exclude, ignore_notebooks)]
