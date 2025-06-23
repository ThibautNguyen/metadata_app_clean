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
    today = pd.Timestamp.now().normalize()  # Utiliser Timestamp pour la compatibilité
    
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
        
        # Calcul du statut
        df['statut'] = df.apply(compute_status, axis=1)
        
        # Réorganisation des colonnes pour le tableau principal et formatage des dates
        df_display = df.copy()
        # Formater les dates pour l'affichage
        df_display['date_publication'] = df_display['date_publication'].dt.strftime('%Y-%m-%d')
        df_display['date_prochaine_publication'] = df_display['date_prochaine_publication'].dt.strftime('%Y-%m-%d')
        
        df_display = df_display.rename(columns={
            'nom_jeu_donnees': 'Jeu de données',
            'producteur': 'Producteur',
            'date_publication': 'Dernière publication',
            'millesime': 'Millésime',
            'date_prochaine_publication': 'Prochaine publication',
            'frequence_maj': 'Fréquence',
            'statut': 'Statut'
        })

        # Affichage du tableau avec st.dataframe pour permettre la sélection
        st.subheader("Tableau de suivi")
        st.info("💡 Cliquez sur une ligne du tableau pour afficher les détails détaillés ci-dessous.")
        
        # Création d'un conteneur pour le tableau
        table_container = st.container()
        
        with table_container:
            selection_state = st.dataframe(
                df_display,
                on_select="rerun",
                selection_mode="single-row",
                key="selection_suivi",
                hide_index=True,
                column_order=["Jeu de données", "Producteur", "Dernière publication", 
                             "Millésime", "Prochaine publication", 
                             "Fréquence", "Statut"],
                use_container_width=True
            )

        # Debug de la sélection (à supprimer en production)
        # st.write("Debug - Selection state:", selection_state)
        # st.write("Debug - Session state:", st.session_state.get("selection_suivi", {}))

        # Gestion de la sélection et affichage des détails
        selection = st.session_state.get("selection_suivi", {"rows": []})

        # Création d'un conteneur pour les détails
        details_container = st.container()

        if selection.get("rows") and len(selection["rows"]) > 0:
            with details_container:
                selected_index = selection["rows"][0]
                selected_row = df_display.iloc[selected_index]
                
                st.markdown("---")
                st.markdown(f"### 📋 Détail du jeu de données : **{selected_row['Jeu de données']}**")
                
                # Affichage avec un style amélioré
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("#### 📊 Informations générales")
                    st.write(f"**Producteur :** {selected_row['Producteur']}")
                    st.write(f"**Fréquence de mise à jour :** {selected_row['Fréquence']}")
                
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
                    st.session_state["selection_suivi"] = {"rows": []}
                    st.rerun()
        else:
            with details_container:
                st.info("👆 Cliquez sur une ligne du tableau ci-dessus pour afficher les détails.")
                if len(df_display) > 0:
                    st.write(f"**{len(df_display)} jeu(x) de données** disponible(s) dans le tableau.")

        # Timeline de couverture temporelle basée sur les périodes de validité
        st.subheader("📈 Timeline de couverture temporelle des jeux de données")
        if not df.empty:
            # Filtrer les lignes avec des dates valides pour le graphique
            df_timeline_valid = df.dropna(subset=['date_publication', 'date_prochaine_publication']).copy()
            
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
                    
                    # Étape 1: Ajouter les barres de couverture temporelle (publication → fin de validité)
                    for idx, row in df_timeline_valid.iterrows():
                        # Barre horizontale : de la date de publication à la fin de validité
                        fig.add_trace(go.Scatter(
                            x=[row['date_publication'], row['date_prochaine_publication']],
                            y=[row['nom_jeu_donnees'], row['nom_jeu_donnees']],
                            mode='lines',
                            line=dict(
                                color=color_map.get(row['statut'], '#bdbdbd'),
                                width=6
                            ),
                            name=f"Période validité",
                            showlegend=False,
                            hovertemplate=(
                                f"<b>Période de validité</b><br>"
                                f"Jeu: {row['nom_jeu_donnees']}<br>"
                                f"De: {row['date_publication'].strftime('%Y-%m-%d')}<br>"
                                f"À: {row['date_prochaine_publication'].strftime('%Y-%m-%d')}<br>"
                                f"Statut: {row['statut']}<br>"
                                "<extra></extra>"
                            )
                        ))
                    
                    # Étape 2: Ajouter les points de publication (par-dessus les barres)
                    for idx, row in df_timeline_valid.iterrows():
                        fig.add_trace(go.Scatter(
                            x=[row['date_publication']],
                            y=[row['nom_jeu_donnees']],
                            mode='markers',
                            marker=dict(
                                color=color_map.get(row['statut'], '#bdbdbd'),
                                size=10,
                                symbol='circle',
                                line=dict(width=1, color='white')
                            ),
                            name=f"Publication",
                            showlegend=False,
                            hovertemplate=(
                                f"<b>Publication</b><br>"
                                f"Jeu: {row['nom_jeu_donnees']}<br>"
                                f"Date: {row['date_publication'].strftime('%Y-%m-%d')}<br>"
                                f"Producteur: {row['producteur']}<br>"
                                f"Fréquence: {row['frequence_maj']}<br>"
                                f"Statut: {row['statut']}<br>"
                                "<extra></extra>"
                            )
                        ))
                    
                    # Configuration du layout
                    fig.update_layout(
                        title="Timeline de couverture temporelle (publication → fin de validité)",
                        xaxis_title="Période",
                        yaxis_title="Jeu de données",
                        height=max(400, len(df_timeline_valid['nom_jeu_donnees'].unique()) * 40),
                        showlegend=False,
                        hovermode='closest'
                    )
                    
                    # Ligne verticale "Aujourd'hui" (méthode compatible)
                    try:
                        today = pd.Timestamp.now().normalize()
                        fig.add_vline(
                            x=today,
                            line_width=2,
                            line_color="red",
                            line_dash="dash",
                            annotation_text="Aujourd'hui",
                            annotation_position="top"
                        )
                    except Exception as e:
                        # Si problème avec la ligne verticale, on continue sans
                        pass
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Informations sur la timeline améliorée
                    st.info(
                        "📊 **Timeline de couverture temporelle :** "
                        "Les barres horizontales colorées montrent la période de validité de chaque jeu de données "
                        "(de la publication jusqu'à la prochaine mise à jour prévue). "
                        "Les points circulaires marquent les dates de publication spécifiques."
                    )
                    
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
            st.markdown("#### 🎨 Légende des statuts")
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