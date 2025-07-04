#!/usr/bin/env python3
"""
Script pour exécuter l'import de la table sirene_geo_2025_T2
"""

import psycopg2
import psycopg2.extras
import csv
import time
import os

def execute_sirene_import():
    """Exécuter l'import de la table sirene_geo_2025_T2"""
    
    csv_file = r'C:\Users\thiba\OneDrive\Documents\Data\economie\geo-Sirene\StockEtablissement\2025-06\GeolocalisationEtablissement_Sirene_pour_etudes_statistiques_utf8.csv'
    
    try:
        # Vérifier l'existence du fichier
        if not os.path.exists(csv_file):
            print(f"❌ Fichier non trouvé: {csv_file}")
            return False
            
        # Configuration locale
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            database="opendata",
            user="cursor_ai",
            password="cursor_ai_is_quite_awesome"
        )
        
        print("✅ Connexion établie")
        cursor = conn.cursor()
        
        # Vérifier si la table existe et qui en est propriétaire
        cursor.execute("""
            SELECT schemaname, tablename, tableowner 
            FROM pg_tables 
            WHERE schemaname = 'economie' 
            AND tablename = 'sirene_geo_2025_t2';
        """)
        existing_table = cursor.fetchone()
        
        table_name = "sirene_geo_2025_t2"
        
        if existing_table:
            print(f"⚠️  Table existante trouvée, propriétaire: {existing_table[2]}")
            # Utiliser un nom différent si on n'est pas propriétaire
            table_name = "sirene_geo_2025_t2_new"
            print(f"📝 Utilisation du nom: {table_name}")
        
        # Étape 1: Suppression de la table si elle existe ET si on en est propriétaire
        print(f"\n🗑️  Étape 1: Suppression de la table {table_name} si elle existe...")
        cursor.execute(f"DROP TABLE IF EXISTS economie.{table_name};")
        conn.commit()
        print("✅ Table supprimée ou n'existait pas")
        
        # Étape 2: Création de la table
        print(f"\n🏗️  Étape 2: Création de la nouvelle table {table_name}...")
        create_table_sql = f"""
        CREATE TABLE economie.{table_name} (
            siret TEXT,
            x TEXT,
            y TEXT,
            qualite_xy TEXT,
            epsg TEXT,
            plg_qp24 TEXT,
            plg_iris TEXT,
            plg_zus TEXT,
            plg_qp15 TEXT,
            plg_qva TEXT,
            plg_code_commune TEXT,
            distance_precision TEXT,
            qualite_qp24 TEXT,
            qualite_iris TEXT,
            qualite_zus TEXT,
            qualite_qp15 TEXT,
            qualite_qva TEXT,
            y_latitude TEXT,
            x_longitude TEXT
        );
        """
        cursor.execute(create_table_sql)
        conn.commit()
        print("✅ Table créée")
        
        # Étape 3: Import des données avec Python
        print("\n📥 Étape 3: Import des données via Python (cela peut prendre plusieurs minutes...)") 
        start_time = time.time()
        
        # Préparer la requête d'insertion
        insert_sql = f"""
        INSERT INTO economie.{table_name} (
            siret, x, y, qualite_xy, epsg, plg_qp24, plg_iris, plg_zus, 
            plg_qp15, plg_qva, plg_code_commune, distance_precision, 
            qualite_qp24, qualite_iris, qualite_zus, qualite_qp15, 
            qualite_qva, y_latitude, x_longitude
        ) VALUES %s
        """
        
        # Lire et insérer le fichier CSV par chunks
        chunk_size = 10000
        total_inserted = 0
        
        with open(csv_file, 'r', encoding='utf-8') as file:
            csv_reader = csv.reader(file, delimiter=';')
            
            # Ignorer l'en-tête
            header = next(csv_reader)
            print(f"📋 Colonnes du CSV: {len(header)} colonnes")
            
            chunk = []
            for row_num, row in enumerate(csv_reader, 1):
                # Normaliser la ligne à 19 colonnes (ajouter des valeurs vides si nécessaire)
                normalized_row = row + [''] * (19 - len(row)) if len(row) < 19 else row[:19]
                chunk.append(tuple(normalized_row))
                
                # Insérer par chunks
                if len(chunk) >= chunk_size:
                    psycopg2.extras.execute_values(
                        cursor, insert_sql, chunk, template=None, page_size=1000
                    )
                    total_inserted += len(chunk)
                    print(f"  📊 {total_inserted:,} lignes insérées...")
                    chunk = []
                    conn.commit()
                
                # Affichage de progression pour gros fichiers
                if row_num % 100000 == 0:
                    elapsed = time.time() - start_time
                    print(f"  ⏱️  Traité {row_num:,} lignes en {elapsed:.1f}s")
            
            # Insérer le dernier chunk
            if chunk:
                psycopg2.extras.execute_values(
                    cursor, insert_sql, chunk, template=None, page_size=1000
                )
                total_inserted += len(chunk)
                conn.commit()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Vérification du nombre de lignes importées
        cursor.execute(f"SELECT COUNT(*) FROM economie.{table_name};")
        count = cursor.fetchone()[0]
        
        print(f"✅ Import terminé !")
        print(f"⏱️  Durée: {duration:.2f} secondes")
        print(f"📊 Nombre de lignes importées: {count:,}")
        print(f"🗂️  Table créée: economie.{table_name}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Erreur PostgreSQL : {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue : {e}")
        return False

if __name__ == "__main__":
    print("🚀 Import de la table sirene_geo_2025_t2")
    print("=" * 60)
    
    if execute_sirene_import():
        print("\n✅ Import réussi !")
    else:
        print("\n❌ Échec de l'import") 