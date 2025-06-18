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
        query = '''
        SELECT DISTINCT ON (nom_jeu_donnees)
            nom_jeu_donnees,
            producteur,
            date_publication,
            millesime,
            date_prochaine_publication,
            frequence_maj
        FROM metadata
        ORDER BY nom_jeu_donnees, date_publication DESC, millesime DESC, id DESC
        '''
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
    date_publication = row['date_publication']
    today = date.today()
    
    # Si la date de publication est postérieure à la date de prochaine publication
    # alors le jeu de données est considéré comme à jour
    if not pd.isnull(date_publication) and date_publication >= dpp:
        return "À jour"
    
    # Sinon, on applique la logique habituelle
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
        for col in ["date_publication", "date_prochaine_publication"]:
            df[col] = pd.to_datetime(df[col]).dt.date
        # Calcul du statut
        df['statut'] = df.apply(compute_status, axis=1)
        # Badge HTML
        df['Statut'] = df['statut'].apply(status_badge)
        # Colonne Fiche (texte cliquable)
        df['Fiche'] = 'Voir fiche'

        # Réorganisation des colonnes pour le tableau principal
        display_cols = [
            'nom_jeu_donnees', 'producteur', 'date_publication', 'millesime', 'date_prochaine_publication', 'frequence_maj', 'Statut', 'Fiche'
        ]
        df_display = df[display_cols].rename(columns={
            'nom_jeu_donnees': 'Jeu de données',
            'producteur': 'Producteur',
            'date_publication': 'Date dernière publication',
            'millesime': 'Année du dernier millésime',
            'date_prochaine_publication': 'Prochaine publication',
            'frequence_maj': 'Fréquence',
        })

        # Affichage du tableau fusionné avec st.data_editor
        st.subheader("Tableau de suivi")
        st.write("<style>th, td {text-align: left !important;}</style>", unsafe_allow_html=True)
        selected = st.data_editor(
            df_display,
            column_config={
                "Statut": st.column_config.TextColumn("Statut", help="Statut du jeu de données", width="small"),
                "Fiche": st.column_config.TextColumn("Fiche", help="Voir la fiche détaillée", width="small")
            },
            hide_index=True,
            use_container_width=True,
            disabled=[col for col in df_display.columns if col != 'Fiche'],
            key="data_editor_suivi"
        )

        # Affichage des détails du jeu de données sélectionné
        if selected is not None and len(selected) > 0:
            selected_row = selected.iloc[0] if hasattr(selected, 'iloc') else selected[0]
            st.markdown("---")
            st.markdown(f"### Détail du jeu de données : {selected_row['Jeu de données']}")
            st.write(f"**Producteur :** {selected_row['Producteur']}")
            st.write(f"**Date de dernière publication :** {selected_row['Date dernière publication']}")
            st.write(f"**Année du dernier millésime :** {selected_row['Année du dernier millésime']}")
            st.write(f"**Prochaine publication :** {selected_row['Prochaine publication']}")
            st.write(f"**Fréquence :** {selected_row['Fréquence']}")

        # Bouton Exporter plus petit
        st.markdown("<style>.stButton button {padding: 0.2rem 0.7rem; font-size: 0.9rem;}</style>", unsafe_allow_html=True)
        export_format = st.radio("Exporter le tableau :", ["CSV", "Excel"], horizontal=True, key="export_radio")
        export_btn = st.button("Exporter", key="export_btn")

        # Export
        if export_btn:
            to_export = df_display.copy()
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

        # Graphique de suivi avec trait vertical rouge pour la date actuelle
        st.subheader("Vue d'ensemble des mises à jour")
        if not df.empty:
            fig = px.timeline(
                df,
                x_start="date_publication",
                x_end="date_prochaine_publication",
                y="nom_jeu_donnees",
                color="statut",
                title="Planning des mises à jour"
            )
            # Ajout du trait vertical rouge pour la date actuelle
            fig.add_vline(x=datetime.now(), line_width=2, line_dash="dash", line_color="red")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Aucune donnée à afficher pour les filtres sélectionnés.")

except Exception as e:
    st.error(f"Une erreur est survenue : {str(e)}")
    st.info("Veuillez vérifier la connexion à la base de données et réessayer.") 