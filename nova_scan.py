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
    text-align: center;
    font-size: 2rem;
    font-weight: 700;
    color: #2979ff;
    margin-bottom: 0.2rem;
    letter-spacing: 2px;
}
.nova-subtitle {
    text-align: center;
    font-size: 0.85rem;
    color: #7a90b8;
    margin-bottom: 1.8rem;
    letter-spacing: 1px;
    text-transform: uppercase;
}
.pdf-info {
    background: rgba(0, 229, 255, 0.06);
    border: 1px solid rgba(0, 229, 255, 0.2);
    border-radius: 10px;
    padding: 1rem 1.2rem;
    margin: 1rem 0;
    font-size: 0.85rem;
}
.pdf-info span { color: #00e5ff; font-weight: 600; }
.badge-crop {
    display: inline-block;
    background: rgba(0,230,118,0.12);
    border: 1px solid #00e676;
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.72rem;
    color: #00e676;
    margin-left: 8px;
}
.badge-manual {
    display: inline-block;
    background: rgba(41,121,255,0.15);
    border: 1px solid #2979ff;
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.72rem;
    color: #82b1ff;
    margin-left: 8px;
}
.badge-no-crop {
    display: inline-block;
    background: rgba(255,193,7,0.12);
    border: 1px solid #ffc107;
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.72rem;
    color: #ffc107;
    margin-left: 8px;
}
[data-testid="stDownloadButton"] > button {
    background-color: #2979ff !important;
    color: white !important;
    border: none !important;
    border-radius: 14px !important;
    font-weight: 700 !important;
    font-size: 1.1rem !important;
    padding: 0.9rem 2rem !important;
    width: 100% !important;
    letter-spacing: 1px !important;
    box-shadow: 0 4px 20px rgba(41,121,255,0.4) !important;
}
[data-testid="stButton"] > button {
    background: transparent !important;
    border: 1px solid #2979ff55 !important;
    color: #7a90b8 !important;
    border-radius: 8px !important;
    width: 100% !important;
    margin-top: 0.5rem !important;
}
.preview-label {
    font-size: 0.75rem;
    color: #7a90b8;
    text-align: center;
    margin-bottom: 0.3rem;
}
.sep { border: none; border-top: 1px solid #0d1e38; margin: 1.5rem 0; }
.tip-box {
    background: rgba(255,193,7,0.06);
    border-left: 3px solid #ffc107;
    border-radius: 0 8px 8px 0;
    padding: 0.7rem 1rem;
    font-size: 0.78rem;
    color: #c9a227;
    margin-bottom: 1rem;
}
.steps-row {
    display: flex;
    justify-content: center;
    gap: 0.5rem;
    margin-bottom: 1.2rem;
    flex-wrap: wrap;
}
.step-badge {
    background: rgba(41,121,255,0.12);
    border: 1px solid #2979ff44;
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 0.72rem;
    color: #7a90b8;
    white-space: nowrap;
}
.step-active {
    background: rgba(41,121,255,0.3);
    border-color: #2979ff;
    color: #fff;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="nova-title">📄 NOVA SCAN</div>', unsafe_allow_html=True)
st.markdown('<div class="nova-subtitle">Numérisation instantanée · Zéro installation</div>', unsafe_allow_html=True)

# ── Reset ─────────────────────────────────────────────────────────────────────
if st.session_state.get("reset_requested"):
    st.session_state["reset_requested"] = False
    st.session_state["scan_key"] = st.session_state.get("scan_key", 0) + 1
    for k in ["corners_result", "pending_image", "pending_name", "crop_mode"]:
        st.session_state.pop(k, None)

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


# ── Détection automatique du document ────────────────────────────────────────
def detecter_contour_auto(img_pil):
    """Retourne les 4 coins détectés (coords image originale) ou None."""
    try:
        import cv2
        img_np = np.array(img_pil.convert("RGB"))
        h, w = img_np.shape[:2]
        scale = 800 / max(h, w)
        small = cv2.resize(img_np, (int(w * scale), int(h * scale)))
        gray = cv2.cvtColor(small, cv2.COLOR_RGB2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blur, 50, 150)
        edges = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=2)
        contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]
        for c in contours:
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            if len(approx) == 4 and cv2.contourArea(c) > (small.shape[0] * small.shape[1] * 0.2):
                pts = (approx.reshape(4, 2) / scale).astype(np.float32)
                s = pts.sum(axis=1)
                diff = np.diff(pts, axis=1)
                ordered = np.zeros((4, 2), dtype=np.float32)
                ordered[0] = pts[np.argmin(s)]    # haut-gauche
                ordered[1] = pts[np.argmin(diff)] # haut-droite
                ordered[2] = pts[np.argmax(s)]    # bas-droite
                ordered[3] = pts[np.argmax(diff)] # bas-gauche
                return ordered.tolist()
        return None
    except Exception:
        return None


# ── Recadrage perspective depuis 4 coins ─────────────────────────────────────
def recadrer_depuis_coins(img_pil, coins):
    """
    coins : liste de 4 points [[x,y], ...] dans l'ordre TL, TR, BR, BL
    coords relatives à l'image PIL originale.
    """
    import cv2
    img_np = np.array(img_pil.convert("RGB"))
    pts = np.array(coins, dtype=np.float32)
    wA = np.linalg.norm(pts[2] - pts[3])
    wB = np.linalg.norm(pts[1] - pts[0])
    hA = np.linalg.norm(pts[1] - pts[2])
    hB = np.linalg.norm(pts[0] - pts[3])
    maxW = int(max(wA, wB))
    maxH = int(max(hA, hB))
    dst = np.array([[0, 0], [maxW-1, 0], [maxW-1, maxH-1], [0, maxH-1]], dtype=np.float32)
    M = cv2.getPerspectiveTransform(pts, dst)
    warped = cv2.warpPerspective(img_np, M, (maxW, maxH))
    # Amélioration contraste scan
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


# ── Canvas interactif de recadrage ───────────────────────────────────────────
def canvas_recadrage(img_pil, coins_initiales, component_key):
    """
    Affiche un canvas HTML avec 4 poignées déplaçables.
    Retourne les coordonnées confirmées ou None.
    """
    # Encoder l'image en base64
    buf = io.BytesIO()
    img_pil.save(buf, format="JPEG", quality=80)
    b64 = base64.b64encode(buf.getvalue()).decode()

    w_orig, h_orig = img_pil.size

    # Coins par défaut si aucun détecté (marges 10%)
    if coins_initiales:
        coins_json = json.dumps(coins_initiales)
    else:
        mx, my = w_orig * 0.08, h_orig * 0.08
        coins_json = json.dumps([
            [mx, my],
            [w_orig - mx, my],
            [w_orig - mx, h_orig - my],
            [mx, h_orig - my],
        ])

    import streamlit.components.v1 as components

    html = f"""
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ background: #050d1a; font-family: 'Segoe UI', sans-serif; touch-action: none; }}
#wrap {{
  position: relative;
  width: 100%;
  max-width: 480px;
  margin: 0 auto;
}}
canvas {{
  display: block;
  width: 100%;
  border-radius: 12px;
  border: 1.5px solid #2979ff44;
  touch-action: none;
  cursor: crosshair;
}}
.toolbar {{
  display: flex;
  gap: 8px;
  margin-top: 10px;
}}
.btn {{
  flex: 1;
  padding: 13px;
  border-radius: 14px;
  font-size: 0.95rem;
  font-weight: 700;
  letter-spacing: 0.5px;
  cursor: pointer;
  border: none;
  font-family: 'Segoe UI', sans-serif;
  transition: transform 0.1s, opacity 0.1s;
  -webkit-tap-highlight-color: transparent;
}}
.btn:active {{ transform: scale(0.97); opacity: 0.9; }}
.btn-confirm {{
  background: linear-gradient(135deg, #2979ff, #1a5cd4);
  color: #fff;
  box-shadow: 0 4px 18px rgba(41,121,255,0.5);
}}
.btn-cancel {{
  background: transparent;
  border: 1px solid #2979ff44 !important;
  color: #7a90b8;
}}
.hint {{
  text-align: center;
  font-size: 0.75rem;
  color: #4a6080;
  margin-top: 7px;
  letter-spacing: 0.3px;
}}
</style>
</head>
<body>
<div id="wrap">
  <canvas id="cv"></canvas>
  <div class="toolbar">
    <button class="btn btn-cancel" onclick="cancel()">✕ Annuler</button>
    <button class="btn btn-confirm" onclick="confirm_crop()">✓ Confirmer le recadrage</button>
  </div>
  <div class="hint">Glissez les coins bleus sur les bords du document</div>
</div>

<script>
const IMG_W = {w_orig};
const IMG_H = {h_orig};
const COINS_INIT = {coins_json};

const canvas = document.getElementById('cv');
const ctx = canvas.getContext('2d');
const img = new Image();
img.src = 'data:image/jpeg;base64,{b64}';

// Résolution interne du canvas = taille image originale
canvas.width = IMG_W;
canvas.height = IMG_H;

// Coins en coords image originale
let coins = COINS_INIT.map(c => ({{x: c[0], y: c[1]}}));
let drag = null;
const R = Math.max(18, Math.min(IMG_W, IMG_H) * 0.04);

img.onload = () => draw();

function draw() {{
  ctx.clearRect(0, 0, IMG_W, IMG_H);
  ctx.drawImage(img, 0, 0);

  // Overlay sombre hors zone
  ctx.save();
  ctx.beginPath();
  ctx.moveTo(coins[0].x, coins[0].y);
  coins.forEach((c,i) => {{ if(i>0) ctx.lineTo(c.x, c.y); }});
  ctx.closePath();
  ctx.save();
  ctx.fillStyle = 'rgba(0,0,0,0.45)';
  ctx.fillRect(0, 0, IMG_W, IMG_H);
  ctx.restore();
  ctx.save();
  ctx.beginPath();
  ctx.moveTo(coins[0].x, coins[0].y);
  coins.forEach((c,i) => {{ if(i>0) ctx.lineTo(c.x, c.y); }});
  ctx.closePath();
  ctx.globalCompositeOperation = 'destination-out';
  ctx.fillStyle = 'rgba(0,0,0,1)';
  ctx.fill();
  ctx.restore();

  // Contour bleu
  ctx.beginPath();
  ctx.moveTo(coins[0].x, coins[0].y);
  coins.forEach((c,i) => {{ if(i>0) ctx.lineTo(c.x, c.y); }});
  ctx.closePath();
  ctx.strokeStyle = '#2979ff';
  ctx.lineWidth = Math.max(3, R * 0.18);
  ctx.stroke();

  // Poignées
  coins.forEach((c, i) => {{
    // Ombre
    ctx.beginPath();
    ctx.arc(c.x, c.y, R + 4, 0, Math.PI*2);
    ctx.fillStyle = 'rgba(0,0,0,0.35)';
    ctx.fill();
    // Cercle
    ctx.beginPath();
    ctx.arc(c.x, c.y, R, 0, Math.PI*2);
    ctx.fillStyle = drag === i ? '#82b1ff' : '#2979ff';
    ctx.fill();
    ctx.strokeStyle = '#fff';
    ctx.lineWidth = Math.max(2, R * 0.12);
    ctx.stroke();
  }});
}}

function getPos(e) {{
  const rect = canvas.getBoundingClientRect();
  const scaleX = IMG_W / rect.width;
  const scaleY = IMG_H / rect.height;
  const src = e.touches ? e.touches[0] : e;
  return {{
    x: Math.max(0, Math.min(IMG_W, (src.clientX - rect.left) * scaleX)),
    y: Math.max(0, Math.min(IMG_H, (src.clientY - rect.top) * scaleY)),
  }};
}}

function hitTest(pos) {{
  for (let i = 0; i < coins.length; i++) {{
    const dx = pos.x - coins[i].x;
    const dy = pos.y - coins[i].y;
    if (Math.sqrt(dx*dx + dy*dy) < R * 1.8) return i;
  }}
  return null;
}}

canvas.addEventListener('mousedown', e => {{ drag = hitTest(getPos(e)); }});
canvas.addEventListener('touchstart', e => {{ e.preventDefault(); drag = hitTest(getPos(e)); }}, {{passive:false}});

canvas.addEventListener('mousemove', e => {{
  if (drag === null) return;
  const p = getPos(e);
  coins[drag] = p;
  draw();
}});
canvas.addEventListener('touchmove', e => {{
  e.preventDefault();
  if (drag === null) return;
  const p = getPos(e);
  coins[drag] = p;
  draw();
}}, {{passive:false}});

canvas.addEventListener('mouseup', () => {{ drag = null; }});
canvas.addEventListener('touchend', () => {{ drag = null; }});

function confirm_crop() {{
  const result = coins.map(c => [Math.round(c.x), Math.round(c.y)]);
  window.parent.postMessage({{type:'nova_corners', key:'{component_key}', corners: result}}, '*');
}}

function cancel() {{
  window.parent.postMessage({{type:'nova_cancel', key:'{component_key}'}}, '*');
}}
</script>
</body>
</html>
"""
    components.html(html, height=620, scrolling=False)


# ── Listener postMessage via query params trick ───────────────────────────────
# Streamlit ne peut pas recevoir postMessage directement.
# On utilise une zone de texte cachée + javascript qui écrit dans un st.text_input,
# puis on lit la valeur. Alternative propre : st.query_params.
# On utilise ici l'approche "composant relais" : un 2e iframe lit le message et
# redirige vers un endpoint Streamlit via fetch sur le même origin — impossible.
# 
# Solution retenue : stocker les coins dans session_state via un st.text_input
# caché dont le JS remplit la valeur via DOM manipulation (hack classique Streamlit).
# Plus robuste : on injecte le canvas dans la même page et on utilise
# un st.text_area + JS pour déclencher un rerun.

def canvas_avec_relay(img_pil, coins_initiales, instance_key):
    """
    Affiche le canvas + un champ texte caché.
    Le JS du canvas écrit les coins dans le champ, déclenche un 'input' event,
    ce qui force Streamlit à relire la valeur au prochain rerun.
    Retourne (action, corners) où action = 'confirm' | 'cancel' | None
    """
    import streamlit.components.v1 as components

    buf = io.BytesIO()
    img_pil.save(buf, format="JPEG", quality=75)
    b64 = base64.b64encode(buf.getvalue()).decode()
    w_orig, h_orig = img_pil.size

    if coins_initiales:
        coins_json = json.dumps(coins_initiales)
    else:
        mx, my = w_orig * 0.08, h_orig * 0.08
        coins_json = json.dumps([
            [mx, my], [w_orig - mx, my],
            [w_orig - mx, h_orig - my], [mx, h_orig - my],
        ])

    field_key = f"_relay_{instance_key}"
    val = st.text_input("relay", key=field_key, label_visibility="collapsed")

    if val.startswith("CONFIRM:"):
        try:
            corners = json.loads(val[8:])
            return "confirm", corners
        except Exception:
            pass
    elif val == "CANCEL":
        return "cancel", None

    html = f"""
<!DOCTYPE html><html><head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#050d1a;font-family:'Segoe UI',sans-serif;touch-action:none;padding:4px}}
#wrap{{position:relative;width:100%;max-width:520px;margin:0 auto}}
canvas{{display:block;width:100%;border-radius:12px;border:1.5px solid #2979ff44;touch-action:none}}
.toolbar{{display:flex;gap:8px;margin-top:10px}}
.btn{{flex:1;padding:14px;border-radius:14px;font-size:1rem;font-weight:700;cursor:pointer;border:none;font-family:'Segoe UI',sans-serif;transition:transform .1s,opacity .1s;-webkit-tap-highlight-color:transparent}}
.btn:active{{transform:scale(.97);opacity:.9}}
.btn-ok{{background:linear-gradient(135deg,#2979ff,#1a5cd4);color:#fff;box-shadow:0 4px 18px rgba(41,121,255,.5)}}
.btn-no{{background:transparent;border:1px solid #2979ff44!important;color:#7a90b8}}
.hint{{text-align:center;font-size:.75rem;color:#4a6080;margin-top:7px}}
</style></head><body>
<div id="wrap">
  <canvas id="cv"></canvas>
  <div class="toolbar">
    <button class="btn btn-no" onclick="doCancel()">✕ Annuler</button>
    <button class="btn btn-ok" onclick="doConfirm()">✓ Confirmer le recadrage</button>
  </div>
  <div class="hint">Glissez les 4 coins bleus sur les bords du document</div>
</div>
<script>
const IW={w_orig},IH={h_orig};
const INIT={coins_json};
const cv=document.getElementById('cv');
const ctx=cv.getContext('2d');
cv.width=IW; cv.height=IH;
const img=new Image();
img.src='data:image/jpeg;base64,{b64}';
let coins=INIT.map(c=>({{x:c[0],y:c[1]}}));
let drag=null;
const R=Math.max(22,Math.min(IW,IH)*0.045);
img.onload=()=>draw();

function draw(){{
  ctx.clearRect(0,0,IW,IH);
  ctx.drawImage(img,0,0);
  // Masque sombre
  ctx.save();
  ctx.fillStyle='rgba(0,0,0,.5)';
  ctx.fillRect(0,0,IW,IH);
  ctx.globalCompositeOperation='destination-out';
  ctx.beginPath();
  ctx.moveTo(coins[0].x,coins[0].y);
  coins.forEach((c,i)=>{{if(i)ctx.lineTo(c.x,c.y)}});
  ctx.closePath();
  ctx.fillStyle='rgba(0,0,0,1)';
  ctx.fill();
  ctx.restore();
  // Contour
  ctx.beginPath();
  ctx.moveTo(coins[0].x,coins[0].y);
  coins.forEach((c,i)=>{{if(i)ctx.lineTo(c.x,c.y)}});
  ctx.closePath();
  ctx.strokeStyle='#2979ff';
  ctx.lineWidth=Math.max(3,R*.15);
  ctx.stroke();
  // Lignes diagonales guide
  ctx.setLineDash([R*.6,R*.4]);
  ctx.strokeStyle='rgba(41,121,255,.3)';
  ctx.lineWidth=Math.max(1,R*.06);
  ctx.beginPath(); ctx.moveTo(coins[0].x,coins[0].y); ctx.lineTo(coins[2].x,coins[2].y); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(coins[1].x,coins[1].y); ctx.lineTo(coins[3].x,coins[3].y); ctx.stroke();
  ctx.setLineDash([]);
  // Poignées
  coins.forEach((c,i)=>{{
    ctx.beginPath(); ctx.arc(c.x,c.y,R+5,0,Math.PI*2);
    ctx.fillStyle='rgba(0,0,0,.3)'; ctx.fill();
    ctx.beginPath(); ctx.arc(c.x,c.y,R,0,Math.PI*2);
    ctx.fillStyle=drag===i?'#82b1ff':'#2979ff'; ctx.fill();
    ctx.strokeStyle='#fff'; ctx.lineWidth=Math.max(2,R*.1); ctx.stroke();
    // Croix centre
    const s=R*.35;
    ctx.strokeStyle='rgba(255,255,255,.7)'; ctx.lineWidth=Math.max(1.5,R*.07);
    ctx.beginPath(); ctx.moveTo(c.x-s,c.y); ctx.lineTo(c.x+s,c.y); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(c.x,c.y-s); ctx.lineTo(c.x,c.y+s); ctx.stroke();
  }});
}}

function gp(e){{
  const r=cv.getBoundingClientRect(),sx=IW/r.width,sy=IH/r.height;
  const s=e.touches?e.touches[0]:e;
  return{{x:Math.max(0,Math.min(IW,(s.clientX-r.left)*sx)),
          y:Math.max(0,Math.min(IH,(s.clientY-r.top)*sy))}};
}}
function hit(p){{
  for(let i=0;i<4;i++){{const d=coins[i],dx=p.x-d.x,dy=p.y-d.y;if(Math.sqrt(dx*dx+dy*dy)<R*2)return i;}}
  return null;
}}
cv.addEventListener('mousedown',e=>{{drag=hit(gp(e));draw();}});
cv.addEventListener('touchstart',e=>{{e.preventDefault();drag=hit(gp(e));draw();}},{{passive:false}});
cv.addEventListener('mousemove',e=>{{if(drag===null)return;coins[drag]=gp(e);draw();}});
cv.addEventListener('touchmove',e=>{{e.preventDefault();if(drag===null)return;coins[drag]=gp(e);draw();}},{{passive:false}});
cv.addEventListener('mouseup',()=>{{drag=null;draw();}});
cv.addEventListener('touchend',()=>{{drag=null;draw();}});

function writeToStreamlit(val){{
  try{{
    const inputs=window.parent.document.querySelectorAll('input[type="text"]');
    for(const inp of inputs){{
      if(inp.value==='' || inp.dataset.novaRelay){{
        inp.dataset.novaRelay='1';
        const nativeInputValueSetter=Object.getOwnPropertyDescriptor(window.parent.HTMLInputElement.prototype,'value').set;
        nativeInputValueSetter.call(inp,val);
        inp.dispatchEvent(new Event('input',{{bubbles:true}}));
        return true;
      }}
    }}
  }}catch(e){{console.error(e);}}
  return false;
}}

function sendToParent(payload){{
  window.parent.postMessage({{novaRelay:true,payload}},'*');
}}

function doConfirm(){{
  const r=coins.map(c=>[Math.round(c.x),Math.round(c.y)]);
  sendToParent('CONFIRM:'+JSON.stringify(r));
}}
function doCancel(){{
  sendToParent('CANCEL');
}}
</script>
</body></html>
"""
    components.html(html, height=640, scrolling=False)
    return None, None


# ── Affichage résultat final ──────────────────────────────────────────────────
def afficher_resultat(img, nom_fichier, badge_mode, key_dl, key_btn):
    try:
        pdf_bytes, img_rgb = image_vers_pdf(img)
        w, h = img_rgb.size
        taille_ko = len(pdf_bytes) / 1024
        taille_str = f"{taille_ko/1024:.1f} Mo" if taille_ko >= 1024 else f"{taille_ko:.0f} Ko"

        st.markdown('<div class="steps-row">'
                    '<div class="step-badge">① ✓ Photo prise</div>'
                    '<div class="step-badge">② ✓ Recadrage</div>'
                    '<div class="step-badge step-active">③ Télécharger</div>'
                    '</div>', unsafe_allow_html=True)

        st.markdown('<div class="preview-label">APERÇU DU DOCUMENT</div>', unsafe_allow_html=True)
        st.image(img_rgb, use_container_width=True)

        badges = {
            "auto":   '<span class="badge-crop">✂️ Recadré automatiquement</span>',
            "manual": '<span class="badge-manual">✋ Recadrage manuel</span>',
            "none":   '<span class="badge-no-crop">⚠️ Sans recadrage</span>',
        }
        badge_html = badges.get(badge_mode, "")

        st.markdown(f"""
        <div class="pdf-info">
            📄 PDF prêt ! {badge_html}<br>
            Taille : <span>{taille_str}</span> &nbsp;|&nbsp;
            Résolution : <span>{w} × {h} px</span>
        </div>
        """, unsafe_allow_html=True)

        st.download_button(
            label="⬇️  TÉLÉCHARGER LE PDF",
            data=pdf_bytes,
            file_name=nom_fichier,
            mime="application/pdf",
            key=key_dl,
        )
    except Exception as e:
        st.error(f"Erreur : {e}")

    st.markdown('<hr class="sep">', unsafe_allow_html=True)
    if st.button("🔄  Scanner un autre document", key=key_btn):
        st.session_state["reset_requested"] = True
        st.rerun()


# ── Flux principal après réception d'une image ───────────────────────────────
def flux_image(img_pil, nom_pdf, instance_prefix):
    """
    Gère le flux complet :
    1. Détection auto
    2. Canvas de recadrage manuel
    3. Résultat PDF
    """
    state_key = f"state_{instance_prefix}"
    corners_key = f"corners_{instance_prefix}"
    badge_key = f"badge_{instance_prefix}"

    if state_key not in st.session_state:
        st.session_state[state_key] = "detecting"

    state = st.session_state[state_key]

    # ── Étape 1 : détection + canvas ────────────────────────────────────────
    if state in ("detecting", "canvas"):
        if state == "detecting":
            with st.spinner("🔍 Détection du document..."):
                coins = detecter_contour_auto(img_pil)
            st.session_state[corners_key] = coins
            st.session_state[state_key] = "canvas"
            st.rerun()

        # ── Canvas interactif ─────────────────────────────────────────────
        st.markdown('<div class="steps-row">'
                    '<div class="step-badge">① ✓ Photo prise</div>'
                    '<div class="step-badge step-active">② Ajuster le recadrage</div>'
                    '<div class="step-badge">③ Télécharger PDF</div>'
                    '</div>', unsafe_allow_html=True)

        coins = st.session_state.get(corners_key)

        if coins:
            st.markdown("""
            <div style="background:rgba(0,230,118,0.07);border:1px solid #00e67644;border-radius:10px;
                        padding:.6rem 1rem;font-size:.78rem;color:#00e676;margin-bottom:.8rem;text-align:center;">
                ✂️ Document détecté automatiquement — ajustez les coins si nécessaire
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="tip-box">
                💡 Document non détecté. Placez les 4 coins bleus manuellement sur les bords.
            </div>
            """, unsafe_allow_html=True)

        # Afficher le canvas
        canvas_avec_relay(img_pil, coins, f"{instance_prefix}_{sk}")

        # Bouton "Utiliser sans recadrage"
        st.markdown('<hr class="sep">', unsafe_allow_html=True)
        if st.button("⏭️  Utiliser sans recadrage", key=f"skip_{instance_prefix}"):
            st.session_state[state_key] = "done_none"
            st.rerun()

        # Lire le relay field (rempli par JS via postMessage trick alternatif)
        # Puisque postMessage cross-frame est bloqué dans Streamlit cloud,
        # on utilise un bouton hidden + URL param approach
        # Alternative propre : st.query_params
        relay_val = st.session_state.get(f"_relay_{instance_prefix}_{sk}", "")
        if relay_val.startswith("CONFIRM:"):
            try:
                corners_from_js = json.loads(relay_val[8:])
                st.session_state[corners_key] = corners_from_js
                st.session_state[badge_key] = "manual"
                st.session_state[state_key] = "done_manual"
                st.rerun()
            except Exception:
                pass
        elif relay_val == "CANCEL":
            st.session_state["reset_requested"] = True
            st.rerun()

    # ── Étape 2 : rendu PDF ──────────────────────────────────────────────────
    elif state in ("done_auto", "done_manual", "done_none"):
        badge = st.session_state.get(badge_key, "none")
        corners = st.session_state.get(corners_key)

        if state == "done_none" or not corners:
            img_finale = img_pil
        else:
            try:
                img_finale = recadrer_depuis_coins(img_pil, corners)
            except Exception:
                img_finale = img_pil

        afficher_resultat(
            img_finale, nom_pdf, badge,
            key_dl=f"dl_{instance_prefix}",
            key_btn=f"reset_{instance_prefix}",
        )


# ── Écoute postMessage via composant relais ───────────────────────────────────
# Streamlit ne peut pas recevoir postMessage nativement.
# On crée un mini-composant "écouteur" qui intercepte les messages
# du canvas iframe et les pousse dans un st.session_state via
# query params + st.rerun(), ce qui est le pattern officiel.

def inject_message_listener(instance_prefix):
    """
    Injecte un iframe invisible qui écoute les postMessages du canvas
    et met à jour les query params pour déclencher un rerun.
    """
    import streamlit.components.v1 as components

    # On lit d'abord les query params
    qp = st.query_params
    nova_action = qp.get("nova_action", "")
    nova_key = qp.get("nova_key", "")
    nova_data = qp.get("nova_data", "")

    state_key = f"state_{instance_prefix}"
    corners_key = f"corners_{instance_prefix}"
    badge_key = f"badge_{instance_prefix}"

    if nova_action == "confirm" and nova_key == instance_prefix:
        try:
            corners = json.loads(nova_data)
            st.session_state[corners_key] = corners
            st.session_state[badge_key] = "manual"
            st.session_state[state_key] = "done_manual"
            # Nettoyer les params
            st.query_params.clear()
            st.rerun()
        except Exception:
            pass
    elif nova_action == "cancel" and nova_key == instance_prefix:
        st.query_params.clear()
        st.session_state["reset_requested"] = True
        st.rerun()

    # Injecter le listener JS
    components.html(f"""
<script>
window.addEventListener('message', function(e) {{
  const d = e.data;
  if (!d || !d.novaRelay) return;
  const payload = d.payload;
  const key = '{instance_prefix}';
  let action, data='';
  if (payload === 'CANCEL') {{
    action = 'cancel';
  }} else if (payload && payload.startsWith('CONFIRM:')) {{
    action = 'confirm';
    data = encodeURIComponent(payload.slice(8));
  }} else return;
  const url = new URL(window.parent.location.href);
  url.searchParams.set('nova_action', action);
  url.searchParams.set('nova_key', key);
  if (data) url.searchParams.set('nova_data', data);
  window.parent.location.href = url.toString();
}});
</script>
""", height=0, scrolling=False)


# ══════════════════════════════════════════════════════════════════════════════
# ONGLETS
# ══════════════════════════════════════════════════════════════════════════════
tab_mobile, tab_import = st.tabs(["📷  Caméra", "🖼️  Importer"])

# ══════════════════════════════════
# ONGLET 1 — CAMÉRA
# ══════════════════════════════════
with tab_mobile:
    photo = st.file_uploader(
        label="photo",
        type=["jpg", "jpeg", "png", "webp", "bmp", "heic"],
        label_visibility="collapsed",
        key=f"cam_{sk}",
    )

    if photo is None:
        import streamlit.components.v1 as components
        components.html("""
        <style>
          *{box-sizing:border-box;margin:0;padding:0}
          body{background:transparent;font-family:'Segoe UI',sans-serif}
          .card{background:rgba(41,121,255,0.07);border:1.5px dashed #2979ff88;border-radius:18px;
                padding:1.4rem 1rem;margin-bottom:1rem;text-align:center}
          .icon{font-size:3.5rem;display:block;margin-bottom:.5rem;animation:pulse 2s infinite}
          @keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.08)}}
          .title{font-size:1.05rem;font-weight:700;color:#fff;margin-bottom:.5rem}
          .tips{text-align:left;display:inline-block}
          .tip{font-size:.82rem;color:#a0b4d0;margin:.25rem 0;display:flex;align-items:center;gap:.4rem}
          .big-btn{display:block;width:100%;background:linear-gradient(135deg,#2979ff,#1a5cd4);color:#fff;
            border:none;border-radius:16px;padding:1.1rem;font-size:1.15rem;font-weight:700;
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
          <div class="step active">① Prendre la photo</div>
          <div class="step">② Ajuster les coins</div>
          <div class="step">③ Télécharger PDF</div>
        </div>
        <script>
        function openCamera(){
          try{
            const inputs=window.parent.document.querySelectorAll('input[type="file"]');
            for(let inp of inputs){inp.setAttribute('capture','environment');inp.setAttribute('accept','image/*');inp.click();return;}
          }catch(e){}
          const inp=document.createElement('input');inp.type='file';inp.accept='image/*';
          inp.setAttribute('capture','environment');inp.click();
        }
        </script>
        """, height=380, scrolling=False)
    else:
        img_mob = corriger_orientation(Image.open(photo))
        inject_message_listener("mob")
        flux_image(img_mob, "nova_scan_document.pdf", "mob")


# ══════════════════════════════════
# ONGLET 2 — IMPORT
# ══════════════════════════════════
with tab_import:
    st.markdown("""
    <div class="tip-box">
        💡 <strong>Formats acceptés :</strong> JPG, PNG, WEBP, BMP
    </div>
    """, unsafe_allow_html=True)

    fichier = st.file_uploader(
        label="Choisir une image",
        type=["jpg", "jpeg", "png", "webp", "bmp"],
        label_visibility="collapsed",
        key=f"upload_{sk}",
    )

    if fichier is not None:
        img_imp = corriger_orientation(Image.open(fichier))
        nom_pdf = fichier.name.rsplit(".", 1)[0] + ".pdf"
        inject_message_listener("imp")
        flux_image(img_imp, nom_pdf, "imp")


# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("""
<hr class="sep">
<div style="text-align:center;font-size:.7rem;color:#2e3f5c;">
    Nova Scan · Module Nova Platform · Traitement 100% en mémoire · Aucun fichier stocké
</div>
""", unsafe_allow_html=True)
