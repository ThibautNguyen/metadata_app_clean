import streamlit as st
import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime
import os

# Configuration de la page
st.set_page_config(
    page_title="Inspecteur de Base de Données",
    page_icon="🔍",
    layout="wide"
)

# Titre et description
st.title("Inspecteur de Base de Données")
st.write("Vérifiez l'état de la base de données et testez les insertions")

# Paramètres de connexion
DB_PARAMS = {
    "host": os.getenv("NEON_HOST", "ep-steep-sky-59276024.eu-central-1.aws.neon.tech"),
    "database": os.getenv("NEON_DATABASE", "neondb"),
    "user": os.getenv("NEON_USER", "neondb_owner"),
    "password": os.getenv("NEON_PASSWORD", "npg_XsA4wfvHy2Rn"),
    "sslmode": "require"
}

# Test de connexion
if st.button("Tester la connexion"):
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()
            st.success(f"Connexion réussie! Version PostgreSQL: {version[0]}")
        conn.close()
    except Exception as e:
        st.error(f"Erreur de connexion: {str(e)}")

# Vérification de la table
if st.button("Vérifier la table 'metadata'"):
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        with conn.cursor() as cur:
            # Vérifier si la table existe
            cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'metadata');")
            table_exists = cur.fetchone()[0]
            
            if table_exists:
                st.success("La table 'metadata' existe!")
                
                # Structure de la table
                cur.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = 'metadata' 
                    ORDER BY ordinal_position;
                """)
                columns = cur.fetchall()
                
                df_columns = pd.DataFrame(columns, columns=["Colonne", "Type", "Nullable"])
                st.table(df_columns)
                
                # Nombre de lignes
                cur.execute("SELECT COUNT(*) FROM metadata;")
                count = cur.fetchone()[0]
                st.info(f"La table contient {count} enregistrements.")
            else:
                st.error("La table 'metadata' n'existe pas!")
                
                # Option pour créer la table
                if st.button("Créer la table"):
                    try:
                        cur.execute("""
                            CREATE TABLE metadata (
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
                        st.success("Table créée avec succès!")
                    except Exception as e:
                        st.error(f"Erreur lors de la création de la table: {str(e)}")
        conn.close()
    except Exception as e:
        st.error(f"Erreur: {str(e)}")

# Test d'insertion
st.subheader("Test d'insertion")
with st.form("test_insertion"):
    nom_fichier = st.text_input("Nom du fichier", "test.csv")
    nom_base = st.text_input("Nom de la base", "TEST")
    schema = st.text_input("Schéma", "TEST")
    description = st.text_area("Description", "Test d'insertion")
    
    submitted = st.form_submit_button("Insérer")
    
    if submitted:
        try:
            conn = psycopg2.connect(**DB_PARAMS)
            with conn.cursor() as cur:
                # Données de test
                test_csv = {
                    "header": ["COL1", "COL2", "COL3"],
                    "data": [["val1", "val2", "val3"], ["val4", "val5", "val6"]],
                    "separator": ";"
                }
                
                # Insertion
                cur.execute("""
                    INSERT INTO metadata 
                    (nom_fichier, nom_base, schema, description, date_creation, date_maj, contenu_csv)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    nom_fichier,
                    nom_base,
                    schema,
                    description,
                    datetime.now().date(),
                    datetime.now().date(),
                    json.dumps(test_csv)
                ))
                
                # Récupérer l'ID
                inserted_id = cur.fetchone()[0]
                
                # Confirmer l'insertion
                conn.commit()
                st.success(f"Insertion réussie! ID: {inserted_id}")
            conn.close()
        except Exception as e:
            st.error(f"Erreur lors de l'insertion: {str(e)}")

# Affichage des données
if st.button("Afficher les données"):
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM metadata")
            rows = cur.fetchall()
            
            if rows:
                # Convertir en DataFrame
                for row in rows:
                    if 'contenu_csv' in row and row['contenu_csv']:
                        row['contenu_csv'] = "[JSON Data]"
                    if 'dictionnaire' in row and row['dictionnaire']:
                        row['dictionnaire'] = "[JSON Data]"
                
                st.dataframe(pd.DataFrame(rows))
            else:
                st.warning("Aucune donnée trouvée dans la table.")
        conn.close()
    except Exception as e:
        st.error(f"Erreur: {str(e)}") 