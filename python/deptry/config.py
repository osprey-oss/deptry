from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from deptry.exceptions import InvalidPyprojectTOMLOptionsError
from deptry.utils import load_pyproject_toml

if TYPE_CHECKING:
    from pathlib import Path

    import click


def _get_invalid_pyproject_toml_keys(ctx: click.Context, deptry_toml_config_keys: set[str]) -> list[str]:
    """Returns the list of options set in `pyproject.toml` that do not exist as CLI parameters."""
    existing_cli_params = {param.name for param in ctx.command.params}

    return sorted(deptry_toml_config_keys.difference(existing_cli_params))


def read_configuration_from_pyproject_toml(
    ctx: click.Context, param: click.Parameter, value: Path | None
) -> Path | None:
    """
    Callback that, given a click context, overrides the default values with configuration options set in a
    pyproject.toml file.
    Using a callback ensures that the following order is respected for setting an option:
    1. Default value is set
    2. Value is overrode by the one set from pyproject.toml, if any
    3. Value is overrode by the one set from the command line, if any
    """

    if value is None or (param.name == "config" and ctx.params.get("config_only") is not None):
        return value

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
