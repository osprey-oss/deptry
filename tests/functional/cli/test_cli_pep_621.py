from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from inline_snapshot import snapshot

from tests.functional.utils import Project

if TYPE_CHECKING:
    from tests.utils import PipVenvFactory


@pytest.mark.xdist_group(name=Project.PEP_621)
def test_cli_with_pep_621(pip_venv_factory: PipVenvFactory) -> None:
    with pip_venv_factory(Project.PEP_621) as virtual_env:
        result = virtual_env.run_deptry(".")

        assert result.returncode == 1
        assert result.stderr == snapshot("""\
Assuming the corresponding module name of package 'black' is 'black'. Install the package or configure a package_module_name_map entry to override this behaviour.
Assuming the corresponding module name of package 'mypy' is 'mypy'. Install the package or configure a package_module_name_map entry to override this behaviour.
Assuming the corresponding module name of package 'pytest' is 'pytest'. Install the package or configure a package_module_name_map entry to override this behaviour.
Scanning 2 files...

pyproject.toml: DEP002 'isort' defined as a dependency but not used in the codebase
pyproject.toml: DEP002 'requests' defined as a dependency but not used in the codebase
pyproject.toml: DEP002 'pytest' defined as a dependency but not used in the codebase
pyproject.toml: DEP005 'asyncio' is defined as a dependency but it is included in the Python standard library.
src/main.py:5:8: DEP004 'black' imported but declared as a dev dependency
src/main.py:6:8: DEP004 'certifi' imported but declared as a dev dependency
src/main.py:9:8: DEP004 'packaging' imported but declared as a dev dependency
src/main.py:10:8: DEP001 'white' imported but missing from the dependency definitions
Found 8 dependency issues.

For more information, see the documentation: https://deptry.com/
""")
