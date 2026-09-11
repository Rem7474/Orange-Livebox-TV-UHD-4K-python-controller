#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Interface Graphique pour le contrôleur de Décodeur TV UHD 4K Orange.
Permet de piloter la Livebox TV sans utiliser la ligne de commande :
- Télécommande virtuelle ergonomique
- Recherche et zapping direct sur les chaînes
- Détection automatique de l'IP du décodeur (hostname contenant 'tv' / port 8080)
- Configuration et persistance de l'IP
- Consultation du statut et informations système
- Exécution asynchrone pour une réactivité maximale
"""

import os
import sys
import json
import re
import socket
import subprocess
import threading
import requests
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# Dossier du script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(SCRIPT_DIR, "config.json")
KEYS_FILE = os.path.join(SCRIPT_DIR, "keys.json")
EPG_IDS_FILE = os.path.join(SCRIPT_DIR, "epg_ids.json")
RESULT_FILE = os.path.join(SCRIPT_DIR, "result.json")

# Palette graphique moderne (Style Orange & Sombre épuré)
THEME = {
    "bg": "#1e1e24",
    "card_bg": "#2a2a32",
    "card_border": "#3c3c46",
    "accent": "#f16e00",       # Orange Livebox
    "accent_hover": "#ff7900",
    "accent_active": "#d95f00",
    "text": "#ffffff",
    "text_muted": "#a0a0ab",
    "power_btn": "#e53935",
    "power_hover": "#ef5350",
    "btn_bg": "#383844",
    "btn_hover": "#4a4a58",
    "btn_active": "#575768",
    "btn_text": "#f5f5f7",
    "entry_bg": "#18181c",
    "success": "#4caf50",
    "error": "#f44336",
    "warning": "#ff9800",
    "console_bg": "#141417",
    "console_text": "#cfcfd6",
}

DEFAULT_IP = "192.168.1.15"
DEFAULT_PORT = "8080"


def discover_decoder_ip(progress_cb=None):
    """
    Recherche automatique de l'IP du décodeur TV :
    1. Résolution DNS de noms d'hôtes courants contenant 'tv' (livebox-tv, decodeur-tv, tv...).
    2. Analyse du cache ARP local et des adresses actives du sous-réseau.
    3. Résolution DNS inverse (reverse lookup) pour vérifier si le hostname contient 'tv'.
    4. Test direct de l'API Livebox TV sur le port 8080 avec vérification du friendlyName.
    """
    if progress_cb:
        progress_cb("Recherche par nom d'hôte DNS...")

    # 1. Noms d'hôtes courants contenant 'tv'
    dns_candidates = [
        "livebox-tv.home", "decodeur-tv.home", "tv.home", "decodeurtv.home",
        "livebox-tv", "decodeur-tv", "tv", "orange-tv.home", "orangetv.home"
    ]
    for host in dns_candidates:
        try:
            ip = socket.gethostbyname(host)
            # Vérifier si le décodeur répond bien sur le port 8080
            r = requests.get(f"http://{ip}:8080/remoteControl/cmd", params={"operation": 10}, timeout=1.0)
            if r.status_code == 200:
                fname = r.json().get("result", {}).get("data", {}).get("friendlyName", host)
                return ip, "8080", f"Hostname DNS '{host}' ({fname})"
        except Exception:
            pass

    # 2. Détermination du sous-réseau local (ex: 192.168.1)
    subnet = "192.168.1"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("192.168.1.1", 80))
        local_ip = s.getsockname()[0]
        s.close()
        subnet = ".".join(local_ip.split(".")[:3])
    except Exception:
        pass

    if progress_cb:
        progress_cb(f"Analyse des périphériques du réseau {subnet}.x...")

    # 3. Récupération des IPs du cache ARP
    arp_ips = []
    try:
        arp_out = subprocess.check_output("arp -a", shell=True, text=True, errors="ignore")
        found = re.findall(r"(\d+\.\d+\.\d+\.\d+)", arp_out)
        arp_ips = [
            ip for ip in found
            if ip.startswith(subnet) and not ip.endswith(".255") and not ip.endswith(".1")
        ]
    except Exception:
        pass

    def probe_single_ip(ip):
        # A. Test port 8080 & API Livebox TV (ultra rapide et fiable)
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(0.3)
            res = sock.connect_ex((ip, 8080))
            sock.close()
            if res == 0:
                r = requests.get(f"http://{ip}:8080/remoteControl/cmd", params={"operation": 10}, timeout=0.8)
                if r.status_code == 200:
                    data = r.json()
                    res_obj = data.get("result", {})
                    if res_obj.get("message") == "ok" or res_obj.get("responseCode") == "0":
                        fname = res_obj.get("data", {}).get("friendlyName", "Décodeur TV Orange")
                        return ip, "8080", fname
        except Exception:
            pass

        # B. Test DNS inverse : est-ce que le hostname contient 'tv' ?
        try:
            h, _, _ = socket.gethostbyaddr(ip)
            if "tv" in h.lower():
                return ip, "8080", f"Hostname: {h}"
        except Exception:
            pass

        return None

    # Test prioritaire sur les adresses actives de l'ARP cache
    if arp_ips:
        with ThreadPoolExecutor(max_workers=20) as ex:
            for match in ex.map(probe_single_ip, arp_ips):
                if match:
                    return match

    # 4. Balayage complet du sous-réseau en tâche de fond si non trouvé dans l'ARP
    if progress_cb:
        progress_cb(f"Balayage approfondi du sous-réseau {subnet}.1 à {subnet}.254...")

    all_ips = [f"{subnet}.{i}" for i in range(1, 255) if f"{subnet}.{i}" not in arp_ips]
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
        clean_ip = self.ip.strip()
        if clean_ip.startswith("http://") or clean_ip.startswith("https://"):
            return f"{clean_ip}:{self.port}/remoteControl/cmd"
        return f"http://{clean_ip}:{self.port}/remoteControl/cmd"

    def load_data(self):
        if os.path.exists(KEYS_FILE):
            try:
                with open(KEYS_FILE, "r", encoding="utf-8") as f:
                    self.keys = json.load(f)
            except Exception as e:
                print(f"Erreur chargement keys.json: {e}")

        if os.path.exists(EPG_IDS_FILE):
            try:
                with open(EPG_IDS_FILE, "r", encoding="utf-8") as f:
                    self.epg_ids = json.load(f)
            except Exception as e:
                print(f"Erreur chargement epg_ids.json: {e}")

    def send_key(self, key_name_or_code, mode=0, timeout=3.0):
        """Opération 1: envoie une touche."""
        key_str = str(key_name_or_code)
        target_key = self.keys.get(key_str, key_str)
        params = {
            "operation": "1",
            "key": target_key,
            "mode": str(mode)
        }
        return self._send_request(params, timeout)

    def change_channel(self, channel_or_epg, timeout=3.0):
        """Opération 9: change de chaîne par code EPG ou nom."""
        chan_str = str(channel_or_epg)
        epg_id = self.epg_ids.get(chan_str, chan_str)
        params = {
            "operation": "9",
            "epg_id": epg_id,
            "uui": 1
        }
        return self._send_request(params, timeout)

    def get_status(self, timeout=3.0):
        """Opération 10: statut et infos système."""
        params = {"operation": "10"}
        return self._send_request(params, timeout)

    def _send_request(self, params, timeout):
        url = self.get_url()
        try:
            resp = requests.get(url, params=params, timeout=timeout)
            resp.raise_for_status()
            data = resp.json()
            try:
                with open(RESULT_FILE, "w", encoding="utf-8") as outfile:
                    json.dump(data, outfile, indent=2)
            except Exception:
                pass
            return True, data, None
        except requests.exceptions.Timeout:
            return False, None, f"Délai d'attente dépassé (timeout {timeout}s) pour {url}"
        except requests.exceptions.ConnectionError:
            return False, None, f"Connexion impossible au décodeur ({url}). Vérifiez l'adresse IP et le réseau."
        except Exception as e:
            return False, None, f"Erreur de communication : {str(e)}"


class OrangeTVApp(tk.Tk):
    """Application graphique principale."""

    def __init__(self):
        super().__init__()
        self.title("Contrôleur TV Orange Livebox UHD 4K")
        self.geometry("1020x780")
        self.minsize(920, 700)
        self.configure(bg=THEME["bg"])

        # Config client
        self.load_config()
        self.client = OrangeTVClient(self.current_ip, self.current_port)

        # Variables UI
        self.ip_var = tk.StringVar(value=self.current_ip)
        self.port_var = tk.StringVar(value=self.current_port)
        self.mode_var = tk.IntVar(value=0)  # 0: court, 1: enfoncer, 2: relâcher
        self.search_chan_var = tk.StringVar()
        self.direct_chan_var = tk.StringVar()
        self.status_text_var = tk.StringVar(value="Prêt - En attente d'une commande")
        self.is_discovering = False

        self.setup_styles()
        self.build_ui()
        self.load_channels_to_tree()

    def load_config(self):
        self.current_ip = DEFAULT_IP
        self.current_port = DEFAULT_PORT
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    self.current_ip = cfg.get("ip", DEFAULT_IP)
                    self.current_port = str(cfg.get("port", DEFAULT_PORT))
            except Exception:
                pass

    def save_config(self, show_popup=True):
        new_ip = self.ip_var.get().strip()
        new_port = self.port_var.get().strip()
        if not new_ip:
            if show_popup:
                messagebox.showwarning("Adresse IP vide", "Veuillez renseigner une adresse IP valide.")
            return

        self.current_ip = new_ip
        self.current_port = new_port or DEFAULT_PORT
        self.client.ip = self.current_ip
        self.client.port = self.current_port

        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump({"ip": self.current_ip, "port": self.current_port}, f, indent=2)
            self.log(f"Configuration sauvegardée : {self.current_ip}:{self.current_port}", "info")
            if show_popup:
                messagebox.showinfo("Configuration", "Adresse IP enregistrée avec succès.")
        except Exception as e:
            self.log(f"Erreur lors de la sauvegarde de la configuration : {e}", "error")

    def setup_styles(self):
        self.style = ttk.Style(self)
        self.style.theme_use("clam")

        self.style.configure(
            "Treeview",
            background=THEME["entry_bg"],
            foreground=THEME["text"],
            fieldbackground=THEME["entry_bg"],
            rowheight=26,
            font=("Segoe UI", 10),
            borderwidth=0
        )
        self.style.configure(
            "Treeview.Heading",
            background=THEME["card_bg"],
            foreground=THEME["text"],
            font=("Segoe UI", 10, "bold"),
            relief="flat"
        )
        self.style.map(
            "Treeview",
            background=[("selected", THEME["accent"])],
            foreground=[("selected", "#ffffff")]
        )
        self.style.map(
            "Treeview.Heading",
            background=[("active", THEME["btn_hover"])]
        )

        self.style.configure(
            "Vertical.TScrollbar",
            background=THEME["card_bg"],
            troughcolor=THEME["bg"],
            arrowcolor=THEME["text_muted"]
        )

    def build_ui(self):
        # En-tête / Barre supérieure
        top_bar = tk.Frame(self, bg=THEME["card_bg"], height=64, padx=16, pady=10)
        top_bar.pack(fill=tk.X, side=tk.TOP)

        title_frame = tk.Frame(top_bar, bg=THEME["card_bg"])
        title_frame.pack(side=tk.LEFT, fill=tk.Y)

        dot = tk.Canvas(title_frame, width=16, height=16, bg=THEME["card_bg"], highlightthickness=0)
        dot.create_oval(2, 2, 14, 14, fill=THEME["accent"], outline="")
        dot.pack(side=tk.LEFT, padx=(0, 8))

        lbl_title = tk.Label(
            title_frame, text="LIVEBOX TV",
            font=("Segoe UI", 14, "bold"), fg=THEME["text"], bg=THEME["card_bg"]
        )
        lbl_title.pack(side=tk.LEFT)

        lbl_sub = tk.Label(
            title_frame, text="UHD 4K",
            font=("Segoe UI", 10), fg=THEME["accent"], bg=THEME["card_bg"]
        )
        lbl_sub.pack(side=tk.LEFT, padx=(6, 0))

        # Zone configuration IP, Auto-détection & Statut
        cfg_frame = tk.Frame(top_bar, bg=THEME["card_bg"])
        cfg_frame.pack(side=tk.RIGHT)

        tk.Label(
            cfg_frame, text="IP :", font=("Segoe UI", 10),
            fg=THEME["text_muted"], bg=THEME["card_bg"]
        ).pack(side=tk.LEFT, padx=(8, 2))

        ip_entry = tk.Entry(
            cfg_frame, textvariable=self.ip_var, width=14, font=("Consolas", 10),
            bg=THEME["entry_bg"], fg=THEME["text"], insertbackground=THEME["text"],
            relief="flat", highlightthickness=1, highlightbackground=THEME["card_border"]
        )
        ip_entry.pack(side=tk.LEFT, padx=3, ipady=3)

        tk.Label(
            cfg_frame, text="Port :", font=("Segoe UI", 10),
            fg=THEME["text_muted"], bg=THEME["card_bg"]
        ).pack(side=tk.LEFT, padx=(4, 2))

        port_entry = tk.Entry(
            cfg_frame, textvariable=self.port_var, width=5, font=("Consolas", 10),
            bg=THEME["entry_bg"], fg=THEME["text"], insertbackground=THEME["text"],
            relief="flat", highlightthickness=1, highlightbackground=THEME["card_border"]
        )
        port_entry.pack(side=tk.LEFT, padx=3, ipady=3)

        # Bouton Auto-détection de l'IP
        self.btn_auto_detect = self.create_button(
            cfg_frame, text="🔍 Détecter IP", command=self.action_auto_detect_ip,
            bg=THEME["btn_bg"], fg="#64b5f6", px=8, py=3, font=("Segoe UI", 9, "bold")
        )
        self.btn_auto_detect.pack(side=tk.LEFT, padx=4)

        btn_save = self.create_button(
            cfg_frame, text="Sauvegarder", command=self.save_config,
            bg=THEME["btn_bg"], fg=THEME["btn_text"], px=8, py=3
        )
        btn_save.pack(side=tk.LEFT, padx=4)

        btn_info = self.create_button(
            cfg_frame, text="État Décodeur (Op 10)", command=self.action_get_status,
            bg=THEME["accent"], fg="#ffffff", px=9, py=3
        )
        btn_info.pack(side=tk.LEFT, padx=4)

        # Corps principal : 2 colonnes
        main_content = tk.Frame(self, bg=THEME["bg"], padx=14, pady=12)
        main_content.pack(fill=tk.BOTH, expand=True)

        # Colonne Gauche : Télécommande Virtuelle
        remote_card = tk.Frame(
            main_content, bg=THEME["card_bg"], bd=0, padx=18, pady=16,
            highlightthickness=1, highlightbackground=THEME["card_border"]
        )
        remote_card.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        self.build_remote_control(remote_card)

        # Colonne Droite : Onglets / Panneau Chaînes + Infos
        right_panel = tk.Frame(main_content, bg=THEME["bg"])
        right_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.build_right_panel(right_panel)

        # Pied de page : Console / Logs & Status Bar
        self.build_bottom_panel()

    def build_remote_control(self, parent):
        # 1. En-tête : Titre & Bouton Power
        header_remote = tk.Frame(parent, bg=THEME["card_bg"])
        header_remote.pack(fill=tk.X, pady=(0, 12))

        lbl = tk.Label(
            header_remote, text="TÉLÉCOMMANDE",
            font=("Segoe UI", 11, "bold"), fg=THEME["text"], bg=THEME["card_bg"]
        )
        lbl.pack(side=tk.LEFT)

        btn_power = tk.Button(
            header_remote, text="⏻ POWER", font=("Segoe UI", 10, "bold"),
            bg=THEME["power_btn"], fg="#ffffff", activebackground=THEME["power_hover"],
            activeforeground="#ffffff", relief="flat", cursor="hand2", padx=12, pady=4,
            command=lambda: self.action_send_key("POWER")
        )
        btn_power.pack(side=tk.RIGHT)

        # 2. Mode d'appui (3 colonnes uniformes)
        mode_frame = tk.LabelFrame(
            parent, text="Mode d'appui", font=("Segoe UI", 9),
            bg=THEME["card_bg"], fg=THEME["text_muted"], padx=8, pady=4,
            relief="solid", bd=1
        )
        mode_frame.pack(fill=tk.X, pady=(0, 12))
        for c in range(3):
            mode_frame.columnconfigure(c, weight=1, uniform="mode_col")

        rb_short = tk.Radiobutton(
            mode_frame, text="Court (0)", variable=self.mode_var, value=0,
            bg=THEME["card_bg"], fg=THEME["text"], selectcolor=THEME["card_bg"],
            activebackground=THEME["card_bg"], activeforeground=THEME["accent"],
            font=("Segoe UI", 8)
        )
        rb_short.grid(row=0, column=0, sticky="w")

        rb_down = tk.Radiobutton(
            mode_frame, text="Maintien (1)", variable=self.mode_var, value=1,
            bg=THEME["card_bg"], fg=THEME["text"], selectcolor=THEME["card_bg"],
            activebackground=THEME["card_bg"], activeforeground=THEME["accent"],
            font=("Segoe UI", 8)
        )
        rb_down.grid(row=0, column=1, sticky="w")

        rb_up = tk.Radiobutton(
            mode_frame, text="Relâche (2)", variable=self.mode_var, value=2,
            bg=THEME["card_bg"], fg=THEME["text"], selectcolor=THEME["card_bg"],
            activebackground=THEME["card_bg"], activeforeground=THEME["accent"],
            font=("Segoe UI", 8)
        )
        rb_up.grid(row=0, column=2, sticky="w")

        # 3. Touches Fonctions (4 colonnes uniformes, pleine largeur)
        fn_row = tk.Frame(parent, bg=THEME["card_bg"])
        fn_row.pack(fill=tk.X, pady=(0, 10))
        for c in range(4):
            fn_row.columnconfigure(c, weight=1, uniform="fn_col")

        self.create_remote_btn(fn_row, "MENU", "MENU").grid(row=0, column=0, sticky="nsew", padx=2, ipady=3)
        self.create_remote_btn(fn_row, "RETOUR", "BACK").grid(row=0, column=1, sticky="nsew", padx=2, ipady=3)
        self.create_remote_btn(fn_row, "DIRECT", "DIRECT").grid(row=0, column=2, sticky="nsew", padx=2, ipady=3)
        self.create_remote_btn(fn_row, "VOD", "VOD").grid(row=0, column=3, sticky="nsew", padx=2, ipady=3)

        # 4. Pavé Directionnel (D-Pad en croix 3x3 parfaitement symétrique)
        dpad_outer = tk.Frame(parent, bg=THEME["card_bg"], pady=4)
        dpad_outer.pack(fill=tk.X, pady=(0, 10))

        dpad_frame = tk.Frame(dpad_outer, bg=THEME["card_bg"])
        dpad_frame.pack(anchor=tk.CENTER)

        for i in range(3):
            dpad_frame.columnconfigure(i, weight=1, uniform="dp_c")
            dpad_frame.rowconfigure(i, weight=1, uniform="dp_r")

        # Haut
        self.create_remote_btn(dpad_frame, "▲", "UP", width=5, height=2, font=("Segoe UI", 11, "bold")).grid(
            row=0, column=1, sticky="nsew", padx=3, pady=3
        )
        # Gauche
        self.create_remote_btn(dpad_frame, "◀", "LEFT", width=5, height=2, font=("Segoe UI", 11, "bold")).grid(
            row=1, column=0, sticky="nsew", padx=3, pady=3
        )
        # OK (au centre, orange)
        self.create_remote_btn(
            dpad_frame, "OK", "OK", width=5, height=2, bg=THEME["accent"], fg="#ffffff",
            active_bg=THEME["accent_hover"], font=("Segoe UI", 11, "bold")
        ).grid(row=1, column=1, sticky="nsew", padx=3, pady=3)
        # Droite
        self.create_remote_btn(dpad_frame, "▶", "RIGHT", width=5, height=2, font=("Segoe UI", 11, "bold")).grid(
            row=1, column=2, sticky="nsew", padx=3, pady=3
        )
        # Bas
        self.create_remote_btn(dpad_frame, "▼", "DOWN", width=5, height=2, font=("Segoe UI", 11, "bold")).grid(
            row=2, column=1, sticky="nsew", padx=3, pady=3
        )

        # 5. Contrôles Volume et Chaînes (2 colonnes uniformes, parfaitement alignées)
        vc_frame = tk.Frame(parent, bg=THEME["card_bg"])
        vc_frame.pack(fill=tk.X, pady=(0, 12))
        for c in range(2):
            vc_frame.columnconfigure(c, weight=1, uniform="vc_col")

        lbl_v = tk.Label(vc_frame, text="VOLUME", font=("Segoe UI", 8, "bold"), fg=THEME["text_muted"], bg=THEME["card_bg"])
        lbl_v.grid(row=0, column=0, pady=(0, 4))

        lbl_c = tk.Label(vc_frame, text="CHAÎNE", font=("Segoe UI", 8, "bold"), fg=THEME["text_muted"], bg=THEME["card_bg"])
        lbl_c.grid(row=0, column=1, pady=(0, 4))

        # Ligne 1 : VOL + / CH +
        self.create_remote_btn(vc_frame, "VOL +", "VOL+", font=("Segoe UI", 9, "bold")).grid(
            row=1, column=0, sticky="nsew", padx=6, pady=2, ipady=3
        )
        self.create_remote_btn(vc_frame, "CH +", "CH+", font=("Segoe UI", 9, "bold")).grid(
            row=1, column=1, sticky="nsew", padx=6, pady=2, ipady=3
        )

        # Ligne 2 : MUTE / PROG
        self.create_remote_btn(vc_frame, "MUTE", "MUTE", font=("Segoe UI", 8, "bold")).grid(
            row=2, column=0, sticky="nsew", padx=6, pady=2, ipady=3
        )
        self.create_remote_btn(vc_frame, "PROG", "PROG", font=("Segoe UI", 8, "bold")).grid(
            row=2, column=1, sticky="nsew", padx=6, pady=2, ipady=3
        )

        # Ligne 3 : VOL - / CH -
        self.create_remote_btn(vc_frame, "VOL -", "VOL-", font=("Segoe UI", 9, "bold")).grid(
            row=3, column=0, sticky="nsew", padx=6, pady=2, ipady=3
        )
        self.create_remote_btn(vc_frame, "CH -", "CH-", font=("Segoe UI", 9, "bold")).grid(
            row=3, column=1, sticky="nsew", padx=6, pady=2, ipady=3
        )

        # 6. Contrôles Média (4 colonnes uniformes)
        media_frame = tk.Frame(parent, bg=THEME["card_bg"])
        media_frame.pack(fill=tk.X, pady=(0, 12))
        for c in range(4):
            media_frame.columnconfigure(c, weight=1, uniform="media_col")

        self.create_remote_btn(media_frame, "⏪", "FBWD", font=("Segoe UI", 9)).grid(
            row=0, column=0, sticky="nsew", padx=2, ipady=3
        )
        self.create_remote_btn(media_frame, "⏯", "PLAY/PAUSE", font=("Segoe UI", 9)).grid(
            row=0, column=1, sticky="nsew", padx=2, ipady=3
        )
        self.create_remote_btn(media_frame, "⏩", "FFWD", font=("Segoe UI", 9)).grid(
            row=0, column=2, sticky="nsew", padx=2, ipady=3
        )
        self.create_remote_btn(media_frame, "● REC", "REC", fg="#ef5350", font=("Segoe UI", 8, "bold")).grid(
            row=0, column=3, sticky="nsew", padx=2, ipady=3
        )

        # 7. Pavé Numérique (3 colonnes uniformes, 0 parfaitement centré)
        keypad_frame = tk.Frame(parent, bg=THEME["card_bg"])
        keypad_frame.pack(fill=tk.X)
        for c in range(3):
            keypad_frame.columnconfigure(c, weight=1, uniform="kp_col")

        for i in range(9):
            digit = str(i + 1)
            self.create_remote_btn(
                keypad_frame, digit, digit, font=("Segoe UI", 10, "bold")
            ).grid(row=i // 3, column=i % 3, sticky="nsew", padx=2, pady=2, ipady=3)

        # Ligne 4 : 0 au centre (col 1), spacers invisibles en col 0 et 2
        spacer_left = tk.Label(keypad_frame, text="", bg=THEME["card_bg"])
        spacer_left.grid(row=3, column=0, sticky="nsew", padx=2, pady=2)

        self.create_remote_btn(
            keypad_frame, "0", "0", font=("Segoe UI", 10, "bold")
        ).grid(row=3, column=1, sticky="nsew", padx=2, pady=2, ipady=3)

        spacer_right = tk.Label(keypad_frame, text="", bg=THEME["card_bg"])
        spacer_right.grid(row=3, column=2, sticky="nsew", padx=2, pady=2)

    def build_right_panel(self, parent):
        # 1. Raccourcis TNT
        quick_frame = tk.Frame(
            parent, bg=THEME["card_bg"], padx=14, pady=12,
            highlightthickness=1, highlightbackground=THEME["card_border"]
        )
        quick_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            quick_frame, text="ZAPPING RAPIDE TNT",
            font=("Segoe UI", 10, "bold"), fg=THEME["text"], bg=THEME["card_bg"]
        ).pack(anchor=tk.W, pady=(0, 8))

        top_channels = [
            ("1 - TF1", "TF1"),
            ("2 - France 2", "FRANCE 2"),
            ("3 - France 3", "FRANCE 3"),
            ("4 - Canal+", "CANAL+"),
            ("5 - France 5", "FRANCE 5"),
            ("6 - M6", "M6"),
            ("7 - Arte", "ARTE"),
            ("8 - C8", "C8"),
            ("9 - W9", "W9"),
            ("10 - TMC", "TMC"),
            ("15 - BFM TV", "BFM TV"),
            ("16 - CNews", "CNEWS"),
            ("21 - L'Équipe", "LA CHAINE L'EQUIPE"),
            ("27 - Franceinfo", "FRANCEINFO"),
        ]

        grid_chan = tk.Frame(quick_frame, bg=THEME["card_bg"])
        grid_chan.pack(fill=tk.X)

        cols = 7
        for idx, (label, epg_key) in enumerate(top_channels):
            r = idx // cols
            c = idx % cols
            btn = tk.Button(
                grid_chan, text=label, font=("Segoe UI", 8),
                bg=THEME["btn_bg"], fg=THEME["text"],
                activebackground=THEME["accent"], activeforeground="#ffffff",
                relief="flat", cursor="hand2", padx=6, pady=4,
                command=lambda k=epg_key: self.action_zap_channel(k)
            )
            btn.grid(row=r, column=c, padx=3, pady=3, sticky="nsew")
            grid_chan.columnconfigure(c, weight=1)

        # 2. Liste complète des chaînes avec recherche
        chan_catalog_card = tk.Frame(
            parent, bg=THEME["card_bg"], padx=14, pady=12,
            highlightthickness=1, highlightbackground=THEME["card_border"]
        )
        chan_catalog_card.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        search_header = tk.Frame(chan_catalog_card, bg=THEME["card_bg"])
        search_header.pack(fill=tk.X, pady=(0, 8))

        tk.Label(
            search_header, text="CATALOGUE DES CHAÎNES",
            font=("Segoe UI", 10, "bold"), fg=THEME["text"], bg=THEME["card_bg"]
        ).pack(side=tk.LEFT)

        tk.Label(
            search_header, text="🔍 Filtrer :", font=("Segoe UI", 9),
            fg=THEME["text_muted"], bg=THEME["card_bg"]
        ).pack(side=tk.LEFT, padx=(16, 4))

        entry_search = tk.Entry(
            search_header, textvariable=self.search_chan_var, font=("Segoe UI", 9),
            bg=THEME["entry_bg"], fg=THEME["text"], insertbackground=THEME["text"],
            relief="flat", highlightthickness=1, highlightbackground=THEME["card_border"],
            width=20
        )
        entry_search.pack(side=tk.LEFT, ipady=3)
        entry_search.bind("<KeyRelease>", lambda e: self.filter_channels())

        tk.Label(
            search_header, text="N° / EPG direct :", font=("Segoe UI", 9),
            fg=THEME["text_muted"], bg=THEME["card_bg"]
        ).pack(side=tk.LEFT, padx=(12, 4))

        entry_direct = tk.Entry(
            search_header, textvariable=self.direct_chan_var, font=("Segoe UI", 9),
            bg=THEME["entry_bg"], fg=THEME["text"], insertbackground=THEME["text"],
            relief="flat", highlightthickness=1, highlightbackground=THEME["card_border"],
            width=7
        )
        entry_direct.pack(side=tk.LEFT, ipady=3)
        entry_direct.bind("<Return>", lambda e: self.action_zap_direct())

        btn_zap_direct = self.create_button(
            search_header, text="Zapper", command=self.action_zap_direct,
            bg=THEME["accent"], fg="#ffffff", px=7, py=3
        )
        btn_zap_direct.pack(side=tk.LEFT, padx=5)

        # Tableau des chaînes
        tree_frame = tk.Frame(chan_catalog_card, bg=THEME["card_bg"])
        tree_frame.pack(fill=tk.BOTH, expand=True)

        columns = ("name", "epg_id")
        self.tree_channels = ttk.Treeview(
            tree_frame, columns=columns, show="headings", selectmode="browse"
        )
        self.tree_channels.heading("name", text="Nom / Raccourci Chaîne", anchor=tk.W)
        self.tree_channels.heading("epg_id", text="Code EPG ID", anchor=tk.W)
        self.tree_channels.column("name", width=340, anchor=tk.W)
        self.tree_channels.column("epg_id", width=120, anchor=tk.W)

        tree_scroll = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree_channels.yview)
        self.tree_channels.configure(yscrollcommand=tree_scroll.set)

        self.tree_channels.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree_channels.bind("<Double-1>", lambda e: self.action_zap_selected_tree())

        tree_action_bar = tk.Frame(chan_catalog_card, bg=THEME["card_bg"], pady=6)
        tree_action_bar.pack(fill=tk.X)

        lbl_hint = tk.Label(
            tree_action_bar, text="💡 Double-cliquez sur une chaîne pour zapper immédiatement.",
            font=("Segoe UI", 8, "italic"), fg=THEME["text_muted"], bg=THEME["card_bg"]
        )
        lbl_hint.pack(side=tk.LEFT)

        btn_zap_tree = self.create_button(
            tree_action_bar, text="Zapper sur la sélection",
            command=self.action_zap_selected_tree, bg=THEME["accent"], fg="#ffffff", px=10, py=4
        )
        btn_zap_tree.pack(side=tk.RIGHT)

    def build_bottom_panel(self):
        bottom_frame = tk.Frame(
            self, bg=THEME["card_bg"], padx=14, pady=8,
            highlightthickness=1, highlightbackground=THEME["card_border"]
        )
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)

        status_bar = tk.Frame(bottom_frame, bg=THEME["card_bg"])
        status_bar.pack(fill=tk.X, pady=(0, 4))

        self.lbl_status_icon = tk.Label(
            status_bar, text="●", font=("Segoe UI", 10),
            fg=THEME["success"], bg=THEME["card_bg"]
        )
        self.lbl_status_icon.pack(side=tk.LEFT, padx=(0, 6))

        lbl_status = tk.Label(
            status_bar, textvariable=self.status_text_var,
            font=("Segoe UI", 9), fg=THEME["text"], bg=THEME["card_bg"]
        )
        lbl_status.pack(side=tk.LEFT)

        btn_clear_log = tk.Button(
            status_bar, text="Effacer le journal", font=("Segoe UI", 8),
            bg=THEME["card_bg"], fg=THEME["text_muted"], relief="flat", cursor="hand2",
            command=self.clear_log
        )
        btn_clear_log.pack(side=tk.RIGHT)

        self.log_text = tk.Text(
            bottom_frame, height=4, bg=THEME["console_bg"], fg=THEME["console_text"],
            font=("Consolas", 8), relief="flat", padx=6, pady=4, wrap=tk.WORD
        )
        self.log_text.pack(fill=tk.X)
        self.log_text.config(state=tk.DISABLED)

    # --- Helpers Widgets ---

    def create_button(self, parent, text, command, bg=THEME["btn_bg"], fg=THEME["btn_text"], px=8, py=4, font=("Segoe UI", 9)):
        btn = tk.Button(
            parent, text=text, font=font, bg=bg, fg=fg,
            activebackground=THEME["btn_hover"], activeforeground="#ffffff",
            relief="flat", cursor="hand2", padx=px, pady=py, command=command
        )
        return btn

    def create_remote_btn(self, parent, text, key_code, width=None, height=None,
                          bg=THEME["btn_bg"], fg=THEME["btn_text"], active_bg=THEME["btn_hover"],
                          font=("Segoe UI", 9)):
        btn = tk.Button(
            parent, text=text, font=font,
            bg=bg, fg=fg, activebackground=active_bg, activeforeground="#ffffff",
            relief="flat", cursor="hand2", padx=2, pady=2,
            command=lambda: self.action_send_key(key_code)
        )
        if width is not None:
            btn.config(width=width)
        if height is not None:
            btn.config(height=height)
        return btn

    # --- Auto-détection de l'IP du Décodeur ---

    def action_auto_detect_ip(self):
        if self.is_discovering:
            return
        self.is_discovering = True
        self.btn_auto_detect.config(state=tk.DISABLED, text="🔍 Détection...")
        self.set_status("Recherche automatique du décodeur TV sur le réseau...", "working")
        self.log("Lancement de l'auto-détection (recherche hostname 'tv' et port 8080)...", "info")

        def task():
            def progress(msg):
                self.after(0, lambda: self.set_status(msg, "working"))

            ip, port, info = discover_decoder_ip(progress_cb=progress)
            self.after(0, lambda: self._on_decoder_discovered(ip, port, info))

        threading.Thread(target=task, daemon=True).start()

    def _on_decoder_discovered(self, ip, port, info):
        self.is_discovering = False
        self.btn_auto_detect.config(state=tk.NORMAL, text="🔍 Détecter IP")

        if ip:
            self.ip_var.set(ip)
            self.port_var.set(port or "8080")
            self.client.ip = ip
            self.client.port = port or "8080"
            self.save_config(show_popup=False)
            msg = f"Décodeur TV trouvé : {ip}:{port} ({info})"
            self.log(msg, "success")
            self.set_status(f"Décodeur détecté : {ip}", "success")
            messagebox.showinfo("Décodeur Détecté !", f"Le décodeur TV Orange a été détecté avec succès :\n\n• Adresse IP : {ip}\n• Port : {port}\n• Description : {info}\n\nL'adresse a été automatiquement sauvegardée.")
        else:
            self.log("Aucun décodeur TV détecté sur le réseau local.", "error")
            self.set_status("Aucun décodeur TV trouvé automatiquement", "error")
            messagebox.showwarning(
                "Décodeur Non Détecté",
                "Impossible de trouver automatiquement le décodeur TV sur le réseau local.\n\n"
                "Vérifiez que votre décodeur est bien allumé et connecté au même réseau WiFi/Ethernet que cet ordinateur."
            )

    # --- Gestion des Chaînes ---

    def load_channels_to_tree(self):
        self.all_channels = []
        if self.client.epg_ids:
            for name, epg in self.client.epg_ids.items():
                self.all_channels.append((str(name), str(epg)))
            
            def sort_key(item):
                name, _ = item
                if name.isdigit():
                    return (0, int(name), "")
                return (1, 0, name.lower())

            self.all_channels.sort(key=sort_key)

        self.display_channels(self.all_channels)

    def display_channels(self, channels_list):
        for item in self.tree_channels.get_children():
            self.tree_channels.delete(item)

        for name, epg in channels_list:
            self.tree_channels.insert("", tk.END, values=(name, epg))

    def filter_channels(self):
        query = self.search_chan_var.get().strip().lower()
        if not query:
            self.display_channels(self.all_channels)
            return

        filtered = [
            (name, epg) for name, epg in self.all_channels
            if query in name.lower() or query in epg.lower()
        ]
        self.display_channels(filtered)

    # --- Actions Asynchrones ---

    def action_send_key(self, key_code):
        mode = self.mode_var.get()
        mode_label = ["court (0)", "enfoncé (1)", "relâché (2)"][mode]
        self.set_status(f"Envoi de la touche '{key_code}' (mode {mode_label})...", "working")

        def task():
            success, data, err = self.client.send_key(key_code, mode=mode)
            self.after(0, lambda: self._on_key_sent(key_code, success, data, err))

        threading.Thread(target=task, daemon=True).start()

    def _on_key_sent(self, key_code, success, data, err):
        if success:
            code = data.get("result", {}).get("responseCode", "?")
            msg = data.get("result", {}).get("message", "ok")
            log_msg = f"Touche '{key_code}' envoyée avec succès -> Code: {code}, Message: '{msg}'"
            self.log(log_msg, "success")
            self.set_status(f"Succès : Touche '{key_code}' envoyée", "success")
        else:
            self.log(f"Échec envoi touche '{key_code}' : {err}", "error")
            self.set_status(f"Erreur : {err}", "error")

    def action_zap_channel(self, epg_key):
        self.set_status(f"Zapping vers '{epg_key}'...", "working")

        def task():
            success, data, err = self.client.change_channel(epg_key)
            self.after(0, lambda: self._on_channel_changed(epg_key, success, data, err))

        threading.Thread(target=task, daemon=True).start()

    def action_zap_direct(self):
        val = self.direct_chan_var.get().strip()
        if not val:
            messagebox.showwarning("Chaîne vide", "Veuillez saisir un numéro ou nom de chaîne.")
            return
        self.action_zap_channel(val)

    def action_zap_selected_tree(self):
        selected = self.tree_channels.selection()
        if not selected:
            messagebox.showinfo("Sélection", "Veuillez sélectionner une chaîne dans la liste.")
            return
        item = self.tree_channels.item(selected[0])
        chan_name = item["values"][0]
        self.action_zap_channel(chan_name)

    def _on_channel_changed(self, channel_key, success, data, err):
        if success:
            code = data.get("result", {}).get("responseCode", "?")
            msg = data.get("result", {}).get("message", "ok")
            log_msg = f"Zapping sur '{channel_key}' réussi -> Code: {code}, Message: '{msg}'"
            self.log(log_msg, "success")
            self.set_status(f"Zapping réussi sur '{channel_key}'", "success")
        else:
            self.log(f"Échec zapping vers '{channel_key}' : {err}", "error")
            self.set_status(f"Erreur zapping : {err}", "error")

    def action_get_status(self):
        self.set_status("Récupération de l'état du décodeur (Op 10)...", "working")

        def task():
            success, data, err = self.client.get_status()
            self.after(0, lambda: self._on_status_received(success, data, err))

        threading.Thread(target=task, daemon=True).start()

    def _on_status_received(self, success, data, err):
        if success:
            res = data.get("result", {})
            code = res.get("responseCode", "?")
            msg = res.get("message", "ok")
            info_data = res.get("data", {})

            self.log(f"Infos reçues : {json.dumps(res, ensure_ascii=False)}", "success")
            self.set_status("État du décodeur récupéré avec succès", "success")

            details = [
                f"Code réponse : {code}",
                f"Message : {msg}",
                "",
                "Données détaillées :"
            ]
            if isinstance(info_data, dict) and info_data:
                for k, v in info_data.items():
                    details.append(f"  • {k} : {v}")
            else:
                details.append(f"  {json.dumps(info_data, indent=2)}")

            messagebox.showinfo("Informations Décodeur TV", "\n".join(details))
        else:
            self.log(f"Erreur récupération état : {err}", "error")
            self.set_status(f"Erreur état : {err}", "error")
            messagebox.showerror("Erreur de connexion", f"Impossible d'interroger le décodeur :\n\n{err}")

    # --- Logs & Status ---

    def set_status(self, text, state="normal"):
        self.status_text_var.set(text)
        color_map = {
            "normal": THEME["text"],
            "working": THEME["warning"],
            "success": THEME["success"],
            "error": THEME["error"]
        }
        color = color_map.get(state, THEME["text"])
        self.lbl_status_icon.config(fg=color)

    def log(self, text, level="info"):
        now = datetime.now().strftime("%H:%M:%S")
        prefix = f"[{now}] "

        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, prefix + text + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def clear_log(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state=tk.DISABLED)


def main():
    app = OrangeTVApp()
    app.mainloop()


if __name__ == "__main__":
    main()
