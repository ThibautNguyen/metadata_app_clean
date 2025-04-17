# Application de Gestion des Métadonnées

Cette application Streamlit permet de gérer facilement les métadonnées de vos jeux de données.

## Fonctionnalités

- 📝 **Saisie des métadonnées** : Créez et modifiez facilement des fiches de métadonnées
- 🔍 **Recherche** : Parcourez les métadonnées existantes avec des filtres avancés
- 💾 **Stockage** : Enregistrement automatique en JSON et TXT
- 🔄 **Synchronisation Git** : Intégration avec Git pour versionner les métadonnées

## Installation

1. Assurez-vous d'avoir Python 3.8+ installé
2. Installez les dépendances :

```bash
cd Applications/Streamlit
pip install -r requirements.txt
```

## Lancement de l'application

```bash
cd Applications/Streamlit
streamlit run Home.py
```

L'application sera accessible à l'adresse : http://localhost:8501

## Structure des fichiers

- `Home.py` : Page d'accueil de l'application
- `pages/02_Saisie.py` : Formulaire de saisie des métadonnées
- `pages/03_Recherche.py` : Interface de recherche et consultation

## Utilisation

1. Accédez à l'application via votre navigateur
2. Pour créer une nouvelle fiche de métadonnées, allez sur "Saisie des métadonnées"
3. Pour chercher parmi les fiches existantes, utilisez "Recherche"

## Synchronisation Git

Les métadonnées sont automatiquement:
- Sauvegardées localement dans le dossier `SGBD/Metadata`
- Ajoutées au dépôt Git local
- Une tâche planifiée synchronise quotidiennement les changements avec GitHub

Pour synchroniser manuellement, exécutez dans PowerShell :
```powershell
Import-Module ".\Applications\setup_git.ps1"
Sync-Metadata
``` 