#!/usr/bin/env python3
"""
Script pour tester la connexion au serveur PostgreSQL local
"""

import psycopg2
import sys

def test_local_connection():
    """Tester la connexion au serveur PostgreSQL local"""
    
    try:
        # Configuration locale selon la documentation
        conn = psycopg2.connect(
            host="localhost",
            port="5432",
            database="opendata",
            user="cursor_ai",
            password="cursor_ai_is_quite_awesome"
        )
        
        print("✅ Connexion au serveur PostgreSQL local réussie !")
        
        cursor = conn.cursor()
        
        # Vérifier les schémas disponibles
        print("\n📋 Schémas disponibles :")
        cursor.execute("""
            SELECT schema_name, 
                   has_schema_privilege('cursor_ai', schema_name, 'USAGE') as has_usage
            FROM information_schema.schemata 
            WHERE schema_name NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
            ORDER BY schema_name;
        """)
        
        schemas = cursor.fetchall()
        for schema_name, has_usage in schemas:
            status = "✅" if has_usage else "❌"
            print(f"   {status} {schema_name}")
        
        # Lister quelques tables par schéma
        print("\n🗂️ Tables par schéma (exemple) :")
        for schema_name, has_usage in schemas:
            if has_usage:  # Seulement si on a accès
                cursor.execute("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = %s 
                    AND table_type = 'BASE TABLE'
                    LIMIT 5;
                """, (schema_name,))
                
                tables = cursor.fetchall()
                if tables:
                    print(f"\n   📁 Schéma '{schema_name}' :")
                    for (table_name,) in tables:
                        print(f"      - {table_name}")
        
        # Tester une requête simple
        print("\n🧪 Test d'une requête simple :")
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        print(f"   Version PostgreSQL : {version}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except psycopg2.Error as e:
        print(f"❌ Erreur de connexion PostgreSQL : {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue : {e}")
        return False

def list_available_sql_files():
    """Lister les scripts SQL disponibles pour import"""
    import os
    
    print("\n📜 Scripts SQL disponibles pour import :")
    
    # Chercher dans le répertoire SGBD
    sgbd_path = "../SGBD"
    if os.path.exists(sgbd_path):
        for root, dirs, files in os.walk(sgbd_path):
            for file in files:
                if file.endswith('.sql'):
                    rel_path = os.path.relpath(os.path.join(root, file), sgbd_path)
                    print(f"   📄 {rel_path}")

if __name__ == "__main__":
    print("🔌 Test de connexion au serveur PostgreSQL local")
    print("=" * 60)
    
    if test_local_connection():
        print("\n" + "=" * 60)
        list_available_sql_files()
        print("\n💡 Connexion réussie ! Vous pouvez maintenant exécuter des scripts COPY.")
    else:
        print("\n❌ Impossible de se connecter. Vérifiez que PostgreSQL est démarré.")
        sys.exit(1) 