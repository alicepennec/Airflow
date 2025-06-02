import os
import pandas as pd
from datetime import datetime
from airflow import DAG
from sqlalchemy import create_engine
from airflow.exceptions import AirflowSkipException
from airflow.operators.python_operator import PythonOperator


# Définition des chemins des fichiers
INPUT_CSV = "/opt/airflow/dags/data/fact_resultats_epreuves.csv"

# Fonction de vérification de la présence d'un fichier
def check_new_file():
    folder = "/opt/airflow/dags/data/"
    return any(f.endswith(".csv") for f in os.listdir(folder))

# Fonction d'extraction
def extract_data():
    df = pd.read_csv(INPUT_CSV, sep=',')
    print(f"Données extraites : {df.shape[0]} lignes")
    return df.to_json()  

# Fonction de chargement des données en base
def load_data(**kwargs):
    ti = kwargs['ti']
    data = ti.xcom_pull(task_ids='extract_task')
    df = pd.read_json(data)

    engine = create_engine('postgresql+psycopg2://airflow:airflow@postgres:5432/airflow')

    with engine.connect() as conn:
        # Charger les ID déjà en base
        try:
            existing_ids = pd.read_sql("SELECT id_resultat FROM table_jo", conn)
            # Filtrer les nouvelles lignes
            df_new = df[~df['id_resultat'].isin(existing_ids['id_resultat'])]
            
        except Exception as e:
            df_new = df.copy()
        
        if df_new.empty:
            print("Aucune nouvelle ligne à insérer.")
        else:
            df_new.to_sql('table_jo', conn, if_exists='append', index=False)
            print(f"{len(df_new)} nouvelles lignes insérées.")

# Définition du DAG
dag = DAG(
    'etl_pipeline_JO',
    description             = 'Pipeline ETL pour extraire et charger des données CSV dans une base de données PostgreSQL',
    schedule_interval       = '0 * * * *',
    # schedule_interval       = '0 8 * 2,8 *',
    start_date              = datetime(2025, 6, 2),
    catchup                 = False,
    is_paused_upon_creation = False 
)

# # Skip si année impaire 
# def skip_if_not_even_year(**kwargs):
#     year = kwargs['execution_date'].year
#     if year % 2 != 0:
#         raise AirflowSkipException(f"Année {year} impaire.")
#     print(f"Année paire détectée : {year}.")

# check_year      = PythonOperator(task_id='check_even_year', python_callable=skip_if_not_even_year, provide_context=True, dag=dag)
extract_task    = PythonOperator(task_id='extract_task', python_callable=extract_data, dag=dag)
load_task       = PythonOperator(task_id='load_task', python_callable=load_data, provide_context=True, dag=dag)

# Définition de l'ordre des tâches
# check_year >> extract_task >> load_task
extract_task >> load_task