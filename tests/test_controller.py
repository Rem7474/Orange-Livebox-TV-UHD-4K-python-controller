#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests unitaires pour le contrôleur TV Orange Livebox UHD 4K.
"""

import os
import sys
import json
import pytest
from unittest.mock import patch, MagicMock

# Ajouter le répertoire racine au PYTHONPATH
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from tvOrangeGui import OrangeTVClient, discover_decoder_ip
import tvOrange


def test_keys_json_integrity():
    """Vérifie que keys.json existe, est valide et contient les touches essentielles."""
    keys_path = os.path.join(ROOT_DIR, "keys.json")
    assert os.path.exists(keys_path), "keys.json doit exister"
    
    with open(keys_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    assert isinstance(data, dict)
    assert len(data) > 30, "keys.json doit contenir au moins 30 touches"
    
    # Touches indispensables
    for required in ["POWER", "VOL+", "VOL-", "MUTE", "UP", "DOWN", "LEFT", "RIGHT", "OK", "MENU", "0", "1"]:
        assert required in data, f"La touche '{required}' doit être présente dans keys.json"


def test_epg_ids_json_integrity():
    """Vérifie que epg_ids.json existe, est valide et contient les chaînes majeures."""
    epg_path = os.path.join(ROOT_DIR, "epg_ids.json")
    assert os.path.exists(epg_path), "epg_ids.json doit exister"
    
    with open(epg_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    assert isinstance(data, dict)
    assert len(data) > 100, "epg_ids.json doit contenir plus de 100 entrées"
    
    # Chaînes majeures
    for ch in ["1", "2", "3", "TF1", "FRANCE 2", "M6", "ARTE"]:
        assert ch in data, f"La chaîne '{ch}' doit être présente dans epg_ids.json"


def test_client_url_formatting():
    """Vérifie la construction correcte de l'URL du décodeur."""
    client1 = OrangeTVClient(ip="192.168.1.15", port="8080")
    assert client1.get_url() == "http://192.168.1.15:8080/remoteControl/cmd"

    client2 = OrangeTVClient(ip="http://192.168.1.50", port="8080")
    assert client2.get_url() == "http://192.168.1.50:8080/remoteControl/cmd"


@patch("requests.get")
def test_client_send_key_mock(mock_get):
    """Vérifie l'envoi d'une commande de touche (Opération 1)."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "result": {"responseCode": "0", "message": "ok", "data": {}}
    }
    mock_get.return_value = mock_resp

    client = OrangeTVClient("192.168.1.15", "8080")
    success, data, err = client.send_key("POWER", mode=0)

    assert success is True
    assert err is None
    assert data["result"]["responseCode"] == "0"
    mock_get.assert_called_once()
    args, kwargs = mock_get.call_args
    assert kwargs["params"]["operation"] == "1"
    assert kwargs["params"]["key"] == client.keys.get("POWER", "116")
    assert kwargs["params"]["mode"] == "0"


@patch("requests.get")
def test_client_change_channel_mock(mock_get):
    """Vérifie le zapping sur une chaîne EPG (Opération 9)."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "result": {"responseCode": "0", "message": "ok", "data": {}}
    }
    mock_get.return_value = mock_resp

    client = OrangeTVClient("192.168.1.15", "8080")
    success, data, err = client.change_channel("TF1")

    assert success is True
    assert err is None
    args, kwargs = mock_get.call_args
    assert kwargs["params"]["operation"] == "9"
    assert kwargs["params"]["epg_id"] == client.epg_ids.get("TF1", "192")
    assert kwargs["params"]["uui"] == 1


@patch("requests.get")
def test_client_get_status_mock(mock_get):
    """Vérifie la récupération de l'état système (Opération 10)."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "result": {
            "responseCode": "0",
            "message": "ok",
            "data": {"friendlyName": "Decodeur TV Orange", "osdContext": "LIVE"}
        }
    }
    mock_get.return_value = mock_resp

    client = OrangeTVClient("192.168.1.15", "8080")
    success, data, err = client.get_status()

    assert success is True
    assert data["result"]["data"]["friendlyName"] == "Decodeur TV Orange"


def test_cli_argument_parsing():
    """Vérifie le bon fonctionnement du parseur CLI de tvOrange.py."""
    opts, args = tvOrange.checkArgs(["-o", "10", "-v"])
    flags = [f[0] for f in opts]
    assert "-o" in flags
    assert "-v" in flags

    op, key, mode, epg = tvOrange.getFlagsAndValues(opts)
    assert op == "10"

    opts2, _ = tvOrange.checkArgs(["-a"])
    flags2 = [f[0] for f in opts2]
    assert "-a" in flags2


def test_gui_app_initialization():
    """Vérifie que la classe OrangeTVApp s'initialise correctement avec Tkinter."""
    if sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
        pytest.skip("Environnement d'affichage graphique non disponible (Linux headless sans DISPLAY)")

    import tvOrangeGui
    channel_count = 0
    try:
        app = tvOrangeGui.OrangeTVApp()
        channel_count = len(app.all_channels)
        app.update()
        app.destroy()
    except Exception as e:
        pytest.fail(f"Échec de l'initialisation de l'application graphique : {e}")

    assert channel_count > 300, "L'application doit avoir chargé plus de 300 chaînes"
