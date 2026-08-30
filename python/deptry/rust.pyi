from pathlib import Path

from .rust import Location as RustLocation

def get_imports_from_py_files(file_paths: list[str]) -> dict[str, list[RustLocation]]: ...
def get_imports_from_ipynb_files(file_paths: list[str]) -> dict[str, list[RustLocation]]: ...
def find_python_files(
    paths: tuple[Path, ...],
    exclude: tuple[str, ...],
    extend_exclude: tuple[str, ...],
    using_default_exclude: bool,
    ignore_notebooks: bool = False,
) -> list[str]: ...

class Location:
    file: str
    line: int
    column: int
    ignored_rule_codes: list[str]
    def __init__(self, file: str, line: int, column: int, ignored_rule_codes: list[str] = ...) -> None: ...
