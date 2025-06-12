import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import plotly.express as px
from utils.db_utils import get_db_connection
import io
from utils.auth import authenticate_and_logout

st.set_page_config(
    page_title="Suivi des mises à jour",
    page_icon="📊",
    layout="wide"
)

# Authentification centralisée (présente sur toutes les pages)
name, authentication_status, username, authenticator = authenticate_and_logout()

st.title("Suivi des mises à jour des données")

# Fonction pour récupérer les données de suivi
@st.cache_data(ttl=3600)  # Cache pour 1 heure
def get_update_data():
    try:
        conn = get_db_connection()
        query = """
        SELECT 
            nom_jeu_donnees,
            producteur,
            date_publication,
            date_maj,
            date_prochaine_publication,
            frequence_maj,
            nom_table
        FROM metadata
        ORDER BY date_prochaine_publication DESC
        """
        df = pd.read_sql(query, conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Erreur lors de la récupération des données : {e}")
        return pd.DataFrame()

def compute_status(row):
    freq = str(row.get('frequence_maj', '') or '').strip().lower()
    if freq == "ponctuelle" or freq == "" or pd.isnull(freq):
        return "MaJ non prévue"
    if pd.isnull(row['date_prochaine_publication']):
        return "Inconnu"
    dpp = row['date_prochaine_publication']
    today = date.today()
    if dpp < today:
        return "En retard"
    elif (dpp - today).days < 7:
        return "À mettre à jour"
    else:
        return "À jour"

def status_badge(statut):
    color = {
        "En retard": "#ff4b4b",
        "À mettre à jour": "#ffa500",
        "À jour": "#4caf50",
        "MaJ non prévue": "#2196f3",
        "Inconnu": "#bdbdbd"
    }.get(statut, "#bdbdbd")
    return f'<span style="background-color:{color};color:white;padding:2px 8px;border-radius:8px;font-size:0.9em;">{statut}</span>'

# --- MAIN LOGIC ---
try:
    df = get_update_data()
    if df.empty:
        st.info("Aucune donnée à afficher (base vide ou erreur de connexion).")
    else:
        # Conversion des dates
        for col in ["date_publication", "date_maj", "date_prochaine_publication"]:
            df[col] = pd.to_datetime(df[col]).dt.date
        # Calcul du statut
        df['statut'] = df.apply(compute_status, axis=1)
        # Badge HTML
        df['statut_badge'] = df['statut'].apply(status_badge)
        # Lien vers la fiche (supposé que Catalogue.py accepte ?table=nom_table)
        df['Fiche'] = df['nom_table'].apply(lambda t: f'<a href="/Catalogue?table={t}" target="_blank">Voir fiche</a>' if pd.notnull(t) else "")

        # Statistiques
        total = len(df)
        n_retard = (df['statut'] == "En retard").sum()
        n_maj = (df['statut'] == "À mettre à jour").sum()
        n_ok = (df['statut'] == "À jour").sum()
        n_nonprevue = (df['statut'] == "MaJ non prévue").sum()
        st.markdown(f"**{total} jeux suivis** | <span style='color:#ff4b4b'>🟥 {n_retard} en retard</span> | <span style='color:#ffa500'>🟧 {n_maj} à mettre à jour</span> | <span style='color:#4caf50'>🟩 {n_ok} à jour</span> | <span style='color:#2196f3'>🔵 {n_nonprevue} MaJ non prévue</span>", unsafe_allow_html=True)

        # Filtres
        col1, col2, col3 = st.columns(3)
        with col1:
            producteurs = ["Tous"] + sorted(df['producteur'].dropna().unique().tolist())
            selected_producteur = st.selectbox(
                "Filtrer par producteur",
                producteurs
            )
        with col2:
            status_options = ["Tous", "À mettre à jour", "À jour", "En retard", "MaJ non prévue"]
            selected_status = st.selectbox(
                "Filtrer par statut",
                status_options
            )
        with col3:
            st.write("")
            st.write("")
            export_format = st.radio("Exporter le tableau :", ["CSV", "Excel"], horizontal=True)
            export_btn = st.button("Exporter", use_container_width=True)

        # Application des filtres
        df_filtered = df.copy()
        if selected_producteur != "Tous":
            df_filtered = df_filtered[df_filtered['producteur'] == selected_producteur]
        if selected_status != "Tous":
            df_filtered = df_filtered[df_filtered['statut'] == selected_status]

        # Affichage du tableau
        st.subheader("Tableau de suivi")
        st.write("<style>th, td {text-align: left !important;}</style>", unsafe_allow_html=True)
        st.write(
            df_filtered[['nom_jeu_donnees', 'producteur', 'date_publication', 'date_maj', 'date_prochaine_publication', 'frequence_maj']]
            .rename(columns={
                'nom_jeu_donnees': 'Jeu de données',
                'producteur': 'Producteur',
                'date_publication': 'Date publication',
                'date_maj': 'Dernière MàJ',
                'date_prochaine_publication': 'Prochaine publication',
                'frequence_maj': 'Fréquence',
            })
        )
        # Tableau enrichi avec badge et lien
        st.markdown(
            df_filtered[['statut_badge', 'Fiche']]
            .to_html(escape=False, index=False, header=["Statut", "Fiche de métadonnées"]),
            unsafe_allow_html=True
        )

        # Graphique de suivi
        st.subheader("Vue d'ensemble des mises à jour")
        if not df_filtered.empty:
            fig = px.timeline(
                df_filtered,
                x_start="date_publication",
                x_end="date_prochaine_publication",
                y="nom_jeu_donnees",
                color="statut",
                title="Planning des mises à jour"
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune donnée à afficher pour les filtres sélectionnés.")

        # Export
        if export_btn:
            to_export = df_filtered.copy()
            to_export = to_export.drop(columns=["statut_badge", "Fiche"])
            if export_format == "CSV":
                csv = to_export.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="Télécharger le CSV",
                    data=csv,
                    file_name="suivi_maj.csv",
                    mime="text/csv"
                )
            else:
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                    to_export.to_excel(writer, index=False, sheet_name='Suivi_MaJ')
                st.download_button(
                    label="Télécharger l'Excel",
                    data=output.getvalue(),
                    file_name="suivi_maj.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

except Exception as e:
    st.error(f"Une erreur est survenue : {str(e)}")
    st.info("Veuillez vérifier la connexion à la base de données et réessayer.") 