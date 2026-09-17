"""
Mobile Price Tracker — daily ETL pipeline.
extract → transform → load → snapshot → report
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT = "/opt/airflow/project"

default_args = {
    "owner": "admin",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,
}

with DAG(
    dag_id="mobile_price_tracker",
    description="Daily Nepal mobile price ETL + history + report",
    schedule="0 6 * * *",
    start_date=datetime(2026, 1, 1),
    catchup=False,
    max_active_runs=1,
    default_args=default_args,
    tags=["etl", "nepal", "mobile"],
) as dag:

    extract = BashOperator(
        task_id="extract",
        bash_command=f"cd {PROJECT} && python scripts/extract.py",
    )

    transform = BashOperator(
        task_id="transform",
        bash_command=f"cd {PROJECT} && python scripts/transform.py",
    )

    load = BashOperator(
        task_id="load",
        bash_command=f"cd {PROJECT} && python scripts/load.py",
    )

    snapshot = BashOperator(
        task_id="snapshot",
        bash_command=f"cd {PROJECT} && python scripts/snapshot.py",
    )

    report = BashOperator(
        task_id="report",
        bash_command=f"cd {PROJECT} && python scripts/report.py",
    )

    extract >> transform >> load >> snapshot >> report