from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest
from inline_snapshot import snapshot

from tests.functional.utils import Project

if TYPE_CHECKING:
    from tests.utils import PipVenvFactory


@pytest.mark.xdist_group(name=Project.GITIGNORE)
def test_cli_gitignore_used(pip_venv_factory: PipVenvFactory) -> None:
    with pip_venv_factory(Project.GITIGNORE) as virtual_env:
        # Simulate the fact that the project is a git repository.
        Path(".git").mkdir(exist_ok=True)

        result = virtual_env.run_deptry(".")

        assert result.returncode == 1
        assert result.stderr == snapshot("""\
Assuming the corresponding module name of package 'black' is 'black'. Install the package or configure a package_module_name_map entry to override this behaviour.
Assuming the corresponding module name of package 'mypy' is 'mypy'. Install the package or configure a package_module_name_map entry to override this behaviour.
Assuming the corresponding module name of package 'pytest' is 'pytest'. Install the package or configure a package_module_name_map entry to override this behaviour.
Scanning 3 files...

pyproject.toml: DEP002 'requests' defined as a dependency but not used in the codebase
pyproject.toml: DEP002 'pytest' defined as a dependency but not used in the codebase
src/foo.py:1:8: DEP004 'black' imported but declared as a dev dependency
Found 3 dependency issues.

For more information, see the documentation: https://deptry.com/
""")


@pytest.mark.xdist_group(name=Project.GITIGNORE)
def test_cli_gitignore_used_for_non_root_directory(pip_venv_factory: PipVenvFactory) -> None:
    with pip_venv_factory(Project.GITIGNORE) as virtual_env:
        # Simulate the fact that the project is a git repository.
        Path(".git").mkdir(exist_ok=True)

        result = virtual_env.run_deptry("src")

        assert result.returncode == 1
        assert result.stderr == snapshot("""\
Assuming the corresponding module name of package 'black' is 'black'. Install the package or configure a package_module_name_map entry to override this behaviour.
Assuming the corresponding module name of package 'mypy' is 'mypy'. Install the package or configure a package_module_name_map entry to override this behaviour.
Assuming the corresponding module name of package 'pytest' is 'pytest'. Install the package or configure a package_module_name_map entry to override this behaviour.
Scanning 3 files...

pyproject.toml: DEP002 'requests' defined as a dependency but not used in the codebase
pyproject.toml: DEP002 'pytest' defined as a dependency but not used in the codebase
src/foo.py:1:8: DEP004 'black' imported but declared as a dev dependency
Found 3 dependency issues.

For more information, see the documentation: https://deptry.com/
""")


@pytest.mark.xdist_group(name=Project.GITIGNORE)
def test_cli_gitignore_not_used_when_using_exclude(pip_venv_factory: PipVenvFactory) -> None:
    with pip_venv_factory(Project.GITIGNORE) as virtual_env:
        # Simulate the fact that the project is a git repository.
        Path(".git").mkdir(exist_ok=True)

        result = virtual_env.run_deptry(". --exclude build/|src/bar\\.py")

        assert result.returncode == 1
        assert result.stderr == snapshot("""\
Assuming the corresponding module name of package 'black' is 'black'. Install the package or configure a package_module_name_map entry to override this behaviour.
Assuming the corresponding module name of package 'mypy' is 'mypy'. Install the package or configure a package_module_name_map entry to override this behaviour.
Assuming the corresponding module name of package 'pytest' is 'pytest'. Install the package or configure a package_module_name_map entry to override this behaviour.
Scanning 5 files...

pyproject.toml: DEP002 'isort' defined as a dependency but not used in the codebase
pyproject.toml: DEP002 'requests' defined as a dependency but not used in the codebase
pyproject.toml: DEP002 'pytest' defined as a dependency but not used in the codebase
src/barfoo.py:1:8: DEP001 'hello' imported but missing from the dependency definitions
src/baz.py:1:8: DEP001 'hej' imported but missing from the dependency definitions
src/foo.py:1:8: DEP004 'black' imported but declared as a dev dependency
src/foobar.py:1:8: DEP004 'mypy' imported but declared as a dev dependency
Found 7 dependency issues.

For more information, see the documentation: https://deptry.com/
""")
