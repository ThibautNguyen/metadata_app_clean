# Metadata App

Application de gestion des métadonnées pour bases de données PostgreSQL.

## État actuel (11/04/2024)

### Fonctionnalités implémentées
1. Interface de saisie des métadonnées
   - Formulaire de saisie avec champs de base
   - Support pour le contenu CSV
   - Support pour le dictionnaire des variables
   - Validation des données

2. Catalogue des métadonnées
   - Affichage des métadonnées
   - Filtrage et recherche
   - Affichage détaillé des métadonnées

3. Base de données
   - Connexion à Neon.tech établie
   - Structure de la table metadata mise à jour avec colonnes JSONB

### Problèmes connus
1. Problème de sauvegarde des métadonnées
   - Les données saisies dans le formulaire n'apparaissent pas dans le catalogue
   - Possible problème dans la fonction save_metadata
   - Vérifier les logs pour plus de détails

2. Synchronisation avec la base de données
   - La connexion fonctionne (test de connexion réussi)
   - Les données ne semblent pas être sauvegardées dans la base
   - Vérifier la transaction SQL et le commit

### À faire pour la prochaine session
1. Déboguer la fonction save_metadata
   - Ajouter des logs détaillés
   - Vérifier la structure des données envoyées
   - Tester la requête SQL directement

2. Améliorer la gestion des erreurs
   - Ajouter plus de messages d'erreur explicites
   - Mettre en place un système de logging plus détaillé

3. Vérifier la structure de la base de données
   - Confirmer que la table a été mise à jour avec les nouvelles colonnes
   - Vérifier les contraintes et les types de données

## Configuration

### Base de données
- Host: ep-wispy-queen-abzi1lne-pooler.eu-west-2.aws.neon.tech
- Database: neondb
- User: neondb_owner
- SSL Mode: require

### Structure des données
```sql
CREATE TABLE metadata (
    id SERIAL PRIMARY KEY,
    nom_fichier VARCHAR(255) NOT NULL,
    nom_base VARCHAR(255),
    schema VARCHAR(255),
    description TEXT,
    date_creation DATE,
    date_maj DATE,
    source VARCHAR(255),
    frequence_maj VARCHAR(255),
    licence VARCHAR(255),
    envoi_par VARCHAR(255),
    contact VARCHAR(255),
    mots_cles TEXT,
    notes TEXT,
    contenu_csv JSONB,
    dictionnaire JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Notes de développement
- Branch principale : main
- Branch de développement : dev-metadata-app
- Déploiement : via Streamlit Cloud
- Repository : https://github.com/ThibautNguyen/DOCS 

## Fonctionnalités

- Saisie et consultation des métadonnées
- Support pour dictionnaires de variables volumineux
- Affichage des données CSV
- Flexibilité dans les séparateurs (virgule ou point-virgule)

## Déploiement sur Streamlit Cloud

1. Connectez-vous à [Streamlit Cloud](https://streamlit.io/cloud)
2. Créez une nouvelle application pointant vers ce dépôt
3. Utilisez la branche `main`
4. Spécifiez `Catalogue.py` comme fichier principal
5. Configurez les variables d'environnement suivantes :
   - `NEON_USER` = "neondb_owner"
   - `NEON_PASSWORD` = "npg_XsA4wfvHy2Rn"
   - `NEON_HOST` = "ep-wispy-queen-abzi1lne-pooler.eu-west-2.aws.neon.tech"
   - `NEON_DATABASE` = "neondb"

## Exécution locale

```
streamlit run Catalogue.py
```

## Structure du projet

- `Catalogue.py` : Point d'entrée principal pour la consultation des métadonnées
- `db_utils.py` : Fonctions d'accès à la base de données
- `pages/01_Saisie.py` : Interface de saisie des métadonnées
- `pages/03_Database_Inspector.py` : Outil d'inspection de la base de données 