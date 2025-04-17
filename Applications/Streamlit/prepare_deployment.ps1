# Script pour préparer le déploiement de l'application Streamlit
# À exécuter depuis le dossier principal du projet

# Vérifier si Git est installé
try {
    git --version | Out-Null
    Write-Host "Git est installé sur votre système." -ForegroundColor Green
} catch {
    Write-Host "Git n'est pas installé. Veuillez l'installer pour continuer." -ForegroundColor Red
    exit
}

# Demander le nom du dépôt GitHub pour le déploiement
$defaultRepo = "metadata-app"
$repoName = Read-Host "Entrez le nom du dépôt GitHub pour le déploiement [$defaultRepo]"
if ([string]::IsNullOrWhiteSpace($repoName)) {
    $repoName = $defaultRepo
}

# Créer un dossier temporaire pour le déploiement
$deploymentDir = "deployment_temp"
New-Item -Path $deploymentDir -ItemType Directory -Force | Out-Null
Write-Host "Dossier temporaire créé: $deploymentDir" -ForegroundColor Green

# Copier les fichiers nécessaires
Write-Host "Copie des fichiers pour le déploiement..." -ForegroundColor Yellow
Copy-Item -Path "Applications/Streamlit/Home.py" -Destination "$deploymentDir/" -Force
Copy-Item -Path "Applications/Streamlit/requirements.txt" -Destination "$deploymentDir/" -Force
Copy-Item -Path "Applications/Streamlit/.gitignore" -Destination "$deploymentDir/" -Force
Copy-Item -Path "Applications/Streamlit/README_DEPLOYMENT.md" -Destination "$deploymentDir/README.md" -Force
Copy-Item -Path "Applications/Streamlit/pages" -Destination "$deploymentDir/" -Recurse -Force
New-Item -Path "$deploymentDir/.streamlit" -ItemType Directory -Force | Out-Null

# Créer le fichier de configuration pour le développement local
$configContent = @"
[theme]
primaryColor = "#1E88E5"
backgroundColor = "#FFFFFF"
secondaryBackgroundColor = "#F0F2F6"
textColor = "#262730"
font = "sans serif"
"@

Set-Content -Path "$deploymentDir/.streamlit/config.toml" -Value $configContent

# Initialiser un dépôt Git dans le dossier de déploiement
Set-Location -Path $deploymentDir
git init
git add .
git commit -m "Initial commit for Streamlit Cloud deployment"

# Afficher les instructions pour connecter au dépôt GitHub
Write-Host ""
Write-Host "==================== INSTRUCTIONS ====================`n" -ForegroundColor Cyan
Write-Host "1. Créez un dépôt GitHub nommé '$repoName'"
Write-Host "2. Exécutez les commandes suivantes pour pousser vers GitHub:`n"
Write-Host "   cd $deploymentDir"
Write-Host "   git remote add origin https://github.com/ThibautNguyen/$repoName.git"
Write-Host "   git branch -M main"
Write-Host "   git push -u origin main`n"
Write-Host "3. Déployez sur Streamlit Cloud:"
Write-Host "   - Visitez https://streamlit.io/cloud"
Write-Host "   - Connectez-vous avec GitHub"
Write-Host "   - Créez une nouvelle app et sélectionnez le dépôt '$repoName'"
Write-Host "   - Configurez le fichier principal comme 'Home.py'"
Write-Host "   - Dans les paramètres, ajoutez les secrets comme indiqué dans le README.md"
Write-Host ""
Write-Host "==================================================="

# Revenir au dossier initial
Set-Location -Path ".." 