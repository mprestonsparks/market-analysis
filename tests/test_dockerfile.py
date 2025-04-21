"""
Tests for Dockerfile.airflow in market-analysis repo.
"""

import pytest
from pathlib import Path


def test_dockerfile_exists():
    path = Path(__file__).parent.parent / 'docker' / 'Dockerfile.airflow'
    assert path.exists(), 'Dockerfile.airflow should exist under docker/'


def test_dockerfile_base_image():
    path = Path(__file__).parent.parent / 'docker' / 'Dockerfile.airflow'
    content = path.read_text()
    assert content.startswith('FROM python:3.9-slim'), \
        'Dockerfile.airflow should use python:3.9-slim as base image'