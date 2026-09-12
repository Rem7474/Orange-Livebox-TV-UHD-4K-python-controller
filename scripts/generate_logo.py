"""Génère le logo de l'app (télévision + télécommande) et l'écrit directement
dans les icônes Android (toutes densités) et le app_icon.ico de l'exécutable
Windows. Dépendance : Pillow (pip install Pillow)."""

import os

from PIL import Image, ImageDraw

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SS = 4
SIZE = 1024 * SS
ORANGE = (255, 102, 0, 255)  # 0xFFFF6600, couleur de marque de l'app
WHITE = (255, 255, 255, 255)

ANDROID_SIZES = {
    "mipmap-mdpi": 48,
    "mipmap-hdpi": 72,
    "mipmap-xhdpi": 96,
    "mipmap-xxhdpi": 144,
    "mipmap-xxxhdpi": 192,
}
ICO_SIZES = [16, 24, 32, 48, 64, 128, 256]


def s(v):
    return int(v * SS)


def generate_master_icon():
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([0, 0, SIZE - 1, SIZE - 1], radius=s(224), fill=ORANGE)

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
    img.alpha_composite(remote_layer, (s(560), s(430)))

    return img.resize((1024, 1024), Image.LANCZOS)


def write_assets(master):
    for name, size in ANDROID_SIZES.items():
        out_dir = os.path.join(
            WORKSPACE, "android_app", "android", "app", "src", "main", "res", name
        )
        os.makedirs(out_dir, exist_ok=True)
        master.resize((size, size), Image.LANCZOS).save(
            os.path.join(out_dir, "ic_launcher.png")
        )

    master.save(
        os.path.join(WORKSPACE, "app_icon.ico"),
        sizes=[(s, s) for s in ICO_SIZES],
    )


if __name__ == "__main__":
    write_assets(generate_master_icon())
    print("Logo régénéré : icônes Android + app_icon.ico")
