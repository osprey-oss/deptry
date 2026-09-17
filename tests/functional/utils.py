from __future__ import annotations

from enum import Enum

TEST_DEPTRY_COMMAND = "deptry --enforce-posix-paths"
DEPTRY_WHEEL_DIRECTORY = "build/functional_tests/deptry"


class Project(str, Enum):
    DEPRECATED_OPTIONS = "deprecated_options"
    EXAMPLE = "example"
    GITIGNORE = "gitignore"
    INLINE_IGNORES = "inline_ignores"
    MULTIPLE_SOURCE_DIRECTORIES = "multiple_source_directories"
    NAMESPACE = "namespace"
    PDM = "pdm"
    PEP_621 = "pep_621"
    PEP_723 = "pep_723"
    POETRY = "poetry"
    POETRY_PEP_621 = "poetry_pep_621"
    PYPROJECT_DIFFERENT_DIRECTORY = "pyproject_different_directory"
    REQUIREMENTS_IN = "requirements_in"
    REQUIREMENTS_TXT = "requirements_txt"
    SRC_DIRECTORY = "src_directory"
    SETUPTOOLS_DYNAMIC_DEPENDENCIES = "setuptools_dynamic_dependencies"
    UV = "uv"
    WITHOUT_DEPTRY_OPTION = "without_deptry_option"

    def __str__(self) -> str:
        return self.value
