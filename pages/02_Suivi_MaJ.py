import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, date
import plotly.express as px
import plotly.graph_objects as go
from utils.db_utils import get_db_connection
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
        SELECT 
            nom_jeu_donnees,
            producteur,
            schema,
            date_publication,
            millesime,
            date_prochaine_publication,
            frequence_maj,
            source
        FROM metadata
        WHERE nom_jeu_donnees IS NOT NULL 
        AND date_publication IS NOT NULL
        ORDER BY nom_jeu_donnees, date_publication DESC, millesime DESC, id DESC
        '''
        df = pd.read_sql(query, conn)
        conn.close()
        
        return df
    except Exception as e:
        st.error(f"Erreur lors de la récupération des données : {e}")
        return pd.DataFrame()

def compute_status_by_dataset(df):
    """
    Calcule le statut pour chaque jeu de données basé sur sa version la plus récente,
    puis applique ce statut à toutes les versions du même jeu de données.
    """
    # Créer une copie pour éviter les modifications
    df = df.copy()
    
    # Fonction pour calculer le statut d'une ligne
    def compute_single_status(row):
        freq = str(row.get('frequence_maj', '') or '').strip().lower()
        if freq == "ponctuelle" or freq == "" or pd.isnull(freq):
            return "MaJ non prévue"
        
        if pd.isnull(row['date_prochaine_publication']):
            return "Inconnu"
        
        dpp = row['date_prochaine_publication']
        date_publication = row['date_publication']
        today = pd.Timestamp.now().normalize()
        
        if not pd.isnull(date_publication) and date_publication >= dpp:
            return "À jour"
        
        if dpp < today:
            return "En retard"
        elif (dpp - today).days < 7:
            return "À mettre à jour"
        else:
            return "À jour"
    
    # Grouper par jeu de données et trouver la version la plus récente
    dataset_status = {}
    
    for dataset_name in df['nom_jeu_donnees'].unique():
        dataset_rows = df[df['nom_jeu_donnees'] == dataset_name].copy()
        # Trier par date de publication décroissante pour avoir la plus récente en premier
        dataset_rows = dataset_rows.sort_values(['date_publication', 'millesime'], ascending=[False, False])
        
        if not dataset_rows.empty:
            # Prendre la première ligne (la plus récente)
            latest_row = dataset_rows.iloc[0]
            status = compute_single_status(latest_row)
            dataset_status[dataset_name] = status
    
    # Appliquer le statut du jeu de données à toutes ses versions
    df['statut'] = df['nom_jeu_donnees'].map(dataset_status)
    
    return df

def compute_status(row):
    """Fonction de compatibilité - ne devrait plus être utilisée directement"""
    freq = str(row.get('frequence_maj', '') or '').strip().lower()
    if freq == "ponctuelle" or freq == "" or pd.isnull(freq):
        return "MaJ non prévue"
    
    if pd.isnull(row['date_prochaine_publication']):
        return "Inconnu"
    
    dpp = row['date_prochaine_publication']
    date_publication = row['date_publication']
    today = pd.Timestamp.now().normalize()
    
    if not pd.isnull(date_publication) and date_publication >= dpp:
        return "À jour"
    
    if dpp < today:
        return "En retard"
    elif (dpp - today).days < 7:
        return "À mettre à jour"
    else:
        return "À jour"

def get_status_color(status):
    return {
        "En retard": "#ff4b4b",
        "À mettre à jour": "#ffa500",
        "À jour": "#4caf50",
        "MaJ non prévue": "#2196f3",
        "Inconnu": "#bdbdbd"
    }.get(status, "#bdbdbd")

# --- MAIN LOGIC ---
try:
    df = get_update_data()
    if df.empty:
        st.info("Aucune donnée à afficher (base vide ou erreur de connexion).")
    else:
        # Conversion des dates (garder en datetime pour Plotly)
        for col in ["date_publication", "date_prochaine_publication"]:
            df[col] = pd.to_datetime(df[col])
        
        # Calcul du statut pour toutes les données
        df = compute_status_by_dataset(df)
        
        # Pour le tableau de suivi, on ne garde que la version la plus récente de chaque jeu de données
        df_table = df.groupby('nom_jeu_donnees').apply(
            lambda x: x.sort_values(['date_publication', 'millesime'], ascending=[False, False]).iloc[0]
        ).reset_index(drop=True)
        
        # Affichage du tableau de suivi
        st.subheader("Tableau de suivi")
        
        # Filtres basés sur le tableau (version la plus récente)
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Filtre par producteur
            producteurs = ["Tous"] + sorted(df_table['producteur'].dropna().unique().tolist())
            selected_producteur = st.selectbox("Filtrer par producteur :", producteurs, key="filter_producteur")
        
        with col2:
            # Filtre par schéma
            schemas = ["Tous"] + sorted(df_table['schema'].dropna().unique().tolist()) if 'schema' in df_table.columns else ["Tous"]
            selected_schema = st.selectbox("Filtrer par schéma :", schemas, key="filter_schema")
        
        with col3:
            # Filtre par statut
            statuts = ["Tous"] + sorted(df_table['statut'].dropna().unique().tolist())
            selected_statut = st.selectbox("Filtrer par statut :", statuts, key="filter_statut")
        
        # Application des filtres sur le tableau
        df_table_filtered = df_table.copy()
        
        if selected_producteur != "Tous":
            df_table_filtered = df_table_filtered[df_table_filtered['producteur'] == selected_producteur]
        
        if selected_schema != "Tous" and 'schema' in df_table_filtered.columns:
            df_table_filtered = df_table_filtered[df_table_filtered['schema'] == selected_schema]
        
        if selected_statut != "Tous":
            df_table_filtered = df_table_filtered[df_table_filtered['statut'] == selected_statut]
        
        # Application des mêmes filtres sur le dataset complet pour le graphique
        df_filtered = df.copy()
        
        if selected_producteur != "Tous":
            df_filtered = df_filtered[df_filtered['producteur'] == selected_producteur]
        
        if selected_schema != "Tous" and 'schema' in df_filtered.columns:
            df_filtered = df_filtered[df_filtered['schema'] == selected_schema]
        
        if selected_statut != "Tous":
            df_filtered = df_filtered[df_filtered['statut'] == selected_statut]
        
        # Mise à jour de df_display avec les données filtrées du tableau
        df_display = df_table_filtered.copy().reset_index(drop=True)
        # Formater les dates pour l'affichage
        df_display['date_publication'] = df_display['date_publication'].dt.strftime('%Y-%m-%d')
        df_display['date_prochaine_publication'] = df_display['date_prochaine_publication'].dt.strftime('%Y-%m-%d')
        
        df_display = df_display.rename(columns={
            'nom_jeu_donnees': 'Jeu de données',
            'producteur': 'Producteur',
            'schema': 'Schéma',
            'date_publication': 'Dernière publication',
            'millesime': 'Millésime',
            'date_prochaine_publication': 'Prochaine publication',
            'frequence_maj': 'Fréquence',
            'source': 'Source',
            'statut': 'Statut'
        })

        st.info("☑️ Cochez une ligne du tableau pour afficher les détails.")
        
        selected_index = None
        
        if len(df_display) > 0:
            # Création d'un conteneur pour le tableau
            table_container = st.container()
            
            with table_container:
                selection_state = st.dataframe(
                    df_display,
                    on_select="rerun",
                    selection_mode="single-row",
                    key="selection_suivi",
                    hide_index=True,
                    column_order=["Jeu de données", "Producteur", "Schéma", "Dernière publication", 
                                 "Millésime", "Prochaine publication", 
                                 "Fréquence", "Statut"],
                    use_container_width=True
                )

                # Gestion de la sélection
                if selection_state.selection.rows and len(selection_state.selection.rows) > 0:
                    selected_index = selection_state.selection.rows[0]
        else:
            st.warning("Aucun jeu de données ne correspond aux filtres sélectionnés.")

        # Création d'un conteneur pour les détails
        details_container = st.container()

        if selected_index is not None:
            with details_container:
                selected_row = df_display.iloc[selected_index]
                
                st.markdown("---")
                st.markdown(f"### 📋 Détail du jeu de données : **{selected_row['Jeu de données']}**")
                
                # Affichage avec un style amélioré
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("#### 📊 Informations générales")
                    st.write(f"**Producteur :** {selected_row['Producteur']}")
                    st.write(f"**Fréquence de mise à jour :** {selected_row['Fréquence']}")
                    
                    # Affichage de la source avec lien cliquable
                    if 'Source' in selected_row and selected_row['Source'] and selected_row['Source'].strip():
                        st.write(f"**Source :** [Accéder aux données]({selected_row['Source']})")
                    else:
                        st.write("**Source :** Non spécifiée")
                
                with col2:
                    st.markdown("#### 📅 Dates")
                    st.write(f"**Dernière publication :** {selected_row['Dernière publication']}")
                    st.write(f"**Prochaine publication :** {selected_row['Prochaine publication']}")
                    st.write(f"**Millésime :** {selected_row['Millésime']}")
                
                with col3:
                    st.markdown("#### 🚦 Statut")
                    status_color = get_status_color(selected_row['Statut'])
                    st.markdown(f"<div style='background-color:{status_color}20; padding:10px; border-radius:5px; border-left:4px solid {status_color};'><strong>Statut :</strong> <span style='color:{status_color};font-weight:bold;'>{selected_row['Statut']}</span></div>", unsafe_allow_html=True)
                    
                    # Calcul du délai jusqu'à la prochaine publication
                    if selected_row['Prochaine publication'] and selected_row['Prochaine publication'] != 'NaT':
                        try:
                            prochaine_date = pd.to_datetime(selected_row['Prochaine publication'])
                            today = pd.Timestamp.now().normalize()
                            delta = (prochaine_date - today).days
                            if delta > 0:
                                st.write(f"**Dans {delta} jour(s)**")
                            elif delta == 0:
                                st.write("**Aujourd'hui !**")
                            else:
                                st.write(f"**En retard de {abs(delta)} jour(s)**")
                        except:
                            pass
                
                # Bouton pour désélectionner
                if st.button("🔄 Désélectionner", help="Cliquez pour masquer les détails"):
                    # Nettoyer la sélection
                    if "selection_suivi" in st.session_state:
                        st.session_state["selection_suivi"] = {"rows": []}
                    st.rerun()
        else:
            with details_container:
                if len(df_display) > 0:
                    st.write(f"**{len(df_display)} jeu(x) de données** disponible(s) dans le tableau.")

        # Timeline de couverture temporelle basée sur les périodes de validité
        st.subheader("📈 Couverture temporelle des jeux de données")
        st.info("💡 Toutes les versions de chaque jeu de données sont affichées. La couleur est basée sur le statut de la version la plus récente.")
        
        if not df_filtered.empty:
            # Filtrer les lignes avec des dates valides pour le graphique
            df_timeline_valid = df_filtered.dropna(subset=['date_publication', 'date_prochaine_publication']).copy()
            
            if not df_timeline_valid.empty:
                # Configuration des couleurs personnalisées pour le graphique
                color_map = {
                    "En retard": "#ff4b4b",
                    "À mettre à jour": "#ffa500", 
                    "À jour": "#4caf50",
                    "MaJ non prévue": "#2196f3",
                    "Inconnu": "#bdbdbd"
                }
                
                # Timeline avancée avec barres de couverture temporelle
                try:
                    # Créer un graphique plotly vide
                    fig = go.Figure()
                    
                    # Nettoyer les données pour éviter les valeurs 'undefined'
                    df_clean = df_timeline_valid.copy()
                    df_clean = df_clean.fillna('Non spécifié')
                    
                    # Trier les données par jeu de données et date de publication pour un affichage cohérent
                    df_clean = df_clean.sort_values(['nom_jeu_donnees', 'date_publication'], ascending=[True, True])
                    
                    # Créer une liste unique des jeux de données pour l'affichage Y
                    jeux_uniques = sorted(df_clean['nom_jeu_donnees'].unique())
                    
                    # Étape 1: Ajouter les barres de couverture temporelle (publication → fin de validité)
                    for idx, row in df_clean.iterrows():
                        # Vérifier que les données sont valides
                        if pd.isna(row['date_publication']) or pd.isna(row['date_prochaine_publication']):
                            continue
                        
                        # Utiliser le nom du jeu de données (toutes les versions sur la même ligne)
                        dataset_name = row['nom_jeu_donnees']
                        
                        # Barre horizontale : de la date de publication à la fin de validité
                        fig.add_trace(go.Scatter(
                            x=[row['date_publication'], row['date_prochaine_publication']],
                            y=[dataset_name, dataset_name],
                            mode='lines',
                            line=dict(
                                color=color_map.get(row['statut'], '#bdbdbd'),
                                width=6
                            ),
                            showlegend=False,
                            hoverinfo='skip'  # Désactiver complètement le hover pour les barres
                        ))
                    
                    # Étape 2: Ajouter les points de publication (par-dessus les barres)
                    for idx, row in df_clean.iterrows():
                        if pd.isna(row['date_publication']):
                            continue
                        
                        # Utiliser le nom du jeu de données (toutes les versions sur la même ligne)
                        dataset_name = row['nom_jeu_donnees']
                        
                        # Créer un hovertemplate propre avec info de la version
                        hover_text = (
                            f"<b>Publication</b><br>"
                            f"Jeu: {str(row['nom_jeu_donnees'])}<br>"
                            f"Millésime: {str(row['millesime'])}<br>"
                            f"Date: {row['date_publication'].strftime('%Y-%m-%d')}<br>"
                            f"Fin validité: {row['date_prochaine_publication'].strftime('%Y-%m-%d')}<br>"
                            f"Producteur: {str(row['producteur'])}<br>"
                            f"Fréquence: {str(row['frequence_maj'])}<br>"
                            f"Statut: {str(row['statut'])}"
                        )
                        
                        fig.add_trace(go.Scatter(
                            x=[row['date_publication']],
                            y=[dataset_name],
                            mode='markers',
                            marker=dict(
                                color=color_map.get(row['statut'], '#bdbdbd'),
                                size=10,
                                symbol='circle',
                                line=dict(width=1, color='white')
                            ),
                            showlegend=False,
                            hovertemplate=hover_text + "<extra></extra>"
                        ))
                    
                    # Configuration du layout avec extension future
                    # Calculer les bornes temporelles étendues
                    min_date = df_clean['date_publication'].min()
                    max_date = df_clean['date_prochaine_publication'].max()
                    
                    # Étendre la timeline : 6 mois avant et 1 an après
                    extended_min = min_date - pd.DateOffset(months=6)
                    extended_max = max_date + pd.DateOffset(years=1)
                    
                    # Calculer la hauteur basée sur le nombre de jeux de données uniques
                    nb_jeux = len(jeux_uniques)
                    
                    fig.update_layout(
                        title="",
                        xaxis_title="",
                        yaxis_title="",
                        height=max(400, nb_jeux * 40),  # Hauteur basée sur le nombre de jeux de données
                        showlegend=False,
                        hovermode='closest',
                        font=dict(size=14),  # Agrandissement de la police
                        xaxis=dict(
                            range=[extended_min, extended_max],
                            showgrid=True,
                            gridwidth=1,
                            gridcolor='lightgray',
                            tickfont=dict(size=12),  # Taille de police pour les dates
                            title=""
                        ),
                        yaxis=dict(
                            categoryorder='array',
                            categoryarray=jeux_uniques[::-1],  # Inverser pour avoir le premier en haut
                            showgrid=True,
                            gridwidth=1,
                            gridcolor='lightgray',
                            tickfont=dict(size=11),  # Taille de police pour les noms des jeux de données
                            title=""
                        ),
                        margin=dict(l=10, r=10, t=10, b=10)  # Réduire les marges
                    )
                    
                    # Ligne verticale rouge "Aujourd'hui" avec shapes (plus simple)
                    try:
                        today = pd.Timestamp.now()
                        
                        # Ajouter une ligne verticale avec add_shape
                        fig.add_shape(
                            type="line",
                            x0=today, x1=today,
                            y0=-0.5, y1=nb_jeux - 0.5,
                            line=dict(
                                color="red",
                                width=3,
                                dash="dash"
                            )
                        )
                        
                        # Ajouter annotation pour "Aujourd'hui"
                        fig.add_annotation(
                            x=today,
                            y=nb_jeux - 0.5,
                            text="Aujourd'hui",
                            showarrow=True,
                            arrowhead=2,
                            arrowcolor="red",
                            bgcolor="rgba(255,255,255,0.8)",
                            bordercolor="red",
                            borderwidth=1
                        )
                        
                    except Exception as e:
                        # Si toujours des problèmes, on continue sans la ligne
                        pass
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                except Exception as e:
                    st.error(f"Erreur lors de la création du graphique : {e}")
                    st.warning("Problème temporaire avec l'affichage des graphiques.")
                    
                    # Affichage alternatif sous forme de tableau
                    st.subheader("📋 Résumé des publications par jeu de données")
                    summary_table = df_timeline_valid.groupby('nom_jeu_donnees').agg({
                        'date_publication': ['min', 'max', 'count'],
                        'producteur': 'first',
                        'statut': lambda x: x.mode().iloc[0] if not x.mode().empty else 'Inconnu'
                    }).round(2)
                    st.dataframe(summary_table, use_container_width=True)
            else:
                st.warning("Aucun jeu de données avec des dates valides pour afficher la timeline.")
            
            # Légende des statuts
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.markdown(f"🔴 **En retard** ({len(df[df['statut'] == 'En retard'])})")
            with col2:
                st.markdown(f"🟠 **À mettre à jour** ({len(df[df['statut'] == 'À mettre à jour'])})")
            with col3:
                st.markdown(f"🟢 **À jour** ({len(df[df['statut'] == 'À jour'])})")
            with col4:
                st.markdown(f"🔵 **MaJ non prévue** ({len(df[df['statut'] == 'MaJ non prévue'])})")
            with col5:
                st.markdown(f"⚪ **Inconnu** ({len(df[df['statut'] == 'Inconnu'])})")
        else:
            st.info("Aucune donnée à afficher pour les filtres sélectionnés.")

except Exception as e:
    st.error(f"Une erreur est survenue : {str(e)}")
    st.info("Veuillez vérifier la connexion à la base de données et réessayer.") 