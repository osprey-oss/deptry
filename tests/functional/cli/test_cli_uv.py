from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from inline_snapshot import snapshot

from tests.functional.utils import Project

if TYPE_CHECKING:
    from tests.utils import UvVenvFactory


@pytest.mark.xdist_group(name=Project.UV)
def test_cli_with_uv(uv_venv_factory: UvVenvFactory) -> None:
    with uv_venv_factory(Project.UV) as virtual_env:
        result = virtual_env.run_deptry(".")

        assert result.returncode == 1
        assert result.stderr == snapshot("""\
Scanning 2 files...

pyproject.toml: DEP002 'isort' defined as a dependency but not used in the codebase
src/main.py:4:8: DEP004 'black' imported but declared as a dev dependency
src/main.py:5:8: DEP004 'certifi' imported but declared as a dev dependency
src/main.py:8:8: DEP004 'mypy' imported but declared as a dev dependency
src/main.py:9:8: DEP004 'packaging' imported but declared as a dev dependency
src/main.py:10:8: DEP004 'pytest' imported but declared as a dev dependency
src/main.py:11:8: DEP004 'pytest_cov' imported but declared as a dev dependency
src/main.py:12:8: DEP001 'white' imported but missing from the dependency definitions
Found 8 dependency issues.

For more information, see the documentation: https://deptry.com/
""")
