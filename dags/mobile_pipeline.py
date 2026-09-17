from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_DIR = "/opt/airflow/project"

default_args = {
    "owner": "admin",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="mobile_price_tracker",
    start_date=datetime(2026, 1, 1),
    schedule="0 6 * * *",
    catchup=False,
    default_args=default_args,
    max_active_runs=1,
    tags=["etl", "mobile", "nepal"],
) as dag:

    extract = BashOperator(
        task_id="extract",
        bash_command=f"cd {PROJECT_DIR} && python scripts/extract.py",
    )

    transform = BashOperator(
        task_id="transform",
        bash_command=f"cd {PROJECT_DIR} && python scripts/transform.py",
    )

    load = BashOperator(
        task_id="load",
        bash_command=f"cd {PROJECT_DIR} && python scripts/load.py",
    )

    snapshot = BashOperator(
        task_id="snapshot",
        bash_command=f"cd {PROJECT_DIR} && python scripts/snapshot.py",
    )

    report = BashOperator(
        task_id="report",
        bash_command=f"cd {PROJECT_DIR} && python scripts/report.py",
    )

    extract >> transform >> load >> snapshot >> report