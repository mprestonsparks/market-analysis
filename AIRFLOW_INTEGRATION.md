# Airflow Integration for Market Analysis

This document summarizes how to integrate the market-analysis project with the Airflow monorepo.

## Docker Image
- Name: `market-analysis:latest`
- Built from: `docker/Dockerfile.airflow`

## Entry Point
- Module: `src.main:main`
- Example command: 
  ```bash
  python -m src.main --symbol AAPL --days 1
  ```

## Required Airflow Connections
- `market_analysis_ibkr` (Interactive Brokers)
  - Stored credentials for IBKR (host, port, client_id)
- `market_analysis_binance` (Binance)
  - Stored API key and secret for Binance data feed

## DAG Location
- File in Airflow Hub: `dags/market-analysis/dag_market_analysis_ingestion.py`

## Environment Variables (optional)
- `IBKR_HOST`, `IBKR_PORT`, `IBKR_CLIENT_ID` (overrides connection if set)
- `BINANCE_API_KEY`, `BINANCE_API_SECRET`

## Usage
1. Build image from this repo:
   ```bash
   cd market-analysis
   docker build -f docker/Dockerfile.airflow -t market-analysis:latest .
   ```

2. In Airflow Hub DAG, run via `DockerOperator`:
   ```python
   DockerOperator(
       task_id='ingest_market_data',
       image='market-analysis:latest',
       command=[
           'python', '-m', 'src.main',
           '--symbol', '{{ params.symbol }}',
           '--start', '{{ ds }}'
       ],
       params={'symbol': 'AAPL'},
       environment={'CONN_ID': 'market_analysis_ibkr'},
       dag=dag
   )
   ```