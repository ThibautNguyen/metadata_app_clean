import streamlit as st
import pandas as pd
import json
import os
import datetime
import re
from io import StringIO
import csv
import sys
import git

# Ajout du chemin pour les modules personnalisés
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Configuration de la page
st.set_page_config(
    page_title="Saisie des Métadonnées",
    page_icon="📝",
    layout="wide"
)

# Titre et description
st.title("Saisie des Métadonnées")
st.markdown("""
Ce formulaire vous permet de créer des fiches de métadonnées pour vos tables de données.
Vous pouvez soit saisir manuellement les informations, soit importer des données pour détection automatique.
""")

# Fonction pour détecter automatiquement le type de données
def detect_data_type(data_content):
    """Détecte automatiquement le type de données (CSV, JSON, etc.)"""
    data_content = data_content.strip()
    
    # Détection JSON
    if (data_content.startswith('{') and data_content.endswith('}')) or \
       (data_content.startswith('[') and data_content.endswith(']')):
        try:
            json.loads(data_content)
            return "json"
        except:
            pass
    
    # Détection CSV
    try:
        df = pd.read_csv(StringIO(data_content), sep=None, engine='python')
        if len(df.columns) > 1:
            return "csv"
    except:
        pass
    
    # Détection texte tabulé
    if '\t' in data_content:
        lines = data_content.split('\n')
        if len(lines) > 1 and '\t' in lines[0]:
            return "tsv"
    
    # Par défaut, format texte
    return "text"

# Fonction pour détecter automatiquement les colonnes depuis un aperçu des données
def detect_columns_from_data(data_preview):
    try:
        # Essayer de détecter le format (CSV, TSV, etc.)
        if ";" in data_preview:
            delimiter = ";"
        elif "\t" in data_preview:
            delimiter = "\t"
        else:
            delimiter = ","
        
        # Lire les données
        df = pd.read_csv(StringIO(data_preview), delimiter=delimiter)
        
        # Créer un dictionnaire pour chaque colonne
        columns = []
        for col in df.columns:
            col_type = "varchar"
            # Déterminer le type de données
            if pd.api.types.is_numeric_dtype(df[col]):
                if all(df[col].dropna().apply(lambda x: int(x) == x if pd.notnull(x) else True)):
                    col_type = "integer"
                else:
                    col_type = "numeric"
            elif pd.api.types.is_datetime64_dtype(df[col]):
                col_type = "timestamp"
            elif pd.api.types.is_bool_dtype(df[col]):
                col_type = "boolean"
            
            columns.append({
                "name": col,
                "type": col_type,
                "description": ""
            })
        
        return columns
    except Exception as e:
        st.error(f"Erreur lors de la détection des colonnes: {str(e)}")
        return []

# Fonction pour convertir les données en format standard
def convert_data(data_content, data_type):
    """Convertit les données au format standard pour le stockage"""
    if data_type == "json":
        return json.loads(data_content)
    
    elif data_type in ["csv", "tsv"]:
        separator = ',' if data_type == "csv" else '\t'
        df = pd.read_csv(StringIO(data_content), sep=separator)
        return df.to_dict(orient="records")
    
    else:  # format texte
        lines = data_content.strip().split('\n')
        return {"content": lines}

# Fonction pour sauvegarder les métadonnées
def save_metadata(metadata, schema, table_name):
    """Sauvegarde les métadonnées dans les dossiers appropriés et synchronise avec Git"""
    # Créer le chemin de dossier si nécessaire
    base_dir = os.path.join(parent_dir, "SGBD", "Metadata")
    schema_dir = os.path.join(base_dir, schema)
    
    os.makedirs(schema_dir, exist_ok=True)
    
    # Créer nom de fichier sécurisé
    safe_name = re.sub(r'[^\w\-\.]', '_', table_name)
    json_path = os.path.join(schema_dir, f"{safe_name}.json")
    txt_path = os.path.join(schema_dir, safe_name)
    
    # Sauvegarder en format JSON
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    # Créer aussi un fichier TXT pour une lecture rapide
    with open(txt_path, 'w', encoding='utf-8') as f:
        f.write(f"Nom de la table: {metadata['table_name']}\n")
        f.write(f"Schéma: {metadata['schema']}\n")
        f.write(f"Description: {metadata['description']}\n")
        f.write(f"Source: {metadata['source']}\n")
        f.write(f"Année: {metadata['year']}\n")
        f.write(f"Contact: {metadata['contact']}\n")
        f.write(f"Date de création: {metadata.get('created_at', datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'))}\n\n")
        
        f.write("Colonnes:\n")
        for col in metadata.get('columns', []):
            f.write(f"- {col['name']} ({col['type']}): {col.get('description', '')}\n")
    
    # Synchroniser avec Git si disponible
    try:
        repo = git.Repo(parent_dir)
        repo.git.add(json_path)
        repo.git.add(txt_path)
        commit_message = f"Ajout/Mise à jour des métadonnées pour {schema}/{table_name}"
        repo.git.commit('-m', commit_message)
        st.success(f"Métadonnées sauvegardées et ajoutées à Git. N'oubliez pas de faire un 'git push' pour synchroniser.")
    except Exception as e:
        st.success(f"Métadonnées sauvegardées avec succès dans {json_path} et {txt_path}")
        st.warning(f"Note: La synchronisation Git n'a pas fonctionné. Erreur: {str(e)}")
    
    return json_path

# Initialisation des variables de session
if "columns" not in st.session_state:
    st.session_state["columns"] = []

# Onglets pour les différentes méthodes d'entrée
tab1, tab2, tab3 = st.tabs(["Saisie manuelle", "Aperçu des données", "Télécharger un fichier"])

with tab1:
    st.markdown("### Saisie manuelle des métadonnées")
    st.info("Remplissez tous les champs pour créer une fiche de métadonnées complète.")

with tab2:
    st.markdown("### Détection automatique depuis un aperçu")
    st.info("Collez un extrait de vos données pour détecter automatiquement la structure.")
    
    data_preview = st.text_area(
        "Collez un extrait de vos données (CSV, Excel, etc.)",
        height=200,
        help="Collez les premières lignes de vos données pour détecter automatiquement les colonnes."
    )
    
    if data_preview:
        if st.button("Détecter les colonnes"):
            st.session_state["detected_columns"] = detect_columns_from_data(data_preview)
            st.success(f"{len(st.session_state['detected_columns'])} colonnes détectées!")

with tab3:
    st.markdown("### Importer depuis un fichier")
    st.info("Téléchargez un fichier pour détecter automatiquement sa structure.")
    
    uploaded_file = st.file_uploader("Choisissez un fichier", type=["csv", "xlsx", "txt", "tsv"])
    
    if uploaded_file is not None:
        try:
            # Détermination du type de fichier
            file_type = uploaded_file.name.split('.')[-1].lower()
            
            if file_type == "json":
                upload_metadata = json.load(uploaded_file)
                st.success("Fichier JSON chargé avec succès!")
                st.json(upload_metadata)
                
            elif file_type in ["csv", "tsv"]:
                separator = ',' if file_type == "csv" else '\t'
                df = pd.read_csv(uploaded_file, sep=separator)
                
                # Détecter les types de colonnes
                columns = []
                for col in df.columns:
                    col_type = "varchar"
                    # Déterminer le type de données
                    if pd.api.types.is_numeric_dtype(df[col]):
                        if all(df[col].dropna().apply(lambda x: int(x) == x if pd.notnull(x) else True)):
                            col_type = "integer"
                        else:
                            col_type = "numeric"
                    elif pd.api.types.is_datetime64_dtype(df[col]):
                        col_type = "timestamp"
                    elif pd.api.types.is_bool_dtype(df[col]):
                        col_type = "boolean"
                    
                    columns.append({
                        "name": col,
                        "type": col_type,
                        "description": ""
                    })
                
                st.session_state["detected_columns"] = columns
                st.success(f"{len(columns)} colonnes détectées!")
                
                # Aperçu des données
                st.subheader("Aperçu")
                st.dataframe(df.head(5))
                
                # Structure des colonnes
                st.subheader("Structure détectée:")
                col_data = []
                for col in columns:
                    col_data.append({"Nom": col["name"], "Type": col["type"], "Description": col["description"]})
                
                st.table(pd.DataFrame(col_data))
                
            elif file_type == "xlsx":
                df = pd.read_excel(uploaded_file)
                
                # Détecter les types de colonnes (même logique que pour CSV)
                columns = []
                for col in df.columns:
                    col_type = "varchar"
                    if pd.api.types.is_numeric_dtype(df[col]):
                        if all(df[col].dropna().apply(lambda x: int(x) == x if pd.notnull(x) else True)):
                            col_type = "integer"
                        else:
                            col_type = "numeric"
                    elif pd.api.types.is_datetime64_dtype(df[col]):
                        col_type = "timestamp"
                    elif pd.api.types.is_bool_dtype(df[col]):
                        col_type = "boolean"
                    
                    columns.append({
                        "name": col,
                        "type": col_type,
                        "description": ""
                    })
                
                st.session_state["detected_columns"] = columns
                st.success(f"{len(columns)} colonnes détectées!")
                
                # Aperçu des données
                st.subheader("Aperçu")
                st.dataframe(df.head(5))
                
                # Structure des colonnes
                st.subheader("Structure détectée:")
                col_data = []
                for col in columns:
                    col_data.append({"Nom": col["name"], "Type": col["type"], "Description": col["description"]})
                
                st.table(pd.DataFrame(col_data))
                
            elif file_type == "txt":
                content = uploaded_file.read().decode("utf-8")
                data_type = detect_data_type(content)
                upload_metadata = convert_data(content, data_type)
                st.success(f"Fichier texte chargé et interprété comme {data_type.upper()}")
                
                # Aperçu
                if isinstance(upload_metadata, list):
                    st.dataframe(pd.DataFrame(upload_metadata).head(5))
                else:
                    st.json(upload_metadata)
                
        except Exception as e:
            st.error(f"Erreur lors de la lecture du fichier: {str(e)}")

# Section d'informations générales et formulaire
st.markdown("---")
st.markdown("## Informations générales")

# Utiliser les colonnes détectées si disponibles
if "detected_columns" in st.session_state and st.session_state["detected_columns"]:
    if st.button("Utiliser les colonnes détectées"):
        st.session_state["columns"] = st.session_state["detected_columns"]
        st.rerun()

# Formulaire pour la saisie des informations générales
with st.form("metadata_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        schema = st.text_input("Schéma", help="Le schéma dans lequel se trouve la table")
        table_name = st.text_input("Nom de la table", help="Le nom de la table dans la base de données")
        year = st.text_input("Année", help="L'année des données (ex: 2023)")
    
    with col2:
        source = st.text_input("Source", help="La source des données (ex: INSEE, Citepa)")
        contact = st.text_input("Contact", help="Personne responsable des données")
    
    description = st.text_area("Description", height=100, help="Description détaillée du contenu de la table")
    
    submitted = st.form_submit_button("Enregistrer les métadonnées")

# Section des colonnes (en dehors du formulaire)
st.markdown("## Colonnes")
st.info("Ajoutez les colonnes de votre table en précisant leur nom, type et description.")

# Bouton pour ajouter une nouvelle colonne
if st.button("Ajouter une colonne"):
    st.session_state["columns"].append({
        "name": "",
        "type": "varchar",
        "description": ""
    })
    st.rerun()

# Affichage des colonnes existantes
for i, col in enumerate(st.session_state["columns"]):
    cols = st.columns([3, 2, 8, 1])
    with cols[0]:
        st.session_state["columns"][i]["name"] = st.text_input(
            f"Nom {i}",
            value=col["name"],
            key=f"col_name_{i}"
        )
    with cols[1]:
        st.session_state["columns"][i]["type"] = st.selectbox(
            f"Type {i}",
            ["varchar", "integer", "numeric", "boolean", "date", "timestamp", "geometry"],
            index=["varchar", "integer", "numeric", "boolean", "date", "timestamp", "geometry"].index(col["type"]) if col["type"] in ["varchar", "integer", "numeric", "boolean", "date", "timestamp", "geometry"] else 0,
            key=f"col_type_{i}"
        )
    with cols[2]:
        st.session_state["columns"][i]["description"] = st.text_input(
            f"Description {i}",
            value=col.get("description", ""),
            key=f"col_desc_{i}"
        )
    with cols[3]:
        if st.button("X", key=f"delete_col_{i}"):
            st.session_state["columns"].pop(i)
            st.rerun()

# Bouton de sauvegarde (en dehors du formulaire)
if submitted:
    if not schema:
        st.error("Veuillez spécifier un schéma")
    elif not table_name:
        st.error("Veuillez spécifier un nom de table")
    else:
        try:
            # Créer le dictionnaire de métadonnées
            metadata = {
                "schema": schema,
                "table_name": table_name,
                "description": description,
                "source": source,
                "year": year,
                "contact": contact,
                "created_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "columns": st.session_state["columns"]
            }
            
            # Sauvegarder les métadonnées
            file_path = save_metadata(metadata, schema, table_name)
            st.success(f"Métadonnées sauvegardées avec succès dans {file_path}")
        except Exception as e:
            st.error(f"Erreur lors de la sauvegarde: {str(e)}") 