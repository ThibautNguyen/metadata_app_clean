# Catalogue des Métadonnées

Application Streamlit pour la saisie, consultation et suivi des métadonnées des jeux de données territoriales.

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32.0-red?logo=streamlit)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue?logo=postgresql)
![Sécurité](https://img.shields.io/badge/Sécurité-Renforcée-green?logo=shield)

## Table des matières

- [Aperçu du projet](#aperçu-du-projet)
- [Fonctionnalités](#fonctionnalités)
- [Démarrage rapide](#démarrage-rapide)
- [Sécurité](#sécurité)
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
- Variables d'environnement configurées (**voir section [Sécurité](#sécurité)**)

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

3. **⚠️ CONFIGURATION SÉCURISÉE OBLIGATOIRE** - Créer un fichier `.env` :
```env
# Variables d'environnement OBLIGATOIRES (à adapter à votre configuration)
NEON_HOST=your_neon_host
NEON_DATABASE=your_database_name
NEON_USER=your_username
NEON_PASSWORD=your_secure_password
```

4. **Lancer l'application** :
```powershell
cd metadata_app_clean
streamlit run Catalogue.py
```

L'application sera accessible sur : http://localhost:8501

## Sécurité

### 🚨 Alertes de Sécurité Critiques

> **⚠️ IMPORTANT** : Si vous avez cloné ce repository avant juin 2025, **changez immédiatement** vos identifiants de base de données car ils étaient exposés publiquement sur GitHub.

### Configuration sécurisée obligatoire

#### Variables d'environnement requises (OBLIGATOIRES)

L'application **refuse de démarrer** sans ces variables :

```bash
# Base de données (OBLIGATOIRE)
NEON_HOST=your_neon_host
NEON_DATABASE=your_database_name  
NEON_USER=your_username
NEON_PASSWORD=your_secure_password

# Optionnel : API Keys
NEON_API_KEY=your_api_key
NEON_API_URL=your_api_url
```

#### Configuration locale (.env)

Créez un fichier `.env` à la racine du projet :

```env
# Base de données Neon.tech - ADAPTEZ À VOTRE CONFIGURATION
NEON_HOST=your_neon_host
NEON_DATABASE=your_database_name
NEON_USER=your_username
NEON_PASSWORD=your_secure_password
```

**🔐 CRITIQUE** : Le fichier `.env` est automatiquement exclu de Git - **ne jamais le committer !**

#### Configuration Streamlit Cloud

Dans l'interface Streamlit Cloud, configurez ces secrets :

```toml
# À adapter à votre configuration
NEON_HOST = "your_neon_host"
NEON_DATABASE = "your_database_name"
NEON_USER = "your_username"
NEON_PASSWORD = "your_secure_password"
```

### Bonnes pratiques de sécurité

#### Mots de passe
- ✅ Utilisez des mots de passe forts (20+ caractères)
- ✅ Incluez majuscules, minuscules, chiffres, symboles
- ❌ Ne réutilisez jamais de mots de passe
- 🔄 Changez régulièrement les identifiants

#### Accès base de données
- ✅ Utilisez des comptes avec privilèges minimaux nécessaires
- ✅ SSL/TLS activé automatiquement (`sslmode=require`)
- 📊 Surveillez les connexions suspectes
- 🌐 Limitez les adresses IP autorisées quand possible

#### Code et développement
- ❌ **JAMAIS** d'identifiants hardcodés dans le code
- ✅ Toujours utiliser des variables d'environnement
- ✅ Vérifier `.gitignore` avant chaque commit
- 🔍 Scanner le code pour détecter les secrets

### Vérification de sécurité

#### Avant chaque commit
```bash
# Vérifier qu'aucun secret n'est présent
git diff --cached | grep -i "password\\|secret\\|key\\|token"

# Scanner les fichiers pour détecter les fuites
grep -r "napi_\\|npg_" . --exclude-dir=.git
```

#### Outils recommandés
- **git-secrets** : Prévention des commits de secrets
- **gitleaks** : Scanner pour détecter les fuites d'identifiants  
- **truffleHog** : Recherche de secrets dans l'historique Git

### 🚨 En cas de compromission

#### Actions immédiates
1. **Changer TOUS les mots de passe** exposés
2. **Révoquer les clés API** compromises  
3. **Auditer les logs** de la base de données
4. **Nettoyer l'historique Git** si nécessaire

#### Checklist de sécurité
- [ ] Variables d'environnement configurées
- [ ] Aucun identifiant hardcodé dans le code
- [ ] `.gitignore` à jour et respecté
- [ ] Secrets Streamlit Cloud configurés
- [ ] Mots de passe forts utilisés
- [ ] SSL/TLS activé pour la base de données
- [ ] Logs de sécurité surveillés

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
├── .env                     # 🔐 Variables d'environnement (local uniquement)
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
Voir section [Démarrage rapide](#démarrage-rapide) et **impérativement** la section [Sécurité](#sécurité).

### Déploiement sur Streamlit Cloud

#### 1. Prérequis
- Repository GitHub connecté
- **Variables de sécurité configurées** (voir section Sécurité)
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
3. **🔐 OBLIGATOIRE** : Configurer les secrets dans l'interface Streamlit Cloud :
```toml
# Configuration sécurisée - À adapter à votre configuration
NEON_HOST = "your_neon_host"
NEON_DATABASE = "your_database_name"
NEON_USER = "your_username"
NEON_PASSWORD = "your_secure_password"

# Optionnel : API Keys
NEON_API_KEY = "your_api_key"
NEON_API_URL = "your_api_url"
```

#### 3. Vérifications post-déploiement
- [ ] L'authentification fonctionne
- [ ] La connexion à la base de données est active
- [ ] Les graphiques s'affichent correctement
- [ ] Toutes les pages sont accessibles
- [ ] **Aucun identifiant visible** dans les logs

#### 4. Problèmes résolus
- ✅ **ModuleNotFoundError** : Résolu avec `requirements.txt` complet
- ✅ **Configuration Streamlit** : Ajout de `.streamlit/config.toml`
- ✅ **Imports relatifs** : Structure de modules optimisée
- ✅ **Sécurité** : Suppression des identifiants hardcodés
- ✅ **Secrets exposés** : Migration vers variables d'environnement

## Maintenance

### Mise à jour des données
```powershell
# 1. Sauvegarder la base avant mise à jour
pg_dump -h $NEON_HOST -U $NEON_USER -d $NEON_DATABASE > backup.sql

# 2. Mettre à jour via l'interface de saisie
streamlit run Catalogue.py
```

### Problèmes connus et solutions

#### Performance
- **Problème** : Grandes tables CSV (>1000 lignes) peuvent ralentir l'interface
- **Solution** : Limiter à 50 lignes dans l'extrait CSV pour optimiser la génération SQL

#### Encodage
- **Problème** : Caractères spéciaux dans les CSV
- **Solution** : Utiliser UTF-8 pour tous les fichiers

#### Sécurité (CRITIQUE)
- **Problème** : Identifiants exposés dans l'historique Git
- **Solution** : Changement obligatoire des identifiants + utilisation variables d'environnement

### Support et contact
- **Documentation** : README.md (ce fichier)
- **Sécurité** : En cas de problème de sécurité, **NE PAS** créer d'issue publique
- **Base de données** : Configuration Neon.tech
- **Authentification** : config.yaml

### Audit de sécurité

#### 🛡️ Statut : SÉCURISÉ ✅ (30 juin 2025)

**Vulnérabilités critiques corrigées :**
- ✅ Configuration d'authentification renforcée (identifiants forts)
- ✅ Branches compromises supprimées de GitHub
- ✅ Scripts d'exposition sécurisés
- ✅ Email administrateur mis à jour : `thibaut.nguyen@spallian.com`

**Outils de maintenance disponibles :**
- 🔐 `scripts/generate_secure_config.py` - Génération d'identifiants forts
- 🔍 `scripts/test_auth.py` - Test sécurisé de configuration  
- 🧹 `scripts/security_cleanup.py` - Nettoyage automatisé

> **Note :** En cas de besoin de nouveaux identifiants, utilisez `python scripts/generate_secure_config.py`

### Changelog

#### Version 1.1 (2025-06-30) - **SÉCURISATION MAJEURE**
- 🔐 **CRITIQUE** : Suppression complète des identifiants hardcodés
- 🛡️ Migration vers variables d'environnement obligatoires
- 📋 Fusion documentation sécurisée
- 🔍 Renforcement .gitignore contre fuites futures
- ⚠️ Guide de compromission et récupération
- 🧹 **AUDIT SÉCURITÉ** : Branches compromises nettoyées
- 🛠️ Scripts de maintenance de sécurité créés

#### Version 1.0
- ✅ Interface multipage complète
- ✅ Authentification sécurisée
- ✅ Génération automatique de SQL
- ✅ Visualisations interactives
- ✅ Déploiement Streamlit Cloud opérationnel

---

© 2025 - Système de Gestion des Métadonnées v1.1 - **Sécurisé**