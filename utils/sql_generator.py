"""
Module de génération automatique de scripts SQL d'import
Contient toutes les fonctions nécessaires pour analyser les métadonnées
et générer des scripts SQL PostgreSQL optimisés.
"""

import streamlit as st
import pandas as pd
import re
import io
import csv
from datetime import datetime
from typing import List, Optional, Tuple
from .db_utils import get_db_connection


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
        # CORRECTION : Retirer 'temps' générique pour éviter "temps partiel" → DATE
        # 'temps': 'TIMESTAMP',  # Trop générique, commenté
        
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
    
    # Types contenant certains mots-clés (patterns PRÉCIS pour éviter les faux positifs)
    if any(keyword in type_clean for keyword in ['text', 'texte', 'long']):
        return 'TEXT'
    elif any(keyword in type_clean for keyword in ['int', 'entier', 'number']):
        return 'INTEGER'
    elif any(keyword in type_clean for keyword in ['float', 'decimal', 'double']):
        return 'DECIMAL(15,6)'
    elif any(keyword in type_clean for keyword in ['date', 'datetime', 'timestamp']):
        # CORRECTION : Retirer 'temps' générique qui capture "temps partiel"
        # Être plus spécifique pour éviter les faux positifs
        return 'DATE'
    elif any(keyword in type_clean for keyword in ['bool', 'vrai', 'faux']):
        return 'BOOLEAN'
    
    return None


def detect_column_type(clean_values: list, csv_separator: str = ';') -> str:
    """
    Détection universelle et intelligente du type SQL pour une colonne.
    Basée uniquement sur l'analyse des données avec marges x8.
    NOUVELLE RÈGLE : Protection INSEE anti-ZZZZZZ automatique.
    
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
    
    # NOUVELLE RÈGLE PRIORITAIRE : Détection explicite des valeurs de masquage INSEE
    has_insee_masking = False
    insee_masking_patterns = ['ZZZZZZ', 'ZZZZZ', 'ZZZZ', 'ZZZ', 'XX', 'XXX', 'XXXX', 's', 'SECRET']
    
    for val in clean_values:
        val_str = str(val).strip().upper()
        if val_str in insee_masking_patterns:
            has_insee_masking = True
            break
    
    # Si masquage INSEE détecté, forcer VARCHAR même si les autres valeurs sont numériques
    if has_insee_masking:
        if max_len <= 10:
            return 'VARCHAR(50)'    # Sécurité pour codes + masquage
        elif max_len <= 25:
            return 'VARCHAR(200)'   
        else:
            return 'TEXT'
    
    # Test numérique ultra-strict (seulement si pas de masquage INSEE)
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


def detect_type_from_description(description: str) -> str:
    """
    Détection universelle du type SQL basée sur l'analyse sémantique des descriptions.
    Cette fonction exploite les descriptions pour identifier les codes/identifiants (protection anti-ZZZZZZ).
    
    Args:
        description: Description de la variable (libellé + description longue)
        
    Returns:
        Type SQL suggéré ou None si aucune détection claire
    """
    if not description:
        return None
        
    desc_lower = description.lower()
    
    # RÈGLE 1 PRIORITAIRE: Comptages → INTEGER (plus spécifique, doit venir AVANT les codes)
    counting_keywords = [
        'nombre de', 'count', 'total', 'effectif', 'population', 
        'nb de', 'quantité', 'quantite', 'effectifs'
    ]
    if any(keyword in desc_lower for keyword in counting_keywords):
        return 'INTEGER'
    
    # RÈGLE 2: Taux/Pourcentages/Ratios → DECIMAL (avant les codes aussi)
    ratio_keywords = [
        'taux', 'pourcentage', 'ratio', 'rate', 'part de', 'proportion',
        'indice', 'moyenne', 'median', 'percentile'
    ]
    if any(keyword in desc_lower for keyword in ratio_keywords):
        return 'DECIMAL(15,6)'
    
    # RÈGLE 3: Codes/Identifiants → VARCHAR (protection universelle anti-ZZZZZZ)
    # Attention : exclure "aide"/"aidé" qui ne sont pas des codes mais des catégories
    code_keywords = [
        'code', 'codes', 'identifiant', 'identifier', 'numéro', 'numero', 
        'référence', 'reference', 'clé', 'cle', 'key', 'id', 'siren', 'siret'
    ]
    # Vérification plus stricte : ne pas confondre "aide" avec "code"
    if any(keyword in desc_lower for keyword in code_keywords):
        # Exclure les faux positifs comme "emplois aidés", "aides familiaux"
        false_positives = ['emplois aidés', 'aides familiaux', 'emploi aidé', 'aide familial']
        if not any(fp in desc_lower for fp in false_positives):
            return 'VARCHAR(50)'
    
    # RÈGLE 4: Libellés/Noms → TEXT ou VARCHAR
    text_keywords = [
        'libellé', 'libelle', 'nom de', 'intitulé', 'intitule', 
        'designation', 'désignation', 'appellation'
    ]
    if any(keyword in desc_lower for keyword in text_keywords):
        return 'VARCHAR(255)'  # Pour les libellés courts/moyens
    
    return None  # Aucune détection sémantique claire


def detect_column_type_with_column_name(clean_values: list, csv_separator: str, column_name: str) -> str:
    """
    Détection universelle et intelligente du type SQL avec prise en compte du nom de colonne.
    Utilise des patterns PRÉCIS pour éviter les faux positifs.
    
    Args:
        clean_values: Liste des valeurs nettoyées de la colonne
        csv_separator: Séparateur CSV utilisé (';' ou ',')
        column_name: Nom de la colonne pour appliquer des règles spécifiques
    
    Returns:
        Type SQL approprié avec règles intelligentes basées sur le nom
    """
    col_lower = column_name.lower()
    
    # RÈGLE UNIVERSELLE 1 : Détection PRÉCISE des identifiants et codes
    # Utilisation de regex pour des patterns exacts et éviter les faux positifs
    identifier_patterns = [
        # Codes explicites (patterns exacts ou délimités)
        r'^code$', r'^cod$', r'^id$', r'_id$', r'^id_', r'_code$', r'^code_',
        r'^identifier$', r'^identifiant$',
        # Codes géographiques INSEE (patterns précis uniquement)
        r'^iris$', r'^triris$', r'^codgeo$', r'^geocode$', 
        r'^commune$', r'^com$', r'^dep$', r'^reg$', r'^uu\d*$',
        # Codes d'entreprises (patterns précis)
        r'^siren$', r'^siret$', r'^nic$', r'^ape$', r'^naf$', r'^tva$',
        # Autres identifiants (patterns délimités)
        r'^reference$', r'^ref$', r'^numero$', r'^num$', r'^matricule$', 
        r'^cle$', r'^key$', r'_ref$', r'_key$',
        # Libellés géographiques (aussi à protéger)
        r'^libcom$', r'^libiris$', r'^typ_iris$', r'^modif_iris$', r'^lab_iris$',
    ]
    
    # Si le nom de colonne matche un pattern d'identifiant PRÉCIS → VARCHAR(50)
    if any(re.search(pattern, col_lower) for pattern in identifier_patterns):
        return 'VARCHAR(50)'
    
    # RÈGLE UNIVERSELLE 2 : Listes de codes → VARCHAR(200) minimum
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


def detect_column_type_intelligent_universal(clean_values: list, csv_separator: str, column_name: str, dict_row: list = None) -> str:
    """
    Détection universelle et intelligente selon la hiérarchie de priorités définie.
    
    HIÉRARCHIE DES PRIORITÉS :
    1. Type explicite dans le dictionnaire des variables
    2. Analyse sémantique des descriptions (protection anti-ZZZZZZ universelle)
    3. Analyse des données réelles
    4. Patterns de noms de colonnes (fallback uniquement)
    
    Args:
        clean_values: Liste des valeurs nettoyées de la colonne
        csv_separator: Séparateur CSV utilisé
        column_name: Nom de la colonne
        dict_row: Ligne du dictionnaire des variables [nom, libelle, description, ...]
        
    Returns:
        Type SQL approprié selon la hiérarchie
    """
    
    # PROTECTION GÉOGRAPHIQUE ABSOLUE : Identifiants géographiques critiques
    # Ces colonnes DOIVENT être VARCHAR même si les données semblent numériques (protection anti-ZZZZZZ)
    geographic_critical_patterns = [
        r'^iris$', r'^triris$', r'^codgeo$', r'^geocode$', 
        r'^commune$', r'^com$', r'^dep$', r'^reg$', r'^uu\d*$',
        r'^libcom$', r'^libiris$', r'^typ_iris$', r'^modif_iris$', r'^lab_iris$'
    ]
    col_lower = column_name.lower()
    if any(re.search(pattern, col_lower) for pattern in geographic_critical_patterns):
        return 'VARCHAR(50)'  # Protection absolue
    
    # PRIORITÉ 1 : Type explicite dans le dictionnaire des variables
    if dict_row and len(dict_row) > 0:
        # Rechercher un type explicite dans les colonnes du dictionnaire
        for field in dict_row[1:]:  # À partir de la 2ème colonne
            field_str = str(field).strip()
            if field_str:
                explicit_type = normalize_data_type(field_str)
                if explicit_type:
                    return explicit_type
    
    # PRIORITÉ 2 : Analyse sémantique des descriptions (protection universelle anti-ZZZZZZ)
    if dict_row and len(dict_row) > 1:
        # Concaténer libellé + description pour l'analyse sémantique
        description_complete = ' '.join(str(field) for field in dict_row[1:])
        semantic_type = detect_type_from_description(description_complete)
        if semantic_type:
            return semantic_type
    
    # PRIORITÉ 3 : Analyse des données réelles
    data_based_type = detect_column_type(clean_values, csv_separator)
    
    # PRIORITÉ 4 : Affiner avec patterns de noms seulement si nécessaire
    # (uniquement pour les cas ambigus de VARCHAR)
    if data_based_type.startswith('VARCHAR') and len(clean_values) > 0:
        # Vérifier si les patterns de noms peuvent affiner le type
        name_based_type = detect_column_type_with_column_name(clean_values, csv_separator, column_name)
        
        # Si le pattern de nom suggère un type plus précis, l'utiliser
        if name_based_type != data_based_type and name_based_type in ['VARCHAR(50)', 'VARCHAR(200)']:
            return name_based_type
    
    return data_based_type


def parse_csv_line(line: str, separator: str) -> list:
    """Parse intelligente d'une ligne CSV avec gestion des guillemets."""
    try:
        reader = csv.reader(io.StringIO(line), delimiter=separator, quotechar='"')
        return next(reader)
    except:
        return line.split(separator)


def generate_sql_from_metadata(table_name: str, debug_mode: bool = False) -> str:
    """
    Génère le script SQL d'import basé sur les métadonnées.
    
    Args:
        table_name: Nom de la table pour laquelle générer le script
        debug_mode: Si True, affiche les informations de debug via Streamlit
    
    Returns:
        Script SQL complet ou message d'erreur
    """
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
        
        # Affichage de debug optionnel
        if debug_mode:
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
-- NOUVELLE HIÉRARCHIE DE DÉTECTION UNIVERSELLE ET INTELLIGENTE :
-- 1. Type explicite dans le dictionnaire des variables (si disponible)
-- 2. Analyse sémantique des descriptions (protection anti-ZZZZZZ universelle)
-- 3. Analyse des données réelles (avec détection masquage)
-- 4. Patterns de noms de colonnes (fallback précis uniquement)
-- =====================================================================================

-- 1. Suppression de la table existante (si elle existe)
DROP TABLE IF EXISTS "{schema}"."{nom_table}";

-- 2. Creation de la table
CREATE TABLE "{schema}"."{nom_table}" (
"""
        
        # Récupération du dictionnaire des variables s'il existe
        dictionnaire = metadata.get('dictionnaire', {})
        dict_data = dictionnaire.get('data', []) if dictionnaire else []
        
        # Traitement des colonnes avec la nouvelle logique intelligente
        cols = []
        for i, col in enumerate(colonnes):
            col_clean = col.strip()
            
            # Récupération des valeurs d'exemple pour cette colonne
            sample_values = [row[i] if len(row) > i else None for row in donnees_exemple]
            clean_values = [str(v).strip() for v in sample_values if v is not None and str(v).strip()]
            
            # Recherche de la ligne correspondante dans le dictionnaire des variables
            dict_row = None
            if dict_data:
                for row in dict_data:
                    if len(row) >= 1 and row[0].strip().lower() == col.lower():
                        dict_row = row
                        break
            
            # NOUVELLE LOGIQUE UNIVERSELLE : Utilisation de la hiérarchie de priorités
            sql_type = detect_column_type_intelligent_universal(
                clean_values=clean_values,
                csv_separator=separateur,
                column_name=col_clean,
                dict_row=dict_row
            )
            
            # Debug optionnel
            if debug_mode:
                if dict_row:
                    st.write(f"🔍 DEBUG {col_clean} - Dictionnaire: {dict_row}")
                st.write(f"🔍 DEBUG {col_clean} - Type détecté: {sql_type}")
            
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
        error_msg = f"❌ Erreur lors de la génération : {str(e)}"
        if debug_mode:
            st.error(error_msg)
        return error_msg


def generate_sql_download_button(table_name: str, button_label: str = "💾 Télécharger le script SQL") -> None:
    """
    Génère et affiche un bouton de téléchargement pour le script SQL.
    
    Args:
        table_name: Nom de la table pour laquelle générer le script
        button_label: Texte du bouton de téléchargement
    """
    sql_script = generate_sql_from_metadata(table_name, debug_mode=False)
    
    if sql_script.startswith("❌"):
        st.error(sql_script)
    else:
        st.download_button(
            label=button_label,
            data=sql_script,
            file_name=f"import_{table_name}.sql",
            mime="text/plain"
        )


def display_sql_generation_interface(table_name: str, debug_mode: bool = True) -> None:
    """
    Affiche l'interface complète de génération SQL avec le script et les boutons.
    
    Args:
        table_name: Nom de la table pour laquelle générer le script
        debug_mode: Si True, affiche les informations de debug
    """
    with st.spinner("Génération du script SQL en cours..."):
        sql_script = generate_sql_from_metadata(table_name, debug_mode=debug_mode)
        
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
                file_name=f"import_{table_name}.sql",
                mime="text/plain"
            )
            
            st.info("""
            ### 📋 Instructions d'utilisation :
            1. **Téléchargez** le script SQL ci-dessus
            2. **Modifiez** le chemin du fichier CSV dans la section COPY
            3. **Exécutez** le script dans votre outil de gestion PostgreSQL (DBeaver, pgAdmin, etc.)
            """) 