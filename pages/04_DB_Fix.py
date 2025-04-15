import streamlit as st
import sys
from pathlib import Path
import logging
import psycopg2
from psycopg2.extras import RealDictCursor

# Ajout du répertoire parent au PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent))
from db_utils import get_db_connection

# Configuration de la page
st.set_page_config(
    page_title="Réparation de la base de données",
    page_icon="🔧",
    layout="wide"
)

# CSS pour le style de l'interface
st.markdown("""
<style>
    .main h1 {
        color: #E74C3C;
    }
    .stButton button {
        background-color: #E74C3C;
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# Titre et description
st.title("🔧 Réparation de la base de données")
st.write("Utilisez cette page pour réparer les problèmes de structure de la base de données.")

def check_table_structure():
    """Vérifie si la table metadata existe et si elle contient tous les champs requis"""
    conn = get_db_connection()
    if not conn:
        return False, "Impossible de se connecter à la base de données"
    
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Vérifier si la table existe
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'metadata'
                );
            """)
            table_exists = cur.fetchone()['exists']
            
            if not table_exists:
                return False, "La table metadata n'existe pas"
            
            # Vérifier les colonnes de la table
            cur.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'metadata';
            """)
            
            columns = [row['column_name'] for row in cur.fetchall()]
            required_columns = [
                'id', 'nom_fichier', 'nom_base', 'schema', 'description',
                'date_creation', 'date_maj', 'source', 'frequence_maj',
                'licence', 'envoi_par', 'contact', 'mots_cles', 'notes',
                'contenu_csv', 'dictionnaire', 'created_at'
            ]
            
            missing_columns = [col for col in required_columns if col not in columns]
            
            if missing_columns:
                return False, f"Colonnes manquantes dans la table: {', '.join(missing_columns)}"
            
            return True, "La structure de la table metadata est correcte"
            
    except Exception as e:
        return False, f"Erreur lors de la vérification de la structure: {str(e)}"
    finally:
        conn.close()

def fix_table_structure():
    """Corrige la structure de la table metadata"""
    conn = get_db_connection()
    if not conn:
        return False, "Impossible de se connecter à la base de données"
    
    try:
        with conn.cursor() as cur:
            # Récupérer les données existantes si la table existe
            existing_data = []
            try:
                cur.execute("SELECT * FROM metadata")
                columns = [desc[0] for desc in cur.description]
                existing_data = [dict(zip(columns, row)) for row in cur.fetchall()]
                st.info(f"Sauvegarde de {len(existing_data)} entrées existantes")
            except Exception as e:
                st.warning(f"Impossible de récupérer les données existantes: {str(e)}")
            
            # Supprimer la table si elle existe
            cur.execute("DROP TABLE IF EXISTS metadata")
            conn.commit()
            
            # Recréer la table avec la structure correcte
            cur.execute("""
                CREATE TABLE metadata (
                    id SERIAL PRIMARY KEY,
                    nom_fichier VARCHAR(255) NOT NULL,
                    nom_base VARCHAR(255),
                    schema VARCHAR(255),
                    description TEXT,
                    date_creation DATE,
                    date_maj DATE,
                    source VARCHAR(255),
                    frequence_maj VARCHAR(255),
                    licence VARCHAR(255),
                    envoi_par VARCHAR(255),
                    contact VARCHAR(255),
                    mots_cles TEXT,
                    notes TEXT,
                    contenu_csv JSONB,
                    dictionnaire JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            
            # Restaurer les données si elles existaient
            if existing_data:
                for record in existing_data:
                    # Préparer les champs présents dans les anciens enregistrements
                    fields = [key for key in record.keys() if key != 'id']
                    placeholders = ', '.join(['%s'] * len(fields))
                    query = f"INSERT INTO metadata ({', '.join(fields)}) VALUES ({placeholders})"
                    
                    # Valeurs pour l'insertion
                    values = [record[field] for field in fields]
                    
                    cur.execute(query, values)
                
                conn.commit()
                st.success(f"Restauration de {len(existing_data)} entrées réussie")
            
            return True, "La table metadata a été recréée avec succès"
            
    except Exception as e:
        conn.rollback()
        return False, f"Erreur lors de la réparation de la structure: {str(e)}"
    finally:
        conn.close()

# Vérifier l'état actuel de la table
status, message = check_table_structure()

if status:
    st.success(message)
else:
    st.error(message)
    
    # Option pour corriger la structure
    if st.button("🛠️ Réparer la structure de la table"):
        with st.spinner("Réparation en cours..."):
            success, repair_message = fix_table_structure()
            if success:
                st.success(repair_message)
                st.balloons()
                # Vérifier à nouveau après la réparation
                new_status, new_message = check_table_structure()
                if new_status:
                    st.success("Vérification après réparation: " + new_message)
                else:
                    st.error("Vérification après réparation: " + new_message)
            else:
                st.error(repair_message)

# Section d'inspection des données
st.markdown("## Inspection des données")

if status:
    if st.button("📊 Afficher les métadonnées enregistrées"):
        conn = get_db_connection()
        if conn:
            try:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("SELECT * FROM metadata")
                    rows = cur.fetchall()
                    
                    if rows:
                        st.write(f"Nombre total d'entrées: {len(rows)}")
                        for i, row in enumerate(rows):
                            with st.expander(f"Entrée #{i+1}: {row['nom_fichier']}"):
                                for key, value in row.items():
                                    st.write(f"**{key}**: {value}")
                    else:
                        st.info("Aucune métadonnée trouvée dans la base de données")
            except Exception as e:
                st.error(f"Erreur lors de l'inspection: {str(e)}")
            finally:
                conn.close()

# Section d'aide
with st.expander("❓ Comment utiliser cette page"):
    st.markdown("""
    ### À propos de cet outil de réparation
    
    Cette page vous permet de diagnostiquer et corriger les problèmes de structure dans la table de métadonnées.
    
    1. **Diagnostic**: Le système vérifie automatiquement si la table existe et si elle contient toutes les colonnes requises.
    
    2. **Réparation**: Si des problèmes sont détectés, vous pouvez cliquer sur le bouton "Réparer la structure de la table" pour:
       - Sauvegarder les données existantes (si possible)
       - Supprimer la table actuelle
       - Recréer la table avec la structure correcte
       - Restaurer les données sauvegardées
       
    3. **Inspection**: Vous pouvez inspecter les métadonnées actuellement enregistrées dans la base de données.
    
    ### Quand utiliser cet outil?
    
    Utilisez cet outil lorsque vous rencontrez des erreurs comme:
    - "column X does not exist"
    - Problèmes lors de l'insertion ou de la récupération des métadonnées
    - Erreurs liées à la structure de la table
    
    **Note**: La réparation de la structure **ne supprimera pas** vos données existantes, sauf si elles ne peuvent pas être adaptées à la nouvelle structure.
    """)

# Pied de page
st.markdown("---")
st.markdown("© 2025 - Système de Gestion des Métadonnées v1.0") 