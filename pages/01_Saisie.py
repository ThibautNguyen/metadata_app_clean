import streamlit as st
import pandas as pd
import json
from datetime import datetime
import os
from pathlib import Path
import sys
from pathlib import Path

# Ajout du répertoire parent au PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent))
from db_utils import init_db, save_metadata

# Configuration de la page
st.set_page_config(
    page_title="Saisie des Métadonnées",
    page_icon="📝",
    layout="wide"
)

# Initialisation de la base de données
init_db()

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
        st.subheader("Informations de base")
        
        # Champs de base
        nom_fichier = st.text_input("Nom du fichier")
        nom_base = st.selectbox(
            "Nom de la base",
            ["INSEE", "Météo France", "Citepa (GES)"],
            help="Organisation productrice des données"
        )
        schema = st.selectbox(
            "Schéma",
            ["Economie", "Démographie", "Environnement", "Social", "Autre"],
            help="Catégorie principale des données"
        )
        description = st.text_area("Description", help="Description détaillée des données")
        
        # Dates
        col1, col2 = st.columns(2)
        with col1:
            date_creation = st.date_input("Date de création", help="Date de création initiale des données")
        with col2:
            date_maj = st.date_input("Dernière mise à jour", help="Date de la dernière mise à jour des données")
        
        # Informations supplémentaires
        st.subheader("Informations supplémentaires")
        
        col1, col2 = st.columns(2)
        with col1:
            source = st.text_input("Source", help="Source originale des données")
            frequence_maj = st.selectbox(
                "Fréquence de mise à jour",
                ["Annuelle", "Semestrielle", "Trimestrielle", "Mensuelle", "Quotidienne", "Ponctuelle"],
                help="Fréquence de mise à jour des données"
            )
            licence = st.selectbox(
                "Licence",
                ["Licence Ouverte", "ODC-BY", "CC-BY-SA", "Autre"],
                help="Licence d'utilisation des données"
            )
        
        with col2:
            envoi_par = st.text_input("Envoi par", help="Personne ayant rempli le formulaire")
            contact = st.text_input("Contact", help="Personne à contacter pour plus d'informations")
            mots_cles = st.text_input("Mots-clés", help="Mots-clés séparés par des virgules")
        
        notes = st.text_area("Notes", help="Informations complémentaires")
        
        # Contenu CSV
        st.subheader("Contenu CSV")
        with st.expander("Contenu CSV", expanded=False):
            st.info("""
            Collez ici le contenu CSV de votre fichier. 
            Format attendu : COD_VAR;LIB_VAR;LIB_VAR_LONG;COD_MOD;LIB_MOD;TYPE_VAR;LONG_VAR
            """)
            contenu_csv = st.text_area(
                "Contenu CSV",
                height=300,
                help="Collez le contenu CSV ici. Utilisez le point-virgule (;) comme séparateur."
            )
            
            if contenu_csv:
                try:
                    # Vérification du format
                    lines = contenu_csv.strip().split('\n')
                    header = lines[0].split(';')
                    expected_header = ['COD_VAR', 'LIB_VAR', 'LIB_VAR_LONG', 'COD_MOD', 'LIB_MOD', 'TYPE_VAR', 'LONG_VAR']
                    
                    if header != expected_header:
                        st.error("Format d'en-tête incorrect. Vérifiez que les colonnes sont dans le bon ordre.")
                    else:
                        # Affichage d'un aperçu
                        st.write("Aperçu des données (5 premières lignes) :")
                        preview_data = []
                        for line in lines[1:6]:  # Afficher les 5 premières lignes de données
                            preview_data.append(line.split(';'))
                        st.table(preview_data)
                        
                        # Initialisation du dictionnaire metadata s'il n'existe pas
                        if "metadata" not in locals():
                            metadata = {}
                        
                        # Stockage des données dans le dictionnaire
                        metadata["contenu_csv"] = {
                            "header": header,
                            "data": lines[1:],  # Toutes les lignes sauf l'en-tête
                            "separator": ";"
                        }
                except Exception as e:
                    st.error(f"Erreur lors de l'analyse du CSV : {str(e)}")

        # Dictionnaire des variables
        st.subheader("Dictionnaire des variables")
        with st.expander("Dictionnaire", expanded=False):
            st.info("""
            Collez ici le dictionnaire des variables.
            Format attendu : COD_VAR;LIB_VAR;LIB_VAR_LONG;COD_MOD;LIB_MOD;TYPE_VAR;LONG_VAR
            """)
            dictionnaire = st.text_area(
                "Dictionnaire",
                height=300,
                help="Collez le dictionnaire des variables ici. Utilisez le point-virgule (;) comme séparateur."
            )
            
            if dictionnaire:
                try:
                    # Vérification du format
                    lines = dictionnaire.strip().split('\n')
                    header = lines[0].split(';')
                    expected_header = ['COD_VAR', 'LIB_VAR', 'LIB_VAR_LONG', 'COD_MOD', 'LIB_MOD', 'TYPE_VAR', 'LONG_VAR']
                    
                    if header != expected_header:
                        st.error("Format d'en-tête incorrect. Vérifiez que les colonnes sont dans le bon ordre.")
                    else:
                        # Affichage d'un aperçu
                        st.write("Aperçu des données (5 premières lignes) :")
                        preview_data = []
                        for line in lines[1:6]:  # Afficher les 5 premières lignes de données
                            preview_data.append(line.split(';'))
                        st.table(preview_data)
                        
                        # Initialisation du dictionnaire metadata s'il n'existe pas
                        if "metadata" not in locals():
                            metadata = {}
                        
                        # Stockage des données dans le dictionnaire
                        metadata["dictionnaire"] = {
                            "header": header,
                            "data": lines[1:],  # Toutes les lignes sauf l'en-tête
                            "separator": ";"
                        }
                except Exception as e:
                    st.error(f"Erreur lors de l'analyse du dictionnaire : {str(e)}")
        
        # Bouton de soumission
        submitted = st.form_submit_button("Sauvegarder les métadonnées")
        
        if submitted:
            if not nom_fichier:
                st.error("Veuillez d'abord saisir un nom de fichier")
            else:
                try:
                    # Initialisation du dictionnaire metadata s'il n'existe pas
                    if "metadata" not in locals():
                        metadata = {}
                    
                    # Création du dictionnaire de métadonnées
                    metadata.update({
                        "nom_fichier": nom_fichier,
                        "informations_base": {
                            "nom_base": nom_base,
                            "schema": schema,
                            "description": description,
                            "date_creation": date_creation.strftime("%Y-%m-%d") if date_creation else None,
                            "date_maj": date_maj.strftime("%Y-%m-%d") if date_maj else None,
                            "source": source,
                            "frequence_maj": frequence_maj,
                            "licence": licence
                        },
                        "informations_supplementaires": {
                            "envoi_par": envoi_par,
                            "contact": contact,
                            "mots_cles": mots_cles,
                            "notes": notes
                        }
                    })
                    
                    st.write("Données à sauvegarder :")
                    st.json(metadata)

                    # Sauvegarde dans la base de données
                    succes, message = save_metadata(metadata)
                    if succes:
                        st.success(message)
                        st.info("Vous pouvez maintenant vérifier les données dans le catalogue.")
                    else:
                        st.error(f"Erreur lors de la sauvegarde : {message}")
                        st.error("Veuillez vérifier les logs pour plus de détails.")

                    # Sauvegarde locale en JSON
                    try:
                        json_path = os.path.join("metadata", f"{nom_fichier}.json")
                        os.makedirs("metadata", exist_ok=True)
                        with open(json_path, "w", encoding="utf-8") as f:
                            json.dump(metadata, f, ensure_ascii=False, indent=4)
                        st.success(f"Métadonnées sauvegardées localement dans {json_path}")
                    except Exception as e:
                        st.error(f"Erreur lors de la sauvegarde locale en JSON : {str(e)}")

                    # Sauvegarde locale en TXT
                    try:
                        txt_path = os.path.join("metadata", f"{nom_fichier}.txt")
                        with open(txt_path, "w", encoding="utf-8") as f:
                            f.write(f"Nom du fichier : {nom_fichier}\n")
                            f.write(f"Nom de la base : {nom_base}\n")
                            f.write(f"Schéma : {schema}\n")
                            f.write(f"Description : {description}\n")
                            if date_creation:
                                f.write(f"Date de création : {date_creation.strftime('%Y-%m-%d')}\n")
                            if date_maj:
                                f.write(f"Dernière mise à jour : {date_maj.strftime('%Y-%m-%d')}\n")
                            f.write(f"Source : {source}\n")
                            f.write(f"Fréquence de mise à jour : {frequence_maj}\n")
                            f.write(f"Licence : {licence}\n")
                            f.write(f"Envoi par : {envoi_par}\n")
                            f.write(f"Contact : {contact}\n")
                            f.write(f"Mots-clés : {mots_cles}\n")
                            f.write(f"Notes : {notes}\n")
                            if contenu_csv:
                                f.write("\nContenu CSV :\n")
                                f.write(contenu_csv)
                            if dictionnaire:
                                f.write("\nDictionnaire des variables :\n")
                                f.write(dictionnaire)
                        st.success(f"Métadonnées sauvegardées localement dans {txt_path}")
                    except Exception as e:
                        st.error(f"Erreur lors de la sauvegarde locale en TXT : {str(e)}")
                        
                except Exception as e:
                    st.error(f"Erreur inattendue : {str(e)}")
                    st.error("Veuillez vérifier les logs pour plus de détails.")

with tab2:
    st.subheader("Structure des données")
    uploaded_file = st.file_uploader("Choisir un fichier CSV", type="csv", key="csv_uploader_unique")
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.write("Aperçu des données :")
        st.dataframe(df.head())
        st.write("Structure des colonnes :")
        st.dataframe(pd.DataFrame({
            'Type': df.dtypes,
            'Non-nuls': df.count(),
            'Nulls': df.isna().sum()
        }))

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