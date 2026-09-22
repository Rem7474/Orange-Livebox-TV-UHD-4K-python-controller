"""Génère le foreground de l'icône adaptative Android (glyphe TV + télécommande
seul, sans fond, recadré et centré dans la zone de sécurité) à partir du même
tracé que generate_logo.py. Écrit assets/adaptive_icon_foreground.png, utilisé
par flutter_launcher_icons (voir pubspec.yaml). Dépendance : Pillow."""

import os

from PIL import Image, ImageDraw

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SS = 4
SIZE = 1024 * SS
ORANGE = (255, 102, 0, 255)  # 0xFFFF6600, couleur de marque de l'app
WHITE = (255, 255, 255, 255)

# Fraction du canevas final (1024) que doit occuper la boîte englobante du
# glyphe, pour rester dans la zone de sécurité des icônes adaptatives quel
# que soit le masque du launcher (cercle, squircle, carré arrondi...).
SAFE_ZONE_FRACTION = 0.62


def s(v):
    return int(v * SS)


def generate_glyph():
    """Dessine le glyphe TV + télécommande seul, sans fond, sur un canevas
    transparent (même tracé que generate_master_icon() dans generate_logo.py,
    minus le rectangle arrondi de fond)."""
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    tv_x0, tv_y0, tv_x1, tv_y1 = s(110), s(260), s(650), s(630)
    draw.rounded_rectangle([tv_x0, tv_y0, tv_x1, tv_y1], radius=s(48), fill=WHITE)

    neck_cx = (tv_x0 + tv_x1) // 2
    draw.rounded_rectangle(
        [neck_cx - s(50), tv_y1, neck_cx + s(50), tv_y1 + s(70)],
        radius=s(14),
        fill=WHITE,
    )
    draw.rounded_rectangle(
        [neck_cx - s(140), tv_y1 + s(70), neck_cx + s(140), tv_y1 + s(112)],
        radius=s(18),
        fill=WHITE,
    )

    cx, cy = (tv_x0 + tv_x1) // 2, (tv_y0 + tv_y1) // 2 - s(10)
    tri_w, tri_h = s(110), s(132)
    draw.polygon(
        [
            (cx - tri_w * 0.35, cy - tri_h / 2),
            (cx - tri_w * 0.35, cy + tri_h / 2),
            (cx + tri_w * 0.65, cy),
        ],
        fill=ORANGE,
    )

    remote_w, remote_h = s(300), s(620)
    remote_layer = Image.new("RGBA", (remote_w, remote_h), (0, 0, 0, 0))
    rdraw = ImageDraw.Draw(remote_layer)
    rdraw.rounded_rectangle([0, 0, remote_w - 1, remote_h - 1], radius=s(70), fill=WHITE)

    rcx = remote_w // 2
    rdraw.ellipse([rcx - s(38), s(60), rcx + s(38), s(136)], fill=ORANGE)
    rdraw.rounded_rectangle(
        [rcx - s(60), s(180), rcx + s(60), s(260)], radius=s(20), fill=ORANGE
    )
    for by in (s(320), s(400), s(480)):
        rdraw.ellipse([rcx - s(70), by, rcx - s(18), by + s(52)], fill=ORANGE)
        rdraw.ellipse([rcx + s(18), by, rcx + s(70), by + s(52)], fill=ORANGE)

    remote_layer = remote_layer.rotate(-18, expand=True, resample=Image.BICUBIC)

    # Canevas de travail plus grand que SIZE pour ne perdre aucun pixel de la
    # télécommande pivotée, qui déborderait sinon du cadrage TV d'origine.
    work = Image.new("RGBA", (SIZE * 2, SIZE * 2), (0, 0, 0, 0))
    work.alpha_composite(img, (SIZE // 2, SIZE // 2))
    work.alpha_composite(remote_layer, (SIZE // 2 + s(560), SIZE // 2 + s(430)))

    return work


def recenter_and_scale(glyph, out_size=1024):
    bbox = glyph.getbbox()
    glyph = glyph.crop(bbox)

    target = int(out_size * SAFE_ZONE_FRACTION)
    scale = target / max(glyph.size)
    new_size = (round(glyph.size[0] * scale), round(glyph.size[1] * scale))
    glyph = glyph.resize(new_size, Image.LANCZOS)

    canvas = Image.new("RGBA", (out_size, out_size), (0, 0, 0, 0))
    offset = ((out_size - glyph.size[0]) // 2, (out_size - glyph.size[1]) // 2)
    canvas.alpha_composite(glyph, offset)
    return canvas


if __name__ == "__main__":
    foreground = recenter_and_scale(generate_glyph())
    out_path = os.path.join(
        WORKSPACE, "android_app", "assets", "icon", "adaptive_icon_foreground.png"
    )
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    foreground.save(out_path)
    print(f"Foreground d'icône adaptative généré : {out_path}")
