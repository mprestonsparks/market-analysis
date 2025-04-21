"""
Tests for the AIRFLOW_INTEGRATION.md document in market-analysis repo.
"""

import pytest
from pathlib import Path


def test_airflow_integration_doc_exists():
    path = Path(__file__).parent.parent / 'AIRFLOW_INTEGRATION.md'
    assert path.exists(), 'AIRFLOW_INTEGRATION.md should exist'


def test_airflow_integration_content():
    text = (Path(__file__).parent.parent / 'AIRFLOW_INTEGRATION.md').read_text()
    assert 'market-analysis:latest' in text, 'Docker image tag missing in integration doc'
    assert 'dags/market-analysis/dag_market_analysis_ingestion.py' in text, \
        'DAG path missing in integration doc'