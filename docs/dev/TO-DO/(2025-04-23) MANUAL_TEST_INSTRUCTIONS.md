# Manual Testing Instructions: Airflow & Market Analysis

## 1. Add Secrets & Credentials
Before running Airflow DAGs or CLI with IBKR/Binance, you must add the required secrets and credentials.

### Binance API Credentials
1. Open https://www.binance.com/en/my/settings/api-management in your browser.
2. Log in to your Binance account.
3. Under "API Management", click "Create API", enter a label (e.g., `market_analysis_test`), and click "Create".
4. Complete 2FA (email and phone) to generate the API Key and Secret.
5. Copy the generated `API Key` and `API Secret` values into your `.env` file as `BINANCE_API_KEY` and `BINANCE_API_SECRET`.
6. To view or reset your secret, click "Edit restrictions" next to your API key and select "View Secret Key".

- Copy `.env.example` to `.env` and fill in:
  - `IBKR_HOST`, `IBKR_PORT`, `IBKR_CLIENT_ID`
  - `BINANCE_API_KEY`, `BINANCE_API_SECRET`
- For Airflow, add connections via the Airflow UI or CLI:
  - IBKR: `market_analysis_ibkr` (host, port, client_id in extras as JSON)
  - Binance: `market_analysis_binance` (api_key, api_secret in extras)

## 2. Build and Start Airflow
- Ensure Docker is running.
- Build the Airflow image (already done):
  ```sh
  docker build -f docker/Dockerfile.airflow -t market-analysis:latest .
  ```
- Start Airflow (adjust compose file/path as needed):
  ```sh
  docker-compose up airflow-webserver airflow-scheduler airflow-worker
  ```
- Access Airflow UI at: http://localhost:8080

## 3. Trigger the DAG
- In the Airflow UI, find the `market_analysis_ingestion` DAG.
- Trigger a DAG run manually.
- Inspect logs for the `ingest_market_data` task. It should run the CLI and attempt to fetch data using your credentials.

## 4. Manual CLI Test
- From the repo root, test the CLI for each provider:
  ```sh
  # YFinance (no secrets required)
  python -m src.main --symbol AAPL --days 5 --provider yf

  # IBKR (requires TWS/Gateway & credentials)
  python -m src.main --symbol AAPL --days 5 --provider ibkr --host <host> --port <port> --client_id <id>

  # Binance
  python -m src.main --symbol BTCUSDT --days 5 --provider binance --api_key <key> --api_secret <secret>
  ```
- Verify output and logs for successful data fetch and analysis.

## 5. Troubleshooting
- If you see credential or connection errors, double-check your `.env` and Airflow connection settings.
- If the DAG fails, inspect the Airflow task logs for Python or provider errors.

---

**Once you have completed these steps, let me know if you encounter any issues or if everything works as expected!**
