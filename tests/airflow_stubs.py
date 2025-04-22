# Lightweight Airflow stubs for DAG import testing only

class DAG:
    def __init__(self, *args, **kwargs):
        pass
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

class DockerOperator:
    def __init__(self, *args, **kwargs):
        pass
    def __rshift__(self, other):
        return other
    def __lshift__(self, other):
        return other
