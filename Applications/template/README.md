# Documentation des Applications

Ce dossier sert de modèle pour la création de nouvelles applications. Pour la documentation concernant la base de données et les métadonnées, se référer au [README du SGBD](../SGBD/README.md).

## Structure des applications

```
nom-de-l-application/
├── app.py                 # Point d'entrée de l'application
├── pages/                 # Pages de l'application
│   └── 01_Accueil.py     # Exemple de page
├── utils/                # Fonctions utilitaires
│   └── __init__.py
├── requirements.txt      # Dépendances Python
└── README.md            # Documentation du projet
```

## Intégration avec l'architecture existante

### Module Core
Le module `Core` fournit des composants réutilisables :
- `Core/utils/` : Fonctions utilitaires communes
- `Core/data_connectors/` : Connecteurs de données
- `Core/config/` : Configuration partagée

Pour utiliser ces composants :
```python
from Core.utils import *
from Core.data_connectors import *
from Core.config import *
```

### Base de données
Pour accéder aux données :
1. Utiliser les connecteurs de `Core/data_connectors`
2. Se référer aux métadonnées dans `SGBD/Metadata/`
3. Utiliser les requêtes SQL existantes de `SGBD/SQL Queries/`

## Bonnes pratiques de développement

### 1. Organisation du code
- **Nommage** :
  - Utiliser des noms explicites en français
  - Suivre la convention `snake_case` pour les fichiers Python
  - Préfixer les pages avec des numéros (ex: `01_Accueil.py`)

- **Structure** :
  - Une page = un fichier Python
  - Regrouper les composants réutilisables dans `utils/`
  - Documenter chaque fonction avec des docstrings

### 2. Gestion des données
- **Accès aux données** :
  - Utiliser exclusivement les connecteurs de `Core/data_connectors`
  - Ne pas implémenter de nouvelles connexions à la base de données
  - Documenter les requêtes SQL complexes

- **Sécurité** :
  - Ne pas stocker de données sensibles dans le code
  - Utiliser des variables d'environnement pour les configurations
  - Valider les entrées utilisateur

### 3. Interface utilisateur
- **Streamlit** :
  - Utiliser les composants natifs de Streamlit
  - Créer des layouts responsifs
  - Gérer les états de chargement

- **Visualisation** :
  - Utiliser Plotly pour les graphiques interactifs
  - Documenter les sources des données
  - Ajouter des tooltips explicatifs

### 4. Documentation
- **Code** :
  - Documenter les fonctions avec des docstrings
  - Utiliser des types hints
  - Commenter les parties complexes

- **Utilisateur** :
  - Ajouter des explications dans l'interface
  - Documenter les fonctionnalités principales
  - Fournir des exemples d'utilisation

### 5. Logs et monitoring
- **Configuration des logs** :
  - Utiliser le module `logging` de Python
  - Définir des niveaux de log appropriés (INFO, DEBUG, ERROR)
  - Stocker les logs dans le dossier `logs/`

- **Format des logs** :
  ```python
  import logging
  
  logging.basicConfig(
      filename='logs/app.log',
      level=logging.INFO,
      format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
  )
  ```

### 6. Tests et maintenance
- **Tests unitaires** :
  - Tester les fonctions critiques
  - Utiliser pytest pour les tests
  - Maintenir une bonne couverture de tests

- **Maintenance** :
  - Documenter les dépendances
  - Mettre à jour régulièrement les packages
  - Suivre les bonnes pratiques de sécurité

## Dépendances

Voir `requirements.txt` pour les dépendances de base. Ajoutez uniquement ce qui est nécessaire pour votre application.

## Exemple d'utilisation

1. Copier ce dossier template
2. Renommer avec le nom de l'application
3. Modifier `requirements.txt` si nécessaire
4. Commencer le développement dans `app.py`

## Ressources

- [Documentation Streamlit](https://docs.streamlit.io/)
- [Documentation Plotly](https://plotly.com/python/)
- [Documentation Pandas](https://pandas.pydata.org/docs/)
- [README du SGBD](../SGBD/README.md) 