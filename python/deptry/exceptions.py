from __future__ import annotations

from typing import TYPE_CHECKING

from click import UsageError

if TYPE_CHECKING:
    from pathlib import Path


class DependencySpecificationNotFoundError(FileNotFoundError):
    def __init__(self, requirements_files: tuple[str, ...]) -> None:
        super().__init__(
            "No file called 'pyproject.toml' with a [tool.poetry.dependencies], [tool.pdm] or [project] section or"
            f" file(s) called '{', '.join(requirements_files)}' found. Exiting."
        )


class PyprojectFileNotFoundError(FileNotFoundError):
    def __init__(self, directory: Path) -> None:
        super().__init__(f"No file `pyproject.toml` found in directory {directory}")


class InvalidPyprojectTOMLOptionsError(UsageError):
    def __init__(self, invalid_options: list[str], pyproject_toml: Path | str = "pyproject.toml") -> None:
        super().__init__(
            f"'[tool.deptry]' section in '{pyproject_toml}' contains invalid configuration options: {invalid_options}."
        )
