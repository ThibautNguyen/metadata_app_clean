import psycopg2
from psycopg2.extras import RealDictCursor
import json
from datetime import datetime
import os

def test_database_insertion():
    """
    Script pour tester la structure de la table metadata et tenter d'insérer une entrée de test
    """
    try:
        # Connexion à la base de données
        print("Tentative de connexion à la base de données...")
        db_params = {
            "host": os.getenv("NEON_HOST", "ep-wispy-queen-abzi1lne-pooler.eu-west-2.aws.neon.tech"),
            "database": os.getenv("NEON_DATABASE", "neondb"),
            "user": os.getenv("NEON_USER", "neondb_owner"),
            "password": os.getenv("NEON_PASSWORD", "npg_XsA4wfvHy2Rn"),
            "sslmode": "require"
        }
        conn = psycopg2.connect(**db_params)
        print("Connexion réussie.")
        
        # Vérification de la structure de la table
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            print("\nVérification de la structure de la table metadata...")
            cur.execute("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'metadata' 
                ORDER BY ordinal_position;
            """)
            columns = cur.fetchall()
            print("\nStructure de la table metadata :")
            for col in columns:
                print(f"  - {col['column_name']} ({col['data_type']})")
            
            # Vérification du nombre de lignes actuelles
            cur.execute("SELECT COUNT(*) as count FROM metadata;")
            count = cur.fetchone()['count']
            print(f"\nNombre actuel de lignes dans la table : {count}")
            
            # Création d'une entrée de test
            print("\nCréation d'une entrée de test...")
            
            # Données CSV de test
            test_csv_data = {
                "header": ["COD_VAR", "LIB_VAR", "LIB_VAR_LONG", "COD_MOD", "LIB_MOD", "TYPE_VAR", "LONG_VAR"],
                "data": [
                    ["TEST1", "Test Variable 1", "Variable de test 1", "1", "Mode 1", "NUM", "10"],
                    ["TEST2", "Test Variable 2", "Variable de test 2", "2", "Mode 2", "CHAR", "20"]
                ],
                "separator": ";"
            }
            
            # Dictionnaire de test
            test_dict_data = {
                "header": ["COD_VAR", "LIB_VAR", "LIB_VAR_LONG", "COD_MOD", "LIB_MOD", "TYPE_VAR", "LONG_VAR"],
                "data": [
                    ["TEST1", "Test Variable 1", "Variable de test 1", "1", "Mode 1", "NUM", "10"],
                    ["TEST2", "Test Variable 2", "Variable de test 2", "2", "Mode 2", "CHAR", "20"]
                ],
                "separator": ";"
            }
            
            # Tentative d'insertion
            print("\nTentative d'insertion d'une ligne de test...")
            try:
                cur.execute("""
                    INSERT INTO metadata (
                        nom_fichier, nom_base, schema, description,
                        date_creation, date_maj, source, frequence_maj,
                        licence, envoi_par, contact, mots_cles, notes,
                        contenu_csv, dictionnaire
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                """, (
                    "test_fichier.csv",                   # nom_fichier
                    "INSEE",                              # nom_base
                    "Economie",                           # schema
                    "Fichier de test pour vérifier l'insertion",  # description
                    datetime.now().date(),                # date_creation
                    datetime.now().date(),                # date_maj
                    "Test",                               # source
                    "Ponctuelle",                         # frequence_maj
                    "Licence Ouverte",                    # licence
                    "Script de test",                     # envoi_par
                    "test@example.com",                   # contact
                    "test, vérification, insertion",      # mots_cles
                    "Notes de test",                      # notes
                    json.dumps(test_csv_data),            # contenu_csv
                    json.dumps(test_dict_data)            # dictionnaire
                ))
                
                conn.commit()
                print("Insertion réussie !")
                
                # Vérification de l'insertion
                cur.execute("SELECT * FROM metadata WHERE nom_fichier = 'test_fichier.csv'")
                inserted_row = cur.fetchone()
                if inserted_row:
                    print(f"\nLigne insérée avec succès - ID: {inserted_row['id']}")
                else:
                    print("\nAucune ligne trouvée après l'insertion, ce qui est étrange.")
                
            except Exception as e:
                print(f"Erreur lors de l'insertion : {str(e)}")
                conn.rollback()
        
        # Fermeture de la connexion
        conn.close()
        print("\nConnexion fermée.")
        
    except Exception as e:
        print(f"Erreur : {str(e)}")

if __name__ == "__main__":
    test_database_insertion() 