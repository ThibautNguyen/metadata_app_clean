import os
import json
import psycopg2
from psycopg2.extras import RealDictCursor

# Paramètres de connexion à la base de données - SÉCURISÉS
def get_db_params():
    """Récupère les paramètres de connexion de manière sécurisée"""
    required_vars = ['NEON_HOST', 'NEON_DATABASE', 'NEON_USER', 'NEON_PASSWORD']
    db_params = {'sslmode': 'require'}
    
    missing_vars = []
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            missing_vars.append(var)
        else:
            db_params[var.lower().replace('neon_', '')] = value
    
    if missing_vars:
        raise Exception(f"Variables d'environnement manquantes : {', '.join(missing_vars)}")
    
    return db_params

def check_db_connection():
    """Vérifie la connexion à la base de données"""
    try:
        # Récupération sécurisée des paramètres
        db_params = get_db_params()
        
        # Établir une connexion à la base de données
        conn = psycopg2.connect(**db_params)
        
        # Créer un curseur
        with conn.cursor() as cur:
            # Exécuter une requête simple
            cur.execute("SELECT 1")
            result = cur.fetchone()
            if result and result[0] == 1:
                print("Connexion à la base de données réussie !")
                return True
        
        # Fermer la connexion
        conn.close()
        return False
    except Exception as e:
        print(f"Erreur de connexion à la base de données : {str(e)}")
        print("Vérifiez que les variables d'environnement NEON_* sont définies")
        return False

def check_metadata_table():
    """Vérifie si la table metadata existe et récupère sa structure"""
    try:
        # Récupération sécurisée des paramètres
        db_params = get_db_params()
        
        # Établir une connexion à la base de données
        conn = psycopg2.connect(**db_params)
        
        # Créer un curseur
        with conn.cursor() as cur:
            # Vérifier si la table metadata existe
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'metadata'
                )
            """)
            table_exists = cur.fetchone()[0]
            
            if not table_exists:
                print("La table 'metadata' n'existe pas.")
                conn.close()
                return False
            
            # Récupérer la structure de la table
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'metadata'
                ORDER BY ordinal_position
            """)
            
            columns = cur.fetchall()
            print("\nStructure de la table 'metadata':")
            for col_name, col_type in columns:
                print(f"- {col_name}: {col_type}")
            
            # Compter le nombre d'enregistrements
            cur.execute("SELECT COUNT(*) FROM metadata")
            count = cur.fetchone()[0]
            print(f"\nNombre d'enregistrements dans la table 'metadata': {count}")
            
            # Si des enregistrements existent, afficher quelques-uns
            if count > 0:
                cur.execute("SELECT * FROM metadata LIMIT 3")
                rows = cur.fetchall()
                print("\nAperçu des enregistrements (ID, nom_table, nom_base, producteur, schema):")
                for row in rows:
                    print(f"- ID: {row[0]}, Nom table: {row[1]}, Nom base: {row[2]}, Producteur: {row[3]}, Schema: {row[4]}")
                
                # Vérifier le contenu CSV et le dictionnaire
                with conn.cursor(cursor_factory=RealDictCursor) as dict_cur:
                    dict_cur.execute("SELECT id, nom_table, contenu_csv, dictionnaire FROM metadata LIMIT 1")
                    row = dict_cur.fetchone()
                    
                    if row:
                        print(f"\nVérification du contenu CSV et du dictionnaire pour l'enregistrement ID {row['id']}:")
                        
                        # Vérifier le contenu_csv
                        if row['contenu_csv']:
                            print("- contenu_csv est présent")
                            try:
                                if isinstance(row['contenu_csv'], str):
                                    csv_data = json.loads(row['contenu_csv'])
                                else:
                                    csv_data = row['contenu_csv']
                                
                                if isinstance(csv_data, dict) and 'header' in csv_data and 'data' in csv_data:
                                    print(f"  - Format valide avec en-tête: {csv_data['header']}")
                                    print(f"  - Nombre de lignes de données: {len(csv_data['data'])}")
                                else:
                                    print("  - Format non valide (manque header ou data)")
                            except Exception as e:
                                print(f"  - Erreur de décodage JSON: {str(e)}")
                        else:
                            print("- contenu_csv est absent")
                        
                        # Vérifier le dictionnaire
                        if row['dictionnaire']:
                            print("- dictionnaire est présent")
                            try:
                                if isinstance(row['dictionnaire'], str):
                                    dict_data = json.loads(row['dictionnaire'])
                                else:
                                    dict_data = row['dictionnaire']
                                
                                if isinstance(dict_data, dict) and 'header' in dict_data and 'data' in dict_data:
                                    print(f"  - Format valide avec en-tête: {dict_data['header']}")
                                    print(f"  - Nombre de lignes de données: {len(dict_data['data'])}")
                                else:
                                    print("  - Format non valide (manque header ou data)")
                            except Exception as e:
                                print(f"  - Erreur de décodage JSON: {str(e)}")
                        else:
                            print("- dictionnaire est absent")
        
        # Fermer la connexion
        conn.close()
        return True
    except Exception as e:
        print(f"Erreur lors de la vérification de la table 'metadata': {str(e)}")
        return False

if __name__ == "__main__":
    print("=== Vérification de la base de données ===")
    if check_db_connection():
        check_metadata_table()
    print("=== Fin de la vérification ===") 