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
        
        # Génération du SQL basique
        sql = f"""-- =====================================================================================
-- SCRIPT D'IMPORT POUR LA TABLE {nom_table}
-- =====================================================================================
-- Producteur: {producteur}
-- Schema: {schema}
-- Description: {description}
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
            
            # Type basique selon le nom de colonne + analyse des valeurs
            if any(x in col.lower() for x in ['code_insee', 'codgeo']):
                sql_type = 'VARCHAR(5)'
            elif any(x in col.lower() for x in ['code_dep', 'dep']):
                sql_type = 'VARCHAR(3)'
            elif any(x in col.lower() for x in ['code_reg', 'reg']):
                # Vérifier la longueur max dans les échantillons
                max_len = max(len(str(v)) for v in sample_values if v is not None) if sample_values else 2
                sql_type = f'VARCHAR({max(max_len + 1, 3)})'  # Au minimum 3, +1 de sécurité
            elif any(x in col.lower() for x in ['code_postal', 'postal']):
                sql_type = 'VARCHAR(10)'  # Codes postaux peuvent être complexes
            elif any(x in col.lower() for x in ['date']):
                sql_type = 'DATE'
            elif any(x in col.lower() for x in ['nom', 'libelle', 'designation']):
                # Calculer la longueur max des noms depuis les échantillons
                max_len = max(len(str(v)) for v in sample_values if v is not None) if sample_values else 100
                sql_type = f'VARCHAR({min(max(max_len + 50, 100), 500)})'  # Entre 100 et 500 caractères
            elif any(x in col.lower() for x in ['url', 'http', 'www']):
                sql_type = 'TEXT'  # URLs peuvent être très longues
            elif any(x in col.lower() for x in ['superficie', 'densite', 'altitude', 'latitude', 'longitude']):
                sql_type = 'DECIMAL(10,3)'  # Coordonnées et mesures
            elif any(x in col.lower() for x in ['population', 'nb_', 'nombre']):
                sql_type = 'INTEGER'
            elif any(x in col.lower() for x in ['type', 'statut', 'categorie', 'classe', 'niveau', 'grille', 'gentile', 'texte', 'taille', 'unite_urbaine']):
                # Colonnes contenant des catégories/classifications = toujours texte
                max_len = max(len(str(v)) for v in sample_values if v is not None) if sample_values else 100
                sql_type = f'VARCHAR({min(max(max_len + 20, 50), 255)})'
            else:
                # Analyser les valeurs pour déterminer le type
                if sample_values:
                    # Nettoyer les valeurs et retirer les None
                    clean_values = [str(v).strip() for v in sample_values if v is not None and str(v).strip()]
                    
                    if not clean_values:
                        sql_type = 'TEXT'
                    else:
                        # Vérifier si c'est numérique de manière plus stricte
                        numeric_count = 0
                        text_count = 0
                        
                        for val in clean_values:
                            # Test plus strict pour les nombres
                            try:
                                # Remplacer la virgule par un point pour les décimales françaises
                                val_normalized = val.replace(',', '.')
                                
                                # Vérifier que c'est bien un nombre (pas de lettres)
                                if re.match(r'^-?\d+\.?\d*$', val_normalized):
                                    float(val_normalized)
                                    numeric_count += 1
                                else:
                                    text_count += 1
                                    # Si on trouve du texte, on arrête l'analyse
                                    if len(val) > 10:  # Texte long = clairement pas numérique
                                        break
                            except (ValueError, TypeError):
                                text_count += 1
                                # Si on trouve du texte, on arrête l'analyse
                                if len(val) > 10:
                                    break
                        
                        # Décision du type basée sur l'analyse
                        if text_count > 0 or numeric_count == 0:
                            # C'est du texte
                            max_len = max(len(val) for val in clean_values)
                            if max_len <= 50:
                                sql_type = 'VARCHAR(100)'
                            elif max_len <= 255:
                                sql_type = 'VARCHAR(300)'
                            else:
                                sql_type = 'TEXT'
                        else:
                            # Tout semble numérique
                            has_decimals = any('.' in str(v).replace(',', '.') for v in clean_values)
                            if has_decimals:
                                sql_type = 'DECIMAL(10,3)'
                            else:
                                # Vérifier la taille des entiers
                                max_int = max(abs(int(float(str(v).replace(',', '.')))) for v in clean_values)
                                if max_int < 32767:
                                    sql_type = 'SMALLINT'
                                elif max_int < 2147483647:
                                    sql_type = 'INTEGER'
                                else:
                                    sql_type = 'BIGINT'
                else:
                    sql_type = 'TEXT'
            
            cols.append(f'    "{col_clean}" {sql_type}')
        
        sql += ",\n".join(cols)
        sql += f"""
);

-- 3. Import des donnees
-- ATTENTION: Modifier le chemin vers votre fichier CSV
-- Si erreur de taille de champ, ajustez les VARCHAR() selon vos donnees reelles
COPY "{schema}"."{nom_table}" FROM '/chemin/vers/votre/{nom_table}.csv'
WITH (FORMAT csv, HEADER true, DELIMITER '{separateur}', ENCODING 'UTF8');

-- 4. Verification de l'import
SELECT COUNT(*) as nb_lignes_importees FROM "{schema}"."{nom_table}";
SELECT * FROM "{schema}"."{nom_table}" LIMIT 5;

-- 5. En cas d'erreur de taille de champ, utilisez cette requete pour diagnostiquer :
-- SELECT column_name, max(length(column_name::text)) as max_length 
-- FROM "{schema}"."{nom_table}" GROUP BY column_name;
"""
        
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
    contenu_csv = st.text_area("Coller ici les 4 premières lignes du fichier CSV", height=150, key="extrait_csv")

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
                
                # DIAGNOSTIC : Afficher l'analyse des types
                st.subheader("🔍 Diagnostic de l'analyse des types")
                try:
                    conn = get_db_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM metadata WHERE nom_table = %s", (nom_table,))
                    result = cursor.fetchone()
                    
                    if result:
                        columns = [desc[0] for desc in cursor.description]
                        metadata = dict(zip(columns, result))
                        contenu_csv = metadata.get('contenu_csv', {})
                        
                        if 'header' in contenu_csv and 'data' in contenu_csv:
                            colonnes = contenu_csv['header']
                            donnees_exemple = contenu_csv.get('data', [])
                            
                            st.write("**Analyse colonne par colonne :**")
                            
                            for i, col in enumerate(colonnes):
                                sample_values = [row[i] if len(row) > i else None for row in donnees_exemple]
                                clean_values = [str(v).strip() for v in sample_values if v is not None and str(v).strip()]
                                
                                # Déterminer le type comme dans l'algorithme
                                if any(x in col.lower() for x in ['code_insee', 'codgeo']):
                                    detected_type = 'VARCHAR(5)'
                                elif any(x in col.lower() for x in ['code_dep', 'dep']):
                                    detected_type = 'VARCHAR(3)'
                                elif any(x in col.lower() for x in ['code_reg', 'reg']):
                                    max_len = max(len(str(v)) for v in sample_values if v is not None) if sample_values else 2
                                    detected_type = f'VARCHAR({max(max_len + 1, 3)})'
                                elif any(x in col.lower() for x in ['type', 'statut', 'categorie', 'classe', 'niveau', 'grille', 'gentile', 'texte', 'taille', 'unite_urbaine']):
                                    max_len = max(len(str(v)) for v in sample_values if v is not None) if sample_values else 100
                                    detected_type = f'VARCHAR({min(max(max_len + 20, 50), 255)})'
                                else:
                                    # Analyse numérique
                                    if clean_values:
                                        numeric_count = 0
                                        text_count = 0
                                        
                                        for val in clean_values[:5]:  # Limiter à 5 valeurs pour l'affichage
                                            try:
                                                val_normalized = val.replace(',', '.')
                                                if re.match(r'^-?\d+\.?\d*$', val_normalized):
                                                    float(val_normalized)
                                                    numeric_count += 1
                                                else:
                                                    text_count += 1
                                            except:
                                                text_count += 1
                                        
                                        if text_count > 0:
                                            max_len = max(len(val) for val in clean_values)
                                            if max_len <= 50:
                                                detected_type = 'VARCHAR(100)'
                                            elif max_len <= 255:
                                                detected_type = 'VARCHAR(300)'
                                            else:
                                                detected_type = 'TEXT'
                                        else:
                                            detected_type = 'INTEGER/DECIMAL'
                                    else:
                                        detected_type = 'TEXT'
                                
                                # Affichage
                                with st.expander(f"📋 {col} → {detected_type}"):
                                    st.write(f"**Échantillon de valeurs:** {clean_values[:3] if clean_values else 'Aucune'}")
                                    if len(clean_values) > 3:
                                        st.write(f"**Total de valeurs:** {len(clean_values)}")
                                    if clean_values:
                                        st.write(f"**Longueur max:** {max(len(str(v)) for v in clean_values)}")
                    
                    conn.close()
                except Exception as e:
                    st.error(f"Erreur lors du diagnostic: {e}")
                
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
                4. **Vérifiez** l'import avec les requêtes de contrôle à la fin du script
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
       - Copiez-collez les premières lignes du fichier CSV
       - Indiquez le séparateur utilisé (par défaut, point-virgule)
       - Ajoutez le dictionnaire des variables si le fichier CSV est disponible
    """)

# Pied de page
st.markdown("---")
st.markdown('<div style="text-align: center; color: #666;">© 2025 - Système de Gestion des Métadonnées</div>', unsafe_allow_html=True) 