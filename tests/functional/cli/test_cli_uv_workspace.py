from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from inline_snapshot import snapshot

from tests.functional.utils import Project

if TYPE_CHECKING:
    from tests.utils import UvVenvFactory


@pytest.mark.xdist_group(name=Project.UV_WORKSPACE)
def test_cli_with_uv_workspace(uv_venv_factory: UvVenvFactory) -> None:
    with uv_venv_factory(Project.UV_WORKSPACE) as virtual_env:
        result = virtual_env.run_deptry(".")

        assert result.returncode == 1
        assert result.stderr == snapshot("""\
Scanning 1 file...
Scanning 1 file...
Scanning 1 file...

packages/bar/pyproject.toml: DEP002 'pandas' defined as a dependency but not used in the codebase
packages/baz/baz/__init__.py:2:1: DEP101 'bar2' imported but it is a uv workspace sibling not declared as a dependency
packages/foo/foo/__init__.py:1:8: DEP102 'pandas' imported but is not declared as a dependency, it is available only because another workspace member declares it
Found 3 dependency issues.

For more information, see the documentation: https://deptry.com/
""")
