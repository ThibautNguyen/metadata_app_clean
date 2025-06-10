import psycopg2
import json
from psycopg2.extras import RealDictCursor

# Paramètres de connexion
params = {
    'host': 'ep-wispy-queen-abzi1lne-pooler.eu-west-2.aws.neon.tech',
    'database': 'neondb',
    'user': 'neondb_owner',
    'password': 'npg_XsA4wfvHy2Rn',
    'sslmode': 'require'
}

def fix_db_structure():
    try:
        # Connexion à la base de données
        print("Tentative de connexion à la base de données...")
        conn = psycopg2.connect(**params)
        print("Connexion établie avec succès!")
        
        # Récupération des données existantes
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            # Vérification de l'existence de la table
            cur.execute("""
                SELECT EXISTS (
                    SELECT FROM information_schema.tables 
                    WHERE table_name = 'metadata'
                );
            """)
            table_exists = cur.fetchone()['exists']
            
            if table_exists:
                print("Table metadata trouvée, vérification des colonnes...")
                
                # Vérification des colonnes actuelles
                cur.execute("""
                    SELECT column_name
                    FROM information_schema.columns 
                    WHERE table_name = 'metadata';
                """)
                columns = [col['column_name'] for col in cur.fetchall()]
                print(f"Colonnes actuelles: {columns}")
                
                # Vérifier si les colonnes contenu_csv et dictionnaire existent
                if 'contenu_csv' not in columns:
                    print("La colonne 'contenu_csv' est manquante, ajout en cours...")
                    cur.execute("ALTER TABLE metadata ADD COLUMN contenu_csv JSONB;")
                    conn.commit()
                    print("Colonne 'contenu_csv' ajoutée avec succès.")
                
                if 'dictionnaire' not in columns:
                    print("La colonne 'dictionnaire' est manquante, ajout en cours...")
                    cur.execute("ALTER TABLE metadata ADD COLUMN dictionnaire JSONB;")
                    conn.commit()
                    print("Colonne 'dictionnaire' ajoutée avec succès.")
                
                if 'contact' not in columns:
                    print("La colonne 'contact' est manquante, ajout en cours...")
                    cur.execute("ALTER TABLE metadata ADD COLUMN contact VARCHAR(255);")
                    conn.commit()
                    print("Colonne 'contact' ajoutée avec succès.")
                
                # Vérification finale
                cur.execute("""
                    SELECT column_name, data_type
                    FROM information_schema.columns 
                    WHERE table_name = 'metadata' 
                    ORDER BY ordinal_position;
                """)
                final_columns = cur.fetchall()
                print("\nStructure finale de la table metadata:")
                for col in final_columns:
                    print(f"  {col['column_name']} ({col['data_type']})")
            else:
                print("La table metadata n'existe pas, création en cours...")
                cur.execute("""
                    CREATE TABLE metadata (
                        id SERIAL PRIMARY KEY,
                        nom_fichier VARCHAR(255) NOT NULL,
                        nom_base VARCHAR(255),
                        schema VARCHAR(255),
                        description TEXT,
                        date_creation DATE,
                        date_maj DATE,
                        source VARCHAR(255),
                        frequence_maj VARCHAR(255),
                        licence VARCHAR(255),
                        envoi_par VARCHAR(255),
                        contact VARCHAR(255),
                        mots_cles TEXT,
                        notes TEXT,
                        contenu_csv JSONB,
                        dictionnaire JSONB,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()
                print("Table metadata créée avec succès.")
        
        # Fermeture de la connexion
        conn.close()
        print("\nConnexion fermée.")
        print("Structure de la base de données corrigée avec succès.")
        
    except Exception as e:
        print(f"Erreur: {type(e).__name__}: {str(e)}")

if __name__ == "__main__":
    fix_db_structure() 