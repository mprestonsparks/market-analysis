"""
Airflow DAG for Analytics Project: Binance Ingestion
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
    'analytics__ingest__binance',
    default_args=DEFAULT_ARGS,
    description='Analytics project: Ingest data from Binance',
    schedule_interval=None,
    start_date=datetime(2023, 1, 1),
    catchup=False,
    max_active_runs=1,
    tags=['analytics', 'binance']
)

binance_task = DockerOperator(
    task_id='ingest_binance_analytics',
    image='market-analysis:latest',
    api_version='auto',
    auto_remove=True,
    command="python src/main.py --symbol BTCUSDT --provider binance --api_key $BINANCE_API_KEY --api_secret $BINANCE_API_SECRET --days 5",
    environment={
        'BINANCE_API_KEY': '{{ var.value.BINANCE_API_KEY }}',
        'BINANCE_API_SECRET': '{{ var.value.BINANCE_API_SECRET }}',
    },
    network_mode='bridge',
    dag=dag,
    pool='market_data',
    execution_timeout=timedelta(minutes=30),
)
