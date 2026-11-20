from __future__ import annotations

from pathlib import Path

from deptry.exceptions import InvalidExcludePatternError
from deptry.rust import find_python_files


def get_all_python_files_in(
    directories: tuple[Path, ...],
    exclude: tuple[str, ...],
    extend_exclude: tuple[str, ...],
    using_default_exclude: bool,
    ignore_notebooks: bool = False,
) -> list[Path]:
    try:
        files = find_python_files(directories, exclude, extend_exclude, using_default_exclude, ignore_notebooks)
    except ValueError as error:
        raise InvalidExcludePatternError(str(error)) from error
    return [Path(f) for f in files]
