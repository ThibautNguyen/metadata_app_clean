import json
import logging
import streamlit as st
import psycopg2
from datetime import datetime
import os
import unicodedata
import psycopg2.extras

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_db_connection():
    """Établit une connexion à la base de données Neon.tech"""
    try:
        # Essayer d'utiliser les variables d'environnement de Streamlit (pour le déploiement)
        # Paramètres par défaut pour la connexion locale
        db_params = {
            'host': 'ep-wispy-queen-abzi1lne-pooler.eu-west-2.aws.neon.tech',
            'database': 'neondb',
            'user': 'neondb_owner',
            'password': 'npg_XsA4wfvHy2Rn',
            'sslmode': 'require'
        }
        
        # Remplacer par les variables d'environnement si elles existent
        if os.environ.get('NEON_HOST'):
            db_params['host'] = os.environ.get('NEON_HOST')
        if os.environ.get('NEON_DATABASE'):
            db_params['database'] = os.environ.get('NEON_DATABASE')
        if os.environ.get('NEON_USER'):
            db_params['user'] = os.environ.get('NEON_USER')
        if os.environ.get('NEON_PASSWORD'):
            db_params['password'] = os.environ.get('NEON_PASSWORD')
            
        logging.info("Tentative de connexion à la base de données")
        conn = psycopg2.connect(**db_params)
        logging.info("Connexion à la base de données réussie")
        return conn
    except Exception as e:
        logging.error(f"Erreur de connexion à la base de données : {str(e)}")
        st.error(f"Erreur de connexion à la base de données : {str(e)}")
        return None

def test_connection():
    """Teste la connexion à la base de données et affiche le résultat"""
    try:
        # Utiliser les mêmes paramètres que get_db_connection
        db_params = {
            'host': 'ep-wispy-queen-abzi1lne-pooler.eu-west-2.aws.neon.tech',
            'database': 'neondb',
            'user': 'neondb_owner',
            'password': 'npg_XsA4wfvHy2Rn',
            'sslmode': 'require'
        }
        
        # Remplacer par les variables d'environnement si elles existent
        if os.environ.get('NEON_HOST'):
            db_params['host'] = os.environ.get('NEON_HOST')
        if os.environ.get('NEON_DATABASE'):
            db_params['database'] = os.environ.get('NEON_DATABASE')
        if os.environ.get('NEON_USER'):
            db_params['user'] = os.environ.get('NEON_USER')
        if os.environ.get('NEON_PASSWORD'):
            db_params['password'] = os.environ.get('NEON_PASSWORD')
            
        conn = psycopg2.connect(**db_params)
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()
            conn.close()
            return True, f"Connexion réussie ! Version PostgreSQL : {version[0]}"
    except Exception as e:
        return False, f"Erreur de connexion : {str(e)}"

def init_db():
    """Initialise la base de données avec la table des métadonnées"""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                # Vérification si la table metadata existe
                cur.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_name = 'metadata'
                """)
                
                table_exists = cur.fetchone() is not None
                
                # Création de la table si elle n'existe pas
                if not table_exists:
                    cur.execute("""
                        CREATE TABLE metadata (
                            id SERIAL PRIMARY KEY,
                            nom_table VARCHAR(255),
                            nom_base VARCHAR(255) NOT NULL,
                            type_donnees VARCHAR(255),
                            producteur VARCHAR(255),
                            nom_jeu_donnees VARCHAR(255),
                            schema VARCHAR(255),
                            description TEXT,
                            millesime DATE,
                            date_maj DATE,
                            source VARCHAR(255),
                            frequence_maj VARCHAR(255),
                            licence VARCHAR(255),
                            envoi_par VARCHAR(255),
                            contact VARCHAR(255),
                            mots_cles TEXT,
                            notes TEXT,
                            contenu_csv JSONB,
                            dictionnaire JSONB,
                            granularite_geo VARCHAR(100),
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """)
                    logging.info("Table metadata créée")
                else:
                    # Vérifier si les anciennes colonnes nom_fichier existe
                    cur.execute("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = 'metadata' AND column_name = 'nom_fichier'
                    """)
                    old_column_exists = cur.fetchone() is not None
                    
                    # Si l'ancienne colonne existe, la renommer
                    if old_column_exists:
                        try:
                            cur.execute("ALTER TABLE metadata RENAME COLUMN nom_fichier TO nom_base")
                            logging.info("Colonne nom_fichier renommée en nom_base")
                        except Exception as e:
                            logging.warning(f"Erreur lors du renommage de la colonne nom_fichier : {str(e)}")
                    
                    # Vérifier si l'ancienne colonne date_creation existe
                    cur.execute("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = 'metadata' AND column_name = 'date_creation'
                    """)
                    date_creation_exists = cur.fetchone() is not None
                    
                    # Vérifier si la nouvelle colonne millesime existe
                    cur.execute("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = 'metadata' AND column_name = 'millesime'
                    """)
                    millesime_exists = cur.fetchone() is not None
                    
                    # Si l'ancienne colonne existe mais pas la nouvelle, la renommer
                    if date_creation_exists and not millesime_exists:
                        try:
                            cur.execute("ALTER TABLE metadata RENAME COLUMN date_creation TO millesime")
                            logging.info("Colonne date_creation renommée en millesime")
                        except Exception as e:
                            logging.warning(f"Erreur lors du renommage de la colonne date_creation : {str(e)}")
                
                # Vérification pour les autres colonnes nom_table et granularite_geo
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'metadata' AND column_name = 'nom_table'
                """)
                
                nom_table_exists = cur.fetchone() is not None
                if not nom_table_exists:
                    try:
                        cur.execute("ALTER TABLE metadata ADD COLUMN nom_table VARCHAR(255)")
                        logging.info("Colonne nom_table ajoutée à la table metadata")
                    except Exception as e:
                        logging.warning(f"Impossible d'ajouter la colonne nom_table : {str(e)}")
                
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'metadata' AND column_name = 'granularite_geo'
                """)
                
                granularite_geo_exists = cur.fetchone() is not None
                if not granularite_geo_exists:
                    try:
                        cur.execute("ALTER TABLE metadata ADD COLUMN granularite_geo VARCHAR(100)")
                        logging.info("Colonne granularite_geo ajoutée à la table metadata")
                    except Exception as e:
                        logging.warning(f"Impossible d'ajouter la colonne granularite_geo : {str(e)}")
                
                conn.commit()
                logging.info("Table metadata configurée")
        except Exception as e:
            logging.error(f"Erreur lors de l'initialisation de la base de données : {str(e)}")
            st.error(f"Erreur lors de l'initialisation de la base de données : {str(e)}")
        finally:
            conn.close()

def get_metadata_columns():
    """Récupère la liste des colonnes de la table metadata"""
    conn = get_db_connection()
    if not conn:
        return []
        
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'metadata'
                ORDER BY ordinal_position
            """)
            
            columns = [row[0] for row in cur.fetchall()]
            return columns
            
    except Exception as e:
        logging.error(f"Erreur lors de la récupération des colonnes : {str(e)}")
        return []
    finally:
        conn.close()

def remove_accents(input_str):
    """Supprime les accents d'une chaîne de caractères"""
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return ''.join([c for c in nfkd_form if not unicodedata.combining(c)])

def get_metadata(search_term=None, schema_filter=None):
    """Récupère les métadonnées depuis la base de données avec possibilité de recherche et filtre par schéma"""
    conn = get_db_connection()
    try:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            if search_term and schema_filter:
                query = """
                SELECT *, 
                    (CASE 
                        WHEN LOWER(nom_jeu_donnees) LIKE LOWER(%s) THEN 4
                        WHEN LOWER(producteur) LIKE LOWER(%s) THEN 3
                        WHEN LOWER(description) LIKE LOWER(%s) THEN 2
                        WHEN LOWER(dictionnaire::text) LIKE LOWER(%s) THEN 1
                        ELSE 0
                    END) +
                    (CASE 
                        WHEN position(LOWER(%s) in LOWER(nom_jeu_donnees)) = 1 THEN 2
                        WHEN position(LOWER(%s) in LOWER(producteur)) = 1 THEN 1.5
                        ELSE 1
                    END) as score
                FROM metadata 
                WHERE (LOWER(nom_jeu_donnees) LIKE LOWER(%s)
                OR LOWER(producteur) LIKE LOWER(%s)
                OR LOWER(description) LIKE LOWER(%s)
                OR LOWER(dictionnaire::text) LIKE LOWER(%s))
                AND LOWER(schema) = LOWER(%s)
                ORDER BY score DESC, nom_jeu_donnees
                """
                search_pattern = f'%{search_term}%'
                cur.execute(query, (
                    search_pattern, search_pattern, search_pattern, search_pattern,  # Pour le CASE du type de champ
                    search_term, search_term,  # Pour le CASE de la position
                    search_pattern, search_pattern, search_pattern, search_pattern,  # Pour le WHERE
                    schema_filter
                ))
            elif search_term:
                query = """
                SELECT *, 
                    (CASE 
                        WHEN LOWER(nom_jeu_donnees) LIKE LOWER(%s) THEN 4
                        WHEN LOWER(producteur) LIKE LOWER(%s) THEN 3
                        WHEN LOWER(description) LIKE LOWER(%s) THEN 2
                        WHEN LOWER(dictionnaire::text) LIKE LOWER(%s) THEN 1
                        ELSE 0
                    END) +
                    (CASE 
                        WHEN position(LOWER(%s) in LOWER(nom_jeu_donnees)) = 1 THEN 2
                        WHEN position(LOWER(%s) in LOWER(producteur)) = 1 THEN 1.5
                        ELSE 1
                    END) as score
                FROM metadata 
                WHERE LOWER(nom_jeu_donnees) LIKE LOWER(%s)
                OR LOWER(producteur) LIKE LOWER(%s)
                OR LOWER(description) LIKE LOWER(%s)
                OR LOWER(dictionnaire::text) LIKE LOWER(%s)
                ORDER BY score DESC, nom_jeu_donnees
                """
                search_pattern = f'%{search_term}%'
                cur.execute(query, (
                    search_pattern, search_pattern, search_pattern, search_pattern,  # Pour le CASE du type de champ
                    search_term, search_term,  # Pour le CASE de la position
                    search_pattern, search_pattern, search_pattern, search_pattern  # Pour le WHERE
                ))
            elif schema_filter:
                query = """
                SELECT * FROM metadata 
                WHERE LOWER(schema) = LOWER(%s)
                ORDER BY nom_jeu_donnees
                """
                cur.execute(query, (schema_filter,))
            else:
                query = "SELECT * FROM metadata ORDER BY nom_jeu_donnees"
                cur.execute(query)
            results = cur.fetchall()
            logging.info(f"Nombre de résultats trouvés : {len(results)}")
            return results
    except Exception as e:
        logging.error(f"Erreur lors de la récupération des métadonnées : {str(e)}")
        return []
    finally:
        conn.close()

def save_metadata(metadata):
    """Sauvegarde les métadonnées dans la base de données"""
    conn = get_db_connection()
    if not conn:
        return False, "Erreur de connexion à la base de données"
    
    try:
        with conn.cursor() as cur:
            # Préparation des données pour l'insertion
            data = {
                'nom_table': metadata.get('informations_base', {}).get('nom_table'),
                'nom_base': metadata.get('informations_base', {}).get('nom_base'),
                'type_donnees': metadata.get('informations_base', {}).get('type_donnees'),
                'producteur': metadata.get('informations_base', {}).get('producteur'),
                'nom_jeu_donnees': metadata.get('informations_base', {}).get('nom_jeu_donnees'),
                'schema': metadata.get('informations_base', {}).get('schema'),
                'description': metadata.get('informations_base', {}).get('description'),
                'millesime': metadata.get('informations_base', {}).get('date_creation'),
                'date_publication': metadata.get('date_publication', None),
                'date_maj': metadata.get('date_maj', None),
                'date_prochaine_publication': metadata.get('date_prochaine_publication', None),
                'source': metadata.get('informations_base', {}).get('source'),
                'frequence_maj': metadata.get('informations_base', {}).get('frequence_maj'),
                'licence': metadata.get('informations_base', {}).get('licence'),
                'envoi_par': metadata.get('informations_base', {}).get('envoi_par'),
                'granularite_geo': metadata.get('informations_base', {}).get('granularite_geo'),
                'contenu_csv': json.dumps(metadata.get('contenu_csv', {})),
                'dictionnaire': json.dumps(metadata.get('dictionnaire', {}))
            }
            
            # Construction de la requête SQL
            columns = ', '.join(data.keys())
            values = ', '.join(['%s'] * len(data))
            query = f"""
                INSERT INTO metadata ({columns})
                VALUES ({values})
                RETURNING id
            """

            # LOG pour debug
            print("REQUETE SQL :", query)
            print("VALEURS :", list(data.values()))
            # Exécution de la requête
            cur.execute(query, list(data.values()))
            new_id = cur.fetchone()[0]
            conn.commit()
            
            return True, f"Métadonnées sauvegardées avec succès (ID: {new_id})"
    except Exception as e:
        conn.rollback()
        logging.error(f"Erreur lors de la sauvegarde des métadonnées : {str(e)}")
        return False, f"Erreur lors de la sauvegarde : {str(e)}"
    finally:
        conn.close()

def get_producteurs_by_type(type_donnees: str) -> list[str]:
    """Récupère la liste des producteurs pour un type de données donné"""
    logging.info(f"Récupération des producteurs pour le type de données : {type_donnees}")
    conn = get_db_connection()
    if not conn:
        logging.error("Impossible de se connecter à la base de données")
        return []
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT producteur 
                FROM metadata 
                WHERE type_donnees = %s 
                AND producteur IS NOT NULL 
                ORDER BY producteur
            """, (type_donnees,))
            producteurs = [row[0] for row in cur.fetchall()]
            logging.info(f"Producteurs trouvés : {producteurs}")
            return producteurs if producteurs else []
    except Exception as e:
        logging.error(f"Erreur lors de la récupération des producteurs : {str(e)}")
        return []
    finally:
        conn.close()

def get_jeux_donnees_by_producteur(producteur: str) -> list[str]:
    """Récupère la liste des jeux de données pour un producteur donné"""
    conn = get_db_connection()
    if not conn:
        return []
    
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT nom_jeu_donnees 
                FROM metadata 
                WHERE producteur = %s 
                AND nom_jeu_donnees IS NOT NULL 
                ORDER BY nom_jeu_donnees
            """, (producteur,))
            jeux = [row[0] for row in cur.fetchall()]
            return jeux if jeux else []
    except Exception as e:
        logging.error(f"Erreur lors de la récupération des jeux de données : {str(e)}")
        return []
    finally:
        conn.close()

def get_types_donnees() -> list[str]:
    """Récupère la liste des types de données existants"""
    return ["donnée ouverte", "donnée client", "donnée restreinte", "donnée payante", "autre"]