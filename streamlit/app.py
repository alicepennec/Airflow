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
Explorez la table en définissant une limite ou saisissez le nom d'un athlète pour filtrer les résultats.
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

tab1, tab2, tab3 = st.tabs(["📊 Exploration Générale", "🔍 Recherche Athlète", "🛠️ Gestion des données"])
with tab1:
    st.subheader("✍️ SQL Query via API")
    st.markdown("Interrogez la base de données de manière sécurisée via l'API.")

    # Zone de saisie
    default_query = "SELECT * FROM resultats LIMIT 10"
    query_input = st.text_area("Entrez votre requête SQL :", value=default_query, height=150)

    if st.button("🚀 Exécuter la requête"):
        try:
            # Envoi de la requête à l'API
            response = requests.post(
                f"{API_URL}/query", 
                json={"query": query_input}
            )

            if response.status_code == 200:
                results = response.json()["data"]
                
                if results:
                    df_res = pd.DataFrame(results)
                    
                    # Affichage des métriques
                    st.metric("Lignes trouvées", len(df_res))
                    
                    # Affichage du tableau
                    st.dataframe(df_res, use_container_width=True)

                    # Bouton de téléchargement
                    csv = df_res.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        label="📥 Télécharger les résultats (CSV)",
                        data=csv,
                        file_name="export_sql_api.csv",
                        mime="text/csv"
                    )
                else:
                    st.warning("La requête a réussi mais n'a retourné aucun résultat.")
            else:
                # Affichage de l'erreur renvoyée par l'API (ex: erreur de syntaxe SQL)
                error_detail = response.json().get("detail", "Erreur inconnue")
                st.error(f"❌ Erreur SQL : {error_detail}")

        except Exception as e:
            st.error(f"❌ Erreur de connexion à l'API : {e}")
            
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
                
with tab3:
    st.header("Gestion des données")
    st.write("Modifiez directement les valeurs dans le tableau, ajoutez des lignes ou supprimez-en.")

    # 1. On récupère les données actuelles via l'API
    response = requests.get(f"{API_URL}/resultats", params={"limit": 50})
    if response.status_code == 200:
        raw_data = response.json()["data"]
        df_admin = pd.DataFrame(raw_data)

        # 2. L'éditeur de données interactif
        # num_rows="dynamic" permet d'ajouter/supprimer des lignes
        edited_data = st.data_editor(
            df_admin, 
            num_rows="dynamic", 
            use_container_width=True,
            key="admin_editor"
        )

        # 3. Traitement des modifications
        if st.button("💾 Enregistrer les changements dans la base"):
            if not edited_data.equals(df_admin):
                st.warning("🔄 Communication avec l'API en cours...")
                
                # On compare ligne par ligne pour ne mettre à jour que ce qui a changé
                for index, row in edited_data.iterrows():
                    if not row.equals(df_admin.iloc[index]):
                        # Préparation des données pour l'API
                        payload = {
                            "id_resultat": int(row['id_resultat']),
                            "athlete_nom": str(row['athlete_nom']),
                            "athlete_prenom": str(row['athlete_prenom']),
                            "sport": str(row['sport']),
                            "classement_epreuve": float(row['classement_epreuve'])
                        }
                        
                        try:
                            # Appel de l'endpoint PUT
                            res = requests.put(
                                f"{API_URL}/resultats/{int(row['id_resultat'])}",
                                json=payload
                            )
                            
                            if res.status_code == 200:
                                st.toast(f"✅ Mis à jour : {row['athlete_nom']}", icon="✔️")
                            else:
                                st.error(f"❌ Erreur sur l'ID {row['id_resultat']} : {res.json().get('detail')}")
                        except Exception as e:
                            st.error(f"❌ Erreur de connexion : {e}")
                
                st.success("✨ Modifications terminées !")
                st.rerun() # Pour rafraîchir le tableau avec les nouvelles valeurs de la base
            else:
                st.info("ℹ️ Aucun changement détecté dans le tableau.")
    else:
        st.error("Impossible de charger les données pour l'administration.")

# Footer
st.divider()
st.caption("Interface d'exploration de données - Projet Simplon 2026")