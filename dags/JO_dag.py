import os
import pandas as pd
from datetime import datetime
from airflow import DAG
from sqlalchemy import create_engine
from airflow.exceptions import AirflowSkipException
from airflow.operators.python_operator import PythonOperator
from airflow.operators.bash import BashOperator

INPUT_CSV = "/opt/airflow/dags/data/fact_resultats_epreuves.csv"
POSTGRES_CONN = 'postgresql+psycopg2://airflow:airflow@postgres:5432/airflow'

# Fonction de vérification de la présence d'un fichier
def check_new_file():
    folder = "/opt/airflow/dags/data/"
    return any(f.endswith(".csv") for f in os.listdir(folder))

# Fonction d'extraction
def extract_data():
    df = pd.read_csv(INPUT_CSV, sep=',')
    engine = create_engine(POSTGRES_CONN)
    df.to_sql('staging_extract', engine, if_exists='replace', index=False)
    print(f"{len(df)} lignes chargées dans staging_extract")
    return df.to_json()  

def transform_data(**kwargs):
    ti = kwargs['ti']
    data = ti.xcom_pull(task_ids='extract_task')
    df = pd.read_json(data)

    df_transformed = df.drop(
        columns=[
            'id_resultat_source','id_athlete_base_resultats','id_personne','id_equipe',
            'id_pays','id_evenement','evenement_en','id_edition','id_competition_sport',
            'competition_en','id_type_competition','id_ville_edition','edition_ville_en',
            'id_nation_edition_base_resultats','id_sport','sport_en','id_discipline_administrative',
            'id_specialite','id_epreuve','id_federation','federation_nom_court']
    ).drop_duplicates()
    return df_transformed.to_json()

# Fonction de chargement des données en base
def load_data(**kwargs):
    ti = kwargs['ti']
    data = ti.xcom_pull(task_ids='transform_task')
    df = pd.read_json(data)

    engine = create_engine(POSTGRES_CONN)

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
    description             = 'Pipeline ETL & Data Control avec Soda',
    schedule_interval       = '0 * * * *',
    # schedule_interval       = '0 8 * 2,8 *',
    start_date              = datetime(2025, 6, 2),
    catchup                 = False,
    is_paused_upon_creation = False 
)

extract_task    = PythonOperator(task_id='extract_task', python_callable=extract_data, dag=dag)
transform_task = PythonOperator(task_id='transform_task', python_callable=transform_data, provide_context=True, dag=dag)
load_task       = PythonOperator(task_id='load_task', python_callable=load_data, provide_context=True, dag=dag)

# --- Contrôles qualité Soda ---
run_soda_checks_extract = BashOperator(
    task_id='run_soda_checks_extract',
    bash_command='soda scan -d my_data_source -c /opt/airflow/soda/configuration.yaml /opt/airflow/soda/checks_extract.yaml',
    dag=dag
)

run_soda_checks_load = BashOperator(
    task_id='run_soda_checks_load',
    bash_command='soda scan -d my_data_source -c /opt/airflow/soda/configuration.yaml /opt/airflow/soda/checks_load.yaml',
    dag=dag
)

# --- Dépendances ---
extract_task >> run_soda_checks_extract >> transform_task >> load_task >> run_soda_checks_load  