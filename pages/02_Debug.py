import streamlit as st
import pandas as pd
import json
from datetime import datetime
import sys
from pathlib import Path

# Ajout du répertoire parent au PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent))
from db_utils import get_db_connection, init_db

# Configuration de la page
st.set_page_config(
    page_title="Déboguer la BD",
    page_icon="🔧",
    layout="wide"
)

# Titre et description
st.title("Déboguer la base de données")
st.write("Cette page permet de vérifier la structure de la base de données et de tester l'insertion de données.")

# Test de la connexion
if st.button("Tester la connexion"):
    conn = get_db_connection()
    if conn:
        st.success("Connexion à la base de données réussie.")
        
        # Version de PostgreSQL
        with conn.cursor() as cur:
            cur.execute("SELECT version();")
            version = cur.fetchone()
            st.info(f"Version PostgreSQL : {version[0]}")
        
        conn.close()
        st.info("Connexion fermée.")
    else:
        st.error("Échec de la connexion à la base de données.")

# Initialisation de la base de données
if st.button("Initialiser la base de données"):
    init_db()
    st.success("Base de données initialisée.")

# Vérification de la structure
if st.button("Vérifier la structure de la table"):
    conn = get_db_connection()
    if conn:
        with conn.cursor() as cur:
            # Vérification de l'existence de la table
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
                    SELECT column_name, data_type 
                    FROM information_schema.columns 
                    WHERE table_name = 'metadata' 
                    ORDER BY ordinal_position;
                """)
                columns = []
                for column in cur.fetchall():
                    columns.append({
                        "Nom de colonne": column[0],
                        "Type de données": column[1]
                    })
                
                st.write("Structure de la table :")
                st.table(pd.DataFrame(columns))
                
                # Nombre de lignes
                cur.execute("SELECT COUNT(*) FROM metadata;")
                count = cur.fetchone()[0]
                st.info(f"Nombre de lignes dans la table : {count}")
                
                # Données existantes
                if count > 0:
                    cur.execute("SELECT * FROM metadata;")
                    rows = cur.fetchall()
                    colnames = [desc[0] for desc in cur.description]
                    
                    # Préparation des données pour affichage
                    data = []
                    for row in rows:
                        row_dict = {}
                        for i, col in enumerate(colnames):
                            # Pour éviter d'afficher de grandes quantités de données JSON
                            if col in ['contenu_csv', 'dictionnaire'] and row[i]:
                                row_dict[col] = "JSON data available"
                            else:
                                row_dict[col] = row[i]
                        data.append(row_dict)
                    
                    st.write("Données existantes :")
                    st.dataframe(pd.DataFrame(data))
            else:
                st.error("La table 'metadata' n'existe pas.")
                
                # Proposition d'initialisation
                st.info("Vous pouvez initialiser la base de données en utilisant le bouton 'Initialiser la base de données'.")
        
        conn.close()
    else:
        st.error("Échec de la connexion à la base de données.")

# Test d'insertion manuelle
st.subheader("Test d'insertion manuelle")

with st.form("test_insertion"):
    nom_fichier = st.text_input("Nom du fichier", "test_insertion.csv")
    nom_base = st.selectbox("Nom de la base", ["INSEE", "Météo France", "Citepa (GES)"])
    schema = st.selectbox("Schéma", ["Economie", "Démographie", "Environnement", "Social", "Autre"])
    description = st.text_area("Description", "Fichier de test pour l'insertion manuelle")
    
    col1, col2 = st.columns(2)
    with col1:
        source = st.text_input("Source", "Test manuel")
        frequence_maj = st.selectbox("Fréquence de mise à jour", ["Annuelle", "Semestrielle", "Trimestrielle", "Mensuelle", "Quotidienne", "Ponctuelle"])
    
    with col2:
        contact = st.text_input("Contact", "test@example.com")
        mots_cles = st.text_input("Mots-clés", "test, insertion, manuelle")
    
    submit = st.form_submit_button("Tester l'insertion")
    
    if submit:
        conn = get_db_connection()
        if conn:
            try:
                # Préparation des données de test
                test_csv_data = {
                    "header": ["COD_VAR", "LIB_VAR", "LIB_VAR_LONG", "COD_MOD", "LIB_MOD", "TYPE_VAR", "LONG_VAR"],
                    "data": [
                        ["TEST1", "Test Variable 1", "Variable de test 1", "1", "Mode 1", "NUM", "10"],
                        ["TEST2", "Test Variable 2", "Variable de test 2", "2", "Mode 2", "CHAR", "20"]
                    ],
                    "separator": ";"
                }
                
                # Conversion en JSON
                contenu_csv_json = json.dumps(test_csv_data)
                dictionnaire_json = json.dumps(test_csv_data)  # On utilise les mêmes données pour simplifier
                
                # Insertion
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO metadata (
                            nom_fichier, nom_base, schema, description,
                            date_creation, date_maj, source, frequence_maj,
                            licence, envoi_par, contact, mots_cles, notes,
                            contenu_csv, dictionnaire
                        ) VALUES (
                            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                        )
                    """, (
                        nom_fichier,
                        nom_base,
                        schema,
                        description,
                        datetime.now().date(),
                        datetime.now().date(),
                        source,
                        frequence_maj,
                        "Licence Ouverte",
                        "Test manuel",
                        contact,
                        mots_cles,
                        "Notes de test",
                        contenu_csv_json,
                        dictionnaire_json
                    ))
                    
                    conn.commit()
                    st.success("Insertion réussie !")
                    
                    # Vérification
                    cur.execute("SELECT * FROM metadata WHERE nom_fichier = %s", (nom_fichier,))
                    row = cur.fetchone()
                    if row:
                        st.success(f"Vérification réussie : ligne trouvée avec ID = {row[0]}")
                    else:
                        st.warning("Étrange : la ligne a été insérée mais n'a pas été trouvée lors de la vérification.")
            
            except Exception as e:
                st.error(f"Erreur lors de l'insertion : {str(e)}")
            finally:
                conn.close()
        else:
            st.error("Échec de la connexion à la base de données.")