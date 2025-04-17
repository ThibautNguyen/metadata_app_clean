# Requêtes SQL pour les Indicateurs

## Vue d'ensemble

Ce dossier contient l'ensemble des requêtes SQL utilisées pour produire des indicateurs statistiques dans le cadre de l'activité professionnelle. Les requêtes sont organisées par thématique.

## Structure des requêtes

### Organisation par thématique

1. **Économie**
   - Indicateurs économiques
   - Données financières
   - Statistiques sectorielles

2. **Environnement**
   - Indicateurs environnementaux
   - Données sur la qualité de l'air
   - Métriques de développement durable

3. **Énergie**
   - Consommation énergétique
   - Production d'énergie
   - Indicateurs d'efficacité énergétique

4. **Logement**
   - Statistiques du parc immobilier
   - Données sur la construction
   - Indicateurs du marché du logement

5. **Population**
   - Données démographiques
   - Statistiques sociales
   - Évolution de la population

## Format des requêtes

Chaque requête SQL doit inclure en en-tête :
```sql
-- Titre : [Nom de la requête]
-- Description : [Description détaillée]
-- Source : [Source des données]
-- Date de création : [JJ/MM/AAAA]
-- Dernière modification : [JJ/MM/AAAA]
-- Auteur : [Nom]
-- Version : [X.Y]
```

## Bonnes pratiques

1. **Documentation**
   - Documenter clairement l'objectif de chaque requête
   - Expliquer les paramètres et variables
   - Décrire les résultats attendus
   - Noter les limitations et contraintes

2. **Organisation**
   - Nommer les fichiers de manière explicite
   - Regrouper les requêtes connexes
   - Maintenir un historique des modifications

3. **Qualité**
   - Optimiser les performances
   - Vérifier la cohérence des résultats
   - Tester les requêtes après modifications

## Maintenance

Pour maintenir la qualité des requêtes :
1. Vérifier régulièrement les performances
2. Mettre à jour la documentation
3. Tester après chaque modification de schéma
4. Documenter les changements dans CHANGELOG.md

## Exemple de structure de fichier

```
SQL Queries/
├── Économie/
│   ├── indicateurs_economiques.sql
│   └── statistiques_sectorielles.sql
├── Environnement/
│   ├── qualite_air.sql
│   └── developpement_durable.sql
├── Énergie/
│   ├── consommation.sql
│   └── production.sql
├── Logement/
│   ├── parc_immobilier.sql
│   └── marche_logement.sql
└── Population/
    ├── demographie.sql
    └── statistiques_sociales.sql
``` 