"""
Module cœur (sans dépendance Tkinter) pour le contrôleur de Décodeur TV UHD 4K Orange.
Fournit :
- Résolution des chemins (script standard et PyInstaller --onefile)
- Chargement/sauvegarde de la configuration (config.json)
- Client HTTP OrangeTVClient
- Découverte automatique de l'adresse IP du décodeur sur le réseau local
"""

import json
import logging
import os
import re
import socket
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit

import requests

logger = logging.getLogger(__name__)

# Chemins d'accès (compatibles script Python standard depuis n'importe quel CWD et PyInstaller --onefile)
if getattr(sys, "frozen", False):
    BUNDLE_DIR = sys._MEIPASS
    APP_DIR = os.path.dirname(sys.executable)
else:
    BUNDLE_DIR = os.path.dirname(os.path.abspath(__file__))
    APP_DIR = BUNDLE_DIR

CONFIG_FILE = os.path.join(APP_DIR, "config.json")
RESULT_FILE = os.path.join(APP_DIR, "result.json")

# Les données peuvent être dans le dossier de l'exécutable ou embarquées dans le bundle
KEYS_FILE = (
    os.path.join(APP_DIR, "keys.json")
    if os.path.exists(os.path.join(APP_DIR, "keys.json"))
    else os.path.join(BUNDLE_DIR, "keys.json")
)
EPG_IDS_FILE = (
    os.path.join(APP_DIR, "epg_ids.json")
    if os.path.exists(os.path.join(APP_DIR, "epg_ids.json"))
    else os.path.join(BUNDLE_DIR, "epg_ids.json")
)

DEFAULT_IP = "192.168.1.15"  # NOSONAR
DEFAULT_PORT = "8080"


def load_config(config_file=None):
    """Charge l'IP et le port depuis config.json (rétrocompatible avec ou sans champ 'port')."""
    path = config_file or CONFIG_FILE
    ip = DEFAULT_IP
    port = DEFAULT_PORT
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            if isinstance(cfg, dict):
                raw_ip = str(cfg.get("ip") or "").strip()
                raw_port = str(cfg.get("port") or "").strip()
                if raw_ip:
                    ip = raw_ip
                if raw_port:
                    port = raw_port
        except (OSError, json.JSONDecodeError, ValueError) as e:
            logger.debug("Impossible de lire %s : %s", path, e)
    return ip, port


def save_config(ip, port=None, config_file=None):
    """Sauvegarde l'IP (et le port par défaut 8080 si absent/vide) dans config.json."""
    path = config_file or CONFIG_FILE
    clean_ip = str(ip or "").strip() or DEFAULT_IP
    clean_port = str(port or "").strip() or DEFAULT_PORT
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"ip": clean_ip, "port": clean_port}, f, indent=2)
    return clean_ip, clean_port


def _detect_local_subnet():
    """Détermine le préfixe /24 du sous-réseau local via socket UDP."""
    for target in (("8.8.8.8", 80), ("192.168.1.1", 80)):  # NOSONAR
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.connect(target)
            local_ip = sock.getsockname()[0]
            if local_ip and not local_ip.startswith("127."):
                return ".".join(local_ip.split(".")[:3])
        except OSError as e:
            logger.debug("Détection sous-réseau via %s impossible : %s", target, e)
        finally:
            if sock is not None:
                sock.close()
    return "192.168.1"


def _get_arp_ips(subnet):
    """Récupère les IPs du cache ARP local sans invoquer de shell."""
    arp_out = ""
    for cmd in (["arp", "-a"], ["ip", "neigh"]):
        try:
            arp_out = subprocess.check_output(cmd, text=True, errors="ignore")
            if arp_out:
                break
        except (OSError, subprocess.SubprocessError) as e:
            logger.debug("Commande %s indisponible : %s", cmd, e)

    if not arp_out:
        return []

    found = re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", arp_out)
    prefix = f"{subnet}."
    return list(
        dict.fromkeys(
            ip
            for ip in found
            if ip.startswith(prefix) and not ip.endswith(".255") and not ip.endswith(".1")
        )
    )


def discover_decoder_ip(progress_cb=None):
    """
    Recherche automatique de l'IP du décodeur TV :
    1. Résolution DNS de noms d'hôtes courants contenant 'tv'.
    2. Analyse du cache ARP local et des adresses actives du sous-réseau.
    3. Résolution DNS inverse pour vérifier si le hostname contient 'tv'.
    4. Test direct de l'API Livebox TV sur le port 8080 avec vérification du friendlyName.
    """
    if progress_cb:
        progress_cb("Recherche par nom d'hôte DNS...")

    dns_candidates = [
        "livebox-tv.home",
        "decodeur-tv.home",
        "tv.home",
        "decodeurtv.home",
        "livebox-tv",
        "decodeur-tv",
        "tv",
        "orange-tv.home",
        "orangetv.home",
    ]
    for host in dns_candidates:
        try:
            ip = socket.gethostbyname(host)
            r = requests.get(
                f"http://{ip}:8080/remoteControl/cmd",  # NOSONAR
                params={"operation": 10},
                timeout=1.0,
            )
            if r.status_code == 200:
                fname = (
                    r.json()
                    .get("result", {})
                    .get("data", {})
                    .get("friendlyName", host)
                )
                return ip, DEFAULT_PORT, f"Hostname DNS '{host}' ({fname})"
        except (OSError, requests.RequestException, ValueError) as e:
            logger.debug("Hôte DNS %s non résolu : %s", host, e)

    subnet = _detect_local_subnet()

    if progress_cb:
        progress_cb(f"Analyse des périphériques du réseau {subnet}.x...")

    arp_ips = _get_arp_ips(subnet)

    def probe_single_ip(ip):
        # A. Test port 8080 & API Livebox TV
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.3)
            res = sock.connect_ex((ip, 8080))
            if res == 0:
                r = requests.get(
                    f"http://{ip}:8080/remoteControl/cmd",  # NOSONAR
                    params={"operation": 10},
                    timeout=0.8,
                )
                if r.status_code == 200:
                    data = r.json()
                    res_obj = data.get("result", {})
                    if (
                        res_obj.get("message") == "ok"
                        or res_obj.get("responseCode") == "0"
                    ):
                        fname = res_obj.get("data", {}).get(
                            "friendlyName", "Décodeur TV Orange"
                        )
                        return ip, DEFAULT_PORT, fname
        except (OSError, requests.RequestException, ValueError) as e:
            logger.debug("Sonde IP %s échouée : %s", ip, e)
        finally:
            if sock is not None:
                sock.close()

        # B. Test DNS inverse : est-ce que le hostname contient 'tv' ?
        try:
            h, _, _ = socket.gethostbyaddr(ip)
            if "tv" in h.lower():
                return ip, DEFAULT_PORT, f"Hostname: {h}"
        except OSError as e:
            logger.debug("DNS inverse %s échoué : %s", ip, e)

        return None

    if arp_ips:
        with ThreadPoolExecutor(max_workers=20) as ex:
            for match in ex.map(probe_single_ip, arp_ips):
                if match:
                    return match

    if progress_cb:
        progress_cb(
            f"Balayage approfondi du sous-réseau {subnet}.1 à {subnet}.254..."
        )

    arp_set = set(arp_ips)
    all_ips = [f"{subnet}.{i}" for i in range(1, 255) if f"{subnet}.{i}" not in arp_set]
    with ThreadPoolExecutor(max_workers=40) as ex:
        for match in ex.map(probe_single_ip, all_ips):
            if match:
                return match

    return None, None, None


class OrangeTVClient:
    """Gestionnaire de communication avec l'API du décodeur Orange."""

    def __init__(self, ip=DEFAULT_IP, port=DEFAULT_PORT):
        self.ip = ip
        self.port = port
        self.keys = {}
        self.epg_ids = {}
        self.load_data()

    def get_url(self):
        raw = str(self.ip or "").strip() or DEFAULT_IP
        if "://" not in raw:
            raw = f"http://{raw}"  # NOSONAR

        parsed = urlsplit(raw)
        scheme = parsed.scheme or "http"
        netloc = parsed.netloc.rstrip("/")

        clean_port = str(self.port or DEFAULT_PORT).strip() or DEFAULT_PORT
        try:
            has_port = parsed.port is not None
        except ValueError:
            has_port = False

        if not has_port:
            netloc = netloc.rstrip(":")
            netloc = f"{netloc}:{clean_port}"

        return f"{scheme}://{netloc}/remoteControl/cmd"

    def load_data(self):
        if os.path.exists(KEYS_FILE):
            try:
                with open(KEYS_FILE, "r", encoding="utf-8") as f:
                    self.keys = json.load(f)
            except (OSError, json.JSONDecodeError, ValueError) as e:
                print(f"Erreur chargement keys.json: {e}")

        if os.path.exists(EPG_IDS_FILE):
            try:
                with open(EPG_IDS_FILE, "r", encoding="utf-8") as f:
                    self.epg_ids = json.load(f)
            except (OSError, json.JSONDecodeError, ValueError) as e:
                print(f"Erreur chargement epg_ids.json: {e}")

    def send_key(self, key_name_or_code, mode=0, timeout=3.0):
        """Opération 1: envoie une touche."""
        key_str = str(key_name_or_code)
        target_key = self.keys.get(key_str, key_str)
        params = {
            "operation": "1",
            "key": target_key,
            "mode": str(mode),
        }
        return self._send_request(params, timeout, save_result=False)

    def change_channel(self, channel_or_epg, timeout=3.0):
        """Opération 9: change de chaîne par code EPG ou nom."""
        chan_str = str(channel_or_epg)
        epg_id = self.epg_ids.get(chan_str, chan_str)
        params = {
            "operation": "9",
            "epg_id": epg_id,
            "uui": 1,
        }
        return self._send_request(params, timeout, save_result=False)

    def get_status(self, timeout=3.0):
        """Opération 10: statut et infos système."""
        params = {"operation": "10"}
        return self._send_request(params, timeout, save_result=True)

    def send_raw_operation(
        self, operation, extra_params=None, timeout=3.0, save_result=False
    ):
        """Opération générique : teste un mode ou une opération avec paramètres optionnels."""
        params = {"operation": str(operation)}
        if extra_params and isinstance(extra_params, dict):
            params.update(extra_params)
        return self._send_request(params, timeout, save_result=save_result)

    def send_key_long_press(self, key_name_or_code, duration=0.2, timeout=3.0):
        """Simule un appui long : mode 1 (enfoncer), attente, puis mode 2 (relâcher)."""
        ok, data, err = self.send_key(key_name_or_code, mode=1, timeout=timeout)
        if not ok:
            return ok, data, err
        time.sleep(duration)
        return self.send_key(key_name_or_code, mode=2, timeout=timeout)

    def _send_request(self, params, timeout, save_result=False):
        url = self.get_url()
        try:
            resp = requests.get(url, params=params, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            if save_result:
                try:
                    with open(RESULT_FILE, "w", encoding="utf-8") as outfile:
                        json.dump(data, outfile, indent=2)
                except OSError as e:
                    logger.debug("Impossible d'écrire %s : %s", RESULT_FILE, e)
            return True, data, None
        except requests.exceptions.Timeout:
            return (
                False,
                None,
                f"Délai d'attente dépassé (timeout {timeout}s) pour {url}",
            )
        except requests.exceptions.ConnectionError:
            return (
                False,
                None,
                f"Connexion impossible au décodeur ({url}). Vérifiez l'adresse IP et le réseau.",
            )
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else "?"
            return False, None, f"Erreur HTTP {status} pour {url} : {e}"
        except ValueError:
            return False, None, f"Réponse JSON invalide reçue de {url}"
        except requests.RequestException as e:
            return False, None, f"Erreur de communication : {e}"
