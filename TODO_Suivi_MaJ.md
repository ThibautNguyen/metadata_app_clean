# TODO - Suivi MàJ et évolutions du catalogue

## 1. Nouvelle page Streamlit : Suivi MàJ
- Créer une page `pages/Suivi_MaJ.py` avec le titre "Suivi de la mise à jour des données".
- Objectifs :
  - Suivre les mises à jour des sources open data (INSEE, Ministère du Logement, etc.)
  - Alerter quand une nouvelle version est publiée
  - Garder en mémoire l'historique des versions
  - Permettre l'intégration de ce suivi dans le catalogue des métadonnées

## 2. Modifications du formulaire de saisie (01_Saisie.py)
- Déplacer le champ "Dernière mise à jour" sous sa position actuelle, à droite de "Granularité géographique*".
- Ajouter un champ "Date de publication" (type DATE) à la place de "Dernière mise à jour".
- Ajouter un champ "Nom du jeu de données" (menu déroulant) juste sous le titre "Informations de base" :
  - Options : "Autre" (en premier), puis tous les jeux de données existants pour le producteur sélectionné.
  - Si "Autre" est sélectionné, afficher un champ texte pour saisir un nouveau nom.
  - Infobulle : "Nom de jeu de données, tel que défini par l'organisme producteur".
- Le champ "Producteur de la donnée" doit passer en première ligne du formulaire, fonctionner comme "Nom du jeu de données" (menu déroulant, "Autre" en premier, champ texte si "Autre").
- Ajouter un champ "Date estimative de la prochaine publication" (type DATE) sous "Fréquence de mises à jour des données" :
  - Cette date est calculée automatiquement à partir de "Date de publication" et "Fréquence de mise à jour des données" (modifiable manuellement si besoin).

## 3. Modifications de la base de données (metadata)
- Structure actuelle à respecter :

```sql
CREATE TABLE metadata (
    id SERIAL PRIMARY KEY,
    type_donnees VARCHAR(50),
    nom_jeu_donnees VARCHAR(255),
    producteur VARCHAR(255),
    nom_table VARCHAR(255),
    nom_base VARCHAR(255) NOT NULL,
    schema VARCHAR(255),
    description TEXT,
    granularite_geo VARCHAR(100),
    millesime DATE,
    date_publication DATE,
    date_maj DATE,
    date_prochaine_publication DATE,
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

## 4. Logique dynamique à implémenter dans le formulaire
- Le menu "Nom du jeu de données" doit afficher uniquement les jeux de données liés au producteur sélectionné.
- Si "Autre" est sélectionné dans un menu, afficher un champ texte pour la saisie manuelle.
- Le champ "Date estimative de la prochaine publication" doit être calculé automatiquement selon la fréquence et la date de publication.

## 5. Points à valider ou à discuter
- Historique des versions : table dédiée ou champ JSON ?
- Type d'alerte pour les nouvelles versions (affichage, email, etc.)
- Possibilité de modification manuelle de la date estimative de prochaine publication.

---

**Ce fichier sert de référence pour la reprise des développements.**
N'hésite pas à le compléter ou à le modifier lors de la prochaine session. 