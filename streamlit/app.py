import streamlit as st
import requests
import pandas as pd
import os

# 1. Configuration de la page
st.set_page_config(
    page_title="Streamlit - JO",
    layout="wide"
)

# 2. Récupération de l'URL de la base (via variable d'environnement)
API_URL = os.getenv("API_URL", "http://api:8000")

# 3. Initialisation de l'Engine SQLAlchemy avec mise en cache
#@st.cache_resource
#def get_engine():
#    if not DATABASE_URL:
#        st.error("DATABASE_URL n'est pas définie dans les variables d'environnement.")
#        return None
#    return create_engine(DATABASE_URL)

#engine = get_engine()

# --- INTERFACE UTILISATEUR ---

st.title("Historique des données des JO")
st.markdown("""
Cette interface vous permet d'interroger la base de données **jo_data** via une API. 
Saisissez votre requête SQL ci-dessous et visualisez les résultats en temps réel.
""")

# Barre latérale (Sidebar)
with st.sidebar:
    st.header("📋 Options API")
    st.info(f"Connecté à : `{API_URL}`")
    
    if st.button("🔌 Tester la connexion API"):
        try:
            response = requests.get(f"{API_URL}/")
            if response.status_code == 200:
                st.success(f"Réponse API : {response.json()['message']}")
        except Exception as e:
            st.error(f"Impossible de joindre l'API : {e}")

# --- FONCTIONNALITÉS ---

tab1, tab2 = st.tabs(["📊 Exploration Générale", "🔍 Recherche Athlète"])

with tab1:
    limit = st.slider("Nombre de résultats à récupérer", 1, 100, 10)
    if st.button("🚀 Récupérer les données"):
        try:
            # Appel au endpoint de l'API
            response = requests.get(f"{API_URL}/resultats", params={"limit": limit})
            
            if response.status_code == 200:
                result_json = response.json()
                df = pd.DataFrame(result_json["data"])
                
                st.metric("Lignes récupérées", result_json["count"])
                st.dataframe(df, use_container_width=True)
                
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button("📥 Télécharger CSV", csv, "export_api.csv", "text/csv")
            else:
                st.error(f"Erreur API : {response.status_code}")
        except Exception as e:
            st.error(f"Erreur de connexion : {e}")

with tab2:
    nom_athlete = st.text_input("Nom de l'athlète (ex: Bolt)")
    if st.button("🔍 Rechercher"):
        if nom_athlete:
            try:
                response = requests.get(f"{API_URL}/resultats/athlete/{nom_athlete}")
                if response.status_code == 200:
                    data = response.json()["data"]
                    if data:
                        df = pd.DataFrame(data)
                        st.dataframe(df, use_container_width=True)
                    else:
                        st.warning("Aucun athlète trouvé avec ce nom.")
            except Exception as e:
                st.error(f"Erreur : {e}")

# Footer
st.divider()
st.caption("Interface d'exploration de données - Projet Simplon 2026")