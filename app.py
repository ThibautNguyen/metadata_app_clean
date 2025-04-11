import streamlit as st

# Configuration de la page
st.set_page_config(
    page_title="Catalogue des métadonnées",
    page_icon="📊",
    layout="wide"
)

# Titre et description
st.title("Catalogue des métadonnées")
st.write("Version de test pour le déploiement")

# Données de test
st.markdown("## Données de test")
data = [
    {"Nom": "Test 1", "Description": "Premier test"},
    {"Nom": "Test 2", "Description": "Deuxième test"}
]

# Afficher les données
st.dataframe(data) 