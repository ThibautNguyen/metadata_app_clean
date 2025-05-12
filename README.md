# Metadata App

Application de gestion des métadonnées pour bases de données PostgreSQL.

## Fonctionnalités principales

- Saisie et consultation des métadonnées via une interface Streamlit
- Support pour le contenu CSV et dictionnaire des variables (JSONB)
- Filtrage, recherche et affichage détaillé des métadonnées
- Validation des données
- Affichage des données CSV
- Flexibilité dans les séparateurs (virgule ou point-virgule)
- Outil d'inspection de la base de données

## Configuration de la base de données

- **Host** : ep-wispy-queen-abzi1lne-pooler.eu-west-2.aws.neon.tech
- **Database** : neondb
- **User** : neondb_owner
- **Password** : (voir variables d'environnement)
- **SSL Mode** : require

### Variables d'environnement recommandées

À placer dans un fichier `.env` ou dans la configuration Streamlit Cloud :
```
NEON_USER=neondb_owner
NEON_PASSWORD=npg_XsA4wfvHy2Rn
NEON_HOST=ep-wispy-queen-abzi1lne-pooler.eu-west-2.aws.neon.tech
NEON_DATABASE=neondb
```

## Structure de la table `metadata`

```sql
CREATE TABLE metadata (
    id SERIAL PRIMARY KEY,
    nom_table VARCHAR(255),
    nom_base VARCHAR(255) NOT NULL,
    producteur VARCHAR(255),
    schema VARCHAR(255),
    description TEXT,
    millesime DATE,
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
    granularite_geo VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Exécution locale

```bash
# 1. Créer/activer l'environnement virtuel
python -m venv .venv
# Sous Windows PowerShell
.\.venv\Scripts\Activate.ps1
# ou utiliser .venv_new si déjà présent

# 2. Installer les dépendances
pip install -r requirements.txt

# 3. Lancer l'application
streamlit run Catalogue.py
```

## Déploiement sur Streamlit Cloud

1. Connectez-vous à [Streamlit Cloud](https://streamlit.io/cloud)
2. Créez une nouvelle application pointant vers ce dépôt
3. Utilisez la branche `main`
4. Spécifiez `Catalogue.py` comme fichier principal
5. Configurez les variables d'environnement (voir plus haut)

## Scripts utiles

- `check_db.py` : Teste la connexion et la structure de la base
- `db_utils.py` : Fonctions d'accès à la base de données
- `test_db_connection.py` : Test de connexion basique
- `pages/01_Saisie.py` : Interface de saisie des métadonnées
- `pages/03_Database_Inspector.py` : Inspection de la base

## Problèmes connus

- Les données saisies dans le formulaire n'apparaissent pas toujours dans le catalogue (vérifier la fonction `save_metadata`)
- Vérifier la transaction SQL et le commit
- Ajouter plus de messages d'erreur explicites et un système de logging détaillé

## À faire / TODO

- Déboguer la fonction `save_metadata`
- Améliorer la gestion des erreurs
- Vérifier la structure de la base et les contraintes

## Structure du projet

- `Catalogue.py` : Point d'entrée principal
- `db_utils.py` : Accès base de données
- `pages/` : Pages Streamlit additionnelles
- `data/` : Fichiers de données statiques
- `scripts/` : Scripts d'import/export
- `README.md` : Documentation principale

## Liens utiles

- Dépôt GitHub : https://github.com/ThibautNguyen/DOCS

---

**Remarque** :  
- Supprime le fichier `README-Thibaut.md` après fusion pour éviter toute confusion.
- Mets à jour ce README à chaque évolution majeure du projet ou de la structure de la base. 