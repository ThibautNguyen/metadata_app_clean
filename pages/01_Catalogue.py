import streamlit as st
import pandas as pd

# Configuration de la page
st.set_page_config(
    page_title="Catalogue des métadonnées",
    page_icon="📚",
    layout="wide"
)

# Titre
st.title("Catalogue des métadonnées")
st.write("Version de test pour le déploiement")

# Section des données de test
st.header("Données de test")

# Création d'un DataFrame de test
data = {
    'Nom': ['Test 1', 'Test 2'],
    'Description': ['Premier test', 'Deuxième test']
}
df = pd.DataFrame(data)

# Affichage du tableau
st.dataframe(
    df,
    column_config={
        "Nom": st.column_config.TextColumn("Nom"),
        "Description": st.column_config.TextColumn("Description"),
    },
    hide_index=True,
) 