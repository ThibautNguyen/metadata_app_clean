# Documentation de l'Authentification

## Points d'attention importants

### 1. Version de streamlit-authenticator
- **Version requise** : 0.3.2
- **Ne pas utiliser** la version 0.4.2 car elle :
  - Change la signature de la méthode `login()`
  - Modifie la structure attendue du YAML
  - N'est pas compatible avec le code existant

### 2. Environnement virtuel
- Toujours utiliser `.venv_new`
- Activer l'environnement avant toute installation :
  ```powershell
  .\.venv_new\Scripts\Activate.ps1
  ```
- Vérifier l'installation :
  ```powershell
  pip list | findstr streamlit-authenticator
  ```

### 3. Génération de hash
- La version 0.3.2 n'inclut pas de méthode `Hasher`
- Utiliser bcrypt directement :
  ```python
  import bcrypt
  password = b'votre_mot_de_passe'
  hash = bcrypt.hashpw(password, bcrypt.gensalt(rounds=12))
  print(hash.decode())
  ```

### 4. Structure du YAML
- Format exact requis :
  ```yaml
  credentials:
    usernames:
      username:
        email: email@example.com
        name: Nom Utilisateur
        password: $2b$12$...  # Hash bcrypt
  cookie:
    expiry_days: 30
    key: some_signature_key
    name: some_cookie_name
  preauthorized:
    emails:
      - email@example.com
  ```

## Dépannage courant

### 1. Module non trouvé
- Vérifier l'activation de `.venv_new`
- Vérifier l'installation : `pip install streamlit-authenticator==0.3.2`

### 2. Erreur de hash
- Vérifier que le hash est au format bcrypt
- Vérifier que le mot de passe correspond exactement

### 3. Erreur de structure YAML
- Vérifier l'indentation
- Vérifier la présence de tous les champs requis

## Historique des problèmes résolus

1. **Problème de versions multiples**
   - Solution : Utiliser strictement la version 0.3.2
   - Raison : Compatibilité avec le code existant

2. **Problème d'environnement virtuel**
   - Solution : Utiliser `.venv_new`
   - Raison : Isolation des dépendances

3. **Problème de génération de hash**
   - Solution : Utiliser bcrypt directement
   - Raison : Absence de `Hasher` en 0.3.2

4. **Problème de structure YAML**
   - Solution : Suivre exactement la structure documentée
   - Raison : Format strict requis par 0.3.2 