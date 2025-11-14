import streamlit as st
from sqlalchemy import create_engine
import pandas as pd
import psycopg2
import os

# Connexion SQLAlchemy
DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)


st.title("SQL Playground - Données Sportives")

default_query = "SELECT * FROM table_jo LIMIT 10"
query = st.text_area("Entrez votre requête SQL ici :", value=default_query)

if st.button("Exécuter"):
    try:
        df = pd.read_sql_query(query, engine)
        st.dataframe(df)
        
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📥 Télécharger en CSV",
            data=csv,
            file_name="résultat_requête.csv",
            mime="text/csv"
        )
        
    except Exception as e:
        st.error(f"Erreur : {e}")

