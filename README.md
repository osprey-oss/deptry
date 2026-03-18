<p align="center">
  <img alt="deptry logo" width="460" height="300" src="https://raw.githubusercontent.com/osprey-oss/deptry/main/docs/static/deptry_Logo-01.svg">
</p>

[![Release](https://img.shields.io/github/v/release/osprey-oss/deptry)](https://pypi.org/project/deptry/)
[![Build status](https://github.com/osprey-oss/deptry/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/osprey-oss/deptry/actions/workflows/main.yml)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/deptry)](https://pypi.org/project/deptry/)
[![codecov](https://codecov.io/gh/osprey-oss/deptry/branch/main/graph/badge.svg)](https://codecov.io/gh/osprey-oss/deptry)
[![PyPI - Downloads](https://img.shields.io/pypi/dm/deptry)](https://pypistats.org/packages/deptry)
[![License](https://img.shields.io/github/license/osprey-oss/deptry)](https://img.shields.io/github/license/osprey-oss/deptry)

_deptry_ is a command line tool to check for issues with dependencies in a Python project, such as unused or missing
dependencies. It supports projects
using [Poetry](https://python-poetry.org/), [pip](https://pip.pypa.io/), [PDM](https://pdm-project.org/), [uv](https://docs.astral.sh/uv/),
and more generally any project supporting [PEP 621](https://peps.python.org/pep-0621/) specification.

Dependency issues are detected by scanning for imported modules within all Python files in a directory and its
subdirectories, and comparing those to the dependencies listed in the project's requirements.

---
<p align="center">
  <a href="https://deptry.com">Documentation</a> - <a href="https://deptry.com/contributing/">Contributing</a>
</p>

---

## Quickstart

### Installation

To add _deptry_ to your project, run one of the following commands:

```shell
# Install with poetry
poetry add --group dev deptry

# Install with pip
pip install deptry
```

> **Warning**: When using pip to install _deptry_, make sure you install it within the virtual environment of your project. Installing _deptry_ globally will not work, since it needs to have access to the metadata of the packages in the virtual environment.

### Prerequisites

_deptry_ should be run within the root directory of the project to be scanned, and the project should be running in its own dedicated virtual environment.

### Usage

To scan your project for dependency issues, run:

```shell
deptry .
```

Example output could look as follows:

```console
Scanning 2 files...

foo/bar.py:1:0: DEP004 'numpy' imported but declared as a dev dependency
foo/bar.py:2:0: DEP001 'matplotlib' imported but missing from the dependency definitions
pyproject.toml: DEP002 'pandas' defined as a dependency but not used in the codebase
Found 3 dependency issues.
```

### Configuration

_deptry_ can be configured by using additional command line arguments, or by adding a `[tool.deptry]` section in _pyproject.toml_. For more information, see the [Usage and Configuration](https://deptry.com/usage/) section of the documentation..

---

Repository initiated with [fpgmaas/cookiecutter-poetry](https://github.com/fpgmaas/cookiecutter-poetry).
