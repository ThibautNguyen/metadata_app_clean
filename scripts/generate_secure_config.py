#!/usr/bin/env python3
"""
Script de génération d'une configuration d'authentification sécurisée
Génère des mots de passe forts et des clés cryptographiquement sécurisées
"""

import bcrypt
import secrets
import string
import yaml
import os
from datetime import datetime

def generate_strong_password(length=24):
    """Génère un mot de passe cryptographiquement fort"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_secure_key(length=64):
    """Génère une clé secrète cryptographiquement sécurisée"""
    return secrets.token_urlsafe(length)

def hash_password(password):
    """Hash un mot de passe avec bcrypt et salt fort"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=14)).decode('utf-8')

def generate_secure_config():
    """Génère une configuration d'authentification sécurisée"""
    
    # Génération d'identifiants forts
    admin_password = generate_strong_password(24)
    cookie_key = generate_secure_key(64)
    
    # Hash sécurisé du mot de passe
    password_hash = hash_password(admin_password)
    
    # Configuration sécurisée
    secure_config = {
        'credentials': {
            'usernames': {
                'admin': {
                    'email': 'admin@collectivite.fr',  # À adapter
                    'name': 'Administrateur',
                    'password': password_hash
                }
            }
        },
        'cookie': {
            'expiry_days': 7,  # Durée réduite pour plus de sécurité
            'key': cookie_key,
            'name': 'streamlit_auth_cookie'
        },
        'preauthorized': {
            'emails': [
                'admin@collectivite.fr'  # À adapter
            ]
        }
    }
    
    # Sauvegarde de la configuration
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    config_filename = f'config_secure_{timestamp}.yaml'
    
    with open(config_filename, 'w', encoding='utf-8') as f:
        yaml.dump(secure_config, f, default_flow_style=False, allow_unicode=True)
    
    # Sauvegarde des identifiants (à stocker en sécurité)
    credentials_filename = f'CREDENTIALS_ADMIN_{timestamp}.txt'
    with open(credentials_filename, 'w', encoding='utf-8') as f:
        f.write("=== IDENTIFIANTS ADMINISTRATEUR ===\n")
        f.write(f"Généré le : {datetime.now()}\n")
        f.write(f"Utilisateur : admin\n")
        f.write(f"Mot de passe : {admin_password}\n")
        f.write(f"Email : admin@collectivite.fr\n")
        f.write("\n=== CLÉS TECHNIQUES ===\n")
        f.write(f"Cookie key : {cookie_key}\n")
        f.write(f"Password hash : {password_hash}\n")
        f.write("\n=== SÉCURITÉ ===\n")
        f.write("⚠️  STOCKEZ CE FICHIER EN LIEU SÛR\n")
        f.write("⚠️  NE JAMAIS COMMITTER SUR GIT\n")
        f.write("⚠️  SUPPRIMEZ CE FICHIER APRÈS USAGE\n")
    
    print("✅ Configuration sécurisée générée !")
    print(f"📄 Fichier config : {config_filename}")
    print(f"🔐 Identifiants : {credentials_filename}")
    print(f"👤 Utilisateur : admin")
    print(f"🔑 Mot de passe : {admin_password}")
    print("\n🚨 ACTIONS REQUISES :")
    print("1. Remplacez config.yaml par le nouveau fichier")
    print("2. Stockez les identifiants en lieu sûr")
    print("3. Supprimez les anciens fichiers compromis")
    print("4. Testez la connexion avec les nouveaux identifiants")

if __name__ == "__main__":
    generate_secure_config() 