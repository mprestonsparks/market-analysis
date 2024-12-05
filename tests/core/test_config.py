"""
Tests for configuration management.
"""
import pytest
from src.api.core.config import Settings, get_settings

def test_default_settings():
    """Test default settings values."""
    settings = get_settings()
    assert settings.app_name == "Market Analysis API"
    assert settings.debug is False
    assert settings.api_host == "0.0.0.0"
    assert settings.api_port == 8000

def test_settings_override():
    """Test settings can be overridden."""
    custom_settings = Settings(
        app_name="Custom API",
        debug=True,
        api_port=9000
    )
    assert custom_settings.app_name == "Custom API"
    assert custom_settings.debug is True
    assert custom_settings.api_port == 9000
