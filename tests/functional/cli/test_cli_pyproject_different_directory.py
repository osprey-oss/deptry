from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from inline_snapshot import snapshot

from tests.functional.utils import Project

if TYPE_CHECKING:
    from tests.utils import PipVenvFactory


@pytest.mark.xdist_group(name=Project.PYPROJECT_DIFFERENT_DIRECTORY)
def test_cli_with_pyproject_different_directory(pip_venv_factory: PipVenvFactory) -> None:
    with pip_venv_factory(
        Project.PYPROJECT_DIFFERENT_DIRECTORY, install_command="pip install ./a_sub_directory"
    ) as virtual_env:
        result = virtual_env.run_deptry("src --config a_sub_directory/pyproject.toml")

        assert result.returncode == 1
        assert result.stderr == snapshot("""\
Assuming the corresponding module name of package 'black' is 'black'. Install the package or configure a package_module_name_map entry to override this behaviour.
Assuming the corresponding module name of package 'mypy' is 'mypy'. Install the package or configure a package_module_name_map entry to override this behaviour.
Assuming the corresponding module name of package 'pytest' is 'pytest'. Install the package or configure a package_module_name_map entry to override this behaviour.
Scanning 4 files...

a_sub_directory/pyproject.toml: DEP002 'isort' defined as a dependency but not used in the codebase
a_sub_directory/pyproject.toml: DEP002 'requests' defined as a dependency but not used in the codebase
a_sub_directory/pyproject.toml: DEP002 'pytest' defined as a dependency but not used in the codebase
src/src_directory/foo.py:4:8: DEP004 'black' imported but declared as a dev dependency
src/src_directory/foo.py:6:8: DEP001 'white' imported but missing from the dependency definitions
Found 5 dependency issues.

For more information, see the documentation: https://deptry.com/
""")
