"""
Test that all Airflow DAGs in the dags/ directory can be imported without error.
This is a basic smoke test to catch syntax errors before deployment.
"""
import os
import importlib.util
import pytest
import sys
import types

def get_dag_files():
    dags_dir = os.path.join(os.path.dirname(__file__), '..', 'dags')
    return [
        os.path.join(dags_dir, f)
        for f in os.listdir(dags_dir)
        if f.endswith('.py') and not f.startswith('__')
    ]

@pytest.mark.parametrize('dag_file', get_dag_files())
def test_dag_import(dag_file):
    # Monkeypatch airflow modules with stubs
    stub_path = Path(__file__).parent / 'airflow_stubs.py'
    stub = types.ModuleType('airflow_stubs')
    exec(stub_path.read_text(), stub.__dict__)
    # Create fake airflow module
    airflow_mod = types.ModuleType('airflow')
    airflow_mod.DAG = stub.DAG
    sys.modules['airflow'] = airflow_mod
    # Create fake airflow.providers.docker.operators.docker module
    docker_mod = types.ModuleType('airflow.providers.docker.operators.docker')
    docker_mod.DockerOperator = stub.DockerOperator
    sys.modules['airflow.providers.docker.operators.docker'] = docker_mod
    # Now import the DAG file
    try:
        spec = importlib.util.spec_from_file_location('dag_module', dag_file)
        module = importlib.util.module_from_spec(spec)
        import traceback
        spec.loader.exec_module(module)
    except Exception as e:
        print(f"\n\nException while importing {dag_file}:")
        traceback.print_exc()
        pytest.fail(f"Failed to import {dag_file}: {e}")
