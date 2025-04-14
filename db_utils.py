import json
import logging
import streamlit as st
import psycopg2
from datetime import datetime

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def get_db_connection():
    """Établit une connexion à la base de données Neon.tech"""
    try:
        logging.info("Tentative de connexion à la base de données")
        conn = psycopg2.connect(
            host='ep-wispy-queen-abzi1lne-pooler.eu-west-2.aws.neon.tech',
            database='neondb',
            user='neondb_owner',
            password='npg_XsA4wfvHy2Rn',
            sslmode='require'
        )
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
                # Création de la table si elle n'existe pas
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS metadata (
                        id SERIAL PRIMARY KEY,
                        nom_fichier VARCHAR(255) NOT NULL,
                        nom_base VARCHAR(255),
                        schema VARCHAR(255),
                        description TEXT,
                        date_creation DATE,
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
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
                logging.info("Table metadata créée ou déjà existante")
                st.success("Table metadata créée ou déjà existante")
        except Exception as e:
            logging.error(f"Erreur lors de l'initialisation de la base de données : {str(e)}")
            st.error(f"Erreur lors de l'initialisation de la base de données : {str(e)}")
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
                    nom_fichier ILIKE %s OR 
                    nom_base ILIKE %s OR 
                    schema ILIKE %s OR 
                    description ILIKE %s OR 
                    mots_cles ILIKE %s
                """
                params = [search_term, search_term, search_term, search_term, search_term]
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
                        st.warning("Erreur lors du décodage du contenu CSV")
                        logging.warning("Erreur lors du décodage du contenu CSV")
                
                if metadata.get("dictionnaire"):
                    try:
                        if isinstance(metadata["dictionnaire"], str):
                            metadata["dictionnaire"] = json.loads(metadata["dictionnaire"])
                    except json.JSONDecodeError:
                        st.warning("Erreur lors du décodage du dictionnaire")
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
    st.write("=== Début de la sauvegarde des métadonnées ===")
    st.write("Données reçues :", metadata)
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
                "nom_fichier": metadata.get("nom_fichier"),
                "nom_base": metadata.get("informations_base", {}).get("nom_base"),
                "schema": metadata.get("informations_base", {}).get("schema"),
                "description": metadata.get("informations_base", {}).get("description")
            }
            
            st.write("Champs requis vérifiés :", required_fields)
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
                    dictionnaire_json = json.dumps(metadata["dictionnaire"])
                
                # Préparation des dates
                date_creation = metadata["informations_base"]["date_creation"]
                date_maj = metadata["informations_base"]["date_maj"]
                
                # Conversion des chaînes de date en objets date si nécessaire
                if isinstance(date_creation, str):
                    try:
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
                
                values = (
                    metadata["nom_fichier"],
                    metadata["informations_base"]["nom_base"],
                    metadata["informations_base"]["schema"],
                    metadata["informations_base"]["description"],
                    date_creation,
                    date_maj,
                    metadata["informations_base"]["source"],
                    metadata["informations_base"]["frequence_maj"],
                    metadata["informations_base"]["licence"],
                    metadata["informations_supplementaires"]["envoi_par"],
                    metadata["informations_supplementaires"]["contact"],
                    metadata["informations_supplementaires"]["mots_cles"],
                    metadata["informations_supplementaires"]["notes"],
                    contenu_csv_json,
                    dictionnaire_json
                )
                st.write("Valeurs préparées pour l'insertion :", values)
                logging.debug(f"Valeurs préparées pour l'insertion : {values}")
            except KeyError as e:
                error_msg = f"Champ manquant dans la structure des métadonnées : {str(e)}"
                st.error(error_msg)
                logging.error(f"{error_msg} - Structure complète : {metadata}")
                return False, error_msg
            
            # Insertion dans la base de données
            try:
                query = """
                    INSERT INTO metadata (
                        nom_fichier, nom_base, schema, description,
                        date_creation, date_maj, source, frequence_maj,
                        licence, envoi_par, contact, mots_cles, notes,
                        contenu_csv, dictionnaire
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                        %s, %s
                    )
                """
                st.write("Requête SQL :", query)
                st.write("Paramètres :", values)
                logging.debug(f"Requête SQL : {query}")
                logging.debug(f"Paramètres : {values}")
                
                cur.execute(query, values)
                st.write("Requête d'insertion exécutée avec succès")
                logging.info("Requête d'insertion exécutée avec succès")
                
                conn.commit()
                st.write("Transaction validée")
                logging.info("Transaction validée")
                
                # Vérification de l'insertion
                cur.execute("SELECT * FROM metadata WHERE nom_fichier = %s", (metadata["nom_fichier"],))
                inserted_row = cur.fetchone()
                if inserted_row:
                    st.write(f"Vérification : ligne insérée avec succès - ID: {inserted_row[0]}")
                    logging.info(f"Vérification : ligne insérée avec succès - ID: {inserted_row[0]}")
                else:
                    warning_msg = "Vérification : aucune ligne trouvée après l'insertion"
                    st.warning(warning_msg)
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
        st.write("Connexion à la base de données fermée")
        logging.info("Connexion à la base de données fermée")