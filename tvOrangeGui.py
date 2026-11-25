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

import json
import threading
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, ttk

from livebox_core import (
    CONFIG_FILE,
    DEFAULT_IP,
    DEFAULT_PORT,
    EPG_IDS_FILE,
    KEYS_FILE,
    OrangeTVClient,
    discover_decoder_ip,
)
from livebox_core import (
    load_config as core_load_config,
)
from livebox_core import (
    save_config as core_save_config,
)

__all__ = [
    "CONFIG_FILE",
    "DEFAULT_IP",
    "DEFAULT_PORT",
    "EPG_IDS_FILE",
    "KEYS_FILE",
    "THEME",
    "ExploreDialog",
    "OrangeTVApp",
    "OrangeTVClient",
    "discover_decoder_ip",
    "main",
]

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
        self.mode_var = tk.IntVar(value=0)  # 0: court, 1: enfoncer, 2: relâcher
        self.search_chan_var = tk.StringVar()
        self.direct_chan_var = tk.StringVar()
        self.status_text_var = tk.StringVar(value="Prêt - En attente d'une commande")
        self.is_discovering = False

        self.setup_styles()
        self.build_ui()
        self.load_channels_to_tree()

    def load_config(self):
        self.current_ip, self.current_port = core_load_config(CONFIG_FILE)

    def save_config(self, show_popup=True):
        new_ip = self.ip_var.get().strip()
        if not new_ip:
            if show_popup:
                messagebox.showwarning(
                    "Adresse IP vide",
                    "Veuillez renseigner une adresse IP valide.",
                )
            return

        self.current_ip = new_ip
        self.current_port = self.current_port or DEFAULT_PORT
        self.client.ip = self.current_ip
        self.client.port = self.current_port

        try:
            core_save_config(
                self.current_ip,
                self.current_port,
                config_file=CONFIG_FILE,
            )
            self.log(
                f"Configuration sauvegardée : {self.current_ip}:{self.current_port}",
                "info",
            )
            if show_popup:
                messagebox.showinfo(
                    "Configuration",
                    "Adresse IP enregistrée avec succès.",
                )
        except OSError as e:
            self.log(
                f"Erreur lors de la sauvegarde de la configuration : {e}",
                "error",
            )

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
            borderwidth=0,
        )
        self.style.configure(
            "Treeview.Heading",
            background=THEME["card_bg"],
            foreground=THEME["text"],
            font=("Segoe UI", 10, "bold"),
            relief="flat",
        )
        self.style.map(
            "Treeview",
            background=[("selected", THEME["accent"])],
            foreground=[("selected", "#ffffff")],
        )
        self.style.map(
            "Treeview.Heading",
            background=[("active", THEME["btn_hover"])],
        )

        self.style.configure(
            "Vertical.TScrollbar",
            background=THEME["card_bg"],
            troughcolor=THEME["bg"],
            arrowcolor=THEME["text_muted"],
        )

    def build_ui(self):
        # En-tête / Barre supérieure
        top_bar = tk.Frame(self, bg=THEME["card_bg"], height=64, padx=16, pady=10)
        top_bar.pack(fill=tk.X, side=tk.TOP)

        title_frame = tk.Frame(top_bar, bg=THEME["card_bg"])
        title_frame.pack(side=tk.LEFT, fill=tk.Y)

        dot = tk.Canvas(
            title_frame, width=16, height=16, bg=THEME["card_bg"], highlightthickness=0
        )
        dot.create_oval(2, 2, 14, 14, fill=THEME["accent"], outline="")
        dot.pack(side=tk.LEFT, padx=(0, 8))

        lbl_title = tk.Label(
            title_frame,
            text="LIVEBOX TV",
            font=("Segoe UI", 14, "bold"),
            fg=THEME["text"],
            bg=THEME["card_bg"],
        )
        lbl_title.pack(side=tk.LEFT)

        lbl_sub = tk.Label(
            title_frame,
            text="UHD 4K",
            font=("Segoe UI", 10),
            fg=THEME["accent"],
            bg=THEME["card_bg"],
        )
        lbl_sub.pack(side=tk.LEFT, padx=(6, 0))

        # Zone configuration IP, Auto-détection & Statut (port 8080 fixe)
        cfg_frame = tk.Frame(top_bar, bg=THEME["card_bg"])
        cfg_frame.pack(side=tk.RIGHT)

        tk.Label(
            cfg_frame,
            text="IP :",
            font=("Segoe UI", 10),
            fg=THEME["text_muted"],
            bg=THEME["card_bg"],
        ).pack(side=tk.LEFT, padx=(8, 2))

        ip_entry = tk.Entry(
            cfg_frame,
            textvariable=self.ip_var,
            width=14,
            font=("Consolas", 10),
            bg=THEME["entry_bg"],
            fg=THEME["text"],
            insertbackground=THEME["text"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=THEME["card_border"],
        )
        ip_entry.pack(side=tk.LEFT, padx=3, ipady=3)

        # Bouton Auto-détection de l'IP
        self.btn_auto_detect = self.create_button(
            cfg_frame,
            text="🔍 Détecter IP",
            command=self.action_auto_detect_ip,
            bg=THEME["btn_bg"],
            fg="#64b5f6",
            px=8,
            py=3,
            font=("Segoe UI", 9, "bold"),
        )
        self.btn_auto_detect.pack(side=tk.LEFT, padx=4)

        btn_save = self.create_button(
            cfg_frame,
            text="Sauvegarder",
            command=self.save_config,
            bg=THEME["btn_bg"],
            fg=THEME["btn_text"],
            px=8,
            py=3,
        )
        btn_save.pack(side=tk.LEFT, padx=4)

        btn_info = self.create_button(
            cfg_frame,
            text="État Décodeur (Op 10)",
            command=self.action_get_status,
            bg=THEME["accent"],
            fg="#ffffff",
            px=9,
            py=3,
        )
        btn_info.pack(side=tk.LEFT, padx=4)

        btn_explore = self.create_button(
            cfg_frame,
            text="🔬 Exploration",
            command=self.action_open_explore,
            bg=THEME["btn_bg"],
            fg="#ce93d8",
            px=9,
            py=3,
            font=("Segoe UI", 9, "bold"),
        )
        btn_explore.pack(side=tk.LEFT, padx=4)

        # Corps principal : 2 colonnes
        main_content = tk.Frame(self, bg=THEME["bg"], padx=14, pady=12)
        main_content.pack(fill=tk.BOTH, expand=True)

        # Colonne Gauche : Télécommande Virtuelle
        remote_card = tk.Frame(
            main_content,
            bg=THEME["card_bg"],
            bd=0,
            padx=18,
            pady=16,
            highlightthickness=1,
            highlightbackground=THEME["card_border"],
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
            header_remote,
            text="TÉLÉCOMMANDE",
            font=("Segoe UI", 11, "bold"),
            fg=THEME["text"],
            bg=THEME["card_bg"],
        )
        lbl.pack(side=tk.LEFT)

        btn_power = tk.Button(
            header_remote,
            text="⏻ POWER",
            font=("Segoe UI", 10, "bold"),
            bg=THEME["power_btn"],
            fg="#ffffff",
            activebackground=THEME["power_hover"],
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=4,
            command=lambda: self.action_send_key("POWER"),
        )
        btn_power.pack(side=tk.RIGHT)

        # 2. Mode d'appui (3 colonnes uniformes)
        mode_frame = tk.LabelFrame(
            parent,
            text="Mode d'appui",
            font=("Segoe UI", 9),
            bg=THEME["card_bg"],
            fg=THEME["text_muted"],
            padx=8,
            pady=4,
            relief="solid",
            bd=1,
        )
        mode_frame.pack(fill=tk.X, pady=(0, 12))
        for c in range(3):
            mode_frame.columnconfigure(c, weight=1, uniform="mode_col")

        rb_short = tk.Radiobutton(
            mode_frame,
            text="Court (0)",
            variable=self.mode_var,
            value=0,
            bg=THEME["card_bg"],
            fg=THEME["text"],
            selectcolor=THEME["card_bg"],
            activebackground=THEME["card_bg"],
            activeforeground=THEME["accent"],
            font=("Segoe UI", 8),
        )
        rb_short.grid(row=0, column=0, sticky="w")

        rb_down = tk.Radiobutton(
            mode_frame,
            text="Maintien (1)",
            variable=self.mode_var,
            value=1,
            bg=THEME["card_bg"],
            fg=THEME["text"],
            selectcolor=THEME["card_bg"],
            activebackground=THEME["card_bg"],
            activeforeground=THEME["accent"],
            font=("Segoe UI", 8),
        )
        rb_down.grid(row=0, column=1, sticky="w")

        rb_up = tk.Radiobutton(
            mode_frame,
            text="Relâche (2)",
            variable=self.mode_var,
            value=2,
            bg=THEME["card_bg"],
            fg=THEME["text"],
            selectcolor=THEME["card_bg"],
            activebackground=THEME["card_bg"],
            activeforeground=THEME["accent"],
            font=("Segoe UI", 8),
        )
        rb_up.grid(row=0, column=2, sticky="w")

        # 3. Touches Fonctions (4 colonnes uniformes, pleine largeur)
        fn_row = tk.Frame(parent, bg=THEME["card_bg"])
        fn_row.pack(fill=tk.X, pady=(0, 10))
        for c in range(4):
            fn_row.columnconfigure(c, weight=1, uniform="fn_col")

        self.create_remote_btn(fn_row, "MENU", "MENU").grid(
            row=0, column=0, sticky="nsew", padx=2, ipady=3
        )
        self.create_remote_btn(fn_row, "RETOUR", "BACK").grid(
            row=0, column=1, sticky="nsew", padx=2, ipady=3
        )
        self.create_remote_btn(fn_row, "DIRECT", "DIRECT").grid(
            row=0, column=2, sticky="nsew", padx=2, ipady=3
        )
        self.create_remote_btn(fn_row, "VOD", "VOD").grid(
            row=0, column=3, sticky="nsew", padx=2, ipady=3
        )

        # 4. Pavé Directionnel (D-Pad en croix 3x3 parfaitement symétrique)
        dpad_outer = tk.Frame(parent, bg=THEME["card_bg"], pady=4)
        dpad_outer.pack(fill=tk.X, pady=(0, 10))

        dpad_frame = tk.Frame(dpad_outer, bg=THEME["card_bg"])
        dpad_frame.pack(anchor=tk.CENTER)

        for i in range(3):
            dpad_frame.columnconfigure(i, weight=1, uniform="dp_c")
            dpad_frame.rowconfigure(i, weight=1, uniform="dp_r")

        self.create_remote_btn(
            dpad_frame, "▲", "UP", width=5, height=2, font=("Segoe UI", 11, "bold")
        ).grid(row=0, column=1, sticky="nsew", padx=3, pady=3)
        self.create_remote_btn(
            dpad_frame, "◀", "LEFT", width=5, height=2, font=("Segoe UI", 11, "bold")
        ).grid(row=1, column=0, sticky="nsew", padx=3, pady=3)
        self.create_remote_btn(
            dpad_frame,
            "OK",
            "OK",
            width=5,
            height=2,
            bg=THEME["accent"],
            fg="#ffffff",
            active_bg=THEME["accent_hover"],
            font=("Segoe UI", 11, "bold"),
        ).grid(row=1, column=1, sticky="nsew", padx=3, pady=3)
        self.create_remote_btn(
            dpad_frame, "▶", "RIGHT", width=5, height=2, font=("Segoe UI", 11, "bold")
        ).grid(row=1, column=2, sticky="nsew", padx=3, pady=3)
        self.create_remote_btn(
            dpad_frame, "▼", "DOWN", width=5, height=2, font=("Segoe UI", 11, "bold")
        ).grid(row=2, column=1, sticky="nsew", padx=3, pady=3)

        # 5. Contrôles Volume et Chaînes (2 colonnes uniformes)
        vc_frame = tk.Frame(parent, bg=THEME["card_bg"])
        vc_frame.pack(fill=tk.X, pady=(0, 12))
        for c in range(2):
            vc_frame.columnconfigure(c, weight=1, uniform="vc_col")

        lbl_v = tk.Label(
            vc_frame,
            text="VOLUME",
            font=("Segoe UI", 8, "bold"),
            fg=THEME["text_muted"],
            bg=THEME["card_bg"],
        )
        lbl_v.grid(row=0, column=0, pady=(0, 4))

        lbl_c = tk.Label(
            vc_frame,
            text="CHAÎNE",
            font=("Segoe UI", 8, "bold"),
            fg=THEME["text_muted"],
            bg=THEME["card_bg"],
        )
        lbl_c.grid(row=0, column=1, pady=(0, 4))

        self.create_remote_btn(
            vc_frame, "VOL +", "VOL+", font=("Segoe UI", 9, "bold")
        ).grid(row=1, column=0, sticky="nsew", padx=6, pady=2, ipady=3)
        self.create_remote_btn(
            vc_frame, "CH +", "CH+", font=("Segoe UI", 9, "bold")
        ).grid(row=1, column=1, sticky="nsew", padx=6, pady=2, ipady=3)

        self.create_remote_btn(
            vc_frame, "MUTE", "MUTE", font=("Segoe UI", 8, "bold")
        ).grid(row=2, column=0, sticky="nsew", padx=6, pady=2, ipady=3)
        self.create_remote_btn(
            vc_frame, "PROG", "PROG", font=("Segoe UI", 8, "bold")
        ).grid(row=2, column=1, sticky="nsew", padx=6, pady=2, ipady=3)

        self.create_remote_btn(
            vc_frame, "VOL -", "VOL-", font=("Segoe UI", 9, "bold")
        ).grid(row=3, column=0, sticky="nsew", padx=6, pady=2, ipady=3)
        self.create_remote_btn(
            vc_frame, "CH -", "CH-", font=("Segoe UI", 9, "bold")
        ).grid(row=3, column=1, sticky="nsew", padx=6, pady=2, ipady=3)

        # 6. Contrôles Média (4 colonnes uniformes)
        media_frame = tk.Frame(parent, bg=THEME["card_bg"])
        media_frame.pack(fill=tk.X, pady=(0, 12))
        for c in range(4):
            media_frame.columnconfigure(c, weight=1, uniform="media_col")

        self.create_remote_btn(media_frame, "⏪", "FBWD", font=("Segoe UI", 9)).grid(
            row=0, column=0, sticky="nsew", padx=2, ipady=3
        )
        self.create_remote_btn(
            media_frame, "⏯", "PLAY/PAUSE", font=("Segoe UI", 9)
        ).grid(row=0, column=1, sticky="nsew", padx=2, ipady=3)
        self.create_remote_btn(media_frame, "⏩", "FFWD", font=("Segoe UI", 9)).grid(
            row=0, column=2, sticky="nsew", padx=2, ipady=3
        )
        self.create_remote_btn(
            media_frame, "● REC", "REC", fg="#ef5350", font=("Segoe UI", 8, "bold")
        ).grid(row=0, column=3, sticky="nsew", padx=2, ipady=3)

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
            parent,
            bg=THEME["card_bg"],
            padx=14,
            pady=12,
            highlightthickness=1,
            highlightbackground=THEME["card_border"],
        )
        quick_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(
            quick_frame,
            text="ZAPPING RAPIDE TNT",
            font=("Segoe UI", 10, "bold"),
            fg=THEME["text"],
            bg=THEME["card_bg"],
        ).pack(anchor=tk.W, pady=(0, 8))

        self.top_channels = [
            ("1 - TF1", "TF1"),
            ("2 - France 2", "FRANCE 2"),
            ("3 - France 3", "FRANCE 3"),
            ("4 - France 4", "FRANCE 4"),
            ("5 - France 5", "FRANCE 5"),
            ("6 - M6", "M6"),
            ("7 - Arte", "ARTE"),
            ("9 - W9", "W9"),
            ("10 - TMC", "TMC"),
            ("13 - BFM TV", "BFM TV"),
            ("14 - CNews", "CNEWS"),
            ("16 - Franceinfo", "FRANCEINFO"),
            ("18 - T18", "T18"),
            ("19 - NOVO19", "NOVO19"),
        ]

        grid_chan = tk.Frame(quick_frame, bg=THEME["card_bg"])
        grid_chan.pack(fill=tk.X)

        cols = 7
        for idx, (label, epg_key) in enumerate(self.top_channels):
            r = idx // cols
            c = idx % cols
            btn = tk.Button(
                grid_chan,
                text=label,
                font=("Segoe UI", 8),
                bg=THEME["btn_bg"],
                fg=THEME["text"],
                activebackground=THEME["accent"],
                activeforeground="#ffffff",
                relief="flat",
                cursor="hand2",
                padx=6,
                pady=4,
                command=lambda k=epg_key: self.action_zap_channel(k),
            )
            btn.grid(row=r, column=c, padx=3, pady=3, sticky="nsew")
            grid_chan.columnconfigure(c, weight=1)

        # 2. Liste complète des chaînes avec recherche
        chan_catalog_card = tk.Frame(
            parent,
            bg=THEME["card_bg"],
            padx=14,
            pady=12,
            highlightthickness=1,
            highlightbackground=THEME["card_border"],
        )
        chan_catalog_card.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        search_header = tk.Frame(chan_catalog_card, bg=THEME["card_bg"])
        search_header.pack(fill=tk.X, pady=(0, 8))

        tk.Label(
            search_header,
            text="CATALOGUE DES CHAÎNES",
            font=("Segoe UI", 10, "bold"),
            fg=THEME["text"],
            bg=THEME["card_bg"],
        ).pack(side=tk.LEFT)

        tk.Label(
            search_header,
            text="🔍 Filtrer :",
            font=("Segoe UI", 9),
            fg=THEME["text_muted"],
            bg=THEME["card_bg"],
        ).pack(side=tk.LEFT, padx=(16, 4))

        entry_search = tk.Entry(
            search_header,
            textvariable=self.search_chan_var,
            font=("Segoe UI", 9),
            bg=THEME["entry_bg"],
            fg=THEME["text"],
            insertbackground=THEME["text"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=THEME["card_border"],
            width=20,
        )
        entry_search.pack(side=tk.LEFT, ipady=3)
        entry_search.bind("<KeyRelease>", lambda e: self.filter_channels())

        tk.Label(
            search_header,
            text="N° / EPG direct :",
            font=("Segoe UI", 9),
            fg=THEME["text_muted"],
            bg=THEME["card_bg"],
        ).pack(side=tk.LEFT, padx=(12, 4))

        entry_direct = tk.Entry(
            search_header,
            textvariable=self.direct_chan_var,
            font=("Segoe UI", 9),
            bg=THEME["entry_bg"],
            fg=THEME["text"],
            insertbackground=THEME["text"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=THEME["card_border"],
            width=7,
        )
        entry_direct.pack(side=tk.LEFT, ipady=3)
        entry_direct.bind("<Return>", lambda e: self.action_zap_direct())

        btn_zap_direct = self.create_button(
            search_header,
            text="Zapper",
            command=self.action_zap_direct,
            bg=THEME["accent"],
            fg="#ffffff",
            px=7,
            py=3,
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

        tree_scroll = ttk.Scrollbar(
            tree_frame, orient=tk.VERTICAL, command=self.tree_channels.yview
        )
        self.tree_channels.configure(yscrollcommand=tree_scroll.set)

        self.tree_channels.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.tree_channels.bind(
            "<Double-1>", lambda e: self.action_zap_selected_tree()
        )

        tree_action_bar = tk.Frame(chan_catalog_card, bg=THEME["card_bg"], pady=6)
        tree_action_bar.pack(fill=tk.X)

        lbl_hint = tk.Label(
            tree_action_bar,
            text="💡 Double-cliquez sur une chaîne pour zapper immédiatement.",
            font=("Segoe UI", 8, "italic"),
            fg=THEME["text_muted"],
            bg=THEME["card_bg"],
        )
        lbl_hint.pack(side=tk.LEFT)

        btn_zap_tree = self.create_button(
            tree_action_bar,
            text="Zapper sur la sélection",
            command=self.action_zap_selected_tree,
            bg=THEME["accent"],
            fg="#ffffff",
            px=10,
            py=4,
        )
        btn_zap_tree.pack(side=tk.RIGHT)

    def build_bottom_panel(self):
        bottom_frame = tk.Frame(
            self,
            bg=THEME["card_bg"],
            padx=14,
            pady=8,
            highlightthickness=1,
            highlightbackground=THEME["card_border"],
        )
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)

        status_bar = tk.Frame(bottom_frame, bg=THEME["card_bg"])
        status_bar.pack(fill=tk.X, pady=(0, 4))

        self.lbl_status_icon = tk.Label(
            status_bar,
            text="●",
            font=("Segoe UI", 10),
            fg=THEME["success"],
            bg=THEME["card_bg"],
        )
        self.lbl_status_icon.pack(side=tk.LEFT, padx=(0, 6))

        lbl_status = tk.Label(
            status_bar,
            textvariable=self.status_text_var,
            font=("Segoe UI", 9),
            fg=THEME["text"],
            bg=THEME["card_bg"],
        )
        lbl_status.pack(side=tk.LEFT)

        btn_clear_log = tk.Button(
            status_bar,
            text="Effacer le journal",
            font=("Segoe UI", 8),
            bg=THEME["card_bg"],
            fg=THEME["text_muted"],
            relief="flat",
            cursor="hand2",
            command=self.clear_log,
        )
        btn_clear_log.pack(side=tk.RIGHT)

        self.log_text = tk.Text(
            bottom_frame,
            height=4,
            bg=THEME["console_bg"],
            fg=THEME["console_text"],
            font=("Consolas", 8),
            relief="flat",
            padx=6,
            pady=4,
            wrap=tk.WORD,
        )
        self.log_text.pack(fill=tk.X)
        self.log_text.config(state=tk.DISABLED)

    # --- Helpers Widgets ---

    def _safe_after(self, callback):
        try:
            if self.winfo_exists():
                self.after(0, lambda: self.winfo_exists() and callback())
        except tk.TclError:
            pass

    def create_button(
        self,
        parent,
        text,
        command,
        bg=THEME["btn_bg"],
        fg=THEME["btn_text"],
        px=8,
        py=4,
        font=("Segoe UI", 9),
    ):
        return tk.Button(
            parent,
            text=text,
            font=font,
            bg=bg,
            fg=fg,
            activebackground=THEME["btn_hover"],
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            padx=px,
            pady=py,
            command=command,
        )

    def create_remote_btn(
        self,
        parent,
        text,
        key_code,
        width=None,
        height=None,
        bg=THEME["btn_bg"],
        fg=THEME["btn_text"],
        active_bg=THEME["btn_hover"],
        font=("Segoe UI", 9),
    ):
        btn = tk.Button(
            parent,
            text=text,
            font=font,
            bg=bg,
            fg=fg,
            activebackground=active_bg,
            activeforeground="#ffffff",
            relief="flat",
            cursor="hand2",
            padx=2,
            pady=2,
            command=lambda: self.action_send_key(key_code),
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
        self.set_status(
            "Recherche automatique du décodeur TV sur le réseau...", "working"
        )
        self.log(
            "Lancement de l'auto-détection (recherche hostname 'tv' et port 8080)...",
            "info",
        )

        def task():
            def progress(msg):
                self._safe_after(lambda: self.set_status(msg, "working"))

            ip, port, info = discover_decoder_ip(progress_cb=progress)
            self._safe_after(lambda: self._on_decoder_discovered(ip, port, info))

        threading.Thread(target=task, daemon=True).start()

    def _on_decoder_discovered(self, ip, port, info):
        self.is_discovering = False
        self.btn_auto_detect.config(state=tk.NORMAL, text="🔍 Détecter IP")

        if ip:
            self.ip_var.set(ip)
            self.current_port = port or DEFAULT_PORT
            self.client.ip = ip
            self.client.port = self.current_port
            self.save_config(show_popup=False)
            msg = f"Décodeur TV trouvé : {ip}:{self.current_port} ({info})"
            self.log(msg, "success")
            self.set_status(f"Décodeur détecté : {ip}", "success")
            messagebox.showinfo(
                "Décodeur Détecté !",
                f"Le décodeur TV Orange a été détecté avec succès :\n\n"
                f"• Adresse IP : {ip}\n• Port : {self.current_port}\n• Description : {info}\n\n"
                "L'adresse a été automatiquement sauvegardée.",
            )
        else:
            self.log("Aucun décodeur TV détecté sur le réseau local.", "error")
            self.set_status("Aucun décodeur TV trouvé automatiquement", "error")
            messagebox.showwarning(
                "Décodeur Non Détecté",
                "Impossible de trouver automatiquement le décodeur TV sur le réseau local.\n\n"
                "Vérifiez que votre décodeur est bien allumé et connecté au même réseau WiFi/Ethernet que cet ordinateur.",
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
            (name, epg)
            for name, epg in self.all_channels
            if query in name.lower() or query in epg.lower()
        ]
        self.display_channels(filtered)

    # --- Actions Asynchrones ---

    def action_send_key(self, key_code):
        mode = self.mode_var.get()
        mode_label = ["court (0)", "enfoncé (1)", "relâché (2)"][mode]
        self.set_status(
            f"Envoi de la touche '{key_code}' (mode {mode_label})...", "working"
        )

        def task():
            success, data, err = self.client.send_key(key_code, mode=mode)
            self._safe_after(
                lambda: self._on_key_sent(key_code, success, data, err)
            )

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
            self._safe_after(
                lambda: self._on_channel_changed(epg_key, success, data, err)
            )

        threading.Thread(target=task, daemon=True).start()

    def action_zap_direct(self):
        val = self.direct_chan_var.get().strip()
        if not val:
            messagebox.showwarning(
                "Chaîne vide", "Veuillez saisir un numéro ou nom de chaîne."
            )
            return
        self.action_zap_channel(val)

    def action_zap_selected_tree(self):
        selected = self.tree_channels.selection()
        if not selected:
            messagebox.showinfo(
                "Sélection", "Veuillez sélectionner une chaîne dans la liste."
            )
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
            self._safe_after(
                lambda: self._on_status_received(success, data, err)
            )

        threading.Thread(target=task, daemon=True).start()

    def _on_status_received(self, success, data, err):
        if success:
            res = data.get("result", {})
            code = res.get("responseCode", "?")
            msg = res.get("message", "ok")
            info_data = res.get("data", {})

            self.log(
                f"Infos reçues : {json.dumps(res, ensure_ascii=False)}", "success"
            )
            self.set_status("État du décodeur récupéré avec succès", "success")

            details = [
                f"Code réponse : {code}",
                f"Message : {msg}",
                "",
                "Données détaillées :",
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
            messagebox.showerror(
                "Erreur de connexion",
                f"Impossible d'interroger le décodeur :\n\n{err}",
            )

    # --- Logs & Status ---

    def set_status(self, text, state="normal"):
        self.status_text_var.set(text)
        color_map = {
            "normal": THEME["text"],
            "working": THEME["warning"],
            "success": THEME["success"],
            "error": THEME["error"],
        }
        color = color_map.get(state, THEME["text"])
        self.lbl_status_icon.config(fg=color)

    def log(self, text, level="info"):
        now = datetime.now().astimezone().strftime("%H:%M:%S")
        prefix = f"[{now}] "

        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, prefix + text + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def clear_log(self):
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state=tk.DISABLED)

    def action_open_explore(self):
        ExploreDialog(self, self.client)


class ExploreDialog(tk.Toplevel):
    """Fenêtre d'exploration et de diagnostic de l'API Orange Livebox TV (touches, modes, EPG)."""

    def __init__(self, parent, client):
        super().__init__(parent)
        self.parent = parent
        self.client = client
        self.title("Explorateur d'API - Décodeur Livebox TV")
        self.geometry("760x650")
        self.minsize(700, 580)
        self.configure(bg=THEME["bg"])

        self.scan_thread = None
        self.stop_scan_flag = False

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.setup_ui()

    def on_close(self):
        self.stop_scan_flag = True
        self.destroy()

    def _safe_after(self, callback):
        try:
            if self.winfo_exists():
                self.after(0, lambda: self.winfo_exists() and callback())
        except tk.TclError:
            pass

    def setup_ui(self):
        header = tk.Frame(self, bg=THEME["card_bg"], padx=16, pady=12)
        header.pack(fill=tk.X)

        tk.Label(
            header,
            text="🔬 Explorateur d'API Livebox TV",
            font=("Segoe UI", 12, "bold"),
            fg=THEME["text"],
            bg=THEME["card_bg"],
        ).pack(anchor=tk.W)

        tk.Label(
            header,
            text="Module d'expérimentation pour tester touches, modes et chaînes EPG à l'aveugle (inspiré de exploreTvOrange.py).",
            font=("Segoe UI", 9),
            fg=THEME["text_muted"],
            bg=THEME["card_bg"],
        ).pack(anchor=tk.W, pady=(2, 0))

        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=14, pady=10)

        tab_keys = tk.Frame(notebook, bg=THEME["card_bg"], padx=14, pady=12)
        notebook.add(tab_keys, text="Touches (Op 1)")
        self.build_tab_keys(tab_keys)

        tab_ops = tk.Frame(notebook, bg=THEME["card_bg"], padx=14, pady=12)
        notebook.add(tab_ops, text="Opérations / Modes")
        self.build_tab_ops(tab_ops)

        tab_epg = tk.Frame(notebook, bg=THEME["card_bg"], padx=14, pady=12)
        notebook.add(tab_epg, text="Chaînes EPG (Op 9)")
        self.build_tab_epg(tab_epg)

        # Zone Console / Logs
        log_frame = tk.Frame(self, bg=THEME["card_bg"], padx=14, pady=8)
        log_frame.pack(fill=tk.BOTH, expand=True, padx=14, pady=(0, 10))

        log_header = tk.Frame(log_frame, bg=THEME["card_bg"])
        log_header.pack(fill=tk.X, pady=(0, 4))

        tk.Label(
            log_header,
            text="Résultats & Réponses API JSON :",
            font=("Segoe UI", 9, "bold"),
            fg=THEME["text"],
            bg=THEME["card_bg"],
        ).pack(side=tk.LEFT)

        tk.Button(
            log_header,
            text="Effacer",
            font=("Segoe UI", 8),
            bg=THEME["btn_bg"],
            fg=THEME["text_muted"],
            relief="flat",
            cursor="hand2",
            command=self.clear_log,
        ).pack(side=tk.RIGHT)

        self.console = tk.Text(
            log_frame,
            height=9,
            bg=THEME["console_bg"],
            fg=THEME["console_text"],
            font=("Consolas", 9),
            relief="flat",
            padx=8,
            pady=6,
            wrap=tk.WORD,
        )
        self.console.pack(fill=tk.BOTH, expand=True)

    def build_tab_keys(self, parent):
        sec_unit = tk.LabelFrame(
            parent,
            text="Test Unitaire d'une Touche",
            font=("Segoe UI", 9, "bold"),
            bg=THEME["card_bg"],
            fg=THEME["text"],
            padx=12,
            pady=10,
            bd=1,
        )
        sec_unit.pack(fill=tk.X, pady=(0, 12))

        row1 = tk.Frame(sec_unit, bg=THEME["card_bg"])
        row1.pack(fill=tk.X)

        tk.Label(
            row1,
            text="Code Touche :",
            font=("Segoe UI", 9),
            fg=THEME["text"],
            bg=THEME["card_bg"],
        ).pack(side=tk.LEFT, padx=(0, 6))

        self.key_entry = tk.Entry(
            row1,
            font=("Consolas", 10),
            width=8,
            bg=THEME["entry_bg"],
            fg=THEME["text"],
            insertbackground=THEME["text"],
            relief="flat",
            highlightthickness=1,
            highlightbackground=THEME["card_border"],
        )
        self.key_entry.insert(0, "116")
        self.key_entry.pack(side=tk.LEFT, padx=(0, 12), ipady=2)

        self.key_mode_var = tk.StringVar(value="0")
        tk.Label(
            row1,
            text="Mode :",
            font=("Segoe UI", 9),
            fg=THEME["text"],
            bg=THEME["card_bg"],
        ).pack(side=tk.LEFT, padx=(0, 4))

        modes = [
            ("Court (0)", "0"),
            ("Enfoncer (1)", "1"),
            ("Relâcher (2)", "2"),
            ("Long (200ms)", "long"),
        ]
        for lbl, val in modes:
            tk.Radiobutton(
                row1,
                text=lbl,
                variable=self.key_mode_var,
                value=val,
                bg=THEME["card_bg"],
                fg=THEME["text"],
                selectcolor=THEME["card_bg"],
                activebackground=THEME["card_bg"],
                activeforeground=THEME["accent"],
                font=("Segoe UI", 8),
            ).pack(side=tk.LEFT, padx=3)

        btn_send = tk.Button(
            row1,
            text="Envoyer",
            font=("Segoe UI", 9, "bold"),
            bg=THEME["accent"],
            fg="#ffffff",
            activebackground=THEME["accent_hover"],
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=2,
            command=self.action_send_single_key,
        )
        btn_send.pack(side=tk.RIGHT)

        sec_scan = tk.LabelFrame(
            parent,
            text="Scanner de Touches (fast_explore)",
            font=("Segoe UI", 9, "bold"),
            bg=THEME["card_bg"],
            fg=THEME["text"],
            padx=12,
            pady=10,
            bd=1,
        )
        sec_scan.pack(fill=tk.X)

        r_range = tk.Frame(sec_scan, bg=THEME["card_bg"])
        r_range.pack(fill=tk.X, pady=(0, 6))

        tk.Label(
            r_range,
            text="Plage : de",
            font=("Segoe UI", 9),
            fg=THEME["text"],
            bg=THEME["card_bg"],
        ).pack(side=tk.LEFT)
        self.scan_start_entry = tk.Entry(
            r_range,
            width=6,
            font=("Consolas", 9),
            bg=THEME["entry_bg"],
            fg=THEME["text"],
            relief="flat",
        )
        self.scan_start_entry.insert(0, "1")
        self.scan_start_entry.pack(side=tk.LEFT, padx=4)

        tk.Label(
            r_range,
            text="à :",
            font=("Segoe UI", 9),
            fg=THEME["text"],
            bg=THEME["card_bg"],
        ).pack(side=tk.LEFT)
        self.scan_end_entry = tk.Entry(
            r_range,
            width=6,
            font=("Consolas", 9),
            bg=THEME["entry_bg"],
            fg=THEME["text"],
            relief="flat",
        )
        self.scan_end_entry.insert(0, "100")
        self.scan_end_entry.pack(side=tk.LEFT, padx=4)

        tk.Label(
            r_range,
            text="Délai (s) :",
            font=("Segoe UI", 9),
            fg=THEME["text"],
            bg=THEME["card_bg"],
        ).pack(side=tk.LEFT, padx=(10, 4))
        self.scan_delay_entry = tk.Entry(
            r_range,
            width=5,
            font=("Consolas", 9),
            bg=THEME["entry_bg"],
            fg=THEME["text"],
            relief="flat",
        )
        self.scan_delay_entry.insert(0, "0.3")
        self.scan_delay_entry.pack(side=tk.LEFT, padx=4)

        self.exclude_known_var = tk.BooleanVar(value=True)
        cb = tk.Checkbutton(
            sec_scan,
            text="Ignorer les touches déjà répertoriées (keys.json)",
            variable=self.exclude_known_var,
            bg=THEME["card_bg"],
            fg=THEME["text"],
            selectcolor=THEME["card_bg"],
            activebackground=THEME["card_bg"],
            font=("Segoe UI", 8),
        )
        cb.pack(anchor=tk.W, pady=(0, 8))

        r_btns = tk.Frame(sec_scan, bg=THEME["card_bg"])
        r_btns.pack(fill=tk.X)

        self.btn_start_scan = tk.Button(
            r_btns,
            text="▶ Démarrer le Scan",
            font=("Segoe UI", 9, "bold"),
            bg="#2e7d32",
            fg="#ffffff",
            activebackground="#388e3c",
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=3,
            command=self.action_start_key_scan,
        )
        self.btn_start_scan.pack(side=tk.LEFT, padx=(0, 6))

        self.btn_stop_scan = tk.Button(
            r_btns,
            text="⏹ Arrêter",
            font=("Segoe UI", 9, "bold"),
            bg="#c62828",
            fg="#ffffff",
            activebackground="#d32f2f",
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=3,
            state=tk.DISABLED,
            command=self.action_stop_key_scan,
        )
        self.btn_stop_scan.pack(side=tk.LEFT)

        self.scan_status_lbl = tk.Label(
            r_btns,
            text="Prêt",
            font=("Segoe UI", 9),
            fg=THEME["text_muted"],
            bg=THEME["card_bg"],
        )
        self.scan_status_lbl.pack(side=tk.RIGHT, padx=6)

    def build_tab_ops(self, parent):
        sec = tk.LabelFrame(
            parent,
            text="Tester une Opération (explore_modes)",
            font=("Segoe UI", 9, "bold"),
            bg=THEME["card_bg"],
            fg=THEME["text"],
            padx=12,
            pady=10,
            bd=1,
        )
        sec.pack(fill=tk.X, pady=(0, 10))

        r1 = tk.Frame(sec, bg=THEME["card_bg"])
        r1.pack(fill=tk.X, pady=(0, 8))

        tk.Label(
            r1,
            text="Code Opération (-o) :",
            font=("Segoe UI", 9),
            fg=THEME["text"],
            bg=THEME["card_bg"],
        ).pack(side=tk.LEFT)
        self.op_entry = tk.Entry(
            r1,
            width=8,
            font=("Consolas", 10),
            bg=THEME["entry_bg"],
            fg=THEME["text"],
            relief="flat",
        )
        self.op_entry.insert(0, "10")
        self.op_entry.pack(side=tk.LEFT, padx=8)

        tk.Button(
            r1,
            text="Tester Opération",
            font=("Segoe UI", 9, "bold"),
            bg=THEME["accent"],
            fg="#ffffff",
            activebackground=THEME["accent_hover"],
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=2,
            command=self.action_test_op,
        ).pack(side=tk.LEFT, padx=10)

        tk.Label(
            sec,
            text="💡 Opérations connues : 1 = Touche télécommande, 9 = Zapping EPG, 10 = Infos décodeur.\n"
            "Testez d'autres entiers (ex: 2, 3, 4, 11...) pour sonder les réponses du décodeur.",
            font=("Segoe UI", 8, "italic"),
            fg=THEME["text_muted"],
            bg=THEME["card_bg"],
            justify=tk.LEFT,
        ).pack(anchor=tk.W)

    def build_tab_epg(self, parent):
        sec = tk.LabelFrame(
            parent,
            text="Tester un Code EPG (explore_epg_ids)",
            font=("Segoe UI", 9, "bold"),
            bg=THEME["card_bg"],
            fg=THEME["text"],
            padx=12,
            pady=10,
            bd=1,
        )
        sec.pack(fill=tk.X, pady=(0, 10))

        r1 = tk.Frame(sec, bg=THEME["card_bg"])
        r1.pack(fill=tk.X, pady=(0, 8))

        tk.Label(
            r1,
            text="Code EPG ID (-e) :",
            font=("Segoe UI", 9),
            fg=THEME["text"],
            bg=THEME["card_bg"],
        ).pack(side=tk.LEFT)
        self.epg_entry = tk.Entry(
            r1,
            width=12,
            font=("Consolas", 10),
            bg=THEME["entry_bg"],
            fg=THEME["text"],
            relief="flat",
        )
        self.epg_entry.insert(0, "192")
        self.epg_entry.pack(side=tk.LEFT, padx=8)

        tk.Button(
            r1,
            text="Tester Zapping EPG",
            font=("Segoe UI", 9, "bold"),
            bg=THEME["accent"],
            fg="#ffffff",
            activebackground=THEME["accent_hover"],
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=2,
            command=self.action_test_epg,
        ).pack(side=tk.LEFT, padx=10)

    # Actions de test
    def action_send_single_key(self):
        k = self.key_entry.get().strip()
        m = self.key_mode_var.get()
        if not k:
            return

        self.log(f"Envoi touche '{k}' (mode {m})...")

        def task():
            if m == "long":
                success, data, err = self.client.send_key_long_press(
                    k, duration=0.2
                )
            else:
                success, data, err = self.client.send_key(k, mode=int(m))
            self._safe_after(
                lambda: self._show_result(
                    f"Touche {k} (mode {m})", success, data, err
                )
            )

        threading.Thread(target=task, daemon=True).start()

    def action_test_op(self):
        op = self.op_entry.get().strip()
        if not op:
            return

        self.log(f"Test opération '{op}'...")

        def task():
            success, data, err = self.client.send_raw_operation(op)
            self._safe_after(
                lambda: self._show_result(f"Opération {op}", success, data, err)
            )

        threading.Thread(target=task, daemon=True).start()

    def action_test_epg(self):
        epg = self.epg_entry.get().strip()
        if not epg:
            return

        self.log(f"Test chaîne EPG '{epg}'...")

        def task():
            success, data, err = self.client.change_channel(epg)
            self._safe_after(
                lambda: self._show_result(
                    f"Chaîne EPG {epg}", success, data, err
                )
            )

        threading.Thread(target=task, daemon=True).start()

    def action_start_key_scan(self):
        try:
            start_k = int(self.scan_start_entry.get().strip())
            end_k = int(self.scan_end_entry.get().strip())
            delay = float(self.scan_delay_entry.get().strip())
        except ValueError:
            messagebox.showerror(
                "Erreur",
                "Veuillez renseigner des entiers valides pour la plage et le délai.",
            )
            return

        self.stop_scan_flag = False
        self.btn_start_scan.config(state=tk.DISABLED)
        self.btn_stop_scan.config(state=tk.NORMAL)
        self.scan_status_lbl.config(
            text=f"Scan en cours ({start_k} à {end_k})...", fg=THEME["warning"]
        )
        self.log(
            f"--- Démarrage du scan des touches de {start_k} à {end_k} (intervalle {delay}s) ---"
        )

        known_codes = set()
        if self.exclude_known_var.get() and self.client.keys:
            for v in self.client.keys.values():
                if str(v).isdigit():
                    known_codes.add(int(v))

        def worker():
            import time

            tested_count = 0
            for key_num in range(start_k, end_k + 1):
                if self.stop_scan_flag:
                    break
                if key_num in known_codes:
                    continue

                self._safe_after(
                    lambda k=key_num: self.scan_status_lbl.config(
                        text=f"Test touche {k}..."
                    )
                )
                success, data, err = self.client.send_key(
                    key_num, mode=0, timeout=1.5
                )
                self._safe_after(
                    lambda k=key_num, s=success, d=data, e=err: self._log_scan_result(
                        k, s, d, e
                    )
                )
                tested_count += 1
                time.sleep(delay)

            self._safe_after(lambda: self._on_scan_finished(tested_count))

        self.scan_thread = threading.Thread(target=worker, daemon=True)
        self.scan_thread.start()

    def action_stop_key_scan(self):
        self.stop_scan_flag = True
        self.scan_status_lbl.config(
            text="Arrêt en cours...", fg=THEME["warning"]
        )

    def _log_scan_result(self, key_num, success, data, err):
        if not self.winfo_exists():
            return
        if success:
            msg = data.get("result", {}).get("message", "ok")
            code = data.get("result", {}).get("responseCode", "?")
            self.log(f"[Touche {key_num}] -> Code: {code}, Msg: '{msg}'")
        else:
            self.log(f"[Touche {key_num}] -> Échec ({err})")

    def _on_scan_finished(self, count):
        if not self.winfo_exists():
            return
        self.btn_start_scan.config(state=tk.NORMAL)
        self.btn_stop_scan.config(state=tk.DISABLED)
        status_txt = (
            "Scan terminé" if not self.stop_scan_flag else "Scan interrompu"
        )
        self.scan_status_lbl.config(
            text=f"{status_txt} ({count} testées)", fg=THEME["success"]
        )
        self.log(f"--- {status_txt} ({count} touches testées) ---")

    def _show_result(self, title, success, data, err):
        if not self.winfo_exists():
            return
        if success:
            self.log(f"[{title}] SUCCÈS :")
            self.log(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            self.log(f"[{title}] ERREUR : {err}")

    def log(self, text):
        now = datetime.now().astimezone().strftime("%H:%M:%S")
        self.console.insert(tk.END, f"[{now}] {text}\n")
        self.console.see(tk.END)

    def clear_log(self):
        self.console.delete("1.0", tk.END)


def main():
    app = OrangeTVApp()
    app.mainloop()


if __name__ == "__main__":
    main()
