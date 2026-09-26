from __future__ import annotations

from pathlib import Path

from deptry.dependency import Dependency
from deptry.imports.location import Location
from deptry.module import Module, ModuleLocations
from deptry.violations import DEP006OptionalDependencyPlacementViolation
from deptry.violations.dep006_optional_runtime.finder import DEP006OptionalDependencyPlacementFinder

SNOWFLAKE = Dependency("snowflake-connector-python", Path("pyproject.toml"), module_names=("snowflake",))
PSYCOPG = Dependency("psycopg", Path("pyproject.toml"), module_names=("psycopg",))
HTTPX = Dependency("httpx", Path("pyproject.toml"), module_names=("httpx",))


def _finder(
    modules_locations: list[ModuleLocations],
    *,
    runtime: dict[str, tuple[str, ...]] | None = None,
    optional_groups: dict[str, tuple[Dependency, ...]] | None = None,
    project_dependencies: tuple[Dependency, ...] = (),
    ignored_modules: tuple[str, ...] = (),
    source_roots: tuple[Path, ...] = (Path("."),),
) -> DEP006OptionalDependencyPlacementFinder:
    return DEP006OptionalDependencyPlacementFinder(
        modules_locations,
        [SNOWFLAKE, PSYCOPG, HTTPX],
        frozenset(),
        ignored_modules=ignored_modules,
        optional_dependencies_runtime=runtime
        or {
            "snowflake": ("mypackage.snowflake", "mypackage.snowflake.*"),
            "postgres": ("mypackage.postgres", "mypackage.postgres.*"),
        },
        optional_group_dependencies=optional_groups
        or {
            "snowflake": (SNOWFLAKE,),
            "postgres": (PSYCOPG,),
        },
        project_dependencies=project_dependencies,
        source_roots=source_roots,
    )


def test_unconfigured_runtime_map_reports_nothing() -> None:
    module = Module("snowflake", package="snowflake-connector-python")
    locations = [Location(Path("mypackage/core.py"), 1, 0)]

    finder = DEP006OptionalDependencyPlacementFinder(
        [ModuleLocations(module, locations)],
        [SNOWFLAKE],
        frozenset(),
        optional_group_dependencies={"snowflake": (SNOWFLAKE,)},
    )

    assert finder.find() == []


def test_base_module_importing_extra_is_reported() -> None:
    module = Module("snowflake", package="snowflake-connector-python")
    location = Location(Path("mypackage/core.py"), 1, 0)

    assert _finder([ModuleLocations(module, [location])]).find() == [
        DEP006OptionalDependencyPlacementViolation(module, location, group="snowflake")
    ]


def test_mapped_module_importing_extra_is_allowed() -> None:
    module = Module("snowflake", package="snowflake-connector-python")
    location = Location(Path("mypackage/snowflake.py"), 1, 0)

    assert not _finder([ModuleLocations(module, [location])]).find()


def test_mapped_descendant_importing_extra_is_allowed() -> None:
    module = Module("snowflake", package="snowflake-connector-python")
    location = Location(Path("mypackage/snowflake/client.py"), 1, 0)

    assert not _finder([ModuleLocations(module, [location])]).find()


def test_wrong_extra_region_is_reported() -> None:
    module = Module("snowflake", package="snowflake-connector-python")
    location = Location(Path("mypackage/postgres.py"), 1, 0)

    assert _finder([ModuleLocations(module, [location])]).find() == [
        DEP006OptionalDependencyPlacementViolation(module, location, group="snowflake")
    ]


def test_package_also_in_project_dependencies_is_allowed_everywhere() -> None:
    module = Module("snowflake", package="snowflake-connector-python")
    location = Location(Path("mypackage/core.py"), 1, 0)

    assert not _finder(
        [ModuleLocations(module, [location])],
        project_dependencies=(SNOWFLAKE,),
    ).find()


def test_src_layout_matches_module_pattern_suffix() -> None:
    module = Module("snowflake", package="snowflake-connector-python")
    location = Location(Path("src/mypackage/snowflake.py"), 1, 0)

    assert not _finder([ModuleLocations(module, [location])], source_roots=(Path("."),)).find()


def test_unmapped_extra_is_not_reported() -> None:
    module = Module("httpx", package="httpx")
    location = Location(Path("mypackage/core.py"), 1, 0)

    assert not _finder(
        [ModuleLocations(module, [location])],
        optional_groups={"snowflake": (SNOWFLAKE,), "plot": (HTTPX,)},
    ).find()


def test_per_rule_ignore_by_module_name() -> None:
    module = Module("snowflake", package="snowflake-connector-python")
    location = Location(Path("mypackage/core.py"), 1, 0)

    assert not _finder(
        [ModuleLocations(module, [location])],
        ignored_modules=("snowflake",),
    ).find()
