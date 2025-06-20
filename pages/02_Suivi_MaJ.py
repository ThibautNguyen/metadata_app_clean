import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import plotly.express as px
from utils.db_utils import get_db_connection
from utils.auth import authenticate_and_logout

st.set_page_config(
    page_title="Suivi des mises à jour",
    page_icon="📊",
    layout="wide"
)

# Authentification centralisée (présente sur toutes les pages)
name, authentication_status, username, authenticator = authenticate_and_logout()

st.title("Suivi des mises à jour des données")

# Fonction pour récupérer les données de suivi
@st.cache_data(ttl=3600)  # Cache pour 1 heure
def get_update_data():
    try:
        conn = get_db_connection()
        query = '''
        SELECT DISTINCT ON (nom_jeu_donnees)
            nom_jeu_donnees,
            producteur,
            date_publication,
            millesime,
            date_prochaine_publication,
            frequence_maj
        FROM metadata
        ORDER BY nom_jeu_donnees, date_publication DESC, millesime DESC, id DESC
        '''
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Erreur lors de la récupération des données : {e}")
        return pd.DataFrame()

def compute_status(row):
    freq = str(row.get('frequence_maj', '') or '').strip().lower()
    if freq == "ponctuelle" or freq == "" or pd.isnull(freq):
        return "MaJ non prévue"
    
    if pd.isnull(row['date_prochaine_publication']):
        return "Inconnu"
    
    dpp = row['date_prochaine_publication']
    date_publication = row['date_publication']
    today = date.today()
    
    if not pd.isnull(date_publication) and date_publication >= dpp:
        return "À jour"
    
    if dpp < today:
        return "En retard"
    elif (dpp - today).days < 7:
        return "À mettre à jour"
    else:
        return "À jour"

def get_status_color(status):
    return {
        "En retard": "#ff4b4b",
        "À mettre à jour": "#ffa500",
        "À jour": "#4caf50",
        "MaJ non prévue": "#2196f3",
        "Inconnu": "#bdbdbd"
    }.get(status, "#bdbdbd")

# --- MAIN LOGIC ---
try:
    df = get_update_data()
    if df.empty:
        st.info("Aucune donnée à afficher (base vide ou erreur de connexion).")
    else:
        # Conversion des dates
        for col in ["date_publication", "date_prochaine_publication"]:
            df[col] = pd.to_datetime(df[col]).dt.date
        
        # Calcul du statut
        df['statut'] = df.apply(compute_status, axis=1)
        
        # Réorganisation des colonnes pour le tableau principal
        df_display = df.rename(columns={
            'nom_jeu_donnees': 'Jeu de données',
            'producteur': 'Producteur',
            'date_publication': 'Dernière publication',
            'millesime': 'Millésime',
            'date_prochaine_publication': 'Prochaine publication',
            'frequence_maj': 'Fréquence',
            'statut': 'Statut'
        })

        # Affichage du tableau avec st.dataframe pour permettre la sélection
        st.subheader("Tableau de suivi")
        
        # Création d'un conteneur pour le tableau
        table_container = st.container()
        
        # Création d'un conteneur pour les détails
        details_container = st.container()
        
        with table_container:
            st.dataframe(
                df_display,
                on_select="rerun",
                selection_mode="single-row",
                key="selection_suivi",
                hide_index=True,
                column_order=["Jeu de données", "Producteur", "Dernière publication", 
                             "Millésime", "Prochaine publication", 
                             "Fréquence", "Statut"],
                use_container_width=True
            )

        # Gestion de la sélection et affichage des détails
        selection = st.session_state.get("selection_suivi", {"rows": []})

        if selection.get("rows"):
            with details_container:
                selected_index = selection["rows"][0]
                selected_row = df_display.iloc[selected_index]
                st.markdown("---")
                st.markdown(f"### Détail du jeu de données : {selected_row['Jeu de données']}")
                
                # Création de deux colonnes pour l'affichage des détails
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Producteur :** {selected_row['Producteur']}")
                    st.write(f"**Date de dernière publication :** {selected_row['Dernière publication']}")
                    st.write(f"**Année du dernier millésime :** {selected_row['Millésime']}")
                with col2:
                    st.write(f"**Prochaine publication :** {selected_row['Prochaine publication']}")
                    st.write(f"**Fréquence :** {selected_row['Fréquence']}")
                    status_color = get_status_color(selected_row['Statut'])
                    st.markdown(f"**Statut :** <span style='color:{status_color};font-weight:bold;'>{selected_row['Statut']}</span>", unsafe_allow_html=True)
        else:
            with details_container:
                st.info("Cliquez sur une ligne du tableau pour afficher les détails.")

        # Graphique de suivi avec trait vertical rouge pour la date actuelle
        st.subheader("Vue d'ensemble des mises à jour")
        if not df.empty:
            fig = px.timeline(
                df,
                x_start="date_publication",
                x_end="date_prochaine_publication",
                y="nom_jeu_donnees",
                color="statut",
                title="Planning des mises à jour"
            )
            # Ajout du trait vertical rouge pour la date actuelle
            fig.add_vline(x=datetime.now(), line_width=2, line_color="red")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune donnée à afficher pour les filtres sélectionnés.")

except Exception as e:
    st.error(f"Une erreur est survenue : {str(e)}")
    st.info("Veuillez vérifier la connexion à la base de données et réessayer.") 