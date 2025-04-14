import json
import logging
import streamlit as st
from .db_connection import get_db_connection

def get_metadata(filters=None):
    """Récupère les métadonnées de la base de données avec des filtres optionnels"""
    conn = get_db_connection()
    if not conn:
        return []
        
    try:
        with conn.cursor() as cur:
            query = "SELECT * FROM metadata"
            params = []
            
            # Si un filtre texte est passé directement (pour rétrocompatibilité)
            if filters is not None and isinstance(filters, str) and filters.strip():
                search_term = f"%{filters}%"
                query += """ WHERE 
                    nom_fichier ILIKE %s OR 
                    nom_base ILIKE %s OR 
                    schema ILIKE %s OR 
                    description ILIKE %s OR 
                    mots_cles ILIKE %s
                """
                params = [search_term, search_term, search_term, search_term, search_term]
            # Si un dictionnaire de filtres est passé
            elif filters and isinstance(filters, dict):
                conditions = []
                
                # Filtres exacts (égalité)
                for key, value in filters.items():
                    if value:
                        conditions.append(f"{key} = %s")
                        params.append(value)
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
            
            logging.debug(f"Requête SQL get_metadata: {query}")
            logging.debug(f"Paramètres: {params}")
            
            cur.execute(query, params)
            columns = [desc[0] for desc in cur.description]
            results = []
            
            for row in cur.fetchall():
                metadata = dict(zip(columns, row))
                # Décodage des données JSON
                if metadata.get("contenu_csv"):
                    try:
                        if isinstance(metadata["contenu_csv"], str):
                            metadata["contenu_csv"] = json.loads(metadata["contenu_csv"])
                    except json.JSONDecodeError:
                        st.warning("Erreur lors du décodage du contenu CSV")
                        logging.warning("Erreur lors du décodage du contenu CSV")
                
                if metadata.get("dictionnaire"):
                    try:
                        if isinstance(metadata["dictionnaire"], str):
                            metadata["dictionnaire"] = json.loads(metadata["dictionnaire"])
                    except json.JSONDecodeError:
                        st.warning("Erreur lors du décodage du dictionnaire")
                        logging.warning("Erreur lors du décodage du dictionnaire")
                
                results.append(metadata)
            
            logging.info(f"Nombre de résultats trouvés : {len(results)}")
            return results
            
    except Exception as e:
        logging.error(f"Erreur lors de la récupération des métadonnées : {str(e)}")
        st.error(f"Erreur lors de la récupération des métadonnées : {str(e)}")
        return []
    finally:
        conn.close()