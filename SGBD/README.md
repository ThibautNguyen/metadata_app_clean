# Gestion des Bases de Données (SGBD)

## Vue d'ensemble

Ce dossier contient l'ensemble des éléments liés à la gestion des bases de données du système d'information, géré via DBeaver.

## Structure

Le dossier SGBD est organisé en deux composants principaux :

### 1. Metadata/
Contient les métadonnées des différents jeux de données importés, organisés par source :
- INSEE : Données statistiques nationales
- Spallian : Données spécifiques
- Sit@del : Données des permis de construire
- Citepa : Données sur les Gaz à Effet de Serre (GES)
- MTES : Données du Ministère de la Transition Écologique
- Météo France : Données météorologiques

### 2. SQL Queries/
Regroupe les requêtes SQL organisées par thématique :
- Économie
- Environnement
- Énergie
- Logement
- Population

## Gestion des données

### Outils utilisés
- DBeaver : Interface de gestion des bases de données
- PostgreSQL : Système de gestion de base de données principal

### Bonnes pratiques
1. Documentation des métadonnées :
   - Description des champs
   - Sources des données
   - Périodicité de mise à jour
   - Format des données

2. Organisation des requêtes SQL :
   - Commentaires détaillés en en-tête
   - Documentation des paramètres
   - Explication des résultats attendus
   - Versioning des requêtes

## Maintenance

Pour maintenir la cohérence des données :
1. Mettre à jour les métadonnées lors de l'import de nouveaux jeux de données
2. Documenter les modifications des schémas de base de données
3. Tester les requêtes SQL après chaque mise à jour de la structure

## Liens utiles
- [Documentation DBeaver](https://dbeaver.io/docs/)
- [Documentation PostgreSQL](https://www.postgresql.org/docs/) 