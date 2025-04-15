import streamlit as st
import pandas as pd
import sys
from pathlib import Path
import json
import io
import csv

# Ajout du répertoire parent au PYTHONPATH
sys.path.append(str(Path(__file__).parent))
from db_utils import test_connection, init_db, get_metadata, get_metadata_columns

# Configuration de la page
st.set_page_config(
    page_title="Catalogue des métadonnées",
    page_icon="📚",
    layout="wide"
)

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
    # Utiliser la fonction de recherche générique de get_metadata
    metadata_results = get_metadata(search_text)
elif selected_schema and selected_schema != "Tous":
    # Filtrer par schéma uniquement
    metadata_results = get_metadata({"schema": selected_schema})
else:
    # Récupérer toutes les métadonnées
    metadata_results = get_metadata()

# Affichage du nombre total de résultats
st.info(f"Nombre total de métadonnées disponibles : {len(metadata_results)}")

# Affichage des résultats
if not metadata_results:
    st.info("Aucun résultat trouvé.")
else:
    # Création d'une liste de dictionnaires pour le DataFrame
    data_list = []
    for meta in metadata_results:
        data_dict = {
            'Nom de la table': meta[17] if meta[17] else '',  # nom_table
            'Producteur': meta[2] if meta[2] else '',         # producteur
            'Schéma': meta[3] if meta[3] else '',            # schema
            'Granularité géographique': meta[18] if meta[18] else '',  # granularite_geo
            'Millésime': meta[5].strftime('%Y') if meta[5] else '',  # millesime (YYYY)
            'Dernière mise à jour': meta[6].strftime('%d-%m-%Y') if meta[6] else ''  # date_maj (DD-MM-YYYY)
        }
        data_list.append(data_dict)
    
    # Création du DataFrame
    df = pd.DataFrame(data_list)
    
    # Affichage du nombre de résultats
    st.write(f"**{len(metadata_results)} résultat(s) trouvé(s)**")
    
    # Affichage du DataFrame
    st.dataframe(df, use_container_width=True)

    # Affichage détaillé des métadonnées
    for i, meta in enumerate(metadata_results):
        with st.expander(f"📄 {meta[17] if meta[17] else 'Métadonnée ' + str(i+1)}", expanded=False):
            st.markdown('<div class="metadata-result">', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**Informations de base**")
                st.write(f"**Producteur :** {meta[2] if meta[2] else 'Non spécifié'}")
                st.write(f"**Schéma :** {meta[3] if meta[3] else 'Non spécifié'}")
                st.write(f"**Millésime :** {meta[5].strftime('%Y') if meta[5] else 'Non spécifié'}")
                st.write(f"**Dernière mise à jour :** {meta[6].strftime('%d-%m-%Y') if meta[6] else 'Non spécifié'}")
                st.write(f"**Fréquence de mise à jour :** {meta[8] if meta[8] else 'Non spécifié'}")
                st.write(f"**Licence :** {meta[9] if meta[9] else 'Non spécifié'}")
                
            with col2:
                st.markdown("**Description**")
                st.write(meta[4] if meta[4] else "Aucune description disponible")
                
                if meta[7]:  # URL source
                    st.markdown("**Source des données**")
                    st.write(f"[Lien vers les données]({meta[7]})")
            
            # Affichage des données et du dictionnaire des variables dans des onglets
            if meta[15] and meta[16]:  # Vérification de l'existence des données et du dictionnaire
                tab1, tab2 = st.tabs(["Aperçu des données", "Dictionnaire des variables"])
                
                with tab1:
                    try:
                        # Conversion des données en DataFrame
                        if isinstance(meta[15], str):
                            # Si c'est une chaîne, on essaie de la parser comme du CSV
                            try:
                                # Essayer d'abord avec le séparateur spécifié dans les métadonnées
                                if meta[10]:
                                    csv_data = pd.read_csv(io.StringIO(meta[15]), sep=meta[10], nrows=4)
                                else:
                                    # Essayer avec le séparateur par défaut (;)
                                    csv_data = pd.read_csv(io.StringIO(meta[15]), sep=';', nrows=4)
                            except:
                                try:
                                    # Si ça échoue, essayer avec la virgule
                                    csv_data = pd.read_csv(io.StringIO(meta[15]), sep=',', nrows=4)
                                except:
                                    csv_data = None
                        elif isinstance(meta[15], dict) and 'data' in meta[15]:
                            # Si c'est un dictionnaire avec une clé 'data'
                            headers = meta[15].get('header', [])
                            data = meta[15].get('data', [])
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
                        if isinstance(meta[16], str):
                            # Si c'est une chaîne, on essaie de la parser
                            try:
                                # Diviser le texte en lignes
                                lines = [line.strip() for line in meta[16].split('\n') if line.strip()]
                                data = []
                                
                                for line in lines:
                                    # Vérifier si la ligne contient des virgules
                                    if ',' in line:
                                        # Diviser la ligne en respectant les virgules
                                        parts = line.split(',', 3)  # Maximum 4 parties
                                        if len(parts) >= 4:
                                            data.append({
                                                'Variable': parts[0].strip(),
                                                'Description': parts[1].strip(),
                                                'Type': parts[2].strip(),
                                                'Valeurs possibles': parts[3].strip()
                                            })
                                
                                if data:
                                    dict_data = pd.DataFrame(data)
                                else:
                                    # Si aucune donnée n'a été extraite, essayer avec pandas
                                    dict_data = pd.read_csv(io.StringIO(meta[16]), sep=None, engine='python')
                            except Exception as e:
                                st.error(f"Erreur lors du parsing des données : {str(e)}")
                                dict_data = None

                        elif isinstance(meta[16], dict) and 'data' in meta[16]:
                            # Si c'est un dictionnaire avec une clé 'data'
                            dict_data = pd.DataFrame(meta[16]['data'])
                            if len(dict_data.columns) >= 4:
                                dict_data.columns = ['Variable', 'Description', 'Type', 'Valeurs possibles']
                        else:
                            dict_data = None

                        if dict_data is not None and not dict_data.empty:
                            st.dataframe(dict_data, use_container_width=True)
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