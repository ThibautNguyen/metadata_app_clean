#!/usr/bin/env python3
"""
Script pour générer une configuration d'authentification sécurisée
Génère de nouveaux identifiants et clés de sécurité
"""

import streamlit_authenticator as stauth
import yaml
import secrets
import string
import os
from datetime import datetime

def generate_secure_key(length=64):
    """Génère une clé de sécurité aléatoire"""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def generate_secure_config():
    """Génère une configuration d'authentification sécurisée"""
    
    print("🔐 GÉNÉRATION DE CONFIGURATION SÉCURISÉE")
    print("=" * 50)
    
    # Demander le mot de passe admin
    admin_password = input("Entrez le nouveau mot de passe pour l'administrateur : ")
    if not admin_password:
        print("❌ Mot de passe requis")
        return False
    
    # Générer le hash du mot de passe
    hashed_password = stauth.Hasher([admin_password]).generate()
    
    # Générer une nouvelle clé de cookie sécurisée
    cookie_key = generate_secure_key(64)
    
    # Configuration sécurisée
    config = {
        'cookie': {
            'expiry_days': 7,
            'key': cookie_key,
            'name': 'streamlit_auth_cookie'
        },
        'credentials': {
            'usernames': {
                'admin': {
                    'email': 'thibaut.nguyen@spallian.com',
                    'name': 'Administrateur',
                    'password': hashed_password
                }
            }
        },
        'preauthorized': {
            'emails': ['thibaut.nguyen@spallian.com']
        }
    }
    
    # Sauvegarder l'ancienne configuration
    if os.path.exists('config.yaml'):
        backup_name = f'config_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.yaml'
        os.rename('config.yaml', backup_name)
        print(f"✅ Ancienne configuration sauvegardée : {backup_name}")
    
    # Écrire la nouvelle configuration
    with open('config.yaml', 'w', encoding='utf-8') as file:
        yaml.dump(config, file, default_flow_style=False, allow_unicode=True)
    
    print("✅ Configuration sécurisée générée : config.yaml")
    print("🔑 Nouvelle clé de cookie générée")
    print("🔐 Nouveau hash de mot de passe généré")
    
    # Afficher les informations de sécurité
    print("\n📋 INFORMATIONS DE SÉCURITÉ :")
    print(f"   - Clé de cookie : {cookie_key[:20]}...")
    print(f"   - Hash du mot de passe : {hashed_password[:20]}...")
    print(f"   - Email autorisé : {config['credentials']['usernames']['admin']['email']}")
    
    return True

def test_new_config():
    """Teste la nouvelle configuration"""
    print("\n🧪 TEST DE LA NOUVELLE CONFIGURATION")
    print("=" * 40)
    
    try:
        with open('config.yaml', 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
        
        # Vérifier la structure
        required_keys = ['cookie', 'credentials', 'preauthorized']
        for key in required_keys:
            if key not in config:
                print(f"❌ Section '{key}' manquante")
                return False
        
        print("✅ Structure de configuration valide")
        
        # Vérifier la clé de cookie
        if len(config['cookie']['key']) < 32:
            print("❌ Clé de cookie trop courte")
            return False
        
        print("✅ Clé de cookie sécurisée")
        
        # Vérifier le hash du mot de passe
        password_hash = config['credentials']['usernames']['admin']['password']
        if not password_hash.startswith('$2b$'):
            print("❌ Hash de mot de passe invalide")
            return False
        
        print("✅ Hash de mot de passe valide")
        
        print("✅ Configuration testée avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors du test : {e}")
        return False

if __name__ == "__main__":
    print("🛡️ SCRIPT DE GÉNÉRATION DE CONFIGURATION SÉCURISÉE")
    print("⚠️  Ce script va remplacer votre configuration actuelle")
    print()
    
    confirmation = input("Voulez-vous continuer ? (oui/non) : ")
    if confirmation.lower() not in ['oui', 'o', 'yes', 'y']:
        print("❌ Opération annulée")
        exit(0)
    
    if generate_secure_config():
        if test_new_config():
            print("\n🎉 CONFIGURATION SÉCURISÉE CRÉÉE AVEC SUCCÈS")
            print("🔒 Votre application est maintenant sécurisée")
            print("\n💡 Prochaines étapes :")
            print("   1. Testez l'authentification : python scripts/test_auth.py")
            print("   2. Lancez l'application : streamlit run Catalogue.py")
        else:
            print("\n❌ Erreur lors du test de la configuration")
    else:
        print("\n❌ Erreur lors de la génération de la configuration") 