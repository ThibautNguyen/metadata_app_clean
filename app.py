import streamlit as st

# Configuration de la page
st.set_page_config(
    page_title="Système de Gestion des Métadonnées",
    page_icon="📊",
    layout="wide"
)

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

# Titre et description
st.title("Système de Gestion des Métadonnées")
st.write("Bienvenue dans le système de gestion des métadonnées. Utilisez le menu de navigation à gauche pour accéder aux différentes fonctionnalités.")

# Description des pages
st.markdown("""
### Fonctionnalités disponibles

1. **Catalogue des métadonnées** 📚
   - Consultez toutes les métadonnées disponibles
   - Recherchez et filtrez les métadonnées
   - Visualisez les détails des métadonnées

2. **Saisie des métadonnées** ✏️
   - Ajoutez de nouvelles métadonnées
   - Complétez les informations détaillées
   - Validez et enregistrez les métadonnées

### Comment utiliser l'application

1. Pour consulter les métadonnées existantes, accédez à la page "Catalogue"
2. Pour ajouter de nouvelles métadonnées, utilisez la page "Saisie"
3. Utilisez les filtres et la recherche pour trouver rapidement les informations
""")

# Pied de page
st.markdown("---")
st.markdown("© 2025 - Système de Gestion des Métadonnées v1.0")

# Données de test
st.markdown("## Données de test")
data = [
    {"Nom": "Test 1", "Description": "Premier test"},
    {"Nom": "Test 2", "Description": "Deuxième test"}
]

# Afficher les données
st.dataframe(data) 