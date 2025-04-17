import streamlit as st
from datetime import datetime

# Configuration de la page
st.set_page_config(
    page_title="Saisie des métadonnées",
    page_icon="✏️",
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
st.title("Saisie des métadonnées")
st.write("Utilisez ce formulaire pour ajouter de nouvelles métadonnées au catalogue.")

# Formulaire de saisie
with st.form("saisie_metadata"):
    # Informations de base
    st.markdown("### Informations de base")
    col1, col2 = st.columns(2)
    
    with col1:
        table_name = st.text_input("Nom de la table*", placeholder="Ex: emplois_salaries_2023")
        producer = st.text_input("Producteur*", placeholder="Ex: INSEE")
    
    with col2:
        title = st.text_input("Titre*", placeholder="Ex: Emplois salariés en 2023")
        last_updated = st.date_input("Date de dernière mise à jour*", value=datetime.now())
    
    # Description détaillée
    st.markdown("### Description")
    description = st.text_area("Description détaillée*", 
                             placeholder="Décrivez le contenu et l'objectif de ces données...",
                             height=150)
    
    # Informations supplémentaires
    st.markdown("### Informations supplémentaires")
    col3, col4 = st.columns(2)
    
    with col3:
        contact = st.text_input("Contact", placeholder="Email ou téléphone")
        source = st.text_input("Source", placeholder="URL ou référence")
    
    with col4:
        year = st.number_input("Année", min_value=2000, max_value=datetime.now().year, value=datetime.now().year)
        frequency = st.selectbox("Fréquence de mise à jour", 
                               ["Ponctuelle", "Annuelle", "Trimestrielle", "Mensuelle", "Hebdomadaire", "Quotidienne"])
    
    # Bouton de soumission
    submitted = st.form_submit_button("Enregistrer les métadonnées")
    
    if submitted:
        # Validation des champs obligatoires
        if not all([table_name, producer, title, description]):
            st.error("Veuillez remplir tous les champs obligatoires (marqués d'un *)")
        else:
            # TODO: Ajouter la logique d'enregistrement
            st.success("Les métadonnées ont été enregistrées avec succès !")

# Section d'aide
with st.expander("Aide à la saisie"):
    st.markdown("""
    ### Champs obligatoires
    
    Les champs marqués d'un astérisque (*) sont obligatoires :
    - **Nom de la table** : Identifiant unique de la table de données
    - **Producteur** : Organisation qui a produit les données
    - **Titre** : Titre descriptif des données
    - **Description** : Explication détaillée du contenu
    
    ### Conseils de saisie
    
    - Utilisez des noms de table courts et sans espaces
    - Soyez précis dans la description
    - Indiquez toutes les informations disponibles
    """)

# Pied de page
st.markdown("---")
st.markdown("© 2025 - Système de Gestion des Métadonnées v1.0") 