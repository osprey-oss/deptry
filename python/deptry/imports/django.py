from __future__ import annotations

import ast
import keyword
import tokenize
from dataclasses import dataclass
from typing import TYPE_CHECKING

from deptry.exceptions import DjangoSettingsModuleNotFoundError
from deptry.imports.location import Location

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class _SequenceValue:
    is_list: bool
    entries: list[tuple[str, Location]]


def _is_module_name(value: str) -> bool:
    return bool(value) and all(part.isidentifier() and not keyword.iskeyword(part) for part in value.split("."))


def _augment(
    previous: _SequenceValue | None, operator: ast.operator, addition: _SequenceValue | None
) -> _SequenceValue | None:
    if not isinstance(operator, ast.Add) or previous is None or addition is None:
        return None
    if previous.is_list:
        previous.entries.extend(addition.entries)
        return previous
    if not addition.is_list:
        return _SequenceValue(is_list=False, entries=previous.entries + addition.entries)
    return None


def _forget_shadowed_names(statement: ast.stmt, bindings: dict[str, _SequenceValue | None]) -> None:
    if isinstance(statement, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
        bindings[statement.name] = None
    elif isinstance(statement, ast.Import):
        for alias in statement.names:
            bindings[alias.asname or alias.name.partition(".")[0]] = None


class _SettingsReader:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.resolved_root = root.resolve()
        self.active: set[Path] = set()
        self.modules: dict[Path, dict[str, _SequenceValue | None]] = {}

    def collect(self, module: str) -> dict[str, list[Location]]:
        bindings = self._load(module, required=True)
        apps = bindings.get("INSTALLED_APPS")
        imports: dict[str, list[Location]] = {}
        seen: set[tuple[str, Location]] = set()
        if apps is not None:
            for name, location in apps.entries:
                top_level = name.partition(".")[0]
                entry = (top_level, location)
                if entry not in seen:
                    seen.add(entry)
                    imports.setdefault(top_level, []).append(location)
        return imports

    def _module_path(self, module: str) -> Path | None:
        if not _is_module_name(module):
            return None
        base = self.root.joinpath(*module.split("."))
        for candidate in (base / "__init__.py", base.with_suffix(".py")):
            if candidate.is_file() and candidate.resolve().is_relative_to(self.resolved_root):
                return candidate
        return None

    def _load(self, module: str, *, required: bool = False) -> dict[str, _SequenceValue | None]:
        path = self._module_path(module)
        if path is None:
            if required:
                raise DjangoSettingsModuleNotFoundError(module, self.root)
            return {}
        key = path.resolve()
        if key in self.active:
            return {}
        if key in self.modules:
            return self.modules[key]
        try:
            with tokenize.open(path) as stream:
                source = stream.read()
            tree = ast.parse(source, filename=str(path))
        except (OSError, UnicodeError, SyntaxError):
            if required:
                raise
            return {}
        self.active.add(key)
        bindings: dict[str, _SequenceValue | None] = {}
        package = module.split(".")
        if path.name != "__init__.py":
            package.pop()
        lines = source.split("\n")
        try:
            for statement in tree.body:
                self._statement(statement, bindings, package, path, lines)
        finally:
            self.active.remove(key)
        self.modules[key] = bindings
        return bindings

    def _statement(
        self,
        statement: ast.stmt,
        bindings: dict[str, _SequenceValue | None],
        package: list[str],
        path: Path,
        lines: list[str],
    ) -> None:
        if isinstance(statement, ast.ImportFrom):
            self._import(statement, bindings, package)
        elif isinstance(statement, ast.Assign):
            value = self._sequence(statement.value, bindings, path, lines)
            for target in statement.targets:
                if isinstance(target, ast.Name):
                    bindings[target.id] = value
        elif isinstance(statement, ast.AnnAssign):
            if isinstance(statement.target, ast.Name) and statement.value is not None:
                bindings[statement.target.id] = self._sequence(statement.value, bindings, path, lines)
        elif isinstance(statement, ast.AugAssign):
            if isinstance(statement.target, ast.Name):
                addition = self._sequence(statement.value, bindings, path, lines)
                name = statement.target.id
                bindings[name] = _augment(bindings.get(name), statement.op, addition)
        else:
            _forget_shadowed_names(statement, bindings)

    def _import(
        self,
        statement: ast.ImportFrom,
        bindings: dict[str, _SequenceValue | None],
        package: list[str],
    ) -> None:
        if statement.level:
            if statement.level > len(package):
                imported: dict[str, _SequenceValue | None] = {}
            else:
                prefix = package[: len(package) - statement.level + 1]
                suffix = statement.module.split(".") if statement.module else []
                imported = self._load(".".join(prefix + suffix))
        else:
            imported = self._load(statement.module or "")
        for alias in statement.names:
            if alias.name != "*":
                bindings[alias.asname or alias.name] = imported.get(alias.name)

    def _sequence(
        self,
        expression: ast.expr,
        bindings: dict[str, _SequenceValue | None],
        path: Path,
        lines: list[str],
    ) -> _SequenceValue | None:
        if isinstance(expression, ast.Name):
            return bindings.get(expression.id)
        if isinstance(expression, (ast.List, ast.Tuple)):
            entries = []
            for element in expression.elts:
                if not isinstance(element, ast.Constant) or not isinstance(element.value, str):
                    continue
                if not _is_module_name(element.value):
                    continue
                prefix = lines[element.lineno - 1].encode("utf-8")[: element.col_offset]
                location = Location(path, element.lineno, len(prefix.decode("utf-8")) + 1)
                entries.append((element.value, location))
            return _SequenceValue(is_list=isinstance(expression, ast.List), entries=entries)
        if isinstance(expression, ast.BinOp) and isinstance(expression.op, ast.Add):
            left = self._sequence(expression.left, bindings, path, lines)
            right = self._sequence(expression.right, bindings, path, lines)
            if left is not None and right is not None and left.is_list is right.is_list:
                return _SequenceValue(is_list=left.is_list, entries=left.entries + right.entries)
        return None


def get_imported_modules_from_django(module: str, root: Path) -> dict[str, list[Location]]:
    """
    Statically read `INSTALLED_APPS` from a Django settings module, without importing or executing it.

    Args:
        module: Dotted name of the settings module, resolved beneath `root`.
        root: Directory containing the project configuration. Settings files outside of it are never read.

    Returns:
        The top-level module name of each app listed in `INSTALLED_APPS`, mapped to the locations of the strings that
        reference it. Strings inherited from other local settings modules keep their original location.
    """
    return _SettingsReader(root).collect(module)
