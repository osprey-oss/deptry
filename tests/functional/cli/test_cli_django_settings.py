from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from inline_snapshot import snapshot

from tests.functional.utils import Project

if TYPE_CHECKING:
    from tests.utils import PipVenvFactory


@pytest.mark.xdist_group(name=Project.DJANGO_SETTINGS)
def test_cli_with_django_settings_module_from_configuration(pip_venv_factory: PipVenvFactory) -> None:
    with pip_venv_factory(Project.DJANGO_SETTINGS) as virtual_env:
        result = virtual_env.run_deptry(".")

        assert result.returncode == 1
        assert result.stderr == snapshot("""\
Assuming the corresponding module name of package 'isort' is 'isort'. Install the package or configure a package_module_name_map entry to override this behaviour.
Scanning 2 files...

mysite/settings/dev.py:3:20: DEP004 'isort' imported but declared as a dev dependency
mysite/settings/dev.py:3:29: DEP001 'white' imported but missing from the dependency definitions
Found 2 dependency issues.

For more information, see the documentation: https://deptry.com/
""")


@pytest.mark.xdist_group(name=Project.DJANGO_SETTINGS)
def test_cli_with_django_settings_module_from_command_line(pip_venv_factory: PipVenvFactory) -> None:
    with pip_venv_factory(Project.DJANGO_SETTINGS) as virtual_env:
        result = virtual_env.run_deptry(". --django-settings-module mysite.settings.base")

        assert result.returncode == 0
        assert result.stderr == snapshot("""\
Assuming the corresponding module name of package 'isort' is 'isort'. Install the package or configure a package_module_name_map entry to override this behaviour.
Scanning 2 files...

Success! No dependency issues found.
""")


@pytest.mark.xdist_group(name=Project.DJANGO_SETTINGS)
def test_cli_with_missing_django_settings_module(pip_venv_factory: PipVenvFactory) -> None:
    with pip_venv_factory(Project.DJANGO_SETTINGS) as virtual_env:
        result = virtual_env.run_deptry(". --django-settings-module mysite.settings.missing")

        assert result.returncode == 2
        assert (
            "Error: Cannot read Django settings: Cannot locate Django settings module 'mysite.settings.missing' beneath ."
            in result.stderr
        )
