import streamlit as st
import pandas as pd
import json
from datetime import datetime
import os
from pathlib import Path
import sys
from pathlib import Path

# Ajout du répertoire parent au PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent))
from db_utils import init_db, save_metadata

# Configuration de la page
st.set_page_config(
    page_title="Saisie de métadonnées",
    page_icon="📝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialisation de la base de données
init_db()

# CSS personnalisé
st.markdown("""
<style>
    .main h1 {
        color: #1E88E5;
    }
    .stButton button {
        background-color: #1E88E5;
        color: white;
    }
    .stSelectbox label, .stTextInput label {
        font-weight: bold;
    }
    .required label::after {
        content: " *";
        color: red;
    }
</style>

<style>
    /* Code couleur pour les types de schémas */
    .schema-economie { color: #1E88E5; }
    .schema-education { color: #43A047; }
    .schema-energie { color: #FB8C00; }
    .schema-environnement { color: #8BC34A; }
    .schema-geo { color: #9C27B0; }
    .schema-logement { color: #F4511E; }
    .schema-mobilite { color: #00ACC1; }
    .schema-population { color: #7CB342; }
    .schema-securite { color: #E53935; }
    
    /* Style des info-bulles */
    .tooltip {
        position: relative;
        display: inline-block;
        cursor: help;
    }
    .tooltip .tooltiptext {
        visibility: hidden;
        width: 120px;
        background-color: #555;
        color: #fff;
        text-align: center;
        border-radius: 6px;
        padding: 5px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        margin-left: -60px;
        opacity: 0;
        transition: opacity 0.3s;
    }
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }
</style>
""", unsafe_allow_html=True)

# Titre et description
st.title("Saisie de métadonnées")
st.write("Formulaire de saisie des métadonnées pour les tables de votre base de données.")

# Création des onglets
tab1, tab2 = st.tabs(["Saisie manuelle", "Structure des données"])

with tab1:
    # Création du formulaire
    st.subheader("Informations de base")
    
    # Formulaire pour les informations de base
    col1, col2 = st.columns(2)
    
    with col1:
        with st.container():
            st.markdown('<div class="required">', unsafe_allow_html=True)
            nom_fichier = st.text_input("Nom de la base de données", help="Nom de la base de données PostgreSQL")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with st.container():
            st.markdown('<div class="required">', unsafe_allow_html=True)
            schema = st.selectbox(
                "Schéma du SGBD", 
                ["economie", "education", "energie", "environnement", 
                 "geo", "logement", "mobilite", "population", "securite"],
                help="Catégorie thématique des données"
            )
            st.markdown('</div>', unsafe_allow_html=True)
        
        with st.container():
            st.markdown('<div class="required">', unsafe_allow_html=True)
            nom_table = st.text_input("Nom de la table", help="Nom de la table dans la base de données")
            st.markdown('</div>', unsafe_allow_html=True)
        
        with st.container():
            st.markdown('<div class="required">', unsafe_allow_html=True)
            nom_base = st.text_input("Producteur de la donnée", help="Organisme producteur de la donnée")
            st.markdown('</div>', unsafe_allow_html=True)
    
    with col2:
        with st.container():
            granularite_geo = st.selectbox(
                "Granularité géographique",
                ["", "commune", "EPCI", "département", "région", "autre"],
                help="Niveau géographique le plus fin auquel est disponible la donnée"
            )
            
        with st.container():
            annee = st.number_input(
                "Millésime/année", 
                min_value=1900, 
                max_value=datetime.now().year, 
                value=datetime.now().year,
                help="Année de référence des données"
            )
        
        with st.container():
            date_maj = st.date_input(
                "Dernière mise à jour", 
                datetime.now().date(),
                help="Date de la dernière mise à jour des données"
            )
    
    st.subheader("Description")
    
    with st.container():
        st.markdown('<div class="required">', unsafe_allow_html=True)
        description = st.text_area(
            "Description détaillée", 
            height=150,
            help="Description détaillée des données, leur collecte, leur utilité, etc."
        )
        st.markdown('</div>', unsafe_allow_html=True)
    
    st.subheader("Informations supplémentaires")
    
    col1, col2 = st.columns(2)
    
    with col1:
        source = st.text_input("Source", help="Source des données (URL, nom du service, etc.)")
        frequence_maj = st.selectbox(
            "Fréquence de mise à jour",
            ["", "Ponctuelle", "Quotidienne", "Hebdomadaire", "Mensuelle", "Trimestrielle", "Semestrielle", "Annuelle"],
            help="Fréquence à laquelle les données sont mises à jour"
        )
    
    with col2:
        licence = st.selectbox(
            "Licence",
            ["", "Licence Ouverte", "ODbL", "CC-BY", "CC-BY-SA", "CC-BY-NC", "CC-BY-ND", "Autre"],
            help="Licence sous laquelle les données sont publiées"
        )
        envoi_par = st.text_input("Rempli par", help="Nom de la personne remplissant ce formulaire")
    
    st.subheader("Données CSV")
    
    with st.expander("Dépliez", expanded=False):
        # Déplacement du sélecteur de séparateur sous le bouton "Dépliez"
        separateur = st.radio("Séparateur", [";", ","], horizontal=True)
        
        st.info("""
        Copiez-collez ici les 4 premières lignes de la table. Format attendu :
        
        COD_VAR;LIB_VAR;LIB_VAR_LONG;COD_MOD;LIB_MOD;TYPE_VAR;LONG_VAR
        COM;Commune ou ARM;Code du département suivi du numéro de commune
        """)
        
        contenu_csv = st.text_area(
            "4 premières lignes du CSV :", 
            height=300,
            help="Copiez-collez ici les 4 premières lignes du fichier CSV"
        )
        
        if contenu_csv:
            try:
                # Vérification du format
                lines = contenu_csv.strip().split('\n')
                header = lines[0].split(separateur)
                
                # Affichage d'un aperçu
                st.write("Aperçu des données (5 premières lignes) :")
                preview_data = []
                for line in lines[1:6]:  # Afficher les 5 premières lignes de données
                    preview_data.append(line.split(separateur))
                st.table(preview_data)
                
                # Initialisation du dictionnaire metadata s'il n'existe pas
                if "metadata" not in locals():
                    metadata = {}
                
                # Traitement du contenu CSV
                if contenu_csv:
                    try:
                        lines = contenu_csv.strip().split('\n')
                        header = lines[0].split(separateur)
                        
                        # Transformation des lignes en liste pour garantir la cohérence
                        data_rows = []
                        for line in lines[1:]:
                            if line.strip():  # Ignorer les lignes vides
                                data_rows.append(line.split(separateur))
                        
                        metadata["contenu_csv"] = {
                            "header": header,
                            "data": data_rows,  # Stockage sous forme de liste de listes
                            "separator": separateur
                        }
                    except Exception as e:
                        st.warning(f"Erreur lors de l'analyse du CSV : {str(e)}")
            except Exception as e:
                st.error(f"Erreur lors de l'analyse du CSV : {str(e)}")
    
    st.subheader("Dictionnaire des variables")
    
    dict_tab1, dict_tab2 = st.tabs(["Copier-coller", "Téléchargement"])
    
    with dict_tab1:
        st.info("""
        Copiez-collez ici le dictionnaire des variables :
        
        **Format attendu** : Un tableau avec une ligne d'en-tête et une ligne par variable, 
        séparé par point-virgule (;) ou virgule (,).
        
        **Exemple** :
        ```
        COD_VAR;LIB_VAR;LIB_VAR_LONG;TYPE_VAR;TAILLE
        CODGEO;Code géographique;Code INSEE de la commune;VARCHAR;5
        LIBGEO;Libellé géographique;Nom de la commune;VARCHAR;50
        ```
        """)
        
        dict_separateur = st.radio("Séparateur pour le dictionnaire", [";", ","], horizontal=True)
        
        dictionnaire = st.text_area(
            "Dictionnaire des variables", 
            height=300,
            help="Copiez-collez ici le dictionnaire des variables au format CSV"
        )
        
        if dictionnaire:
            try:
                lines = dictionnaire.strip().split('\n')
                if len(lines) > 0:
                    header_sample = lines[0].split(dict_separateur)
                    
                    # Affichage d'un aperçu
                    st.write("Aperçu du dictionnaire :")
                    
                    preview_data = []
                    for i, line in enumerate(lines[:6]):  # Afficher les 5 premières lignes + header
                        if i == 0:  # C'est l'en-tête
                            header = line.split(dict_separateur)
                        else:
                            preview_data.append(line.split(dict_separateur))
                    
                    # Création d'un DataFrame pour l'aperçu
                    if preview_data:
                        try:
                            # Uniformiser les données pour éviter les erreurs
                            uniform_data = []
                            for row in preview_data:
                                # Si la ligne a moins de colonnes que l'en-tête, ajouter des valeurs vides
                                if len(row) < len(header):
                                    row.extend([''] * (len(header) - len(row)))
                                # Si la ligne a plus de colonnes que l'en-tête, tronquer
                                elif len(row) > len(header):
                                    row = row[:len(header)]
                                uniform_data.append(row)
                            
                            df_preview = pd.DataFrame(uniform_data, columns=header)
                            st.dataframe(df_preview)
                        except Exception as e:
                            st.warning(f"Erreur lors de la création de l'aperçu : {str(e)}")
                            st.write("Données brutes de l'aperçu :")
                            for row in preview_data:
                                st.write(row)
                    
                    # Information sur le format
                    if len(header_sample) < 3:
                        st.warning(f"Le dictionnaire ne semble avoir que {len(header_sample)} colonnes. Est-ce le bon séparateur ?")
                    elif len(lines) < 2:
                        st.warning("Le dictionnaire ne contient que l'en-tête, sans données de variables.")
                    elif len(lines) > 1000:
                        st.warning(f"Le dictionnaire est très volumineux ({len(lines)} lignes). Les performances peuvent être affectées.")
                else:
                    st.error("Le dictionnaire semble vide.")
            except Exception as e:
                st.error(f"Erreur lors de l'analyse du dictionnaire : {str(e)}")
    
    with dict_tab2:
        st.write("Téléchargement du dictionnaire (à venir)")
        uploaded_file = st.file_uploader("Choisir un fichier CSV", type="csv")
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file, sep=None, engine='python')
                st.write("Aperçu des données :")
                st.dataframe(df.head())
                
                # Détection du séparateur
                sep = ',' if ',' in uploaded_file.getvalue().decode('utf-8') else ';'
                st.info(f"Séparateur détecté : '{sep}'")
                
                # Convertir en format attendu
                dict_data = []
                for _, row in df.iterrows():
                    dict_data.append(list(row.values))
                
                # Sauvegarder pour le formulaire
                if "metadata" not in locals():
                    metadata = {}
                
                metadata["dictionnaire"] = {
                    "header": list(df.columns),
                    "data": dict_data,
                    "separator": sep
                }
                
                st.success("Dictionnaire chargé avec succès")
            except Exception as e:
                st.error(f"Erreur lors du chargement du fichier : {str(e)}")
    
    # Bouton de soumission
    st.markdown("### Validation et envoi")
    submitted = st.button("Enregistrer les métadonnées", type="primary")
    
    # Traitement de la soumission
    if submitted:
        if not nom_fichier:
            st.error("Veuillez d'abord saisir un nom de fichier")
        else:
            try:
                # Préparation du dictionnaire de métadonnées
                metadata = {"contenu_csv": {}, "dictionnaire": {}}
                
                # Traitement du contenu CSV
                if contenu_csv:
                    try:
                        lines = contenu_csv.strip().split('\n')
                        header = lines[0].split(separateur)
                        
                        # Transformation des lignes en liste pour garantir la cohérence
                        data_rows = []
                        for line in lines[1:]:
                            if line.strip():  # Ignorer les lignes vides
                                data_rows.append(line.split(separateur))
                        
                        metadata["contenu_csv"] = {
                            "header": header,
                            "data": data_rows,  # Stockage sous forme de liste de listes
                            "separator": separateur
                        }
                    except Exception as e:
                        st.warning(f"Erreur lors de l'analyse du CSV : {str(e)}")
                
                # Traitement du dictionnaire des variables
                if dictionnaire:
                    try:
                        lines = dictionnaire.strip().split('\n')
                        
                        # S'assurer qu'il y a au moins une ligne d'en-tête
                        if not lines:
                            st.warning("Le dictionnaire est vide, il sera ignoré.")
                        else:
                            # Utiliser le séparateur choisi pour le dictionnaire
                            header = lines[0].split(dict_separateur)
                            
                            # Transformation des lignes en liste pour garantir la cohérence
                            data_rows = []
                            for line in lines[1:]:
                                if line.strip():  # Ignorer les lignes vides
                                    data_rows.append(line.split(dict_separateur))
                            
                            # Vérifier si nous avons des données
                            if not data_rows:
                                st.warning("Le dictionnaire ne contient pas de données, uniquement l'en-tête.")
                            
                            # Afficher un avertissement si le dictionnaire est très volumineux
                            if len(data_rows) > 1000:
                                st.warning(f"Le dictionnaire est très volumineux ({len(data_rows)} lignes). " +
                                          "Les performances peuvent être affectées. " +
                                          "Seules les 2000 premières lignes seront stockées.")
                            
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
                            
                            metadata["dictionnaire"] = {
                                "header": header,
                                "data": uniform_data[:2000],  # Limiter à 2000 lignes maximum
                                "separator": dict_separateur
                            }
                    except Exception as e:
                        st.warning(f"Erreur lors de l'analyse du dictionnaire : {str(e)}")
                        st.warning("Le dictionnaire sera ignoré.")
                        metadata["dictionnaire"] = {}
                
                # Création du dictionnaire de métadonnées
                metadata.update({
                    "nom_fichier": nom_fichier,
                    "informations_base": {
                        "nom_table": nom_table,
                        "nom_base": nom_base,
                        "schema": schema,
                        "description": description,
                        "date_creation": str(annee),
                        "date_maj": date_maj.strftime("%Y-%m-%d") if date_maj else None,
                        "source": source,
                        "frequence_maj": frequence_maj,
                        "licence": licence,
                        "envoi_par": envoi_par,
                        "separateur_csv": separateur,
                        "granularite_geo": granularite_geo
                    }
                })

                # Sauvegarde dans la base de données
                succes, message = save_metadata(metadata)
                if succes:
                    st.success(message)
                    # Création d'un encadré de succès bien visible
                    st.balloons()
                    st.success("""
                    ### ✅ Métadonnées sauvegardées avec succès!
                    
                    Vos métadonnées sont maintenant disponibles dans le catalogue.
                    Vous pouvez les consulter dans l'onglet "Catalogue".
                    """)
                else:
                    st.error(f"Erreur lors de la sauvegarde : {message}")
                    st.error("Veuillez vérifier les logs pour plus de détails.")

                # Sauvegarde locale en JSON
                try:
                    json_path = os.path.join("metadata", f"{nom_fichier}.json")
                    os.makedirs("metadata", exist_ok=True)
                    with open(json_path, "w", encoding="utf-8") as f:
                        json.dump(metadata, f, ensure_ascii=False, indent=4)
                    st.success(f"Métadonnées sauvegardées localement dans {json_path}")
                except Exception as e:
                    st.error(f"Erreur lors de la sauvegarde locale en JSON : {str(e)}")

                # Sauvegarde locale en TXT
                try:
                    txt_path = os.path.join("metadata", f"{nom_fichier}.txt")
                    with open(txt_path, "w", encoding="utf-8") as f:
                        f.write(f"Nom de la base de données : {nom_fichier}\n")
                        f.write(f"Schéma du SGBD : {schema}\n")
                        f.write(f"Nom de la table : {nom_table}\n")
                        f.write(f"Producteur de la donnée : {nom_base}\n")
                        f.write(f"Granularité géographique : {granularite_geo}\n")
                        f.write(f"Description : {description}\n")
                        f.write(f"Millésime/année : {annee}\n")
                        if date_maj:
                            f.write(f"Dernière mise à jour : {date_maj.strftime('%Y-%m-%d')}\n")
                        f.write(f"Source : {source}\n")
                        f.write(f"Fréquence de mises à jour des données : {frequence_maj}\n")
                        f.write(f"Licence d'utilisation des données : {licence}\n")
                        f.write(f"Personne remplissant le formulaire : {envoi_par}\n")
                        f.write(f"Séparateur CSV : {separateur}\n")
                        if contenu_csv:
                            f.write("\nContenu CSV :\n")
                            f.write(contenu_csv)
                        if dictionnaire:
                            f.write("\nDictionnaire des variables :\n")
                            f.write(dictionnaire)
                    st.success(f"Métadonnées sauvegardées localement dans {txt_path}")
                except Exception as e:
                    st.error(f"Erreur lors de la sauvegarde locale en TXT : {str(e)}")
                    
            except Exception as e:
                st.error(f"Erreur inattendue : {str(e)}")
                st.error("Veuillez vérifier les logs pour plus de détails.")

with tab2:
    st.subheader("Structure des données")
    uploaded_file = st.file_uploader("Choisir un fichier CSV", type="csv")
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.write("Aperçu des données :")
        st.dataframe(df.head())
        st.write("Structure des colonnes :")
        st.dataframe(pd.DataFrame({
            'Type': df.dtypes,
            'Non-nuls': df.count(),
            'Nulls': df.isna().sum()
        }))

# Section d'aide
with st.expander("Aide pour la saisie"):
    st.markdown("""
    ### Champs obligatoires
    Les champs marqués d'un astérisque (*) sont obligatoires.
    
    - **Schéma du SGBD** : Schéma de la table dans le SGBD Intelligence des Territoires
    - **Nom de la table** : Nom de la table dans le SGBD Intelligence des Territoires
    - **Table de la base de données** : Nom de la table dans le SGBD Intelligence des Territoires
    - **Producteur de la donnée** : Nom de l'organisme pourvoyeur de la donnée
    - **Millésime/année** : Année de référence des données
    - **Dernière mise à jour** : Date de la dernière mise à jour des données
    - **Description** : Description détaillée du contenu des données
    
    ### Conseils de saisie
    1. **Informations de base**
       - Le nom de la table est actuellement limité à certaines valeurs prédéfinies
       - Le schéma doit correspondre à l'une des catégories prédéfinies
       - Le producteur doit être l'organisme source des données
       - Le millésime doit correspondre à l'année de référence des données
    
    2. **Description**
       - Soyez aussi précis que possible dans la description
    
    3. **Informations supplémentaires**
       - Indiquez la personne qui remplit le formulaire
       - Précisez la source originale des données (URL ou référence)
       - Sélectionnez la fréquence de mise à jour appropriée
       - Choisissez la licence qui correspond aux conditions d'utilisation
    
    4. **Données CSV**
       - Copiez-collez les premières lignes du fichier CSV
       - Indiquez le séparateur utilisé (par défaut, point-virgule)
       - Ajoutez le dictionnaire des variables si le fichier CSV est disponible
    """)

# Pied de page
st.markdown("---")
st.markdown("© 2025 - Système de Gestion des Métadonnées") 