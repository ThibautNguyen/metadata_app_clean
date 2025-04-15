import streamlit as st
import pandas as pd
import sys
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import json

# Ajout du répertoire parent au PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent))

# Configuration de la page
st.set_page_config(
    page_title="Database Inspector",
    page_icon="🔍",
    layout="wide"
)

# Titre et description
st.title("Database Inspector")
st.write("Cet outil permet d'examiner la base de données Neon.tech et de diagnostiquer les problèmes de connexion et d'enregistrement.")

# Paramètres de connexion
st.subheader("Paramètres de connexion")
with st.expander("Voir/modifier les paramètres", expanded=True):
    host = st.text_input("Host", value="ep-wispy-queen-abzi1lne-pooler.eu-west-2.aws.neon.tech")
    database = st.text_input("Database", value="neondb")
    user = st.text_input("User", value="neondb_owner")
    password = st.text_input("Password", value="npg_XsA4wfvHy2Rn", type="password")
    sslmode = st.selectbox("SSL Mode", options=["require", "disable", "allow", "prefer", "verify-ca", "verify-full"], index=0)

# Fonction pour se connecter à la base de données
def connect_to_db():
    try:
        conn = psycopg2.connect(
            host=host,
            database=database,
            user=user,
            password=password,
            sslmode=sslmode
        )
        return conn, None
    except Exception as e:
        return None, str(e)

# Test de connexion
if st.button("Tester la connexion"):
    conn, error = connect_to_db()
    if conn:
        st.success("Connexion réussie à la base de données Neon.tech!")
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()
            st.info(f"Version PostgreSQL: {version[0]}")
        conn.close()
    else:
        st.error(f"Échec de la connexion: {error}")

# Vérification de la structure de la table
st.subheader("Structure de la table 'metadata'")
if st.button("Vérifier la structure"):
    conn, error = connect_to_db()
    if conn:
        with conn.cursor() as cur:
            # Vérifier si la table existe
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'metadata'
                );
            """)
            table_exists = cur.fetchone()[0]
            
            if table_exists:
                st.success("La table 'metadata' existe.")
                
                # Structure de la table
                cur.execute("""
                    SELECT column_name, data_type, is_nullable
                    FROM information_schema.columns 
                    WHERE table_name = 'metadata' 
                    ORDER BY ordinal_position;
                """)
                columns = []
                for col in cur.fetchall():
                    columns.append({
                        "Colonne": col[0],
                        "Type": col[1],
                        "Nullable": col[2]
                    })
                
                st.write("Structure de la table:")
                st.table(pd.DataFrame(columns))
            else:
                st.error("La table 'metadata' n'existe pas.")
                
                # Option pour créer la table
                if st.button("Créer la table 'metadata'"):
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
                        st.success("Table 'metadata' créée avec succès!")
                    except Exception as e:
                        st.error(f"Erreur lors de la création de la table: {e}")
        conn.close()
    else:
        st.error(f"Échec de la connexion: {error}")

# Contenu de la table
st.subheader("Contenu de la table 'metadata'")
if st.button("Voir le contenu"):
    conn, error = connect_to_db()
    if conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            try:
                cur.execute("SELECT COUNT(*) FROM metadata")
                count = cur.fetchone()['count']
                
                if count > 0:
                    st.info(f"La table contient {count} enregistrements.")
                    
                    # Récupérer les données
                    cur.execute("SELECT * FROM metadata")
                    rows = cur.fetchall()
                    
                    # Simplifier les données JSON pour l'affichage
                    for row in rows:
                        if row.get('contenu_csv'):
                            row['contenu_csv'] = "[JSON Data]"
                        if row.get('dictionnaire'):
                            row['dictionnaire'] = "[JSON Data]"
                    
                    # Convertir en DataFrame et afficher
                    st.write("Données dans la table:")
                    st.dataframe(pd.DataFrame(rows))
                    
                    # Option pour voir les détails d'un enregistrement
                    st.write("Voir les détails d'un enregistrement:")
                    ids = [row['id'] for row in rows]
                    selected_id = st.selectbox("Sélectionner un ID:", ids)
                    
                    if selected_id:
                        # Récupérer l'enregistrement complet
                        for row in rows:
                            if row['id'] == selected_id:
                                # Récupérer les données JSON originales
                                cur.execute("SELECT contenu_csv, dictionnaire FROM metadata WHERE id = %s", (selected_id,))
                                json_data = cur.fetchone()
                                
                                # Afficher les détails
                                st.write("#### Détails de l'enregistrement:")
                                col1, col2 = st.columns(2)
                                
                                with col1:
                                    st.write("**Informations de base:**")
                                    st.write(f"- **Nom fichier:** {row['nom_fichier']}")
                                    st.write(f"- **Nom base:** {row['nom_base']}")
                                    st.write(f"- **Schéma:** {row['schema']}")
                                    st.write(f"- **Description:** {row['description']}")
                                
                                with col2:
                                    st.write("**Informations supplémentaires:**")
                                    st.write(f"- **Source:** {row['source']}")
                                    st.write(f"- **Contact:** {row['contact']}")
                                    st.write(f"- **Mots-clés:** {row['mots_cles']}")
                                
                                # Afficher contenu CSV si disponible
                                if json_data['contenu_csv']:
                                    st.write("**Aperçu du contenu CSV:**")
                                    try:
                                        if isinstance(json_data['contenu_csv'], str):
                                            csv_data = json.loads(json_data['contenu_csv'])
                                        else:
                                            csv_data = json_data['contenu_csv']
                                            
                                        if 'header' in csv_data and 'data' in csv_data:
                                            df = pd.DataFrame(csv_data['data'], columns=csv_data['header'])
                                            st.dataframe(df)
                                    except Exception as e:
                                        st.error(f"Erreur lors de l'affichage du contenu CSV: {e}")
                else:
                    st.warning("La table 'metadata' est vide.")
            except Exception as e:
                st.error(f"Erreur lors de la récupération des données: {e}")
        conn.close()
    else:
        st.error(f"Échec de la connexion: {error}")

# Test d'insertion manuelle
st.subheader("Test d'insertion manuelle")
with st.form("test_insertion"):
    test_nom_fichier = st.text_input("Nom du fichier", "test_manual_insert.csv")
    test_nom_base = st.text_input("Nom de la base", "TEST")
    test_schema = st.text_input("Schéma", "TEST")
    test_description = st.text_area("Description", "Test d'insertion manuelle")
    
    test_submit = st.form_submit_button("Insérer un enregistrement de test")
    
    if test_submit:
        conn, error = connect_to_db()
        if conn:
            try:
                with conn.cursor() as cur:
                    # Préparation des données de test
                    test_csv_data = {
                        "header": ["COL1", "COL2", "COL3"],
                        "data": [
                            ["val1", "val2", "val3"],
                            ["val4", "val5", "val6"]
                        ],
                        "separator": ";"
                    }
                    
                    # Insertion
                    cur.execute("""
                        INSERT INTO metadata (
                            nom_fichier, nom_base, schema, description,
                            date_creation, date_maj, source, 
                            envoi_par, contact, contenu_csv
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                        RETURNING id
                    """, (
                        test_nom_fichier,
                        test_nom_base,
                        test_schema,
                        test_description,
                        datetime.now().date(),
                        datetime.now().date(),
                        "Test manuel",
                        "Database Inspector",
                        "test@example.com",
                        json.dumps(test_csv_data)
                    ))
                    
                    # Récupérer l'ID inséré
                    result = cur.fetchone()
                    
                    conn.commit()
                    st.success(f"Enregistrement de test inséré avec succès! ID: {result[0]}")
            except Exception as e:
                st.error(f"Erreur lors de l'insertion de l'enregistrement de test: {e}")
                conn.rollback()
            finally:
                conn.close()
        else:
            st.error(f"Échec de la connexion: {error}")

# Logs
st.subheader("Logs")
with st.expander("Logs de débogage"):
    if st.button("Voir les derniers logs"):
        st.info("Cette fonctionnalité serait connectée à vos fichiers de logs pour afficher les erreurs récentes.")
        st.code("""
        2023-04-15 14:32:45 - INFO - Tentative de connexion à la base de données
        2023-04-15 14:32:46 - INFO - Connexion à la base de données réussie
        2023-04-15 14:32:47 - DEBUG - Requête SQL get_metadata: SELECT * FROM metadata
        2023-04-15 14:32:47 - DEBUG - Paramètres: []
        2023-04-15 14:32:47 - INFO - Nombre de résultats trouvés : 0
        """, language="text") 