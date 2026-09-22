"""Génère le feature graphic Play Store (1024x500) pour Télécommande TV
Orange, dans le même style visuel que le social-preview GitHub mais recadré
pour le format Play et sans références multi-plateformes/GitHub (non
pertinentes pour une fiche store). Dépendances : Pillow, playwright
(pip install Pillow playwright && playwright install chromium)."""

import base64
import os

from PIL import Image
from playwright.sync_api import sync_playwright

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_logo_base64():
    img_path = os.path.join(WORKSPACE, "assets", "logo.png")
    with open(img_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def generate_html(logo_b64):
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    width: 1024px;
    height: 500px;
    background-color: #0A0D14;
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    color: #F8FAFC;
    position: relative;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 56px;
  }}

  .top-accent {{
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, #FF4500 0%, #FF6600 35%, #FFA240 65%, rgba(255,102,0,0.1) 100%);
    z-index: 20;
  }}

  .glow-orange-main {{
    position: absolute;
    width: 620px; height: 620px;
    right: -60px; top: -140px;
    background: radial-gradient(circle, rgba(255,102,0,0.30) 0%, rgba(255,102,0,0.08) 45%, transparent 70%);
    z-index: 1;
  }}

  .glow-orange-left {{
    position: absolute;
    width: 380px; height: 380px;
    left: -100px; bottom: -140px;
    background: radial-gradient(circle, rgba(255,102,0,0.08) 0%, transparent 65%);
    z-index: 1;
  }}

  .grid-pattern {{
    position: absolute;
    inset: 0;
    background-image:
      linear-gradient(rgba(255,255,255,0.035) 1px, transparent 1px),
      linear-gradient(90deg, rgba(255,255,255,0.035) 1px, transparent 1px);
    background-size: 36px 36px;
    mask-image: radial-gradient(ellipse 90% 85% at 50% 50%, black 45%, transparent 95%);
    -webkit-mask-image: radial-gradient(ellipse 90% 85% at 50% 50%, black 45%, transparent 95%);
    z-index: 2;
  }}

  .left-col {{
    position: relative;
    z-index: 10;
    display: flex;
    flex-direction: column;
    justify-content: center;
    max-width: 560px;
  }}

  .badge-category {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 5px 13px;
    background: rgba(255,102,0,0.12);
    border: 1px solid rgba(255,102,0,0.35);
    border-radius: 9999px;
    font-size: 11.5px;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: #FF8833;
    width: fit-content;
    margin-bottom: 18px;
  }}

  .badge-category .dot {{
    width: 6px; height: 6px;
    border-radius: 50%;
    background-color: #FF6600;
    box-shadow: 0 0 8px #FF6600;
  }}

  h1 {{
    font-size: 42px;
    font-weight: 900;
    line-height: 1.12;
    letter-spacing: -0.02em;
    margin-bottom: 13px;
    color: #FFFFFF;
  }}

  .highlight {{
    background: linear-gradient(135deg, #FF6600 0%, #FFA040 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }}

  .subtitle {{
    font-size: 16.5px;
    font-weight: 400;
    color: #94A3B8;
    line-height: 1.48;
    margin-bottom: 26px;
    max-width: 480px;
  }}

  .features {{
    display: flex;
    flex-direction: column;
    gap: 11px;
  }}

  .feature-item {{
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 14.5px;
    font-weight: 500;
    color: #CBD5E1;
  }}

  .feature-item svg {{
    width: 18px; height: 18px;
    stroke: #FF6600;
    flex-shrink: 0;
  }}

  .right-col {{
    position: relative;
    z-index: 10;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 340px;
    height: 400px;
  }}

  .showcase-card {{
    position: relative;
    width: 260px; height: 260px;
    background: radial-gradient(circle at 50% 40%, rgba(255,102,0,0.14) 0%, rgba(255,255,255,0.02) 65%);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 38px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 20px 54px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.15);
  }}

  .showcase-glow {{
    position: absolute;
    width: 200px; height: 200px;
    background: radial-gradient(circle, rgba(255,102,0,0.5) 0%, rgba(255,102,0,0.12) 60%, transparent 80%);
    filter: blur(24px);
    z-index: 0;
  }}

  .logo-img {{
    position: relative;
    width: 190px; height: 190px;
    z-index: 1;
    filter: drop-shadow(0 16px 28px rgba(255,102,0,0.45)) drop-shadow(0 0 40px rgba(255,102,0,0.25));
  }}

  .floating-pill {{
    position: absolute;
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px 15px;
    background: rgba(15,23,42,0.9);
    border: 1px solid rgba(255,255,255,0.15);
    border-radius: 12px;
    font-size: 12px;
    font-weight: 600;
    color: #F1F5F9;
    box-shadow: 0 12px 28px rgba(0,0,0,0.5);
    z-index: 5;
  }}

  .pill-status {{ top: -6px; right: -26px; }}
  .pill-status .live-indicator {{
    width: 8px; height: 8px;
    border-radius: 50%;
    background: #10B981;
    box-shadow: 0 0 10px #10B981;
  }}

  .pill-channel {{ bottom: -6px; left: -30px; }}
  .pill-channel .tv-dot {{
    width: 19px; height: 19px;
    background: linear-gradient(135deg, #FF6600 0%, #FF8833 100%);
    border-radius: 5px;
    display: flex; align-items: center; justify-content: center;
    font-size: 10px; font-weight: 800; color: white;
  }}
</style>
</head>
<body>

  <div class="top-accent"></div>
  <div class="glow-orange-main"></div>
  <div class="glow-orange-left"></div>
  <div class="grid-pattern"></div>

  <div class="left-col">
    <div class="badge-category">
      <div class="dot"></div>
      Compatible Orange Livebox TV
    </div>

    <h1>Télécommande TV <span class="highlight">Orange</span></h1>

    <div class="subtitle">
      Télécommande virtuelle, guide de 300+ chaînes et détection automatique sur le réseau local.
    </div>

    <div class="features">
      <div class="feature-item">
        <svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M5 12.55a11 11 0 0 1 14.08 0"></path>
          <path d="M1.42 9a16 16 0 0 1 21.16 0"></path>
          <path d="M8.53 16.11a6 6 0 0 1 6.95 0"></path>
          <line x1="12" y1="20" x2="12.01" y2="20"></line>
        </svg>
        <span>Détection automatique du décodeur sur le Wi-Fi</span>
      </div>
      <div class="feature-item">
        <svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="2" y="7" width="20" height="15" rx="2" ry="2"></rect>
          <polyline points="17 2 12 7 7 2"></polyline>
        </svg>
        <span>Zapping instantané sur 300+ chaînes</span>
      </div>
      <div class="feature-item">
        <svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="6" y="2" width="12" height="20" rx="3"></rect>
          <line x1="12" y1="6" x2="12" y2="6.01"></line>
          <line x1="12" y1="10" x2="12" y2="10.01"></line>
          <line x1="10" y1="14" x2="14" y2="14"></line>
        </svg>
        <span>D-Pad, volume, clavier numérique &amp; retour haptique</span>
      </div>
    </div>
  </div>

  <div class="right-col">
    <div class="showcase-card">
      <div class="showcase-glow"></div>
      <img class="logo-img" src="data:image/png;base64,{logo_b64}" alt="App Logo" />

      <div class="floating-pill pill-status">
        <div class="live-indicator"></div>
        <span>Décodeur connecté</span>
      </div>

      <div class="floating-pill pill-channel">
        <div class="tv-dot">1</div>
        <span>TF1 • En direct</span>
      </div>
    </div>
  </div>

</body>
</html>
"""


def main():
    out_dir = os.path.join(WORKSPACE, "store-assets")
    os.makedirs(out_dir, exist_ok=True)
    logo_b64 = get_logo_base64()
    html_content = generate_html(logo_b64)

    output = os.path.join(out_dir, "feature-graphic.png")

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1024, "height": 500}, device_scale_factor=1)
        page.set_content(html_content, wait_until="networkidle")
        page.evaluate("() => document.fonts.ready")
        page.wait_for_timeout(800)
        page.screenshot(path=output)
        browser.close()

    im = Image.open(output)
    assert im.size == (1024, 500), f"Taille inattendue : {im.size}"

    print(f"Feature graphic généré : {output} ({im.size[0]}x{im.size[1]})")


if __name__ == "__main__":
    main()
