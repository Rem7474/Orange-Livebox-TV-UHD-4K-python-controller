"""
Ce module permet d'explorer les possibilités de l'API du décodeur TV UHD 4K Orange
(touches, modes/opérations, codes EPG).
"""

import time

import requests

from livebox_core import OrangeTVClient, load_config

_ip, _port = load_config()
URL = OrangeTVClient(_ip, _port).get_url()
REQUEST_TIMEOUT = 3.0


def explore_keys():
    for key in range(1, 1000):
        print(f"On lance l'opération 1, appui simple, touche {key}")
        params = {"operation": 1, "key": key, "mode": 0}
        r = requests.get(url=URL, params=params, timeout=REQUEST_TIMEOUT)
        getFullResult(r.json())

        waitForUser("Press enter to continue")

        print(f"On lance l'opération 1, appui long (200ms), touche {key}")
        print("On appuie")
        params = {"operation": 1, "key": key, "mode": 1}
        r = requests.get(url=URL, params=params, timeout=REQUEST_TIMEOUT)
        getFullResult(r.json())

        time.sleep(0.2)

        print("On relache")
        params = {"operation": 1, "key": key, "mode": 2}
        r = requests.get(url=URL, params=params, timeout=REQUEST_TIMEOUT)
        getFullResult(r.json())

        waitForUser("Press enter to continue")


def fast_explore_simple_keys_except_list():
    notin = {
        116, 512, 513, 514, 515, 516, 517, 518, 519, 520, 521,
        402, 403, 115, 114, 113, 103, 108, 105, 106, 352, 158,
        139, 164, 168, 159, 167, 393, 1, 28, 72, 75, 77, 80,
        166, 207, 208, 365, 407, 408, 412, 529, 582,
    }
    for key in range(1, 1001):
        if key not in notin:
            print(f"On lance l'opération 1, appui simple, touche {key}")
            params = {"operation": 1, "key": key, "mode": 0}
            r = requests.get(url=URL, params=params, timeout=REQUEST_TIMEOUT)
            getFullResult(r.json())


def explore_modes():
    for mode in range(1, 1001):
        print(f"On lance l'opération {mode}")
        params = {"operation": mode}
        r = requests.get(url=URL, params=params, timeout=REQUEST_TIMEOUT)
        if getFullResult(r.json()) == "ok":
            waitForUser("Press enter to continue")


def explore_epg_ids():
    # Bruteforcé jusqu'à 11000, à reprendre une nuit
    for epg_id in range(11000, 9999999999):
        epg_code = (10 - len(str(epg_id))) * "*" + str(epg_id)
        print(f"On lance la chaine d'EPG {epg_code}")
        params = {"operation": 9, "epg_id": epg_code, "uui": 1}

        loop = True
        while loop:
            r = requests.get(url=URL, params=params, timeout=REQUEST_TIMEOUT)
            if getFullResult(r.json()) == "ok":
                if waitForUser("Press enter to continue, some other key to try again") == "":
                    loop = False
            else:
                loop = False


def trySendingTwoDigitsInARow():
    params = {"operation": 1, "key": 519, "mode": 1}
    requests.get(url=URL, params=params, timeout=REQUEST_TIMEOUT)

    params = {"operation": 1, "key": 512, "mode": 0}
    requests.get(url=URL, params=params, timeout=REQUEST_TIMEOUT)

    params = {"operation": 1, "key": 519, "mode": 2}
    requests.get(url=URL, params=params, timeout=REQUEST_TIMEOUT)


def getFullResult(data):
    resultCode = data["result"]["responseCode"]
    resultMessage = data["result"]["message"]
    resultData = data["result"]["data"]
    print(f"Code réponse:{resultCode}\nMessage:{resultMessage}\nDonnées:{resultData}")
    return resultMessage


def waitForUser(text):
    return input(text)


if __name__ == "__main__":
    print(
        "exploreTvOrange.py - Module d'exploration API Livebox TV.\n"
        f"URL configurée : {URL}\n"
        "Fonctions disponibles : explore_keys(), fast_explore_simple_keys_except_list(), "
        "explore_modes(), explore_epg_ids(), trySendingTwoDigitsInARow().\n"
        "Importez ce module ou utilisez l'onglet 'Exploration' de tvOrangeGui.py."
    )
