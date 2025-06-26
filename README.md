# Application de Gestion des Métadonnées

Application Streamlit pour la saisie et le suivi des métadonnées des jeux de données.

## Setup et Installation

### Prérequis
- Python 3.x
- PostgreSQL (accès à la base Neon.tech)

### Installation

1. **Utiliser l'environnement virtuel centralisé** (à la racine de DOCS) :
```powershell
# Depuis le répertoire DOCS
.\.venv\Scripts\Activate.ps1
```

2. **Vérifier les dépendances** (déjà installées dans l'environnement central) :
```powershell
pip list | findstr -i "streamlit"
```

3. **Lancer l'application** :
```powershell
cd metadata_app_clean
streamlit run Catalogue.py
```

## Structure du Projet

```
metadata_app_clean/
├── Catalogue.py           # Page d'accueil
├── pages/
│   ├── 01_Saisie.py      # Formulaire de saisie
│   └── 02_Suivi_MaJ.py   # Suivi des mises à jour
├── utils/
│   ├── auth.py           # Authentification
│   └── db_utils.py       # Utilitaires base de données
├── scripts/              # Scripts de maintenance
└── config.yaml          # Configuration

```

## Notes importantes

- **Environnement virtuel** : Utilise l'environnement centralisé `../..venv/`
- **Base de données** : PostgreSQL sur Neon.tech
- **Authentification** : Via streamlit-authenticator
- **Génération SQL** : Script d'import automatique depuis les métadonnées

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

## Scripts utiles

- `check_db.py` : Teste la connexion et la structure de la base
- `