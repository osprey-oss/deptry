# Usage

## Basic Usage

_deptry_ can be run with:

```shell
deptry .
```

where `.` is the path to the root directory of the project to be scanned.

If your project has multiple source directories, multiple root directories can be provided:

```shell
deptry a_directory another_directory
```

If you want to configure _deptry_ using `pyproject.toml`, or if your dependencies are stored in `pyproject.toml`, but it is located in another location than the one _deptry_ is run from, you can specify the location to it by using `--config <path_to_pyproject.toml>` argument.

## Dependencies extraction

_deptry_ can extract dependencies from a broad range of [dependency managers](supported-dependency-managers.md).

Dependencies are always extracted into two separate groups:

- regular ones, meant to be used in the codebase
- development ones

This is an important distinction, as development dependencies are usually meant to only be used outside the
codebase (e.g. `pytest` to run tests, Mypy for type-checking, or Ruff for formatting). For this reason, _deptry_ will
not run [Unused dependencies (DEP002)](rules-violations.md#unused-dependencies-dep002) for development dependencies.

## Imports extraction

_deptry_ will search for imports in Python files (`*.py`, and `*.ipynb` unless [`--ignore-notebooks`](configuration.md#ignore-notebooks)
is set) that are not part of excluded files.

Imports will be extracted regardless of where they are made in a file (top-level, functions, class methods, guarded by
conditions, ...).

The only exception is imports that are guarded
by [`TYPE_CHECKING`](https://docs.python.org/3/library/typing.html#typing.TYPE_CHECKING). In this specific case,
_deptry_ will not extract those imports, as they are not considered problematic. For instance:

```python
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # This import will not be extracted as it is guarded by `TYPE_CHECKING` and `from __future__ import annotations`
    # is used. This means the import should only be evaluated by type checkers, and should not be evaluated during runtime.
    import mypy_boto3_s3
```

### Inline ignore comments

Individual import statements can be excluded from _deptry_'s analysis by adding an inline `# deptry: ignore` comment,
similar to `# noqa` in flake8/ruff or `# type: ignore` in mypy. The following forms are supported:

```python
import foo  # deptry: ignore
```

This will suppress all violation rules for this import. To suppress only specific rules, provide the rule codes in
brackets:

```python
import foo  # deptry: ignore[DEP001]
import bar  # deptry: ignore[DEP001,DEP003]
```

The comment must be placed on the same line as the import statement (specifically, on the line where the `import` or
`from` keyword appears).

!!! note

    Inline ignore comments only apply to rules that report violations on import lines (DEP001, DEP003, DEP004).
    Rules that report on dependency definitions (DEP002, DEP005) are not affected, as their violations point to
    `pyproject.toml` or requirements files, not to source code lines.

### Dynamic imports

There is some support for imports created with [`importlib.import_module`](https://docs.python.org/3/library/importlib.html#importlib.import_module) that use a string literal:

```python
import importlib

importlib.import_module("foo")  # package 'foo' imported
```

but not where the argument is provided dynamically from a variable, attribute, etc., e.g.:

```python
bar = "foo"
importlib.import_module(bar)  # Not detected
```

## Excluding files and directories

To determine issues with imported modules and dependencies, _deptry_ will scan the working directory and its subdirectories recursively for `.py` and `.ipynb` files, so it can
extract the imported modules from those files. Any file solely used for development purposes, such as a file used for unit testing, should not be scanned. By default, the directories
`venv`, `.venv`, `.direnv`, `tests`, `.git` and the file `setup.py` are excluded.

_deptry_ also reads entries in `.gitignore` file, to ignore any pattern present in the file, similarly to what `git` does.

To ignore other directories and files than the defaults, use the `--exclude` (short `-e`) flag. The argument can either be one long regular expression, or it can be reused multiple times to pass multiple smaller regular expressions. The paths should be specified as paths relative to the directory _deptry_ is running in, without the trailing `./`. An example:

```shell
deptry . --exclude bar --exclude ".*/foo/"
deptry . --exclude "bar|.*/foo/"
```

The two statements above are equivalent, and will both ignore all files in the directory `bar`, and all files within any directory named `foo`.

Note that using the `--exclude` argument overwrites the defaults, and will prevent _deptry_ from considering entries in
`.gitignore`.
To add additional patterns to ignore on top of the defaults instead of overwriting them, or to make sure that _deptry_
still considers `.gitignore`, use the `--extend-exclude` (short `-ee`) flag.

```shell
deptry . --extend-exclude bar --extend-exclude ".*/foo/"
deptry . --extend-exclude "bar|.*/foo/"
```

This will exclude `venv`, `.venv`, `.direnv`, `.git`, `tests`, `setup.py`, `bar`, and any directory named `foo`, as well
as entries in `.gitignore`, if there are some.

## Usage in pre-commit

_deptry_ can be added to your [pre-commit](https://pre-commit.com/) rules. Here is
an example config for your `.pre-commit-config.yaml` file:

```yaml
- repo: https://github.com/osprey-oss/deptry.git
  rev: "<tag>"
  hooks:
    - id: deptry
      args: ["--ignore", "DEP001"]
```

Replace `<tag>` with one of the [tags](https://github.com/osprey-oss/deptry/tags) from the
project or a specific commit hash.

!!! important

    This will only pull in the pre commit-hooks config file from the version passed to the `rev` agument. The actual version of _deptry_ that will be run will be the first one found in your path, so you will need to add _deptry_ to your local virtual environment.

    For the pre-commit hook to run successfully, it should be run within the virtual environment of the project to be scanned, since it needs access to the metadata of the installed packages.

## Increasing verbosity

To show more details about the scanned Python files, the imported modules found, and how _deptry_ determines issues in dependencies, add the `--verbose` (short `-v`) flag:

```shell
deptry . --verbose
```
