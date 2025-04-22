"""
Airflow DAG for Trading Project: IBKR Ingestion
"""
from datetime import datetime, timedelta
from airflow import DAG
from airflow.providers.docker.operators.docker import DockerOperator

DEFAULT_ARGS = {
    'owner': 'airflow',
    'depends_on_past': False,
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'trading__ingest__ibkr',
    default_args=DEFAULT_ARGS,
    description='Trading project: Ingest data from Interactive Brokers',
    schedule_interval=None,
    start_date=datetime(2023, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=['trading', 'ibkr']
)

ibkr_task = DockerOperator(
    task_id='ingest_ibkr_trading',
    image='market-analysis:latest',
    api_version='auto',
    auto_remove=True,
    command="python src/main.py --symbol AAPL --provider ibkr --host $IB_HOST --port $IB_PORT --client_id $IB_CLIENT_ID --days 5",
    environment={
        'IB_HOST': '{{ var.value.IB_HOST | default("localhost") }}',
        'IB_PORT': '{{ var.value.IB_PORT | default(7496) }}',
        'IB_CLIENT_ID': '{{ var.value.IB_CLIENT_ID | default(1) }}',
    },
    network_mode='bridge',
    dag=dag,
    pool='market_data',
    execution_timeout=timedelta(minutes=30),
)
