#!/usr/bin/env python3
"""
Met à jour epg_ids.json, android_app/assets/epg_ids.json et epg_ids.md
à partir du catalogue Orange TV (chaines-tv.orange.fr via iptv-org/epg),
en appliquant la numérotation TNT officielle 2025/2026 (remaniement ARCOM juin 2025).
"""

import json
import os
import xml.etree.ElementTree as ET
from datetime import datetime, timezone

import requests

SOURCE_URL = (
    "https://raw.githubusercontent.com/iptv-org/epg/master/sites/"
    "chaines-tv.orange.fr/chaines-tv.orange.fr.channels.xml"
)

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EPG_JSON_PATH = os.path.join(ROOT_DIR, "epg_ids.json")
ANDROID_EPG_JSON_PATH = os.path.join(ROOT_DIR, "android_app", "assets", "epg_ids.json")
EPG_MD_PATH = os.path.join(ROOT_DIR, "epg_ids.md")

# Numérotation officielle TNT + Canal+ (plan ARCOM juin 2025 / 2026)
AUTHORITATIVE_NUMBERS = {
    1: "192",   # TF1
    2: "4",     # FRANCE 2
    3: "80",    # FRANCE 3
    4: "78",    # FRANCE 4
    5: "47",    # FRANCE 5
    6: "118",   # M6
    7: "111",   # ARTE
    8: "234",   # LCP/PS
    9: "119",   # W9
    10: "195",  # TMC
    11: "446",  # TFX
    12: "482",  # GULLI
    13: "481",  # BFM TV
    14: "226",  # CNEWS
    15: "112",  # LCI
    16: "2111", # FRANCEINFO
    17: "458",  # CSTAR
    18: "4139", # T18
    19: "4138", # NOVO19
    20: "1404", # TF1 SERIES FILMS
    21: "1401", # LA CHAINE L'EQUIPE
    22: "1403", # 6TER
    23: "1402", # RMC STORY
    24: "1400", # RMC DECOUVERTE
    25: "1399", # RMC LIFE (ex Chérie 25)
    40: "34",   # CANAL+
}


def normalize_channel_name(raw_name: str) -> str:
    name = raw_name.strip()
    if name.endswith(":"):
        name = name[:-1].strip()
    return name


def fetch_orange_channels(url: str = SOURCE_URL) -> dict[str, str]:
    """Retourne un dict {epg_id: nom_chaine} depuis le XML iptv-org/epg."""
    resp = requests.get(url, timeout=15)
    resp.raise_for_status()
    root = ET.fromstring(resp.content)

    channels_by_id: dict[str, str] = {}
    for elem in root.findall("channel"):
        epg_id = (elem.attrib.get("site_id") or "").strip()
        name = normalize_channel_name(elem.text or "")
        if not epg_id or not name:
            continue
        channels_by_id.setdefault(epg_id, name)
    return channels_by_id


def load_existing_numbers(path: str) -> dict[int, str]:
    """Récupère les numéros Orange (> 25) encore valides depuis l'ancien epg_ids.json."""
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        old_data = json.load(f)
    preserved: dict[int, str] = {}
    for key, epg_id in old_data.items():
        if key.isdigit():
            num = int(key)
            if num > 25:
                preserved[num] = str(epg_id)
    return preserved


def build_epg_catalog(
    channels_by_id: dict[str, str],
    existing_numbers: dict[int, str],
) -> tuple[dict[str, str], list[tuple[int | None, str, str]]]:
    """Construit le dictionnaire epg_ids.json et la table triée pour epg_ids.md."""
    number_to_epg: dict[int, str] = dict(AUTHORITATIVE_NUMBERS)
    assigned_epg_ids = set(AUTHORITATIVE_NUMBERS.values())

    for num, epg_id in sorted(existing_numbers.items()):
        if num in number_to_epg:
            continue
        if epg_id in channels_by_id and epg_id not in assigned_epg_ids:
            number_to_epg[num] = epg_id
            assigned_epg_ids.add(epg_id)

    epg_to_number = {epg_id: num for num, epg_id in number_to_epg.items()}

    result: dict[str, str] = {}
    for num in sorted(number_to_epg):
        epg_id = number_to_epg[num]
        if epg_id in channels_by_id:
            result[str(num)] = epg_id

    used_names: set[str] = set()
    table_rows: list[tuple[int | None, str, str]] = []

    for num in sorted(number_to_epg):
        epg_id = number_to_epg[num]
        name = channels_by_id.get(epg_id)
        if not name:
            continue
        table_rows.append((num, epg_id, name))

    unnumbered = [
        (epg_id, name)
        for epg_id, name in channels_by_id.items()
        if epg_id not in epg_to_number
    ]
    unnumbered.sort(key=lambda item: item[1].lower())
    for epg_id, name in unnumbered:
        table_rows.append((None, epg_id, name))

    # Ajoute toutes les chaînes par nom (en garantissant l'unicité des clés)
    ordered_by_num_then_name = [
        (epg_id, channels_by_id[epg_id])
        for num in sorted(number_to_epg)
        for epg_id in [number_to_epg[num]]
        if epg_id in channels_by_id
    ] + unnumbered

    for epg_id, name in ordered_by_num_then_name:
        key = name
        if key in used_names or key.isdigit():
            key = f"{name} ({epg_id})"
        used_names.add(key)
        result[key] = epg_id

    return result, table_rows


def write_epg_markdown(table_rows: list[tuple[int | None, str, str]]) -> None:
    today = datetime.now(tz=timezone.utc).date().isoformat()
    source_note = (
        "Données issues du guide Orange TV (`chaines-tv.orange.fr` via `iptv-org/epg`) "
        "avec la numérotation TNT officielle (plan ARCOM 2025/2026)."
    )
    lines = [
        f"# Liste des IDs EPG des chaînes de la TV Orange (mise à jour le {today})",
        "",
        source_note,
        "",
        "N° Chaine | EPG_ID | Nom Chaine",
        "-- | --- | ---",
    ]
    for num, epg_id, name in table_rows:
        num_str = str(num) if num is not None else "-"
        safe_name = name.replace("|", "/")
        lines.append(f"{num_str} | {epg_id} | {safe_name}")
    lines.append("")

    with open(EPG_MD_PATH, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))


def _files_already_up_to_date(payload: str) -> bool:
    if not os.path.exists(EPG_MD_PATH):
        return False
    for path in (EPG_JSON_PATH, ANDROID_EPG_JSON_PATH):
        if not os.path.exists(path):
            return False
        with open(path, "r", encoding="utf-8") as f:
            if f.read() != payload:
                return False
    return True


def main() -> None:
    channels_by_id = fetch_orange_channels()
    existing_numbers = load_existing_numbers(EPG_JSON_PATH)
    epg_dict, table_rows = build_epg_catalog(channels_by_id, existing_numbers)

    payload = json.dumps(epg_dict, ensure_ascii=False, separators=(",", ":"))
    if _files_already_up_to_date(payload):
        print("Aucune modification détectée dans le catalogue des chaînes.")
        return

    for path in (EPG_JSON_PATH, ANDROID_EPG_JSON_PATH):
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(payload)

    write_epg_markdown(table_rows)

    unique_channels = len(channels_by_id)
    numbered_count = sum(1 for k in epg_dict if k.isdigit())
    print(
        f"Mis à jour : {unique_channels} chaînes uniques "
        f"({numbered_count} numérotées, {len(epg_dict)} entrées JSON)."
    )


if __name__ == "__main__":
    main()
