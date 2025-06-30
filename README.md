# Catalogue des Métadonnées

Application Streamlit pour la saisie, consultation et suivi des métadonnées des jeux de données territoriales.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32.0-red?logo=streamlit)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue?logo=postgresql)

## Table des matières

- [Aperçu du projet](#aperçu-du-projet)
- [Fonctionnalités](#fonctionnalités)
- [Démarrage rapide](#démarrage-rapide)
- [Utilisation](#utilisation)
- [Développement](#développement)
- [Structure du projet](#structure-du-projet)
- [Déploiement](#déploiement)
- [Maintenance](#maintenance)

## Aperçu du projet

### Contexte
Cette application répond aux besoins de gestion et de catalogage des métadonnées pour les collectivités territoriales. Elle permet de centraliser, documenter et suivre les jeux de données utilisés dans le cadre de politiques publiques basées sur la donnée.

### Technologies utilisées
- **Python 3.11+** - Langage principal
- **Streamlit 1.32.0** - Interface utilisateur web
- **PostgreSQL 15** - Base de données (Neon.tech)
- **Plotly 5.18.0** - Visualisations interactives
- **streamlit-authenticator** - Système d'authentification

### Indicateurs couverts
- Métadonnées de jeux de données INSEE, ministériels et territoriaux
- Suivi temporel des mises à jour
- Dictionnaires de variables automatisés
- Génération de scripts SQL d'import

## Fonctionnalités

✅ **Saisie et consultation** des métadonnées via interface Streamlit  
✅ **Support CSV** avec détection automatique du séparateur  
✅ **Dictionnaire des variables** en format JSONB  
✅ **Recherche et filtrage** multicritères  
✅ **Suivi temporel** des mises à jour  
✅ **Génération automatique** de scripts SQL d'import  
✅ **Authentification** sécurisée  
✅ **Visualisations interactives** avec Plotly  

## Démarrage rapide

### Prérequis
- Python 3.11+
- Accès à une base PostgreSQL
- Variables d'environnement configurées

### Installation locale

1. **Utiliser l'environnement virtuel centralisé** :
```powershell
# Depuis le répertoire DOCS
.\.venv\Scripts\Activate.ps1
```

2. **Vérifier les dépendances** :
```powershell
pip list | findstr -i "streamlit"
```

3. **Configurer les variables d'environnement** (fichier `.env`) :
```env
NEON_HOST=ep-wispy-queen-abzi1lne-pooler.eu-west-2.aws.neon.tech
NEON_DATABASE=neondb
NEON_USER=neondb_owner
NEON_PASSWORD=npg_XsA4wfvHy2Rn
```

4. **Lancer l'application** :
```powershell
cd metadata_app_clean
streamlit run Catalogue.py
```

L'application sera accessible sur : http://localhost:8501

## Utilisation

### Interface principale (Catalogue.py)
- **Recherche** : Saisir un terme pour filtrer les métadonnées
- **Filtres** : Par schéma (économie, population, etc.) et producteur
- **Consultation** : Aperçu des données et dictionnaire des variables

### Page de saisie (01_Saisie.py)
- Formulaire complet de métadonnées
- Import d'extraits CSV (50 premières lignes recommandées)
- Génération automatique de scripts SQL

### Page de suivi (02_Suivi_MaJ.py)
- Tableau de bord des mises à jour
- Timeline de couverture temporelle
- Statuts : À jour, En retard, À mettre à jour

## Développement

### Environnement de développement
```powershell
# Activation de l'environnement centralisé
.\.venv\Scripts\Activate.ps1

# Lancement en mode développement
streamlit run Catalogue.py --server.runOnSave=true
```

### Structure de la base de données
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
    date_publication DATE,
    date_prochaine_publication DATE,
    source VARCHAR(255),
    frequence_maj VARCHAR(255),
    licence VARCHAR(255),
    envoi_par VARCHAR(255),
    contenu_csv JSONB,
    dictionnaire JSONB,
    granularite_geo VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Scripts utiles
- `scripts/check_db.py` : Test de connexion à la base
- `scripts/test_auth.py` : Vérification de l'authentification
- `utils/sql_generator.py` : Génération de scripts SQL

## Structure du projet

```
metadata_app_clean/
├── Catalogue.py              # 🏠 Page principale - Consultation des métadonnées
├── requirements.txt          # 📦 Dépendances Python
├── config.yaml              # ⚙️ Configuration authenticator
├── .streamlit/
│   ├── config.toml          # 🔧 Configuration Streamlit
│   └── secrets.toml         # 🔐 Secrets (local uniquement)
├── pages/
│   ├── 01_Saisie.py         # ✏️ Formulaire de saisie des métadonnées
│   └── 02_Suivi_MaJ.py      # 📊 Suivi des mises à jour et timeline
├── utils/
│   ├── auth.py              # 🔐 Gestion de l'authentification
│   ├── db_utils.py          # 🗄️ Utilitaires base de données
│   └── sql_generator.py     # 🛠️ Génération automatique de scripts SQL
└── scripts/                 # 🔧 Scripts de maintenance et tests
    ├── check_db.py
    ├── test_auth.py
    └── test_db_connection.py
```

## Déploiement

### Déploiement local
Voir section [Démarrage rapide](#démarrage-rapide)

### Déploiement sur Streamlit Cloud

#### 1. Prérequis
- Repository GitHub connecté
- Fichier `requirements.txt` présent :
```
streamlit==1.32.0
streamlit-authenticator==0.3.2
pandas==2.2.0
plotly==5.18.0
psycopg2-binary==2.9.9
python-dotenv==1.0.1
PyYAML==6.0.1
```

#### 2. Configuration Streamlit Cloud
1. Connecter le repository GitHub à Streamlit Cloud
2. Sélectionner `Catalogue.py` comme point d'entrée
3. Configurer les secrets dans l'interface Streamlit Cloud :
```toml
# Configuration de la base de données Neon.tech
NEON_HOST = "ep-wispy-queen-abzi1lne-pooler.eu-west-2.aws.neon.tech"
NEON_DATABASE = "neondb"
NEON_USER = "neondb_owner"
NEON_PASSWORD = "npg_XsA4wfvHy2Rn"

# Clé API pour neon.tech
NEON_API_KEY = "napi_40g81dc3l11a08wos2rt63q2im3qnz9cnykro6wc3mohivxf3jtzz0o4wfbbnnqu"
NEON_API_URL = "https://console.neon.tech/api/v2/"
```

#### 3. Vérifications post-déploiement
- [ ] L'authentification fonctionne
- [ ] La connexion à la base de données est active
- [ ] Les graphiques s'affichent correctement
- [ ] Toutes les pages sont accessibles

#### 4. Problèmes résolus
- ✅ **ModuleNotFoundError** : Résolu avec `requirements.txt` complet
- ✅ **Configuration Streamlit** : Ajout de `.streamlit/config.toml`
- ✅ **Imports relatifs** : Structure de modules optimisée

## Maintenance

### Mise à jour des données
```powershell
# Sauvegarder la base avant mise à jour
pg_dump -h $NEON_HOST -U $NEON_USER -d $NEON_DATABASE > backup.sql

# Mettre à jour via l'interface de saisie
streamlit run Catalogue.py
```

### Problèmes connus
- **Performance** : Grandes tables CSV (>1000 lignes) peuvent ralentir l'interface
  - **Solution** : Limiter à 50 lignes dans l'extrait CSV
- **Encodage** : Caractères spéciaux dans les CSV
  - **Solution** : Utiliser UTF-8 pour tous les fichiers

### Support
- **Documentation** : README.md (ce fichier)
- **Base de données** : Configuration Neon.tech
- **Authentification** : config.yaml

### Changelog

#### Version actuelle
- ✅ Interface multipage complète
- ✅ Authentification sécurisée
- ✅ Génération automatique de SQL
- ✅ Visualisations interactives
- ✅ Déploiement Streamlit Cloud opérationnel

---

© 2025 - Système de Gestion des Métadonnées v1.0