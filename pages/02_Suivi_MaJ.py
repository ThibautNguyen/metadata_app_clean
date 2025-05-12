import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
from db_utils import get_db_connection

st.set_page_config(
    page_title="Suivi des mises à jour",
    page_icon="📊",
    layout="wide"
)

st.title("Suivi des mises à jour des données")

# Initialisation de la connexion à la base de données
@st.cache_resource
def init_db():
    return get_db_connection()

# Fonction pour récupérer les données de suivi
@st.cache_data(ttl=3600)  # Cache pour 1 heure
def get_update_data():
    conn = init_db()
    query = """
    SELECT 
        nom_jeu_donnees,
        producteur,
        date_publication,
        date_maj,
        date_prochaine_publication,
        frequence_maj
    FROM metadata
    ORDER BY date_prochaine_publication DESC
    """
    return pd.read_sql(query, conn)

# Interface principale
try:
    # Récupération des données
    df = get_update_data()
    
    # Filtres
    col1, col2 = st.columns(2)
    with col1:
        producteurs = ["Tous"] + sorted(df['producteur'].unique().tolist())
        selected_producteur = st.selectbox(
            "Filtrer par producteur",
            producteurs
        )
    
    with col2:
        status_options = ["Tous", "À mettre à jour", "À jour", "En retard"]
        selected_status = st.selectbox(
            "Filtrer par statut",
            status_options
        )
    
    # Application des filtres
    if selected_producteur != "Tous":
        df = df[df['producteur'] == selected_producteur]
    
    # Affichage des données
    st.subheader("Tableau de suivi")
    st.dataframe(
        df,
        use_container_width=True,
        hide_index=True
    )
    
    # Graphique de suivi
    st.subheader("Vue d'ensemble des mises à jour")
    fig = px.timeline(
        df,
        x_start="date_publication",
        x_end="date_prochaine_publication",
        y="nom_jeu_donnees",
        color="producteur",
        title="Planning des mises à jour"
    )
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"Une erreur est survenue : {str(e)}")
    st.info("Veuillez vérifier la connexion à la base de données et réessayer.") 