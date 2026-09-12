import base64
import os
import shutil
from PIL import Image
from playwright.sync_api import sync_playwright

workspace = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_logo_base64():
    ico_path = os.path.join(workspace, "app_icon.ico")
    if os.path.exists(ico_path):
        ico = Image.open(ico_path)
        ico.seek(0)
        img = ico.copy()
    else:
        img_path = os.path.join(workspace, "android_app", "android", "app", "src", "main", "res", "mipmap-xxxhdpi", "ic_launcher.png")
        img = Image.open(img_path)
    
    logo_out = os.path.join(workspace, "assets", "logo.png")
    img.save(logo_out)
    with open(logo_out, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def generate_html(logo_b64):
    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800;900&family=JetBrains+Mono:wght@500;600&display=swap" rel="stylesheet">
<style>
  * {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }}

  body {{
    width: 1280px;
    height: 640px;
    background-color: #0A0D14;
    font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    color: #F8FAFC;
    position: relative;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 80px;
  }}

  /* Top accent line */
  .top-accent {{
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, #FF4500 0%, #FF6600 35%, #FFA240 65%, rgba(255, 102, 0, 0.1) 100%);
    z-index: 20;
  }}

  /* Glowing background orbs */
  .glow-orange-main {{
    position: absolute;
    width: 800px;
    height: 800px;
    right: -40px;
    top: -80px;
    background: radial-gradient(circle, rgba(255, 102, 0, 0.28) 0%, rgba(255, 102, 0, 0.08) 45%, transparent 70%);
    pointer-events: none;
    z-index: 1;
  }}

  .glow-orange-left {{
    position: absolute;
    width: 500px;
    height: 500px;
    left: -100px;
    top: 20px;
    background: radial-gradient(circle, rgba(255, 102, 0, 0.08) 0%, transparent 65%);
    pointer-events: none;
    z-index: 1;
  }}

  .glow-blue {{
    position: absolute;
    width: 500px;
    height: 500px;
    left: 120px;
    bottom: -160px;
    background: radial-gradient(circle, rgba(59, 130, 246, 0.07) 0%, transparent 70%);
    pointer-events: none;
    z-index: 1;
  }}

  /* Grid overlay */
  .grid-pattern {{
    position: absolute;
    inset: 0;
    background-image: 
      linear-gradient(rgba(255, 255, 255, 0.035) 1px, transparent 1px),
      linear-gradient(90deg, rgba(255, 255, 255, 0.035) 1px, transparent 1px);
    background-size: 40px 40px;
    mask-image: radial-gradient(ellipse 90% 85% at 50% 50%, black 45%, transparent 95%);
    -webkit-mask-image: radial-gradient(ellipse 90% 85% at 50% 50%, black 45%, transparent 95%);
    pointer-events: none;
    z-index: 2;
  }}

  /* Left column */
  .left-col {{
    position: relative;
    z-index: 10;
    display: flex;
    flex-direction: column;
    justify-content: center;
    max-width: 660px;
  }}

  .category-row {{
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 22px;
  }}

  .badge-category {{
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 6px 14px;
    background: rgba(255, 102, 0, 0.12);
    border: 1px solid rgba(255, 102, 0, 0.35);
    border-radius: 9999px;
    font-size: 12.5px;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #FF8833;
  }}

  .badge-category .dot {{
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background-color: #FF6600;
    box-shadow: 0 0 8px #FF6600;
  }}

  .badge-version {{
    padding: 5px 12px;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 9999px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    font-weight: 600;
    color: #94A3B8;
  }}

  h1 {{
    font-size: 48px;
    font-weight: 900;
    line-height: 1.15;
    letter-spacing: -0.025em;
    margin-bottom: 15px;
    color: #FFFFFF;
  }}

  .highlight {{
    background: linear-gradient(135deg, #FF6600 0%, #FFA040 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }}

  .subtitle {{
    font-size: 18.5px;
    font-weight: 400;
    color: #94A3B8;
    line-height: 1.52;
    margin-bottom: 28px;
  }}

  /* Platform pills */
  .platforms {{
    display: flex;
    gap: 12px;
    margin-bottom: 28px;
  }}

  .platform-card {{
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 9px 17px;
    background: linear-gradient(180deg, rgba(255, 255, 255, 0.06) 0%, rgba(255, 255, 255, 0.02) 100%);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    font-size: 14px;
    font-weight: 600;
    color: #E2E8F0;
    box-shadow: 0 4px 14px rgba(0, 0, 0, 0.3);
  }}

  .platform-card svg {{
    width: 18px;
    height: 18px;
    flex-shrink: 0;
  }}

  /* Feature grid */
  .features {{
    display: grid;
    grid-template-columns: auto auto;
    gap: 13px 26px;
    margin-bottom: 30px;
  }}

  .feature-item {{
    display: flex;
    align-items: center;
    gap: 10px;
    font-size: 14px;
    font-weight: 500;
    color: #CBD5E1;
  }}

  .feature-item svg {{
    width: 18px;
    height: 18px;
    stroke: #FF6600;
    flex-shrink: 0;
  }}

  /* Footer repo tag */
  .footer-meta {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-top: 20px;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
  }}

  .repo-link {{
    display: flex;
    align-items: center;
    gap: 10px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    color: #94A3B8;
  }}

  .repo-link svg {{
    width: 18px;
    height: 18px;
    fill: #CBD5E1;
  }}

  .repo-tags {{
    display: flex;
    gap: 8px;
  }}

  .tag-pill {{
    font-size: 11.5px;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 6px;
    background: rgba(255, 255, 255, 0.05);
    color: #94A3B8;
    border: 1px solid rgba(255, 255, 255, 0.08);
  }}

  /* Right column (Showcase) */
  .right-col {{
    position: relative;
    z-index: 10;
    display: flex;
    align-items: center;
    justify-content: center;
    width: 440px;
    height: 480px;
  }}

  /* Outer showcase card */
  .showcase-card {{
    position: relative;
    width: 330px;
    height: 330px;
    background: radial-gradient(circle at 50% 40%, rgba(255, 102, 0, 0.14) 0%, rgba(255, 255, 255, 0.02) 65%);
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 46px;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 
      0 24px 64px rgba(0, 0, 0, 0.5),
      inset 0 1px 0 rgba(255, 255, 255, 0.15);
  }}

  .showcase-glow {{
    position: absolute;
    width: 260px;
    height: 260px;
    background: radial-gradient(circle, rgba(255, 102, 0, 0.5) 0%, rgba(255, 102, 0, 0.12) 60%, transparent 80%);
    filter: blur(28px);
    z-index: 0;
  }}

  .logo-img {{
    position: relative;
    width: 240px;
    height: 240px;
    z-index: 1;
    filter: drop-shadow(0 20px 35px rgba(255, 102, 0, 0.45)) drop-shadow(0 0 50px rgba(255, 102, 0, 0.25));
  }}

  /* Floating UI badges */
  .floating-pill {{
    position: absolute;
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 18px;
    background: rgba(15, 23, 42, 0.9);
    border: 1px solid rgba(255, 255, 255, 0.15);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border-radius: 14px;
    font-size: 13.5px;
    font-weight: 600;
    color: #F1F5F9;
    box-shadow: 0 16px 36px rgba(0, 0, 0, 0.5);
    z-index: 5;
  }}

  .pill-status {{
    top: -10px;
    right: -20px;
  }}

  .pill-status .live-indicator {{
    width: 9px;
    height: 9px;
    border-radius: 50%;
    background: #10B981;
    box-shadow: 0 0 12px #10B981;
  }}

  .pill-channel {{
    bottom: -10px;
    left: -20px;
  }}

  .pill-channel .tv-dot {{
    width: 22px;
    height: 22px;
    background: linear-gradient(135deg, #FF6600 0%, #FF8833 100%);
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 11px;
    font-weight: 800;
    color: white;
  }}

</style>
</head>
<body>

  <div class="top-accent"></div>
  <div class="glow-orange-main"></div>
  <div class="glow-orange-left"></div>
  <div class="glow-blue"></div>
  <div class="grid-pattern"></div>

  <!-- Left Content -->
  <div class="left-col">
    <div class="category-row">
      <div class="badge-category">
        <div class="dot"></div>
        Orange Livebox TV • Contrôleur
      </div>
      <div class="badge-version">v1.1.4</div>
    </div>

    <h1>
      Livebox TV <span class="highlight">Controller</span>
    </h1>

    <div class="subtitle">
      Télécommande virtuelle, guide des chaînes EPG, découverte automatique sur le réseau local &amp; statut en direct.
    </div>

    <!-- Platforms -->
    <div class="platforms">
      <div class="platform-card">
        <!-- Android SVG -->
        <svg viewBox="0 0 24 24" fill="#3DDC84">
          <path d="M17.523 15.3414c-.5511 0-.9993-.4486-.9993-.9997s.4482-.9993.9993-.9993c.551 0 .9993.4482.9993.9993.0001.5511-.4483.9997-.9993.9997m-11.046 0c-.5511 0-.9993-.4486-.9993-.9997s.4482-.9993.9993-.9993c.5511 0 .9993.4482.9993.9993 0 .5511-.4482.9997-.9993.9997m11.4045-6.02l1.9973-3.4592a.416.416 0 00-.1521-.5676.416.416 0 00-.5676.1521l-2.0223 3.503C15.5902 8.4111 13.8533 8.125 12 8.125s-3.5902.2861-5.1368.8247L4.8409 5.4467a.4161.4161 0 00-.5677-.1521.4157.4157 0 00-.1521.5676l1.9973 3.4592C2.6889 11.1867.3432 14.6589 0 18.761h24c-.3432-4.1021-2.6889-7.5743-6.1185-9.4396"/>
        </svg>
        <span>Android APK</span>
      </div>

      <div class="platform-card">
        <!-- Windows SVG -->
        <svg viewBox="0 0 24 24" fill="#00A4EF">
          <path d="M0 3.449L9.75 2.1v9.451H0m10.949-9.602L24 0v11.4H10.949M0 12.6h9.75v9.451L0 20.699M10.949 12.6H24V24l-13.051-1.802"/>
        </svg>
        <span>Windows EXE</span>
      </div>

      <div class="platform-card">
        <!-- Python SVG -->
        <svg viewBox="0 0 24 24" fill="#FFD43B">
          <path d="M11.914 0C5.825 0 6.2 2.656 6.2 2.656l.007 2.752h5.814v.826H3.84S0 5.792 0 11.913c0 6.124 3.35 5.92 3.35 5.92h2.001v-2.825s-.108-3.35 3.284-3.35h5.618s3.178.051 3.178-3.127V3.127S17.96 0 11.914 0zm-3.3 1.838a1.002 1.002 0 11.001 2.004 1.002 1.002 0 01-.001-2.004zm3.472 22.162c6.089 0 5.714-2.656 5.714-2.656l-.007-2.752h-5.814v-.826h8.181s3.84.442 3.84-5.679c0-6.124-3.35-5.92-3.35-5.92h-2.001v2.825s.108 3.35-3.284 3.35H8.745s-3.178-.051-3.178 3.127v5.404s-.538 3.127 5.509 3.127zm3.3-1.838a1.002 1.002 0 11-.001-2.004 1.002 1.002 0 01.001 2.004z"/>
        </svg>
        <span>Python CLI &amp; GUI</span>
      </div>
    </div>

    <!-- Feature Grid with Feather/Heroic SVGs -->
    <div class="features">
      <div class="feature-item">
        <!-- Wi-Fi scan SVG -->
        <svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M5 12.55a11 11 0 0 1 14.08 0"></path>
          <path d="M1.42 9a16 16 0 0 1 21.16 0"></path>
          <path d="M8.53 16.11a6 6 0 0 1 6.95 0"></path>
          <line x1="12" y1="20" x2="12.01" y2="20"></line>
        </svg>
        <span>Découverte auto IP &amp; Wi-Fi</span>
      </div>

      <div class="feature-item">
        <!-- TV / Channels SVG -->
        <svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="2" y="7" width="20" height="15" rx="2" ry="2"></rect>
          <polyline points="17 2 12 7 7 2"></polyline>
        </svg>
        <span>Zapping 300+ chaînes EPG</span>
      </div>

      <div class="feature-item">
        <!-- Remote / Control SVG -->
        <svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect x="6" y="2" width="12" height="20" rx="3"></rect>
          <line x1="12" y1="6" x2="12" y2="6.01"></line>
          <line x1="12" y1="10" x2="12" y2="10.01"></line>
          <line x1="10" y1="14" x2="14" y2="14"></line>
          <line x1="12" y1="12" x2="12" y2="16"></line>
        </svg>
        <span>D-Pad, Volume &amp; Clavier</span>
      </div>

      <div class="feature-item">
        <!-- Security Shield SVG -->
        <svg viewBox="0 0 24 24" fill="none" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
          <polyline points="9 12 11 14 15 10"></polyline>
        </svg>
        <span>Local Network Protections (LNP)</span>
      </div>
    </div>

    <!-- Meta / GitHub -->
    <div class="footer-meta">
      <div class="repo-link">
        <svg viewBox="0 0 24 24">
          <path d="M12 0C5.37 0 0 5.37 0 12c0 5.31 3.435 9.795 8.205 11.385.6.105.825-.255.825-.57 0-.285-.015-1.23-.015-2.235-3.015.555-3.795-.735-4.035-1.41-.135-.345-.72-1.41-1.23-1.695-.42-.225-1.02-.78-.015-.795.945-.015 1.62.87 1.845 1.23 1.08 1.815 2.805 1.305 3.495.99.105-.78.42-1.305.765-1.605-2.67-.3-5.46-1.335-5.46-5.925 0-1.305.465-2.385 1.23-3.225-.12-.3-.54-1.53.12-3.18 0 0 1.005-.315 3.3 1.23.96-.27 1.98-.405 3-.405s2.04.135 3 .405c2.295-1.56 3.3-1.23 3.3-1.23.66 1.65.24 2.88.12 3.18.765.84 1.23 1.905 1.23 3.225 0 4.605-2.805 5.625-5.475 5.925.435.375.81 1.095.81 2.22 0 1.605-.015 2.895-.015 3.3 0 .315.225.69.825.57A12.02 12.02 0 0024 12c0-6.63-5.37-12-12-12z"/>
        </svg>
        <span>Rem7474 / Orange-Livebox-TV-UHD-4K-python-controller</span>
      </div>

      <div class="repo-tags">
        <span class="tag-pill">MIT License</span>
        <span class="tag-pill">Open Source</span>
      </div>
    </div>
  </div>

  <!-- Right Showcase -->
  <div class="right-col">
    <div class="showcase-card">
      <div class="showcase-glow"></div>
      <img class="logo-img" src="data:image/png;base64,{logo_b64}" alt="App Logo" />
      
      <!-- Floating Pills -->
      <div class="floating-pill pill-status">
        <div class="live-indicator"></div>
        <span>Décodeur Connecté</span>
      </div>

      <div class="floating-pill pill-channel">
        <div class="tv-dot">1</div>
        <span>TF1 HD • En direct</span>
      </div>
    </div>
  </div>

</body>
</html>
"""

def main():
    os.makedirs(os.path.join(workspace, "assets"), exist_ok=True)
    os.makedirs(os.path.join(workspace, ".github"), exist_ok=True)
    logo_b64 = get_logo_base64()
    html_content = generate_html(logo_b64)
    
    preview_output = os.path.join(workspace, "assets", "social-preview.png")
    github_output = os.path.join(workspace, ".github", "social-preview.png")
    
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 640}, device_scale_factor=1)
        page.set_content(html_content, wait_until="networkidle")
        page.evaluate("() => document.fonts.ready")
        page.wait_for_timeout(1000)
        page.screenshot(path=preview_output)
        browser.close()
    
    # Also save to .github/social-preview.png for direct reference
    shutil.copyfile(preview_output, github_output)

    print(f"Generated {preview_output} and {github_output} successfully! Dimensions: 1280x640")

if __name__ == "__main__":
    main()
