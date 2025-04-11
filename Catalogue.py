import streamlit as st
import pandas as pd
from db_utils import test_connection, init_db, get_metadata

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

# Test de connexion et initialisation de la base de données
col1, col2, col3 = st.columns([1,1,1])
with col1:
    if st.button("🔌 Tester la connexion", use_container_width=True):
        succes, message = test_connection()
        if succes:
            st.success(message)
        else:
            st.error(message)

with col2:
    if st.button("🗃️ Initialiser la base de données", use_container_width=True):
        try:
            init_db()
            st.success("Table des métadonnées créée avec succès!")
        except Exception as e:
            st.error(f"Erreur lors de l'initialisation : {str(e)}")

# Interface de recherche
st.markdown("## Recherche")
col1, col2 = st.columns([3, 1])

with col1:
    search_text = st.text_input("Rechercher par mot-clé", placeholder="Entrez un terme à rechercher...")

with col2:
    selected_producer = st.selectbox("Filtrer par producteur", ["Tous", "INSEE", "Météo France", "Citepa (GES)"])

# Récupération des métadonnées depuis la base de données
metadata_results = get_metadata(search_text, selected_producer)

# Afficher le nombre total de métadonnées
st.info(f"Nombre total de métadonnées disponibles : {len(metadata_results)}")

# Affichage des résultats
st.markdown("## Résultats")

if metadata_results:
    # Conversion des résultats en DataFrame
    results_df = pd.DataFrame([
        {
            "Nom": meta["nom_fichier"],
            "Producteur": meta["producteur"],
            "Titre": meta["titre"],
            "Dernière mise à jour": meta["derniere_mise_a_jour"].strftime("%Y-%m-%d %H:%M:%S") if meta["derniere_mise_a_jour"] else ""
        }
        for meta in metadata_results
    ])

    # Afficher le tableau
    st.dataframe(results_df, use_container_width=True)

    # Affichage détaillé des métadonnées
    if st.checkbox("Afficher les détails complets"):
        for meta in metadata_results:
            with st.expander(f"📄 {meta['nom_fichier']} - {meta['titre']}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Informations de base**")
                    st.write(f"- **Producteur :** {meta['producteur']}")
                    st.write(f"- **Schéma :** {meta['schema']}")
                    st.write(f"- **Source :** {meta['source']}")
                    st.write(f"- **Licence :** {meta['licence']}")
                with col2:
                    st.write("**Informations supplémentaires**")
                    st.write(f"- **Contact :** {meta['contact']}")
                    st.write(f"- **Envoyé par :** {meta['envoi_par']}")
                    st.write(f"- **Fréquence de mise à jour :** {meta['frequence_maj']}")
                st.write("**Description**")
                st.write(meta['notes'] if meta['notes'] else "Pas de description disponible")
                if meta['mots_cles']:
                    st.write("**Mots-clés**")
                    st.write(meta['mots_cles'])
else:
    st.warning("Aucune métadonnée trouvée. Utilisez le formulaire de saisie pour en ajouter.")

# Section d'aide et informations
with st.expander("Aide et informations"):
    st.markdown("""
    ### Comment utiliser ce catalogue
    
    - **Recherche par mot-clé** : Saisissez un terme dans le champ de recherche pour filtrer les métadonnées.
    - **Filtre par producteur** : Utilisez le menu déroulant pour filtrer par organisation productrice de données.
    - **Consulter les détails** : Cochez la case "Afficher les détails complets" pour voir toutes les informations.
    
    ### Structure des métadonnées
    
    Les métadonnées sont structurées avec les informations suivantes :
    - **Nom** : Identifiant unique de la table de données
    - **Producteur** : Organisation qui a produit les données
    - **Description** : Explication détaillée des données
    - **Informations supplémentaires** : Contacts, dates, sources, licence, etc.
    """)

# Pied de page
st.markdown("---")
st.markdown("© 2025 - Système de Gestion des Métadonnées v1.0") 