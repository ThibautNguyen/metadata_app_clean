import streamlit as st
import pandas as pd
import json
import os
import glob
import re
import sys
import requests
import base64
from io import StringIO, BytesIO

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

# Titre et description
st.title("Recherche de Métadonnées")
st.markdown("""
Ce module vous permet de rechercher et consulter les fiches de métadonnées existantes.
Utilisez les filtres pour trouver rapidement les informations dont vous avez besoin.
""")

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
    """Charge toutes les métadonnées disponibles"""
    metadata_files = []
    
    if source == "local":
        # Chargement depuis le système de fichiers local
        base_dir = os.path.join(parent_dir, "SGBD", "Metadata")
        metadata_files_paths = glob.glob(f"{base_dir}/**/*.json", recursive=True)
        
        for file_path in metadata_files_paths:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Adapter le format pour correspondre à la structure attendue
                    if "table_name" in data and "schema" in data:
                        # Format original
                        data["file_path"] = file_path
                        metadata_files.append(data)
                    elif "_metadata" in data:
                        # Format de la nouvelle version
                        meta_info = data["_metadata"]
                        meta_info["file_path"] = file_path
                        
                        # Adapter au format attendu
                        meta_info["table_name"] = meta_info.get("name", "")
                        meta_info["schema"] = meta_info.get("category", "")
                        
                        # Fusionner avec le reste des données
                        metadata = {**data, **meta_info}
                        del metadata["_metadata"]  # Éviter les duplications
                        metadata_files.append(metadata)
                    else:
                        # Format inconnu
                        schema = os.path.basename(os.path.dirname(file_path))
                        table_name = os.path.basename(file_path).replace('.json', '')
                        
                        data["file_path"] = file_path
                        data["table_name"] = table_name
                        data["schema"] = schema
                        data["last_modified"] = "N/A"
                        metadata_files.append(data)
            except Exception as e:
                st.warning(f"Erreur lors du chargement de {file_path}: {str(e)}")
    
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
                                
                                try:
                                    metadata = file_response.json()
                                    
                                    # Adapter le format pour correspondre à la structure attendue
                                    if "table_name" not in metadata:
                                        metadata["table_name"] = table_name
                                    if "schema" not in metadata:
                                        metadata["schema"] = schema
                                    
                                    metadata["file_path"] = file_path
                                    metadata["github_url"] = file_url
                                    metadata_files.append(metadata)
                                except Exception as e:
                                    st.warning(f"Erreur lors de l'analyse du fichier JSON {file_path}: {str(e)}")
                    except Exception as e:
                        st.warning(f"Erreur lors de la lecture du fichier GitHub {file_path}: {str(e)}")
            else:
                st.error(f"Erreur lors de l'accès à GitHub: {response.status_code} - {response.text}")
        except Exception as e:
            st.error(f"Erreur lors de la connexion à GitHub: {str(e)}")
    
    return metadata_files

# Fonction pour rechercher dans les métadonnées avec filtres avancés
def search_metadata(metadata_list, search_text="", schema=None, source=None, year=None, date_range=None):
    """Filtre les métadonnées selon les critères de recherche avancés"""
    results = []
    
    search_text = search_text.lower() if search_text else ""
    
    for metadata in metadata_list:
        # Filtrer par schéma si spécifié
        if schema and schema != "Tous" and metadata.get("schema", "") != schema:
            continue
        
        # Filtrer par source si spécifiée
        if source and source != "Toutes" and metadata.get("source", "") != source:
            continue
        
        # Filtrer par année si spécifiée
        if year and year != "Toutes":
            meta_year = metadata.get("year", "")
            if not meta_year or str(meta_year) != str(year):
                continue
        
        # Filtrer par date si spécifiée
        if date_range:
            # Format de date attendu: "YYYY-MM-DD"
            last_modified = metadata.get("last_modified", metadata.get("created_at", ""))
            if last_modified:
                if isinstance(last_modified, str):
                    date_part = last_modified.split(" ")[0]
                    if date_part < date_range[0] or date_part > date_range[1]:
                        continue
        
        # Filtrer par texte de recherche si spécifié
        if search_text:
            match_found = False
            
            # Recherche dans le nom de la table
            if "table_name" in metadata and search_text in metadata["table_name"].lower():
                match_found = True
            
            # Recherche dans la description
            elif "description" in metadata and isinstance(metadata["description"], str) and search_text in metadata["description"].lower():
                match_found = True
            
            # Recherche dans les colonnes
            elif "columns" in metadata:
                for col in metadata["columns"]:
                    if (("name" in col and search_text in col["name"].lower()) or 
                        ("description" in col and isinstance(col["description"], str) and search_text in col["description"].lower())):
                        match_found = True
                        break
            
            # Recherche dans d'autres champs
            else:
                for key, value in metadata.items():
                    if isinstance(value, str) and search_text in value.lower():
                        match_found = True
                        break
            
            if not match_found:
                continue
        
        results.append(metadata)
    
    return results

# Fonction pour charger le contenu complet d'un fichier de métadonnées
def load_metadata_content(file_path, is_github_url=False):
    """Charge le contenu complet d'un fichier de métadonnées"""
    try:
        if is_github_url:
            # Chargement depuis GitHub
            response = requests.get(file_path)
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Erreur lors du chargement depuis GitHub: {response.status_code}")
                return None
        else:
            # Chargement depuis le système de fichiers local
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        st.error(f"Erreur lors du chargement du fichier: {str(e)}")
        return None

# Sélection de la source des métadonnées
data_source = st.radio(
    "Source des métadonnées",
    ["Local", "GitHub"],
    horizontal=True,
    help="Choisissez entre les métadonnées stockées localement ou celles sur GitHub"
)

# Chargement des métadonnées
if data_source == "Local":
    all_metadata = load_all_metadata(source="local")
    st.success(f"Chargement de {len(all_metadata)} fiches de métadonnées depuis le stockage local.")
else:
    with st.spinner("Chargement des métadonnées depuis GitHub..."):
        all_metadata = load_all_metadata(source="github")
    st.success(f"Chargement de {len(all_metadata)} fiches de métadonnées depuis GitHub.")

# Extraction des schémas uniques
schemas = sorted(list(set([m.get('schema', '') for m in all_metadata if 'schema' in m and m['schema']])))
schemas = ['Tous'] + schemas

# Extraction des sources uniques
sources = sorted(list(set([m.get('source', '') for m in all_metadata if 'source' in m and m['source']])))
sources = ['Toutes'] + sources

# Extraction des années uniques
years = sorted(list(set([str(m.get('year', '')) for m in all_metadata if 'year' in m and m['year']])))
years = ['Toutes'] + years

# Filtres de recherche
st.markdown("## Filtres de recherche")

# Onglets pour recherche simple/avancée
tab1, tab2 = st.tabs(["Recherche simple", "Recherche avancée"])

with tab1:
    # Filtres simples sur une ligne
    col1, col2, col3 = st.columns(3)
    
    with col1:
        schema_filter = st.selectbox("Schéma", schemas)
    
    with col2:
        source_filter = st.selectbox("Source", sources)
    
    with col3:
        year_filter = st.selectbox("Année", years)
    
    # Recherche textuelle
    search_text = st.text_input("Recherche par mot-clé", 
                             placeholder="Recherche dans les noms de tables, descriptions et colonnes")

with tab2:
    # Recherche avancée avec plus d'options
    adv_search_text = st.text_input("Recherche par mot-clé (avancée)", 
                                  placeholder="Recherche dans tous les champs")
    
    col1, col2 = st.columns(2)
    
    with col1:
        adv_schema_filter = st.selectbox("Schéma (avancé)", schemas)
        adv_source_filter = st.selectbox("Source (avancée)", sources)
    
    with col2:
        adv_year_filter = st.selectbox("Année (avancée)", years)
        
        # Filtre par date de modification
        use_date_filter = st.checkbox("Filtrer par date de modification")
        
        if use_date_filter:
            date_from = st.date_input("De", value=None)
            date_to = st.date_input("À", value=None)
            
            if date_from and date_to:
                date_range = [str(date_from), str(date_to)]
            else:
                date_range = None
        else:
            date_range = None

# Décider quels paramètres de recherche utiliser
active_tab = 0  # Par défaut, onglet 1 (Recherche simple)
if tab2:
    active_tab = 1  # Si l'onglet 2 est actif

if active_tab == 0:  # Recherche simple
    final_search_text = search_text
    final_schema = schema_filter
    final_source = source_filter
    final_year = year_filter
    final_date_range = None
else:  # Recherche avancée
    final_search_text = adv_search_text
    final_schema = adv_schema_filter
    final_source = adv_source_filter
    final_year = adv_year_filter
    final_date_range = date_range

# Bouton de recherche
if st.button("Rechercher") or True:  # Auto-recherche 
    results = search_metadata(all_metadata, final_search_text, final_schema, final_source, final_year, final_date_range)
    
    # Afficher les résultats
    st.subheader(f"Résultats ({len(results)} trouvés)")
    
    if not results:
        st.info("Aucun résultat trouvé. Essayez d'autres critères de recherche.")
    else:
        # Convertir les résultats en DataFrame pour un affichage plus propre
        df_results = []
        for metadata in results:
            # Extraire les champs à afficher dans le tableau
            result_row = {
                "Nom": metadata.get("table_name", metadata.get("name", "N/A")),
                "Schéma": metadata.get("schema", metadata.get("category", "N/A")),
                "Source": metadata.get("source", "N/A"),
                "Année": metadata.get("year", "N/A"),
                "Description": metadata.get("description", "")[:50] + "..." if metadata.get("description", "") and len(metadata.get("description", "")) > 50 else metadata.get("description", ""),
                "Dernière modification": metadata.get("last_modified", metadata.get("created_at", "N/A"))
            }
            df_results.append(result_row)
        
        # Création du DataFrame
        df_display = pd.DataFrame(df_results)
        
        # Ajouter un index pour identifier les lignes
        df_display.insert(0, "#", range(1, len(df_display) + 1))
        
        # Afficher le tableau des résultats
        st.dataframe(df_display, use_container_width=True)
        
        # Sélectionner un résultat pour voir les détails
        st.subheader("Détails")
        selected_idx = st.selectbox("Sélectionnez un résultat pour voir les détails", 
                                  range(len(results)),
                                  format_func=lambda i: f"{i+1}. {results[i].get('table_name', results[i].get('name', 'N/A'))}")
        
        if selected_idx is not None:
            selected_result = results[selected_idx]
            
            # Afficher les informations de base
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Nom de la table:** {selected_result.get('table_name', selected_result.get('name', 'N/A'))}")
                st.write(f"**Schéma:** {selected_result.get('schema', selected_result.get('category', 'N/A'))}")
                st.write(f"**Source:** {selected_result.get('source', 'N/A')}")
            
            with col2:
                st.write(f"**Année:** {selected_result.get('year', 'N/A')}")
                st.write(f"**Contact:** {selected_result.get('contact', 'N/A')}")
                st.write(f"**Dernière modification:** {selected_result.get('last_modified', selected_result.get('created_at', 'N/A'))}")
            
            st.markdown("---")
            
            # Afficher la description complète
            if "description" in selected_result and selected_result["description"]:
                st.subheader("Description")
                st.write(selected_result["description"])
                st.markdown("---")
            
            # Charger et afficher le contenu complet
            file_path = selected_result.get("file_path")
            github_url = selected_result.get("github_url")
            
            if github_url:
                content = load_metadata_content(github_url, is_github_url=True)
            elif file_path:
                content = load_metadata_content(file_path)
            else:
                content = None
                st.warning("Chemin de fichier non disponible pour ce résultat.")
                
            if content:
                # Afficher les colonnes s'il y en a
                if "columns" in content and isinstance(content["columns"], list) and content["columns"]:
                    st.subheader("Structure des données")
                    col_data = []
                    for col in content["columns"]:
                        col_data.append({
                            "Nom": col.get("name", "N/A"),
                            "Type": col.get("type", "N/A"),
                            "Description": col.get("description", "")
                        })
                    st.table(pd.DataFrame(col_data))
                    st.markdown("---")
                
                # Afficher les données en colonnes pour les options d'export
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    # Afficher un aperçu des données si disponible
                    if "data_sample" in content and isinstance(content["data_sample"], list) and content["data_sample"]:
                        st.subheader("Aperçu des données")
                        st.dataframe(pd.DataFrame(content["data_sample"]))
                        st.markdown("---")
                    
                    # Afficher le contenu JSON complet (en excluant les champs déjà affichés)
                    st.subheader("Contenu complet (JSON)")
                    
                    # Créer une copie pour l'affichage
                    display_content = {}
                    for key, value in content.items():
                        if key not in ["file_path", "github_url", "_metadata"]:
                            display_content[key] = value
                    
                    st.json(display_content)
                
                with col2:
                    # Options d'exportation
                    st.subheader("Exporter")
                    export_format = st.radio("Format:", ["JSON", "CSV", "Excel", "TXT"], horizontal=False)
                    
                    if st.button("Télécharger"):
                        if export_format == "JSON":
                            # Exporter en JSON
                            json_str = json.dumps(display_content, indent=2, ensure_ascii=False)
                            st.download_button(
                                label="Télécharger JSON",
                                data=json_str,
                                file_name=f"{selected_result.get('table_name', 'data')}.json",
                                mime="application/json"
                            )
                        
                        elif export_format == "CSV":
                            # Exporter en CSV
                            try:
                                # Tenter de créer un DataFrame à partir du contenu
                                if "columns" in content and "data_sample" in content:
                                    # Créer un DataFrame vide avec les colonnes définies
                                    df = pd.DataFrame(columns=[c["name"] for c in content["columns"]])
                                    
                                    # Ajouter les données d'exemple si disponibles
                                    if content["data_sample"]:
                                        df = pd.DataFrame(content["data_sample"])
                                
                                elif isinstance(content.get("data_sample"), list):
                                    df = pd.DataFrame(content["data_sample"])
                                
                                elif "columns" in content:
                                    # Créer un DataFrame vide avec seulement les colonnes
                                    df = pd.DataFrame(columns=[c["name"] for c in content["columns"]])
                                
                                else:
                                    # Convertir le dictionnaire en DataFrame plat
                                    df = pd.json_normalize(display_content)
                                
                                csv = df.to_csv(index=False)
                                st.download_button(
                                    label="Télécharger CSV",
                                    data=csv,
                                    file_name=f"{selected_result.get('table_name', 'data')}.csv",
                                    mime="text/csv"
                                )
                            except Exception as e:
                                st.error(f"Impossible de convertir en CSV: {str(e)}")
                        
                        elif export_format == "Excel":
                            # Exporter en Excel
                            try:
                                # Même logique que pour le CSV
                                if "columns" in content and "data_sample" in content:
                                    df = pd.DataFrame(columns=[c["name"] for c in content["columns"]])
                                    if content["data_sample"]:
                                        df = pd.DataFrame(content["data_sample"])
                                
                                elif isinstance(content.get("data_sample"), list):
                                    df = pd.DataFrame(content["data_sample"])
                                
                                elif "columns" in content:
                                    df = pd.DataFrame(columns=[c["name"] for c in content["columns"]])
                                
                                else:
                                    df = pd.json_normalize(display_content)
                                
                                # Créer un buffer pour le fichier Excel
                                output = BytesIO()
                                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                                    df.to_excel(writer, sheet_name='Métadonnées', index=False)
                                
                                excel_data = output.getvalue()
                                st.download_button(
                                    label="Télécharger Excel",
                                    data=excel_data,
                                    file_name=f"{selected_result.get('table_name', 'data')}.xlsx",
                                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                                )
                            except Exception as e:
                                st.error(f"Impossible de convertir en Excel: {str(e)}")
                        
                        elif export_format == "TXT":
                            # Créer un fichier texte simple
                            try:
                                txt_content = f"Nom de la table: {selected_result.get('table_name', selected_result.get('name', 'N/A'))}\n"
                                txt_content += f"Schéma: {selected_result.get('schema', selected_result.get('category', 'N/A'))}\n"
                                txt_content += f"Description: {selected_result.get('description', 'N/A')}\n"
                                txt_content += f"Source: {selected_result.get('source', 'N/A')}\n"
                                txt_content += f"Année: {selected_result.get('year', 'N/A')}\n"
                                txt_content += f"Contact: {selected_result.get('contact', 'N/A')}\n"
                                txt_content += f"Dernière modification: {selected_result.get('last_modified', selected_result.get('created_at', 'N/A'))}\n\n"
                                
                                if "columns" in content and isinstance(content["columns"], list):
                                    txt_content += "Colonnes:\n"
                                    for col in content["columns"]:
                                        txt_content += f"- {col.get('name', 'N/A')} ({col.get('type', 'N/A')}): {col.get('description', '')}\n"
                                
                                st.download_button(
                                    label="Télécharger TXT",
                                    data=txt_content,
                                    file_name=f"{selected_result.get('table_name', 'data')}.txt",
                                    mime="text/plain"
                                )
                            except Exception as e:
                                st.error(f"Impossible de créer le fichier TXT: {str(e)}")
                    
                    # Lien vers la source
                    if github_url:
                        st.markdown("---")
                        st.subheader("Lien source")
                        github_view_url = github_url.replace("raw.githubusercontent.com", "github.com").replace(f"/{GITHUB_BRANCH}/", f"/blob/{GITHUB_BRANCH}/")
                        st.markdown(f"[Voir sur GitHub]({github_view_url})")
                    
                    # Actions supplémentaires
                    st.markdown("---")
                    st.subheader("Actions")
                    
                    if st.button("Éditer cette fiche"):
                        st.session_state["edit_metadata"] = selected_result
                        st.info("Fonctionnalité d'édition en développement. Veuillez utiliser l'onglet de saisie pour modifier cette fiche.")
                    
                    if st.button("Créer une copie"):
                        st.session_state["copy_metadata"] = selected_result
                        st.info("Fonctionnalité de copie en développement. Veuillez utiliser l'onglet de saisie pour créer une nouvelle fiche basée sur celle-ci.") 