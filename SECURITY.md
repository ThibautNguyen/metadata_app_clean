# Guide de Sécurité - Catalogue des Métadonnées

## 🚨 Alertes de Sécurité

### ⚠️ IMPORTANT - Compromission d'identifiants
Si vous avez cloné ce repository avant le commit de sécurisation, **changez immédiatement** vos identifiants de base de données car ils étaient exposés publiquement sur GitHub.

## 🔐 Configuration Sécurisée

### Variables d'environnement requises

L'application utilise les variables d'environnement suivantes (OBLIGATOIRES) :

```bash
# Base de données
NEON_HOST=your_neon_host
NEON_DATABASE=your_database_name  
NEON_USER=your_username
NEON_PASSWORD=your_secure_password

# Optionnel : API Keys
NEON_API_KEY=your_api_key
NEON_API_URL=your_api_url
```

### Configuration locale (.env)

Créez un fichier `.env` à la racine du projet :

```env
# Base de données Neon.tech
NEON_HOST=your_neon_host
NEON_DATABASE=your_database_name
NEON_USER=your_username
NEON_PASSWORD=your_secure_password
```

**ATTENTION** : Le fichier `.env` est exclu de Git via `.gitignore` - ne jamais le committer !

### Configuration Streamlit Cloud

Dans l'interface Streamlit Cloud, ajoutez les secrets suivants :

```toml
NEON_HOST = "your_neon_host"
NEON_DATABASE = "your_database_name"
NEON_USER = "your_username"
NEON_PASSWORD = "your_secure_password"
```

## 🛡️ Bonnes Pratiques

### Mots de passe
- Utilisez des mots de passe forts (20+ caractères)
- Incluez majuscules, minuscules, chiffres, symboles
- Ne réutilisez jamais de mots de passe
- Changez régulièrement les identifiants

### Accès base de données
- Utilisez des comptes avec privilèges minimaux nécessaires
- Activez toujours SSL/TLS (`sslmode=require`)
- Surveillez les connexions suspectes
- Limitez les adresses IP autorisées quand possible

### Code
- ❌ **JAMAIS** d'identifiants hardcodés dans le code
- ✅ Toujours utiliser des variables d'environnement
- ✅ Vérifier `.gitignore` avant chaque commit
- ✅ Scanner le code pour détecter les secrets

## 🔍 Vérification de Sécurité

### Avant chaque commit
```bash
# Vérifier qu'aucun secret n'est présent
git diff --cached | grep -i "password\\|secret\\|key\\|token"

# Scanner les fichiers
grep -r "napi_\\|npg_" . --exclude-dir=.git
```

### Outils recommandés
- **git-secrets** : Prévention des commits de secrets
- **gitleaks** : Scanner pour détecter les fuites d'identifiants
- **truffleHog** : Recherche de secrets dans l'historique Git

## 🚨 En cas de compromission

### Actions immédiates
1. **Changer TOUS les mots de passe** exposés
2. **Révoquer les clés API** compromises
3. **Auditer les logs** de la base de données
4. **Nettoyer l'historique Git** si nécessaire

### Nettoyage historique Git
```bash
# ATTENTION : Réécrit l'historique - coordonner avec l'équipe
git filter-branch --force --index-filter \
'git rm --cached --ignore-unmatch fichier_avec_secrets.py' \
--prune-empty --tag-name-filter cat -- --all
```

## 📋 Checklist de Sécurité

- [ ] Variables d'environnement configurées
- [ ] Aucun identifiant hardcodé dans le code
- [ ] `.gitignore` à jour
- [ ] Secrets Streamlit Cloud configurés
- [ ] Mots de passe forts utilisés
- [ ] SSL/TLS activé pour la base de données
- [ ] Logs de sécurité surveillés

## 📞 Support Sécurité

En cas de problème de sécurité :
1. NE PAS exposer d'informations sensibles dans les issues
2. Changer immédiatement les identifiants
3. Documenter l'incident pour prévention future

---

**Dernière mise à jour** : 2025-06-30  
**Version** : 1.0 