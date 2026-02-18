import py_compile
from pathlib import Path

import pytest


@pytest.mark.parametrize(
    "relative_path",
    [
        "__init__.py",
        "05_adapters/openclaw_adapter.py",
        "tests/test_core.py",
        "shell/__init__.py",
        "shell/05_adapters/openclaw_adapter.py",
        "shell/tests/test_core.py",
    ],
)
def test_numeric_module_reference_files_compile(relative_path: str):
    repo_root = Path(__file__).resolve().parent.parent
    py_compile.compile(str(repo_root / relative_path), doraise=True)
