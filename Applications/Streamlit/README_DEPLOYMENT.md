# Déploiement sur Streamlit Cloud

Ce document explique comment déployer l'application de gestion des métadonnées sur Streamlit Cloud.

## Prérequis

- Un compte Streamlit Cloud (https://streamlit.io/cloud)
- Un dépôt GitHub contenant votre application

## Étapes de déploiement

1. **Créer un nouveau dépôt GitHub pour l'application** (si ce n'est pas déjà fait)
   - Créez un dépôt public ou privé sur GitHub
   - Poussez le contenu du dossier `Applications/Streamlit` vers ce dépôt

2. **Se connecter à Streamlit Cloud**
   - Accédez à https://streamlit.io/cloud
   - Connectez-vous avec votre compte GitHub

3. **Déployer une nouvelle application**
   - Cliquez sur "New app"
   - Sélectionnez le dépôt GitHub de votre application
   - Entrez le chemin vers le fichier principal : `Home.py`
   - Cliquez sur "Deploy"

4. **Configurer les secrets**
   - Une fois déployée, allez dans les paramètres de l'application
   - Dans l'onglet "Secrets", ajoutez les informations suivantes :
   ```toml
   [github]
   repo = "ThibautNguyen/DOCS"
   branch = "main"
   metadata_path = "SGBD/Metadata"
   ```

5. **Accéder à l'application**
   - Cliquez sur l'URL fournie pour accéder à votre application

## Structure des fichiers importants

- `Home.py` : Page d'accueil de l'application
- `requirements.txt` : Dépendances nécessaires
- `.streamlit/secrets.toml` : Configuration locale (ne pas inclure dans Git)
- `pages/` : Pages supplémentaires de l'application

## Dépannage

- Si l'application ne trouve pas les métadonnées, vérifiez les valeurs dans les secrets
- Pour les problèmes de dépendances, vérifiez que `requirements.txt` est à jour
- Consultez les logs de l'application pour identifier les erreurs potentielles 