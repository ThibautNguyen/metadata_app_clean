import os
import json
import sys
from db_utils import get_db_connection, get_metadata

def print_metadata_info():
    """Affiche les informations sur les métadonnées stockées dans la base de données"""
    print("=== Vérification des métadonnées ===")
    
    # Récupérer toutes les métadonnées
    metadata_results = get_metadata()
    
    if not metadata_results:
        print("Aucune métadonnée trouvée dans la base de données.")
        return
    
    print(f"Nombre de métadonnées trouvées : {len(metadata_results)}")
    
    # Afficher les informations pour chaque métadonnée
    for i, meta in enumerate(metadata_results[:3]):  # Limiter à 3 pour la lisibilité
        print(f"\n--- Métadonnée #{i+1} ---")
        print(f"ID (si présent) : {meta.get('id', 'Non disponible')}")
        print(f"Nom de la table : {meta.get('nom_table', 'Non disponible')}")
        print(f"Nom de la base : {meta.get('nom_base', 'Non disponible')}")
        print(f"Producteur : {meta.get('producteur', 'Non disponible')}")
        print(f"Schéma : {meta.get('schema', 'Non disponible')}")
        print(f"Description : {meta.get('description', 'Non disponible')[:100]}...")  # Tronquer la description
        
        # Vérifier si le contenu CSV est présent et valide
        if meta.get('contenu_csv'):
            print("\nContenu CSV :")
            if isinstance(meta['contenu_csv'], dict):
                # Déjà un dictionnaire
                csv_data = meta['contenu_csv']
            else:
                # Essayer de décoder le JSON
                try:
                    csv_data = json.loads(meta['contenu_csv'])
                    print("  - Décodage JSON réussi")
                except:
                    print("  - Erreur de décodage JSON")
                    csv_data = None
            
            if csv_data and isinstance(csv_data, dict):
                if 'header' in csv_data and 'data' in csv_data:
                    print(f"  - En-tête : {csv_data['header']}")
                    print(f"  - Nombre de lignes de données : {len(csv_data['data'])}")
                    print(f"  - Séparateur : {csv_data.get('separator', 'Non spécifié')}")
                    
                    # Afficher un exemple de données
                    if csv_data['data']:
                        print(f"  - Exemple de données : {csv_data['data'][0]}")
                else:
                    print("  - Format non valide (manque header ou data)")
            else:
                print("  - Format non valide")
        else:
            print("\nAucun contenu CSV trouvé.")
        
        # Vérifier si le dictionnaire est présent et valide
        if meta.get('dictionnaire'):
            print("\nDictionnaire des variables :")
            if isinstance(meta['dictionnaire'], dict):
                # Déjà un dictionnaire
                dict_data = meta['dictionnaire']
            else:
                # Essayer de décoder le JSON
                try:
                    dict_data = json.loads(meta['dictionnaire'])
                    print("  - Décodage JSON réussi")
                except:
                    print("  - Erreur de décodage JSON")
                    dict_data = None
            
            if dict_data and isinstance(dict_data, dict):
                if 'header' in dict_data and 'data' in dict_data:
                    print(f"  - En-tête : {dict_data['header']}")
                    print(f"  - Nombre de lignes de données : {len(dict_data['data'])}")
                    print(f"  - Séparateur : {dict_data.get('separator', 'Non spécifié')}")
                    
                    # Afficher un exemple de données
                    if dict_data['data']:
                        print(f"  - Exemple de données : {dict_data['data'][0]}")
                else:
                    print("  - Format non valide (manque header ou data)")
            else:
                print("  - Format non valide")
        else:
            print("\nAucun dictionnaire trouvé.")
    
    if len(metadata_results) > 3:
        print(f"\n... et {len(metadata_results) - 3} autres métadonnées.")

def check_db_connection():
    """Vérifie si la connexion à la base de données fonctionne"""
    print("=== Vérification de la connexion à la base de données ===")
    conn = get_db_connection()
    if conn:
        print("Connexion à la base de données réussie !")
        conn.close()
        return True
    else:
        print("Échec de la connexion à la base de données.")
        return False

if __name__ == "__main__":
    print("Vérification de la base de données PostgreSQL...")
    
    # Vérifier la connexion
    if check_db_connection():
        # Afficher les informations sur les métadonnées
        print_metadata_info()
    else:
        print("Impossible de vérifier les métadonnées car la connexion à la base de données a échoué.")
    
    print("\n=== Fin de la vérification ===") 