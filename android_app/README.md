# Télécommande TV Orange (Android)

Application mobile Android moderne et autonome pour contrôler le décodeur **Orange Livebox TV UHD 4K** directement depuis votre smartphone connecté au Wi-Fi local.

> **Avertissement de non-affiliation :** cette application est un outil indépendant développé par RemCorp. Elle n'est ni affiliée, ni soutenue, ni éditée par la société Orange. « Orange » et « Livebox » sont des marques déposées de leurs propriétaires respectifs, mentionnées ici uniquement pour indiquer la compatibilité matérielle.

---

## ✨ Fonctionnalités

### 1. 📱 Télécommande Tactile Complète (Opération 1)
- **Alimentation (Power)** avec retour visuel de l'état (Allumé / Veille / Hors ligne).
- **Pavé Directionnel (D-Pad)** : Navigation Haut, Bas, Gauche, Droite et validation centrale **OK**.
- **Gestion du volume et des chaînes** : Double commande basculante (VOL+ / VOL-, CH+ / CH-) et mise en sourdine (**MUTE**).
- **Touches système** : Retour, Menu / Accueil, Guide TV (Programme), VOD, Enregistrer (**REC**).
- **Contrôles multimédias** : Lecture / Pause, Avance rapide, Retour rapide, Direct.
- **Pavé numérique escamotable** : Accès direct aux chiffres 0 à 9 en un tap.
- **Retour haptique** : Vibrations subtiles à chaque appui pour une sensation de télécommande physique.

### 2. 📺 Guide des Chaînes & Zapping Direct (Opération 9)
- Intégration de plus de **300 chaînes Orange TV** issues de `epg_ids.json`.
- **Recherche instantanée** par nom (ex: *TF1, Arte, Canal+*) ou par numéro de chaîne (ex: *1, 2, 7*).
- **Gestion des favoris** : Étoilez vos chaînes favorites pour les retrouver instantanément en haut de liste.
- **Zapping en 1 clic** : Changement immédiat de chaîne sur le téléviseur.

### 3. 🔍 Scan Réseau & Détection Automatique (Opération 10)
- **Recherche automatique** du ou des décodeurs sur le Wi-Fi (résolution DNS des noms d'hôtes `livebox-tv.home` et balayage HTTP du sous-réseau `192.168.1.x` sur le port 8080). Si plusieurs décodeurs sont détectés (foyer multi-TV), un sélecteur permet de choisir celui à configurer.
- **Statut en temps réel** : Nom du décodeur, état de marche/veille, contexte d'affichage (`LIVE`, `HOMEPAGE`).
- **Configuration manuelle** : Saisie personnalisée de l'adresse IP et du port avec bouton de test immédiat.
- **Persistance locale** : Paramètres sauvegardés automatiquement dans l'appareil.

---

## 🚀 Installation & Compilation

### Prérequis
- Smartphone ou émulateur Android (Android 5.0 Lollipop - API 21 minimum).
- Flutter SDK (>= 3.12.0).

### Lancer en mode développement
```bash
cd android_app
flutter pub get
flutter run
```

### Exécuter les tests unitaires
```bash
cd android_app
flutter test
```

### Compiler l'APK Release
```bash
cd android_app
flutter build apk --release
```
Le fichier généré se situe dans :
`build/app/outputs/flutter-apk/app-release.apk`

### Compiler l'AAB Release (format requis pour le Play Store)
```bash
cd android_app
flutter build appbundle --release
```
Le fichier généré se situe dans :
`build/app/outputs/bundle/release/app-release.aab`

---

## 🔒 Permissions utilisées

L'application ne collecte, ne stocke et ne transmet **aucune donnée personnelle** à un serveur externe : l'adresse IP/port du décodeur et la liste des chaînes favorites restent stockés localement sur l'appareil (`SharedPreferences`). Aucun SDK d'analytics, de publicité ou de tracking n'est intégré.

| Permission Android | Pourquoi |
|---|---|
| `INTERNET` | Envoyer les commandes HTTP au décodeur sur le réseau local (télécommande, zapping, statut). |
| `ACCESS_NETWORK_STATE`, `ACCESS_WIFI_STATE` | Vérifier la connectivité Wi-Fi avant de tenter une requête ou un scan. |
| `ACCESS_LOCAL_NETWORK` | Autoriser les requêtes HTTP vers des adresses IP privées (API Android 16+ dédiée à cet usage, remplace la géolocalisation historiquement requise pour le scan réseau). |
| `NEARBY_WIFI_DEVICES` (`neverForLocation`) | Découverte automatique du décodeur par scan du sous-réseau local, sans accès à la géolocalisation. |
| `CHANGE_WIFI_MULTICAST_STATE`, `CHANGE_NETWORK_STATE` | Fiabiliser la résolution réseau locale pendant le scan de découverte. |

Aucune permission de géolocalisation, caméra, contacts, stockage ou téléphonie n'est demandée.
