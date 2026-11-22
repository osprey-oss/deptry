# deptry — VS Code Extension

Surfaces [deptry](https://deptry.com) dependency violations as inline diagnostics in VS Code.

## Features

- Runs `deptry` automatically on save and shows issues in the Problems panel
- Inline squiggles on the offending import or dependency definition
- Each diagnostic links to the relevant rule documentation
- Status bar item showing live run state and issue count

### Detected issues

| Code | Description |
|------|-------------|
| DEP001 | Import missing from dependency definitions |
| DEP002 | Dependency declared but not used |
| DEP003 | Transitive dependency used directly |
| DEP004 | Dev dependency used in non-dev code |
| DEP005 | Standard library module declared as dependency |

## Requirements

`deptry` must be installed in your project's virtual environment:

```bash
pip install deptry
# or
uv add --dev deptry
```

The extension automatically discovers the deptry binary from:
1. The Python interpreter selected in the VS Code Python extension
2. Common local venv directories (`.venv`, `venv`, `env`)
3. `deptry` on your system `PATH`

## Configuration

| Setting | Default | Description |
|---------|---------|-------------|
| `deptry.executable` | `"deptry"` | Explicit path to binary (e.g. `.venv/bin/deptry`) |
| `deptry.runOnSave` | `true` | Re-run on Python / `pyproject.toml` save |
| `deptry.args` | `[]` | Extra CLI arguments (e.g. `["--ignore", "DEP002"]`) |
| `deptry.rootDirectory` | `""` | Directory to scan. Defaults to workspace root so that deptry uses your `pyproject.toml` config |
| `deptry.severityMap` | see below | Map error codes to diagnostic severity |

Default severity map:
```json
{
  "DEP001": "error",
  "DEP002": "warning",
  "DEP003": "warning",
  "DEP004": "error",
  "DEP005": "warning"
}
```

## Commands

| Command | Description |
|---------|-------------|
| `deptry: Run Dependency Check` | Run deptry manually |
| `deptry: Clear Diagnostics` | Clear all deptry diagnostics |

## How it works

The extension runs `deptry . --json-output <tmpfile>` from your workspace root, parses the JSON output, and maps each violation to a VS Code diagnostic on the relevant file and line.
