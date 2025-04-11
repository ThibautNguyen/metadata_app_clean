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
tab1, tab2 = st.tabs(["Saisie manuelle", "Charger fichier"])

with tab1:
    with st.form("metadata_form"):
        # Informations de base
        st.subheader("Informations de base")
        
        # Première ligne : Nom de la base et Schéma
        col1, col2 = st.columns(2)
        with col1:
            database_name = st.selectbox("Nom de la base *", 
                                       ["opendata"],
                                       help="dans le SGBD Intelligence des Territoires",
                                       key="database_name")
        with col2:
            schema = st.selectbox("Schéma *",
                                ["admin", "economie", "education", "energie", "environnement", 
                                 "logement", "mobilite", "population", "public", "referentiels", 
                                 "sante", "securite", "social"],
                                help="dans le SGBD Intelligence des Territoires",
                                key="schema")
        
        # Deuxième ligne : Nom de la table et Producteur
        col3, col4 = st.columns(2)
        with col3:
            table_name = st.text_input("Nom de la table *", 
                                     help="dans le SGBD Intelligence des Territoires",
                                     key="table_name")
        with col4:
            producer = st.text_input("Producteur de la donnée *",
                                   help="Nom de l'organisme pourvoyeur de la donnée",
                                   key="producer")
        
        # Troisième ligne : Nom du jeu de données et Millésime
        col5, col6 = st.columns(2)
        with col5:
            dataset_name = st.text_input("Nom du jeu de données *",
                                       help="Nom donné par le producteur de données",
                                       key="dataset_name")
        with col6:
            year = st.number_input("Millésime/année *",
                                 min_value=1900,
                                 max_value=datetime.now().year,
                                 value=datetime.now().year,
                                 help="Année de référence des données",
                                 key="year")

        # Description détaillée
        st.subheader("Description")
        description = st.text_area("Description détaillée", key="description", 
                                 help="Description complète de la donnée, son contexte et son utilisation")

        # Informations supplémentaires
        st.subheader("Informations supplémentaires")
        col7, col8 = st.columns(2)
        
        with col7:
            contact = st.text_input("Envoi par", 
                                  help="Personne ayant rempli le formulaire",
                                  key="contact")
            source = st.text_input("Source", 
                                 help="URL de la source originale ou nom du client référent ayant transmis la donnée",
                                 key="source")
        
        with col8:
            last_update = st.date_input("Dernière mise à jour", 
                                      help="date de la dernière mise à jour de la table sur la plateforme de téléchargement",
                                      key="last_update", 
                                      value=datetime.now())
            frequency = st.selectbox("Fréquence de mise à jour *", 
                                   ["Quotidienne", "Hebdomadaire", "Mensuelle", "Annuelle", "Ponctuelle"],
                                   index=3,  # "Annuelle" par défaut
                                   key="frequency")
            license = st.selectbox("Licence", 
                                 ["Licence ouverte / Open License (Etalab)",
                                  "Licence ODbL (Open Database License)",
                                  "Creative Commons (CC)",
                                  "Autre licence de donnée ouverte",
                                  "Licence de données privées"],
                                 key="license")

        # 4 premières lignes du fichier CSV
        st.subheader("4 premières lignes du fichier CSV")
        st.write("Copiez-collez les 4 premières lignes (en-tête compris) de la table au format CSV")
        separator = st.radio("Séparateur", [";", ","], horizontal=True)
        csv_content = st.text_area("Contenu CSV", height=150, 
                                 help="Collez ici les 4 premières lignes de votre fichier CSV")

        # Dictionnaire des variables
        st.subheader("Dictionnaire des variables")
        st.write("Copiez-collez le dictionnaire des variables depuis le fichier CSV correspondant")
        variable_dict = st.text_area("Dictionnaire", height=150,
                                   help="Collez ici le dictionnaire des variables")

        # Bouton de soumission
        submitted = st.form_submit_button("Enregistrer les métadonnées")
        
        if submitted:
            # Validation des champs obligatoires
            required_fields = {
                "database_name": "Nom de la base",
                "schema": "Schéma",
                "table_name": "Nom de la table",
                "producer": "Producteur de la donnée",
                "dataset_name": "Nom du jeu de données",
                "year": "Millésime/année",
                "frequency": "Fréquence de mise à jour"
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
                    "database_name": st.session_state.database_name,
                    "schema": st.session_state.schema,
                    "table_name": st.session_state.table_name,
                    "producer": st.session_state.producer,
                    "dataset_name": st.session_state.dataset_name,
                    "year": st.session_state.year,
                    "description": st.session_state.description,
                    "last_update": st.session_state.last_update.strftime("%Y-%m-%d"),
                    "frequency": st.session_state.frequency,
                    "contact": st.session_state.contact,
                    "source": st.session_state.source,
                    "license": st.session_state.license,
                    "csv_separator": separator,
                    "csv_content": csv_content,
                    "variable_dictionary": variable_dict
                }
                
                # Sauvegarde en JSON
                os.makedirs("metadata", exist_ok=True)
                with open(f"metadata/{st.session_state.table_name}.json", "w", encoding="utf-8") as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=4)
                
                st.success("Métadonnées enregistrées avec succès!")
                st.json(metadata)

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

# Section d'aide
with st.expander("Aide pour la saisie"):
    st.markdown("""
    ### Champs obligatoires
    - **Nom de la base** : Nom de la base de données dans le SGBD Intelligence des Territoires
    - **Schéma** : Schéma de la table dans le SGBD Intelligence des Territoires
    - **Nom de la table** : Nom de la table dans la base de données
    - **Producteur de la donnée** : Nom de l'organisme pourvoyeur de la donnée
    - **Nom du jeu de données** : Nom donné par le producteur de données
    - **Millésime/année** : Année de référence des données
    - **Fréquence de mise à jour** : Fréquence à laquelle les données sont mises à jour
    
    ### Conseils de saisie
    1. **Informations de base**
       - Le nom de la base est actuellement limité à "opendata"
       - Le schéma doit correspondre à l'une des catégories prédéfinies
       - Le nom de la table doit être unique dans la base de données
       - Le producteur de la donnée doit être l'organisme source des données
       - Le nom du jeu de données doit être celui utilisé par le producteur
       - Le millésime doit correspondre à l'année de référence des données
    
    2. **Description**
       - Soyez aussi précis que possible dans la description
       - Incluez le contexte d'utilisation des données
       - Mentionnez les limitations éventuelles
    
    3. **Informations supplémentaires**
       - Indiquez la personne qui remplit le formulaire
       - Précisez la source originale des données (URL ou client référent)
       - Mettez à jour la date de dernière modification
       - Sélectionnez la fréquence de mise à jour appropriée
       - Choisissez la licence qui correspond aux conditions d'utilisation
    
    4. **Données CSV**
       - Copiez-collez les 4 premières lignes du fichier CSV
       - Indiquez le séparateur utilisé (; ou ,)
       - Ajoutez le dictionnaire des variables si disponible
    """)

# Pied de page
st.markdown("---")
st.markdown("© 2025 - Système de Gestion des Métadonnées") 