"""
Test configuration and fixtures.
"""
import pytest
import asyncio
from fastapi.testclient import TestClient
from src.api.core.app import app

pytest_plugins = ["pytest_asyncio"]

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for each test case."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_app():
    """Create a test application."""
    return app

@pytest.fixture
def test_client(test_app):
    """Create a test client using the test application."""
    with TestClient(test_app) as client:
        yield client
