import streamlit as st
import os
import sys

# Configuration de la page avec gestion d'erreurs
try:
    st.set_page_config(
        page_title="Gestion des Métadonnées",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="expanded"
    )
except Exception as e:
    st.error(f"Erreur lors de la configuration de la page: {str(e)}")

# Ajout du chemin pour les modules personnalisés (avec gestion d'erreurs)
try:
    # Obtenir le chemin du fichier actuel
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Dans Streamlit Cloud, nous n'avons pas besoin d'ajouter le chemin parent
    # Le code ci-dessous est commenté car il peut causer des problèmes en production
    # parent_dir = os.path.dirname(current_dir)
    # if parent_dir not in sys.path:
    #     sys.path.append(parent_dir)
    
    st.write(f"Chemin actuel: {current_dir}")  # Pour déboguer
except Exception as e:
    st.error(f"Erreur lors de la configuration des chemins: {str(e)}")

# Titre et introduction
st.title("Système de Gestion des Métadonnées")
st.markdown("""
Cette application permet de gérer les métadonnées de vos jeux de données statistiques.
Elle offre les fonctionnalités suivantes :
""")

# Création des cartes pour les fonctionnalités
try:
    col1, col2 = st.columns(2)

    with col1:
        st.info("### 📝 Saisie des métadonnées")
        st.markdown("""
        Créez et modifiez facilement des fiches de métadonnées pour vos données.
        
        Fonctionnalités:
        - Formulaire structuré
        - Validation automatique
        - Enregistrement en JSON et TXT
        """)
        st.page_link("pages/02_Saisie.py", label="Accéder à la saisie", icon="✏️")

    with col2:
        st.info("### 🔍 Recherche")
        st.markdown("""
        Recherchez rapidement parmi les métadonnées existantes.
        
        Fonctionnalités:
        - Recherche par mot-clé
        - Filtrage par catégorie
        - Accès direct aux fiches
        """)
        st.page_link("pages/03_Recherche.py", label="Accéder à la recherche", icon="🔎")
except Exception as e:
    st.error(f"Erreur lors de l'affichage des cartes: {str(e)}")

# Pied de page
st.markdown("---")
st.markdown("© 2025 - Système de Gestion des Métadonnées v1.0")

# Débogage - Afficher les variables d'environnement et le contenu du répertoire
st.markdown("### Informations de débogage")
with st.expander("Afficher les informations de débogage"):
    st.write("Répertoire courant:", os.getcwd())
    st.write("Contenu du répertoire:")
    try:
        files = os.listdir(".")
        st.write(files)
    except Exception as e:
        st.error(f"Erreur lors de la lecture du répertoire: {str(e)}") 