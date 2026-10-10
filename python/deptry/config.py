from __future__ import annotations

import logging
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any

from deptry.exceptions import InvalidPyprojectTOMLOptionsError
from deptry.utils import load_pyproject_toml

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    import click

# Options that can be set for a single member of a workspace. The other ones only make sense for a whole run.
_WORKSPACE_MEMBER_OPTIONS = frozenset({
    "ignore",
    "per_rule_ignores",
    "exclude",
    "extend_exclude",
    "using_default_exclude",
    "ignore_notebooks",
    "known_first_party",
    "package_module_name_map",
    "optional_dependencies_dev_groups",
    "non_dev_dependency_groups",
    "experimental_namespace_package",
})


def _get_invalid_pyproject_toml_keys(ctx: click.Context, deptry_toml_config_keys: set[str]) -> list[str]:
    """Returns the list of options set in `pyproject.toml` that do not exist as CLI parameters."""
    existing_cli_params = {param.name for param in ctx.command.params}

    return sorted(deptry_toml_config_keys.difference(existing_cli_params))


def read_configuration_from_pyproject_toml(ctx: click.Context, _param: click.Parameter, value: Path) -> Path | None:
    """
    Callback that, given a click context, overrides the default values with configuration options set in a
    pyproject.toml file.
    Using a callback ensures that the following order is respected for setting an option:
    1. Default value is set
    2. Value is overrode by the one set from pyproject.toml, if any
    3. Value is overrode by the one set from the command line, if any
    """

    try:
        pyproject_data = load_pyproject_toml(value)
    except FileNotFoundError:
        logging.debug("No pyproject.toml file to read configuration from.")
        return value

    try:
        deptry_toml_config: dict[str, Any] = pyproject_data["tool"]["deptry"]
    except KeyError:
        logging.debug("No configuration for deptry was found in pyproject.toml.")
        return value

    invalid_pyproject_toml_keys = _get_invalid_pyproject_toml_keys(ctx, set(deptry_toml_config))
    if invalid_pyproject_toml_keys:
        raise InvalidPyprojectTOMLOptionsError(invalid_pyproject_toml_keys)

    click_default_map: dict[str, Any] = {}

    if ctx.default_map:
        click_default_map.update(ctx.default_map)

    click_default_map.update(deptry_toml_config)

    ctx.default_map = click_default_map

    return value


def read_workspace_member_configuration(pyproject_toml: Path) -> dict[str, Any]:
    """
    Read the `[tool.deptry]` section of a workspace member as overrides for `Config`. Options are validated and
    converted by the CLI parameters, like the ones read from the `pyproject.toml` deptry is run with. Options that only
    make sense for a whole run are ignored.
    """
    import click

    from deptry.cli import cli

    deptry_toml_config: dict[str, Any] = load_pyproject_toml(pyproject_toml).get("tool", {}).get("deptry", {})

    ctx = click.Context(cli)
    invalid_pyproject_toml_keys = _get_invalid_pyproject_toml_keys(ctx, set(deptry_toml_config))
    if invalid_pyproject_toml_keys:
        raise InvalidPyprojectTOMLOptionsError(invalid_pyproject_toml_keys, pyproject_toml)

    cli_params = {param.name: param for param in cli.params}
    overrides = {key: cli_params[key].type_cast_value(ctx, value) for key, value in deptry_toml_config.items()}

    if overrides.get("pep621_dev_dependency_groups"):
        overrides["optional_dependencies_dev_groups"] = overrides["pep621_dev_dependency_groups"]
    if overrides.get("exclude"):
        overrides["using_default_exclude"] = False

    ignored_options = sorted(set(deptry_toml_config) - _WORKSPACE_MEMBER_OPTIONS - {"pep621_dev_dependency_groups"})
    if ignored_options:
        logging.warning(
            "Options %s in '[tool.deptry]' section of '%s' are ignored, as they can only be set for the whole"
            " workspace.",
            ignored_options,
            pyproject_toml,
        )

    return {key: value for key, value in overrides.items() if key in _WORKSPACE_MEMBER_OPTIONS}


@dataclass(frozen=True)
class Config:
    root: tuple[Path, ...]
    config: Path
    no_ansi: bool
    per_rule_ignores: Mapping[str, tuple[str, ...]]
    ignore: tuple[str, ...]
    exclude: tuple[str, ...]
    extend_exclude: tuple[str, ...]
    using_default_exclude: bool
    ignore_notebooks: bool
    requirements_files: tuple[str, ...]
    using_default_requirements_files: bool
    requirements_files_dev: tuple[str, ...]
    known_first_party: tuple[str, ...]
    json_output: str
    package_module_name_map: Mapping[str, tuple[str, ...]]
    optional_dependencies_dev_groups: tuple[str, ...]
    non_dev_dependency_groups: tuple[str, ...]
    experimental_namespace_package: bool
    enforce_posix_paths: bool
    github_output: bool
    github_warning_errors: tuple[str, ...]

    def with_overrides(self, overrides: dict[str, Any]) -> Config:
        """Return a new Config with the given fields overridden."""
        return replace(self, **overrides)
