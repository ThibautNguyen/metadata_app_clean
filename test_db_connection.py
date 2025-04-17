import psycopg2
from psycopg2 import Error

try:
    # Connexion à la base de données
    connection = psycopg2.connect(
        host="localhost",
        port="5432",
        database="opendata",
        user="cursor_ai",
        password="cursor_ai_is_quite_awesome"
    )

    # Création d'un curseur
    cursor = connection.cursor()

    # Exécution de la requête pour lister les tables
    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
    """)

    # Récupération des résultats
    tables = cursor.fetchall()
    
    print("Tables disponibles dans le schéma public :")
    for table in tables:
        print(f"- {table[0]}")

except (Exception, Error) as error:
    print("Erreur lors de la connexion à PostgreSQL :", error)

finally:
    if 'connection' in locals():
        cursor.close()
        connection.close()
        print("\nConnexion PostgreSQL fermée") 