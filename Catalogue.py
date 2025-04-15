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
    .main h1 {
        color: #1E88E5;
    }
    .stButton button {
        background-color: #1E88E5;
        color: white;
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
    # Conversion des résultats en DataFrame avec gestion des clés manquantes
    results_df = pd.DataFrame([
        {
            "Nom de la table": meta.get("nom_table", "") or meta.get("nom_base", "") or meta.get("nom_fichier", "Non spécifié"),
            "Producteur de la donnée": meta.get("producteur", "Non spécifié"),
            "Schéma du SGBD": meta.get("schema", "Non spécifié"),
            "Millésime/année": meta.get("millesime", meta.get("date_creation", "")).strftime("%Y") if meta.get("millesime") or meta.get("date_creation") else "Non spécifié",
            "Dernière mise à jour": meta.get("date_maj", "").strftime("%d/%m/%Y") if meta.get("date_maj") else "Non spécifiée"
        }
        for meta in metadata_results
    ])

    # Réorganiser les colonnes selon l'ordre demandé
    columns_order = ["Nom de la table", "Producteur de la donnée", "Schéma du SGBD"]
    all_columns = list(results_df.columns)
    remaining_columns = [col for col in all_columns if col not in columns_order]
    ordered_columns = columns_order + remaining_columns
    
    # Afficher le tableau avec les colonnes réorganisées
    st.dataframe(results_df[ordered_columns], use_container_width=True)

    # Affichage détaillé des métadonnées
    if st.checkbox("Afficher les détails complets"):
        for meta in metadata_results:
            with st.expander(f"📄 {meta.get('nom_table', '') or meta['nom_base']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Informations de base**")
                    st.write(f"- **Nom de la table :** {meta.get('nom_table', 'Non spécifié') or meta.get('nom_base', 'Non spécifié')}")
                    st.write(f"- **Producteur de la donnée :** {meta.get('producteur', 'Non spécifié')}")
                    st.write(f"- **Schéma du SGBD :** {meta.get('schema', 'Non spécifié')}")
                    st.write(f"- **Granularité géographique :** {meta.get('granularite_geo', 'Non spécifiée')}")
                    st.write(f"- **Nom de la base de données :** {meta.get('nom_base', 'Non spécifié')}")
                    millesime = meta.get("millesime") or meta.get("date_creation")
                    st.write(f"- **Millésime/année :** {millesime.strftime('%Y') if millesime else 'Non spécifié'}")
                    st.write(f"- **Dernière mise à jour :** {meta.get('date_maj', '').strftime('%d/%m/%Y') if meta.get('date_maj') else 'Non spécifiée'}")
                with col2:
                    st.write("**Informations supplémentaires**")
                    st.write(f"- **Source (URL) :** {meta.get('source', 'Non spécifiée')}")
                    st.write(f"- **Fréquence de mise à jour :** {meta.get('frequence_maj', 'Non spécifiée')}")
                    st.write(f"- **Licence d'utilisation :** {meta.get('licence', 'Non spécifiée')}")
                    st.write(f"- **Personne remplissant le formulaire :** {meta.get('envoi_par', 'Non spécifiée')}")
                
                st.write("**Description**")
                st.write(meta.get('description', 'Pas de description disponible'))
                
                # Affichage du contenu CSV si disponible
                if meta.get('contenu_csv'):
                    st.write("**Contenu CSV**")
                    try:
                        contenu_csv = meta['contenu_csv']
                        # Si c'est une chaîne, essayer de la décoder en JSON
                        if isinstance(contenu_csv, str):
                            try:
                                contenu_csv = json.loads(contenu_csv)
                                st.success("Décodage JSON réussi")
                            except json.JSONDecodeError as e:
                                st.warning(f"Erreur lors du décodage JSON du contenu CSV : {str(e)}")
                                st.info("Contenu brut : " + str(meta['contenu_csv'])[:200] + "...")
                                continue  # Passer à l'élément suivant
                            
                        # Vérifier si le contenu CSV a un format valide
                        if isinstance(contenu_csv, dict):
                            # Assouplir la vérification du format
                            has_data = 'data' in contenu_csv and contenu_csv['data']
                            has_header = 'header' in contenu_csv and contenu_csv['header']
                            
                            if has_data and has_header:
                                # Récupérer le séparateur du CSV
                                separator = contenu_csv.get('separator', ';')
                                st.caption(f"Séparateur utilisé: '{separator}'")
                                
                                # Traitement des données
                                header = contenu_csv['header']
                                data_rows = []
                                
                                # Traiter chaque ligne de données
                                for row in contenu_csv['data']:
                                    # Si la ligne est une chaîne, la diviser selon le séparateur
                                    if isinstance(row, str):
                                        data_rows.append(row.split(separator))
                                    # Si c'est déjà une liste, l'utiliser telle quelle
                                    elif isinstance(row, list):
                                        data_rows.append(row)
                                
                                # Vérifier si les données sont uniformes
                                if data_rows:
                                    # Si le header a moins de colonnes que les données, ajuster
                                    max_cols = max(len(row) for row in data_rows)
                                    if len(header) < max_cols:
                                        # Ajouter des colonnes manquantes
                                        header.extend([f"Col{i+1}" for i in range(len(header), max_cols)])
                                        st.warning(f"L'en-tête a été étendu avec des noms de colonnes génériques (Col1, Col2, etc.)")
                                    
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
                                        st.dataframe(df_csv)
                                    except Exception as e:
                                        st.warning(f"Erreur lors de la création du DataFrame : {str(e)}")
                                        st.write("Données brutes :")
                                        st.write(data_rows[:5])  # Afficher les 5 premières lignes
                                else:
                                    st.warning("Aucune donnée à afficher")
                            else:
                                missing = []
                                if not has_header:
                                    missing.append("header")
                                if not has_data:
                                    missing.append("data")
                                st.warning(f"Format de données CSV incomplet (manque {', '.join(missing)})")
                                st.json(contenu_csv)  # Afficher le contenu JSON tel quel
                        else:
                            st.warning(f"Format de données CSV non reconnu (type: {type(contenu_csv)})")
                            st.write(str(contenu_csv)[:500] + "...")  # Afficher un extrait
                    except Exception as e:
                        st.warning(f"Erreur lors de l'affichage du contenu CSV : {str(e)}")
                        st.info("Contenu brut : " + str(meta['contenu_csv'])[:200] + "...")
                
                # Affichage du dictionnaire si disponible
                if meta.get('dictionnaire'):
                    st.write("**Dictionnaire des variables**")
                    try:
                        dictionnaire = meta['dictionnaire']
                        # Si c'est une chaîne, essayer de la décoder en JSON
                        if isinstance(dictionnaire, str):
                            try:
                                dictionnaire = json.loads(dictionnaire)
                                st.success("Décodage JSON réussi")
                            except json.JSONDecodeError as e:
                                st.warning(f"Erreur lors du décodage JSON du dictionnaire : {str(e)}")
                                st.info("Contenu brut : " + str(meta['dictionnaire'])[:200] + "...")
                                continue  # Passer à l'élément suivant
                            
                        # Vérifier si le dictionnaire a un format valide
                        if isinstance(dictionnaire, dict):
                            # Assouplir la vérification du format
                            has_data = 'data' in dictionnaire and dictionnaire['data']
                            has_header = 'header' in dictionnaire and dictionnaire['header']
                            
                            if has_data and has_header:
                                # Récupérer le séparateur du dictionnaire
                                separator = dictionnaire.get('separator', ';')
                                st.caption(f"Séparateur utilisé: '{separator}'")
                                
                                # Traitement des données
                                header = dictionnaire['header']
                                data_rows = []
                                
                                # Traiter chaque ligne de données
                                for row in dictionnaire['data']:
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
                                    # Si le header a moins de colonnes que les données, ajuster
                                    max_cols = max(len(row) for row in data_rows)
                                    if len(header) < max_cols:
                                        # Ajouter des colonnes manquantes
                                        header.extend([f"Col{i+1}" for i in range(len(header), max_cols)])
                                        st.warning(f"L'en-tête a été étendu avec des noms de colonnes génériques (Col1, Col2, etc.)")
                                    
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
                                        st.dataframe(df_dict)
                                    except Exception as e:
                                        st.warning(f"Erreur lors de la création du DataFrame : {str(e)}")
                                        st.write("Données brutes (5 premières lignes) :")
                                        st.write(uniform_data[:5])
                                    
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
                                    st.warning("Aucune donnée à afficher dans le dictionnaire")
                            else:
                                missing = []
                                if not has_header:
                                    missing.append("header")
                                if not has_data:
                                    missing.append("data")
                                st.warning(f"Format de données du dictionnaire incomplet (manque {', '.join(missing)})")
                                st.json(dictionnaire)  # Afficher le contenu JSON tel quel
                        else:
                            st.warning(f"Format de données du dictionnaire non reconnu (type: {type(dictionnaire)})")
                            st.write(str(dictionnaire)[:500] + "...")  # Afficher un extrait
                    except Exception as e:
                        st.warning(f"Erreur lors de l'affichage du dictionnaire : {str(e)}")
                        # Afficher les 500 premiers caractères du contenu brut
                        st.info("Contenu brut (extrait) : " + str(meta['dictionnaire'])[:500] + "...")
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