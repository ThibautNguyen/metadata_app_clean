import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import os
import pandas as pd
import sys
from pathlib import Path
import json
import io
import csv
import unicodedata
import logging
import psycopg2.extras
from utils.db_utils import test_connection, init_db, get_metadata, get_metadata_columns
import importlib
from utils.auth import authenticate_and_logout
from utils.sql_generator import display_sql_generation_interface_new

# Configuration de la page
st.set_page_config(
    page_title="Catalogue de données",
    page_icon="📊",
    layout="wide"
)

# Authentification centralisée (présente sur toutes les pages)
name, authentication_status, username, authenticator = authenticate_and_logout()

# Ajout du répertoire parent au PYTHONPATH
sys.path.append(str(Path(__file__).parent))

def remove_accents(input_str):
    """Supprime les accents d'une chaîne de caractères"""
    nfkd_form = unicodedata.normalize('NFKD', input_str)
    return ''.join([c for c in nfkd_form if not unicodedata.combining(c)])

def highlight_text(text, search_term):
    """Met en surbrillance le terme recherché dans le texte"""
    if not text or not search_term:
        return text
    try:
        # Convertir en minuscules pour la comparaison
        text_lower = str(text).lower()
        search_lower = str(search_term).lower()
        
        # Trouver toutes les occurrences du terme recherché
        start = 0
        highlighted_text = str(text)  # Conserver le texte original
        while True:
            pos = text_lower.find(search_lower, start)
            if pos == -1:
                break
            # Remplacer uniquement la partie correspondante dans le texte original
            original_part = text[pos:pos+len(search_term)]
            highlighted_text = highlighted_text[:pos] + f'<span style="background-color: #FFFF00">{original_part}</span>' + highlighted_text[pos+len(search_term):]
            start = pos + len(search_term)
        return highlighted_text
    except Exception as e:
        logging.error(f"Erreur lors de la mise en surbrillance : {str(e)}")
        return text

# CSS pour le style de l'interface
st.markdown("""
<style>
    /* Styles généraux */
    .main {
        max-width: 1200px;
        margin: 0 auto;
    }
    
    /* Style du titre */
    .main h1 {
        color: #1E4B88;
        font-size: 2.2rem;
        margin-bottom: 0.8rem;
    }
    
    /* Style des titres de section */
    .main h2 {
        color: #333;
        font-size: 1.5rem;
        margin-top: 1.5rem;
        margin-bottom: 1rem;
        padding-bottom: 0.5rem;
        border-bottom: 1px solid #e0e0e0;
    }
    
    /* Style des conteneurs */
    .stExpander {
        border: 1px solid #e0e0e0;
        border-radius: 5px;
        margin-bottom: 1rem;
    }
    
    /* Style des boutons */
    .stButton button {
        background-color: #1E88E5;
        color: white;
        font-weight: 500;
        border-radius: 4px;
    }
    
    /* Style du bouton de recherche */
    .stButton.search button {
        background-color: #4CAF50;
        width: 100%;
    }
    
    /* Style des messages d'information */
    .stInfo {
        background-color: #E3F2FD;
        padding: 16px;
        border-radius: 5px;
        border-left: 5px solid #1E88E5;
    }
    
    /* Style des messages d'avertissement */
    .stWarning {
        background-color: #FFF8E1;
        padding: 16px;
        border-radius: 5px;
        border-left: 5px solid #FFC107;
    }
    
    /* Style des messages d'erreur */
    .stError {
        background-color: #FFEBEE;
        padding: 16px;
        border-radius: 5px;
        border-left: 5px solid #F44336;
    }
    
    /* Style des tableaux */
    .stDataFrame {
        border: 1px solid #e0e0e0;
        border-radius: 5px;
    }
    
    /* Style des cases à cocher */
    .stCheckbox label {
        font-weight: 500;
        color: #333;
    }
    
    /* Style des conteneurs expandables */
    button[data-baseweb="accordion"] {
        background-color: #f8f9fa;
        border-radius: 5px;
        margin-bottom: 8px;
        border-left: 4px solid #1E88E5;
    }
    
    /* Style des liens de téléchargement */
    .stDownloadButton button {
        background-color: #4CAF50;
        color: white;
    }
    
    /* Style pour les blocs de code */
    .stCode {
        background-color: #f5f5f5;
        border-radius: 5px;
        border: 1px solid #e0e0e0;
    }
    
    /* Style pour les onglets */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1rem;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 0.5rem 1rem;
        font-size: 1rem;
        font-weight: 500;
    }
    .stTabs [data-baseweb="tab-highlight"] {
        background-color: #1E88E5;
    }
    
    /* Style pour les entrées de recherche */
    .stTextInput > div > div {
        border-radius: 5px;
    }
    .stTextInput input {
        font-size: 1rem;
    }
    
    /* Style pour le sélecteur */
    .stSelectbox > div > div {
        border-radius: 5px;
    }
    
    /* Style pour les expanders de résultats */
    .metadata-result {
        border-left: 4px solid #1E88E5;
        margin-bottom: 1rem;
        background-color: #f8f9fa;
    }
    
    /* Style pour les expanders d'aide */
    .help-section {
        margin-top: 2rem;
        padding-top: 1rem;
        border-top: 1px solid #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)

# Titre et description
st.title("Catalogue des métadonnées")
st.write("Consultez et recherchez les métadonnées disponibles.")

# Initialisation automatique de la base de données
try:
    init_db()
except Exception as e:
    st.error(f"Erreur lors de l'initialisation : {str(e)}")

# Interface de recherche
st.subheader("Recherche")
st.write("La recherche s'effectue dans les champs suivants : nom du jeu de données, producteur de la donnée, description et dictionnaire des variables.")

col1, col2, col3 = st.columns([3, 1, 2])

with col1:
    search_text = st.text_input("Rechercher", placeholder="Entrez un terme à rechercher...")

with col2:
    selected_schema = st.selectbox("Filtrer par schéma", 
                                ["Tous", "economie", "education", "energie", "environnement", 
                                 "geo", "logement", "mobilite", "population", "reseau", "securite"])

# Récupération des métadonnées depuis la base de données (avant filtre producteur)
if search_text:
    schema_filter = selected_schema if selected_schema != "Tous" else None
    metadata_results = get_metadata(search_text, schema_filter)
elif selected_schema and selected_schema != "Tous":
    metadata_results = get_metadata(None, selected_schema)
else:
    metadata_results = get_metadata()

# --- Ajout du filtre producteur ---
# Extraire la liste des producteurs uniques
if metadata_results:
    producteurs_uniques = sorted(list({meta.get('producteur', '') for meta in metadata_results if meta.get('producteur', '')}))
    producteurs_options = ["Tous"] + producteurs_uniques
else:
    producteurs_options = ["Tous"]

with col3:
    selected_producteur = st.selectbox("Filtrer par producteur", producteurs_options)

# Appliquer le filtre producteur si sélectionné
if selected_producteur != "Tous":
    metadata_results = [meta for meta in metadata_results if meta.get('producteur', '') == selected_producteur]

# Affichage du nombre total de résultats
st.info(f"Nombre total de métadonnées disponibles : {len(metadata_results)}")

# Affichage des résultats
if not metadata_results:
    st.info("Aucun résultat trouvé.")
else:
    # Création du DataFrame avec les colonnes principales
    if metadata_results:
        # Si les résultats sont des dicts
        if isinstance(metadata_results[0], dict):
            data_list = []
            for meta in metadata_results:
                data_dict = {
                    'Nom du jeu de données': meta.get('nom_jeu_donnees', ''),
                    'Nom de la table': meta.get('nom_table', ''),
                    'Producteur de la donnée': meta.get('producteur', ''),
                    'Schéma du SGBD': meta.get('schema', ''),
                    'Granularité géographique': meta.get('granularite_geo', ''),
                    'Millésime/année': meta.get('millesime', '') if meta.get('millesime') else '',
                    'Date de publication': meta.get('date_publication', '').strftime('%d-%m-%Y') if meta.get('date_publication') else '',
                }
                data_list.append(data_dict)
            df = pd.DataFrame(data_list)
        else:
            # fallback: ancienne logique (index)
            data_list = []
            for meta in metadata_results:
                data_dict = {
                    'Nom du jeu de données': meta[5] if len(meta) > 5 and meta[5] else '',
                    'Nom de la table': meta[17] if len(meta) > 17 and meta[17] else '',
                    'Producteur de la donnée': meta[2] if len(meta) > 2 and meta[2] else '',
                    'Schéma du SGBD': meta[3] if len(meta) > 3 and meta[3] else '',
                    'Granularité géographique': meta[18] if len(meta) > 18 and meta[18] else '',
                    'Millésime/année': meta[8] if len(meta) > 8 and meta[8] else '',
                    'Date de publication': meta[9].strftime('%d-%m-%Y') if len(meta) > 9 and meta[9] else '',
                }
                data_list.append(data_dict)
            df = pd.DataFrame(data_list)
        # Affichage du nombre de résultats
        st.write(f"**{len(metadata_results)} résultat(s) trouvé(s)**")
        # Mise en forme conditionnelle
        def highlight_search_term(val):
            if search_text and isinstance(val, str):
                if search_text.lower() in val.lower():
                    return 'background-color: yellow'
            return ''
        styled_df = df.style.map(highlight_search_term, subset=['Nom du jeu de données', 'Nom de la table', 'Producteur de la donnée'])
        # Création d'un conteneur pour le tableau (comme dans la page de suivi)
        table_container = st.container()
        
        with table_container:
            st.dataframe(
                styled_df,
                column_config={
                    "Nom du jeu de données": st.column_config.TextColumn(
                        "Nom du jeu de données",
                        help="Nom du jeu de données (regroupement logique)"
                    ),
                    "Nom de la table": st.column_config.TextColumn(
                        "Nom de la table",
                        help="Nom de la table dans la base de données"
                    ),
                    "Producteur de la donnée": st.column_config.TextColumn(
                        "Producteur de la donnée",
                        help="Organisme producteur des données"
                    ),
                    "Date de publication": st.column_config.TextColumn(
                        "Date de publication",
                        help="Date de publication de la table"
                    )
                },
                hide_index=True,
                use_container_width=True
            )

        # Affichage détaillé des métadonnées
        for i, meta in enumerate(metadata_results):
            with st.expander(f"📄 {meta['nom_table'] if meta['nom_table'] else 'Métadonnée ' + str(i+1)}", expanded=False):
                st.markdown('<div class="metadata-result">', unsafe_allow_html=True)
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 📋 Informations de base")
                    st.write(f"**Nom du jeu de données :** {meta['nom_jeu_donnees'] if meta['nom_jeu_donnees'] else 'Non spécifié'}")
                    st.write(f"**Producteur :** {meta['producteur'] if meta['producteur'] else 'Non spécifié'}")
                    st.write(f"**Schéma :** {meta['schema'] if meta['schema'] else 'Non spécifié'}")
                    st.write(f"**Millésime :** {meta['millesime'] if meta['millesime'] else 'Non spécifié'}")
                    st.write(f"**Date de publication :** {meta['date_publication'].strftime('%d-%m-%Y') if meta['date_publication'] else 'Non spécifié'}")
                    st.write(f"**Fréquence de mise à jour :** {meta['frequence_maj'] if meta['frequence_maj'] else 'Non spécifié'}")
                    st.write(f"**Type de données :** {meta['type_donnees'] if meta['type_donnees'] else 'Non spécifié'}")
                    
                with col2:
                    st.markdown("### 📝 Description")
                    st.write(meta['description'] if meta['description'] else "Aucune description disponible")
                    
                    if meta['source']:  # URL source
                        st.markdown("#### 🔗 Source des données")
                        st.write(f"[Lien vers les données]({meta['source']})")
                
                # Affichage des données et du dictionnaire des variables dans des onglets (dictionnaire en premier)
                if meta['contenu_csv'] and meta['dictionnaire']:
                    tab1, tab2 = st.tabs(["Dictionnaire des variables", "Aperçu des données"])
                    with tab1:
                        try:
                            # Conversion du dictionnaire en DataFrame
                            if isinstance(meta['dictionnaire'], str):
                                try:
                                    if meta['separateur']:
                                        dict_data = pd.read_csv(io.StringIO(meta['dictionnaire']), sep=meta['separateur'])
                                    else:
                                        dict_data = pd.read_csv(io.StringIO(meta['dictionnaire']), sep=';')
                                except:
                                    try:
                                        dict_data = pd.read_csv(io.StringIO(meta['dictionnaire']), sep=',')
                                    except:
                                        dict_data = None
                            elif isinstance(meta['dictionnaire'], dict) and 'data' in meta['dictionnaire']:
                                headers = meta['dictionnaire'].get('header', [])
                                data = meta['dictionnaire'].get('data', [])
                                dict_data = pd.DataFrame(data, columns=headers)
                            else:
                                dict_data = None
                            if dict_data is not None and not dict_data.empty:
                                def highlight_search_term_dict(val):
                                    if search_text and isinstance(val, str):
                                        if search_text.lower() in val.lower():
                                            return 'background-color: yellow'
                                    return ''
                                styled_dict_data = dict_data.style.map(highlight_search_term_dict)
                                st.dataframe(styled_dict_data, use_container_width=True)
                            else:
                                st.info("Aucune information sur les variables disponible")
                        except Exception as e:
                            st.error(f"Erreur lors du chargement du dictionnaire des variables : {str(e)}")
                    with tab2:
                        try:
                            if isinstance(meta['contenu_csv'], str):
                                try:
                                    if meta['separateur']:
                                        csv_data = pd.read_csv(io.StringIO(meta['contenu_csv']), sep=meta['separateur'], nrows=4)
                                    else:
                                        csv_data = pd.read_csv(io.StringIO(meta['contenu_csv']), sep=';', nrows=4)
                                except:
                                    try:
                                        csv_data = pd.read_csv(io.StringIO(meta['contenu_csv']), sep=',', nrows=4)
                                    except:
                                        csv_data = None
                            elif isinstance(meta['contenu_csv'], dict) and 'data' in meta['contenu_csv']:
                                headers = meta['contenu_csv'].get('header', [])
                                data = meta['contenu_csv'].get('data', [])
                                csv_data = pd.DataFrame(data, columns=headers)
                                csv_data = csv_data.head(4)
                            else:
                                csv_data = None
                            if csv_data is not None and not csv_data.empty:
                                st.dataframe(csv_data, use_container_width=True)
                            else:
                                st.info("Aucune donnée disponible")
                        except Exception as e:
                            st.info("Erreur lors du chargement des données")
                            st.error(str(e))
                
                # Séparateur visuel
                st.markdown("---")
                
                # Section de génération SQL (visible pour toutes les tables)
                st.markdown("### 🔧 Génération du script SQL d'import")
                col_sql1, col_sql2 = st.columns([3, 1])
                with col_sql1:
                    st.info("Générez automatiquement le script SQL d'import pour cette table.")
                with col_sql2:
                    debug_mode = st.checkbox("Mode debug", key=f"debug_{meta['nom_table']}", help="Affiche des informations supplémentaires pour le débogage")
                
                if st.button("Générer le script SQL d'import", key=f"sql_btn_{meta['nom_table']}", type="primary"):
                    display_sql_generation_interface_new(meta['nom_table'], debug_mode=debug_mode)
                
                st.markdown('</div>', unsafe_allow_html=True)

# Section d'aide et informations
st.markdown('<div class="help-section">', unsafe_allow_html=True)
with st.expander("❓ Aide et informations"):
    st.markdown("""
    ### Comment utiliser ce catalogue
    
    - **Recherche** : Saisissez un terme dans le champ de recherche pour filtrer les métadonnées. La recherche s'effectue dans le nom de la base, le nom de la table, le producteur, la description, le schéma, la source, la licence et la personne ayant rempli le formulaire.
    - **Filtre par schéma** : Utilisez le menu déroulant pour filtrer par schéma de base de données.
    - **Consulter les détails** : Cochez la case "Afficher les détails complets" pour voir toutes les informations, y compris le contenu CSV et le dictionnaire des variables si disponibles.
    
    ### Structure des métadonnées
    
    Les métadonnées sont structurées avec les informations suivantes :
    - **Informations de base** : Nom de la base, nom de la table, producteur, schéma, granularité géographique, millésime, date de mise à jour
    - **Informations supplémentaires** : Source, fréquence de mise à jour, licence, personne remplissant le formulaire
    - **Description** : Explication détaillée des données
    - **Contenu CSV** : Les premières lignes du fichier pour comprendre sa structure
    - **Dictionnaire des variables** : Description détaillée des variables du jeu de données
    """)

# Section de mapping des colonnes (visible uniquement si expanded)
with st.expander("🔍 Mapping des colonnes de la base de données"):
    # Récupérer les colonnes de la base de données
    db_columns = get_metadata_columns()
    
    # Définir le mapping entre les colonnes de la base et les champs du formulaire
    column_mapping = {
        "id": "ID (auto-généré)",
        "nom_table": "Nom de la table",
        "nom_base": "Nom de la base de données",
        "producteur": "Producteur de la donnée",
        "schema": "Schéma du SGBD",
        "granularite_geo": "Granularité géographique",
        "description": "Description",
        "millesime": "Millésime/année",
        "date_maj": "Dernière mise à jour",
        "source": "Source (URL)",
        "frequence_maj": "Fréquence de mises à jour des données",
        "licence": "Licence d'utilisation des données",
        "envoi_par": "Personne remplissant le formulaire",
        "contact": "Contact (non utilisé actuellement)",
        "mots_cles": "Mots-clés (non utilisé actuellement)",
        "notes": "Notes (non utilisé actuellement)",
        "contenu_csv": "Contenu CSV",
        "dictionnaire": "Dictionnaire des variables",
        "created_at": "Date de création de l'entrée (auto-générée)"
    }
    
    # Créer un DataFrame pour afficher le mapping
    mapping_df = pd.DataFrame({
        "Colonne de la base de données": db_columns,
        "Champ du formulaire": [column_mapping.get(col, "Non mappé") for col in db_columns]
    })
    
    st.dataframe(mapping_df, use_container_width=True)
st.markdown('</div>', unsafe_allow_html=True)

# Pied de page
st.markdown("---")
st.markdown("© 2025 - Système de Gestion des Métadonnées v1.0") 