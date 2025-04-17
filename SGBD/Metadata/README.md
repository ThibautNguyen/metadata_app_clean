# Métadonnées des Jeux de Données

## Vue d'ensemble

Ce dossier contient les métadonnées des différents jeux de données importés dans le système d'information. Les métadonnées sont organisées par source de données.

## Structure des métadonnées

Pour chaque source de données, les métadonnées contiennent les informations suivantes :
- Description générale du jeu de données
- Schéma de la base de données
- Description des tables et champs
- Périodicité de mise à jour
- Source et date d'acquisition
- Format des données
- Clés de jointure avec d'autres jeux de données

## Sources de données

### 1. INSEE
- Données statistiques nationales
- Recensement de la population
- Indicateurs économiques
- Données démographiques

### 2. Spallian
- Données spécifiques à l'organisation
- Informations sectorielles
- Données géographiques

### 3. Sit@del (permis de construire)
- Données sur les permis de construire
- Informations urbanistiques
- Données de construction

### 4. Citepa (GES)
- Données sur les Gaz à Effet de Serre
- Inventaires d'émissions
- Indicateurs environnementaux

### 5. Ministère de la Transition Ecologique
- Données environnementales
- Politiques publiques
- Réglementations

### 6. Météo France
- Données météorologiques
- Historiques climatiques
- Prévisions

## Format des métadonnées

Les métadonnées sont stockées dans des fichiers au format suivant :
- JSON pour la structure des données
- Markdown pour la documentation
- SQL pour les schémas de base de données

## Mise à jour des métadonnées

Procédure à suivre lors de l'ajout ou de la modification d'un jeu de données :
1. Créer ou mettre à jour le fichier de métadonnées correspondant
2. Documenter les changements dans le fichier CHANGELOG.md
3. Vérifier la cohérence avec les autres jeux de données
4. Mettre à jour les requêtes SQL si nécessaire

## Bonnes pratiques

1. Documentation :
   - Maintenir à jour la description des champs
   - Documenter les transformations de données
   - Noter les limitations et contraintes

2. Organisation :
   - Utiliser des noms de fichiers explicites
   - Structurer les métadonnées de manière cohérente
   - Maintenir un historique des modifications

3. Qualité :
   - Vérifier la complétude des informations
   - S'assurer de la cohérence des formats
   - Documenter les anomalies connues 