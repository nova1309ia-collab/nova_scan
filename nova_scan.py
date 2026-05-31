import streamlit as st
from PIL import Image
import io
import numpy as np
import base64
import json

st.set_page_config(
    page_title="Nova Scan",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
html, body, [data-testid="stAppViewContainer"] {
    background-color: #050d1a;
    color: #e0e8ff;
    font-family: 'Segoe UI', sans-serif;
}
[data-testid="stHeader"] { display: none; }
[data-testid="stFileUploader"] { display: none !important; }
.nova-title {
    text-align: center; font-size: 2rem; font-weight: 700;
    color: #2979ff; margin-bottom: 0.2rem; letter-spacing: 2px;
}
.nova-subtitle {
    text-align: center; font-size: 0.85rem; color: #7a90b8;
    margin-bottom: 1.8rem; letter-spacing: 1px; text-transform: uppercase;
}
.pdf-info {
    background: rgba(0,229,255,0.06); border: 1px solid rgba(0,229,255,0.2);
    border-radius: 10px; padding: 1rem 1.2rem; margin: 1rem 0; font-size: 0.85rem;
}
.pdf-info span { color: #00e5ff; font-weight: 600; }
.badge-crop {
    display:inline-block; background:rgba(0,230,118,0.12); border:1px solid #00e676;
    border-radius:20px; padding:3px 12px; font-size:0.72rem; color:#00e676; margin-left:8px;
}
.badge-manual {
    display:inline-block; background:rgba(41,121,255,0.15); border:1px solid #2979ff;
    border-radius:20px; padding:3px 12px; font-size:0.72rem; color:#82b1ff; margin-left:8px;
}
.badge-no-crop {
    display:inline-block; background:rgba(255,193,7,0.12); border:1px solid #ffc107;
    border-radius:20px; padding:3px 12px; font-size:0.72rem; color:#ffc107; margin-left:8px;
}
[data-testid="stDownloadButton"] > button {
    background-color: #2979ff !important; color: white !important; border: none !important;
    border-radius: 14px !important; font-weight: 700 !important; font-size: 1.1rem !important;
    padding: 0.9rem 2rem !important; width: 100% !important; letter-spacing: 1px !important;
    box-shadow: 0 4px 20px rgba(41,121,255,0.4) !important;
}
[data-testid="stButton"] > button {
    background: transparent !important; border: 1px solid #2979ff55 !important;
    color: #7a90b8 !important; border-radius: 8px !important;
    width: 100% !important; margin-top: 0.5rem !important;
}
.preview-label { font-size:0.75rem; color:#7a90b8; text-align:center; margin-bottom:0.3rem; }
.sep { border: none; border-top: 1px solid #0d1e38; margin: 1.5rem 0; }
.tip-box {
    background: rgba(255,193,7,0.06); border-left: 3px solid #ffc107;
    border-radius: 0 8px 8px 0; padding: 0.7rem 1rem;
    font-size: 0.78rem; color: #c9a227; margin-bottom: 1rem;
}
.steps-row { display:flex; justify-content:center; gap:0.5rem; margin-bottom:1.2rem; flex-wrap:wrap; }
.step-badge {
    background:rgba(41,121,255,0.12); border:1px solid #2979ff44;
    border-radius:20px; padding:4px 14px; font-size:0.72rem; color:#7a90b8; white-space:nowrap;
}
.step-active { background:rgba(41,121,255,0.3); border-color:#2979ff; color:#fff; font-weight:600; }
/* Cacher le champ relay */
div[data-testid="stTextInput"] { display: none !important; }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="nova-title">📄 NOVA SCAN</div>', unsafe_allow_html=True)
st.markdown('<div class="nova-subtitle">Numérisation instantanée · Zéro installation</div>', unsafe_allow_html=True)

# ── Reset ─────────────────────────────────────────────────────────────────────
if st.session_state.get("reset_requested"):
    st.session_state["reset_requested"] = False
    st.session_state["scan_key"] = st.session_state.get("scan_key", 0) + 1
    for k in list(st.session_state.keys()):
        if k.startswith(("state_", "corners_", "badge_", "_relay_")):
            del st.session_state[k]

if "scan_key" not in st.session_state:
    st.session_state["scan_key"] = 0
sk = st.session_state["scan_key"]


# ── Correction EXIF ───────────────────────────────────────────────────────────
def corriger_orientation(img):
    try:
        from PIL import ExifTags
        exif = img._getexif()
        if exif:
            for tag, val in exif.items():
                if ExifTags.TAGS.get(tag) == "Orientation":
                    rotations = {3: 180, 6: 270, 8: 90}
                    if val in rotations:
                        img = img.rotate(rotations[val], expand=True)
                    break
    except Exception:
        pass
    return img


# ── Détection automatique ─────────────────────────────────────────────────────
def detecter_contour_auto(img_pil):
    try:
        import cv2
        img_np = np.array(img_pil.convert("RGB"))
        h, w = img_np.shape[:2]
        scale = 800 / max(h, w)
        small = cv2.resize(img_np, (int(w*scale), int(h*scale)))
        gray = cv2.cvtColor(small, cv2.COLOR_RGB2GRAY)
        blur = cv2.GaussianBlur(gray, (5,5), 0)
        edges = cv2.Canny(blur, 50, 150)
        edges = cv2.dilate(edges, np.ones((3,3), np.uint8), iterations=2)
        contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]
        for c in contours:
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02*peri, True)
            if len(approx)==4 and cv2.contourArea(c) > (small.shape[0]*small.shape[1]*0.2):
                pts = (approx.reshape(4,2)/scale).astype(np.float32)
                s = pts.sum(axis=1); diff = np.diff(pts, axis=1)
                ordered = np.zeros((4,2), dtype=np.float32)
                ordered[0]=pts[np.argmin(s)];  ordered[1]=pts[np.argmin(diff)]
                ordered[2]=pts[np.argmax(s)];  ordered[3]=pts[np.argmax(diff)]
                return ordered.tolist()
        return None
    except Exception:
        return None


# ── Recadrage perspective ─────────────────────────────────────────────────────
def recadrer_depuis_coins(img_pil, coins):
    import cv2
    img_np = np.array(img_pil.convert("RGB"))
    pts = np.array(coins, dtype=np.float32)
    wA = np.linalg.norm(pts[2]-pts[3]); wB = np.linalg.norm(pts[1]-pts[0])
    hA = np.linalg.norm(pts[1]-pts[2]); hB = np.linalg.norm(pts[0]-pts[3])
    maxW = int(max(wA,wB)); maxH = int(max(hA,hB))
    dst = np.array([[0,0],[maxW-1,0],[maxW-1,maxH-1],[0,maxH-1]], dtype=np.float32)
    M = cv2.getPerspectiveTransform(pts, dst)
    warped = cv2.warpPerspective(img_np, M, (maxW, maxH))
    gray = cv2.cvtColor(warped, cv2.COLOR_RGB2GRAY)
    clean = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 21, 10)
    return Image.fromarray(clean).convert("RGB")


# ── Conversion → PDF ──────────────────────────────────────────────────────────
def image_vers_pdf(img):
    img = corriger_orientation(img)
    if img.mode != "RGB":
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="PDF", resolution=150)
    buf.seek(0)
    return buf.getvalue(), img


# ── Canvas interactif ─────────────────────────────────────────────────────────
def canvas_recadrage(img_pil, coins_initiales, relay_input_key):
    """
    Affiche le canvas avec 4 coins déplaçables.
    Quand l'utilisateur confirme, le JS écrit dans le st.text_input
    identifié par relay_input_key via manipulation DOM native Streamlit.
    """
    import streamlit.components.v1 as components

    # Redimensionner pour alléger le base64 (max 1200px)
    img_display = img_pil.copy()
    max_dim = 1200
    w_o, h_o = img_display.size
    if max(w_o, h_o) > max_dim:
        scale = max_dim / max(w_o, h_o)
        img_display = img_display.resize((int(w_o*scale), int(h_o*scale)), Image.LANCZOS)

    w_disp, h_disp = img_display.size
    scale_x = w_o / w_disp  # pour reconvertir en coords originales
    scale_y = h_o / h_disp

    buf = io.BytesIO()
    img_display.save(buf, format="JPEG", quality=82)
    b64 = base64.b64encode(buf.getvalue()).decode()

    # Coins en coords display
    if coins_initiales:
        coins_disp = [[c[0]/scale_x, c[1]/scale_y] for c in coins_initiales]
    else:
        mx, my = w_disp*0.08, h_disp*0.08
        coins_disp = [
            [mx, my], [w_disp-mx, my],
            [w_disp-mx, h_disp-my], [mx, h_disp-my]
        ]
    coins_json = json.dumps(coins_disp)
    scales_json = json.dumps([scale_x, scale_y])

    # Le JS va chercher l'input Streamlit par son data-testid aria-label
    # On passe le relay_input_key pour qu'il trouve le bon champ
    html = f"""<!DOCTYPE html><html><head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#050d1a;font-family:'Segoe UI',sans-serif;padding:2px;overflow:hidden}}
#wrap{{position:relative;width:100%;max-width:600px;margin:0 auto}}
#cvWrap{{position:relative;width:100%;}}
canvas{{display:block;width:100%;border-radius:10px;touch-action:none;cursor:crosshair;}}
.toolbar{{display:flex;gap:8px;margin-top:10px}}
.btn{{flex:1;padding:14px 8px;border-radius:14px;font-size:.95rem;font-weight:700;
      cursor:pointer;border:none;font-family:'Segoe UI',sans-serif;
      -webkit-tap-highlight-color:transparent;transition:transform .1s,opacity .1s}}
.btn:active{{transform:scale(.97);opacity:.85}}
.btn-ok{{background:linear-gradient(135deg,#2979ff,#1565c0);color:#fff;
         box-shadow:0 4px 18px rgba(41,121,255,.5)}}
.btn-skip{{background:rgba(255,255,255,.06);border:1px solid #2979ff44!important;color:#7a90b8}}
.hint{{text-align:center;font-size:.75rem;color:#4a6080;margin-top:7px;letter-spacing:.3px}}
#status{{text-align:center;font-size:.78rem;color:#00e676;margin-top:5px;min-height:1.2em}}
</style></head><body>
<div id="wrap">
  <div id="cvWrap">
    <canvas id="cv"></canvas>
  </div>
  <div class="toolbar">
    <button class="btn btn-skip" onclick="doSkip()">⏭ Sans recadrage</button>
    <button class="btn btn-ok" onclick="doConfirm()">✓ Confirmer</button>
  </div>
  <div class="hint">Glissez les 4 coins 🔵 sur les bords du document</div>
  <div id="status"></div>
</div>
<script>
const IW={w_disp}, IH={h_disp};
const SCALES={scales_json};   // [sx, sy] pour reconvertir en coords originales
const COINS_INIT={coins_json};
const RELAY_KEY='{relay_input_key}';

const cv=document.getElementById('cv');
const ctx=cv.getContext('2d');
// Taille interne = taille affichée (on travaille en coords display)
cv.width=IW; cv.height=IH;

const img=new Image();
img.src='data:image/jpeg;base64,{b64}';
let coins=COINS_INIT.map(c=>({{x:c[0],y:c[1]}}));
let drag=null;
const R=Math.max(20, Math.min(IW,IH)*0.042);

img.onload=()=>draw();

// ── Dessin ────────────────────────────────────────────────────────
function draw(){{
  ctx.clearRect(0,0,IW,IH);

  // 1. Image de fond
  ctx.drawImage(img,0,0);

  // 2. Masque semi-transparent HORS zone sélectionnée
  //    On utilise un canvas offscreen pour éviter le bug destination-out
  const offscreen=new OffscreenCanvas(IW,IH);
  const oc=offscreen.getContext('2d');
  oc.fillStyle='rgba(0,0,0,0.55)';
  oc.fillRect(0,0,IW,IH);
  // Trouer la zone doc
  oc.globalCompositeOperation='destination-out';
  oc.beginPath();
  oc.moveTo(coins[0].x,coins[0].y);
  coins.forEach((c,i)=>{{if(i)oc.lineTo(c.x,c.y)}});
  oc.closePath();
  oc.fillStyle='rgba(0,0,0,1)';
  oc.fill();
  ctx.drawImage(offscreen,0,0);

  // 3. Contour bleu
  ctx.beginPath();
  ctx.moveTo(coins[0].x,coins[0].y);
  coins.forEach((c,i)=>{{if(i)ctx.lineTo(c.x,c.y)}});
  ctx.closePath();
  ctx.strokeStyle='#2979ff';
  ctx.lineWidth=Math.max(2.5,R*.12);
  ctx.stroke();

  // 4. Poignées
  coins.forEach((c,i)=>{{
    // Halo
    ctx.beginPath(); ctx.arc(c.x,c.y,R+6,0,Math.PI*2);
    ctx.fillStyle='rgba(0,0,0,.25)'; ctx.fill();
    // Cercle
    ctx.beginPath(); ctx.arc(c.x,c.y,R,0,Math.PI*2);
    const active=drag===i;
    ctx.fillStyle=active?'#82b1ff':'#2979ff'; ctx.fill();
    ctx.strokeStyle='#fff'; ctx.lineWidth=Math.max(2,R*.1); ctx.stroke();
    // Croix
    const s=R*.38;
    ctx.strokeStyle='rgba(255,255,255,.85)'; ctx.lineWidth=Math.max(1.5,R*.08);
    ctx.beginPath(); ctx.moveTo(c.x-s,c.y); ctx.lineTo(c.x+s,c.y); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(c.x,c.y-s); ctx.lineTo(c.x,c.y+s); ctx.stroke();
    // Label coin
    const labels=['↖','↗','↘','↙'];
    ctx.fillStyle='rgba(255,255,255,.7)';
    ctx.font=`bold ${{Math.max(11,R*.45)}}px Segoe UI`;
    ctx.textAlign='center'; ctx.textBaseline='middle';
    ctx.fillText(labels[i], c.x, c.y);
  }});
}}

// ── Coords canvas ─────────────────────────────────────────────────
function gp(e){{
  const r=cv.getBoundingClientRect();
  const sx=IW/r.width, sy=IH/r.height;
  const src=e.touches?e.touches[0]:e;
  return{{
    x:Math.max(0,Math.min(IW,(src.clientX-r.left)*sx)),
    y:Math.max(0,Math.min(IH,(src.clientY-r.top)*sy))
  }};
}}
function hit(p){{
  for(let i=0;i<4;i++){{
    const dx=p.x-coins[i].x, dy=p.y-coins[i].y;
    if(Math.sqrt(dx*dx+dy*dy)<R*2.2) return i;
  }}
  return null;
}}

cv.addEventListener('mousedown',e=>{{e.preventDefault();drag=hit(gp(e));draw();}});
cv.addEventListener('touchstart',e=>{{e.preventDefault();drag=hit(gp(e));draw();}},{{passive:false}});
cv.addEventListener('mousemove',e=>{{if(drag===null)return;coins[drag]=gp(e);draw();}});
cv.addEventListener('touchmove',e=>{{e.preventDefault();if(drag===null)return;coins[drag]=gp(e);draw();}},{{passive:false}});
cv.addEventListener('mouseup',()=>{{drag=null;draw();}});
cv.addEventListener('touchend',()=>{{drag=null;draw();}});

// ── Écriture dans Streamlit via DOM ───────────────────────────────
function writeRelay(value){{
  // Cherche le bon input Streamlit (celui dont le label=RELAY_KEY)
  // Streamlit génère un input[type=text] pour chaque st.text_input
  try{{
    const parent=window.parent.document;
    // Cherche par aria-label ou par data-testid contenant la clé
    let found=null;
    const inputs=parent.querySelectorAll('input[type="text"]');
    for(const inp of inputs){{
      // Streamlit met le label comme aria-label sur certaines versions,
      // ou on cherche le plus proche input vide / marqué relay
      if(inp.getAttribute('aria-label')===RELAY_KEY || inp.dataset.novaRelay===RELAY_KEY){{
        found=inp; break;
      }}
    }}
    // Fallback : prendre le premier input text vide non marqué
    if(!found){{
      for(const inp of inputs){{
        if(!inp.dataset.novaRelay){{
          found=inp; break;
        }}
      }}
    }}
    if(!found){{ document.getElementById('status').textContent='⚠ Champ non trouvé'; return false; }}
    found.dataset.novaRelay=RELAY_KEY;
    const setter=Object.getOwnPropertyDescriptor(window.parent.HTMLInputElement.prototype,'value').set;
    setter.call(found, value);
    found.dispatchEvent(new Event('input',{{bubbles:true}}));
    return true;
  }}catch(err){{
    document.getElementById('status').textContent='Erreur: '+err.message;
    return false;
  }}
}}

function doConfirm(){{
  // Reconvertir en coords image originale
  const result=coins.map(c=>[
    Math.round(c.x*SCALES[0]),
    Math.round(c.y*SCALES[1])
  ]);
  document.getElementById('status').textContent='⏳ Application du recadrage...';
  const ok=writeRelay('CONFIRM:'+JSON.stringify(result));
  if(!ok) document.getElementById('status').textContent='⚠ Réessayez ou utilisez "Sans recadrage"';
}}

function doSkip(){{
  document.getElementById('status').textContent='⏳ Chargement...';
  writeRelay('SKIP');
}}
</script>
</body></html>"""

    components.html(html, height=660, scrolling=False)


# ── Affichage résultat ────────────────────────────────────────────────────────
def afficher_resultat(img, nom_fichier, badge_mode, key_dl, key_btn):
    try:
        pdf_bytes, img_rgb = image_vers_pdf(img)
        w, h = img_rgb.size
        taille_ko = len(pdf_bytes)/1024
        taille_str = f"{taille_ko/1024:.1f} Mo" if taille_ko>=1024 else f"{taille_ko:.0f} Ko"

        st.markdown('<div class="steps-row">'
                    '<div class="step-badge">① ✓ Photo prise</div>'
                    '<div class="step-badge">② ✓ Recadrage</div>'
                    '<div class="step-badge step-active">③ Télécharger</div>'
                    '</div>', unsafe_allow_html=True)

        st.markdown('<div class="preview-label">APERÇU DU DOCUMENT</div>', unsafe_allow_html=True)
        st.image(img_rgb, use_container_width=True)

        badges = {
            "auto":   '<span class="badge-crop">✂️ Recadré auto</span>',
            "manual": '<span class="badge-manual">✋ Recadrage manuel</span>',
            "none":   '<span class="badge-no-crop">⚠️ Sans recadrage</span>',
        }
        st.markdown(f"""<div class="pdf-info">
            📄 PDF prêt&nbsp;! {badges.get(badge_mode,'')}
            <br>Taille : <span>{taille_str}</span> &nbsp;|&nbsp; Résolution : <span>{w} × {h} px</span>
        </div>""", unsafe_allow_html=True)

        st.download_button(
            label="⬇️  TÉLÉCHARGER LE PDF",
            data=pdf_bytes, file_name=nom_fichier,
            mime="application/pdf", key=key_dl,
        )
    except Exception as e:
        st.error(f"Erreur PDF : {e}")

    st.markdown('<hr class="sep">', unsafe_allow_html=True)
    if st.button("🔄  Scanner un autre document", key=key_btn):
        st.session_state["reset_requested"] = True
        st.rerun()


# ── Flux principal ────────────────────────────────────────────────────────────
def flux_image(img_pil, nom_pdf, prefix):
    state_key   = f"state_{prefix}"
    corners_key = f"corners_{prefix}"
    badge_key   = f"badge_{prefix}"
    relay_key   = f"relay_{prefix}_{sk}"

    if state_key not in st.session_state:
        st.session_state[state_key] = "detecting"

    state = st.session_state[state_key]

    # ── DÉTECTION ──
    if state == "detecting":
        with st.spinner("🔍 Détection du document..."):
            coins = detecter_contour_auto(img_pil)
        st.session_state[corners_key] = coins
        st.session_state[state_key] = "canvas"
        st.rerun()

    # ── CANVAS ──
    elif state == "canvas":
        st.markdown('<div class="steps-row">'
                    '<div class="step-badge">① ✓ Photo prise</div>'
                    '<div class="step-badge step-active">② Ajuster le recadrage</div>'
                    '<div class="step-badge">③ PDF</div>'
                    '</div>', unsafe_allow_html=True)

        coins = st.session_state.get(corners_key)
        if coins:
            st.markdown("""<div style="background:rgba(0,230,118,.07);border:1px solid #00e67644;
                border-radius:10px;padding:.55rem 1rem;font-size:.78rem;color:#00e676;
                margin-bottom:.7rem;text-align:center;">
                ✂️ Document détecté — ajustez les coins si besoin</div>""",
                unsafe_allow_html=True)
        else:
            st.markdown("""<div class="tip-box">
                💡 Document non détecté. Placez les coins manuellement.</div>""",
                unsafe_allow_html=True)

        # Champ relay (caché par CSS)
        relay_val = st.text_input("relay", key=relay_key, label_visibility="collapsed")

        # Canvas
        canvas_recadrage(img_pil, coins, relay_key)

        # Traitement de la réponse du JS
        if relay_val.startswith("CONFIRM:"):
            try:
                corners_from_js = json.loads(relay_val[8:])
                st.session_state[corners_key] = corners_from_js
                st.session_state[badge_key] = "manual"
                st.session_state[state_key] = "result"
                st.rerun()
            except Exception as e:
                st.error(f"Erreur recadrage : {e}")
        elif relay_val == "SKIP":
            st.session_state[badge_key] = "none"
            st.session_state[state_key] = "result"
            st.rerun()

    # ── RÉSULTAT ──
    elif state == "result":
        badge  = st.session_state.get(badge_key, "none")
        corners = st.session_state.get(corners_key)

        if badge == "none" or not corners:
            img_finale = img_pil
        else:
            try:
                img_finale = recadrer_depuis_coins(img_pil, corners)
            except Exception:
                img_finale = img_pil
                st.warning("Recadrage impossible, image originale utilisée.")

        afficher_resultat(
            img_finale, nom_pdf, badge,
            key_dl=f"dl_{prefix}_{sk}",
            key_btn=f"reset_{prefix}_{sk}",
        )


# ══════════════════════════════════════════════════════════════════════════════
# ONGLETS
# ══════════════════════════════════════════════════════════════════════════════
tab_mobile, tab_import = st.tabs(["📷  Caméra", "🖼️  Importer"])

# ── ONGLET CAMÉRA ─────────────────────────────────────────────────────────────
with tab_mobile:
    photo = st.file_uploader(
        label="photo", type=["jpg","jpeg","png","webp","bmp","heic"],
        label_visibility="collapsed", key=f"cam_{sk}",
    )
    if photo is None:
        import streamlit.components.v1 as components
        components.html("""
        <style>
        *{box-sizing:border-box;margin:0;padding:0}
        body{background:transparent;font-family:'Segoe UI',sans-serif}
        .card{background:rgba(41,121,255,.07);border:1.5px dashed #2979ff88;border-radius:18px;
              padding:1.4rem 1rem;margin-bottom:1rem;text-align:center}
        .icon{font-size:3.5rem;display:block;margin-bottom:.5rem;animation:pulse 2s infinite}
        @keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.08)}}
        .title{font-size:1.05rem;font-weight:700;color:#fff;margin-bottom:.5rem}
        .tips{text-align:left;display:inline-block}
        .tip{font-size:.82rem;color:#a0b4d0;margin:.25rem 0;display:flex;align-items:center;gap:.4rem}
        .big-btn{display:block;width:100%;background:linear-gradient(135deg,#2979ff,#1a5cd4);
          color:#fff;border:none;border-radius:16px;padding:1.1rem;font-size:1.15rem;font-weight:700;
          letter-spacing:1px;cursor:pointer;box-shadow:0 4px 24px rgba(41,121,255,.55);
          font-family:'Segoe UI',sans-serif;text-align:center;margin-bottom:.8rem;
          -webkit-tap-highlight-color:transparent;transition:transform .1s,opacity .1s}
        .big-btn:active{transform:scale(.97);opacity:.9}
        .badge{display:flex;align-items:center;justify-content:center;gap:.4rem;
          background:rgba(0,230,118,.08);border:1px solid #00e67644;border-radius:10px;
          padding:.5rem;font-size:.75rem;color:#00e676;margin-bottom:.8rem}
        .steps{display:flex;justify-content:center;gap:.4rem;flex-wrap:wrap}
        .step{background:rgba(41,121,255,.12);border:1px solid #2979ff44;border-radius:20px;
              padding:4px 12px;font-size:.7rem;color:#7a90b8}
        .step.active{background:rgba(41,121,255,.3);border-color:#2979ff;color:#fff;font-weight:600}
        </style>
        <div class="card">
          <span class="icon">📷</span>
          <div class="title">Photographiez votre document</div>
          <div class="tips">
            <div class="tip">💡 Fond contrasté (table sombre ou claire)</div>
            <div class="tip">☀️ Bonne lumière, sans reflets</div>
            <div class="tip">📐 Les 4 coins du document visibles</div>
          </div>
        </div>
        <div class="badge">✂️ Recadrage manuel interactif — ajustez les 4 coins</div>
        <button class="big-btn" onclick="openCamera()">📷 &nbsp; Ouvrir l'appareil photo</button>
        <div class="steps">
          <div class="step active">① Photo</div>
          <div class="step">② Ajuster</div>
          <div class="step">③ PDF</div>
        </div>
        <script>
        function openCamera(){
          try{
            const inp=window.parent.document.querySelector('input[type="file"]');
            if(inp){inp.setAttribute('capture','environment');inp.setAttribute('accept','image/*');inp.click();return;}
          }catch(e){}
          const inp=document.createElement('input');inp.type='file';inp.accept='image/*';
          inp.setAttribute('capture','environment');inp.click();
        }
        </script>
        """, height=390, scrolling=False)
    else:
        img_mob = corriger_orientation(Image.open(photo))
        flux_image(img_mob, "nova_scan_document.pdf", "mob")

# ── ONGLET IMPORT ─────────────────────────────────────────────────────────────
with tab_import:
    st.markdown('<div class="tip-box">💡 <strong>Formats :</strong> JPG, PNG, WEBP, BMP</div>',
                unsafe_allow_html=True)
    fichier = st.file_uploader(
        label="Choisir une image", type=["jpg","jpeg","png","webp","bmp"],
        label_visibility="collapsed", key=f"upload_{sk}",
    )
    if fichier is not None:
        img_imp = corriger_orientation(Image.open(fichier))
        nom_pdf = fichier.name.rsplit(".",1)[0]+".pdf"
        flux_image(img_imp, nom_pdf, "imp")

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("""<hr class="sep">
<div style="text-align:center;font-size:.7rem;color:#2e3f5c;">
Nova Scan · Traitement 100 % en mémoire · Aucun fichier stocké
</div>""", unsafe_allow_html=True)
