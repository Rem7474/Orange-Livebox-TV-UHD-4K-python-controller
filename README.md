# Orange-Livebox-TV-UHD-4K-python-controller

Ce module permet de contrôler le décodeur TV UHD 4K Orange soit via une **interface graphique moderne (GUI)** complète, soit via la **ligne de commande (CLI)**.
Il nécessite les modules suivants : `requests` (et `tkinter` inclus par défaut avec Python).

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
  * Boutons d'accès direct en 1 clic pour les principales chaînes (TF1, France 2, France 3, Canal+, France 5, M6, Arte, C8, W9, TMC, BFM TV, CNews, L'Équipe...)
  * Recherche et filtrage en temps réel parmi toutes les chaînes disponibles (`epg_ids.json`)
  * Saisie directe d'un numéro ou code EPG
  * Double-clic dans la liste pour zapper instantanément
* **Détection Automatique du Décodeur (Hostname 'tv' & API)** :
  * Bouton **"🔍 Détecter IP"** : scanne le réseau local, identifie automatiquement le décodeur (recherche de nom d'hôte contenant "tv" ou réponse API) et configure l'adresse en 1 clic !
* **Configuration Facile & Persistance** :
  * Saisie manuelle ou détection automatique de l'IP/port
  * Sauvegarde automatique dans `config.json` (réutilisé automatiquement par le script CLI)
* **Module d'Exploration & Diagnostic (inspiré d'exploreTvOrange.py)** :
  * Bouton **"🔬 Exploration"** : ouvre une interface dédiée pour tester à l'aveugle des codes touches inconnus (appui court, long, maintien, scan automatique par plage), tester des modes/opérations brutes et des codes EPG personnalisés avec affichage JSON en direct.
* **Console de statut & Réactivité** :
  * Exécution asynchrone des requêtes réseau (l'application ne se fige jamais)
  * Journalisation détaillée des commandes envoyées et des retours API

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
   [Voir la liste des keys : le code donné à l'option peut être la valeur de la colonne CODE_INT ou CODE_STR.](https://github.com/DalFanajin/Orange-Livebox-TV-UHD-4K-python-controller/blob/master/keys.md)
	
* -e ou --epg_id :
   Obligatoire si -o ou --operation est égal à '9'.
   Correspond au code EPG de la chaîne que le décodeur TV doit afficher.
   
   Valeurs connues possibles :
   [Voir la liste des epg_ids : le code donné à l'option peut être la valeur de n'importe quelle colonne.](https://github.com/DalFanajin/Orange-Livebox-TV-UHD-4K-python-controller/blob/master/epg_ids.md)
   
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

## Concernant l'outil

[Un grand merci à tous les contributeurs du topic à cette addresse.](https://communaute.orange.fr/t5/TV-par-ADSL-et-Fibre/API-pour-commander-le-decodeur-TV-depusi-une-tablette/td-p/43443)

Je suis loin d'être un expert des outils utilisés par ce module : il peut présenter des erreurs, être incomplet, etc.
N'hésitez pas à le modifier, l'adapter, le partager, et l'utiliser quel que soit le contexte.

[Je vous serais reconnaissant de me transmettre les éventuelles améliorations/corrections à y apporter sur le repository github.](https://github.com/DalFanajin/Orange-Livebox-TV-UHD-4K-python-controller)

Etant donné que le décodeur est exclusivement français, je n'ai pas prévu de traduction anglaise les documentations associées : si elle est nécessaire, n'hésitez pas à me solliciter.
This decoder is a french product, so I didn't translate documentation files in english : do not hesitate to ask if you need a translation anyway.