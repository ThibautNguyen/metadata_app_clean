import streamlit as st
import os
import json
import pandas as pd
import sys
import requests
import base64
from io import StringIO

# Ajout du chemin pour les modules personnalisés
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Configuration de la page
st.set_page_config(
    page_title="Recherche de Métadonnées",
    page_icon="🔍",
    layout="wide"
)

# Chemin vers le dossier des métadonnées
METADATA_DIR = os.path.join(parent_dir, "SGBD", "Metadata")

# Configuration GitHub (à placer dans le fichier .streamlit/secrets.toml pour le déploiement)
try:
    # Essayer de charger depuis les secrets (pour le déploiement)
    GITHUB_REPO = st.secrets["github"]["repo"]
    GITHUB_BRANCH = st.secrets["github"]["branch"]
    GITHUB_PATH = st.secrets["github"]["metadata_path"]
except Exception:
    # Fallback vers les valeurs par défaut (pour le développement local)
    GITHUB_REPO = "ThibautNguyen/DOCS"
    GITHUB_BRANCH = "main"
    GITHUB_PATH = "SGBD/Metadata"

# Fonction pour charger toutes les métadonnées
def load_all_metadata(source="local"):
    metadata_files = []
    
    if source == "local":
        # Chargement depuis le système de fichiers local
        for root, dirs, files in os.walk(METADATA_DIR):
            for file in files:
                if file.endswith('.json'):
                    file_path = os.path.join(root, file)
                    # Extraire le schéma à partir du chemin
                    schema = os.path.basename(os.path.dirname(file_path))
                    # Extraire le nom de la table à partir du fichier
                    table_name = file.replace('.json', '')
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                            # Ajouter le chemin du fichier
                            metadata['file_path'] = file_path
                            metadata_files.append(metadata)
                    except Exception as e:
                        st.warning(f"Erreur lors de la lecture du fichier {file_path}: {str(e)}")
    
    elif source == "github":
        # Chargement depuis GitHub
        try:
            # Obtenir la liste des fichiers dans le dépôt
            repo_api_url = f"https://api.github.com/repos/{GITHUB_REPO}/git/trees/{GITHUB_BRANCH}?recursive=1"
            response = requests.get(repo_api_url)
            if response.status_code == 200:
                files_data = response.json()
                # Filtrer uniquement les fichiers JSON dans le dossier Metadata
                json_files = [item for item in files_data.get('tree', []) if 
                            item.get('path', '').startswith(GITHUB_PATH) and 
                            item.get('path', '').endswith('.json')]
                
                # Charger chaque fichier JSON
                for file_info in json_files:
                    file_path = file_info.get('path')
                    file_url = f"https://raw.githubusercontent.com/{GITHUB_REPO}/{GITHUB_BRANCH}/{file_path}"
                    
                    try:
                        file_response = requests.get(file_url)
                        if file_response.status_code == 200:
                            # Extraire le schéma à partir du chemin
                            path_parts = file_path.split('/')
                            if len(path_parts) > 2:
                                schema = path_parts[-2]
                                table_name = path_parts[-1].replace('.json', '')
                                
                                metadata = file_response.json()
                                metadata['file_path'] = file_path
                                metadata['github_url'] = file_url
                                metadata_files.append(metadata)
                    except Exception as e:
                        st.warning(f"Erreur lors de la lecture du fichier GitHub {file_path}: {str(e)}")
            else:
                st.error(f"Erreur lors de l'accès à GitHub: {response.status_code} - {response.text}")
        except Exception as e:
            st.error(f"Erreur lors de la connexion à GitHub: {str(e)}")
    
    return metadata_files

# Titre de la page
st.title("Recherche de Métadonnées")
st.markdown("""
Ce module vous permet de rechercher et consulter les fiches de métadonnées existantes.
Utilisez les filtres pour trouver rapidement les informations dont vous avez besoin.
""")

# Sélection de la source de données
data_source = st.radio(
    "Source des métadonnées",
    ["Local", "GitHub"],
    horizontal=True,
    help="Choisissez entre les métadonnées stockées localement ou celles sur GitHub"
)

# Chargement des métadonnées
if data_source == "Local":
    metadata_list = load_all_metadata(source="local")
    st.info(f"Chargement de {len(metadata_list)} fiches de métadonnées depuis le stockage local.")
else:
    with st.spinner("Chargement des métadonnées depuis GitHub..."):
        metadata_list = load_all_metadata(source="github")
    st.info(f"Chargement de {len(metadata_list)} fiches de métadonnées depuis GitHub.")

# Extraction des schémas uniques pour filtrage
schemas = sorted(list(set([m.get('schema', '') for m in metadata_list if 'schema' in m])))
schemas = ['Tous'] + schemas

# Extraction des sources uniques pour filtrage
sources = sorted(list(set([m.get('source', '') for m in metadata_list if 'source' in m])))
sources = ['Toutes'] + sources

# Extraction des années uniques pour filtrage
years = sorted(list(set([m.get('year', '') for m in metadata_list if 'year' in m])))
years = ['Toutes'] + years

# Filtres de recherche
st.markdown("## Filtres de recherche")

col1, col2, col3 = st.columns(3)

with col1:
    schema_filter = st.selectbox("Schéma", schemas)
    
with col2:
    source_filter = st.selectbox("Source", sources)
    
with col3:
    year_filter = st.selectbox("Année", years)

# Recherche textuelle
search_query = st.text_input("Recherche par mot-clé", help="Recherche dans les noms de tables, descriptions et colonnes")

# Filtrage des métadonnées
filtered_metadata = metadata_list

if schema_filter != 'Tous':
    filtered_metadata = [m for m in filtered_metadata if m.get('schema', '') == schema_filter]

if source_filter != 'Toutes':
    filtered_metadata = [m for m in filtered_metadata if m.get('source', '') == source_filter]

if year_filter != 'Toutes':
    filtered_metadata = [m for m in filtered_metadata if m.get('year', '') == year_filter]

if search_query:
    search_query = search_query.lower()
    search_results = []
    
    for metadata in filtered_metadata:
        # Recherche dans le nom de la table
        if 'table_name' in metadata and search_query in metadata['table_name'].lower():
            search_results.append(metadata)
            continue
            
        # Recherche dans la description
        if 'description' in metadata and search_query in metadata['description'].lower():
            search_results.append(metadata)
            continue
            
        # Recherche dans les colonnes
        if 'columns' in metadata:
            for col in metadata['columns']:
                if (('name' in col and search_query in col['name'].lower()) or 
                    ('description' in col and search_query in col['description'].lower())):
                    search_results.append(metadata)
                    break
    
    filtered_metadata = search_results

# Affichage des résultats
st.markdown("## Résultats")
st.info(f"{len(filtered_metadata)} fiche(s) trouvée(s)")

if not filtered_metadata:
    st.warning("Aucune fiche de métadonnées ne correspond à vos critères. Essayez d'élargir votre recherche.")
else:
    # Création d'un DataFrame pour afficher les résultats
    results_data = []
    for metadata in filtered_metadata:
        results_data.append({
            'Schéma': metadata.get('schema', ''),
            'Table': metadata.get('table_name', ''),
            'Source': metadata.get('source', ''),
            'Année': metadata.get('year', ''),
            'Description': metadata.get('description', '')[:100] + '...' if len(metadata.get('description', '')) > 100 else metadata.get('description', ''),
            'Nb colonnes': len(metadata.get('columns', [])),
            'file_path': metadata.get('file_path', '')
        })
    
    results_df = pd.DataFrame(results_data)
    
    # Affichage sous forme de tableau interactif
    st.dataframe(
        results_df.drop(columns=['file_path']),
        column_config={
            'Description': st.column_config.TextColumn(width="large")
        },
        hide_index=True
    )
    
    # Sélection d'une fiche pour afficher les détails
    st.markdown("## Détails d'une fiche")
    
    # Création d'une liste de sélection
    selected_options = [f"{m['Schéma']}.{m['Table']}" for m in results_data]
    selected_item = st.selectbox("Sélectionnez une fiche pour voir les détails", selected_options)
    
    if selected_item:
        # Récupération de la fiche sélectionnée
        selected_schema, selected_table = selected_item.split('.')
        selected_metadata = None
        
        for metadata in filtered_metadata:
            if metadata.get('schema') == selected_schema and metadata.get('table_name') == selected_table:
                selected_metadata = metadata
                break
        
        if selected_metadata:
            st.markdown(f"### {selected_metadata.get('schema')}.{selected_metadata.get('table_name')}")
            
            # Affichage du lien GitHub si disponible
            if 'github_url' in selected_metadata:
                st.markdown(f"[Voir sur GitHub]({selected_metadata['github_url']})")
            
            # Informations générales
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"**Source:** {selected_metadata.get('source', '')}")
            with col2:
                st.markdown(f"**Année:** {selected_metadata.get('year', '')}")
            with col3:
                st.markdown(f"**Contact:** {selected_metadata.get('contact', '')}")
            
            st.markdown(f"**Description:**")
            st.markdown(selected_metadata.get('description', ''))
            
            # Colonnes
            st.markdown("### Colonnes")
            
            if 'columns' in selected_metadata and selected_metadata['columns']:
                columns_data = []
                for col in selected_metadata['columns']:
                    columns_data.append({
                        'Nom': col.get('name', ''),
                        'Type': col.get('type', ''),
                        'Description': col.get('description', '')
                    })
                
                columns_df = pd.DataFrame(columns_data)
                st.dataframe(columns_df, hide_index=True)
            else:
                st.warning("Aucune information sur les colonnes n'est disponible.")
            
            # Option pour afficher le JSON brut
            with st.expander("Afficher le JSON brut"):
                st.json(selected_metadata)
            
            # Suggestion de documentation SQL
            st.markdown("### Documentation SQL")
            
            sql_doc = f"""```sql
-- Exemple de requête SQL pour {selected_metadata.get('schema')}.{selected_metadata.get('table_name')}
SELECT 
    {', '.join([f'"{col.get("name")}"' for col in selected_metadata.get('columns', [])[:5]])}
    {', ...' if len(selected_metadata.get('columns', [])) > 5 else ''}
FROM {selected_metadata.get('schema')}.{selected_metadata.get('table_name')}
LIMIT 10;
```"""
            st.markdown(sql_doc) 