import json
import logging
import streamlit as st
import psycopg2
from datetime import datetime
import os

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
        conn = psycopg2.connect(
            host='ep-wispy-queen-abzi1lne-pooler.eu-west-2.aws.neon.tech',
            database='neondb',
            user='neondb_owner',
            password='npg_XsA4wfvHy2Rn',
            sslmode='require'
        )
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
                            producteur VARCHAR(255),
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

def get_metadata(filters=None):
    """Récupère les métadonnées de la base de données avec des filtres optionnels"""
    conn = get_db_connection()
    if not conn:
        return []
        
    try:
        with conn.cursor() as cur:
            query = "SELECT * FROM metadata"
            params = []
            
            # Si un filtre texte est passé directement (pour rétrocompatibilité)
            if filters is not None and isinstance(filters, str) and filters.strip():
                search_term = f"%{filters}%"
                query += """ WHERE 
                    nom_base ILIKE %s OR 
                    producteur ILIKE %s OR 
                    schema ILIKE %s OR 
                    description ILIKE %s OR
                    COALESCE(nom_table, '') ILIKE %s OR
                    COALESCE(source, '') ILIKE %s OR
                    COALESCE(licence, '') ILIKE %s OR
                    COALESCE(envoi_par, '') ILIKE %s
                """
                
                params = [search_term] * 8  # Répète le terme pour chaque condition OR
            # Si un dictionnaire de filtres est passé
            elif filters and isinstance(filters, dict):
                conditions = []
                
                # Filtres exacts (égalité)
                for key, value in filters.items():
                    if value:
                        conditions.append(f"{key} = %s")
                        params.append(value)
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
            
            logging.debug(f"Requête SQL get_metadata: {query}")
            logging.debug(f"Paramètres: {params}")
            
            cur.execute(query, params)
            columns = [desc[0] for desc in cur.description]
            results = []
            
            for row in cur.fetchall():
                metadata = dict(zip(columns, row))
                # Décodage des données JSON
                if metadata.get("contenu_csv"):
                    try:
                        if isinstance(metadata["contenu_csv"], str):
                            metadata["contenu_csv"] = json.loads(metadata["contenu_csv"])
                    except json.JSONDecodeError:
                        logging.warning("Erreur lors du décodage du contenu CSV")
                
                if metadata.get("dictionnaire"):
                    try:
                        if isinstance(metadata["dictionnaire"], str):
                            metadata["dictionnaire"] = json.loads(metadata["dictionnaire"])
                    except json.JSONDecodeError:
                        logging.warning("Erreur lors du décodage du dictionnaire")
                
                results.append(metadata)
            
            logging.info(f"Nombre de résultats trouvés : {len(results)}")
            return results
            
    except Exception as e:
        logging.error(f"Erreur lors de la récupération des métadonnées : {str(e)}")
        st.error(f"Erreur lors de la récupération des métadonnées : {str(e)}")
        return []
    finally:
        conn.close()

def save_metadata(metadata):
    """Sauvegarde les métadonnées dans la base de données"""
    logging.info("Début de la sauvegarde des métadonnées")
    logging.debug(f"Données reçues : {metadata}")
    
    # Vérification de la structure des données
    if not isinstance(metadata, dict):
        error_msg = f"Format de métadonnées incorrect : {type(metadata)}, attendu : dict"
        st.error(error_msg)
        logging.error(error_msg)
        return False, error_msg
    
    conn = get_db_connection()
    if not conn:
        error_msg = "Impossible de se connecter à la base de données"
        st.error(error_msg)
        logging.error(error_msg)
        return False, error_msg
        
    try:
        logging.info("Connexion à la base de données établie")
        with conn.cursor() as cur:
            # Vérification des champs requis
            required_fields = {
                "nom_base": metadata.get("nom_fichier"),  # nom_fichier dans le dictionnaire correspond à nom_base dans la BD
                "producteur": metadata.get("informations_base", {}).get("nom_base"),  # nom_base dans le dictionnaire correspond à producteur dans la BD
                "schema": metadata.get("informations_base", {}).get("schema"),
                "description": metadata.get("informations_base", {}).get("description")
            }
            
            logging.debug(f"Champs requis vérifiés : {required_fields}")
            
            missing_fields = [field for field, value in required_fields.items() if not value]
            if missing_fields:
                error_msg = f"Champs requis manquants : {', '.join(missing_fields)}"
                st.error(error_msg)
                logging.error(error_msg)
                return False, error_msg
            
            # Préparation des valeurs pour l'insertion
            try:
                # Conversion des données CSV et dictionnaire en JSON
                contenu_csv_json = None
                if "contenu_csv" in metadata:
                    logging.debug("Conversion du contenu CSV en JSON")
                    contenu_csv_json = json.dumps(metadata["contenu_csv"])
                
                dictionnaire_json = None
                if "dictionnaire" in metadata:
                    logging.debug("Conversion du dictionnaire en JSON")
                    # Vérifier si le dictionnaire est volumineux
                    dict_data = metadata["dictionnaire"].get("data", [])
                    dict_header = metadata["dictionnaire"].get("header", [])
                    dict_separator = metadata["dictionnaire"].get("separator", ";")
                    
                    # Vérifier la taille du dictionnaire
                    if len(dict_data) > 2000:
                        logging.warning(f"Dictionnaire très volumineux ({len(dict_data)} lignes). Traitement optimisé.")
                        # Limiter le dictionnaire aux 2000 premières lignes
                        metadata["dictionnaire"]["data"] = dict_data[:2000]
                        logging.info(f"Dictionnaire limité aux 2000 premières lignes pour des raisons de performance")
                    
                    dictionnaire_json = json.dumps(metadata["dictionnaire"])
                    logging.debug(f"Taille du dictionnaire JSON: {len(dictionnaire_json)} caractères")
                
                # Préparation des dates
                date_creation = metadata["informations_base"]["date_creation"]
                date_maj = metadata["informations_base"]["date_maj"]
                
                # Conversion des chaînes de date en objets date si nécessaire
                if isinstance(date_creation, str):
                    try:
                        # Si la date de création est juste une année (ex: "2020")
                        if date_creation.isdigit() and len(date_creation) == 4:
                            date_creation = f"{date_creation}-01-01"
                        
                        date_creation = datetime.strptime(date_creation, "%Y-%m-%d").date()
                        logging.debug(f"Date de création convertie : {date_creation}")
                    except ValueError as e:
                        logging.warning(f"Erreur de conversion de la date de création : {str(e)}")
                
                if isinstance(date_maj, str):
                    try:
                        date_maj = datetime.strptime(date_maj, "%Y-%m-%d").date()
                        logging.debug(f"Date de mise à jour convertie : {date_maj}")
                    except ValueError as e:
                        logging.warning(f"Erreur de conversion de la date de mise à jour : {str(e)}")
                
                # Récupération du nom de la table depuis les informations de base
                nom_table = metadata["informations_base"].get("nom_table", "")
                
                # Récupération de la granularité géographique
                granularite_geo = metadata["informations_base"].get("granularite_geo", "")
                
                # Vérifier si la colonne date_creation a été renommée en millesime
                cur.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'metadata' AND column_name = 'millesime'
                """)
                
                use_millesime = cur.fetchone() is not None
                
                # Construire les colonnes et valeurs pour l'insertion en fonction de la présence de millesime
                if use_millesime:
                    columns = ["nom_table", "nom_base", "producteur", "schema", "description", 
                               "millesime", "date_maj", "source", "frequence_maj",
                               "licence", "envoi_par", "contact", "mots_cles", "notes",
                               "contenu_csv", "dictionnaire", "granularite_geo"]
                else:
                    columns = ["nom_table", "nom_base", "producteur", "schema", "description", 
                               "date_creation", "date_maj", "source", "frequence_maj",
                               "licence", "envoi_par", "contact", "mots_cles", "notes",
                               "contenu_csv", "dictionnaire", "granularite_geo"]
                
                values = [
                    nom_table,
                    metadata["nom_fichier"],  # nom_fichier dans le dictionnaire correspond à nom_base dans la BD
                    metadata["informations_base"]["nom_base"],  # nom_base dans le dictionnaire correspond à producteur dans la BD
                    metadata["informations_base"]["schema"],
                    metadata["informations_base"]["description"],
                    date_creation,
                    date_maj,
                    metadata["informations_base"]["source"],
                    metadata["informations_base"]["frequence_maj"],
                    metadata["informations_base"]["licence"],
                    metadata["informations_base"]["envoi_par"],
                    "",  # champ contact vide
                    "",  # champ mots_cles vide
                    "",  # champ notes vide
                    contenu_csv_json,
                    dictionnaire_json,
                    granularite_geo
                ]
                
                # Construire la requête SQL dynamiquement
                placeholders = ", ".join(["%s"] * len(values))
                columns_str = ", ".join(columns)
                
                query = f"""
                    INSERT INTO metadata (
                        {columns_str}
                    ) VALUES (
                        {placeholders}
                    )
                """
                
                logging.debug(f"Valeurs préparées pour l'insertion : {values}")
            except KeyError as e:
                error_msg = f"Champ manquant dans la structure des métadonnées : {str(e)}"
                st.error(error_msg)
                logging.error(f"{error_msg} - Structure complète : {metadata}")
                return False, error_msg
            
            # Insertion dans la base de données
            try:
                cur.execute(query, values)
                logging.info("Requête d'insertion exécutée avec succès")
                
                conn.commit()
                logging.info("Transaction validée")
                
                # Vérification de l'insertion avec nom_base au lieu de nom_fichier
                cur.execute("SELECT * FROM metadata WHERE nom_base = %s AND nom_table = %s", 
                           (metadata["nom_fichier"], nom_table))
                inserted_row = cur.fetchone()
                if inserted_row:
                    logging.info(f"Vérification : ligne insérée avec succès - ID: {inserted_row[0]}")
                else:
                    warning_msg = "Vérification : aucune ligne trouvée après l'insertion"
                    logging.warning(warning_msg)
                
                return True, "Métadonnées sauvegardées avec succès dans la base de données"
                
            except Exception as e:
                error_msg = f"Erreur lors de l'exécution de la requête : {str(e)}"
                st.error(error_msg)
                logging.error(error_msg)
                conn.rollback()
                logging.info("Transaction annulée")
                return False, error_msg
                
    except Exception as e:
        error_msg = f"Erreur inattendue : {str(e)}"
        st.error(error_msg)
        logging.error(error_msg)
        return False, error_msg
    finally:
        conn.close()
        logging.info("Connexion à la base de données fermée")