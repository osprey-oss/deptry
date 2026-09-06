from __future__ import annotations

from pathlib import Path

from deptry.dependency_getter.pep621.poetry import PoetryDependencyGetter
from tests.utils import run_within_dir


def test_dependency_getter(tmp_path: Path) -> None:
    fake_pyproject_toml = """
[tool.poetry]
name = "foo"

[tool.poetry.dependencies]
python = ">=3.7,<4.0"
bar = { version = ">=2.5.1,<4.0.0", python = ">3.7" }
foo-bar = { version = ">=2.5.1,<4.0.0", optional = true, python = ">3.7" }
fox-python = "*"  # top level module is called "fox"

[tool.poetry.dev-dependencies]
toml = "^0.10.2"
qux = { version = ">=2.5.1,<4.0.0", optional = true }

[tool.poetry.group.lint.dependencies]
black = "^22.6.0"
mypy = "^1.3.0"

[tool.poetry.group.test.dependencies]
pytest = "^7.3.0"
pytest-cov = "^4.0.0"
"""

    with run_within_dir(tmp_path):
        with Path("pyproject.toml").open("w") as f:
            f.write(fake_pyproject_toml)

        getter = PoetryDependencyGetter(
            config=Path("pyproject.toml"),
            package_module_name_map={"fox-python": ("fox",)},
        )
        dependencies_extract = getter.get()
        dependencies = dependencies_extract.dependencies
        dev_dependencies = dependencies_extract.dev_dependencies

        assert len(dependencies) == 3
        assert len(dev_dependencies) == 6

        assert dependencies[0].name == "bar"
        assert "bar" in dependencies[0].top_levels

        assert dependencies[1].name == "foo-bar"
        assert "foo_bar" in dependencies[1].top_levels

        assert dependencies[2].name == "fox-python"
        assert "fox" in dependencies[2].top_levels

        assert dev_dependencies[0].name == "toml"
        assert "toml" in dev_dependencies[0].top_levels

        assert dev_dependencies[1].name == "qux"
        assert "qux" in dev_dependencies[1].top_levels

        assert dev_dependencies[2].name == "black"
        assert "black" in dev_dependencies[2].top_levels

        assert dev_dependencies[3].name == "mypy"
        assert "mypy" in dev_dependencies[3].top_levels

        assert dev_dependencies[4].name == "pytest"
        assert "pytest" in dev_dependencies[4].top_levels

        assert dev_dependencies[5].name == "pytest-cov"
        assert "pytest_cov" in dev_dependencies[5].top_levels


def test_dependency_getter_pep_621(tmp_path: Path) -> None:
    fake_pyproject_toml = """
[project]
name = "foo"
requires-python = ">=3.7,<4.0"
dependencies = [
    "bar>=2.5.1,<4.0.0",
    "fox-python",
]

[project.optional-dependencies]
an-extra = ["foobar>=2.5.1,<4.0.0"]

[tool.poetry.dependencies]
fox-python = { git = "https://example.com/foo/bar.git", tag = "v1.2.3" }
# This dependency will not be used by Poetry nor extracted by deptry, as `[project.dependencies]` defines at least once
# dependency, and in this case, dependencies in `[tool.poetry.dependencies]` only enrich existing dependencies from
# `[project.dependencies]`, so deptry will completely skip `[tool.poetry.dependencies]`.
skipped-dependency = "1.2.3"

[tool.poetry.dev-dependencies]
toml = "^0.10.2"
qux =  { version = ">=2.5.1,<4.0.0", optional = true }

[tool.poetry.group.lint.dependencies]
black = "^22.6.0"
mypy = "^1.3.0"

[tool.poetry.group.test.dependencies]
pytest = "^7.3.0"
pytest-cov = "^4.0.0"
"""

    with run_within_dir(tmp_path):
        with Path("pyproject.toml").open("w") as f:
            f.write(fake_pyproject_toml)

        getter = PoetryDependencyGetter(
            config=Path("pyproject.toml"),
            package_module_name_map={"fox-python": ("fox",)},
        )
        dependencies_extract = getter.get()
        dependencies = dependencies_extract.dependencies
        dev_dependencies = dependencies_extract.dev_dependencies

        assert len(dependencies) == 3
        assert len(dev_dependencies) == 6

        assert dependencies[0].name == "bar"
        assert "bar" in dependencies[0].top_levels

        assert dependencies[1].name == "fox-python"
        assert "fox" in dependencies[1].top_levels

        assert dependencies[2].name == "foobar"
        assert "foobar" in dependencies[2].top_levels

        assert dev_dependencies[0].name == "toml"
        assert "toml" in dev_dependencies[0].top_levels

        assert dev_dependencies[1].name == "qux"
        assert "qux" in dev_dependencies[1].top_levels

        assert dev_dependencies[2].name == "black"
        assert "black" in dev_dependencies[2].top_levels

        assert dev_dependencies[3].name == "mypy"
        assert "mypy" in dev_dependencies[3].top_levels

        assert dev_dependencies[4].name == "pytest"
        assert "pytest" in dev_dependencies[4].top_levels

        assert dev_dependencies[5].name == "pytest-cov"
        assert "pytest_cov" in dev_dependencies[5].top_levels


def test_dependency_getter_empty_dependencies(tmp_path: Path) -> None:
    fake_pyproject_toml = """
[tool.poetry]
name = "foo"
"""

    with run_within_dir(tmp_path):
        with Path("pyproject.toml").open("w") as f:
            f.write(fake_pyproject_toml)

        getter = PoetryDependencyGetter(config=Path("pyproject.toml"))
        dependencies_extract = getter.get()

        assert len(dependencies_extract.dependencies) == 0
        assert len(dependencies_extract.dev_dependencies) == 0


def test_dependency_getter_non_dev_dependency_groups(tmp_path: Path) -> None:
    fake_pyproject_toml = """
[tool.poetry]
name = "foo"

[tool.poetry.dependencies]
python = ">=3.9"
bar = "^1.0.0"

[tool.poetry.group.baremetal.dependencies]
uvicorn = "^0.30.0"

[tool.poetry.group.test.dependencies]
pytest = "^7.3.0"
"""

    with run_within_dir(tmp_path):
        with Path("pyproject.toml").open("w") as f:
            f.write(fake_pyproject_toml)

        getter = PoetryDependencyGetter(config=Path("pyproject.toml"), non_dev_dependency_groups=("baremetal",))
        dependencies_extract = getter.get()

        assert [dependency.name for dependency in dependencies_extract.dependencies] == ["bar", "uvicorn"]
        assert [dependency.name for dependency in dependencies_extract.dev_dependencies] == ["pytest"]
