import streamlit as st
import pandas as pd
import json
from datetime import datetime, timedelta
import os
import sys
from pathlib import Path
from utils.auth import authenticate_and_logout
import re

# Ajout du répertoire parent au PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent))
from utils.db_utils import init_db, save_metadata, get_types_donnees, get_producteurs_by_type, get_jeux_donnees_by_producteur, get_db_connection

def normalize_data_type(raw_type: str) -> str:
    """
    Normalise un type de données brut vers un type SQL standard.
    
    Args:
        raw_type: Type brut trouvé dans le dictionnaire des variables
        
    Returns:
        Type SQL standardisé ou None si non reconnu
    """
    if not raw_type:
        return None
    
    type_clean = str(raw_type).strip().lower()
    
    # Mapping des types courants vers SQL
    type_mappings = {
        # Types texte
        'text': 'TEXT',
        'string': 'VARCHAR(255)',
        'str': 'VARCHAR(255)', 
        'char': 'VARCHAR(255)',
        'character': 'VARCHAR(255)',
        'varchar': 'VARCHAR(255)',
        'texte': 'TEXT',
        'chaîne': 'VARCHAR(255)',
        'chaine': 'VARCHAR(255)',
        
        # Types numériques entiers
        'int': 'INTEGER',
        'integer': 'INTEGER',
        'entier': 'INTEGER',
        'number': 'INTEGER',
        'numeric': 'INTEGER',
        'num': 'INTEGER',
        'bigint': 'BIGINT',
        'smallint': 'SMALLINT',
        
        # Types numériques décimaux
        'float': 'DECIMAL(15,6)',
        'decimal': 'DECIMAL(15,6)',
        'double': 'DECIMAL(15,6)',
        'real': 'DECIMAL(15,6)',
        'décimal': 'DECIMAL(15,6)',
        'flottant': 'DECIMAL(15,6)',
        
        # Types date/temps
        'date': 'DATE',
        'datetime': 'TIMESTAMP',
        'timestamp': 'TIMESTAMP',
        'time': 'TIME',
        'temps': 'TIMESTAMP',
        
        # Types booléens
        'boolean': 'BOOLEAN',
        'bool': 'BOOLEAN',
        'booléen': 'BOOLEAN',
        'vrai/faux': 'BOOLEAN',
        'oui/non': 'BOOLEAN',
        
        # Types binaires/blob
        'blob': 'BYTEA',
        'binary': 'BYTEA',
        'binaire': 'BYTEA'
    }
    
    # Recherche directe
    if type_clean in type_mappings:
        return type_mappings[type_clean]
    
    # Recherche avec VARCHAR(n)
    import re
    varchar_match = re.match(r'varchar\s*\(\s*(\d+)\s*\)', type_clean)
    if varchar_match:
        size = int(varchar_match.group(1))
        return f'VARCHAR({size})'
    
    # Recherche avec DECIMAL(n,m)
    decimal_match = re.match(r'decimal\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)', type_clean)
    if decimal_match:
        precision = int(decimal_match.group(1))
        scale = int(decimal_match.group(2))
        return f'DECIMAL({precision},{scale})'
    
    # Types contenant certains mots-clés
    if any(keyword in type_clean for keyword in ['text', 'texte', 'long']):
        return 'TEXT'
    elif any(keyword in type_clean for keyword in ['int', 'entier', 'number']):
        return 'INTEGER'
    elif any(keyword in type_clean for keyword in ['float', 'decimal', 'double']):
        return 'DECIMAL(15,6)'
    elif any(keyword in type_clean for keyword in ['date', 'temps']):
        return 'DATE'
    elif any(keyword in type_clean for keyword in ['bool', 'vrai', 'faux']):
        return 'BOOLEAN'
    
    return None

def detect_column_type(clean_values: list, csv_separator: str = ';') -> str:
    """
    Détection universelle et intelligente du type SQL pour une colonne.
    Basée uniquement sur l'analyse des données avec marges x8.
    
    Args:
        clean_values: Liste des valeurs nettoyées de la colonne
        csv_separator: Séparateur CSV utilisé (';' ou ',')
    
    Returns:
        Type SQL approprié avec marges x8 de sécurité
    """
    if not clean_values:
        return 'VARCHAR(255)'
    
    # Analyse de base
    max_len = max(len(str(v)) for v in clean_values)
    
    # Test numérique ultra-strict
    all_numeric = True
    has_decimals = False
    
    for val in clean_values:
        val_str = str(val).strip()
        
        # Test numérique selon le séparateur
        if csv_separator == ';':
            # Format français : virgule = décimal
            if not re.match(r'^-?\d+(,\d*)?$', val_str.replace(' ', '')):
                all_numeric = False
                break
            if ',' in val_str:
                has_decimals = True
        else:
            # Format anglais : point = décimal
            if not re.match(r'^-?\d+(\.\d*)?$', val_str.replace(' ', '')):
                all_numeric = False
                break
            if '.' in val_str:
                has_decimals = True
    
    # Décision finale
    if all_numeric:
        return 'DECIMAL(15,6)' if has_decimals else 'INTEGER'
    else:
        # VARCHAR avec marges x8 pures basées uniquement sur les données
        if max_len <= 5:
            return 'VARCHAR(40)'    # Marge x8
        elif max_len <= 10:
            return 'VARCHAR(80)'    # Marge x8
        elif max_len <= 25:
            return 'VARCHAR(200)'   # Marge x8
        elif max_len <= 50:
            return 'VARCHAR(400)'   # Marge x8
        elif max_len <= 100:
            return 'VARCHAR(800)'   # Marge x8
        else:
            return 'TEXT'

def detect_column_type_with_column_name(clean_values: list, csv_separator: str, column_name: str) -> str:
    """
    Détection universelle et intelligente du type SQL avec prise en compte du nom de colonne.
    
    Args:
        clean_values: Liste des valeurs nettoyées de la colonne
        csv_separator: Séparateur CSV utilisé (';' ou ',')
        column_name: Nom de la colonne pour appliquer des règles spécifiques
    
    Returns:
        Type SQL approprié avec règles intelligentes basées sur le nom
    """
    col_lower = column_name.lower()
    
    # RÈGLE SPÉCIALE 1 : Colonnes de codes individuels → VARCHAR(50)
    if ('code' in col_lower and 
        not col_lower.startswith('codes_') and  # Exclure codes_postaux
        not 'liste' in col_lower and           # Exclure autres listes
        not 'multiple' in col_lower):          # Exclure codes multiples
        return 'VARCHAR(50)'
    
    # RÈGLE SPÉCIALE 2 : Listes de codes → VARCHAR(200) minimum
    if (col_lower.startswith('codes_') or 
        ('code' in col_lower and ('liste' in col_lower or 'multiple' in col_lower))):
        # Analyser les données pour voir si VARCHAR(200) suffit
        base_type = detect_column_type(clean_values, csv_separator)
        if base_type.startswith('VARCHAR'):
            try:
                detected_size = int(base_type.split('(')[1].split(')')[0])
                # Prendre le maximum entre 200 et la taille détectée
                return f'VARCHAR({max(200, detected_size)})'
            except:
                return 'VARCHAR(200)'
        elif base_type == 'TEXT':
            return 'TEXT'
        else:
            return 'VARCHAR(200)'  # Sécurité par défaut
    
    # Sinon, utiliser la détection normale basée sur les données
    return detect_column_type(clean_values, csv_separator)

def parse_csv_line(line: str, separator: str) -> list:
    """Parse intelligente d'une ligne CSV avec gestion des guillemets."""
    import csv
    import io
    
    try:
        reader = csv.reader(io.StringIO(line), delimiter=separator, quotechar='"')
        return next(reader)
    except:
        return line.split(separator)

# Fonction de génération SQL SIMPLIFIÉE
def generate_sql_from_metadata(table_name: str) -> str:
    """Génère le script SQL d'import basé sur les métadonnées."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM metadata WHERE nom_table = %s", (table_name,))
        result = cursor.fetchone()
        
        if not result:
            return f"❌ Table '{table_name}' non trouvée dans les métadonnées"
        
        columns = [desc[0] for desc in cursor.description]
        metadata = dict(zip(columns, result))
        
        # Extraction des infos principales
        nom_table = metadata.get('nom_table', 'unknown_table')
        schema = metadata.get('schema', 'public')
        description = metadata.get('description', '')
        producteur = metadata.get('producteur', '')
        
        # Récupération de la structure CSV
        contenu_csv = metadata.get('contenu_csv', {})
        if not contenu_csv or 'header' not in contenu_csv:
            return f"❌ Structure CSV non disponible pour '{table_name}'"
        
        colonnes = contenu_csv['header']
        separateur = contenu_csv.get('separator', ';')
        donnees_exemple = contenu_csv.get('data', [])
        
        # Affichage de debug
        st.write(f"🔍 DEBUG: Colonnes trouvées: {len(colonnes)}")
        st.write(f"🔍 DEBUG: Données d'exemple: {len(donnees_exemple)} lignes")
        
        # Génération du SQL
        sql = f"""-- =====================================================================================
-- SCRIPT D'IMPORT POUR LA TABLE {nom_table}
-- =====================================================================================
-- Producteur: {producteur}
-- Schema: {schema}
-- Genere automatiquement le {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- 
-- RÈGLES DE DÉTECTION DES TYPES :
-- 1. Priorité aux types définis dans le dictionnaire des variables
-- 2. Codes individuels (code_insee, dep_code...) → VARCHAR(50) (gestion ZZZZZZZZZ)
-- 3. Listes de codes (codes_postaux...) → VARCHAR(200) minimum selon données
-- 4. Analyse des données avec marges de sécurité x8
-- =====================================================================================

-- 1. Suppression de la table existante (si elle existe)
DROP TABLE IF EXISTS "{schema}"."{nom_table}";

-- 2. Creation de la table
CREATE TABLE "{schema}"."{nom_table}" (
"""
        
        # Traitement des colonnes avec debug
        cols = []
        for i, col in enumerate(colonnes):
            col_clean = col.strip()
            
            # Récupération des valeurs d'exemple pour cette colonne
            sample_values = [row[i] if len(row) > i else None for row in donnees_exemple]
            clean_values = [str(v).strip() for v in sample_values if v is not None and str(v).strip()]
            
            # Récupération du dictionnaire des variables s'il existe
            dictionnaire = metadata.get('dictionnaire', {})
            dict_data = dictionnaire.get('data', []) if dictionnaire else []
            
            # ==================================================================================
            # PRIORITÉ 1 : TYPES DÉFINIS PAR LE PRODUCTEUR DANS LE DICTIONNAIRE DES VARIABLES
            # ==================================================================================
            
            producteur_type = None
            if dict_data and len(dict_data) > 0:
                # Liste complète des libellés possibles pour identifier une colonne de type
                type_column_labels = [
                    'type', 'data type', 'datatype', 'data_type', 
                    'field type', 'fieldtype', 'field_type',
                    'column type', 'column_type', 'columndatatype', 'column_data_type',
                    'valuetype', 'variable datatype', 'value_type', 'value_data_type', 
                    'variable_data_type', 'type de donnée', 'type de données', 'type_donnee'
                ]
                
                # MÉTHODE 1: Recherche par header du dictionnaire (si présent)
                dict_headers = dict_data[0] if len(dict_data) > 0 else []
                type_column_index = None
                data_start_index = 0  # Par défaut, pas de header
                
                # Vérifier si la première ligne semble être un header
                if dict_headers and len(dict_headers) >= 2:
                    first_row_seems_header = any(
                        str(header).strip().lower() in type_column_labels 
                        for header in dict_headers
                    )
                    
                    if first_row_seems_header:
                        data_start_index = 1  # Ignorer la première ligne (header)
                        # Chercher l'index de la colonne de type
                        for i, header in enumerate(dict_headers):
                            header_clean = str(header).strip().lower()
                            if header_clean in type_column_labels:
                                type_column_index = i
                                break
                
                # MÉTHODE 2: Recherche de la ligne correspondant à notre colonne
                for dict_row in dict_data[data_start_index:]:  # Utiliser l'index approprié
                    if len(dict_row) >= 1 and dict_row[0].strip().lower() == col.lower():
                        # DEBUG: Afficher la ligne du dictionnaire pour cette colonne
                        if col_clean.lower() == 'dep_nom':
                            st.write(f"🔍 DEBUG dep_nom - Ligne dictionnaire: {dict_row}")
                            st.write(f"🔍 DEBUG dep_nom - Headers dictionnaire: {dict_headers}")
                            st.write(f"🔍 DEBUG dep_nom - Index colonne type: {type_column_index}")
                        
                        # Si on a trouvé une colonne de type définie
                        if type_column_index is not None and len(dict_row) > type_column_index:
                            type_value = str(dict_row[type_column_index]).strip()
                            if type_value and type_value.lower() not in ['', 'nan', 'null', 'none']:
                                # Normalisation et validation du type
                                producteur_type = normalize_data_type(type_value)
                                if col_clean.lower() == 'dep_nom':
                                    st.write(f"🔍 DEBUG dep_nom - Type brut trouvé: '{type_value}' → normalisé: '{producteur_type}'")
                        
                        # MÉTHODE 3: Recherche dans toutes les colonnes si pas trouvé via header
                        if not producteur_type:
                            for type_field in dict_row[1:]:  # À partir de la 2ème colonne
                                type_str = str(type_field).strip()
                                if type_str:
                                    normalized_type = normalize_data_type(type_str)
                                    if normalized_type:
                                        producteur_type = normalized_type
                                        if col_clean.lower() == 'dep_nom':
                                            st.write(f"🔍 DEBUG dep_nom - Type trouvé par scan: '{type_str}' → '{producteur_type}'")
                                        break
                        break
            
            # ==================================================================================
            # PRIORITÉ 2 : ANALYSE CSV ULTRA-SÉCURISÉE SI PAS DE TYPE DU PRODUCTEUR
            # ==================================================================================
            
            # DEBUG spécial pour dep_nom
            if col_clean.lower() == 'dep_nom':
                st.write(f"🔍 DEBUG dep_nom - Échantillon CSV: {clean_values[:5]}")
                if clean_values:
                    max_len_found = max(len(str(v)) for v in clean_values)
                    st.write(f"🔍 DEBUG dep_nom - Longueur max trouvée: {max_len_found}")
            
            # ÉTAPE 1: Si le producteur a défini un type, l'utiliser en priorité absolue
            if producteur_type:
                sql_type = producteur_type
                if col_clean.lower() == 'dep_nom':
                    st.write(f"🔍 DEBUG dep_nom - UTILISATION TYPE PRODUCTEUR: {sql_type}")
            else:
                # ÉTAPE 2: Analyse CSV avec règles intelligentes (nom de colonne + données)
                sql_type = detect_column_type_with_column_name(clean_values, separateur, col_clean)
                
                # Debug pour les colonnes de codes
                col_lower = col_clean.lower()
                if ('code' in col_lower and 
                    not col_lower.startswith('codes_') and 
                    not 'liste' in col_lower and 
                    not 'multiple' in col_lower):
                    st.write(f"🔍 DEBUG {col_clean} - Code individuel détecté → VARCHAR(50)")
                elif (col_lower.startswith('codes_') or 
                      ('code' in col_lower and ('liste' in col_lower or 'multiple' in col_lower))):
                    st.write(f"🔍 DEBUG {col_clean} - Liste de codes détectée → VARCHAR(200) minimum")
                
                if col_clean.lower() == 'dep_nom':
                    st.write(f"🔍 DEBUG dep_nom - Type détecté final: {sql_type}")
            
            cols.append(f'    "{col_clean}" {sql_type}')
        
        sql += ",\n".join(cols)
        sql += "\n);\n"
        
        # Description
        if description:
            desc_lines = description.replace('\r\n', '\n').replace('\r', '\n').split('\n')
            sql += "\n-- ====================================================================================="
            sql += "\n-- DESCRIPTION DES DONNEES"
            sql += "\n-- ====================================================================================="
            for line in desc_lines:
                sql += f"\n-- {line}"
            sql += "\n-- ====================================================================================="
        
        conn.close()
        return sql
        
    except Exception as e:
        st.error(f"❌ Erreur lors de la génération : {str(e)}")
        return f"❌ Erreur lors de la génération : {str(e)}"

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
        "", "commune", "IRIS", "carreau", "adresse", "EPCI", "département", "région", "bassin de vie", "autre"
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
        "economie", "education", "energie", "environnement", 
        "geo", "logement", "mobilite", "population", "reseau", "securite"
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
col_btn1, col_btn2 = st.columns(2)
with col_btn1:
submitted = st.button("Sauvegarder les métadonnées")
with col_btn2:
    generate_sql = st.button("Générer le script SQL d'import", help="Génère automatiquement le script SQL d'import basé sur les métadonnées")

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

            # Sauvegarde locale en JSON
            try:
                json_path = os.path.join("metadata", f"{nom_table}.json")
                os.makedirs("metadata", exist_ok=True)
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=4)
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
            except Exception as e:
                st.error(f"Erreur lors de la sauvegarde locale en TXT : {str(e)}")
                
        except Exception as e:
            st.error(f"Erreur inattendue : {str(e)}")
            st.error("Veuillez vérifier les logs pour plus de détails.")

# Traitement du bouton de génération SQL
if generate_sql:
    if not nom_table:
        st.error("Veuillez d'abord saisir un nom de table pour générer le script SQL")
    else:
        with st.spinner("Génération du script SQL en cours..."):
            sql_script = generate_sql_from_metadata(nom_table)
            
            if sql_script.startswith("❌"):
                st.error(sql_script)
            else:
                st.success("🎉 Script SQL généré avec succès !")
                
                # Affichage du script avec possibilité de copier
                st.subheader("📄 Script SQL d'import généré")
                st.code(sql_script, language="sql")
                
                # Bouton de téléchargement
                st.download_button(
                    label="💾 Télécharger le script SQL",
                    data=sql_script,
                    file_name=f"import_{nom_table}.sql",
                    mime="text/plain"
                )
                
                st.info("""
                ### 📋 Instructions d'utilisation :
                1. **Téléchargez** le script SQL ci-dessus
                2. **Modifiez** le chemin du fichier CSV dans la section COPY
                3. **Exécutez** le script dans votre outil de gestion PostgreSQL (DBeaver, pgAdmin, etc.)
                """)

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