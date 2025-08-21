import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
import os
import sys
from pathlib import Path
from utils.auth import authenticate_and_logout
from utils.sql_generator import display_sql_generation_interface_new
import re

# Ajout du répertoire parent au PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent))
from utils.db_utils import init_db, save_metadata, get_types_donnees, get_producteurs_by_type, get_jeux_donnees_by_producteur, get_db_connection

def parse_csv_line(line: str, separator: str) -> list:
    """Parse intelligente d'une ligne CSV avec gestion des guillemets."""
    import csv
    import io
    
    try:
        reader = csv.reader(io.StringIO(line), delimiter=separator, quotechar='"')
        return next(reader)
    except:
        return line.split(separator)

# Configuration de la page
st.set_page_config(
    page_title="Saisie des métadonnées",
    page_icon="📝",
    layout="wide"
)

# Authentification centralisée (présente sur toutes les pages)
name, authentication_status, username, authenticator = authenticate_and_logout()

# Initialisation de la base de données
init_db()

# CSS pour le style du formulaire
st.markdown("""
<style>
    /* Style du titre */
    h1 {
        color: #1E4B88;
        font-size: 2rem;
        margin-bottom: 0.5rem;
    }
    
    /* Style des sous-titres */
    h2, h3, .stSubheader {
        color: #333;
        margin-top: 0;
        margin-bottom: 16px;
    }
    
    /* Style des boîtes */
    .block-container {
        max-width: 1200px;
        padding-top: 1rem;
    }
    
    /* Style des champs obligatoires */
    .required label::after {
        content: " *";
        color: red;
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
    
    /* Améliorations visuelles générales */
    label {
        font-weight: 500;
    }
    
    .stInfo {
        background-color: #E3F2FD;
        padding: 10px;
        border-radius: 5px;
        border-left: 5px solid #1E88E5;
    }
    
    /* Style des messages de succès */
    .stSuccess {
        background-color: #E8F5E9;
        padding: 16px;
        border-radius: 5px;
        border-left: 5px solid #4CAF50;
    }
    
    /* Style du séparateur */
    hr {
        margin-top: 2rem;
        margin-bottom: 2rem;
        border: 0;
        border-top: 1px solid #eee;
    }
</style>
""", unsafe_allow_html=True)

# Titre et description
st.title("Saisie des métadonnées")
st.write("Remplissez le formulaire ci-dessous pour ajouter de nouvelles métadonnées.")

# --- NOUVELLE ORGANISATION DU FORMULAIRE AVEC LOGIQUE DYNAMIQUE ---

# Récupération des options depuis la base de données
from utils.db_utils import get_types_donnees, get_producteurs_by_type, get_jeux_donnees_by_producteur

# --- Affichage du formulaire restructuré ---
col1, col2 = st.columns(2)

with col1:
    # Type de données
    types_donnees = get_types_donnees()
    type_sel = st.selectbox("Type de données*", types_donnees, key="type_donnees_select")
    if type_sel == "autre":
        type_donnees = st.text_input("Préciser le type de données*", key="type_donnees_input")
    else:
        type_donnees = type_sel

with col2:
    # Producteur de la donnée
    producteurs_dyn = get_producteurs_by_type(type_donnees)
    producteurs_options = producteurs_dyn + ["Autre"] if producteurs_dyn else ["Autre"]
    producteur_sel = st.selectbox("Producteur de la donnée*", producteurs_options, key="producteur_select")
    if producteur_sel == "Autre":
        producteur = st.text_input("Saisir un nouveau producteur*", key="producteur_input")
    else:
        producteur = producteur_sel

col3, col4 = st.columns(2)
with col3:
    # Nom du jeu de données
    jeux_dyn = get_jeux_donnees_by_producteur(producteur)
    jeux_options = jeux_dyn + ["Autre"] if jeux_dyn else ["Autre"]
    jeu_sel = st.selectbox("Nom du jeu de données*", jeux_options, key="jeu_donnees_select")
    if jeu_sel == "Autre":
        nom_jeu_donnees = st.text_input("Saisir un nouveau nom de jeu de données*", key="jeu_donnees_input")
    else:
        nom_jeu_donnees = jeu_sel

with col4:
    granularite_geo = st.selectbox("Granularité géographique*", [
        "", "commune", "IRIS", "carreau", "adresse", "coordonnées GPS", "EPCI", "département", "région", "bassin de vie", "autre"
    ], index=1, help="Niveau géographique le plus fin des données")

col5, col6 = st.columns(2)
with col5:
    date_publication = st.date_input("Date de publication*", 
        value=datetime.now().date(), 
        format="DD/MM/YYYY",
        min_value=datetime(1949, 1, 1).date())
with col6:
    date_maj = st.date_input("Date de dernière mise à jour*", 
        value=datetime.now().date(), 
        format="DD/MM/YYYY",
        min_value=datetime(1949, 1, 1).date())
# S'assurer que date_maj est bien accessible partout
if 'date_maj' not in locals():
    date_maj = datetime.now().date()

col7, col8 = st.columns(2)
with col7:
    millesime = st.number_input("Millésime/année*", min_value=1900, max_value=datetime.now().year, value=datetime.now().year, help="Année de référence des données")
with col8:
    frequence_maj = st.selectbox("Fréquence de mise à jour des données*", [
        "", "Annuelle", "Semestrielle", "Trimestrielle", "Mensuelle", "Quotidienne", "Ponctuelle"
    ], help="Fréquence à laquelle les données sont mises à jour")
    def calculer_prochaine_publication(date_pub, freq):
        if not date_pub or not freq:
            return None
        if freq == "Annuelle":
            return date_pub + timedelta(days=365)
        elif freq == "Semestrielle":
            return date_pub + timedelta(days=182)
        elif freq == "Trimestrielle":
            return date_pub + timedelta(days=91)
        elif freq == "Mensuelle":
            return date_pub + timedelta(days=30)
        elif freq == "Quotidienne":
            return date_pub + timedelta(days=1)
        else:
            return None
    date_prochaine_publication_auto = calculer_prochaine_publication(date_publication, frequence_maj)
with col8:
    date_prochaine_publication = st.date_input(
        "Date estimative de la prochaine publication*",
        value=date_prochaine_publication_auto if date_prochaine_publication_auto else datetime.now().date(),
        format="DD/MM/YYYY",
        min_value=datetime(1949, 1, 1).date(),
        help="Cette date est calculée automatiquement selon la fréquence, mais peut être modifiée."
    )

# Description (pleine largeur)
st.markdown('<div class="required">', unsafe_allow_html=True)
description = st.text_area("Description*", height=150, help="Description détaillée des données, leur collecte, leur utilité, etc.", key="description")
st.markdown('</div>', unsafe_allow_html=True)

# --- Informations d'import ---
col9, col10 = st.columns(2)
with col9:
    nom_base = st.selectbox("Nom de la base de données*", ["opendata"], help="Nom de la base de données dans le SGBD")
with col10:
    schema = st.selectbox("Schéma thématique*", [
        "raw_eco", "raw_educ", "raw_energie", "raw_envir", "raw_fin_loc", 
        "raw_log", "raw_mobil", "raw_pop", "raw_reseau", "raw_sante_soc", "raw_securite"
    ], help="Schéma du SGBD dans lequel la table est importée")

# Nom de la table (moitié de ligne)
col11, _ = st.columns([1,1])
with col11:
    nom_table = st.text_input("Nom de la table*", help="Nom de la table dans la base de données")

# Note sur les champs obligatoires
st.markdown('<p style="color: #666;">Les champs marqués d\'un * sont obligatoires.</p>', unsafe_allow_html=True)

# Section Informations supplémentaires
st.subheader("Informations supplémentaires")

col1, col2 = st.columns(2)

with col1:
    source = st.text_input("Source (URL)", help="Source des données (URL, nom du service, etc.)")
    
    licence = st.selectbox("Licence d'utilisation des données",
        ["", "Licence Ouverte Etalab", "Open Data Commons Open Database License (ODbL)", 
         "CC0", "CC BY", "CC BY-SA", "CC BY-NC", "CC BY-ND", 
         "Domaine public", "Licence propriétaire"],
        help="Licence sous laquelle les données sont publiées")

with col2:
    envoi_par = st.text_input("Personne remplissant le formulaire", help="Nom de la personne remplissant ce formulaire")

# Sections dépliables
with st.expander("Extrait CSV", expanded=False):
    separateur = st.radio("Séparateur", [";", ","], horizontal=True)
    contenu_csv = st.text_area("Coller ici les 50 premières lignes du fichier CSV (incluant l'en-tête)", height=200, key="extrait_csv", 
                              help="Pour une meilleure détection des types de données, copiez les 50 premières lignes de votre fichier CSV. Plus d'exemples = meilleure précision du script SQL généré.")

with st.expander("Dictionnaire des variables", expanded=False):
    dict_separateur = st.radio("Séparateur du dictionnaire", [";", ","], horizontal=True)
    dictionnaire = st.text_area("Coller ici le dictionnaire des variables depuis le fichier CSV", height=150, key="dictionnaire")

# Boutons d'action
col_btn1, col_btn2 = st.columns([1, 1])
with col_btn1:
    submitted = st.button("Sauvegarder les métadonnées")
with col_btn2:
    generate_sql = st.button("Générer le script SQL d'import", help="Génère automatiquement le script SQL d'import basé sur les métadonnées")

# Option debug en dessous des boutons
debug_mode = st.checkbox("Mode debug", value=False, help="Affiche des informations supplémentaires pour le débogage")

# Traitement de la soumission
if submitted:
    if not nom_table:
        st.error("Veuillez saisir un nom de table")
    else:
        try:
            # Préparation du dictionnaire de métadonnées avec les nouveaux champs à la racine
            metadata = {
                "type_donnees": type_donnees,
                "nom_jeu_donnees": nom_jeu_donnees,
                "date_publication": date_publication.strftime("%Y-%m-%d") if date_publication else None,
                "date_maj": date_maj.strftime("%Y-%m-%d") if date_maj else None,
                "date_prochaine_publication": date_prochaine_publication.strftime("%Y-%m-%d") if date_prochaine_publication else None,
                "contenu_csv": {},
                "dictionnaire": {},
                "nom_fichier": nom_base,  # correspond à nom_base dans la BD
                "nom_table": nom_table,
                "informations_base": {
                    "nom_table": nom_table,
                    "nom_base": nom_base,
                    "type_donnees": type_donnees,
                    "producteur": producteur,
                    "nom_jeu_donnees": nom_jeu_donnees,
                    "schema": schema,
                    "description": description,
                    "date_creation": str(millesime),
                    "source": source,
                    "frequence_maj": frequence_maj,
                    "licence": licence,
                    "envoi_par": envoi_par,
                    "separateur_csv": separateur,
                    "granularite_geo": granularite_geo
                }
            }
            
            # Traitement du contenu CSV
            if contenu_csv:
                try:
                    lines = contenu_csv.strip().split('\n')
                    
                    # Parser l'en-tête avec la fonction unifiée
                    header = parse_csv_line(lines[0], separateur)
                    
                    # Parser les données (maximum 50 lignes pour performance)
                    data_rows = []
                    for line in lines[1:51]:  # Limiter à 50 lignes de données
                        if line.strip():  # Ignorer les lignes vides
                            parsed_row = parse_csv_line(line, separateur)
                            data_rows.append(parsed_row)
                    
                    metadata["contenu_csv"] = {
                        "header": header,
                        "data": data_rows,
                        "separator": separateur
                    }
                except Exception as e:
                    st.warning(f"Erreur lors de l'analyse du CSV : {str(e)}")
                    st.warning("Vérifiez le format CSV et le séparateur choisi.")
            
            # Traitement du dictionnaire des variables
            if dictionnaire:
                try:
                    lines = dictionnaire.strip().split('\n')
                    
                    # S'assurer qu'il y a au moins une ligne d'en-tête
                    if not lines:
                        st.warning("Le dictionnaire est vide, il sera ignoré.")
                    else:
                        # Parser l'en-tête avec la fonction unifiée
                        header = parse_csv_line(lines[0], dict_separateur)
                        
                        # Parser les données avec la fonction unifiée
                        data_rows = []
                        for line in lines[1:]:
                            if line.strip():  # Ignorer les lignes vides
                                parsed_row = parse_csv_line(line, dict_separateur)
                                data_rows.append(parsed_row)
                        
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
                st.balloons()
                st.success("""
### ✅ Métadonnées sauvegardées avec succès!

Vos métadonnées sont maintenant disponibles dans le catalogue.
Vous pouvez les consulter dans l'onglet "Catalogue".
""")
            else:
                st.error(f"Erreur lors de la sauvegarde : {message}")
                st.error("Veuillez vérifier les logs pour plus de détails.")

            # Sauvegarde locale (optionnelle - ne pas afficher d'erreur si échec)
            try:
                # Créer le répertoire metadata dans le répertoire courant de l'application
                metadata_dir = os.path.join(os.path.dirname(__file__), "..", "metadata")
                os.makedirs(metadata_dir, exist_ok=True)
                
                # Sauvegarde en JSON
                json_path = os.path.join(metadata_dir, f"{nom_table}.json")
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=4)
                
                # Sauvegarde en TXT  
                txt_path = os.path.join(metadata_dir, f"{nom_table}.txt")
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(f"Nom de la table : {nom_table}\n")
                    f.write(f"Nom de la base de données : {nom_base}\n")
                    f.write(f"Schéma du SGBD : {schema}\n")
                    f.write(f"Producteur de la donnée : {producteur}\n")
                    f.write(f"Granularité géographique : {granularite_geo}\n")
                    f.write(f"Description : {description}\n")
                    f.write(f"Millésime/année : {millesime}\n")
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
                
                st.info(f"📁 Sauvegarde locale effectuée dans le répertoire metadata/")
                
            except Exception as e:
                # Sauvegarde locale échouée - ce n'est pas critique
                st.warning(f"⚠️ Sauvegarde locale non disponible (non critique) : {str(e)}")
                
        except Exception as e:
            st.error(f"Erreur inattendue : {str(e)}")
            st.error("Veuillez vérifier les logs pour plus de détails.")

# Traitement du bouton de génération SQL
if generate_sql:
    if not nom_table:
        st.error("Veuillez d'abord saisir un nom de table pour générer le script SQL")
    else:
        # Utilisation de la fonction du module sql_generator qui gère tout l'affichage
        display_sql_generation_interface_new(nom_table, debug_mode=debug_mode)

# Section d'aide
with st.expander("Aide pour la saisie ❓"):
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
       - Copiez-collez les 50 premières lignes de votre fichier CSV (en-tête inclus)
       - Plus d'exemples = meilleure précision du script SQL généré automatiquement
       - Indiquez le séparateur utilisé (point-virgule par défaut pour les fichiers français)
       - Ajoutez le dictionnaire des variables si disponible pour optimiser la détection des types
    """)

# Pied de page
st.markdown("---")
st.markdown('<div style="text-align: center; color: #666;">© 2025 - Système de Gestion des Métadonnées</div>', unsafe_allow_html=True) 
