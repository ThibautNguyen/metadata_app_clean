import os
import psycopg2
import json

# Paramètres de connexion à la base de données
DB_PARAMS = {
    "host": os.getenv("NEON_HOST", "ep-wispy-queen-abzi1lne-pooler.eu-west-2.aws.neon.tech"),
    "database": os.getenv("NEON_DATABASE", "neondb"),
    "user": os.getenv("NEON_USER", "neondb_owner"),
    "password": os.getenv("NEON_PASSWORD", "npg_XsA4wfvHy2Rn"),
    "sslmode": "require"
}

def test_connection():
    """Teste la connexion à la base de données"""
    try:
        print("Tentative de connexion à la base de données PostgreSQL...")
        conn = psycopg2.connect(**DB_PARAMS)
        print("Connexion réussie !")
        
        # Fermer la connexion
        conn.close()
        print("Connexion fermée.")
        return True
    except Exception as e:
        print(f"Erreur de connexion : {e}")
        return False

def test_metadata_table():
    """Teste la présence de la table metadata et affiche ses colonnes"""
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        cursor = conn.cursor()
        
        # Vérifier si la table metadata existe
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'metadata'
            )
        """)
        table_exists = cursor.fetchone()[0]
        
        if not table_exists:
            print("La table 'metadata' n'existe pas.")
            conn.close()
            return False
        
        print("La table 'metadata' existe.")
        
        # Récupérer les colonnes de la table
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'metadata'
            ORDER BY ordinal_position
        """)
        
        columns = cursor.fetchall()
        print("\nColonnes de la table metadata:")
        for column in columns:
            print(f"- {column[0]} ({column[1]})")
        
        # Compter le nombre d'entrées
        cursor.execute("SELECT COUNT(*) FROM metadata")
        count = cursor.fetchone()[0]
        print(f"\nNombre d'entrées dans la table metadata: {count}")
        
        # Afficher quelques entrées s'il y en a
        if count > 0:
            print("\nAperçu des données (max 3 entrées):")
            cursor.execute("SELECT * FROM metadata LIMIT 3")
            rows = cursor.fetchall()
            
            col_names = [desc[0] for desc in cursor.description]
            
            for row_idx, row in enumerate(rows):
                print(f"\n--- Entrée {row_idx+1} ---")
                # Afficher les colonnes principales
                main_cols = ["id", "nom_table", "nom_base", "producteur", "schema", "description"]
                for col in main_cols:
                    if col in col_names:
                        idx = col_names.index(col)
                        # Limiter la longueur pour la description
                        if col == "description" and row[idx]:
                            value = row[idx][:100] + "..." if len(row[idx]) > 100 else row[idx]
                        else:
                            value = row[idx]
                        print(f"{col}: {value}")
                
                # Vérifier le contenu_csv et le dictionnaire
                csv_idx = col_names.index("contenu_csv") if "contenu_csv" in col_names else -1
                dict_idx = col_names.index("dictionnaire") if "dictionnaire" in col_names else -1
                
                if csv_idx >= 0 and row[csv_idx]:
                    print("\ncontenu_csv est présent")
                    try:
                        # Tester si le JSON est valide
                        csv_data = json.loads(row[csv_idx]) if isinstance(row[csv_idx], str) else row[csv_idx]
                        if isinstance(csv_data, dict) and "header" in csv_data and "data" in csv_data:
                            print(f"- Format valide avec {len(csv_data['data'])} lignes de données")
                        else:
                            print("- Format incorrect (manque header ou data)")
                    except json.JSONDecodeError:
                        print("- Erreur de décodage JSON")
                else:
                    print("\ncontenu_csv est absent")
                
                if dict_idx >= 0 and row[dict_idx]:
                    print("\ndictionnaire est présent")
                    try:
                        # Tester si le JSON est valide
                        dict_data = json.loads(row[dict_idx]) if isinstance(row[dict_idx], str) else row[dict_idx]
                        if isinstance(dict_data, dict) and "header" in dict_data and "data" in dict_data:
                            print(f"- Format valide avec {len(dict_data['data'])} lignes de données")
                        else:
                            print("- Format incorrect (manque header ou data)")
                    except json.JSONDecodeError:
                        print("- Erreur de décodage JSON")
                else:
                    print("\ndictionnaire est absent")
        
        conn.close()
        return True
    except Exception as e:
        print(f"Erreur lors du test de la table metadata : {e}")
        return False

if __name__ == "__main__":
    print("====== Test de la base de données PostgreSQL ======")
    
    if test_connection():
        print("\n====== Test de la table metadata ======")
        test_metadata_table()
    
    print("\n====== Test terminé ======") 