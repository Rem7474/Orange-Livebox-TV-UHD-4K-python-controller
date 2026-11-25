#!/usr/bin/env python3
"""
Tests unitaires pour le contrôleur TV Orange Livebox UHD 4K.
"""

import ast
import json
import os
import sys
from unittest.mock import MagicMock, patch

import pytest
import requests

# Ajouter le répertoire racine au PYTHONPATH
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

import livebox_core
import tvOrange
from tvOrangeGui import OrangeTVClient, discover_decoder_ip


def test_keys_json_integrity():
    """Vérifie que keys.json existe, est valide, sans doublons et contient les touches essentielles."""
    keys_path = os.path.join(ROOT_DIR, "keys.json")
    assert os.path.exists(keys_path), "keys.json doit exister"

    with open(keys_path, "r", encoding="utf-8") as f:
        pairs = json.load(f, object_pairs_hook=list)

    keys = [k for k, _ in pairs]
    assert len(keys) == len(set(keys)), (
        f"Doublons détectés dans keys.json : {[k for k in keys if keys.count(k) > 1]}"
    )

    data = dict(pairs)
    assert len(data) > 30, "keys.json doit contenir au moins 30 touches"

    for required in [
        "POWER",
        "VOL+",
        "VOL-",
        "MUTE",
        "UP",
        "DOWN",
        "LEFT",
        "RIGHT",
        "OK",
        "OK2",
        "PLAY/PAUSE",
        "PLAY/PAUSE2",
        "FFWD",
        "FFWD2",
        "MENU",
        "0",
        "1",
        "BACK2",
    ]:
        assert required in data, (
            f"La touche '{required}' doit être présente dans keys.json"
        )

    assert data["1"] == "513"
    assert data["BACK2"] == "1"
    assert data["OK"] == "352"
    assert data["OK2"] == "28"
    assert data["PLAY/PAUSE"] == "164"
    assert data["PLAY/PAUSE2"] == "207"
    assert data["FFWD"] == "159"
    assert data["FFWD2"] == "208"


def test_assets_in_sync_with_root():
    """Vérifie que android_app/assets/{keys,epg_ids}.json sont identiques aux fichiers racine."""
    root_keys_path = os.path.join(ROOT_DIR, "keys.json")
    android_keys_path = os.path.join(ROOT_DIR, "android_app", "assets", "keys.json")
    with open(root_keys_path, "rb") as f1, open(android_keys_path, "rb") as f2:
        assert f1.read() == f2.read(), (
            "keys.json et android_app/assets/keys.json doivent être identiques octet pour octet"
        )

    root_epg_path = os.path.join(ROOT_DIR, "epg_ids.json")
    android_epg_path = os.path.join(ROOT_DIR, "android_app", "assets", "epg_ids.json")
    with open(root_epg_path, "r", encoding="utf-8") as f1, open(
        android_epg_path, "r", encoding="utf-8"
    ) as f2:
        assert json.load(f1) == json.load(f2), (
            "epg_ids.json et android_app/assets/epg_ids.json doivent correspondre"
        )


def test_epg_ids_json_integrity():
    """Vérifie que epg_ids.json existe, est valide et contient les chaînes TNT 2025/2026."""
    epg_path = os.path.join(ROOT_DIR, "epg_ids.json")
    assert os.path.exists(epg_path), "epg_ids.json doit exister"

    with open(epg_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert isinstance(data, dict)
    assert len(data) > 300, "epg_ids.json doit contenir plus de 300 entrées"

    for ch in [
        "1",
        "2",
        "3",
        "4",
        "18",
        "19",
        "TF1",
        "FRANCE 2",
        "FRANCE 4",
        "M6",
        "ARTE",
        "T18",
        "NOVO19",
    ]:
        assert ch in data, f"La chaîne '{ch}' doit être présente dans epg_ids.json"

    assert data["4"] == "78"
    assert data["18"] == "4139"
    assert data["19"] == "4138"
    assert data["T18"] == "4139"
    assert data["NOVO19"] == "4138"


def test_livebox_core_has_no_tkinter_import():
    """Vérifie que livebox_core.py n'importe pas tkinter."""
    core_path = os.path.join(ROOT_DIR, "livebox_core.py")
    with open(core_path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=core_path)

    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])

    assert "tkinter" not in imported


def test_config_load_and_save_backwards_compat(tmp_path):
    """Vérifie load_config/save_config avec ou sans champ 'port'."""
    cfg_path = tmp_path / "config.json"

    # Sans fichier -> valeurs par défaut
    assert livebox_core.load_config(str(cfg_path)) == (
        livebox_core.DEFAULT_IP,
        livebox_core.DEFAULT_PORT,
    )

    # Ancien config sans port
    cfg_path.write_text(json.dumps({"ip": "192.168.1.42"}), encoding="utf-8")
    assert livebox_core.load_config(str(cfg_path)) == ("192.168.1.42", "8080")

    # Ancien config avec port personnalisé
    cfg_path.write_text(
        json.dumps({"ip": "192.168.1.42", "port": "9090"}), encoding="utf-8"
    )
    assert livebox_core.load_config(str(cfg_path)) == ("192.168.1.42", "9090")

    # save_config sans port -> DEFAULT_PORT
    livebox_core.save_config("192.168.1.99", config_file=str(cfg_path))
    saved = json.loads(cfg_path.read_text(encoding="utf-8"))
    assert saved == {"ip": "192.168.1.99", "port": "8080"}


def test_client_url_formatting():
    """Vérifie la construction correcte de l'URL du décodeur et les cas limites."""
    assert (
        OrangeTVClient(ip="192.168.1.15", port="8080").get_url()
        == "http://192.168.1.15:8080/remoteControl/cmd"
    )
    assert (
        OrangeTVClient(ip="http://192.168.1.50", port="8080").get_url()
        == "http://192.168.1.50:8080/remoteControl/cmd"
    )
    assert (
        OrangeTVClient(ip="https://192.168.1.50", port="8080").get_url()
        == "https://192.168.1.50:8080/remoteControl/cmd"
    )
    assert (
        OrangeTVClient(ip="http://192.168.1.15:8080", port="8080").get_url()
        == "http://192.168.1.15:8080/remoteControl/cmd"
    )
    assert (
        OrangeTVClient(ip="192.168.1.15:8080", port="8080").get_url()
        == "http://192.168.1.15:8080/remoteControl/cmd"
    )
    assert (
        OrangeTVClient(ip="192.168.1.15:9090", port="8080").get_url()
        == "http://192.168.1.15:9090/remoteControl/cmd"
    )
    assert (
        OrangeTVClient(ip="  192.168.1.15  ", port=" 8080 ").get_url()
        == "http://192.168.1.15:8080/remoteControl/cmd"
    )
    assert (
        OrangeTVClient(ip="  http://192.168.1.15:8080/  ", port="8080").get_url()
        == "http://192.168.1.15:8080/remoteControl/cmd"
    )


@patch("livebox_core.requests.get")
def test_client_send_key_mock(mock_get, tmp_path, monkeypatch):
    """Vérifie l'envoi d'une touche (Opération 1) sans écraser result.json."""
    result_path = tmp_path / "result.json"
    monkeypatch.setattr(livebox_core, "RESULT_FILE", str(result_path))

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
    _, kwargs = mock_get.call_args
    assert kwargs["params"]["operation"] == "1"
    assert kwargs["params"]["key"] == client.keys.get("POWER", "116")
    assert kwargs["params"]["mode"] == "0"
    assert not result_path.exists()


@patch("livebox_core.requests.get")
def test_client_change_channel_mock(mock_get, tmp_path, monkeypatch):
    """Vérifie le zapping sur une chaîne EPG (Opération 9) sans écraser result.json."""
    result_path = tmp_path / "result.json"
    monkeypatch.setattr(livebox_core, "RESULT_FILE", str(result_path))

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "result": {"responseCode": "0", "message": "ok", "data": {}}
    }
    mock_get.return_value = mock_resp

    client = OrangeTVClient("192.168.1.15", "8080")
    success, _data, err = client.change_channel("TF1")

    assert success is True
    assert err is None
    _, kwargs = mock_get.call_args
    assert kwargs["params"]["operation"] == "9"
    assert kwargs["params"]["epg_id"] == client.epg_ids.get("TF1", "192")
    assert kwargs["params"]["uui"] == 1
    assert not result_path.exists()


@patch("livebox_core.requests.get")
def test_client_get_status_mock(mock_get, tmp_path, monkeypatch):
    """Vérifie l'état système (Opération 10) et l'écriture de result.json."""
    result_path = tmp_path / "result.json"
    monkeypatch.setattr(livebox_core, "RESULT_FILE", str(result_path))

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "result": {
            "responseCode": "0",
            "message": "ok",
            "data": {"friendlyName": "Decodeur TV Orange", "osdContext": "LIVE"},
        }
    }
    mock_get.return_value = mock_resp

    client = OrangeTVClient("192.168.1.15", "8080")
    success, data, err = client.get_status()

    assert success is True
    assert err is None
    assert data["result"]["data"]["friendlyName"] == "Decodeur TV Orange"
    assert result_path.exists()


@patch("livebox_core.requests.get")
def test_client_error_handling(mock_get):
    """Vérifie la gestion des erreurs Timeout, ConnectionError, HTTP 500 et JSON invalide."""
    client = OrangeTVClient("192.168.1.15", "8080")

    # Timeout
    mock_get.side_effect = requests.exceptions.Timeout("timed out")
    ok, data, err = client.get_status()
    assert ok is False
    assert data is None
    assert "timeout" in err.lower()

    # ConnectionError
    mock_get.side_effect = requests.exceptions.ConnectionError("refused")
    ok, data, err = client.send_key("POWER")
    assert ok is False
    assert data is None
    assert "impossible" in err.lower()

    # HTTP 500
    resp_500 = MagicMock()
    resp_500.status_code = 500
    http_err = requests.exceptions.HTTPError("500 Server Error", response=resp_500)
    resp_500.raise_for_status.side_effect = http_err
    mock_get.side_effect = None
    mock_get.return_value = resp_500
    ok, data, err = client.get_status()
    assert ok is False
    assert data is None
    assert "500" in err

    # JSON invalide
    resp_bad_json = MagicMock()
    resp_bad_json.status_code = 200
    resp_bad_json.raise_for_status.return_value = None
    resp_bad_json.json.side_effect = ValueError("Expecting value")
    mock_get.return_value = resp_bad_json
    ok, data, err = client.get_status()
    assert ok is False
    assert data is None
    assert "json" in err.lower()


def test_discover_decoder_ip_dns_hit():
    """Vérifie discover_decoder_ip lorsque la résolution DNS trouve le décodeur."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "result": {
            "responseCode": "0",
            "message": "ok",
            "data": {"friendlyName": "Décodeur UHD"},
        }
    }

    with patch("livebox_core.socket.gethostbyname") as mock_dns, patch(
        "livebox_core.requests.get", return_value=mock_resp
    ) as mock_get:
        mock_dns.side_effect = (
            lambda host: "192.168.1.25" if host == "livebox-tv.home" else (_ for _ in ()).throw(OSError("nope"))
        )
        messages = []
        ip, port, info = discover_decoder_ip(progress_cb=messages.append)

    assert ip == "192.168.1.25"
    assert port == "8080"
    assert "Décodeur UHD" in info
    assert mock_get.called
    assert len(messages) >= 1


def test_discover_decoder_ip_arp_hit():
    """Vérifie discover_decoder_ip via cache ARP sans invocation shell=True."""
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "result": {
            "responseCode": "0",
            "message": "ok",
            "data": {"friendlyName": "Livebox TV Salon"},
        }
    }

    udp_sock = MagicMock()
    udp_sock.getsockname.return_value = ("192.168.1.10", 12345)
    tcp_sock = MagicMock()
    tcp_sock.connect_ex.return_value = 0

    def socket_factory(family, sock_type):
        if sock_type == livebox_core.socket.SOCK_DGRAM:
            return udp_sock
        return tcp_sock

    with patch("livebox_core.socket.gethostbyname", side_effect=OSError("no dns")), patch(
        "livebox_core.socket.socket", side_effect=socket_factory
    ), patch(
        "livebox_core.subprocess.check_output",
        return_value="  192.168.1.33          aa-bb-cc-dd-ee-ff     dynamic\n",
    ) as mock_arp, patch(
        "livebox_core.requests.get", return_value=mock_resp
    ):
        ip, port, info = discover_decoder_ip()

    assert ip == "192.168.1.33"
    assert port == "8080"
    assert info == "Livebox TV Salon"
    mock_arp.assert_called_with(["arp", "-a"], text=True, errors="ignore")


def test_cli_argument_parsing():
    """Vérifie le parseur argparse de tvOrange.py."""
    tvOrange.VERBOSE = False
    args1 = tvOrange.parse_args(["-o", "10", "-v"])
    assert args1.operation == "10"
    assert args1.verbose is True
    assert tvOrange.VERBOSE is True

    tvOrange.VERBOSE = False
    args2 = tvOrange.parse_args(["-a"])
    assert args2.auto is True
    assert args2.gui is False

    tvOrange.VERBOSE = False
    args3 = tvOrange.parse_args(["-v", "-g"])
    assert args3.verbose is True
    assert args3.gui is True

    # Opération invalide -> SystemExit non nul
    with pytest.raises(SystemExit) as exc:
        tvOrange.main(["-o", "999"])
    assert exc.value.code != 0

    # Touche inconnue -> SystemExit non nul
    with pytest.raises(SystemExit) as exc_key:
        tvOrange.main(["-o", "1", "-m", "0", "-k", "TOUCHE_INCONNUE"])
    assert exc_key.value.code != 0

    # EPG inconnu -> SystemExit non nul
    with pytest.raises(SystemExit) as exc_epg:
        tvOrange.main(["-o", "9", "-e", "CHAINE_INCONNUE"])
    assert exc_epg.value.code != 0


def test_gui_app_initialization():
    """Vérifie que OrangeTVApp et ExploreDialog s'initialisent correctement avec Tkinter."""
    if sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
        pytest.skip(
            "Environnement d'affichage graphique non disponible (Linux headless sans DISPLAY)"
        )

    import tvOrangeGui

    app = tvOrangeGui.OrangeTVApp()
    channel_count = len(app.all_channels)
    assert not hasattr(app, "port_var"), "Le champ Port doit être retiré de l'UI"
    assert app.current_port == "8080"
    labels = [lbl for lbl, _ in app.top_channels]
    assert "4 - France 4" in labels
    assert "18 - T18" in labels
    assert "19 - NOVO19" in labels
    assert "8 - C8" not in labels
    for _, epg_key in app.top_channels:
        assert epg_key in app.client.epg_ids, f"Raccourci TNT manquant dans epg_ids.json : {epg_key}"

    dlg = tvOrangeGui.ExploreDialog(app, app.client)
    assert dlg.protocol("WM_DELETE_WINDOW") != ""
    dlg.on_close()
    assert dlg.stop_scan_flag is True

    app.update()
    app.destroy()

    assert channel_count > 300, "L'application doit avoir chargé plus de 300 chaînes"
