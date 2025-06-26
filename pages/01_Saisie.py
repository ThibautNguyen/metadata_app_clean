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

def detect_column_type(clean_values: list, csv_separator: str, dict_type_hint: str = None) -> str:
    """
    Détection universelle et robuste du type SQL pour une colonne.
    
    Args:
        clean_values: Liste des valeurs nettoyées de la colonne
        csv_separator: Séparateur CSV utilisé (';' ou ',')
        dict_type_hint: Suggestion du dictionnaire des variables (optionnel)
    
    Returns:
        Type SQL approprié (VARCHAR(x), INTEGER, DECIMAL, TEXT, etc.)
    """
    if not clean_values:
        return 'VARCHAR(255)'  # Défaut sécurisé
    
    # ÉTAPE 1: Analyse statistique des données
    max_len = max(len(str(v)) for v in clean_values)
    min_len = min(len(str(v)) for v in clean_values)
    avg_len = sum(len(str(v)) for v in clean_values) / len(clean_values)
    variance_len = sum((len(str(v)) - avg_len) ** 2 for v in clean_values) / len(clean_values)
    
    # ÉTAPE 2: Détection des patterns à haut risque
    list_pattern_count = 0
    long_text_count = 0
    high_risk_patterns = []
    
    for val in clean_values:
        val_str = str(val)
        # Listes (multiples virgules)
        if val_str.count(',') >= 2:
            list_pattern_count += 1
        # Texte libre long
        if val_str.count(' ') >= 3 and len(val_str) > 30:
            long_text_count += 1
        # Texte très long
        if len(val_str) > 100:
            high_risk_patterns.append('texte_tres_long')
    
    # Seuils de détection des patterns à risque
    if list_pattern_count > len(clean_values) * 0.2:
        high_risk_patterns.append('liste_frequente')
    if long_text_count > len(clean_values) * 0.3:
        high_risk_patterns.append('texte_libre_frequent')
    if variance_len > (avg_len * 2) and avg_len > 20:
        high_risk_patterns.append('longueurs_tres_variables')
    
    # Si patterns à risque détectés → TEXT immédiatement
    if high_risk_patterns:
        return 'TEXT'
    
    # ÉTAPE 3: Test numérique intelligent selon le séparateur CSV
    all_numeric = True
    has_decimals = False
    max_int = 0
    
    for val in clean_values:
        val_str = str(val).strip()
        
        # Logique adaptée au séparateur CSV
        if csv_separator == ';':
            # Format français : virgule = décimal
            val_clean = val_str.replace(' ', '').strip()
            if not re.match(r'^-?\d+(,\d*)?$', val_clean):  # Accepte entiers ET décimaux
                all_numeric = False
                break
            val_for_calc = val_clean.replace(',', '.')
        else:
            # Format anglais : point = décimal
            val_clean = val_str.replace(' ', '').strip()
            if not re.match(r'^-?\d+(\.\d*)?$', val_clean):  # Accepte entiers ET décimaux
                all_numeric = False
                break
            val_for_calc = val_clean
        
        try:
            num_val = float(val_for_calc)
            # Détection des décimaux selon le format d'origine
            if (',' in val_str and csv_separator == ';') or ('.' in val_str and csv_separator != ';'):
                has_decimals = True
            else:
                max_int = max(max_int, abs(int(num_val)))
        except (ValueError, OverflowError):
            all_numeric = False
            break
    
    # ÉTAPE 4: Décision basée sur l'analyse numérique
    if all_numeric and len(clean_values) > 0:
        if has_decimals:
            base_type = 'DECIMAL(15,6)'
        else:
            # Choix conservateur pour les entiers
            if max_int <= 2147483647:
                base_type = 'INTEGER'
            else:
                base_type = 'BIGINT'
    else:
        # VARCHAR adaptatif avec marges de sécurité importantes
        if max_len <= 5:
            base_type = 'VARCHAR(20)'       # Marge x4
        elif max_len <= 10:
            base_type = 'VARCHAR(50)'       # Marge x5
        elif max_len <= 25:
            base_type = 'VARCHAR(100)'      # Marge x4
        elif max_len <= 50:
            base_type = 'VARCHAR(200)'      # Marge x4
        elif max_len <= 100:
            base_type = 'VARCHAR(500)'      # Marge x5
        elif max_len <= 200:
            base_type = 'VARCHAR(1000)'     # Marge x5
        else:
            base_type = 'TEXT'
    
    # ÉTAPE 5: Application intelligente du hint du dictionnaire
    if dict_type_hint:
        if dict_type_hint == 'DATE':
            return 'DATE'  # Toujours faire confiance pour les dates
        elif dict_type_hint == 'TEXT':
            return 'TEXT'  # Toujours prendre le plus permissif
        elif dict_type_hint == 'BOOLEAN':
            # Vérifier la cohérence avec les données
            boolean_values = {'oui', 'non', 'true', 'false', '1', '0', 'vrai', 'faux', 'yes', 'no'}
            if all(str(v).lower().strip() in boolean_values for v in clean_values):
                return 'BOOLEAN'
        elif dict_type_hint.startswith('VARCHAR'):
            # Prendre la taille la plus grande entre dictionnaire et analyse
            try:
                dict_size = int(dict_type_hint.split('(')[1].split(')')[0])
                if base_type.startswith('VARCHAR'):
                    current_size = int(base_type.split('(')[1].split(')')[0])
                    return f'VARCHAR({max(dict_size, current_size)})'
                elif base_type not in ['TEXT', 'DECIMAL(15,6)', 'INTEGER', 'BIGINT']:
                    return dict_type_hint
            except:
                pass  # Si erreur de parsing, ignorer le hint
    
    return base_type

def parse_csv_line(line: str, separator: str) -> list:
    """
    Parse intelligente d'une ligne CSV avec gestion des guillemets.
    Utilisée pour CSV ET dictionnaire des variables.
    
    Args:
        line: Ligne CSV à parser
        separator: Séparateur utilisé (';' ou ',')
    
    Returns:
        Liste des valeurs parsées
    """
    import csv
    import io
    
    try:
        # Utiliser le module csv standard pour un parsing correct
        reader = csv.reader(io.StringIO(line), delimiter=separator, quotechar='"')
        return next(reader)
    except:
        # Fallback : split simple si le parsing CSV échoue
        return line.split(separator)

# Fonction de génération SQL simplifiée
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
        
        # Récupération du dictionnaire des variables s'il existe
        dictionnaire = metadata.get('dictionnaire', {})
        dict_data = dictionnaire.get('data', []) if dictionnaire else []
        
        # IMPORTANT : récupération du séparateur CSV pour la détection numérique
        csv_separator = separateur
        
        # Génération du SQL basique
        sql = f"""-- =====================================================================================
-- SCRIPT D'IMPORT POUR LA TABLE {nom_table}
-- =====================================================================================
-- Producteur: {producteur}
-- Schema: {schema}
-- Genere automatiquement le {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- =====================================================================================

-- 1. Suppression de la table existante (si elle existe)
DROP TABLE IF EXISTS "{schema}"."{nom_table}";

-- 2. Creation de la table
CREATE TABLE "{schema}"."{nom_table}" (
"""
        
        # Colonnes avec types basiques
        cols = []
        for i, col in enumerate(colonnes):
            col_clean = col.strip()
            # Récupération des valeurs d'exemple pour cette colonne
            sample_values = [row[i] if len(row) > i else None for row in donnees_exemple]
            clean_values = [str(v).strip() for v in sample_values if v is not None and str(v).strip()]
            
            # ALGORITHME UNIVERSEL ET ROBUSTE
            # Analyse du dictionnaire pour hints de type
            dict_type_hint = None
            if dict_data:
                # Chercher la colonne dans le dictionnaire
                for dict_row in dict_data:
                    if len(dict_row) >= 2 and dict_row[0].strip().lower() == col.lower():
                        description = dict_row[1].lower() if len(dict_row) > 1 else ""
                        modalites = dict_row[2].lower() if len(dict_row) > 2 else ""
                        
                        # Analyse du dictionnaire pour hints de type
                        desc_and_modalites = f"{description} {modalites}"
                        
                        # Détection basée sur la sémantique du dictionnaire
                        if any(x in desc_and_modalites for x in ['date', 'timestamp', 'temps', 'année', 'mois', 'jour']):
                            dict_type_hint = 'DATE'
                        elif any(x in desc_and_modalites for x in ['url', 'lien', 'http', 'www', 'site']):
                            dict_type_hint = 'TEXT'
                        elif any(x in desc_and_modalites for x in ['booléen', 'boolean', 'vrai', 'faux', 'oui', 'non']):
                            dict_type_hint = 'BOOLEAN'
                        elif any(x in desc_and_modalites for x in ['texte long', 'description', 'commentaire', 'note']):
                            dict_type_hint = 'TEXT'
                        # Si le dictionnaire indique des modalités courtes et limitées
                        elif modalites and len(modalites.split(',')) <= 10 and max(len(x.strip()) for x in modalites.split(',')) <= 50:
                            dict_type_hint = f"VARCHAR({max(50, max(len(x.strip()) for x in modalites.split(',')) + 10)})"
                        break
            
            # Détection intelligente du type avec la fonction unifiée
            if clean_values and all(v.startswith('http') for v in clean_values if v):
                # URLs détectées directement dans les données
                sql_type = 'TEXT'
            else:
                # Utilisation de la fonction unifiée de détection
                sql_type = detect_column_type(clean_values, csv_separator, dict_type_hint)
            
            cols.append(f'    "{col_clean}" {sql_type}')
        
        sql += ",\n".join(cols)
        sql += f"""
);
"""
        
        # Ajouter la description de façon sécurisée
        if description:
            # Nettoyer la description et la formatter ligne par ligne
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
        "", "commune", "IRIS", "carreau", "adresse", "EPCI", "département", "région", "autre"
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