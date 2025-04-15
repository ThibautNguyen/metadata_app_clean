import streamlit as st
import pandas as pd
import sys
from pathlib import Path
import json

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
</style>
""", unsafe_allow_html=True)

# Titre et description
st.title("Catalogue des métadonnées")
st.write("Recherchez et explorez les métadonnées disponibles pour vos analyses et projets.")

# Initialisation automatique de la base de données
try:
    init_db()
except Exception as e:
    st.error(f"Erreur lors de l'initialisation : {str(e)}")

# Interface de recherche
st.markdown("## Recherche")
col1, col2 = st.columns([3, 1])

with col1:
    search_text = st.text_input("Rechercher", placeholder="Entrez un terme à rechercher...")
    if search_text:
        st.caption("La recherche s'effectue dans le nom de la base, le producteur, la description et le schéma")

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

# Afficher le nombre total de métadonnées
st.info(f"Nombre total de métadonnées disponibles : {len(metadata_results)}")

# Affichage des résultats
st.markdown("## Résultats")

if metadata_results:
    # Création d'un conteneur avec style
    st.markdown('<div class="results-container" style="background-color: white; padding: 20px; border-radius: 10px; box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);">', unsafe_allow_html=True)
    
    # Affichage du nombre de résultats
    st.info(f"{len(metadata_results)} métadonnées trouvées")
    
    # Conversion des résultats en DataFrame avec gestion des clés manquantes
    results_df = pd.DataFrame([
        {
            "Nom de la table": meta.get("nom_table", "") or meta.get("nom_base", "") or meta.get("nom_fichier", "Non spécifié"),
            "Producteur de la donnée": meta.get("producteur", "Non spécifié"),
            "Schéma du SGBD": meta.get("schema", "Non spécifié"),
            "Granularité géographique": meta.get("granularite_geo", "Non spécifiée"),
            "Millésime/année": meta.get("millesime", meta.get("date_creation", "")).strftime("%Y") if meta.get("millesime") or meta.get("date_creation") else "Non spécifié",
            "Dernière mise à jour": meta.get("date_maj", "").strftime("%d/%m/%Y") if meta.get("date_maj") else "Non spécifiée"
        }
        for meta in metadata_results
    ])

    # Réorganiser les colonnes selon l'ordre demandé
    columns_order = ["Nom de la table", "Producteur de la donnée", "Schéma du SGBD", "Granularité géographique"]
    all_columns = list(results_df.columns)
    remaining_columns = [col for col in all_columns if col not in columns_order]
    ordered_columns = columns_order + remaining_columns
    
    # Afficher le tableau avec les colonnes réorganisées et style amélioré
    st.dataframe(results_df[ordered_columns], use_container_width=True)

    # Option pour afficher les détails
    with st.expander("Afficher les détails complets des métadonnées", expanded=False):
        # Affichage détaillé des métadonnées
        for i, meta in enumerate(metadata_results):
            with st.expander(f"📄 {meta.get('nom_table', '') or meta.get('nom_base', '') or 'Métadonnée ' + str(i+1)}", expanded=False):
                # Utilisation de colonnes pour l'affichage
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("##### Informations de base")
                    st.write(f"- **Nom de la table :** {meta.get('nom_table', 'Non spécifié') or meta.get('nom_base', 'Non spécifié')}")
                    st.write(f"- **Producteur de la donnée :** {meta.get('producteur', 'Non spécifié')}")
                    st.write(f"- **Schéma du SGBD :** {meta.get('schema', 'Non spécifié')}")
                    st.write(f"- **Granularité géographique :** {meta.get('granularite_geo', 'Non spécifiée')}")
                    st.write(f"- **Nom de la base de données :** {meta.get('nom_base', 'Non spécifié')}")
                    millesime = meta.get("millesime") or meta.get("date_creation")
                    st.write(f"- **Millésime/année :** {millesime.strftime('%Y') if millesime else 'Non spécifié'}")
                    st.write(f"- **Dernière mise à jour :** {meta.get('date_maj', '').strftime('%d/%m/%Y') if meta.get('date_maj') else 'Non spécifiée'}")
                
                with col2:
                    st.markdown("##### Informations supplémentaires")
                    st.write(f"- **Source (URL) :** {meta.get('source', 'Non spécifiée')}")
                    st.write(f"- **Fréquence de mise à jour :** {meta.get('frequence_maj', 'Non spécifiée')}")
                    st.write(f"- **Licence d'utilisation :** {meta.get('licence', 'Non spécifiée')}")
                    st.write(f"- **Personne remplissant le formulaire :** {meta.get('envoi_par', 'Non spécifiée')}")
                
                # Description sur toute la largeur
                st.markdown("##### Description")
                description_text = meta.get('description', 'Pas de description disponible')
                if description_text and len(description_text) > 10:  # Vérification que la description existe et n'est pas vide
                    st.markdown(f"<div style='background-color: #f8f9fa; padding: 10px; border-radius: 5px; border-left: 3px solid #1E88E5;'>{description_text}</div>", unsafe_allow_html=True)
                else:
                    st.markdown("<div style='background-color: #f8f9fa; padding: 10px; border-radius: 5px; color: #777;'>Pas de description disponible</div>", unsafe_allow_html=True)
                
                # Onglets pour le contenu CSV et le dictionnaire
                if meta.get('contenu_csv') or meta.get('dictionnaire'):
                    data_tab, dict_tab = st.tabs(["Contenu CSV", "Dictionnaire des variables"])
                    
                    with data_tab:
                        if meta.get('contenu_csv'):
                            st.markdown("##### Aperçu des données")
                            # Affichage du contenu CSV (code existant)
                            try:
                                contenu_csv = meta['contenu_csv']
                                # Si c'est une chaîne, essayer de la décoder en JSON
                                if isinstance(contenu_csv, str):
                                    try:
                                        contenu_csv = json.loads(contenu_csv)
                                    except json.JSONDecodeError as e:
                                        st.warning(f"Erreur lors du décodage JSON du contenu CSV : {str(e)}")
                                        st.info("Contenu brut : " + str(meta['contenu_csv'])[:200] + "...")
                                        continue  # Passer à l'élément suivant
                                
                                # Vérifier si le contenu CSV a un format valide
                                if isinstance(contenu_csv, dict):
                                    # Assouplir la vérification du format - accepter différentes structures
                                    header = contenu_csv.get('header', [])
                                    data = contenu_csv.get('data', [])
                                    separator = contenu_csv.get('separator', ';')
                                    
                                    has_valid_data = len(data) > 0
                                    has_valid_header = len(header) > 0
                                    
                                    if has_valid_data and has_valid_header:
                                        st.caption(f"Séparateur utilisé: '{separator}'")
                                        
                                        # Traitement des données
                                        data_rows = []
                                        
                                        # Traiter chaque ligne de données
                                        for row in data:
                                            # Si la ligne est une chaîne, la diviser selon le séparateur
                                            if isinstance(row, str):
                                                data_rows.append(row.split(separator))
                                            # Si c'est déjà une liste, l'utiliser telle quelle
                                            elif isinstance(row, list):
                                                data_rows.append(row)
                                    
                                    # Vérifier si les données sont uniformes
                                    if data_rows:
                                        # Déterminer le nombre maximum de colonnes dans les données
                                        max_cols = max(len(row) for row in data_rows)
                                        
                                        # Si le header a moins de colonnes que les données, ajuster
                                        if len(header) < max_cols:
                                            # Ajouter des colonnes manquantes
                                            header.extend([f"Col{i+1}" for i in range(len(header), max_cols)])
                                            st.info(f"L'en-tête a été complété avec des noms de colonnes génériques")
                                        
                                        # Créer le DataFrame avec les données traitées
                                        try:
                                            # Uniformiser les données pour éviter les erreurs
                                            uniform_data = []
                                            for row in data_rows:
                                                # Si la ligne a moins de colonnes que l'en-tête, ajouter des valeurs vides
                                                if len(row) < len(header):
                                                    row.extend([''] * (len(header) - len(row)))
                                                # Si la ligne a plus de colonnes que l'en-tête, tronquer
                                                elif len(row) > len(header):
                                                    row = row[:len(header)]
                                                uniform_data.append(row)
                                            
                                            df_csv = pd.DataFrame(uniform_data, columns=header)
                                            st.dataframe(df_csv, use_container_width=True)
                                        except Exception as e:
                                            st.warning(f"Erreur lors de la création du DataFrame : {str(e)}")
                                            st.write("Données brutes (5 premières lignes) :")
                                            for i, row in enumerate(data_rows[:5]):
                                                st.write(f"Ligne {i+1}: {row}")
                                    else:
                                        st.warning("Aucune donnée à afficher")
                                else:
                                    st.warning(f"Format de données CSV non reconnu (type: {type(contenu_csv)})")
                                # Tenter d'afficher le contenu de manière intelligente
                                if isinstance(contenu_csv, list):
                                    st.write("Liste détectée, affichage des 5 premiers éléments:")
                                    st.code("\n".join([str(item) for item in contenu_csv[:5]]))
                                else:
                                    st.write("Contenu brut (extrait):")
                                    st.code(str(contenu_csv)[:500] + "..." if len(str(contenu_csv)) > 500 else str(contenu_csv))
                            except Exception as e:
                                st.error(f"Erreur lors de l'affichage du contenu CSV : {str(e)}")
                                st.info("Contenu brut (extrait) : " + str(meta.get('contenu_csv', ''))[:200] + "..." if len(str(meta.get('contenu_csv', ''))) > 200 else str(meta.get('contenu_csv', '')))
                        else:
                            st.info("Aucun aperçu CSV disponible pour cette métadonnée.")
                    
                    with dict_tab:
                        if meta.get('dictionnaire'):
                            st.markdown("##### Dictionnaire des variables")
                            # Affichage du dictionnaire (code existant)
                            try:
                                dictionnaire = meta['dictionnaire']
                                # Si c'est une chaîne, essayer de la décoder en JSON
                                if isinstance(dictionnaire, str):
                                    try:
                                        dictionnaire = json.loads(dictionnaire)
                                    except json.JSONDecodeError as e:
                                        st.warning(f"Erreur lors du décodage JSON du dictionnaire : {str(e)}")
                                        st.info("Contenu brut : " + str(meta['dictionnaire'])[:200] + "...")
                                        continue  # Passer à l'élément suivant
                                
                                # Vérifier si le dictionnaire a un format valide
                                if isinstance(dictionnaire, dict):
                                    # Assouplir la vérification du format - accepter différentes structures
                                    header = dictionnaire.get('header', [])
                                    data = dictionnaire.get('data', [])
                                    separator = dictionnaire.get('separator', ';')
                                    
                                    has_valid_data = len(data) > 0
                                    has_valid_header = len(header) > 0
                                    
                                    if has_valid_data and has_valid_header:
                                        st.caption(f"Séparateur utilisé: '{separator}'")
                                        
                                        # Traitement des données
                                        data_rows = []
                                        
                                        # Traiter chaque ligne de données
                                        for row in data:
                                            # Si la ligne est une chaîne, la diviser selon le séparateur
                                            if isinstance(row, str):
                                                data_rows.append(row.split(separator))
                                            # Si c'est déjà une liste, l'utiliser telle quelle
                                            elif isinstance(row, list):
                                                data_rows.append(row)
                                    
                                    # Afficher une information sur la taille du dictionnaire
                                    total_rows = len(data_rows)
                                    st.info(f"Dictionnaire contenant {total_rows} variables")
                                    
                                    # Vérifier si les données sont uniformes
                                    if data_rows:
                                        # Déterminer le nombre maximum de colonnes dans les données
                                        max_cols = max(len(row) for row in data_rows)
                                        
                                        # Si le header a moins de colonnes que les données, ajuster
                                        if len(header) < max_cols:
                                            # Ajouter des colonnes manquantes
                                            header.extend([f"Col{i+1}" for i in range(len(header), max_cols)])
                                            st.info(f"L'en-tête a été complété avec des noms de colonnes génériques")
                                        
                                        # Uniformiser les données pour éviter les erreurs
                                        uniform_data = []
                                        for row in data_rows:
                                            # Si la ligne a moins de colonnes que l'en-tête, ajouter des valeurs vides
                                            if len(row) < len(header):
                                                row.extend([''] * (len(header) - len(row)))
                                            # Si la ligne a plus de colonnes que l'en-tête, tronquer
                                            elif len(row) > len(header):
                                                row = row[:len(header)]
                                            uniform_data.append(row)
                                        
                                        # Pagination pour les grands dictionnaires
                                        if total_rows > 100:
                                            # Afficher un avertissement 
                                            st.warning(f"Le dictionnaire est volumineux. Affichage des 100 premières lignes sur {total_rows}.")
                                            # Créer le DataFrame avec les 100 premières lignes
                                            df_dict = pd.DataFrame(uniform_data[:100], columns=header)
                                        else:
                                            # Créer le DataFrame avec toutes les données
                                            df_dict = pd.DataFrame(uniform_data, columns=header)
                                        
                                        try:
                                            st.dataframe(df_dict, use_container_width=True)
                                        except Exception as e:
                                            st.warning(f"Erreur lors de la création du DataFrame : {str(e)}")
                                            st.write("Données brutes (5 premières lignes) :")
                                            for i, row in enumerate(uniform_data[:5]):
                                                st.write(f"Ligne {i+1}: {row}")
                                        
                                        # Proposer de télécharger le dictionnaire complet si volumineux
                                        if total_rows > 100:
                                            try:
                                                # Créer un DataFrame complet pour le téléchargement
                                                df_full = pd.DataFrame(uniform_data, columns=header)
                                                # Convertir en CSV pour le téléchargement
                                                csv = df_full.to_csv(index=False)
                                                st.download_button(
                                                    label="Télécharger le dictionnaire complet",
                                                    data=csv,
                                                    file_name="dictionnaire_variables.csv",
                                                    mime="text/csv"
                                                )
                                            except Exception as e:
                                                st.warning(f"Erreur lors de la création du fichier de téléchargement : {str(e)}")
                                    else:
                                        # Format incomplet mais essayer d'afficher ce qu'on a
                                        if not has_valid_header and has_valid_data:
                                            st.warning("En-tête manquant dans le dictionnaire, utilisation d'en-têtes génériques")
                                            # Créer un en-tête générique basé sur la première ligne de données
                                            sample_row = data[0]
                                            if isinstance(sample_row, str):
                                                col_count = len(sample_row.split(separator))
                                            elif isinstance(sample_row, list):
                                                col_count = len(sample_row)
                                            else:
                                                col_count = 1
                                            
                                            header = [f"Colonne {i+1}" for i in range(col_count)]
                                            
                                            # Traiter les données comme avant
                                            data_rows = []
                                            for row in data:
                                                if isinstance(row, str):
                                                    data_rows.append(row.split(separator))
                                                elif isinstance(row, list):
                                                    data_rows.append(row)
                                            
                                            try:
                                                # Uniformiser les données
                                                uniform_data = []
                                                for row in data_rows:
                                                    if len(row) < len(header):
                                                        row.extend([''] * (len(header) - len(row)))
                                                    elif len(row) > len(header):
                                                        row = row[:len(header)]
                                                    uniform_data.append(row)
                                                
                                                # Limiter l'affichage si le dictionnaire est volumineux
                                                if len(uniform_data) > 100:
                                                    st.warning(f"Affichage limité aux 100 premières lignes sur {len(uniform_data)}")
                                                    uniform_data = uniform_data[:100]
                                                
                                                df_dict = pd.DataFrame(uniform_data, columns=header)
                                                st.dataframe(df_dict, use_container_width=True)
                                            except Exception as e:
                                                st.error(f"Impossible de créer un tableau pour le dictionnaire : {str(e)}")
                                                st.write("Données brutes (extrait) :")
                                                st.code(str(data[:5]))
                                        elif has_valid_header and not has_valid_data:
                                            st.warning("Aucune donnée trouvée dans le dictionnaire, affichage de l'en-tête uniquement")
                                            st.write("En-tête du dictionnaire :")
                                            st.code(header)
                                        else:
                                            st.warning("Format de données du dictionnaire non reconnu")
                                            st.write("Structure détectée :")
                                            st.json(dictionnaire)
                                else:
                                    st.warning(f"Format de données du dictionnaire non reconnu (type: {type(dictionnaire)})")
                                    # Tenter d'afficher le contenu de manière intelligente
                                    if isinstance(dictionnaire, list):
                                        st.write("Liste détectée, affichage des 5 premiers éléments:")
                                        st.code("\n".join([str(item) for item in dictionnaire[:5]]))
                                    else:
                                        st.write("Contenu brut (extrait):")
                                        st.code(str(dictionnaire)[:500] + "..." if len(str(dictionnaire)) > 500 else str(dictionnaire))
                            except Exception as e:
                                st.error(f"Erreur lors de l'affichage du dictionnaire : {str(e)}")
                                # Afficher les 200 premiers caractères du contenu brut
                                st.info("Contenu brut (extrait) : " + str(meta.get('dictionnaire', ''))[:200] + "..." if len(str(meta.get('dictionnaire', ''))) > 200 else str(meta.get('dictionnaire', '')))
                        else:
                            st.info("Aucun dictionnaire de variables disponible pour cette métadonnée.")
    
    # Fermeture du conteneur
    st.markdown('</div>', unsafe_allow_html=True)
else:
    st.warning("Aucune métadonnée trouvée. Utilisez le formulaire de saisie pour en ajouter.")

# Section d'aide et informations
with st.expander("Aide et informations"):
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
with st.expander("Mapping des colonnes de la base de données"):
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

# Pied de page
st.markdown("---")
st.markdown("© 2025 - Système de Gestion des Métadonnées v1.0") 