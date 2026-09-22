# Réponses suggérées — Formulaires Play Console

Document de référence pour remplir les formulaires du Play Console au moment de la soumission (compte développeur pas encore validé au moment de la rédaction). À vérifier/adapter selon l'état réel de l'app à ce moment-là, notamment si de nouvelles fonctionnalités ont été ajoutées entre-temps.

## Data Safety (Sécurité des données)

**Question initiale : "Votre application collecte-t-elle ou partage-t-elle l'un des types de données utilisateur requis ?"**
→ **Non** — aucune collecte de données.

Justification (à garder en tête si le formulaire redemande des détails) :
- Aucune donnée n'est transmise à un serveur (l'app ne communique qu'avec le décodeur TV sur le réseau local, jamais avec Internet).
- Aucun SDK tiers d'analytics, de publicité ou de crash reporting.
- Les seules données stockées (IP/port du décodeur, chaînes favorites) restent en local sur l'appareil via `SharedPreferences`, jamais transmises.
- Pas de compte utilisateur, pas d'identifiant publicitaire utilisé.

**Chiffrement des données en transit** : sans objet (pas de données transmises à un serveur externe ; les échanges avec le décodeur se font en HTTP sur le réseau local uniquement).

**Suppression des données** : se fait par désinstallation de l'app ou effacement des données dans les paramètres Android (pas de compte à supprimer côté serveur, puisqu'il n'y a pas de serveur).

## Content Rating (Classification du contenu / questionnaire IARC)

Catégorie d'app : **Utilitaires / Outils**.

Toutes les questions du questionnaire IARC concernant violence, contenu sexuel, langage grossier, contenu généré par les utilisateurs, jeux d'argent simulés, interactions sociales, partage de localisation, achats intégrés, etc. → **Non / Aucun**.

Résultat attendu : classification la plus basse disponible (PEGI 3 / Everyone selon les régions).

## Target Audience (Audience cible)

- Tranche d'âge : **audience générale**, pas de ciblage spécifique moins de 13 ans (l'app n'a pas de contenu ni de fonctionnalité pensée pour les enfants).
- Ne pas cocher "S'adresse principalement aux enfants" (évite les contraintes COPPA/Families Policy supplémentaires, non pertinentes ici).

## Ads (Publicités)

**Non**, l'application ne contient aucune publicité.

## App Access (Accès à l'application)

**"Toutes les fonctionnalités sont disponibles sans accès particulier"** — pas de compte, pas de connexion, pas de contenu restreint. Aucune information d'identification à fournir aux testeurs Google.

## Government apps / COVID-19 / Financial features

Sans objet pour cette app — répondre Non/N/A à ces sections si présentes.

## Permissions déclarées (rappel pour la section correspondante)

Voir le détail et la justification dans [`android_app/README.md`](../android_app/README.md#-permissions-utilisées) : `INTERNET`, `ACCESS_NETWORK_STATE`, `ACCESS_WIFI_STATE`, `ACCESS_LOCAL_NETWORK`, `NEARBY_WIFI_DEVICES` (neverForLocation), `CHANGE_WIFI_MULTICAST_STATE`, `CHANGE_NETWORK_STATE`. Aucune permission sensible (localisation, caméra, contacts, stockage, téléphonie).
