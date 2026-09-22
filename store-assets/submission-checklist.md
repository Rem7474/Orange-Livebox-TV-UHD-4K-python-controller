# Checklist de soumission Play Console — Télécommande TV Orange

Guide pas à pas pour la toute première création de la fiche. Tous les fichiers référencés sont dans `store-assets/` sauf mention contraire.

## 1. Créer l'application

Play Console → Toutes les applications → Créer une application.
- Nom de l'app : `Télécommande TV Orange`
- Langue par défaut : Français
- Type : Application
- Gratuite
- Cocher les déclarations de politique développeur / export

## 2. Présence sur le Store → Fiche principale

| Champ | Valeur / source |
|---|---|
| Nom de l'app | `Télécommande TV Orange` |
| Description courte | Voir `listing-fr.md` (73 caractères) |
| Description complète | Voir `listing-fr.md` |
| Icône de l'app (512×512) | `play-store-icon-512.png` |
| Feature graphic (1024×500) | `feature-graphic.png` |
| Captures d'écran téléphone | `screenshots/*.png` — **brouillon web, voir note ci-dessous** |
| Catégorie | Outils |
| Coordonnées (email) | `contact@remcorp.fr` |
| Site web | `https://github.com/Rem7474/Orange-Livebox-TV-UHD-4K-python-controller` |

**Note sur les captures d'écran** : celles fournies sont un rendu web du vrai code de l'app (fidèle mais pas pris sur device réel), avec un artefact connu (icône radar affichée en "@"). Utilisables pour le test interne ; à remplacer par de vraies captures avant la promotion en production, comme recommandé par Google.

## 3. App content (Contenu de l'application)

Toutes les réponses détaillées sont dans `play-console-answers.md`. Résumé :

| Section | Réponse |
|---|---|
| Politique de confidentialité | `https://rem7474.github.io/Orange-Livebox-TV-UHD-4K-python-controller/privacy.html` |
| Sécurité des données (Data Safety) | Aucune collecte de données |
| Classification du contenu | Toutes réponses "Non" → classification la plus basse |
| Audience cible | Audience générale, pas destiné aux enfants |
| Publicités | Aucune |
| Accès à l'application | Toutes les fonctionnalités disponibles sans accès particulier |
| Compte développeur gouvernemental / financier | Sans objet |

## 4. Signature de l'application

Au tout premier upload d'AAB, Google proposera d'activer **Play App Signing** — accepter (recommandé : Google gère la clé de signature finale, l'upload continue de se faire avec la clé déjà configurée dans les secrets GitHub du repo).

## 5. Récupérer l'AAB signé

Déjà généré par la CI au tag `v1.1.5` :
👉 `https://github.com/Rem7474/Orange-Livebox-TV-UHD-4K-python-controller/releases/tag/v1.1.5`

Télécharger `TelecommandeTVOrange.aab` (vérifier son empreinte avec le `.sha256` fourni si besoin).

## 6. Premier envoi — Test interne (recommandé avant production)

Version → Tester → Version interne → Créer une version.
- Uploader l'AAB téléchargé à l'étape 5
- Nom de version / notes de version (ex. "Première version")
- Ajouter des testeurs (ton adresse email suffit pour commencer)
- Publier la version interne, installer via le lien de test, vérifier que tout fonctionne sur un vrai appareil

## 7. Promotion en production

Une fois le test interne validé (et les captures d'écran réelles mises à jour si tu le souhaites) : Version → Production → Promouvoir la version testée, ou créer une nouvelle version de production avec le même AAB.

## Ce qui reste de ton ressort

- Créer/remplir la fiche dans la Play Console (je n'y ai pas accès)
- Vérifier la sauvegarde du keystore de release (voir échange précédent)
- Prendre de vraies captures d'écran sur un appareil Android avant la promotion en production
