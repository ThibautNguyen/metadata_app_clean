#!/usr/bin/env python3
"""
Script de nettoyage de sécurité pour metadata_app_clean
Nettoie les identifiants compromis et sécurise la configuration
"""

import os
import subprocess
import sys
from datetime import datetime

def run_command(command, ignore_errors=False):
    """Exécute une commande système de manière sécurisée"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode != 0 and not ignore_errors:
            print(f"❌ Erreur lors de l'exécution : {command}")
            print(f"   Sortie d'erreur : {result.stderr}")
            return False
        return result.stdout.strip()
    except Exception as e:
        print(f"❌ Exception lors de l'exécution de {command}: {e}")
        return False

def check_git_status():
    """Vérifie l'état Git et les branches compromises"""
    print("=== VÉRIFICATION DE L'ÉTAT GIT ===")
    
    # Vérifier que nous sommes dans un repo Git
    if not os.path.exists('.git'):
        print("❌ Ce n'est pas un repository Git")
        return False
    
    # Lister les branches
    branches_output = run_command("git --no-pager branch -a")
    if branches_output:
        print("📋 Branches détectées :")
        for line in branches_output.split('\n'):
            if line.strip():
                print(f"   {line}")
    
    return True

def scan_for_compromised_files():
    """Scanne les fichiers compromis dans le repository"""
    print("\n=== SCAN DES FICHIERS COMPROMIS ===")
    
    compromised_patterns = [
        'password123',
        'some_random_key',
        'admin@example.com',
        '$2b$12$5vQnnesAYGkYOYEfhgTZ6uo67cH06AhegQtMUFmX8oYaaeqFo8iGu'
    ]
    
    compromised_files = []
    
    for pattern in compromised_patterns:
        print(f"🔍 Recherche de '{pattern[:20]}...'")
        result = run_command(f'git --no-pager grep -l "{pattern}" HEAD', ignore_errors=True)
        if result and result != False:
            files = result.split('\n')
            for file in files:
                if file.strip() and file not in compromised_files:
                    compromised_files.append(file.strip())
    
    if compromised_files:
        print("⚠️  FICHIERS COMPROMIS TROUVÉS :")
        for file in compromised_files:
            print(f"   📄 {file}")
    else:
        print("✅ Aucun fichier compromis trouvé dans HEAD")
    
    return compromised_files

def create_security_backup():
    """Crée une sauvegarde avant nettoyage"""
    print("\n=== CRÉATION DE SAUVEGARDE DE SÉCURITÉ ===")
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_branch = f"backup_security_{timestamp}"
    
    result = run_command(f"git checkout -b {backup_branch}")
    if result is not False:
        print(f"✅ Sauvegarde créée : branche '{backup_branch}'")
        run_command("git checkout main")
        return backup_branch
    else:
        print("❌ Impossible de créer la sauvegarde")
        return None

def generate_security_actions():
    """Génère la liste des actions de sécurité à entreprendre"""
    print("\n=== ACTIONS DE SÉCURITÉ REQUISES ===")
    
    actions = [
        "🔐 IMMÉDIAT - Générer nouveaux identifiants : python scripts/generate_secure_config.py",
        "🔄 IMMÉDIAT - Remplacer config.yaml par la version sécurisée",
        "🧹 RECOMMANDÉ - Nettoyer l'historique Git des branches compromises",
        "🚫 CRITIQUE - Supprimer les branches distantes compromises sur GitHub",
        "🔍 CONTRÔLE - Scanner tout le code pour d'autres fuites",
        "📧 NOTIFICATION - Informer l'équipe du changement d'identifiants",
        "🔒 VALIDATION - Tester la nouvelle configuration"
    ]
    
    for i, action in enumerate(actions, 1):
        print(f"{i}. {action}")
    
    return actions

def clean_compromised_branches():
    """Nettoie les branches compromises (interactif)"""
    print("\n=== NETTOYAGE DES BRANCHES COMPROMISES ===")
    
    compromised_branches = [
        'backup-streamlit-1.32.0',
        'ameliorations-interface',
        'temp_branch'
    ]
    
    print("⚠️  ATTENTION : Cette action est IRRÉVERSIBLE")
    print("📋 Branches à nettoyer :")
    for branch in compromised_branches:
        print(f"   - {branch}")
    
    response = input("\n❓ Voulez-vous procéder au nettoyage ? (oui/non) : ")
    if response.lower() in ['oui', 'o', 'yes', 'y']:
        for branch in compromised_branches:
            print(f"🧹 Suppression de la branche locale '{branch}'...")
            run_command(f"git branch -D {branch}", ignore_errors=True)
            
            print(f"🌐 Suppression de la branche distante 'origin/{branch}'...")
            run_command(f"git push origin --delete {branch}", ignore_errors=True)
        
        print("✅ Nettoyage des branches terminé")
    else:
        print("ℹ️  Nettoyage annulé par l'utilisateur")

def main():
    """Fonction principale du script de sécurité"""
    print("🛡️  SCRIPT DE NETTOYAGE DE SÉCURITÉ")
    print("📅 Exécuté le :", datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    print("=" * 60)
    
    # Vérifications préliminaires
    if not check_git_status():
        sys.exit(1)
    
    # Scan des fichiers compromis
    compromised_files = scan_for_compromised_files()
    
    # Création de sauvegarde
    backup_branch = create_security_backup()
    
    # Génération des actions requises
    actions = generate_security_actions()
    
    print("\n" + "=" * 60)
    print("🚨 RÉSUMÉ DE SÉCURITÉ")
    print("=" * 60)
    
    if compromised_files:
        print(f"⚠️  {len(compromised_files)} fichier(s) compromis détecté(s)")
    else:
        print("✅ Aucun fichier compromis dans la version actuelle")
    
    if backup_branch:
        print(f"✅ Sauvegarde créée : {backup_branch}")
    
    print(f"📋 {len(actions)} actions de sécurité listées")
    
    print("\n💡 PROCHAINES ÉTAPES :")
    print("1. Exécutez : python scripts/generate_secure_config.py")
    print("2. Remplacez config.yaml par le nouveau fichier généré")
    print("3. Testez avec : python scripts/test_auth.py")
    print("4. Nettoyez les branches compromises (optionnel)")
    
    # Option de nettoyage des branches
    print("\n" + "=" * 60)
    clean_response = input("❓ Voulez-vous nettoyer les branches compromises maintenant ? (oui/non) : ")
    if clean_response.lower() in ['oui', 'o', 'yes', 'y']:
        clean_compromised_branches()
    
    print("\n🎯 Script de sécurité terminé")

if __name__ == "__main__":
    main() 