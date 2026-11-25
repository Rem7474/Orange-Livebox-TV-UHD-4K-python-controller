"""
Ce module permet de contrôler le décodeur TV orange via la ligne de commande Unix/Windows d'un système.
Il nécessite le module requests (et livebox_core).

Développé et testé pour le décodeur TV UHD 4K Orange :

	Modèle : Livebox Fibre
	Version de firmware : 1.12.16
	Version de firmware Orange : g0-f-fr

Options :

	-h ou --help :
		Optionnel. Affiche l'aide de la ligne de commande.

	-g ou --gui :
		Optionnel. Lance l'interface graphique (également lancée par défaut sans aucun argument).

	-a ou --auto :
		Optionnel. Recherche automatiquement l'adresse IP du décodeur TV sur le réseau local et met à jour config.json.

	-v ou --verbose :
		Optionnel. Affiche les informations détaillées de déroulement du programme.

	-o ou --operation :
		Obligatoire (sauf -g/-a). Spécifie l'instruction à envoyer au décodeur TV :
			10 : affiche les informations système et l'état actuel du décodeur TV (sauvegarde result.json).
			9  : permet de se rendre sur une chaîne précise via -e / --epg_id.
			1  : simule l'appui d'une touche via -m / --mode et -k / --key.

	-m ou --mode :
		Obligatoire si -o / --operation vaut '1' (0 = court, 1 = maintien, 2 = relâche).

	-k ou --key :
		Obligatoire si -o / --operation vaut '1' (voir keys.json / keys.md).

	-e ou --epg_id :
		Obligatoire si -o / --operation vaut '9' (voir epg_ids.json / epg_ids.md).
"""

import argparse
import sys

from livebox_core import (
    CONFIG_FILE,
    EPG_IDS_FILE,
    KEYS_FILE,
    OrangeTVClient,
    discover_decoder_ip,
    load_config,
    save_config,
)

VERBOSE = False

__all__ = [
    "CONFIG_FILE",
    "EPG_IDS_FILE",
    "KEYS_FILE",
    "VERBOSE",
    "build_parser",
    "getFullResult",
    "main",
    "parse_args",
    "printError",
    "printVerbose",
]


def build_parser():
    """Construit le parseur d'arguments argparse pour la CLI tvOrange."""
    parser = argparse.ArgumentParser(
        prog="tvOrange.py",
        description="Contrôleur en ligne de commande pour le décodeur TV UHD 4K Orange.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Affiche les informations détaillées dans la console.",
    )
    parser.add_argument(
        "-a",
        "--auto",
        action="store_true",
        help="Recherche automatiquement l'IP du décodeur TV et met à jour config.json.",
    )
    parser.add_argument(
        "-g",
        "--gui",
        action="store_true",
        help="Lance l'interface graphique Tkinter.",
    )
    parser.add_argument(
        "-o",
        "--operation",
        type=str,
        default="",
        help="Opération à exécuter : '1' (touche), '9' (chaîne EPG), '10' (état).",
    )
    parser.add_argument(
        "-m",
        "--mode",
        type=str,
        default="",
        help="Mode d'appui pour -o 1 : '0' (court), '1' (maintien), '2' (relâche).",
    )
    parser.add_argument(
        "-k",
        "--key",
        type=str,
        default="",
        help="Code ou nom de touche pour -o 1 (voir keys.json).",
    )
    parser.add_argument(
        "-e",
        "--epg_id",
        type=str,
        default="",
        help="Identifiant ou nom de chaîne EPG pour -o 9 (voir epg_ids.json).",
    )
    return parser


def parse_args(argv):
    """Parse les arguments CLI via argparse et met à jour VERBOSE si demandé."""
    global VERBOSE
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.verbose:
        VERBOSE = True
        printVerbose("Verbose ON")
    return args


def getFullResult(data):
    """Extrait responseCode, message et data depuis la réponse JSON du décodeur."""
    if not isinstance(data, dict) or not isinstance(data.get("result"), dict):
        raise TypeError("Structure JSON inattendue dans la réponse du décodeur.")
    res = data["result"]
    result_code = res.get("responseCode")
    result_message = res.get("message", "")
    result_data = res.get("data", {})
    if result_code is None:
        raise ValueError("Champ 'responseCode' manquant dans la réponse du décodeur.")

    printVerbose(
        f"Code réponse:{result_code}\nMessage:{result_message}\nDonnées:{result_data}"
    )
    return result_code, result_message, result_data


def printVerbose(text):
    if VERBOSE:
        print(f"\033[1;34;40m{text}\033[0m")


def printError(text):
    print(f"\033[1;31;40m{text}\033[0m", file=sys.stderr)


def main(argv=None):
    global VERBOSE
    if argv is None:
        argv = sys.argv[1:]

    if len(argv) == 0:
        try:
            import tvOrangeGui

            tvOrangeGui.main()
            sys.exit(0)
        except Exception as e:  # noqa: BLE001
            printError(f"Erreur lors du lancement de l'interface graphique : {e}")
            sys.exit(1)

    VERBOSE = False
    args = parse_args(argv)

    if args.gui:
        try:
            import tvOrangeGui

            tvOrangeGui.main()
            sys.exit(0)
        except Exception as e:  # noqa: BLE001
            printError(f"Erreur lors du lancement de l'interface graphique : {e}")
            sys.exit(1)

    if args.auto:
        print("Recherche automatique du décodeur TV sur le réseau...")
        ip, port, info = discover_decoder_ip(lambda m: print(f"  {m}"))
        if ip:
            print("\nDécodeur TV trouvé avec succès !")
            print(f"  Adresse IP : {ip}")
            print(f"  Port       : {port}")
            print(f"  Détail     : {info}")
            save_config(ip, port)
            print(f"Configuration sauvegardée dans '{CONFIG_FILE}'.")
            sys.exit(0)
        else:
            printError("Aucun décodeur TV détecté sur le réseau local.")
            sys.exit(1)

    operation = args.operation.strip()
    if operation not in ("1", "9", "10"):
        printError(
            "L'opération (-o ou --operation) doit être '1', '9' ou '10'. "
            "Utilisez -h ou --help pour obtenir plus d'informations."
        )
        sys.exit(1)

    ip, port = load_config()
    client = OrangeTVClient(ip, port)

    if operation == "1":
        if not args.key:
            printError("L'option -k / --key est obligatoire avec -o 1.")
            sys.exit(1)
        if args.mode not in ("0", "1", "2"):
            printError(
                "L'option -m / --mode doit être '0', '1' ou '2' avec -o 1."
            )
            sys.exit(1)
        if not client.keys:
            printError(f"Impossible de charger la table des touches ({KEYS_FILE}).")
            sys.exit(1)
        if args.key not in client.keys:
            printError(
                f"Touche inconnue : '{args.key}'. Consultez keys.json ou keys.md."
            )
            sys.exit(1)
        printVerbose(f"-o:{operation}\n-k:{args.key}\n-m:{args.mode}")
        success, result, err = client.send_key(args.key, mode=int(args.mode))

    elif operation == "9":
        if not args.epg_id:
            printError("L'option -e / --epg_id est obligatoire avec -o 9.")
            sys.exit(1)
        if not client.epg_ids:
            printError(
                f"Impossible de charger la table des chaînes ({EPG_IDS_FILE})."
            )
            sys.exit(1)
        if args.epg_id not in client.epg_ids:
            printError(
                f"EPG ID ou chaîne inconnue : '{args.epg_id}'. Consultez epg_ids.json ou epg_ids.md."
            )
            sys.exit(1)
        printVerbose(f"-o:{operation}\n-e:{args.epg_id}")
        success, result, err = client.change_channel(args.epg_id)

    else:  # operation == "10"
        printVerbose(f"-o:{operation}")
        success, result, err = client.get_status()

    if not success:
        printError(err or "Erreur de communication avec le décodeur.")
        sys.exit(1)

    try:
        result_code, _, _ = getFullResult(result)
    except (TypeError, ValueError) as e:
        printError(f"Réponse invalide du décodeur : {e}")
        sys.exit(1)

    try:
        exit_code = int(result_code)
    except (TypeError, ValueError):
        exit_code = 1

    sys.exit(exit_code)


if __name__ == "__main__":
    main(sys.argv[1:])
