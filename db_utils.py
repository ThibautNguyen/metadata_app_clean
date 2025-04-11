import psycopg2
from psycopg2.extras import RealDictCursor
import streamlit as st

def get_db_connection():
    """Établit une connexion à la base de données Neon.tech"""
    try:
        conn = psycopg2.connect(
            host=st.secrets["NEON_HOST"],
            database="neondb",
            user=st.secrets["NEON_USER"],
            password=st.secrets["NEON_PASSWORD"],
            sslmode='require'
        )
        return conn
    except Exception as e:
        st.error(f"Erreur de connexion à la base de données : {str(e)}")
        return None

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
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
        except Exception as e:
            st.error(f"Erreur lors de l'initialisation de la base de données : {str(e)}")
        finally:
            conn.close()

def save_metadata(metadata):
    """Sauvegarde les métadonnées dans la base de données"""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO metadata (
                        nom_fichier, nom_base, schema, description,
                        date_creation, date_maj, source, frequence_maj,
                        licence, envoi_par, contact, mots_cles, notes
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    metadata["nom_fichier"],
                    metadata["informations_base"]["nom_base"],
                    metadata["informations_base"]["schema"],
                    metadata["informations_base"]["description"],
                    metadata["informations_base"]["date_creation"],
                    metadata["informations_base"]["date_maj"],
                    metadata["informations_base"]["source"],
                    metadata["informations_base"]["frequence_maj"],
                    metadata["informations_base"]["licence"],
                    metadata["informations_supplementaires"]["envoi_par"],
                    metadata["informations_supplementaires"]["contact"],
                    metadata["informations_supplementaires"]["mots_cles"],
                    metadata["informations_supplementaires"]["notes"]
                ))
                conn.commit()
                return True, "Métadonnées sauvegardées avec succès dans la base de données"
        except Exception as e:
            return False, f"Erreur lors de la sauvegarde : {str(e)}"
        finally:
            conn.close()
    return False, "Impossible de se connecter à la base de données"

def test_connection():
    """Teste la connexion à la base de données et affiche le résultat"""
    try:
        conn = psycopg2.connect(
            host=st.secrets["NEON_HOST"],
            database="neondb",
            user=st.secrets["NEON_USER"],
            password=st.secrets["NEON_PASSWORD"],
            sslmode='require'
        )
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()
            conn.close()
            return True, f"Connexion réussie ! Version PostgreSQL : {version[0]}"
    except Exception as e:
        return False, f"Erreur de connexion : {str(e)}" 