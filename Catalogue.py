import streamlit as st
import pandas as pd
from db_utils import test_connection

# Configuration de la page
st.set_page_config(
    page_title="Catalogue de Métadonnées",
    page_icon="📚",
    layout="wide"
)

# Titre de la page
st.title("Catalogue de Métadonnées")

# Test de connexion à la base de données
col1, col2, col3 = st.columns([1,2,1])
with col2:
    if st.button("🔌 Tester la connexion à la base de données", use_container_width=True):
        succes, message = test_connection()
        if succes:
            st.success(message)
        else:
            st.error(message)

st.write("Bienvenue dans le catalogue de métadonnées. Utilisez la barre latérale pour naviguer.")

# CSS pour le style de l'interface
st.markdown("""
<style>
    .main h1 {
        color: #1E88E5;
    }
    .stButton button {
        background-color: #1E88E5;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Données de démonstration
demo_metadata = [
    {
        "table_name": "emplois_salaries_2016",
        "producer": "INSEE",
        "title": "Emplois salariés en 2016",
        "description": "Description des emplois salariés en France en 2016 par secteur d'activité.",
        "last_updated": "2023-05-15 14:30:22"
    },
    {
        "table_name": "indicateurs_climat_2022",
        "producer": "Météo France",
        "title": "Indicateurs climatiques 2022",
        "description": "Relevés des principaux indicateurs climatiques en France pour l'année 2022.",
        "last_updated": "2023-01-10 09:15:45"
    },
    {
        "table_name": "emissions_ges_2021",
        "producer": "Citepa (GES)",
        "title": "Émissions de GES 2021",
        "description": "Inventaire des émissions de gaz à effet de serre en France pour l'année 2021.",
        "last_updated": "2022-11-30 16:45:10"
    }
]

# Interface de recherche
st.markdown("## Recherche")
col1, col2 = st.columns([3, 1])

with col1:
    search_text = st.text_input("Rechercher par mot-clé", placeholder="Entrez un terme à rechercher...")

with col2:
    selected_producer = st.selectbox("Filtrer par producteur", ["Tous", "INSEE", "Météo France", "Citepa (GES)"])

# Afficher le nombre total de métadonnées
st.info(f"Nombre total de métadonnées disponibles : {len(demo_metadata)}")

# Affichage des résultats
st.markdown("## Résultats")

# Tableau des résultats
results_df = pd.DataFrame([
    {
        "Nom": meta.get("table_name", ""),
        "Producteur": meta.get("producer", ""),
        "Titre": meta.get("title", ""),
        "Dernière mise à jour": meta.get("last_updated", "")
    }
    for meta in demo_metadata
])

# Afficher le tableau
st.dataframe(results_df, use_container_width=True)

# Section d'aide et informations
with st.expander("Aide et informations"):
    st.markdown("""
    ### Comment utiliser ce catalogue
    
    - **Recherche par mot-clé** : Saisissez un terme dans le champ de recherche pour filtrer les métadonnées.
    - **Filtre par producteur** : Utilisez le menu déroulant pour filtrer par organisation productrice de données.
    - **Consulter les détails** : Cliquez sur une ligne dans le tableau pour voir les détails.
    
    ### Structure des métadonnées
    
    Les métadonnées sont structurées avec les informations suivantes :
    - **Nom** : Identifiant unique de la table de données
    - **Producteur** : Organisation qui a produit les données
    - **Description** : Explication détaillée des données
    - **Colonnes** : Structure des champs de la table avec types et descriptions
    - **Informations supplémentaires** : Contacts, années, sources, etc.
    """)

# Pied de page
st.markdown("---")
st.markdown("© 2025 - Système de Gestion des Métadonnées v1.0") 