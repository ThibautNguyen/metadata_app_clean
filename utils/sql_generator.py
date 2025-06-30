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
    
    # RÈGLE UNIVERSELLE 1 : Détection intelligente des identifiants et codes
    # Patterns universels pour tous types d'identifiants (pas seulement "code")
    identifier_patterns = [
        # Codes explicites
        'code', 'cod', 'id', 'identifier', 'identifiant',
        # Codes géographiques INSEE
        'iris', 'triris', 'codgeo', 'geocode', 'commune', 'com', 'dep', 'reg', 'uu',
        # Codes d'entreprises
        'siren', 'siret', 'nic', 'ape', 'naf', 'tva',
        # Autres identifiants
        'reference', 'ref', 'numero', 'num', 'n°', 'matricule', 'cle', 'key'
    ]
    
    # Si le nom de colonne contient un pattern d'identifiant → VARCHAR(50)
    if any(pattern in col_lower for pattern in identifier_patterns):
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
-- RÈGLES DE DÉTECTION UNIVERSELLES ET INTELLIGENTES :
-- 1. Priorité aux types définis dans le dictionnaire des variables
-- 2. Identifiants universels (code, iris, triris, siren, siret, com, dep...) → VARCHAR(50)
-- 3. Listes de codes (codes_postaux...) → VARCHAR(200) minimum selon données
-- 4. Détection explicite masquage (ZZZZZZ, s, SECRET...) → VARCHAR forcé
-- 5. Analyse des données avec marges de sécurité x8
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
            
            # PROTECTION SPÉCIALE : Identifiants géographiques critiques
            # Ces colonnes DOIVENT être VARCHAR même si le dictionnaire dit NUM (pour éviter ZZZZZZ)
            geographic_identifiers = ['iris', 'triris', 'codgeo', 'com', 'dep', 'reg', 'uu2010']
            is_geographic_identifier = any(pattern in col_clean.lower() for pattern in geographic_identifiers)
            
            producteur_type = None
            if dict_data and len(dict_data) > 0 and not is_geographic_identifier:
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
                        if debug_mode and col_clean.lower() == 'dep_nom':
                            st.write(f"🔍 DEBUG dep_nom - Ligne dictionnaire: {dict_row}")
                            st.write(f"🔍 DEBUG dep_nom - Headers dictionnaire: {dict_headers}")
                            st.write(f"🔍 DEBUG dep_nom - Index colonne type: {type_column_index}")
                        
                        # Si on a trouvé une colonne de type définie
                        if type_column_index is not None and len(dict_row) > type_column_index:
                            type_value = str(dict_row[type_column_index]).strip()
                            if type_value and type_value.lower() not in ['', 'nan', 'null', 'none']:
                                # Normalisation et validation du type
                                producteur_type = normalize_data_type(type_value)
                                if debug_mode and col_clean.lower() == 'dep_nom':
                                    st.write(f"🔍 DEBUG dep_nom - Type brut trouvé: '{type_value}' → normalisé: '{producteur_type}'")
                        
                        # MÉTHODE 3: Recherche dans toutes les colonnes si pas trouvé via header
                        if not producteur_type:
                            for type_field in dict_row[1:]:  # À partir de la 2ème colonne
                                type_str = str(type_field).strip()
                                if type_str:
                                    normalized_type = normalize_data_type(type_str)
                                    if normalized_type:
                                        producteur_type = normalized_type
                                        if debug_mode and col_clean.lower() == 'dep_nom':
                                            st.write(f"🔍 DEBUG dep_nom - Type trouvé par scan: '{type_str}' → '{producteur_type}'")
                                        break
                        break
            
            # ==================================================================================
            # ÉTAPE 1: Si le producteur a défini un type, l'utiliser en priorité absolue
            if producteur_type:
                sql_type = producteur_type
                if debug_mode and col_clean.lower() == 'dep_nom':
                    st.write(f"🔍 DEBUG dep_nom - UTILISATION TYPE PRODUCTEUR: {sql_type}")
            elif is_geographic_identifier:
                # FORÇAGE : Identifiants géographiques → toujours VARCHAR(50) (gestion ZZZZZZ)
                sql_type = 'VARCHAR(50)'
                if debug_mode:
                    st.write(f"🔍 DEBUG {col_clean} - IDENTIFIANT GÉOGRAPHIQUE FORCÉ → VARCHAR(50)")
            else:
                # ÉTAPE 2: Analyse CSV avec règles intelligentes (nom de colonne + données)
                sql_type = detect_column_type_with_column_name(clean_values, separateur, col_clean)
            
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