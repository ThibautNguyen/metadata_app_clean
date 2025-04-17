# Guide de Connexion aux Bases de Données PostgreSQL

## Configurations de Connexion

### 1. Base de Données Locale (localhost)
```python
# Configuration locale
conn = psycopg2.connect(
    host="localhost",
    port="5432",
    database="opendata",
    user="cursor_ai",
    password="cursor_ai_is_quite_awesome"
)
```

### 2. Base de Données Neon.tech (Cloud)
```python
# Configuration Neon.tech
conn = psycopg2.connect(
    host="ep-wispy-queen-abzi1lne-pooler.eu-west-2.aws.neon.tech",
    port="5432",
    database="neondb",
    user="neondb_owner",
    password="npg_XsA4wfvHy2Rn"
)
```

### 3. Bonnes Pratiques pour la Gestion des Configurations
- Utiliser des variables d'environnement pour les informations sensibles
- Créer un fichier `.env` pour stocker les configurations :
```env
# Configuration Locale
LOCAL_DB_HOST=localhost
LOCAL_DB_PORT=5432
LOCAL_DB_NAME=opendata
LOCAL_DB_USER=cursor_ai
LOCAL_DB_PASSWORD=cursor_ai_is_quite_awesome

# Configuration Neon.tech
NEON_HOST=ep-wispy-queen-abzi1lne-pooler.eu-west-2.aws.neon.tech
NEON_PORT=5432
NEON_DATABASE=neondb
NEON_USER=neondb_owner
NEON_PASSWORD=npg_XsA4wfvHy2Rn
```

- Exemple d'utilisation avec python-dotenv :
```python
from dotenv import load_dotenv
import os

load_dotenv()

def get_db_connection(env="local"):
    if env == "local":
        return psycopg2.connect(
            host=os.getenv("LOCAL_DB_HOST"),
            port=os.getenv("LOCAL_DB_PORT"),
            database=os.getenv("LOCAL_DB_NAME"),
            user=os.getenv("LOCAL_DB_USER"),
            password=os.getenv("LOCAL_DB_PASSWORD")
        )
    elif env == "neon":
        return psycopg2.connect(
            host=os.getenv("NEON_HOST"),
            port=os.getenv("NEON_PORT"),
            database=os.getenv("NEON_DATABASE"),
            user=os.getenv("NEON_USER"),
            password=os.getenv("NEON_PASSWORD")
        )
    else:
        raise ValueError("Configuration de base de données non reconnue")
```

## Analyse des Erreurs Rencontrées

### 1. Erreur Initiale : Accès au Schéma (Base Locale)
- **Problème** : Tentative d'accès direct à la table `tableau_technologies_internet` sans spécifier le schéma.
- **Symptôme** : Erreur "relation does not exist".
- **Solution** : Utiliser la notation complète `reseau.tableau_technologies_internet`.
- **Leçon** : Toujours vérifier le schéma des tables et utiliser la notation `schema.table`.

### 2. Erreur de Droits d'Accès (Base Locale)
- **Problème** : Droits insuffisants sur le schéma 'reseau'.
- **Symptôme** : Permission denied sur le schéma.
- **Solution** : 
  1. Vérifier les droits avec `\dn` dans psql
  2. Obtenir le droit USAGE sur le schéma
  3. Obtenir les droits SELECT sur les tables spécifiques

### 3. Erreur de Normalisation (Base Locale)
- **Problème** : Tentative d'utilisation de la fonction `unaccent` non disponible.
- **Symptôme** : "function unaccent(text) does not exist".
- **Solution** : Revenir à une recherche case-insensitive simple avec `LOWER()`.
- **Leçon** : Vérifier la disponibilité des extensions avant de les utiliser.

## Différences Clés entre Environnements

### Base Locale (localhost)
- Accès direct via localhost
- Configuration des droits via psql en local
- Performance dépendante de la machine locale
- Idéal pour le développement et les tests

### Base Cloud (Neon.tech)
- Connexion via URL sécurisée
- Gestion des droits via l'interface web Neon
- Performance dépendante de la connexion internet
- Adapté pour la production et le partage
- Nécessite une gestion plus stricte des ressources (timeouts, pooling)

## Points de Vigilance Spécifiques au Cloud

1. **Gestion des Connexions**
   - Implémenter un mécanisme de retry en cas de perte de connexion
   - Utiliser un connection pooling pour optimiser les performances
   - Gérer les timeouts de manière appropriée

2. **Sécurité**
   - Ne JAMAIS commiter les credentials dans le code
   - Utiliser des variables d'environnement ou des secrets managers
   - Restreindre les accès IP si possible

3. **Performance**
   - Optimiser les requêtes pour minimiser la latence
   - Mettre en cache les données fréquemment utilisées
   - Monitorer l'utilisation des ressources

## Process Correct de Connexion

### 1. Configuration de la Connexion
```python
conn = psycopg2.connect(
    host="localhost",
    port="5432",
    database="opendata",
    user="cursor_ai",
    password="cursor_ai_is_quite_awesome"
)
```

### 2. Vérification des Droits
```sql
-- Vérifier les schémas accessibles
SELECT schema_name, has_schema_privilege('cursor_ai', schema_name, 'USAGE') as has_usage
FROM information_schema.schemata;

-- Vérifier les droits sur les tables
SELECT table_schema, table_name, has_table_privilege('cursor_ai', table_schema || '.' || table_name, 'SELECT')
FROM information_schema.tables
WHERE table_schema = 'reseau';
```

### 3. Bonnes Pratiques
1. **Toujours utiliser des noms complets** : `schema.table`
2. **Gérer proprement les connexions** :
   ```python
   try:
       # Code d'accès à la BD
   finally:
       cur.close()
       conn.close()
   ```
3. **Vérifier les données avant traitement** :
   ```python
   cur.execute("SELECT COUNT(*) FROM reseau.tableau_technologies_internet")
   count = cur.fetchone()[0]
   print(f"Nombre total d'enregistrements : {count}")
   ```

## Points de Vigilance pour le Futur

1. **Schémas et Tables**
   - Toujours vérifier l'existence et l'accessibilité des schémas
   - Utiliser la notation complète `schema.table`
   - Documenter la structure des tables utilisées

2. **Gestion des Droits**
   - Vérifier les droits USAGE sur les schémas
   - Vérifier les droits SELECT sur les tables
   - Demander les droits manquants si nécessaire

3. **Traitement des Données**
   - Valider le format des données avant traitement
   - Gérer les valeurs NULL et les cas particuliers
   - Utiliser des requêtes paramétrées pour éviter les injections SQL

4. **Performance et Stabilité**
   - Limiter la taille des résultats si nécessaire
   - Fermer proprement les connexions
   - Gérer les timeouts et les reconnexions

## Commandes Utiles pour le Diagnostic

```sql
-- Vérifier les schémas disponibles
\dn

-- Lister les tables d'un schéma
\dt reseau.*

-- Vérifier la structure d'une table
\d reseau.tableau_technologies_internet

-- Vérifier les droits
\dp reseau.tableau_technologies_internet
```

## Note Importante sur les Noms de Tables

### Évolution du Nom de la Table
- **Nom initial** (issu de l'import CSV) : `tableau_technologies_internet`
- **Nom actuel** (après renommage) : `techno_internet_com_2024`

La table a été renommée pour plus de clarté et de cohérence. Pour l'utiliser, il faut maintenant :
```sql
-- Syntaxe correcte (avec le schéma)
SELECT * FROM reseau.techno_internet_com_2024;
```

### Points Importants
1. Le schéma `reseau` doit toujours être spécifié
2. L'ancien nom `tableau_technologies_internet` n'est plus valide
3. DBeaver et la base de données affichent maintenant le même nom

## Problèmes Courants et Solutions

### 1. Commande `psql` non reconnue dans PowerShell
- **Problème** : La commande `psql` n'est pas reconnue dans PowerShell même si PostgreSQL est installé.
- **Message d'erreur** : 
  ```
  Le terme «psql» n'est pas reconnu comme nom d'applet de commande, fonction, fichier de script ou programme exécutable.
  ```
- **Solution validée** : 
  Utiliser Python avec psycopg2 comme alternative à psql. Cette approche a été testée et fonctionne correctement.

### 2. Alternative Python (Solution validée)
Pour remplacer les commandes psql courantes, voici les équivalents en Python :

```python
import psycopg2

# Connexion à la base
conn = psycopg2.connect(
    host="localhost",
    port="5432",
    database="opendata",
    user="cursor_ai",
    password="cursor_ai_is_quite_awesome"
)
cur = conn.cursor()

# Équivalent de \dt schema.*
def list_tables(schema):
    cur.execute("""
        SELECT table_name, table_type
        FROM information_schema.tables 
        WHERE table_schema = %s
        ORDER BY table_name;
    """, (schema,))
    return cur.fetchall()

# Équivalent de \d table
def describe_table(schema, table):
    cur.execute("""
        SELECT 
            column_name,
            data_type,
            character_maximum_length,
            is_nullable
        FROM information_schema.columns
        WHERE table_schema = %s 
        AND table_name = %s
        ORDER BY ordinal_position;
    """, (schema, table))
    return cur.fetchall()

try:
    # Exemple d'utilisation
    tables = list_tables('reseau')
    for table in tables:
        print(f"- {table[0]} (Type: {table[1]}")

finally:
    cur.close()
    conn.close()
```

### Note sur les Alternatives Non Testées
D'autres solutions comme l'ajout au PATH ou l'utilisation du chemin complet vers psql.exe pourraient fonctionner mais n'ont pas été validées dans notre environnement. Il est préférable d'utiliser la solution Python qui a été testée et confirmée fonctionnelle. 