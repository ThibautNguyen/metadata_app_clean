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

# Configuration de la page
st.set_page_config(
    page_title="Catalogue de données",
    page_icon="📊",
    layout="wide"
)

# Chargement de la configuration
with open('config.yaml') as file:
    config = yaml.load(file, Loader=SafeLoader)

# Configuration de l'authentification
authenticator = stauth.Authenticate(
    config['credentials'],
    'metadata_cookie',
    'metadata_key',
    cookie_expiry_days=30
)

# Interface de connexion
name, authentication_status, username = authenticator.login('main', 'Connexion')
if authentication_status is False:
    st.error("Nom d'utilisateur/mot de passe incorrect")
    st.stop()
elif authentication_status is None:
    st.warning("Veuillez entrer votre nom d'utilisateur et votre mot de passe")
    st.stop()
elif authentication_status:
    st.sidebar.success(f"Bienvenue *{name}*")
    if st.sidebar.button('Déconnexion'):
        authenticator.logout('sidebar')
        st.rerun()

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
st.write("La recherche s'effectue dans les champs suivants : nom de la table, description, producteur de la donnée et dictionnaire des variables.")

col1, col2 = st.columns([3, 1])

with col1:
    search_text = st.text_input("Rechercher", placeholder="Entrez un terme à rechercher...")

with col2:
    selected_schema = st.selectbox("Filtrer par schéma", 
                                ["Tous", "economie", "education", "energie", "environnement", 
                                 "geo", "logement", "mobilite", "population", "securite"])

# Récupération des métadonnées depuis la base de données
if search_text:
    # Utiliser la fonction de recherche avec le filtre de schéma si nécessaire
    schema_filter = selected_schema if selected_schema != "Tous" else None
    metadata_results = get_metadata(search_text, schema_filter)
elif selected_schema and selected_schema != "Tous":
    # Filtrer par schéma uniquement
    metadata_results = get_metadata(None, selected_schema)
else:
    # Récupérer toutes les métadonnées
    metadata_results = get_metadata()

# Affichage du nombre total de résultats
st.info(f"Nombre total de métadonnées disponibles : {len(metadata_results)}")

# Affichage des résultats
if not metadata_results:
    st.info("Aucun résultat trouvé.")
else:
    # Création du DataFrame avec les colonnes principales
    if metadata_results:
        # Si les résultats sont des tuples, transformer en dicts
        if isinstance(metadata_results[0], dict):
            data_list = []
            for meta in metadata_results:
                data_dict = {
                    'Nom de la table': meta.get('nom_table', ''),
                    'Producteur de la donnée': meta.get('producteur', ''),
                    'Schéma du SGBD': meta.get('schema', ''),
                    'Granularité géographique': meta.get('granularite_geo', ''),
                    'Millésime/année': meta.get('millesime', '').strftime('%Y') if meta.get('millesime') else '',
                    'Dernière mise à jour': meta.get('date_maj', '').strftime('%d-%m-%Y') if meta.get('date_maj') else ''
                }
                data_list.append(data_dict)
            df = pd.DataFrame(data_list)
        else:
            # fallback: ancienne logique (index)
            data_list = []
            for meta in metadata_results:
                data_dict = {
                    'Nom de la table': meta[17] if len(meta) > 17 and meta[17] else '',
                    'Producteur de la donnée': meta[2] if len(meta) > 2 and meta[2] else '',
                    'Schéma du SGBD': meta[3] if len(meta) > 3 and meta[3] else '',
                    'Granularité géographique': meta[18] if len(meta) > 18 and meta[18] else '',
                    'Millésime/année': meta[5].strftime('%Y') if len(meta) > 5 and meta[5] else '',
                    'Dernière mise à jour': meta[6].strftime('%d-%m-%Y') if len(meta) > 6 and meta[6] else ''
                }
                data_list.append(data_dict)
            df = pd.DataFrame(data_list)
        
        # Affichage du nombre de résultats
        st.write(f"**{len(metadata_results)} résultat(s) trouvé(s)**")
        
        # Configuration de la mise en forme conditionnelle
        def highlight_search_term(val):
            if search_text and isinstance(val, str):
                if search_text.lower() in val.lower():
                    return 'background-color: yellow'
            return ''
        
        # Application de la mise en forme conditionnelle
        styled_df = df.style.map(highlight_search_term, subset=['Nom de la table', 'Producteur de la donnée'])
        
        # Affichage du DataFrame avec mise en forme
        st.dataframe(
            styled_df,
            column_config={
                "Nom de la table": st.column_config.TextColumn(
                    "Nom de la table",
                    help="Nom de la table dans la base de données",
                    width="medium"
                ),
                "Producteur de la donnée": st.column_config.TextColumn(
                    "Producteur de la donnée",
                    help="Organisme producteur des données",
                    width="medium"
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
                    st.markdown("**Informations de base**")
                    st.write(f"**Producteur :** {meta['producteur'] if meta['producteur'] else 'Non spécifié'}")
                    st.write(f"**Schéma :** {meta['schema'] if meta['schema'] else 'Non spécifié'}")
                    st.write(f"**Millésime :** {meta['millesime'].strftime('%Y') if meta['millesime'] else 'Non spécifié'}")
                    st.write(f"**Dernière mise à jour :** {meta['date_maj'].strftime('%d-%m-%Y') if meta['date_maj'] else 'Non spécifié'}")
                    st.write(f"**Fréquence de mise à jour :** {meta['frequence_maj'] if meta['frequence_maj'] else 'Non spécifié'}")
                    st.write(f"**Licence :** {meta['licence'] if meta['licence'] else 'Non spécifié'}")
                    
                with col2:
                    st.markdown("**Description**")
                    st.write(meta['description'] if meta['description'] else "Aucune description disponible")
                    
                    if meta['source']:  # URL source
                        st.markdown("**Source des données**")
                        st.write(f"[Lien vers les données]({meta['source']})")
                
                # Affichage des données et du dictionnaire des variables dans des onglets
                if meta['contenu_csv'] and meta['dictionnaire']:  # Vérification de l'existence des données et du dictionnaire
                    tab1, tab2 = st.tabs(["Aperçu des données", "Dictionnaire des variables"])
                    
                    with tab1:
                        try:
                            # Conversion des données en DataFrame
                            if isinstance(meta['contenu_csv'], str):
                                # Si c'est une chaîne, on essaie de la parser comme du CSV
                                try:
                                    # Essayer d'abord avec le séparateur spécifié dans les métadonnées
                                    if meta['separateur']:
                                        csv_data = pd.read_csv(io.StringIO(meta['contenu_csv']), sep=meta['separateur'], nrows=4)
                                    else:
                                        # Essayer avec le séparateur par défaut (;)
                                        csv_data = pd.read_csv(io.StringIO(meta['contenu_csv']), sep=';', nrows=4)
                                except:
                                    try:
                                        # Si ça échoue, essayer avec la virgule
                                        csv_data = pd.read_csv(io.StringIO(meta['contenu_csv']), sep=',', nrows=4)
                                    except:
                                        csv_data = None
                            elif isinstance(meta['contenu_csv'], dict) and 'data' in meta['contenu_csv']:
                                # Si c'est un dictionnaire avec une clé 'data'
                                headers = meta['contenu_csv'].get('header', [])
                                data = meta['contenu_csv'].get('data', [])
                                csv_data = pd.DataFrame(data, columns=headers)
                                csv_data = csv_data.head(4)  # Limiter à 4 lignes
                            else:
                                csv_data = None

                            if csv_data is not None and not csv_data.empty:
                                st.dataframe(csv_data, use_container_width=True)
                            else:
                                st.info("Aucune donnée disponible")
                        except Exception as e:
                            st.info("Erreur lors du chargement des données")
                            st.error(str(e))
                            
                    with tab2:
                        try:
                            # Conversion du dictionnaire en DataFrame
                            if isinstance(meta['dictionnaire'], str):
                                try:
                                    # Essayer d'abord avec le séparateur spécifié dans les métadonnées
                                    if meta['separateur']:
                                        dict_data = pd.read_csv(io.StringIO(meta['dictionnaire']), sep=meta['separateur'])
                                    else:
                                        # Essayer avec le point-virgule par défaut
                                        dict_data = pd.read_csv(io.StringIO(meta['dictionnaire']), sep=';')
                                except:
                                    try:
                                        # Si ça échoue, essayer avec la virgule
                                        dict_data = pd.read_csv(io.StringIO(meta['dictionnaire']), sep=',')
                                    except:
                                        dict_data = None
                            elif isinstance(meta['dictionnaire'], dict) and 'data' in meta['dictionnaire']:
                                # Si c'est un dictionnaire avec une clé 'data'
                                headers = meta['dictionnaire'].get('header', [])
                                data = meta['dictionnaire'].get('data', [])
                                dict_data = pd.DataFrame(data, columns=headers)
                            else:
                                dict_data = None

                            if dict_data is not None and not dict_data.empty:
                                # Configuration de la mise en forme conditionnelle pour le dictionnaire
                                def highlight_search_term_dict(val):
                                    if search_text and isinstance(val, str):
                                        if search_text.lower() in val.lower():
                                            return 'background-color: yellow'
                                    return ''
                                
                                # Application de la mise en forme conditionnelle au dictionnaire
                                styled_dict_data = dict_data.style.map(highlight_search_term_dict)
                                
                                # Affichage du DataFrame avec mise en forme
                                st.dataframe(
                                    styled_dict_data,
                                    use_container_width=True
                                )
                            else:
                                st.info("Aucune information sur les variables disponible")
                        except Exception as e:
                            st.error(f"Erreur lors du chargement du dictionnaire des variables : {str(e)}")
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