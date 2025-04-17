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
    # Statistiques sur la couverture fibre
    print("Analyse de la couverture fibre :")
    cur.execute("""
        SELECT 
            CASE 
                WHEN "% Fibre" = '100%' THEN '100%'
                WHEN "% Fibre" >= '75%' THEN '75-99%'
                WHEN "% Fibre" >= '50%' THEN '50-74%'
                WHEN "% Fibre" >= '25%' THEN '25-49%'
                WHEN "% Fibre" > '0%' THEN '1-24%'
                WHEN "% Fibre" = '0%' THEN '0%'
                ELSE 'Non renseigné'
            END as tranche_couverture,
            COUNT(*) as nombre_communes
        FROM reseau.techno_internet_com_2024
        GROUP BY tranche_couverture
        ORDER BY 
            CASE tranche_couverture
                WHEN '100%' THEN 1
                WHEN '75-99%' THEN 2
                WHEN '50-74%' THEN 3
                WHEN '25-49%' THEN 4
                WHEN '1-24%' THEN 5
                WHEN '0%' THEN 6
                ELSE 7
            END;
    """)
    stats = cur.fetchall()
    
    print("\nRépartition des communes par taux de couverture fibre :")
    total = sum(row[1] for row in stats)
    for tranche, nombre in stats:
        pourcentage = (nombre / total) * 100
        print(f"{tranche:<10} : {nombre:>5} communes ({pourcentage:>5.1f}%)")

    # Top 5 des communes les mieux couvertes
    print("\nTop 5 des communes les mieux couvertes en fibre :")
    cur.execute("""
        SELECT "Commune", "% Fibre", "Code Insee"
        FROM reseau.techno_internet_com_2024
        WHERE "% Fibre" IS NOT NULL
        ORDER BY CAST(REPLACE(REPLACE("% Fibre", '%', ''), ',', '.') AS FLOAT) DESC
        LIMIT 5;
    """)
    top_communes = cur.fetchall()
    for commune in top_communes:
        print(f"{commune[0]:<30} : {commune[1]} (Code INSEE: {commune[2]})")

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