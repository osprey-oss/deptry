from __future__ import annotations

import concurrent.futures
from pathlib import Path
from typing import TYPE_CHECKING

from deptry.imports.extract import get_imported_modules_from_list_of_files

if TYPE_CHECKING:
    from deptry.imports.location import Location

ITERATIONS = 50
WORKERS = 8
FIXTURE_FILE = Path("tests/fixtures/some_imports.py")


def _extract_imports() -> dict[str, list[Location]]:
    return get_imported_modules_from_list_of_files([FIXTURE_FILE])


def test_concurrent_import_extraction() -> None:
    if not FIXTURE_FILE.exists():
        return

    expected = _extract_imports()

    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = [pool.submit(_extract_imports) for _ in range(ITERATIONS)]
        results = [f.result() for f in futures]

    for result in results:
        assert set(result.keys()) == set(expected.keys())
