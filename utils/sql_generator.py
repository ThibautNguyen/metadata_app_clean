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
from typing import List, Optional, Tuple, Dict
from .db_utils import get_db_connection
import textwrap


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


def _detect_column_type_from_dictionary(dict_info: Dict) -> Optional[str]:
    """
    Analyse intelligente du dictionnaire pour détecter le type de données.
    Recherche des patterns dans toutes les colonnes du dictionnaire.
    """
    # Patterns pour la détection des types
    type_patterns = {
        'codes': [
            r'code[s]?\s*(?:possible|autorisé|valide|détaillé)',
            r'modalité[s]?\s*(?:possible|autorisée)',
            r'correspondance[s]?[\s_](?:code|valeur)',
            r'valeur[s]?\s*(?:possible|autorisée)',
            r'liste\s*(?:des\s*)?(?:code|valeur)',
            r'nomenclature',
            r'codification',
        ],
        'text_type': [
            r'type[s]?[\s_](?:donnée|variable|champ)',
            r'format[\s_](?:donnée|variable|champ)',
            r'nature[\s_](?:donnée|variable|champ)',
            r'caractéristique[\s_](?:donnée|variable)',
            r'description[\s_]type',
        ]
    }

    # Fonction pour détecter les patterns dans une chaîne
    def has_pattern(text: str, patterns: List[str]) -> bool:
        if not isinstance(text, str):
            return False
        text = text.lower()
        return any(re.search(pattern.lower(), text) for pattern in patterns)

    # Parcourir toutes les clés du dictionnaire
    for key, value in dict_info.items():
        key_lower = key.lower()

        # 1. Recherche de colonnes contenant des codes/modalités
        if has_pattern(key_lower, type_patterns['codes']):
            if isinstance(value, str):
                # Extraction des codes numériques (en gérant les négatifs)
                numeric_codes = re.findall(r'[-]?\d+', value)
                if numeric_codes:
                    # Si tous les codes sont numériques
                    if all(c.strip('-').isdigit() for c in numeric_codes):
                        max_val = max(abs(int(c)) for c in numeric_codes)
                        if max_val < 128:
                            return 'SMALLINT'
                        return 'INTEGER'
                    
                # Si les codes sont alphanumériques, déterminer la longueur max
                all_codes = re.findall(r'[A-Za-z0-9]+', value)
                if all_codes:
                    max_length = max(len(code) for code in all_codes)
                    return f'VARCHAR({max(max_length * 2, 20)})'  # Marge de sécurité

        # 2. Recherche de colonnes décrivant le type
        if has_pattern(key_lower, type_patterns['text_type']):
            if isinstance(value, str):
                value_lower = value.lower()
                
                # Détection du type à partir de la description
                if any(x in value_lower for x in ['entier', 'integer', 'nombre entier']):
                    return 'INTEGER'
                elif any(x in value_lower for x in ['decimal', 'réel', 'float', 'nombre décimal']):
                    return 'DECIMAL(10,3)'
                elif any(x in value_lower for x in ['booléen', 'boolean', 'vrai/faux', 'oui/non']):
                    return 'BOOLEAN'
                elif any(x in value_lower for x in ['date', 'datetime']):
                    return 'DATE'
                elif 'texte' in value_lower or 'caractère' in value_lower:
                    # Recherche d'une longueur spécifiée
                    length_match = re.search(r'(\d+)[\s]*(?:caractère|char)', value_lower)
                    if length_match:
                        return f'VARCHAR({length_match.group(1)})'
                    return 'VARCHAR(255)'

    return None


def detect_column_type(clean_values: list, csv_separator: str = ';', column_name: str = '', dict_info: Dict = None) -> str:
    """
    Détection universelle et intelligente du type SQL pour une colonne.
    Basée sur l'analyse des données, du nom de colonne et du dictionnaire.
    
    Args:
        clean_values: Liste des valeurs nettoyées de la colonne
        csv_separator: Séparateur CSV utilisé (';' ou ',')
        column_name: Nom de la colonne pour une meilleure détection
        dict_info: Informations du dictionnaire pour cette colonne
    
    Returns:
        Type SQL approprié avec marges de sécurité
    """
    if not clean_values:
        return 'VARCHAR(255)'
    
    # 1. Vérification du dictionnaire si disponible
    if dict_info:
        dict_type = _detect_column_type_from_dictionary(dict_info)
        if dict_type:
            return dict_type
    
    # 2. Analyse du nom de colonne
    col_lower = column_name.lower() if column_name else ''
    
    # Détection des colonnes géographiques
    if any(col_lower == x for x in ['lat', 'latitude', 'long', 'longitude']):
        return 'DECIMAL(10,6)'
    
    # Détection des codes géographiques
    if col_lower in ['codgeo', 'code_insee', 'insee']:
        return 'VARCHAR(5)'
    elif any(pattern in col_lower for pattern in ['code_dep', 'dep']):
        return 'VARCHAR(3)'
    elif any(pattern in col_lower for pattern in ['code_reg', 'reg']):
        return 'VARCHAR(2)'
    elif col_lower.startswith('code') or col_lower.endswith('_id'):
        return 'VARCHAR(20)'
    
    # Détection des dates et années
    elif any(pattern in col_lower for pattern in ['annee', 'year']):
        return 'INTEGER'
    elif any(pattern in col_lower for pattern in ['date', 'timestamp']):
        return 'DATE'
    
    # Détection des pourcentages
    elif any(pattern in col_lower for pattern in ['taux', '%', 'pct', 'pourcentage', 'part']):
        return 'DECIMAL(5,2)'
    
    # 3. Analyse des valeurs avec gestion du masquage INSEE
    max_len = max(len(str(v)) for v in clean_values)
    
    # Détection du masquage INSEE
    insee_masking_patterns = ['ZZZZZZ', 'ZZZZZ', 'ZZZZ', 'ZZZ', 'XX', 'XXX', 'XXXX', 's', 'SECRET']
    has_insee_masking = any(
        str(val).strip().upper() in insee_masking_patterns 
        for val in clean_values
    )
    
    if has_insee_masking:
        if max_len <= 10:
            return 'VARCHAR(50)'
        elif max_len <= 25:
            return 'VARCHAR(200)'   
        else:
            return 'TEXT'
    
    # Test numérique strict
    all_numeric = True
    has_decimals = False
    
    for val in clean_values:
        val_str = str(val).strip()
        
        # Gestion selon le séparateur décimal
        if csv_separator == ';':
            # Format français
            if not re.match(r'^-?\d+(,\d*)?$', val_str.replace(' ', '')):
                all_numeric = False
                break
            if ',' in val_str:
                has_decimals = True
        else:
            # Format anglais
            if not re.match(r'^-?\d+(\.\d*)?$', val_str.replace(' ', '')):
                all_numeric = False
                break
            if '.' in val_str:
                has_decimals = True
    
    # Décision finale avec marges de sécurité
    if all_numeric:
        if has_decimals:
            return 'DECIMAL(15,6)'
        else:
            # Test pour les petits entiers
            try:
                max_val = max(abs(int(str(v).replace(' ', ''))) for v in clean_values)
                if max_val < 32768:
                    return 'SMALLINT'
                elif max_val < 2147483648:
                    return 'INTEGER'
                else:
                    return 'BIGINT'
            except:
                return 'INTEGER'
    else:
        # VARCHAR avec marges de sécurité
        if max_len <= 5:
            return 'VARCHAR(40)'
        elif max_len <= 10:
            return 'VARCHAR(80)'
        elif max_len <= 25:
            return 'VARCHAR(200)'
        elif max_len <= 50:
            return 'VARCHAR(400)'
        elif max_len <= 100:
            return 'VARCHAR(800)'
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
        'nombre de', "nombre d'", 'count', 'total', 'effectif', 'population', 
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
    
    # RÈGLE 4: Libellés/Noms → différentes tailles selon le type
    
    # RÈGLE 4a: Libellés géographiques spécifiques → VARCHAR(200)
    geo_label_keywords = [
        'libellé de la commune', 'libellé commune', 'libellé de l\'iris', 'libellé iris',
        'label de l\'iris', 'label iris',  # Ajout pour LAB_IRIS
        'libcom', 'libiris', 'lab_iris'
    ]
    if any(keyword in desc_lower for keyword in geo_label_keywords):
        return 'VARCHAR(200)'  # Pour les libellés géographiques (peuvent être longs)
    
    # RÈGLE 4b: Autres libellés → VARCHAR(255)
    text_keywords = [
        'libellé', 'libelle', 'nom de', 'intitulé', 'intitule', 
        'designation', 'désignation', 'appellation'
    ]
    if any(keyword in desc_lower for keyword in text_keywords):
        return 'VARCHAR(255)'  # Pour les libellés courts/moyens standards
    
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
    
    # RÈGLE PRIORITAIRE NOUVELLE : Libellés géographiques → VARCHAR(200)
    label_patterns = [
        r'^libcom$', r'^libiris$', r'^lab_iris$'  # Vrais libellés descriptifs
    ]
    
    # Si le nom de colonne matche un pattern de libellé → VARCHAR(200)
    if any(re.search(pattern, col_lower) for pattern in label_patterns):
        return 'VARCHAR(200)'
    
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
        # Indicateurs techniques géographiques (SANS les vrais libellés)
        r'^typ_iris$', r'^modif_iris$',
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
    col_lower = column_name.lower()
    
    # Protection spéciale pour les libellés géographiques → VARCHAR(200)
    geo_label_patterns = [r'^libcom$', r'^libiris$', r'^lab_iris$']
    if any(re.search(pattern, col_lower) for pattern in geo_label_patterns):
        return 'VARCHAR(200)'  # Protection absolue pour les libellés géographiques
    
    # Protection pour les identifiants techniques → VARCHAR(50)
    geographic_critical_patterns = [
        r'^iris$', r'^triris$', r'^codgeo$', r'^geocode$', 
        r'^commune$', r'^com$', r'^dep$', r'^reg$', r'^uu\d*$',
        r'^typ_iris$', r'^modif_iris$'  # Seulement les identifiants techniques
    ]
    if any(re.search(pattern, col_lower) for pattern in geographic_critical_patterns):
        return 'VARCHAR(50)'  # Protection absolue pour les codes seulement
    
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
            # Protection spéciale : Si l'analyse sémantique détecte VARCHAR(200) pour un libellé géographique,
            # forcer ce type (priorité absolue sur l'analyse des données)
            if semantic_type == 'VARCHAR(200)':
                return semantic_type
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


def generate_sql_script(table_name: str, schema: str, columns: List[Dict], description: str = "", 
                   producteur: str = "", type_donnees: str = "", millesime: str = "",
                   derniere_maj: str = "", frequence_maj: str = "") -> str:
    """
    Génère un script SQL pour créer une table avec les colonnes spécifiées.
    """
    # Formatage de la description en lignes de 80 caractères max, chacune précédée de --
    wrapped_description = []
    for line in description.split('\n'):
        if line.strip():  # Si la ligne n'est pas vide
            # Découper la ligne en segments de 77 caractères max
            wrapped = textwrap.wrap(line, width=77)  # 77 pour tenir compte du "-- "
            # Ajouter chaque segment avec le préfixe "--"
            wrapped_description.extend([f"-- {wrapped_line}" for wrapped_line in wrapped])
        else:
            # Pour les lignes vides, ajouter un commentaire vide
            wrapped_description.append("--")

    # S'assurer que toutes les lignes commencent par "--"
    description_formatted = '\n'.join(line if line.startswith('--') else f"-- {line}" 
                                    for line in wrapped_description)

    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    header = f"""-- =====================================================================================
-- SCRIPT D'IMPORT POUR LA TABLE {table_name}
-- =====================================================================================
-- Producteur: {producteur}
-- Type de données: {type_donnees}
-- Schéma: {schema}
-- Base de données: opendata
-- Description:
{description_formatted}
-- Millésime: {millesime}
-- Dernière mise à jour: {derniere_maj}
-- Fréquence de mise à jour: {frequence_maj}
-- Généré le {current_time}
-- =====================================================================================

"""

    # Suppression de la table
    drop_table = f'-- Suppression de la table existante (si elle existe)\nDROP TABLE IF EXISTS "{schema}"."{table_name}";\n\n'

    # Création de la table
    create_table = f'-- Création de la table avec types optimisés\nCREATE TABLE "{schema}"."{table_name}" (\n'
    
    # Ajout des colonnes
    columns_sql = []
    for col in columns:
        col_name = col['name']
        col_type = col['type']
        columns_sql.append(f'    "{col_name}" {col_type}')
    
    create_table += ',\n'.join(columns_sql)
    create_table += '\n);\n'

    # Assemblage du script final
    sql_script = header + drop_table + create_table
    
    return sql_script


def generate_sql_from_metadata(table_name: str, debug_mode: bool = False) -> str:
    """
    Génère une requête SQL d'import complète basée sur les métadonnées stockées.
    Version améliorée avec support complet du dictionnaire et détection intelligente des types.
    
    Args:
        table_name: Nom de la table dans la base de métadonnées
        debug_mode: Si True, affiche des informations de débogage
    
    Returns:
        Script SQL complet pour l'import des données
    """
    try:
        # Connexion à la base de métadonnées
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Récupération des métadonnées
        cursor.execute("SELECT * FROM metadata WHERE nom_table = %s", (table_name,))
        result = cursor.fetchone()
        
        if not result:
            raise ValueError(f"Table '{table_name}' non trouvée dans la base de métadonnées")
        
        # Conversion en dictionnaire
        columns = [desc[0] for desc in cursor.description]
        metadata = dict(zip(columns, result))
        
        # Extraction des informations principales
        nom_table = metadata.get('nom_table', 'unknown_table')
        schema = metadata.get('schema', 'public')
        description = metadata.get('description', '')
        producteur = metadata.get('producteur', '')
        type_donnees = metadata.get('type_donnees', '')
        date_maj = metadata.get('date_maj', '')
        frequence_maj = metadata.get('frequence_maj', '')
        millesime = metadata.get('date_creation', '')
        
        # Extraction du contenu CSV et du dictionnaire
        contenu_csv = metadata.get('contenu_csv', {})
        dictionnaire = metadata.get('dictionnaire', {})
        
        # Vérification de la présence des en-têtes CSV
        if not contenu_csv or 'header' not in contenu_csv:
            raise ValueError(f"Structure CSV non disponible pour la table '{table_name}'")
        
        colonnes = contenu_csv['header']
        separateur = contenu_csv.get('separator', ';')
        donnees_exemple = contenu_csv.get('data', [])
        
        # Création du dictionnaire des variables pour l'inférence de type
        dict_mapping = {}
        if dictionnaire and 'header' in dictionnaire and 'data' in dictionnaire:
            dict_headers = dictionnaire['header']
            dict_data = dictionnaire['data']
            
            # Pour chaque ligne du dictionnaire, créer un mapping nom_colonne -> infos
            for row in dict_data:
                if len(row) >= len(dict_headers):
                    var_info = dict(zip(dict_headers, row))
                    if dict_headers and row:
                        var_name = row[0]
                        dict_mapping[var_name] = var_info

        # Génération des définitions de colonnes
        columns_info = []
        for i, col in enumerate(colonnes):
            # Nettoyage du nom de colonne
            col_clean = col.strip()
            
            # Récupération des valeurs d'exemple pour cette colonne
            sample_values = [row[i] if len(row) > i else None for row in donnees_exemple]
            
            # Recherche des informations du dictionnaire
            dict_info = dict_mapping.get(col, {})
            
            # Inférence du type SQL avec toutes les informations disponibles
            sql_type = detect_column_type(
                clean_values=sample_values,
                csv_separator=separateur,
                column_name=col_clean,
                dict_info=dict_info
            )
            
            # Debug mode : afficher les détails de l'inférence
            if debug_mode:
                st.write(f"Colonne: {col_clean}")
                st.write(f"Type inféré: {sql_type}")
                st.write("---")
            
            columns_info.append({
                "name": col_clean,
                "type": sql_type
            })

        # Utilisation de generate_sql_script pour la génération finale
        sql_script = generate_sql_script(
            table_name=nom_table,
            schema=schema,
            columns=columns_info,
            description=description,
            producteur=producteur,
            type_donnees=type_donnees,
            millesime=millesime,
            derniere_maj=date_maj,
            frequence_maj=frequence_maj
        )
        
        conn.close()
        return sql_script
        
    except Exception as e:
        if debug_mode:
            st.error(f"Erreur lors de la génération du SQL : {str(e)}")
        raise


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


def display_sql_generation_interface_new(table_name: str, debug_mode: bool = True) -> None:
    """
    Affiche l'interface complète de génération SQL avec le script et les boutons.
    
    Args:
        table_name: Nom de la table pour laquelle générer le script
        debug_mode: Si True, affiche les informations de debug
    """
    # Interface de génération SQL avec commentaires corrigés
    
    try:
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
            2. **Créez le schéma** si nécessaire : `CREATE SCHEMA IF NOT EXISTS "nom_schema";`
            3. **Importez vos données** avec une commande COPY adaptée à votre fichier
            4. **Exécutez** le script dans votre outil de gestion PostgreSQL (DBeaver, pgAdmin, etc.)
            """)
    except Exception as e:
        st.error(f"🔥 ERREUR DANS NOTRE NOUVELLE FONCTION : {str(e)}") 