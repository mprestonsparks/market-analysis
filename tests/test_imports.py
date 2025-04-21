"""
Smoke tests to ensure key modules import correctly.
"""

import importlib
import pytest


@pytest.mark.parametrize("module", [
    "src.main",
    "src.market_analysis",
    "src.data_providers.interactive_brokers_provider",
])
def test_module_imports(module):
    try:
        importlib.import_module(module)
    except Exception as e:
        pytest.fail(f"Failed to import {module}: {e}")