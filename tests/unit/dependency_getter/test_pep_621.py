from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from deptry.dependency_getter.pep621.base import PEP621DependencyGetter
from tests.utils import run_within_dir

if TYPE_CHECKING:
    from _pytest.logging import LogCaptureFixture


def test_dependency_getter(tmp_path: Path) -> None:
    fake_pyproject_toml = """[project]
name = "foo"
dependencies = [
    "qux",
    "bar>=20.9",
    "optional-foo[option]>=0.12.11",
    "conditional-bar>=1.1.0; python_version < '3.11'",
    "fox-python",  # top level module is called "fox"
]

[project.optional-dependencies]
group1 = [
    "foobar",
    "barfoo",
]
group2 = [
    "dep",
]
"""

    with run_within_dir(tmp_path):
        with Path("pyproject.toml").open("w") as f:
            f.write(fake_pyproject_toml)

        getter = PEP621DependencyGetter(
            config=Path("pyproject.toml"),
            package_module_name_map={"fox-python": ("fox",)},
        )
        dependencies = getter.get().dependencies

        assert len(dependencies) == 8

        assert dependencies[0].name == "qux"
        assert "qux" in dependencies[0].top_levels

        assert dependencies[1].name == "bar"
        assert "bar" in dependencies[1].top_levels

        assert dependencies[2].name == "optional-foo"
        assert "optional_foo" in dependencies[2].top_levels

        assert dependencies[3].name == "conditional-bar"
        assert "conditional_bar" in dependencies[3].top_levels

        assert dependencies[4].name == "fox-python"
        assert "fox" in dependencies[4].top_levels

        assert dependencies[5].name == "foobar"
        assert "foobar" in dependencies[5].top_levels

        assert dependencies[6].name == "barfoo"
        assert "barfoo" in dependencies[6].top_levels

        assert dependencies[7].name == "dep"
        assert "dep" in dependencies[7].top_levels

        extract = getter.get()
        assert set(extract.optional_group_dependencies) == {"group1", "group2"}
        assert [dependency.name for dependency in extract.project_dependencies] == [
            "qux",
            "bar",
            "optional-foo",
            "conditional-bar",
            "fox-python",
        ]


def test_dependency_getter_optional_dependencies_dev_groups(tmp_path: Path) -> None:
    fake_pyproject_toml = """[project]
name = "foo"
dependencies = ["qux"]

[project.optional-dependencies]
group1 = ["foobar"]
group2 = ["barfoo"]

[dependency-groups]
dev-group = ["foo", "baz"]
all = [{include-group = "dev-group"}, "foobaz"]
"""

    with run_within_dir(tmp_path):
        with Path("pyproject.toml").open("w") as f:
            f.write(fake_pyproject_toml)

        getter = PEP621DependencyGetter(config=Path("pyproject.toml"), optional_dependencies_dev_groups=("group2",))
        dependencies = getter.get().dependencies
        dev_dependencies = getter.get().dev_dependencies

        assert len(dependencies) == 2
        assert len(dev_dependencies) == 4

        assert dependencies[0].name == "qux"
        assert "qux" in dependencies[0].top_levels

        assert dependencies[1].name == "foobar"
        assert "foobar" in dependencies[1].top_levels

        assert dev_dependencies[0].name == "barfoo"
        assert "barfoo" in dev_dependencies[0].top_levels

        assert dev_dependencies[1].name == "foo"
        assert "foo" in dev_dependencies[1].top_levels

        assert dev_dependencies[2].name == "baz"
        assert "baz" in dev_dependencies[2].top_levels

        assert dev_dependencies[3].name == "foobaz"
        assert "foobaz" in dev_dependencies[3].top_levels


def test_dependency_getter_incorrect_optional_dependencies_dev_group(tmp_path: Path, caplog: LogCaptureFixture) -> None:
    fake_pyproject_toml = """[project]
name = "foo"
dependencies = ["qux"]

[project.optional-dependencies]
group1 = ["foobar"]
group2 = ["barfoo"]
"""

    with run_within_dir(tmp_path), caplog.at_level(logging.INFO):
        with Path("pyproject.toml").open("w") as f:
            f.write(fake_pyproject_toml)

        getter = PEP621DependencyGetter(config=Path("pyproject.toml"), optional_dependencies_dev_groups=("group3",))
        dependencies = getter.get().dependencies

        assert (
            "Trying to extract the dependencies from the optional dependency groups ['group3'] as development dependencies, but the following groups were not found: ['group3']"
            in caplog.text
        )

        assert len(dependencies) == 3

        assert dependencies[0].name == "qux"
        assert "qux" in dependencies[0].top_levels

        assert dependencies[1].name == "foobar"
        assert "foobar" in dependencies[1].top_levels

        assert dependencies[2].name == "barfoo"
        assert "barfoo" in dependencies[2].top_levels


def test_dependency_getter_non_dev_dependency_groups(tmp_path: Path) -> None:
    fake_pyproject_toml = """[project]
name = "foo"
dependencies = ["qux"]

[dependency-groups]
group1 = ["foobar"]
group2 = ["barfoo"]
"""

    with run_within_dir(tmp_path):
        with Path("pyproject.toml").open("w") as f:
            f.write(fake_pyproject_toml)

        getter = PEP621DependencyGetter(config=Path("pyproject.toml"), non_dev_dependency_groups=("group2",))
        dependencies = getter.get().dependencies
        dev_dependencies = getter.get().dev_dependencies

        assert len(dependencies) == 2
        assert len(dev_dependencies) == 1

        assert dependencies[0].name == "qux"
        assert "qux" in dependencies[0].top_levels

        assert dependencies[1].name == "barfoo"
        assert "barfoo" in dependencies[1].top_levels

        assert dev_dependencies[0].name == "foobar"
        assert "foobar" in dev_dependencies[0].top_levels


def test_dependency_getter_incorrect_dependency_groups_non_dev_group(tmp_path: Path, caplog: LogCaptureFixture) -> None:
    fake_pyproject_toml = """[project]
name = "foo"
dependencies = ["qux"]

[dependency-groups]
group1 = ["foobar"]
group2 = ["barfoo"]
"""

    with run_within_dir(tmp_path), caplog.at_level(logging.INFO):
        with Path("pyproject.toml").open("w") as f:
            f.write(fake_pyproject_toml)

        getter = PEP621DependencyGetter(config=Path("pyproject.toml"), non_dev_dependency_groups=("group3",))
        dependencies = getter.get().dependencies
        dev_dependencies = getter.get().dev_dependencies

        assert (
            "Trying to extract the dependencies from the dependency groups ['group3'] as regular dependencies, but the following groups were not found: ['group3']"
            in caplog.text
        )

        assert len(dependencies) == 1
        assert len(dev_dependencies) == 2

        assert dependencies[0].name == "qux"
        assert "qux" in dependencies[0].top_levels

        assert dev_dependencies[0].name == "foobar"
        assert "foobar" in dev_dependencies[0].top_levels

        assert dev_dependencies[1].name == "barfoo"
        assert "barfoo" in dev_dependencies[1].top_levels


def test_dependency_getter_empty_dependencies(tmp_path: Path) -> None:
    fake_pyproject_toml = """[project]
name = "foo"
"""

    with run_within_dir(tmp_path):
        with Path("pyproject.toml").open("w") as f:
            f.write(fake_pyproject_toml)

        getter = PEP621DependencyGetter(config=Path("pyproject.toml"))
        dependencies_extract = getter.get()

        assert len(dependencies_extract.dependencies) == 0
        assert len(dependencies_extract.dev_dependencies) == 0


def test_dependency_getter_invalid_dependencies(tmp_path: Path) -> None:
    """Test that invalid dependencies are skipped, but valid dependencies are still parsed."""
    fake_pyproject_toml = """[project]
name = "foo"
dependencies = [
    "qux",
    # Invalid dependency, as the dependency marker does not exist.
    "foo-bar>=1.1.0; java_version < '3.11'",
    "bar>=20.9",
]
"""

    with run_within_dir(tmp_path):
        with Path("pyproject.toml").open("w") as f:
            f.write(fake_pyproject_toml)

        dependencies = PEP621DependencyGetter(config=Path("pyproject.toml")).get().dependencies

        assert len(dependencies) == 2

        assert dependencies[0].name == "qux"
        assert "qux" in dependencies[0].top_levels

        assert dependencies[1].name == "bar"
        assert "bar" in dependencies[1].top_levels


def test_dependency_getter_with_setuptools_dynamic_dependencies(tmp_path: Path) -> None:
    fake_pyproject_toml = """[build-system]
requires = ["setuptools"]
build-backend = "setuptools.build_meta"

[project]
name = "foo"
dynamic = ["dependencies", "optional-dependencies"]

[tool.setuptools.dynamic]
dependencies = { file = ["requirements.txt", "requirements-2.txt"] }

[tool.setuptools.dynamic.optional-dependencies]
# Both strings and list of strings are accepted.
cli = { file = "cli-requirements.txt" }
dev = { file = ["dev-requirements.txt"] }
"""

    with run_within_dir(tmp_path):
        with Path("pyproject.toml").open("w") as f:
            f.write(fake_pyproject_toml)

        with Path("requirements.txt").open("w") as f:
            f.write("foo==1.2.3")

        with Path("requirements-2.txt").open("w") as f:
            f.write("bar==1.2.3")

        with Path("cli-requirements.txt").open("w") as f:
            f.write("cli-dep==1.2.3")

        with Path("dev-requirements.txt").open("w") as f:
            f.write("dev-dep==1.2.3")

        extract = PEP621DependencyGetter(config=Path("pyproject.toml"), optional_dependencies_dev_groups=("dev",)).get()
        dependencies = extract.dependencies
        dev_dependencies = extract.dev_dependencies

        assert len(dependencies) == 3
        assert len(dev_dependencies) == 1

        assert dependencies[0].name == "foo"
        assert dependencies[1].name == "bar"
        assert dependencies[2].name == "cli-dep"
        assert dev_dependencies[0].name == "dev-dep"


def test_dependency_getter_with_setuptools_dynamic_dependencies_without_build_backend(tmp_path: Path) -> None:
    fake_pyproject_toml = """[project]
name = "foo"
dynamic = ["dependencies", "optional-dependencies"]

[tool.setuptools.dynamic]
dependencies = { file = ["requirements.txt", "requirements-2.txt"] }

[tool.setuptools.dynamic.optional-dependencies]
# Both strings and list of strings are accepted.
cli = { file = "cli-requirements.txt" }
dev = { file = ["dev-requirements.txt"] }
"""

    with run_within_dir(tmp_path):
        with Path("pyproject.toml").open("w") as f:
            f.write(fake_pyproject_toml)

        with Path("requirements.txt").open("w") as f:
            f.write("foo==1.2.3")

        with Path("requirements-2.txt").open("w") as f:
            f.write("bar==1.2.3")

        with Path("cli-requirements.txt").open("w") as f:
            f.write("cli-dep==1.2.3")

        with Path("dev-requirements.txt").open("w") as f:
            f.write("dev-dep==1.2.3")

        extract = PEP621DependencyGetter(config=Path("pyproject.toml"), optional_dependencies_dev_groups=("dev",)).get()
        dependencies = extract.dependencies
        dev_dependencies = extract.dev_dependencies

        assert len(dependencies) == 0
        assert len(dev_dependencies) == 0


def test_dependency_getter_with_setuptools_dynamic_dependencies_with_another_build_backend(tmp_path: Path) -> None:
    fake_pyproject_toml = """[build-system]
requires = ["pdm-backend"]
build-backend = "pdm.backend"

[project]
name = "foo"
dynamic = ["dependencies", "optional-dependencies"]

[tool.setuptools.dynamic]
dependencies = { file = ["requirements.txt", "requirements-2.txt"] }

[tool.setuptools.dynamic.optional-dependencies]
# Both strings and list of strings are accepted.
cli = { file = "cli-requirements.txt" }
dev = { file = ["dev-requirements.txt"] }
"""

    with run_within_dir(tmp_path):
        with Path("pyproject.toml").open("w") as f:
            f.write(fake_pyproject_toml)

        with Path("requirements.txt").open("w") as f:
            f.write("foo==1.2.3")

        with Path("requirements-2.txt").open("w") as f:
            f.write("bar==1.2.3")

        with Path("cli-requirements.txt").open("w") as f:
            f.write("cli-dep==1.2.3")

        with Path("dev-requirements.txt").open("w") as f:
            f.write("dev-dep==1.2.3")

        extract = PEP621DependencyGetter(config=Path("pyproject.toml"), optional_dependencies_dev_groups=("dev",)).get()
        dependencies = extract.dependencies
        dev_dependencies = extract.dev_dependencies

        assert len(dependencies) == 0
        assert len(dev_dependencies) == 0


def test_dependency_getter_with_setuptools_dynamic_dependencies_only_optional(tmp_path: Path) -> None:
    fake_pyproject_toml = """[build-system]
requires = ["setuptools"]
build-backend = "setuptools.build_meta"

[project]
name = "foo"
dependencies = ["foo==1.2.3"]
dynamic = ["optional-dependencies"]

[tool.setuptools.dynamic.optional-dependencies]
dev = { file = ["dev-requirements.txt"] }
"""

    with run_within_dir(tmp_path):
        with Path("pyproject.toml").open("w") as f:
            f.write(fake_pyproject_toml)

        with Path("dev-requirements.txt").open("w") as f:
            f.write("dev-dep==1.2.3")

        extract = PEP621DependencyGetter(config=Path("pyproject.toml"), optional_dependencies_dev_groups=("dev",)).get()
        dependencies = extract.dependencies
        dev_dependencies = extract.dev_dependencies

        assert len(dependencies) == 1
        assert len(dev_dependencies) == 1

        assert dependencies[0].name == "foo"
        assert dev_dependencies[0].name == "dev-dep"


def test_dependency_getter_with_setuptools_dynamic_dependencies_only_dependencies(tmp_path: Path) -> None:
    fake_pyproject_toml = """[build-system]
requires = ["setuptools"]
build-backend = "setuptools.build_meta"

[project]
name = "foo"
dependencies = ["foo==1.2.3"]
dynamic = ["dependencies"]

[tool.setuptools.dynamic]
dependencies = { file = "requirements.txt" }
"""

    with run_within_dir(tmp_path):
        with Path("pyproject.toml").open("w") as f:
            f.write(fake_pyproject_toml)

        with Path("requirements.txt").open("w") as f:
            f.write("foo==1.2.3")

        extract = PEP621DependencyGetter(config=Path("pyproject.toml"), optional_dependencies_dev_groups=("dev",)).get()
        dependencies = extract.dependencies
        dev_dependencies = extract.dev_dependencies

        assert len(dependencies) == 1
        assert len(dev_dependencies) == 0

        assert dependencies[0].name == "foo"
