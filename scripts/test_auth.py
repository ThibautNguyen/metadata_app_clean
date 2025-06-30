#!/usr/bin/env python3
"""
Script de test de l'authentification - VERSION SÉCURISÉE
Ce script teste la configuration d'authentification sans exposer d'informations sensibles
"""

import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import sys
import os
import bcrypt

def test_auth_config():
    """Test la configuration d'authentification de manière sécurisée"""
    
    print('=== TEST DE CONFIGURATION D\'AUTHENTIFICATION ===')
    print(f'Répertoire de travail : {os.getcwd()}')
    
    config_path = 'config.yaml'
    print(f'Fichier config.yaml présent : {os.path.isfile(config_path)}')
    
    if not os.path.isfile(config_path):
        print('❌ ERREUR : config.yaml introuvable')
        return False
    
    try:
        # Test de chargement du YAML
        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.load(file, Loader=SafeLoader)
        
        print('✅ Chargement YAML réussi')
        
        # Vérification de la structure (sans exposer les valeurs)
        required_keys = ['credentials', 'cookie', 'preauthorized']
        for key in required_keys:
            if key in config:
                print(f'✅ Section "{key}" présente')
            else:
                print(f'❌ Section "{key}" manquante')
                return False
        
        # Vérification des credentials (structure seulement)
        if 'usernames' in config['credentials']:
            user_count = len(config['credentials']['usernames'])
            print(f'✅ {user_count} utilisateur(s) configuré(s)')
            
            # Vérification que tous les utilisateurs ont un hash bcrypt valide
            for username, user_data in config['credentials']['usernames'].items():
                if 'password' in user_data:
                    password_hash = user_data['password']
                    if password_hash.startswith('$2b$') and len(password_hash) == 60:
                        print(f'✅ Utilisateur "{username}" : hash bcrypt valide')
                    else:
                        print(f'❌ Utilisateur "{username}" : hash bcrypt invalide')
                        return False
                else:
                    print(f'❌ Utilisateur "{username}" : pas de mot de passe')
                    return False
        else:
            print('❌ Section "usernames" manquante dans credentials')
            return False
        
        # Vérification des paramètres de cookie
        cookie_config = config['cookie']
        if 'key' in cookie_config and 'name' in cookie_config:
            key_length = len(cookie_config['key'])
            print(f'✅ Configuration cookie valide (clé de {key_length} caractères)')
            
            # Alerte si clé faible détectée
            if cookie_config['key'] in ['some_random_key', 'changeme', 'default']:
                print('⚠️  ALERTE SÉCURITÉ : Clé de cookie par défaut détectée')
                print('⚠️  Utilisez le script generate_secure_config.py')
                return False
        else:
            print('❌ Configuration cookie incomplète')
            return False
        
        print('✅ Configuration d\'authentification valide')
        return True
        
    except yaml.YAMLError as e:
        print(f'❌ Erreur YAML : {e}')
        return False
    except Exception as e:
        print(f'❌ Erreur générale : {e}')
        return False

def test_bcrypt_functionality():
    """Test le fonctionnement de bcrypt (sans exposer de données sensibles)"""
    
    print('\n=== TEST DE LA FONCTIONNALITÉ BCRYPT ===')
    
    try:
        # Test avec un mot de passe temporaire
        test_password = 'test_temporaire_12345'
        test_hash = bcrypt.hashpw(test_password.encode('utf-8'), bcrypt.gensalt(rounds=12))
        
        # Vérification que le hash est correct
        if bcrypt.checkpw(test_password.encode('utf-8'), test_hash):
            print('✅ Bcrypt fonctionne correctement')
            return True
        else:
            print('❌ Bcrypt ne fonctionne pas correctement')
            return False
            
    except Exception as e:
        print(f'❌ Erreur bcrypt : {e}')
        return False

if __name__ == "__main__":
    print('🔐 SCRIPT DE TEST D\'AUTHENTIFICATION SÉCURISÉ')
    print('📝 Ce script ne révèle aucune information sensible')
    print()
    
    # Tests
    config_ok = test_auth_config()
    bcrypt_ok = test_bcrypt_functionality()
    
    print('\n=== RÉSUMÉ DES TESTS ===')
    if config_ok and bcrypt_ok:
        print('✅ Tous les tests sont passés')
        print('🔐 Configuration d\'authentification prête')
    else:
        print('❌ Certains tests ont échoué')
        print('⚠️  Vérifiez la configuration avant déploiement')
        
    print('\n💡 Pour générer une configuration sécurisée :')
    print('    python scripts/generate_secure_config.py') 