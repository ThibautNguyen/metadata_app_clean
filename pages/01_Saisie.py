import streamlit as st
import pandas as pd
import json
from datetime import datetime
import os

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
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 1rem;
        font-size: 1.1rem;
    }
</style>
""", unsafe_allow_html=True)

# Titre et description
st.title("Saisie des métadonnées")
st.write("Remplissez le formulaire ci-dessous pour ajouter de nouvelles métadonnées.")

# Création des onglets
tab1, tab2, tab3 = st.tabs(["Informations générales", "Structure des données", "Validation"])

with tab1:
    with st.form("metadata_form"):
        # Informations de base
        st.subheader("Informations de base")
        col1, col2 = st.columns(2)
        
        with col1:
            table_name = st.text_input("Nom de la table *", key="table_name", help="Nom unique de la table")
            producer = st.text_input("Producteur *", key="producer", help="Organisation responsable de la donnée")
            category = st.selectbox("Catégorie *", 
                                  ["Économie", "Environnement", "Démographie", "Transport", "Énergie", "Autre"],
                                  key="category")
        
        with col2:
            title = st.text_input("Titre *", key="title", help="Titre descriptif de la donnée")
            last_update = st.date_input("Dernière mise à jour", key="last_update", value=datetime.now())
            frequency = st.selectbox("Fréquence de mise à jour *", 
                                   ["Quotidienne", "Hebdomadaire", "Mensuelle", "Annuelle", "Ponctuelle"],
                                   key="frequency")

        # Description détaillée
        st.subheader("Description")
        description = st.text_area("Description détaillée *", key="description", 
                                 help="Description complète de la donnée, son contexte et son utilisation")

        # Informations supplémentaires
        st.subheader("Informations supplémentaires")
        col3, col4 = st.columns(2)
        
        with col3:
            contact = st.text_input("Contact *", key="contact", help="Personne ou service à contacter")
            source = st.text_input("Source", key="source", help="Source originale des données")
        
        with col4:
            year = st.number_input("Année *", min_value=1900, max_value=datetime.now().year, 
                                 value=datetime.now().year, key="year")
            license = st.selectbox("Licence *", 
                                 ["CC BY", "CC BY-SA", "CC BY-NC", "CC BY-ND", "CC BY-NC-SA", "CC BY-NC-ND"],
                                 key="license")

        # Bouton de soumission
        submitted = st.form_submit_button("Enregistrer les métadonnées")

with tab2:
    st.subheader("Structure des données")
    uploaded_file = st.file_uploader("Télécharger un fichier CSV pour détecter automatiquement les colonnes", 
                                    type=['csv'])
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            st.write("Colonnes détectées :")
            st.dataframe(df.head())
            
            # Formulaire pour les métadonnées des colonnes
            st.subheader("Métadonnées des colonnes")
            for column in df.columns:
                with st.expander(f"Métadonnées pour {column}"):
                    col_type = st.selectbox(f"Type de données pour {column}",
                                          ["Texte", "Nombre", "Date", "Booléen"],
                                          key=f"type_{column}")
                    col_desc = st.text_area(f"Description pour {column}",
                                          key=f"desc_{column}")
                    col_unit = st.text_input(f"Unité pour {column}",
                                           key=f"unit_{column}")
        except Exception as e:
            st.error(f"Erreur lors de la lecture du fichier : {str(e)}")

with tab3:
    st.subheader("Validation des métadonnées")
    if submitted:
        # Validation des champs obligatoires
        required_fields = {
            "table_name": "Nom de la table",
            "producer": "Producteur",
            "title": "Titre",
            "description": "Description",
            "contact": "Contact",
            "year": "Année",
            "license": "Licence"
        }
        
        missing_fields = []
        for field, label in required_fields.items():
            if not st.session_state.get(field):
                missing_fields.append(label)
        
        if missing_fields:
            st.error("Veuillez remplir les champs obligatoires suivants :")
            for field in missing_fields:
                st.write(f"- {field}")
        else:
            # Préparation des métadonnées
            metadata = {
                "table_name": st.session_state.table_name,
                "producer": st.session_state.producer,
                "title": st.session_state.title,
                "description": st.session_state.description,
                "category": st.session_state.category,
                "last_update": st.session_state.last_update.strftime("%Y-%m-%d"),
                "frequency": st.session_state.frequency,
                "contact": st.session_state.contact,
                "source": st.session_state.source,
                "year": st.session_state.year,
                "license": st.session_state.license
            }
            
            # Sauvegarde en JSON
            os.makedirs("metadata", exist_ok=True)
            with open(f"metadata/{st.session_state.table_name}.json", "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=4)
            
            st.success("Métadonnées enregistrées avec succès!")
            st.json(metadata)

# Section d'aide
with st.expander("Aide pour la saisie"):
    st.markdown("""
    ### Champs obligatoires
    - **Nom de la table** : Identifiant unique de la table
    - **Producteur** : Organisation responsable
    - **Titre** : Titre descriptif de la donnée
    - **Description** : Description détaillée
    - **Contact** : Personne ou service à contacter
    - **Année** : Année de référence
    - **Licence** : Type de licence d'utilisation
    
    ### Conseils de saisie
    1. Soyez aussi précis que possible dans la description
    2. Indiquez la source des données si disponible
    3. Mettez à jour la date de dernière modification
    4. Utilisez l'onglet "Structure des données" pour importer un fichier CSV
    """)

# Pied de page
st.markdown("---")
st.markdown("© 2025 - Système de Gestion des Métadonnées") 