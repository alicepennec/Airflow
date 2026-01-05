import streamlit as st
from sqlalchemy import create_engine, text
import pandas as pd
import os

# 1. Configuration de la page
st.set_page_config(
    page_title="Streamlit - JO",
    layout="wide"
)

# 2. Récupération de l'URL de la base (via variable d'environnement)
DATABASE_URL = os.getenv("DATABASE_URL")

# 3. Initialisation de l'Engine SQLAlchemy avec mise en cache
@st.cache_resource
def get_engine():
    if not DATABASE_URL:
        st.error("DATABASE_URL n'est pas définie dans les variables d'environnement.")
        return None
    return create_engine(DATABASE_URL)

engine = get_engine()

# --- INTERFACE UTILISATEUR ---

st.title("Historique des données des JO")
st.markdown("""
Cette interface vous permet d'interroger directement la base de données **jo_data**. 
Saisissez votre requête SQL ci-dessous et visualisez les résultats en temps réel.
""")

# Barre latérale (Sidebar) pour l'aide
with st.sidebar:
    #st.header("📋 Aide-mémoire")
    st.info("Table disponible : **resultats**")
    if st.button("Voir la structure de la table"):
        try:
            query = text("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'resultats'")
            with engine.connect() as conn:
                # On exécute la requête et on transforme le résultat en DataFrame
                result = conn.execute(query)
                structure = pd.DataFrame(result.fetchall(), columns=result.keys())
                st.dataframe(structure)
        except Exception as e:
            st.error(f"Erreur structure : {e}")
            
# Zone de saisie de la requête
default_query = "SELECT * FROM resultats LIMIT 10"
query = st.text_area("✍️ Entrez votre requête SQL :", value=default_query, height=150)

# Bouton d'exécution
if st.button("🚀 Exécuter"):
    try:
        query_to_run = text(query)
        
        with engine.connect() as conn:
            # MÉTHODE MANUELLE : On exécute d'abord, on crée le DataFrame ensuite
            result = conn.execute(query_to_run)
            
            # Récupération des données et des noms de colonnes
            data = result.fetchall()
            columns = result.keys()
            
            df = pd.DataFrame(data, columns=columns)
        
        if df.empty:
            st.warning("Aucun résultat trouvé.")
        else:
            st.metric("Lignes trouvées", len(df))
            st.dataframe(df, use_container_width=True)
            
            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Télécharger CSV", csv, "export.csv", "text/csv")
            
    except Exception as e:
        st.error(f"❌ Erreur SQL : {e}")

# Footer
st.divider()
st.caption("Interface d'exploration de données - Projet Simplon 2026")