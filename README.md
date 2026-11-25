# Orange-Livebox-TV-UHD-4K-python-controller

[![CI](https://github.com/Rem7474/Orange-Livebox-TV-UHD-4K-python-controller/actions/workflows/ci.yml/badge.svg)](https://github.com/Rem7474/Orange-Livebox-TV-UHD-4K-python-controller/actions/workflows/ci.yml)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=Rem7474_Orange-Livebox-TV-UHD-4K-python-controller&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=Rem7474_Orange-Livebox-TV-UHD-4K-python-controller)
[![Release](https://img.shields.io/github/v/release/Rem7474/Orange-Livebox-TV-UHD-4K-python-controller?color=orange)](https://github.com/Rem7474/Orange-Livebox-TV-UHD-4K-python-controller/releases)
[![Dependabot](https://img.shields.io/badge/dependabot-activé-brightgreen?logo=dependabot)](https://github.com/Rem7474/Orange-Livebox-TV-UHD-4K-python-controller/network/updates)

Suite complète pour piloter et automatiser votre décodeur **Orange Livebox TV UHD 4K** sur votre réseau local. Ce projet propose désormais **3 solutions complémentaires** adaptées à tous vos usages :

| Solution | Plateforme | Technologie | Description |
|---|---|---|---|
| 🖥️ **Flutter Desktop** | Windows | Flutter (Dart) | Interface moderne 2 colonnes (télécommande + guide des chaînes) avec raccourcis clavier |
| 📱 **Mobile App** | Android (Smartphones & Tablettes) | Flutter (Dart) | Application mobile tactile fluide (D-Pad, volume/chaînes, près de 400 chaînes, scan Wi-Fi) |
| 🖥️ **Desktop GUI (Python)** | Windows, Linux, macOS | Python / Tkinter | Interface graphique légère avec télécommande virtuelle, zapping TNT & module d'exploration |
| ⌨️ **CLI Script** | Tous OS | Python standard | Outil en ligne de commande idéal pour scripts d'automatisation, raccourcis et cron |

---

## 🖥️ Interface Graphique (GUI)

Pour lancer l'interface graphique :
```bash
python tvOrangeGui.py
```
ou simplement :
```bash
python tvOrange.py
```

### 🚀 Exécutable Windows autonome (.exe)
Vous pouvez également utiliser l'application sans installer Python :
* **Téléchargement direct** : téléchargez **`LiveboxTVController.exe`** depuis la page des [Releases GitHub](https://github.com/Rem7474/Orange-Livebox-TV-UHD-4K-python-controller/releases) (fichier unique intégrant toutes les dépendances et chaînes).
* **Compilation locale** : double-cliquez sur **`build_exe.bat`** pour générer **`dist\LiveboxTVController.exe`** (le dossier `dist/` est ignoré par Git et n'est pas inclus dans le dépôt).

<img width="2880" height="1641" alt="image" src="https://github.com/user-attachments/assets/08812778-c3a2-4bde-9946-3f0158a0818b" />

### Fonctionnalités de l'Interface Graphique :
* **Télécommande virtuelle complète** :
  * Marche / Arrêt (POWER)
  * Pavé directionnel (Haut, Bas, Gauche, Droite, OK)
  * Menu, Retour, Direct, VOD, Prog
  * Contrôle du volume (Vol +, Vol -, Mute) et des chaînes (P +, P -)
  * Contrôles multimédia (Lecture/Pause, Avance, Retour, Enregistrement)
  * Pavé numérique complet (0 à 9)
  * Choix du mode d'appui : court (0), enfoncé (1), relâché (2)
* **Zapping Rapide TNT & Catalogue de Chaînes** :
  * Boutons d'accès direct en 1 clic pour les principales chaînes TNT (TF1, France 2, France 3, France 4, France 5, M6, Arte, W9, TMC, BFM TV, CNews, Franceinfo, T18, NOVO19)
  * Recherche et filtrage en temps réel parmi toutes les chaînes disponibles (`epg_ids.json`, actualisable via `python scripts/update_epg_ids.py`)
  * Saisie directe d'un numéro ou code EPG
  * Double-clic dans la liste pour zapper instantanément
* **Détection Automatique du Décodeur (Hostname 'tv' & API)** :
  * Bouton **"🔍 Détecter IP"** : scanne le réseau local, identifie automatiquement le décodeur (recherche de nom d'hôte contenant "tv" ou réponse API) et configure l'adresse en 1 clic !
* **Configuration Facile & Persistance** :
  * Saisie manuelle ou détection automatique de l'adresse IP (port `8080` fixe)
  * Sauvegarde automatique dans `config.json` (réutilisé automatiquement par le script CLI)
* **Module d'Exploration & Diagnostic (inspiré d'exploreTvOrange.py)** :
  * Bouton **"🔬 Exploration"** : ouvre une interface dédiée pour tester à l'aveugle des codes touches inconnus (appui court, long, maintien, scan automatique par plage), tester des modes/opérations brutes et des codes EPG personnalisés avec affichage JSON en direct.
* **Console de statut & Réactivité** :
  * Exécution asynchrone des requêtes réseau (l'application ne se fige jamais)
  * Journalisation détaillée des commandes envoyées et des retours API

---

## 📱 Application Multiplateforme Flutter (Android & Windows Desktop)

Une application moderne et autonome, nommée **Télécommande TV Orange**, est disponible dans le dossier [`android_app/`](android_app/). Elle fonctionne à la fois sur **Android** et sur **Windows Desktop** (interface responsive 2 colonnes avec raccourcis clavier : flèches, Entrée = OK, Échap/Retour = Retour, Espace = Lecture/Pause, `+/-` = Volume, `M` = Muet, `PageUp`/`PageDown` = Chaînes, `P` = Power, `H` = Menu, pavé numérique `0–9`). Voir le [README dédié](android_app/README.md) pour le détail, y compris l'avertissement de non-affiliation à Orange.

### ✨ Fonctionnalités Mobile :
* **Télécommande tactile intégrale** :
  * Marche / Veille avec voyant d'état interactif en temps réel (Vert = allumé, Rouge/Orange = veille ou hors-ligne).
  * Disque directionnel ergonomique (D-Pad : Haut, Bas, Gauche, Droite, OK).
  * Double commande basculante pour le volume (`VOL+`, `VOL-`, `MUTE`) et les chaînes (`CH+`, `CH-`).
  * Touches d'accès direct : Retour, Menu / Accueil, Guide TV, VOD, Enregistrement (`REC`).
  * Commandes multimédia : Lecture / Pause, Avance rapide, Retour rapide, Direct.
  * Clavier numérique escamotable (0 à 9) déployable en 1 tap.
  * **Retour haptique physique** : vibration subtile à chaque appui de touche.
* **Guide des Chaînes & Zapping instantané** :
  * Intégration de près de 400 chaînes Orange TV (397 chaînes uniques) avec numérotation TNT 2025/2026 officielle.
  * Recherche en temps réel par nom (ex: *TF1, Canal+, Arte*) ou par numéro de chaîne.
  * Mise en favoris (★) d'un clic pour épingler vos chaînes préférées en haut de la liste.
* **Détection Wi-Fi automatique** :
  * Détection en 1 clic de l'adresse IP de votre décodeur sans configuration manuelle (résolution DNS `livebox-tv.home` et scan de sous-réseau `192.168.1.x:8080`).
  * Affichage en direct du statut : nom du décodeur, contexte d'affichage (`LIVE`, `HOMEPAGE`), état d'alimentation.

### 📥 Comment installer l'application :
1. Rendez-vous sur la page des [Releases GitHub](https://github.com/Rem7474/Orange-Livebox-TV-UHD-4K-python-controller/releases).
2. Téléchargez **`TelecommandeTVOrange.apk`** (Android) ou **`TelecommandeTVOrange-Windows.zip`** (Windows Desktop, décompresser puis lancer `android_app.exe`).
3. Sur Android, ouvrez le fichier `.apk` téléchargé et autorisez l'installation depuis cette source si demandé.
4. Assurez-vous d'être connecté au même réseau Wi-Fi/Ethernet que votre décodeur Livebox TV : l'application détectera automatiquement votre décodeur !

### 🛠️ Compilation locale de l'APK :
```bash
cd android_app
flutter pub get
flutter test
flutter build apk --release
```
Le fichier généré sera disponible dans `android_app/build/app/outputs/flutter-apk/app-release.apk`.

---

## ⌨️ Utilisation en Ligne de Commande (CLI)

Développé et testé pour le décodeur TV UHD 4K Orange :

	Modèle : Livebox Fibre
	Version de firmware : 1.12.16
	Version de firmware Orange : g0-f-fr)
	
Développé et testé sur un système connecté au même réseau local que le décodeur TV :

	L'adresse IP locale de votre décodeur peut être détectée automatiquement (`python tvOrange.py -a`),
	configurée via la GUI (enregistrée dans `config.json`), ou définie dans la variable globale 'URL'.
	
## Options CLI :

* -a ou --auto :
   Optionnel.
   Sans argument.
   Recherche automatiquement l'adresse IP du décodeur TV sur le réseau local et met à jour `config.json`.

* -g ou --gui :
   Optionnel.
   Lance l'interface graphique (également le comportement par défaut sans aucun argument).

* -h ou --help :
   Optionnel.
   Sans argument.
   Permet d'afficher cette docstring.
		
* -v ou --verbose :
		Optionnel.
		Sans argument.
		Permet d'afficher les informations écrites dans la console par la méthode 'printVerbose', utilisée pour afficher les informations de déroulement du programme.
		
* -o ou --operation :
   Obligatoire.
   Spécifie l'instruction à envoyer au décodeur TV.
   
   Valeurs possibles :
   Valeur | Description
   --- | ---
   10 | affiche les informations système et l'état actuel du décodeur TV, enregistre les informations dans result.json
   9 | permet de se rendre sur une chaîne précise en indiquant un code EPG (Electronic Program Guide) en indiquant l'epg_id (-e ou --epg_id)
   1 | permet de simuler l'appui d'une touche sur la télécommande en indiquant le mode (-m ou --mode) et la key (-k ou --key)
			
* -m ou --mode :
   Obligatoire si -o ou --operation est égal à '1'.
   Correspond au mode d'appui du bouton correspondant à la touche de la télécommande.
   
   Valeurs possibles :
   Valeur | Description
   --- | ---
   0 | simule un appui court sur la touche de la télécommande (keyDown + keyUp)
   1 | simule un appui sur la touche de la télécommande sans relache du bouton (keyDown)
   2 | simule une relache du bouton de la touche de la télécommande (keyUp)
   
* -k ou --key :
   Obligatoire si -o ou --operation est égal à '1'.
   Correspond au 'code télécommande' du signal que l'on souhaite envoyer au décodeur TV.
   
   Valeurs connues possibles :
   [Voir la liste des keys : le code donné à l'option peut être la valeur de la colonne CODE_INT ou CODE_STR.](keys.md)
	
* -e ou --epg_id :
   Obligatoire si -o ou --operation est égal à '9'.
   Correspond au code EPG de la chaîne que le décodeur TV doit afficher.
   
   Valeurs connues possibles :
   [Voir la liste des epg_ids : le code donné à l'option peut être la valeur de n'importe quelle colonne.](epg_ids.md)
   
## Exemples
* Obtenir l'état du décodeur et l'enregistre dans result.json
`python3 tvOrange.py -o 10`

* Demander au décodeur TV la chaîne TF1 :
`python3 tvOrange.py -o 9 -e TF1`

* Appuyer une fois sur la touche On/Off de la télécommande :
`python3 tvOrange.py -o 1 -m 0 -k POWER`

* Enfoncer la touche Volume + de la télécommande :
`python3 tvOrange.py -o 1 -m 1 -k VOL+`

* Relacher la touche Volume + de la télécommande :
`python3 tvOrange.py -o 1 -m 2 -k VOL+`

---

## 🧪 Tests & CI/CD

Le projet intègre une chaîne d'intégration et de déploiement continus (CI/CD) complète et automatisée via GitHub Actions :

* **Tests unitaires Python (Matrix Linux & Windows, Python 3.10 à 3.13)** :
  ```bash
  pip install -r requirements-dev.txt
  ruff check --extend-exclude scripts .
  pytest -v tests/
  ```
* **Tests unitaires & Analyse mobile Flutter** :
  ```bash
  cd android_app
  flutter analyze
  flutter test
  ```
* **Qualité de code SonarCloud** :
  Analyse statique automatique validant la sécurité et la fiabilité du code (Quality Gate actif).
* **Surveillance automatique des dépendances (Dependabot)** :
  Scan hebdomadaire des bibliothèques Python (`pip`), des dépendances Flutter (`pub`) et Android (`gradle`), ainsi que des actions GitHub pour appliquer automatiquement les correctifs de sécurité.
* **Actualisation automatique des chaînes EPG (`update-epg.yml`)** :
  Workflow hebdomadaire (chaque lundi à 06h30 UTC, ou déclenchable manuellement) exécutant `scripts/update_epg_ids.py` et ouvrant automatiquement une Pull Request en cas de changement dans le catalogue Orange TV.
* **Publication automatique des Releases** :
  La création d'un tag git (ex: `v1.1.0`) déclenche automatiquement :
  - La compilation sous Windows de l'exécutable autonome `LiveboxTVController.exe`.
  - La compilation sous Ubuntu de l'application Android `TelecommandeTVOrange.apk`.
  - La génération des empreintes d'intégrité SHA-256 pour chaque fichier.
  - La publication directe sur la page des Releases GitHub.
  ```bash
  git tag v1.1.0
  git push origin v1.1.0
  ```

---

## Concernant l'outil

[Un grand merci à tous les contributeurs du topic à cette addresse.](https://communaute.orange.fr/t5/TV-par-ADSL-et-Fibre/API-pour-commander-le-decodeur-TV-depusi-une-tablette/td-p/43443)

Je suis loin d'être un expert des outils utilisés par ce module : il peut présenter des erreurs, être incomplet, etc.
N'hésitez pas à le modifier, l'adapter, le partager, et l'utiliser quel que soit le contexte.

[Je vous serais reconnaissant de me transmettre les éventuelles améliorations/corrections à y apporter sur le repository github.](https://github.com/Rem7474/Orange-Livebox-TV-UHD-4K-python-controller)

Etant donné que le décodeur est exclusivement français, je n'ai pas prévu de traduction anglaise les documentations associées : si elle est nécessaire, n'hésitez pas à me solliciter.
This decoder is a french product, so I didn't translate documentation files in english : do not hesitate to ask if you need a translation anyway.
