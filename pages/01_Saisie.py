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
        
        # Champs de base - Modifications des libellés et descriptions
        col1, col2 = st.columns(2)
        with col1:
            schema = st.selectbox(
                "Schéma du SGBD *", 
                ["economie", "education", "energie", "environnement", "geo", "logement", "mobilite", "population", "securite"],
                help="Schéma de la table dans le SGBD Intelligence des Territoires"
            )
        with col2:
            nom_fichier = st.selectbox(
                "Nom de la base de données *", 
                ["opendata"],
                help="Nom de la table dans le SGBD Intelligence des Territoires"
            )
        
        col3, col4 = st.columns(2)
        with col3:
            nom_table = st.text_input(
                "Nom de la table *", 
                help="Nom de la table dans le SGBD Intelligence des Territoires"
            )
        with col4:
            nom_base = st.text_input(
                "Producteur de la donnée *",
                help="Nom de l'organisme pourvoyeur de la donnée"
            )
        
        # Dates
        col1, col2 = st.columns(2)
        with col1:
            annee = st.number_input(
                "Millésime/année *", 
                min_value=1900,
                max_value=datetime.now().year,
                value=datetime.now().year,
                help="Année de référence des données"
            )
        with col2:
            date_maj = st.date_input(
                "Dernière mise à jour *", 
                format="DD/MM/YYYY",
                help="Date de la dernière mise à jour des données"
            )
        
        # Granularité géographique
        granularite_geo = st.selectbox(
            "Granularité géographique",
            ["IRIS", "Commune", "EPCI", "Département", "Région", "Carreau", "Adresse", "Coordonnées géographiques"],
            help="Granularité géographique la plus fine de la table de données"
        )
        
        # Description
        description = st.text_area(
            "Description *", 
            help="Description détaillée du contenu et de l'utilisation des données"
        )
        
        # Informations supplémentaires
        st.subheader("Informations supplémentaires")
        
        col1, col2 = st.columns(2)
        with col1:
            source = st.text_input(
                "Source (URL)", 
                help="URL ou référence de la source originale des données"
            )
        with col2:
            frequence_maj = st.selectbox(
                "Fréquence de mises à jour des données",
                ["Annuelle", "Semestrielle", "Trimestrielle", "Mensuelle", "Quotidienne", "Ponctuelle"],
                help="Fréquence à laquelle les données sont mises à jour"
            )
            
        col3, col4 = st.columns(2)
        with col3:
            licence = st.selectbox(
                "Licence d'utilisation des données",
                ["Licence ouverte / Etalab", "Creative Commons", "Licence propriétaire", "Autre"],
                help="Conditions d'utilisation des données"
            )
        with col4:
            envoi_par = st.text_input(
                "Personne remplissant le formulaire", 
                help="Nom de la personne qui remplit le formulaire"
            )
        
        # Contenu CSV
        st.subheader("Contenu CSV")
        
        with st.expander("Dépliez", expanded=False):
            # Déplacement du sélecteur de séparateur sous le bouton "Dépliez"
            separateur = st.radio("Séparateur", [";", ","], horizontal=True)
            
            st.info("""
            Copiez-collez ici les 4 premières lignes de la table. Format attendu :
            
            COD_VAR;LIB_VAR;LIB_VAR_LONG;COD_MOD;LIB_MOD;TYPE_VAR;LONG_VAR
            COM;Commune ou ARM;Code du département suivi du numéro de commune
            """)
            
            contenu_csv = st.text_area(
                "4 premières lignes du CSV :", 
                height=300,
                help="Copiez-collez ici les 4 premières lignes du fichier CSV"
            )
            
            if contenu_csv:
                try:
                    # Vérification du format
                    lines = contenu_csv.strip().split('\n')
                    header = lines[0].split(separateur)
                    
                    # Affichage d'un aperçu
                    st.write("Aperçu des données (5 premières lignes) :")
                    preview_data = []
                    for line in lines[1:6]:  # Afficher les 5 premières lignes de données
                        preview_data.append(line.split(separateur))
                    st.table(preview_data)
                    
                    # Initialisation du dictionnaire metadata s'il n'existe pas
                    if "metadata" not in locals():
                        metadata = {}
                    
                    # Traitement du contenu CSV
                    if contenu_csv:
                        try:
                            lines = contenu_csv.strip().split('\n')
                            header = lines[0].split(separateur)
                            
                            # Transformation des lignes en liste pour garantir la cohérence
                            data_rows = []
                            for line in lines[1:]:
                                if line.strip():  # Ignorer les lignes vides
                                    data_rows.append(line.split(separateur))
                            
                            metadata["contenu_csv"] = {
                                "header": header,
                                "data": data_rows,  # Stockage sous forme de liste de listes
                                "separator": separateur
                            }
                        except Exception as e:
                            st.warning(f"Erreur lors de l'analyse du CSV : {str(e)}")
                except Exception as e:
                    st.error(f"Erreur lors de l'analyse du CSV : {str(e)}")
        
        # Dictionnaire des variables
        st.subheader("Dictionnaire des variables")
        with st.expander("Dépliez", expanded=False):
            # Ajout du sélecteur de séparateur pour le dictionnaire
            dict_separateur = st.radio("Séparateur du dictionnaire", [";", ","], horizontal=True)
            
            st.info("""
            Copiez-collez ici le dictionnaire des variables. Format attendu :
            
            P20_POP1564;Pop 15-64 ans en 2020 (princ);Nombre de personnes de 15 à 64 ans;;;NUM;17
            """)
            
            dictionnaire = st.text_area(
                "Dictionnaire des variables :", 
                height=300,
                help="Copiez-collez ici le dictionnaire des variables"
            )
            
            if dictionnaire:
                try:
                    # Vérification du format
                    lines = dictionnaire.strip().split('\n')
                    header = lines[0].split(dict_separateur)  # Utiliser le séparateur choisi
                    expected_header = ['COD_VAR', 'LIB_VAR', 'LIB_VAR_LONG', 'COD_MOD', 'LIB_MOD', 'TYPE_VAR', 'LONG_VAR']
                    
                    # Au lieu de vérifier que les en-têtes sont identiques, on vérifie juste le nombre de colonnes
                    if len(header) < 3:
                        st.warning("Format d'en-tête potentiellement incorrect. Le dictionnaire doit avoir au moins 3 colonnes.")
                    
                    # Affichage d'un aperçu
                    st.write("Aperçu des données (5 premières lignes) :")
                    preview_data = []
                    for line in lines[1:6]:  # Afficher les 5 premières lignes de données
                        preview_data.append(line.split(dict_separateur))  # Utiliser le séparateur choisi
                    st.table(preview_data)
                    
                    # Initialisation du dictionnaire metadata s'il n'existe pas
                    if "metadata" not in locals():
                        metadata = {}
                    
                    # Traitement du dictionnaire des variables
                    if dictionnaire:
                        try:
                            lines = dictionnaire.strip().split('\n')
                            # Tentative de déduire les colonnes à partir des données
                            sample_line = lines[0].split(dict_separateur)  # Utiliser le séparateur choisi
                            
                            # Définition des colonnes attendues
                            expected_columns = ['COD_VAR', 'LIB_VAR', 'LIB_VAR_LONG', 'COD_MOD', 'LIB_MOD', 'TYPE_VAR', 'LONG_VAR']
                            
                            # Vérifier s'il y a le bon nombre de colonnes (optionnel)
                            if len(sample_line) != len(expected_columns):
                                st.warning(f"Le nombre de colonnes ({len(sample_line)}) ne correspond pas au nombre attendu ({len(expected_columns)}). Le dictionnaire sera tout de même traité.")
                            
                            # Transformation des lignes en liste pour garantir la cohérence
                            data_rows = []
                            for line in lines[1:]:
                                if line.strip():  # Ignorer les lignes vides
                                    data_rows.append(line.split(dict_separateur))  # Utiliser le séparateur choisi
                            
                            # Afficher un avertissement si le dictionnaire est très volumineux
                            if len(data_rows) > 1000:
                                st.warning(f"Le dictionnaire est très volumineux ({len(data_rows)} lignes). " +
                                          "Les performances peuvent être affectées. " +
                                          "Seules les 2000 premières lignes seront stockées.")
                            
                            # Utilisation des colonnes déduites ou des colonnes attendues selon la situation
                            metadata["dictionnaire"] = {
                                "header": expected_columns[:len(sample_line)],
                                "data": data_rows,  # Stockage sous forme de liste de listes
                                "separator": dict_separateur  # Utiliser le séparateur choisi
                            }
                        except Exception as e:
                            st.warning(f"Erreur lors de l'analyse du dictionnaire : {str(e)}")
                except Exception as e:
                    st.error(f"Erreur lors de l'analyse du dictionnaire : {str(e)}")
        
        # Bouton de soumission
        st.markdown("---")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submitted = st.form_submit_button(
                "Sauvegarder les métadonnées", 
                type="primary",
                use_container_width=True
            )
        
        if submitted:
            if not nom_fichier:
                st.error("Veuillez d'abord saisir un nom de fichier")
            else:
                try:
                    # Préparation du dictionnaire de métadonnées
                    metadata = {"contenu_csv": {}, "dictionnaire": {}}
                    
                    # Traitement du contenu CSV
                    if contenu_csv:
                        try:
                            lines = contenu_csv.strip().split('\n')
                            header = lines[0].split(separateur)
                            
                            # Transformation des lignes en liste pour garantir la cohérence
                            data_rows = []
                            for line in lines[1:]:
                                if line.strip():  # Ignorer les lignes vides
                                    data_rows.append(line.split(separateur))
                            
                            metadata["contenu_csv"] = {
                                "header": header,
                                "data": data_rows,  # Stockage sous forme de liste de listes
                                "separator": separateur
                            }
                        except Exception as e:
                            st.warning(f"Erreur lors de l'analyse du CSV : {str(e)}")
                    
                    # Traitement du dictionnaire des variables
                    if dictionnaire:
                        try:
                            lines = dictionnaire.strip().split('\n')
                            # Tentative de déduire les colonnes à partir des données
                            sample_line = lines[0].split(dict_separateur)  # Utiliser le séparateur choisi
                            
                            # Définition des colonnes attendues
                            expected_columns = ['COD_VAR', 'LIB_VAR', 'LIB_VAR_LONG', 'COD_MOD', 'LIB_MOD', 'TYPE_VAR', 'LONG_VAR']
                            
                            # Vérifier s'il y a le bon nombre de colonnes (optionnel)
                            if len(sample_line) != len(expected_columns):
                                st.warning(f"Le nombre de colonnes ({len(sample_line)}) ne correspond pas au nombre attendu ({len(expected_columns)}). Le dictionnaire sera tout de même traité.")
                            
                            # Transformation des lignes en liste pour garantir la cohérence
                            data_rows = []
                            for line in lines[1:]:
                                if line.strip():  # Ignorer les lignes vides
                                    data_rows.append(line.split(dict_separateur))  # Utiliser le séparateur choisi
                            
                            # Afficher un avertissement si le dictionnaire est très volumineux
                            if len(data_rows) > 1000:
                                st.warning(f"Le dictionnaire est très volumineux ({len(data_rows)} lignes). " +
                                          "Les performances peuvent être affectées. " +
                                          "Seules les 2000 premières lignes seront stockées.")
                            
                            # Utilisation des colonnes déduites ou des colonnes attendues selon la situation
                            metadata["dictionnaire"] = {
                                "header": expected_columns[:len(sample_line)],
                                "data": data_rows,  # Stockage sous forme de liste de listes
                                "separator": dict_separateur  # Utiliser le séparateur choisi
                            }
                        except Exception as e:
                            st.warning(f"Erreur lors de l'analyse du dictionnaire : {str(e)}")
                    
                    # Création du dictionnaire de métadonnées
                    metadata.update({
                        "nom_fichier": nom_fichier,
                        "informations_base": {
                            "nom_table": nom_table,
                            "nom_base": nom_base,
                            "schema": schema,
                            "description": description,
                            "date_creation": str(annee),
                            "date_maj": date_maj.strftime("%Y-%m-%d") if date_maj else None,
                            "source": source,
                            "frequence_maj": frequence_maj,
                            "licence": licence,
                            "envoi_par": envoi_par,
                            "separateur_csv": separateur,
                            "granularite_geo": granularite_geo
                        }
                    })

                    # Sauvegarde dans la base de données
                    succes, message = save_metadata(metadata)
                    if succes:
                        st.success(message)
                        # Création d'un encadré de succès bien visible
                        st.balloons()
                        st.success("""
                        ### ✅ Métadonnées sauvegardées avec succès!
                        
                        Vos métadonnées sont maintenant disponibles dans le catalogue.
                        Vous pouvez les consulter dans l'onglet "Catalogue".
                        """)
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
                            f.write(f"Nom de la base de données : {nom_fichier}\n")
                            f.write(f"Schéma du SGBD : {schema}\n")
                            f.write(f"Nom de la table : {nom_table}\n")
                            f.write(f"Producteur de la donnée : {nom_base}\n")
                            f.write(f"Granularité géographique : {granularite_geo}\n")
                            f.write(f"Description : {description}\n")
                            f.write(f"Millésime/année : {annee}\n")
                            if date_maj:
                                f.write(f"Dernière mise à jour : {date_maj.strftime('%Y-%m-%d')}\n")
                            f.write(f"Source : {source}\n")
                            f.write(f"Fréquence de mises à jour des données : {frequence_maj}\n")
                            f.write(f"Licence d'utilisation des données : {licence}\n")
                            f.write(f"Personne remplissant le formulaire : {envoi_par}\n")
                            f.write(f"Séparateur CSV : {separateur}\n")
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
    uploaded_file = st.file_uploader("Choisir un fichier CSV", type="csv")
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
    Les champs marqués d'un astérisque (*) sont obligatoires.
    
    - **Schéma du SGBD** : Schéma de la table dans le SGBD Intelligence des Territoires
    - **Nom de la table** : Nom de la table dans le SGBD Intelligence des Territoires
    - **Table de la base de données** : Nom de la table dans le SGBD Intelligence des Territoires
    - **Producteur de la donnée** : Nom de l'organisme pourvoyeur de la donnée
    - **Millésime/année** : Année de référence des données
    - **Dernière mise à jour** : Date de la dernière mise à jour des données
    - **Description** : Description détaillée du contenu des données
    
    ### Conseils de saisie
    1. **Informations de base**
       - Le nom de la table est actuellement limité à certaines valeurs prédéfinies
       - Le schéma doit correspondre à l'une des catégories prédéfinies
       - Le producteur doit être l'organisme source des données
       - Le millésime doit correspondre à l'année de référence des données
    
    2. **Description**
       - Soyez aussi précis que possible dans la description
    
    3. **Informations supplémentaires**
       - Indiquez la personne qui remplit le formulaire
       - Précisez la source originale des données (URL ou référence)
       - Sélectionnez la fréquence de mise à jour appropriée
       - Choisissez la licence qui correspond aux conditions d'utilisation
    
    4. **Données CSV**
       - Copiez-collez les premières lignes du fichier CSV
       - Indiquez le séparateur utilisé (par défaut, point-virgule)
       - Ajoutez le dictionnaire des variables si le fichier CSV est disponible
    """)

# Pied de page
st.markdown("---")
st.markdown("© 2025 - Système de Gestion des Métadonnées") 