from airflow import DAG
from airflow.operators.empty import EmptyOperator
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

default_args = {
    'owner': 'apennec',
    "depends_on_past": False,
    "start_date": datetime(2025,6,2),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5)
}

dag = DAG(
    "premier_dag_test",
    default_args=default_args,
    schedule_interval = '0 * * * *',
    description="Un simple dag de test"
    )

def print_hello():
    return 'Hello world, c\'est mon premier dag'

start = EmptyOperator(
    task_id = 'start',
    dag=dag
)

hello_world = PythonOperator(
    task_id = 'hello_world',
    python_callable=print_hello,
    dag=dag
)

end = EmptyOperator(
    task_id = 'end',
    dag=dag
)

start >> hello_world >> end