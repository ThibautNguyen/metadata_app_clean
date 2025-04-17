import psycopg2

# Connexion à la base de données
conn = psycopg2.connect(
    host="localhost",
    port="5432",
    database="opendata",
    user="cursor_ai",
    password="cursor_ai_is_quite_awesome"
)

# Création d'un curseur
cur = conn.cursor()

try:
    # Vérifier le search_path actuel
    print("Search path actuel :")
    cur.execute("SHOW search_path;")
    print(cur.fetchone()[0])
    
    print("\nSchémas accessibles pour l'utilisateur cursor_ai :")
    cur.execute("""
        SELECT 
            nspname AS schema_name,
            has_schema_privilege('cursor_ai', nspname, 'USAGE') as has_usage,
            has_schema_privilege('cursor_ai', nspname, 'CREATE') as has_create
        FROM pg_namespace
        WHERE nspname NOT LIKE 'pg_%' 
        AND nspname != 'information_schema'
        ORDER BY schema_name;
    """)
    schemas = cur.fetchall()
    for schema in schemas:
        print(f"Schéma : {schema[0]}")
        print(f"- Droit USAGE : {schema[1]}")
        print(f"- Droit CREATE : {schema[2]}")
    
    print("\nTables accessibles dans le schéma 'reseau' :")
    cur.execute("""
        SELECT 
            table_name,
            has_table_privilege('cursor_ai', 'reseau.' || table_name, 'SELECT') as has_select
        FROM information_schema.tables 
        WHERE table_schema = 'reseau'
        ORDER BY table_name;
    """)
    tables = cur.fetchall()
    for table in tables:
        print(f"Table : {table[0]}")
        print(f"- Droit SELECT : {table[1]}")

except psycopg2.Error as e:
    print(f"\nErreur PostgreSQL détaillée :")
    print(f"Code erreur : {e.pgcode}")
    print(f"Message : {e.pgerror}")
    print(f"Détails : {e.diag.message_detail if e.diag.message_detail else 'Pas de détails supplémentaires'}")
    print(f"Indice : {e.diag.message_hint if e.diag.message_hint else 'Pas d\'indice disponible'}")

finally:
    # Fermeture de la connexion
    cur.close()
    conn.close() 