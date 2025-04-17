# Script de configuration Git
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

# Fonction pour synchroniser les métadonnées
function Sync-Metadata {
    param (
        [switch]$Force = $false
    )

    Write-Host "Synchronisation des métadonnées..." -ForegroundColor Cyan

    # Vérification des modifications
    $status = git status --porcelain "SGBD/Metadata/"
    if (-not $status -and -not $Force) {
        Write-Host "Aucune modification détectée dans les métadonnées." -ForegroundColor Yellow
        return
    }

    # Ajout des fichiers modifiés
    git add "SGBD/Metadata/"

    # Création du commit
    $commitMessage = "Mise à jour des métadonnées - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"
    git commit -m $commitMessage

    # Push vers GitHub
    try {
        git push origin main
        Write-Host "Synchronisation réussie !" -ForegroundColor Green
    } catch {
        Write-Host "Erreur lors de la synchronisation : $_" -ForegroundColor Red
    }
}

# Fonction pour configurer la tâche planifiée
function Set-SyncSchedule {
    $taskName = "Sync_Metadata_GitHub"
    $scriptPath = $PSScriptRoot + "\sync_metadata.ps1"
    $taskDescription = "Synchronisation quotidienne des métadonnées avec GitHub"

    # Création du script de synchronisation
    @"
# Script de synchronisation des métadonnées
Set-Location '$PWD'
Import-Module '$PSScriptRoot\setup_git.ps1'
Sync-Metadata
"@ | Out-File -FilePath $scriptPath -Encoding UTF8

    # Configuration de la tâche planifiée
    $action = New-ScheduledTaskAction -Execute "PowerShell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$scriptPath`""
    $trigger = New-ScheduledTaskTrigger -Daily -At 3AM
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -DontStopOnIdleEnd

    # Création ou mise à jour de la tâche
    try {
        Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description $taskDescription -Force
        Write-Host "Tâche planifiée configurée avec succès !" -ForegroundColor Green
        Write-Host "La synchronisation s'exécutera quotidiennement à 3h du matin." -ForegroundColor Cyan
    } catch {
        Write-Host "Erreur lors de la configuration de la tâche planifiée : $_" -ForegroundColor Red
    }

    # Ajouter une tâche au démarrage
    $startupTrigger = New-ScheduledTaskTrigger -AtStartup
    Register-ScheduledTask -TaskName "Sync_Metadata_Startup" -Action $action -Trigger $startupTrigger
}

# Configuration initiale de Git
Write-Host "Configuration de Git pour le projet..." -ForegroundColor Cyan

# Vérification de la présence de Git
try {
    git --version | Out-Null
} catch {
    Write-Host "Git n'est pas installé. Veuillez l'installer avant de continuer." -ForegroundColor Red
    exit 1
}

# Configuration de Git
Write-Host "Configuration de Git..." -ForegroundColor Yellow
git config --global user.name "Système d'Information"
git config --global user.email "si@example.com"
git config --global core.autocrlf false
git config --global core.safecrlf false

# Suppression complète du dépôt Git existant
Write-Host "Suppression du dépôt Git existant..." -ForegroundColor Yellow
if (Test-Path .git) {
    Remove-Item -Recurse -Force .git
}

# Suppression des sous-modules Git
Write-Host "Suppression des sous-modules Git..." -ForegroundColor Yellow
if (Test-Path "SGBD/.git") {
    Remove-Item -Recurse -Force "SGBD/.git"
}

# Initialisation d'un nouveau dépôt
Write-Host "Initialisation d'un nouveau dépôt Git..." -ForegroundColor Yellow
git init

# Création d'un fichier .gitignore temporaire
Write-Host "Configuration du .gitignore..." -ForegroundColor Yellow
@"
# Environnements virtuels Python
venv/
env/
.venv/
.env/

# Fichiers Python
__pycache__/
*.py[cod]
*$py.class

# Fichiers de log
*.log

# Fichiers de configuration Streamlit
.streamlit/

# Fichiers de données sensibles
*.env
*.env.local

# Fichiers système
.DS_Store
Thumbs.db

# Dossiers de build
build/
dist/
*.egg-info/

# Fichiers temporaires
*.tmp
*.temp
"@ | Out-File -FilePath .gitignore -Encoding UTF8

# Ajout des fichiers
Write-Host "Ajout des fichiers au suivi..." -ForegroundColor Yellow
git add --all

# Vérification de l'état du dépôt
$status = git status --porcelain
if (-not $status) {
    Write-Host "Aucun fichier à commiter. Création d'un commit vide..." -ForegroundColor Yellow
    git commit --allow-empty -m "Initial commit - Configuration du projet"
} else {
    Write-Host "Création du commit initial..." -ForegroundColor Yellow
    git commit -m "Initial commit - Configuration du projet"
}

# Configuration du dépôt distant
Write-Host "`nConfiguration du dépôt distant..." -ForegroundColor Yellow

# Vérification si le remote existe déjà
$remote_exists = git remote | Select-String "origin"
if ($remote_exists) {
    Write-Host "Le dépôt distant 'origin' existe déjà" -ForegroundColor Yellow
    Write-Host "Voulez-vous le mettre à jour ? (O/N)" -ForegroundColor Cyan
    $update = Read-Host
    if ($update -eq "O" -or $update -eq "o") {
        $remote_url = Read-Host "Entrez la nouvelle URL du dépôt distant"
        git remote set-url origin $remote_url
    }
} else {
    Write-Host "Voulez-vous configurer un dépôt distant ? (O/N)" -ForegroundColor Cyan
    $response = Read-Host
    if ($response -eq "O" -or $response -eq "o") {
        $remote_url = Read-Host "Entrez l'URL du dépôt distant (GitHub, GitLab, etc.)"
        if ($remote_url) {
            git remote add origin $remote_url
        }
    }
}

# Push vers le dépôt distant
Write-Host "`nEnvoi des modifications vers le dépôt distant..." -ForegroundColor Yellow
try {
    # Création de la branche main
    Write-Host "Création de la branche main..." -ForegroundColor Yellow
    git checkout -b main
    
    # Vérification du commit
    $commit = git rev-parse --verify HEAD
    if (-not $commit) {
        Write-Host "Création d'un commit vide..." -ForegroundColor Yellow
        git commit --allow-empty -m "Initial commit"
    }
    
    # Push vers le dépôt distant
    Write-Host "Envoi des modifications..." -ForegroundColor Yellow
    $push_result = git push -u origin main --force 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Push réussi !" -ForegroundColor Green
    } else {
        Write-Host "Erreur lors du push : $push_result" -ForegroundColor Red
        Write-Host "`nEssayez de résoudre les conflits manuellement avec :" -ForegroundColor Yellow
        Write-Host "1. git pull origin main --allow-unrelated-histories" -ForegroundColor Cyan
        Write-Host "2. Résolvez les conflits si nécessaire" -ForegroundColor Cyan
        Write-Host "3. git add ." -ForegroundColor Cyan
        Write-Host "4. git commit -m 'Résolution des conflits'" -ForegroundColor Cyan
        Write-Host "5. git push -u origin main" -ForegroundColor Cyan
    }
} catch {
    Write-Host "Erreur lors du push : $_" -ForegroundColor Red
    Write-Host "Veuillez suivre les instructions ci-dessus pour résoudre les conflits manuellement" -ForegroundColor Yellow
}

# Configuration de la synchronisation automatique
Write-Host "`nConfiguration de la synchronisation automatique..." -ForegroundColor Yellow
Write-Host "Voulez-vous configurer la synchronisation automatique des métadonnées ? (O/N)" -ForegroundColor Cyan
$syncResponse = Read-Host
if ($syncResponse -eq "O" -or $syncResponse -eq "o") {
    Set-SyncSchedule
}

Write-Host "`nConfiguration terminée !" -ForegroundColor Green
Write-Host "Pour synchroniser manuellement les métadonnées : Sync-Metadata" -ForegroundColor Cyan
Write-Host "Pour forcer la synchronisation : Sync-Metadata -Force" -ForegroundColor Cyan

Get-ScheduledTask -TaskName "Sync_Metadata_*" | Format-Table TaskName, State, LastRunTime, NextRunTime

Sync-Metadata 