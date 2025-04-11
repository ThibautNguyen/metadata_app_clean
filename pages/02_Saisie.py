import streamlit as st
from datetime import datetime

# Configuration de la page
st.set_page_config(
    page_title="Saisie des métadonnées",
    page_icon="✏️",
    layout="wide"
)

# CSS pour le style du formulaire
st.markdown("""
<style>
    .stTextInput > label {
        font-weight: bold;
    }
    .required::after {
        content: " *";
        color: red;
    }
</style>
""", unsafe_allow_html=True)

# Titre et description
st.title("Saisie des métadonnées")
st.write("Remplissez le formulaire ci-dessous pour ajouter de nouvelles métadonnées.")

# Formulaire de saisie
with st.form("metadata_form"):
    # Informations de base
    st.subheader("Informations de base")
    col1, col2 = st.columns(2)
    
    with col1:
        table_name = st.text_input("Nom de la table", key="table_name", help="Nom unique de la table")
        producer = st.text_input("Producteur", key="producer", help="Organisation responsable de la donnée")
    
    with col2:
        title = st.text_input("Titre", key="title", help="Titre descriptif de la donnée")
        last_update = st.date_input("Dernière mise à jour", key="last_update", value=datetime.now())

    # Description détaillée
    st.subheader("Description")
    description = st.text_area("Description détaillée", key="description", 
                             help="Description complète de la donnée, son contexte et son utilisation")

    # Informations supplémentaires
    st.subheader("Informations supplémentaires")
    col3, col4 = st.columns(2)
    
    with col3:
        contact = st.text_input("Contact", key="contact", help="Personne ou service à contacter")
        source = st.text_input("Source", key="source", help="Source originale des données")
    
    with col4:
        year = st.number_input("Année", min_value=1900, max_value=datetime.now().year, 
                             value=datetime.now().year, key="year")
        frequency = st.selectbox("Fréquence de mise à jour", 
                               ["Quotidienne", "Hebdomadaire", "Mensuelle", "Annuelle", "Ponctuelle"],
                               key="frequency")

    # Bouton de soumission
    submitted = st.form_submit_button("Enregistrer les métadonnées")
    
    if submitted:
        if not table_name or not title or not description:
            st.error("Veuillez remplir tous les champs obligatoires.")
        else:
            st.success("Métadonnées enregistrées avec succès!")

# Section d'aide
with st.expander("Aide pour la saisie"):
    st.markdown("""
    ### Champs obligatoires
    - **Nom de la table** : Identifiant unique de la table
    - **Titre** : Titre descriptif de la donnée
    - **Description** : Description détaillée de la donnée
    
    ### Conseils de saisie
    1. Soyez aussi précis que possible dans la description
    2. Indiquez la source des données si disponible
    3. Mettez à jour la date de dernière modification
    """)

# Pied de page
st.markdown("---")
st.markdown("© 2025 - Système de Gestion des Métadonnées") 