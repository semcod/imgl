"""Guards against pytest collection breaking for the whole repo.

2026-07-05 incident: `pytest --collect-only` failed before collecting a
single test, with `ModuleNotFoundError: No module named 'dsl2imgl'`.
`dsl2imgl` is an optional sub-package installed via `imgl install control`
(see `imgl/installs.py`), not part of the root venv by default. Its two
test files did a bare top-level `from dsl2imgl import ...`, which broke
collection for the *entire* repo whenever the control stack wasn't
installed. Fixed with `pytest.importorskip("dsl2imgl")` in both files so
they skip cleanly instead.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent


def test_root_collection_succeeds_without_import_errors():
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, (
        f"pytest --collect-only failed (rc={result.returncode}):\n"
        f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
    )
    assert "ModuleNotFoundError" not in result.stdout
    assert "error during collection" not in result.stdout.lower()


def test_dsl2imgl_tests_skip_cleanly_when_not_installed():
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "packages/dsl2imgl/tests/", "-q"],
        cwd=_REPO_ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )
    # exit code 5 = "no tests collected" -- expected here: importorskip()
    # skips at module-collection time when dsl2imgl isn't installed, so
    # there are zero *collected* items, not a failure.
    assert result.returncode in (0, 5), (
        f"unexpected exit code {result.returncode}:\n{result.stdout}"
    )
    assert "error" not in result.stdout.lower()
    assert "modulenotfounderror" not in result.stdout.lower()
