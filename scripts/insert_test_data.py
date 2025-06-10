import psycopg2
import json
from psycopg2.extras import RealDictCursor
from datetime import date

# Paramètres de connexion
params = {
    'host': 'ep-wispy-queen-abzi1lne-pooler.eu-west-2.aws.neon.tech',
    'database': 'neondb',
    'user': 'neondb_owner',
    'password': 'npg_XsA4wfvHy2Rn',
    'sslmode': 'require'
}

def insert_test_data():
    try:
        # Connexion à la base de données
        print("Tentative de connexion à la base de données...")
        conn = psycopg2.connect(**params)
        print("Connexion établie avec succès!")
        
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
        
        # Création d'une entrée de test
        test_data = {
            "nom_fichier": "donnees_test",
            "nom_base": "INSEE",
            "schema": "Economie",
            "description": "Jeu de données de test pour vérifier le fonctionnement du système de métadonnées",
            "date_creation": date(2023, 1, 1),
            "date_maj": date(2023, 6, 15),
            "source": "Test automatique",
            "frequence_maj": "Annuelle",
            "licence": "Licence Ouverte",
            "envoi_par": "Script de test",
            "contact": "admin@example.com",
            "mots_cles": "test, données, exemple",
            "notes": "Ces données sont générées par un script de test",
            "contenu_csv": json.dumps(test_csv_data),
            "dictionnaire": json.dumps(test_dict_data)
        }
        
        with conn.cursor() as cur:
            # Insertion des données de test
            print("Insertion des données de test...")
            
            # Préparation de la requête SQL
            columns = ", ".join(test_data.keys())
            placeholders = ", ".join(["%s"] * len(test_data))
            
            query = f"INSERT INTO metadata ({columns}) VALUES ({placeholders})"
            
            # Exécution de la requête
            cur.execute(query, list(test_data.values()))
            conn.commit()
            print("Données de test insérées avec succès!")
            
            # Vérification de l'insertion
            cur.execute("SELECT * FROM metadata WHERE nom_fichier = %s", ("donnees_test",))
            result = cur.fetchone()
            
            if result:
                print("Vérification réussie: les données ont été insérées correctement.")
            else:
                print("ERREUR: Les données n'ont pas été trouvées après l'insertion.")
        
        # Fermeture de la connexion
        conn.close()
        print("\nConnexion fermée.")
        
    except Exception as e:
        print(f"Erreur: {type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    insert_test_data() 