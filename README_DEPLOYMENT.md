# Guide de déploiement Streamlit Cloud

## Problèmes résolus

### 1. ModuleNotFoundError
- ✅ **Résolu** : Ajout du fichier `requirements.txt` avec toutes les dépendances
- ✅ **Résolu** : Configuration Streamlit dans `.streamlit/config.toml`

### 2. Dépendances requises
```
streamlit==1.32.0
streamlit-authenticator==0.3.2
pandas==2.2.0
plotly==5.18.0
psycopg2-binary==2.9.9
python-dotenv==1.0.1
PyYAML==6.0.1
```

### 3. Configuration secrets Streamlit Cloud
Les secrets suivants doivent être configurés dans Streamlit Cloud :

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

### 4. Point d'entrée
- **Fichier principal** : `Catalogue.py`
- **Pages** : `pages/01_Saisie.py` et `pages/02_Suivi_MaJ.py`

### 5. Structure des fichiers
```
metadata_app_clean/
├── Catalogue.py          # Page principale
├── requirements.txt      # Dépendances Python
├── .streamlit/
│   ├── config.toml      # Configuration Streamlit
│   └── secrets.toml     # Secrets (local uniquement)
├── pages/
│   ├── 01_Saisie.py     # Page de saisie
│   └── 02_Suivi_MaJ.py  # Page de suivi
├── utils/
│   ├── auth.py          # Authentification
│   ├── db_utils.py      # Utilitaires base de données
│   └── sql_generator.py # Générateur SQL
└── config.yaml          # Configuration authenticator
```

## Déploiement sur Streamlit Cloud

1. Connecter le repository GitHub à Streamlit Cloud
2. Sélectionner le fichier `Catalogue.py` comme point d'entrée
3. Configurer les secrets dans l'interface Streamlit Cloud
4. Déployer l'application

## Vérifications post-déploiement

- [ ] L'authentification fonctionne
- [ ] La connexion à la base de données est active
- [ ] Les graphiques s'affichent correctement
- [ ] Toutes les pages sont accessibles 