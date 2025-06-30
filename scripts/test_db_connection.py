import psycopg2
from psycopg2 import Error
import logging
import os

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(module)s: %(message)s",
)

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

def test_connection():
    """Teste la connexion à la base de données Neon.tech"""
    try:
        # Paramètres de connexion sécurisés
        db_params = get_db_params()
        
        # Connexion à la base de données
        connection = psycopg2.connect(**db_params)
        logging.info("✓ Connexion établie avec succès")
        
        cursor = connection.cursor()
        
        # Test de la table metadata
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'metadata'
            );
        """)
        table_exists = cursor.fetchone()[0]
        
        if table_exists:
            # Compte le nombre d'enregistrements
            cursor.execute("SELECT COUNT(*) FROM metadata")
            count = cursor.fetchone()[0]
            logging.info(f"✓ Nombre d'enregistrements dans la table metadata: {count}")
            
            # Affiche la structure de la table
            cursor.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'metadata'
                ORDER BY ordinal_position;
            """)
            print("\nStructure de la table metadata:")
            for col in cursor.fetchall():
                print(f"- {col[0]}: {col[1]}")
            
            # Échantillon de données
            cursor.execute("SELECT * FROM metadata LIMIT 5;")
            sample = cursor.fetchall()
            print("\nÉchantillon de données:")
            for row in sample:
                print(f"- {row}")
        else:
            logging.error("❌ La table 'metadata' n'existe pas")
            
        return True
        
    except (Exception, Error) as error:
        logging.error(f"❌ Erreur: {error}")
        return False
        
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()
            logging.info("Connexion fermée")

if __name__ == "__main__":
    print("=== Test de connexion à la base de données Neon.tech ===\n")
    success = test_connection()
    print(f"\n=== Résumé ===")
    print(f"Test de connexion: {'✓' if success else '❌'}") 