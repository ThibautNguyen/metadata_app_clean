import psycopg2
from psycopg2.extras import RealDictCursor

def check_database():
    try:
        # Connexion à la base de données
        conn = psycopg2.connect(
            host='ep-wispy-queen-abzi1lne-pooler.eu-west-2.aws.neon.tech',
            database="neondb",
            user="neondb_owner",
            password="npg_XsA4wfvHy2Rn",
            sslmode='require'
        )
        
        # Création d'un curseur
        cur = conn.cursor(cursor_factory=RealDictCursor)
        
        # Vérification de l'existence de la table metadata
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'metadata'
            );
        """)
        table_exists = cur.fetchone()['exists']
        print(f"La table metadata existe : {table_exists}")
        
        if table_exists:
            # Récupération du nombre de lignes
            cur.execute("SELECT COUNT(*) as count FROM metadata;")
            count = cur.fetchone()['count']
            print(f"\nNombre de lignes dans la table : {count}")
            
            if count > 0:
                # Récupération de toutes les métadonnées
                cur.execute("SELECT * FROM metadata;")
                rows = cur.fetchall()
                print("\nContenu de la table metadata :")
                for row in rows:
                    print("\n---")
                    for key, value in row.items():
                        print(f"{key}: {value}")
        
        # Fermeture de la connexion
        cur.close()
        conn.close()
        
    except Exception as e:
        print(f"Erreur : {str(e)}")

if __name__ == "__main__":
    check_database() 