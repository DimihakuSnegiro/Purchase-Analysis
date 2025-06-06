from airflow import DAG
from airflow.operators.bash import BashOperator
from datetime import datetime

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2025, 6, 1),
    'retries': 0,
}

with DAG(
    dag_id='run_batch',
    default_args=default_args,
    schedule_interval='@daily',
    catchup=False,
    description='batch',
) as dag:

    postgres_batch = BashOperator(
        task_id='run_postgres_batch',
        bash_command=(
            'docker exec spark-batch spark-submit '
            '--jars /opt/spark-apps/jars/postgresql-42.6.0.jar,'
            '/opt/spark-apps/jars/clickhouse-jdbc-0.4.6.jar '
            '/opt/spark-apps/postgres_batch.py'
        )
    )

    iceberg_batch = BashOperator(
        task_id='run_iceberg_batch',
        bash_command=(
            'docker exec spark-batch spark-submit '
            '--jars /opt/spark-apps/jars/iceberg-spark-runtime-3.5_2.12.jar,'
            '/opt/spark-apps/jars/clickhouse-jdbc-0.4.6.jar '
            '/opt/spark-apps/iceberg_batch.py'
        )
    )
    
    postgres_batch >> iceberg_batch