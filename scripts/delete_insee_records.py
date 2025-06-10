import psycopg2
from psycopg2.extras import RealDictCursor
import logging

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def delete_insee_records():
    try:
        logging.info("Démarrage de la fonction delete_insee_records")
        
        # Paramètres de connexion
        db_params = {
            'host': 'ep-wispy-queen-abzi1lne-pooler.eu-west-2.aws.neon.tech',
            'database': 'neondb',
            'user': 'neondb_owner',
            'password': 'npg_XsA4wfvHy2Rn',
            'sslmode': 'require'
        }
        
        logging.info("Tentative de connexion à la base de données")
        # Connexion à la base de données
        conn = psycopg2.connect(**db_params)
        logging.info("Connexion réussie")
        
        # Afficher d'abord les enregistrements qui seront supprimés
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            logging.info("Exécution de la requête SELECT")
            cur.execute("""
                SELECT id, nom_table, nom_base, producteur, schema 
                FROM metadata 
                WHERE producteur = 'INSEE' 
                AND (nom_base ILIKE '%Population%' OR nom_base ILIKE '%Logement%');
            """)
            records = cur.fetchall()
            
            if records:
                print("\nEnregistrements qui seront supprimés :")
                for record in records:
                    print(f"- ID: {record['id']}, Table: {record['nom_table']}, Base: {record['nom_base']}, Producteur: {record['producteur']}, Schema: {record['schema']}")
                
                # Demander confirmation
                confirmation = input("\nVoulez-vous procéder à la suppression ? (oui/non) : ")
                if confirmation.lower() != 'oui':
                    print("Suppression annulée.")
                    return
                
                # Procéder à la suppression
                logging.info("Exécution de la requête DELETE")
                cur.execute("""
                    DELETE FROM metadata 
                    WHERE producteur = 'INSEE' 
                    AND (nom_base ILIKE '%Population%' OR nom_base ILIKE '%Logement%');
                """)
                deleted_count = cur.rowcount
                
                # Commit des changements
                conn.commit()
                print(f"\nNombre d'enregistrements supprimés : {deleted_count}")
            else:
                print("Aucun enregistrement trouvé correspondant aux critères.")
        
    except Exception as e:
        logging.error(f"Erreur lors de la suppression : {str(e)}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()
            logging.info("Connexion fermée")

if __name__ == "__main__":
    logging.info("Démarrage du script")
    delete_insee_records()
    logging.info("Fin du script") 