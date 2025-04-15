import streamlit as st
import pandas as pd
import json
from datetime import datetime
import os
import sys
from pathlib import Path

# Ajout du répertoire parent au PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent))
from db_utils import init_db, save_metadata

# Configuration de la page
st.set_page_config(
    page_title="Saisie des métadonnées",
    page_icon="📝",
    layout="wide"
)

# Initialisation de la base de données
init_db()

# CSS pour le style du formulaire - RECRÉATION EXACTE DU STYLE PRÉFÉRÉ
st.markdown("""
<style>
    /* Styles généraux */
    .main {
        max-width: 1200px;
        margin: 0 auto;
    }
    
    /* Style du titre */
    .main h1 {
        color: #1E4B88;
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }
    
    /* Style du conteneur principal avec cadre et ombre */
    .form-container {
        background-color: white;
        border-radius: 10px;
        box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
        margin-bottom: 20px;
        padding: 20px;
    }
    
    /* Style des sous-titres */
    .stSubheader {
        color: #333;
        border-bottom: 1px solid #e0e0e0;
        padding-bottom: 8px;
        margin-top: 20px;
        margin-bottom: 16px;
    }
    
    /* Style des champs obligatoires */
    .required label::after {
        content: " *";
        color: red;
    }
    
    /* Style des onglets */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 1rem 1.5rem;
        font-size: 1rem;
        font-weight: 500;
    }
    .stTabs [data-baseweb="tab-highlight"] {
        background-color: #1E88E5;
    }
    
    /* Style des boutons dépliables */
    button[data-baseweb="accordion"] {
        background-color: #f8f9fa;
        border-radius: 5px;
        margin-bottom: 10px;
    }
    
    /* Style du bouton de sauvegarde */
    .stButton button {
        background-color: #4CAF50;
        color: white;
        font-weight: 500;
        border-radius: 4px;
        padding: 0.5rem 1rem;
        width: 100%;
    }
    
    /* Style des champs de saisie */
    .stTextInput, .stSelectbox, .stDateInput, .stTextArea {
        margin-bottom: 15px;
    }
    .stTextInput > label, .stSelectbox > label, .stDateInput > label, .stTextArea > label {
        font-weight: 500;
    }
    
    /* Style des informations d'aide */
    .stExpander {
        border: 1px solid #e0e0e0;
        border-radius: 5px;
        margin-top: 1rem;
    }
    
    /* Style des messages de succès */
    .stSuccess {
        background-color: #E8F5E9;
        padding: 16px;
        border-radius: 5px;
        border-left: 5px solid #4CAF50;
    }
</style>
""", unsafe_allow_html=True)

# Titre et description
st.title("Saisie des métadonnées")
st.write("Remplissez le formulaire ci-dessous pour ajouter de nouvelles métadonnées.")

# Conteneur du formulaire avec style cadré
st.markdown('<div class="form-container">', unsafe_allow_html=True)

# Section Informations de base
st.subheader("Informations de base")

# Organisation en colonnes
col1, col2 = st.columns(2)

with col1:
    st.markdown('<div class="required">', unsafe_allow_html=True)
    schema = st.selectbox("Schéma du SGBD", 
        ["economie", "education", "energie", "environnement", 
         "geo", "logement", "mobilite", "population", "securite"],
         help="Catégorie thématique des données")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="required">', unsafe_allow_html=True)
    nom_base = st.selectbox("Nom de la base de données", 
        ["opendata"], 
        help="Nom de la base de données dans le SGBD")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="required">', unsafe_allow_html=True)
    nom_table = st.text_input("Nom de la table", help="Nom de la table dans la base de données")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="required">', unsafe_allow_html=True)
    producteur = st.text_input("Producteur de la donnée", help="Organisme producteur de la donnée")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    granularite_geo = st.selectbox("Granularité géographique", 
        ["", "commune", "EPCI", "département", "région", "IRIS", "autre"],
        help="Niveau géographique le plus fin des données")
    
    st.markdown('<div class="required">', unsafe_allow_html=True)
    millesime = st.number_input("Millésime/année", 
        min_value=1900, 
        max_value=datetime.now().year, 
        value=datetime.now().year,
        help="Année de référence des données")
    st.markdown('</div>', unsafe_allow_html=True)
    
    st.markdown('<div class="required">', unsafe_allow_html=True)
    date_maj = st.date_input("Dernière mise à jour", 
        datetime.now().date(),
        help="Date de la dernière mise à jour des données")
    st.markdown('</div>', unsafe_allow_html=True)

# Section Description
st.markdown('<div class="required">', unsafe_allow_html=True)
description = st.text_area("Description", 
    height=150,
    help="Description détaillée des données, leur collecte, leur utilité, etc.")
st.markdown('</div>', unsafe_allow_html=True)

# Section Informations supplémentaires
st.subheader("Informations supplémentaires")

col1, col2 = st.columns(2)

with col1:
    source = st.text_input("Source (URL)", help="Source des données (URL, nom du service, etc.)")
    frequence_maj = st.selectbox("Fréquence de mises à jour des données",
        ["", "Annuelle", "Semestrielle", "Trimestrielle", "Mensuelle", "Quotidienne", "Ponctuelle"],
        help="Fréquence à laquelle les données sont mises à jour")

with col2:
    licence = st.selectbox("Licence d'utilisation des données",
        ["", "Licence ouverte / Etalab", "ODbL", "CC-BY", "CC-BY-SA", "CC-BY-NC", "CC-BY-ND", "Autre"],
        help="Licence sous laquelle les données sont publiées")
    envoi_par = st.text_input("Personne remplissant le formulaire", help="Nom de la personne remplissant ce formulaire")

# Section Contenu CSV
st.subheader("Contenu CSV")
with st.expander("Déplier", expanded=False):
    separateur = st.radio("Séparateur", [";", ","], horizontal=True)
    
    st.info("""
    Copiez-collez ici les 4 premières lignes de la table. Format attendu :
    
    COD_VAR;LIB_VAR;LIB_VAR_LONG;COD_MOD;LIB_MOD;TYPE_VAR;LONG_VAR
    COM;Commune ou ARM;Code du département suivi du numéro de commune
    """)
    
    contenu_csv = st.text_area("4 premières lignes du CSV :", 
        height=200,
        help="Copiez-collez ici les 4 premières lignes du fichier CSV")
    
    if contenu_csv:
        try:
            # Vérification du format
            lines = contenu_csv.strip().split('\n')
            header = lines[0].split(separateur)
            
            # Affichage d'un aperçu
            st.write("Aperçu des données (5 premières lignes) :")
            preview_data = []
            for line in lines[1:6]:  # Afficher les 5 premières lignes de données
                if line.strip():
                    preview_data.append(line.split(separateur))
            st.table(preview_data)
        except Exception as e:
            st.error(f"Erreur lors de l'analyse du CSV : {str(e)}")

# Section Dictionnaire des variables
st.subheader("Dictionnaire des variables")
with st.expander("Déplier", expanded=False):
    dict_separateur = st.radio("Séparateur du dictionnaire", [";", ","], horizontal=True)
    
    st.info("""
    Copiez-collez ici le dictionnaire des variables. Format attendu :
    
    CODE;LIBELLÉ;DESCRIPTION;TYPE;LONGUEUR
    CODGEO;Code géographique;Code de la commune;VARCHAR;5
    """)
    
    dictionnaire = st.text_area("Dictionnaire des variables :", 
        height=200,
        help="Copiez-collez ici le dictionnaire des variables (format CSV)")

# Bouton de soumission
submitted = st.button("Sauvegarder les métadonnées")

st.markdown('</div>', unsafe_allow_html=True)  # Fermeture du conteneur du formulaire

# Traitement de la soumission
if submitted:
    if not nom_table:
        st.error("Veuillez saisir un nom de table")
    else:
        try:
            # Préparation du dictionnaire de métadonnées
            metadata = {
                "contenu_csv": {}, 
                "dictionnaire": {},
                "nom_fichier": nom_base,  # correspond à nom_base dans la BD
                "nom_table": nom_table,
                "informations_base": {
                    "nom_table": nom_table,
                    "nom_base": producteur,  # nom_base dans le formulaire correspond à producteur dans la BD
                    "schema": schema,
                    "description": description,
                    "granularite_geo": granularite_geo,
                    "date_creation": str(millesime),
                    "date_maj": date_maj.strftime("%Y-%m-%d") if date_maj else None,
                    "source": source,
                    "frequence_maj": frequence_maj,
                    "licence": licence,
                    "envoi_par": envoi_par
                }
            }
            
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
                    
                    # S'assurer qu'il y a au moins une ligne d'en-tête
                    if not lines:
                        st.warning("Le dictionnaire est vide, il sera ignoré.")
                    else:
                        # Utiliser le séparateur choisi pour le dictionnaire
                        header = lines[0].split(dict_separateur)
                        
                        # Transformation des lignes en liste pour garantir la cohérence
                        data_rows = []
                        for line in lines[1:]:
                            if line.strip():  # Ignorer les lignes vides
                                data_rows.append(line.split(dict_separateur))
                        
                        # Vérifier si nous avons des données
                        if not data_rows:
                            st.warning("Le dictionnaire ne contient pas de données, uniquement l'en-tête.")
                        
                        # Uniformiser les données pour éviter les erreurs
                        uniform_data = []
                        for row in data_rows:
                            # Si la ligne a moins de colonnes que l'en-tête, ajouter des valeurs vides
                            if len(row) < len(header):
                                row.extend([''] * (len(header) - len(row)))
                            # Si la ligne a plus de colonnes que l'en-tête, tronquer
                            elif len(row) > len(header):
                                row = row[:len(header)]
                            uniform_data.append(row)
                        
                        metadata["dictionnaire"] = {
                            "header": header,
                            "data": uniform_data[:2000],  # Limiter à 2000 lignes maximum
                            "separator": dict_separateur
                        }
                except Exception as e:
                    st.warning(f"Erreur lors de l'analyse du dictionnaire : {str(e)}")
                    st.warning("Le dictionnaire sera ignoré.")
                    metadata["dictionnaire"] = {}

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
                json_path = os.path.join("metadata", f"{nom_table}.json")
                os.makedirs("metadata", exist_ok=True)
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=4)
                st.success(f"Métadonnées sauvegardées localement dans {json_path}")
            except Exception as e:
                st.error(f"Erreur lors de la sauvegarde locale en JSON : {str(e)}")

            # Sauvegarde locale en TXT
            try:
                txt_path = os.path.join("metadata", f"{nom_table}.txt")
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(f"Nom de la table : {nom_table}\n")
                    f.write(f"Nom de la base de données : {nom_base}\n")
                    f.write(f"Schéma du SGBD : {schema}\n")
                    f.write(f"Producteur de la donnée : {producteur}\n")
                    f.write(f"Granularité géographique : {granularite_geo}\n")
                    f.write(f"Description : {description}\n")
                    f.write(f"Millésime/année : {millesime}\n")
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

# Section d'aide
st.markdown('<div class="form-container">', unsafe_allow_html=True)
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
st.markdown('</div>', unsafe_allow_html=True)

# Pied de page
st.markdown("---")
st.markdown('<div style="text-align: center; color: #666;">© 2025 - Système de Gestion des Métadonnées</div>', unsafe_allow_html=True) 