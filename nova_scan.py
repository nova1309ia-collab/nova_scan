import streamlit as st
from PIL import Image, ImageEnhance, ImageFilter
import io
import numpy as np
import base64
import json

st.set_page_config(
    page_title="Nova Scan", page_icon="📄",
    layout="centered", initial_sidebar_state="collapsed",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@600;700;800&family=DM+Sans:wght@400;500;600&display=swap');

:root{
  --bg:#2a3d6b;
  --bg2:#2f4475;
  --blue:#4d8aff;
  --blue-dim:rgba(77,138,255,.18);
  --blue-glow:rgba(77,138,255,.35);
  --cyan:#00e5ff;
  --green:#00e676;
  --amber:#ffc107;
  --text:#e8eeff;
  --muted:#8ba4cc;
  --card:rgba(255,255,255,.05);
  --border:rgba(77,138,255,.22);
  --radius:16px;
}

/* ── Base ── */
html,body,[data-testid="stAppViewContainer"]{
  background-color:var(--bg)!important;
  color:var(--text);
  font-family:'DM Sans',sans-serif;
}
[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"]{display:none!important}
div[data-testid="stTextInput"]{display:none!important}

/* Cache tous les uploaders par défaut (onglet Caméra) */
[data-testid="stFileUploader"]{display:none!important}

/* Réactive uniquement l'uploader dans le wrapper import */
.uploader-import [data-testid="stFileUploader"]{
  display:block!important;
  background:rgba(77,138,255,.06)!important;
  border:1.5px dashed rgba(77,138,255,.4)!important;
  border-radius:var(--radius)!important;
  padding:.5rem!important;
}
.uploader-import [data-testid="stFileUploader"] section{border:none!important;background:transparent!important;padding:.5rem!important}
.uploader-import [data-testid="stFileUploaderDropzoneInstructions"]{color:var(--muted)!important;font-size:.82rem!important}
.uploader-import [data-testid="stFileUploaderDropzone"] button{
  background:var(--blue-dim)!important;
  border:1px solid var(--blue)!important;
  color:#fff!important;
  border-radius:10px!important;
  font-weight:600!important;
  padding:.5rem 1.2rem!important;
  font-size:.85rem!important;
}

/* Remove default padding on mobile */
.block-container{padding:1rem .8rem 2rem!important;max-width:480px!important}
@media(max-width:480px){.block-container{padding:.75rem .6rem 2rem!important}}

/* ── Header ── */
.nova-title{
  text-align:center;
  font-family:'Syne',sans-serif;
  font-size:2.1rem;
  font-weight:800;
  background:linear-gradient(135deg,#6ea8ff 0%,#2979ff 50%,#00b4ff 100%);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
  margin-bottom:.15rem;
  letter-spacing:3px;
  filter:drop-shadow(0 0 18px rgba(41,121,255,.4));
}
.nova-subtitle{
  text-align:center;
  font-size:.75rem;
  color:var(--muted);
  margin-bottom:1.6rem;
  letter-spacing:2px;
  text-transform:uppercase;
  font-weight:500;
}

/* ── Tabs ── */
[data-testid="stTabs"] [role="tablist"]{
  background:var(--bg2)!important;
  border-radius:14px!important;
  padding:4px!important;
  border:1px solid var(--border)!important;
  gap:4px!important;
}
[data-testid="stTabs"] [role="tab"]{
  border-radius:10px!important;
  font-family:'DM Sans',sans-serif!important;
  font-weight:600!important;
  font-size:.88rem!important;
  color:var(--muted)!important;
  padding:.55rem 1rem!important;
  transition:all .2s!important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"]{
  background:var(--blue-dim)!important;
  color:#fff!important;
  box-shadow:0 0 16px var(--blue-glow)!important;
}
[data-testid="stTabs"] [role="tab"]:focus{box-shadow:none!important}
[data-testid="stTabContent"]{padding-top:.8rem!important}

/* ── Cards / Info boxes ── */
.pdf-info{
  background:rgba(0,229,255,.05);
  border:1px solid rgba(0,229,255,.18);
  border-radius:var(--radius);
  padding:1rem 1.1rem;
  margin:1rem 0;
  font-size:.84rem;
  line-height:1.7;
}
.pdf-info span{color:var(--cyan);font-weight:600}

.tip-box{
  background:rgba(255,193,7,.05);
  border-left:3px solid var(--amber);
  border-radius:0 12px 12px 0;
  padding:.75rem 1rem;
  font-size:.8rem;
  color:#c9a227;
  margin-bottom:1rem;
}

/* ── Badges ── */
.badge-crop,.badge-manual,.badge-no-crop{
  display:inline-flex;align-items:center;gap:4px;
  border-radius:20px;padding:3px 12px;
  font-size:.72rem;font-weight:600;margin-left:6px;
}
.badge-crop{background:rgba(0,230,118,.1);border:1px solid var(--green);color:var(--green)}
.badge-manual{background:rgba(41,121,255,.12);border:1px solid var(--blue);color:#82b1ff}
.badge-no-crop{background:rgba(255,193,7,.1);border:1px solid var(--amber);color:var(--amber)}

/* ── Step indicators ── */
.steps-row{
  display:flex;justify-content:center;
  gap:.4rem;margin-bottom:1.1rem;flex-wrap:wrap;
}
.step-badge{
  background:rgba(41,121,255,.08);
  border:1px solid rgba(41,121,255,.2);
  border-radius:30px;
  padding:5px 14px;
  font-size:.72rem;
  color:var(--muted);
  white-space:nowrap;
  font-weight:500;
}
.step-active{
  background:rgba(41,121,255,.22);
  border-color:var(--blue);
  color:#fff;
  font-weight:700;
  box-shadow:0 0 10px rgba(41,121,255,.3);
}

/* ── Buttons ── */
[data-testid="stDownloadButton"]>button{
  background:linear-gradient(135deg,#2979ff,#1565c0)!important;
  color:#fff!important;
  border:none!important;
  border-radius:var(--radius)!important;
  font-family:'Syne',sans-serif!important;
  font-weight:700!important;
  font-size:1.05rem!important;
  padding:1rem 2rem!important;
  width:100%!important;
  letter-spacing:1.5px!important;
  box-shadow:0 4px 24px var(--blue-glow)!important;
  transition:transform .15s,box-shadow .15s!important;
  -webkit-tap-highlight-color:transparent!important;
  min-height:56px!important;
}
[data-testid="stDownloadButton"]>button:active{
  transform:scale(.97)!important;
  box-shadow:0 2px 12px var(--blue-glow)!important;
}
[data-testid="stButton"]>button{
  background:rgba(255,255,255,.03)!important;
  border:1px solid rgba(41,121,255,.3)!important;
  color:var(--muted)!important;
  border-radius:12px!important;
  width:100%!important;
  margin-top:.6rem!important;
  font-family:'DM Sans',sans-serif!important;
  font-size:.9rem!important;
  min-height:48px!important;
  transition:all .15s!important;
  -webkit-tap-highlight-color:transparent!important;
}
[data-testid="stButton"]>button:hover{
  border-color:var(--blue)!important;
  color:#aac4ff!important;
}

/* ── Radio (mode selector) ── */
[data-testid="stRadio"]>div{
  display:flex!important;
  flex-direction:row!important;
  gap:6px!important;
  flex-wrap:nowrap!important;
}
[data-testid="stRadio"] label{
  flex:1!important;
  background:rgba(41,121,255,.06)!important;
  border:1.5px solid rgba(41,121,255,.2)!important;
  border-radius:12px!important;
  padding:10px 4px!important;
  text-align:center!important;
  cursor:pointer!important;
  font-size:.78rem!important;
  font-weight:600!important;
  color:var(--muted)!important;
  transition:all .15s!important;
  min-height:46px!important;
  display:flex!important;
  align-items:center!important;
  justify-content:center!important;
  -webkit-tap-highlight-color:transparent!important;
}
[data-testid="stRadio"] label:has(input:checked){
  background:rgba(41,121,255,.22)!important;
  border-color:var(--blue)!important;
  color:#fff!important;
  box-shadow:0 0 12px rgba(41,121,255,.25)!important;
}
[data-testid="stRadio"] input{display:none!important}

/* ── Image preview ── */
.preview-label{
  font-size:.72rem;
  color:var(--muted);
  text-align:center;
  margin-bottom:.4rem;
  letter-spacing:1.5px;
  text-transform:uppercase;
  font-weight:500;
}
[data-testid="stImage"]{border-radius:var(--radius);overflow:hidden}

/* ── Separator ── */
.sep{border:none;border-top:1px solid rgba(41,121,255,.1);margin:1.4rem 0}

/* ── Spinner ── */
[data-testid="stSpinner"] p{color:var(--muted)!important;font-size:.85rem!important}

/* ── Scrollbar ── */
::-webkit-scrollbar{width:4px}
::-webkit-scrollbar-track{background:transparent}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:4px}

/* ── Bandeau Apps Nova ── */
.nova-apps-banner{
  background: linear-gradient(135deg, rgba(15,25,60,.95) 0%, rgba(20,35,80,.95) 100%);
  border: 1px solid rgba(77,138,255,.3);
  border-radius: 20px;
  padding: 1.2rem 1rem 1rem;
  margin: 1.4rem 0 .8rem;
  position: relative;
  overflow: hidden;
}
.nova-apps-banner::before{
  content:'';
  position:absolute;inset:0;
  background: radial-gradient(ellipse at top right, rgba(77,138,255,.12) 0%, transparent 65%);
  pointer-events:none;
}
.nova-apps-banner-title{
  font-family:'Syne',sans-serif;
  font-size:.72rem;
  font-weight:700;
  color:rgba(77,138,255,.7);
  letter-spacing:2.5px;
  text-transform:uppercase;
  text-align:center;
  margin-bottom:.9rem;
}
.nova-apps-grid{
  display:flex;
  gap:.7rem;
  flex-direction:column;
}
.nova-app-card{
  background: rgba(255,255,255,.04);
  border: 1px solid rgba(77,138,255,.2);
  border-radius: 14px;
  padding: .85rem 1rem;
  display: flex;
  align-items: center;
  gap: .9rem;
  text-decoration: none !important;
  transition: border-color .2s, background .2s, transform .15s;
  -webkit-tap-highlight-color: transparent;
}
.nova-app-card:hover{
  border-color: rgba(77,138,255,.55);
  background: rgba(77,138,255,.07);
  transform: translateY(-1px);
}
.nova-app-card:active{ transform: scale(.98); }
.nova-app-icon{
  width: 46px; height: 46px;
  border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
  font-size: 1.5rem;
  flex-shrink: 0;
}
.icon-platform{ background: linear-gradient(135deg, #1a3f9f, #2979ff); }
.icon-agency{   background: linear-gradient(135deg, #4a1fa8, #7c3aed); }
.nova-app-body{ flex: 1; min-width: 0; }
.nova-app-name{
  font-family: 'Syne', sans-serif;
  font-weight: 700;
  font-size: .92rem;
  color: #e8eeff;
  margin-bottom: .18rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.nova-app-desc{
  font-size: .74rem;
  color: #7a90b8;
  line-height: 1.45;
}
.nova-app-badge{
  font-size: .62rem;
  font-weight: 700;
  letter-spacing: 1px;
  padding: 3px 9px;
  border-radius: 20px;
  white-space: nowrap;
  flex-shrink: 0;
}
.badge-free-green{
  background: rgba(0,230,118,.1);
  border: 1px solid rgba(0,230,118,.35);
  color: #00e676;
}
.badge-free-violet{
  background: rgba(124,58,237,.15);
  border: 1px solid rgba(124,58,237,.4);
  color: #c084fc;
}
.nova-app-card { flex-wrap: wrap; }
.nova-app-card-top {
  display: flex;
  align-items: center;
  gap: .9rem;
  width: 100%;
}
.nova-visit-btn {
  display: block;
  width: 100%;
  margin-top: .75rem;
  padding: .6rem 1rem;
  border-radius: 10px;
  font-family: 'Syne', sans-serif;
  font-size: .82rem;
  font-weight: 700;
  letter-spacing: 1px;
  text-align: center;
  text-decoration: none !important;
  transition: opacity .15s, transform .1s;
  -webkit-tap-highlight-color: transparent;
}
.nova-visit-btn:active { transform: scale(.97); opacity: .85; }
.btn-visit-green {
  background: linear-gradient(135deg, #00c853, #00897b);
  color: #fff !important;
  box-shadow: 0 3px 14px rgba(0,200,83,.35);
}
.btn-visit-violet {
  background: linear-gradient(135deg, #7c3aed, #4f46e5);
  color: #fff !important;
  box-shadow: 0 3px 14px rgba(124,58,237,.35);
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="nova-title">📄 NOVA SCAN</div>', unsafe_allow_html=True)
st.markdown('<div class="nova-subtitle">Numérisation instantanée · Zéro installation</div>', unsafe_allow_html=True)

if "scan_key" not in st.session_state:
    st.session_state["scan_key"] = 0
sk = st.session_state["scan_key"]


# ── Helpers ───────────────────────────────────────────────────────────────────
def corriger_orientation(img):
    """Corrige l'orientation EXIF — appeler UNE SEULE FOIS à l'ouverture."""
    try:
        from PIL import ExifTags
        exif = img._getexif()
        if exif:
            for tag, val in exif.items():
                if ExifTags.TAGS.get(tag) == "Orientation":
                    rotations = {3:180, 6:270, 8:90}
                    if val in rotations:
                        img = img.rotate(rotations[val], expand=True)
                    break
    except Exception:
        pass
    return img

def img_to_b64(img_pil):
    """Sauvegarde en PNG lossless pour préserver les couleurs exactes."""
    buf = io.BytesIO()
    img_pil.convert("RGB").save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()

def b64_to_img(s):
    return Image.open(io.BytesIO(base64.b64decode(s)))

def detecter_contour_auto(img_pil):
    try:
        import cv2
        img_np = np.array(img_pil.convert("RGB"))
        h, w = img_np.shape[:2]
        sc = 800/max(h,w)
        small = cv2.resize(img_np,(int(w*sc),int(h*sc)))
        gray = cv2.cvtColor(small,cv2.COLOR_RGB2GRAY)
        blur = cv2.GaussianBlur(gray,(5,5),0)
        edges = cv2.Canny(blur,30,120)
        edges = cv2.dilate(edges,np.ones((3,3),np.uint8),iterations=2)
        cnts,_ = cv2.findContours(edges,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
        cnts = sorted(cnts,key=cv2.contourArea,reverse=True)[:10]
        for c in cnts:
            peri = cv2.arcLength(c,True)
            # Essai avec tolérance croissante : 2%, 3%, 5%
            for tol in [0.02, 0.03, 0.05]:
                approx = cv2.approxPolyDP(c, tol*peri, True)
                if len(approx)==4 and cv2.contourArea(c)>(small.shape[0]*small.shape[1]*0.15):
                    pts = (approx.reshape(4,2)/sc).astype(np.float32)
                    s=pts.sum(axis=1); diff=np.diff(pts,axis=1)
                    o=np.zeros((4,2),dtype=np.float32)
                    o[0]=pts[np.argmin(s)]; o[1]=pts[np.argmin(diff)]
                    o[2]=pts[np.argmax(s)]; o[3]=pts[np.argmax(diff)]
                    return o.tolist()
        # Fallback : bounding rect du plus grand contour
        if cnts:
            c = cnts[0]
            area = cv2.contourArea(c)
            if area > (small.shape[0]*small.shape[1]*0.1):
                x,y,bw,bh = cv2.boundingRect(c)
                # Convertir en coords originales
                x,y,bw,bh = x/sc, y/sc, bw/sc, bh/sc
                pad = min(w,h)*0.01  # petit padding
                x1,y1 = max(0,x-pad), max(0,y-pad)
                x2,y2 = min(w,x+bw+pad), min(h,y+bh+pad)
                return [[x1,y1],[x2,y1],[x2,y2],[x1,y2]]
        return None
    except:
        return None

def _ordonner_coins(pts):
    """Réordonne 4 points en [haut-gauche, haut-droit, bas-droit, bas-gauche].
    Fonctionne quelle que soit l'ordre d'entrée (canvas, détection auto, manuel)."""
    pts = np.array(pts, dtype=np.float32)
    s = pts.sum(axis=1)
    diff = np.diff(pts, axis=1).flatten()
    ordered = np.zeros((4, 2), dtype=np.float32)
    ordered[0] = pts[np.argmin(s)]    # haut-gauche  : x+y minimal
    ordered[2] = pts[np.argmax(s)]    # bas-droit     : x+y maximal
    ordered[1] = pts[np.argmin(diff)] # haut-droit    : x-y minimal
    ordered[3] = pts[np.argmax(diff)] # bas-gauche    : x-y maximal
    return ordered

def recadrer_depuis_coins(img_pil, coins, mode="couleur"):
    import cv2
    img_np = np.array(img_pil.convert("RGB"))
    pts = _ordonner_coins(coins)  # ← ordre garanti : TL, TR, BR, BL
    wA=np.linalg.norm(pts[2]-pts[3]); wB=np.linalg.norm(pts[1]-pts[0])
    hA=np.linalg.norm(pts[1]-pts[2]); hB=np.linalg.norm(pts[0]-pts[3])
    mW=int(max(wA,wB)); mH=int(max(hA,hB))
    if mW < 10 or mH < 10:
        return img_pil
    dst=np.array([[0,0],[mW-1,0],[mW-1,mH-1],[0,mH-1]],dtype=np.float32)
    M=cv2.getPerspectiveTransform(pts,dst)
    warped=cv2.warpPerspective(img_np,M,(mW,mH))

    if mode == "nb":
        gray=cv2.cvtColor(warped,cv2.COLOR_RGB2GRAY)
        clean=cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,cv2.THRESH_BINARY,21,10)
        return Image.fromarray(clean).convert("RGB")
    elif mode == "gris":
        gray=cv2.cvtColor(warped,cv2.COLOR_RGB2GRAY)
        pil_gray = Image.fromarray(gray)
        pil_gray = ImageEnhance.Contrast(pil_gray).enhance(1.4)
        return pil_gray.convert("RGB")
    else:
        pil_color = Image.fromarray(warped)
        pil_color = ImageEnhance.Contrast(pil_color).enhance(1.2)
        pil_color = ImageEnhance.Sharpness(pil_color).enhance(1.3)
        return pil_color

def image_vers_pdf(img):
    if img.mode != "RGB":
        img = img.convert("RGB")
    # Upscale si l'image est trop petite pour donner un PDF lisible
    w, h = img.size
    MIN_DIM = 1200  # px minimum pour un PDF A4 correct
    if max(w, h) < MIN_DIM:
        scale = MIN_DIM / max(w, h)
        img = img.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="PDF", resolution=200)
    buf.seek(0)
    return buf.getvalue(), img


# ── Bandeau Apps Nova ─────────────────────────────────────────────────────────
def afficher_bandeau_apps():
    import streamlit.components.v1 as components
    # ✅ FIX MOBILE : hauteur augmentée de 320 → 420 pour éviter la coupure
    components.html("""<!DOCTYPE html><html><head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:transparent;font-family:'DM Sans',sans-serif;padding:0}
.banner{background:linear-gradient(135deg,rgba(15,25,60,.97) 0%,rgba(20,35,80,.97) 100%);border:1px solid rgba(77,138,255,.3);border-radius:20px;padding:1.1rem 1rem 1.2rem;position:relative;overflow:hidden}
.banner::before{content:'';position:absolute;inset:0;background:radial-gradient(ellipse at top right,rgba(77,138,255,.13) 0%,transparent 65%);pointer-events:none}
.title{font-family:'Syne',sans-serif;font-size:.7rem;font-weight:700;color:rgba(77,138,255,.75);letter-spacing:2.5px;text-transform:uppercase;text-align:center;margin-bottom:.85rem}
.grid{display:flex;flex-direction:column;gap:.7rem}
.card{background:rgba(255,255,255,.04);border:1px solid rgba(77,138,255,.2);border-radius:14px;padding:.85rem .9rem}
.card-top{display:flex;align-items:center;gap:.8rem;margin-bottom:.7rem}
.icon{width:44px;height:44px;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:1.4rem;flex-shrink:0}
.icon-blue{background:linear-gradient(135deg,#1a3f9f,#2979ff)}
.icon-violet{background:linear-gradient(135deg,#4a1fa8,#7c3aed)}
.body{flex:1;min-width:0}
.name{font-family:'Syne',sans-serif;font-weight:700;font-size:.9rem;color:#e8eeff;display:flex;align-items:center;gap:6px;margin-bottom:.15rem;flex-wrap:wrap}
.badge{font-size:.58rem;font-weight:700;letter-spacing:1px;padding:2px 8px;border-radius:20px;white-space:nowrap}
.badge-green{background:rgba(0,230,118,.1);border:1px solid rgba(0,230,118,.35);color:#00e676}
.badge-violet{background:rgba(124,58,237,.15);border:1px solid rgba(124,58,237,.4);color:#c084fc}
.desc{font-size:.73rem;color:#7a90b8;line-height:1.45}
.btn{display:block;width:100%;padding:.65rem 1rem;border-radius:10px;font-family:'Syne',sans-serif;font-size:.8rem;font-weight:700;letter-spacing:.8px;text-align:center;text-decoration:none;color:#fff;transition:opacity .15s,transform .1s;-webkit-tap-highlight-color:transparent}
.btn:active{transform:scale(.97);opacity:.85}
.btn-green{background:linear-gradient(135deg,#00c853,#00897b);box-shadow:0 3px 14px rgba(0,200,83,.35)}
.btn-violet{background:linear-gradient(135deg,#7c3aed,#4f46e5);box-shadow:0 3px 14px rgba(124,58,237,.35)}
</style></head><body>
<div class="banner">
  <div class="title">✦ Découvrez aussi nos autres apps Nova ✦</div>
  <div class="grid">
    <div class="card">
      <div class="card-top">
        <div class="icon icon-blue">🤖</div>
        <div class="body">
          <div class="name">Nova Platform <span class="badge badge-green">GRATUIT</span></div>
          <div class="desc">Génère tes CV, exposés, rapports et documents scolaires grâce à l'IA — en quelques secondes.</div>
        </div>
      </div>
      <a href="https://dawn-flower-c012.mypublic1309.workers.dev/" target="_blank" class="btn btn-green">🚀 Visiter Nova Platform →</a>
    </div>
    <div class="card">
      <div class="card-top">
        <div class="icon icon-violet">🛠️</div>
        <div class="body">
          <div class="name">Nova Conception <span class="badge badge-violet">GRATUIT</span></div>
          <div class="desc">Crée ton site web ou ton application mobile professionnelle — sans coder, gratuitement.</div>
        </div>
      </div>
      <a href="https://aged-term-0d2e.nova1309ia.workers.dev/" target="_blank" class="btn btn-violet">🌐 Visiter Nova Conception →</a>
    </div>
  </div>
</div>
</body></html>""", height=420, scrolling=False)


# ── Canvas interactif (affichage uniquement — boutons Streamlit natifs) ──────
def afficher_canvas(img_pil, coins_initiales, prefix, sk_local):
    """Affiche le canvas dans un components.html. Stocke les coins via une
    hidden text_input mise à jour par postMessage → st.session_state."""
    import streamlit.components.v1 as components

    max_dim = 900
    img_d = img_pil.copy()
    w_o, h_o = img_d.size
    if max(w_o, h_o) > max_dim:
        sc = max_dim / max(w_o, h_o)
        img_d = img_d.resize((int(w_o * sc), int(h_o * sc)), Image.LANCZOS)
    wd, hd = img_d.size
    sx, sy = w_o / wd, h_o / hd

    buf = io.BytesIO()
    img_d.save(buf, format="JPEG", quality=75)
    b64 = base64.b64encode(buf.getvalue()).decode()

    if coins_initiales:
        cd = [[c[0] / sx, c[1] / sy] for c in coins_initiales]
    else:
        mx, my = wd * .08, hd * .08
        cd = [[mx, my], [wd - mx, my], [wd - mx, hd - my], [mx, hd - my]]

    st.session_state[f"canvas_sx_{prefix}_{sk_local}"] = sx
    st.session_state[f"canvas_sy_{prefix}_{sk_local}"] = sy

    coins_json_key = f"canvas_coins_json_{prefix}_{sk_local}"
    # Toujours initialiser avec les coins courants (évite les coords obsolètes)
    if coins_json_key not in st.session_state:
        st.session_state[coins_json_key] = json.dumps(cd)

    relay_key = f"relay_coins_{prefix}_{sk_local}"
    relay_val = st.text_input("_coins_", key=relay_key, label_visibility="collapsed",
                               value=st.session_state[coins_json_key])

    # TOUJOURS mettre à jour coins_json_key depuis le relay si valide
    # (le relay est mis à jour par sendCoins() côté JS à chaque déplacement de coin)
    if relay_val:
        try:
            parsed_relay = json.loads(relay_val)
            if (isinstance(parsed_relay, list) and len(parsed_relay) == 4
                    and all(isinstance(p, list) and len(p) == 2 for p in parsed_relay)):
                st.session_state[coins_json_key] = relay_val  # toujours écraser
        except Exception:
            pass

    html = f"""<!DOCTYPE html><html><head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#050d1a;padding:2px;font-family:'Segoe UI',sans-serif}}
canvas{{display:block;width:100%;border-radius:10px;touch-action:none}}
.hint{{text-align:center;font-size:.72rem;color:#3a5070;margin-top:5px;line-height:1.5}}
</style></head><body>
<canvas id="cv"></canvas>
<div class="hint">⬛ Glisser l'intérieur pour déplacer &nbsp;·&nbsp; 🔵 Poignées pour redimensionner &nbsp;·&nbsp; 🔄 Rotation en haut</div>
<script>
const IW={wd}, IH={hd};
const INIT={json.dumps(cd)};
const cv=document.getElementById('cv');
const ctx=cv.getContext('2d');
cv.width=IW; cv.height=IH;
const img=new Image(); img.src='data:image/jpeg;base64,{b64}';

/* ── Rectangle state ── */
/* cx,cy = centre ; w,h = demi-largeur/hauteur ; angle = radians */
function initFromCorners(pts){{
  const xs=pts.map(p=>p[0]), ys=pts.map(p=>p[1]);
  const x0=Math.min(...xs),x1=Math.max(...xs);
  const y0=Math.min(...ys),y1=Math.max(...ys);
  return {{cx:(x0+x1)/2, cy:(y0+y1)/2, hw:(x1-x0)/2, hh:(y1-y0)/2, angle:0}};
}}
let R=initFromCorners(INIT);

/* ── Drag state ── */
/* mode: null | 'move' | 'resize-NW'|'NE'|'SE'|'SW' | 'resize-N'|'S'|'E'|'W' | 'rotate' */
let drag=null, dragStart=null, snapR=null;

const HR=Math.max(16, Math.min(IW,IH)*.038); /* handle radius */
const ROT_DIST=HR*2.8;                         /* rotation handle offset from top edge */

/* ── Corners & handles in world space ── */
function corners(){{
  const cos=Math.cos(R.angle), sin=Math.sin(R.angle);
  const rot=(lx,ly)=>{{
    return {{x: R.cx + lx*cos - ly*sin,
             y: R.cy + lx*sin + ly*cos}};
  }};
  return {{
    TL:rot(-R.hw,-R.hh), TR:rot( R.hw,-R.hh),
    BR:rot( R.hw, R.hh), BL:rot(-R.hw, R.hh),
    N: rot(0,-R.hh), S: rot(0, R.hh),
    E: rot( R.hw,0), W: rot(-R.hw,0),
    ROT: rot(0,-R.hh-ROT_DIST)
  }};
}}

/* ── Draw ── */
img.onload=()=>{{draw();sendCoins();}};

function draw(){{
  ctx.clearRect(0,0,IW,IH);
  ctx.drawImage(img,0,0);

  const c=corners();
  const pts=[c.TL,c.TR,c.BR,c.BL];

  /* overlay sombre hors rectangle */
  const off=new OffscreenCanvas(IW,IH), oc=off.getContext('2d');
  oc.fillStyle='rgba(0,0,0,.52)'; oc.fillRect(0,0,IW,IH);
  oc.globalCompositeOperation='destination-out';
  oc.beginPath(); oc.moveTo(pts[0].x,pts[0].y);
  pts.forEach((p,i)=>{{if(i)oc.lineTo(p.x,p.y)}}); oc.closePath();
  oc.fillStyle='rgba(0,0,0,1)'; oc.fill();
  ctx.drawImage(off,0,0);

  /* bordure rectangle */
  ctx.beginPath(); ctx.moveTo(pts[0].x,pts[0].y);
  pts.forEach((p,i)=>{{if(i)ctx.lineTo(p.x,p.y)}}); ctx.closePath();
  ctx.strokeStyle='#2979ff'; ctx.lineWidth=Math.max(2,HR*.12); ctx.stroke();

  /* ligne rotation */
  ctx.beginPath(); ctx.moveTo(c.N.x,c.N.y); ctx.lineTo(c.ROT.x,c.ROT.y);
  ctx.strokeStyle='rgba(41,121,255,.5)'; ctx.lineWidth=Math.max(1.5,HR*.07); ctx.stroke();

  /* poignées coins (bleu) */
  [['TL',c.TL],['TR',c.TR],['BR',c.BR],['BL',c.BL]].forEach(([k,p])=>{{
    ctx.beginPath(); ctx.arc(p.x,p.y,HR,0,Math.PI*2);
    ctx.fillStyle=drag&&drag.mode==='resize-'+k?'#82b1ff':'#2979ff';
    ctx.fill();
    ctx.strokeStyle='#fff'; ctx.lineWidth=Math.max(1.5,HR*.09); ctx.stroke();
    /* croix */
    const s=HR*.38;
    ctx.strokeStyle='rgba(255,255,255,.85)'; ctx.lineWidth=Math.max(1.5,HR*.07);
    ctx.beginPath(); ctx.moveTo(p.x-s,p.y); ctx.lineTo(p.x+s,p.y); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(p.x,p.y-s); ctx.lineTo(p.x,p.y+s); ctx.stroke();
  }});

  /* poignées milieux (petites, cyan) */
  [['N',c.N],['S',c.S],['E',c.E],['W',c.W]].forEach(([k,p])=>{{
    const sr=HR*.65;
    ctx.beginPath(); ctx.arc(p.x,p.y,sr,0,Math.PI*2);
    ctx.fillStyle=drag&&drag.mode==='resize-'+k?'#80deea':'#00b4d8';
    ctx.fill();
    ctx.strokeStyle='#fff'; ctx.lineWidth=Math.max(1,HR*.07); ctx.stroke();
  }});

  /* poignée rotation (orange) */
  ctx.beginPath(); ctx.arc(c.ROT.x,c.ROT.y,HR*.72,0,Math.PI*2);
  ctx.fillStyle=drag&&drag.mode==='rotate'?'#ffcc02':'#ffa726';
  ctx.fill();
  ctx.strokeStyle='#fff'; ctx.lineWidth=Math.max(1.5,HR*.08); ctx.stroke();
  ctx.fillStyle='#fff'; ctx.font=`bold ${{Math.round(HR*.7)}}px Segoe UI`;
  ctx.textAlign='center'; ctx.textBaseline='middle';
  ctx.fillText('↻',c.ROT.x,c.ROT.y+1);
}}

/* ── Input helpers ── */
function gp(e){{
  const r=cv.getBoundingClientRect(), scx=IW/r.width, scy=IH/r.height;
  const s=e.touches?e.touches[0]:e;
  return {{x:(s.clientX-r.left)*scx, y:(s.clientY-r.top)*scy}};
}}
function dist(a,b){{return Math.sqrt((a.x-b.x)**2+(a.y-b.y)**2);}}

/* check hit on a world-space point, radius rr */
function hitPt(p,wp,rr){{return dist(p,wp)<rr;}}

/* check if point is inside rotated rectangle */
function insideRect(p){{
  const cos=Math.cos(-R.angle), sin=Math.sin(-R.angle);
  const dx=p.x-R.cx, dy=p.y-R.cy;
  const lx=dx*cos-dy*sin, ly=dx*sin+dy*cos;
  return Math.abs(lx)<=R.hw && Math.abs(ly)<=R.hh;
}}

function detectHit(p){{
  const c=corners();
  const hr2=HR*1.6, sr2=HR*.65*1.8;
  /* rotation first (smallest, on top) */
  if(hitPt(p,c.ROT,HR*1.3)) return 'rotate';
  /* corner handles */
  if(hitPt(p,c.TL,hr2)) return 'resize-TL';
  if(hitPt(p,c.TR,hr2)) return 'resize-TR';
  if(hitPt(p,c.BR,hr2)) return 'resize-BR';
  if(hitPt(p,c.BL,hr2)) return 'resize-BL';
  /* mid handles */
  if(hitPt(p,c.N,sr2))  return 'resize-N';
  if(hitPt(p,c.S,sr2))  return 'resize-S';
  if(hitPt(p,c.E,sr2))  return 'resize-E';
  if(hitPt(p,c.W,sr2))  return 'resize-W';
  /* inside = move */
  if(insideRect(p))      return 'move';
  return null;
}}

/* ── Drag logic ── */
function onDown(e){{
  e.preventDefault();
  const p=gp(e);
  const mode=detectHit(p);
  if(!mode)return;
  drag={{mode, p0:p, R0:{{...R}}}};
  draw();
}}

function localCoord(wx,wy){{
  /* world → local (unrotated) */
  const cos=Math.cos(-R.angle), sin=Math.sin(-R.angle);
  const dx=wx-R.cx, dy=wy-R.cy;
  return {{lx:dx*cos-dy*sin, ly:dx*sin+dy*cos}};
}}

function onMove(e){{
  if(!drag)return; e.preventDefault();
  const p=gp(e);
  const dx=p.x-drag.p0.x, dy=p.y-drag.p0.y;
  const R0=drag.R0;

  if(drag.mode==='move'){{
    R.cx=Math.max(0,Math.min(IW, R0.cx+dx));
    R.cy=Math.max(0,Math.min(IH, R0.cy+dy));

  }} else if(drag.mode==='rotate'){{
    const angle=Math.atan2(p.y-R.cy, p.x-R.cx)+Math.PI/2;
    R.angle=angle;

  }} else {{
    /* resize : trouver coin opposé fixe, puis recalcul centre+demi-dims */
    const cos=Math.cos(R0.angle), sin=Math.sin(R0.angle);
    const rot =(lx,ly)=>{{return {{x:R0.cx+lx*cos-ly*sin, y:R0.cy+lx*sin+ly*cos}}}};
    const unrot=(wx,wy)=>{{
      const ddx=wx-R0.cx, ddy=wy-R0.cy;
      return {{lx:ddx*cos+ddy*sin, ly:-ddx*sin+ddy*cos}};
    }};

    /* ancre = coin/milieu opposé ; mobile = coin/milieu qu'on tire */
    let anchor, moveFn;
    if(drag.mode==='resize-TL'){{
      anchor=rot( R0.hw, R0.hh);
      moveFn=(px,py)=>{{
        const {{lx,ly}}=unrot(px,py);
        R.hw=Math.max(20,Math.abs(R0.hw-lx)/1)*1; // asymmetric safe
        /* recompute from anchor */
        const nlx=-R.hw, nly=-R.hh;
        // actually use direct approach below
      }};
    }}

    /* simpler unified approach: find opposite anchor corner/edge in world */
    let ax=R0.cx, ay=R0.cy; /* anchor world coords */
    let moveX=true, moveY=true;
    if(drag.mode==='resize-TL'){{ ax=rot( R0.hw, R0.hh).x; ay=rot( R0.hw, R0.hh).y; }}
    if(drag.mode==='resize-TR'){{ ax=rot(-R0.hw, R0.hh).x; ay=rot(-R0.hw, R0.hh).y; }}
    if(drag.mode==='resize-BR'){{ ax=rot(-R0.hw,-R0.hh).x; ay=rot(-R0.hw,-R0.hh).y; }}
    if(drag.mode==='resize-BL'){{ ax=rot( R0.hw,-R0.hh).x; ay=rot( R0.hw,-R0.hh).y; }}
    if(drag.mode==='resize-N') {{ ax=rot(0, R0.hh).x;      ay=rot(0, R0.hh).y;  moveX=false; }}
    if(drag.mode==='resize-S') {{ ax=rot(0,-R0.hh).x;      ay=rot(0,-R0.hh).y;  moveX=false; }}
    if(drag.mode==='resize-E') {{ ax=rot(-R0.hw,0).x;      ay=rot(-R0.hw,0).y;  moveY=false; }}
    if(drag.mode==='resize-W') {{ ax=rot( R0.hw,0).x;      ay=rot( R0.hw,0).y;  moveY=false; }}

    /* current drag point in local frame relative to anchor */
    const ddx=p.x-ax, ddy=p.y-ay;
    const llx= ddx*cos+ddy*sin;  /* local x of (drag-anchor) */
    const lly=-ddx*sin+ddy*cos;  /* local y */

    if(moveX&&moveY){{
      R.hw=Math.max(20, Math.abs(llx)/2);
      R.hh=Math.max(20, Math.abs(lly)/2);
      R.cx=ax+(llx/2)*cos-(lly/2)*sin;
      R.cy=ay+(llx/2)*sin+(lly/2)*cos;
    }} else if(!moveX){{
      R.hh=Math.max(20, Math.abs(lly)/2);
      R.cx=ax-(0)*cos-( lly/2)*sin;
      R.cy=ay-(0)*sin+( lly/2)*cos;
    }} else {{
      R.hw=Math.max(20, Math.abs(llx)/2);
      R.cx=ax+(llx/2)*cos-(0)*sin;
      R.cy=ay+(llx/2)*sin+(0)*cos;
    }}
  }}
  draw();
}}

function onUp(e){{
  if(!drag)return;
  drag=null;
  sendCoins();
  draw();
}}

/* ── sendCoins : envoie les 4 coins [TL,TR,BR,BL] en coords canvas ── */
function sendCoins(){{
  const c=corners();
  const disp=[[c.TL.x,c.TL.y],[c.TR.x,c.TR.y],[c.BR.x,c.BR.y],[c.BL.x,c.BL.y]]
    .map(p=>[Math.round(p[0]),Math.round(p[1])]);
  const val=JSON.stringify(disp);
  try{{
    const doc=window.parent.document;
    const nativeSetter=Object.getOwnPropertyDescriptor(
      window.parent.HTMLInputElement.prototype,'value').set;
    let sent=false;
    for(const el of doc.querySelectorAll('input[type="text"]')){{
      if(el.getAttribute('aria-label')==='_coins_'){{
        nativeSetter.call(el,val); el.dispatchEvent(new Event('input',{{bubbles:true}}));
        sent=true; break;
      }}
    }}
    if(!sent){{
      for(const el of doc.querySelectorAll('input[type="text"]')){{
        const st2=window.parent.getComputedStyle(el.closest('[data-testid="stTextInput"]')||el);
        if(st2.display==='none'||st2.visibility==='hidden'){{
          nativeSetter.call(el,val); el.dispatchEvent(new Event('input',{{bubbles:true}}));
        }}
      }}
    }}
  }}catch(e){{}}
}}

cv.addEventListener('mousedown', onDown);
cv.addEventListener('touchstart', onDown, {{passive:false}});
cv.addEventListener('mousemove', onMove);
cv.addEventListener('touchmove', onMove, {{passive:false}});
cv.addEventListener('mouseup', onUp);
cv.addEventListener('touchend', onUp);
</script></body></html>"""

    # Hauteur = proportionnelle à la VRAIE largeur d'affichage (480px max = block-container)
    # et non à 320px, sinon les coordonnées des coins sont décalées visuellement.
    display_w = 460  # largeur utile estimée du block-container mobile (480px - padding)
    display_h = int(hd * display_w / wd)
    components.html(html, height=display_h + 50, scrolling=False)
    return coins_json_key


# ── Affichage résultat ────────────────────────────────────────────────────────
def afficher_resultat(img, nom_fichier, badge_mode, key_dl, key_btn):
    try:
        pdf_bytes, img_rgb = image_vers_pdf(img)
        w,h = img_rgb.size
        ko = len(pdf_bytes)/1024
        taille = f"{ko/1024:.1f} Mo" if ko>=1024 else f"{ko:.0f} Ko"

        st.markdown('<div class="steps-row">'
                    '<div class="step-badge">① ✓ Photo prise</div>'
                    '<div class="step-badge">② ✓ Recadrage</div>'
                    '<div class="step-badge step-active">③ Télécharger</div>'
                    '</div>', unsafe_allow_html=True)
        st.markdown('<div class="preview-label">APERÇU DU DOCUMENT</div>', unsafe_allow_html=True)
        st.image(img_rgb, use_container_width=True)

        badges={"auto":'<span class="badge-crop">✂️ Recadré auto</span>',
                "manual":'<span class="badge-manual">✋ Recadrage manuel</span>',
                "none":'<span class="badge-no-crop">⚠️ Sans recadrage</span>'}
        st.markdown(f"""<div class="pdf-info">📄 PDF prêt&nbsp;! {badges.get(badge_mode,'')}
            <br>Taille : <span>{taille}</span> &nbsp;|&nbsp; Résolution : <span>{w} × {h} px</span>
        </div>""", unsafe_allow_html=True)
        st.download_button(label="⬇️  TÉLÉCHARGER LE PDF", data=pdf_bytes,
                           file_name=nom_fichier, mime="application/pdf", key=key_dl)

        # ── Bandeau Apps Nova (affiché après le téléchargement) ──
        afficher_bandeau_apps()

    except Exception as e:
        st.error(f"Erreur PDF : {e}")

    st.markdown('<hr class="sep">', unsafe_allow_html=True)
    if st.button("🔄  Scanner un autre document", key=key_btn):
        for k in list(st.session_state.keys()):
            if k.startswith(("state_","corners_","badge_","img_b64_","nom_pdf_","mode_")):
                del st.session_state[k]
        st.session_state["scan_key"] = sk+1
        st.rerun()


# ── Flux principal ────────────────────────────────────────────────────────────
def flux_image(img_pil, nom_pdf, prefix):
    sk_local    = st.session_state["scan_key"]
    state_key   = f"state_{prefix}"
    corners_key = f"corners_{prefix}"
    badge_key   = f"badge_{prefix}"
    img_b64_key = f"img_b64_{prefix}"
    nom_key     = f"nom_pdf_{prefix}"
    mode_key    = f"mode_{prefix}"
    relay_key   = f"_relay_{prefix}_{sk_local}"

    if img_b64_key not in st.session_state:
        st.session_state[img_b64_key] = img_to_b64(img_pil)
        st.session_state[nom_key] = nom_pdf

    if state_key not in st.session_state:
        st.session_state[state_key] = "canvas"
        # Coins initiaux = pleine image avec 2% de marge
        st.session_state[corners_key] = None  # pas de coins auto par défaut

    img_pil = b64_to_img(st.session_state[img_b64_key])
    nom_pdf = st.session_state[nom_key]
    state   = st.session_state[state_key]

    # ── CANVAS ──
    if state == "canvas":
        st.markdown('<div class="steps-row">'
                    '<div class="step-badge">① ✓ Photo prise</div>'
                    '<div class="step-badge step-active">② Ajuster le recadrage</div>'
                    '<div class="step-badge">③ PDF</div>'
                    '</div>', unsafe_allow_html=True)

        coins = st.session_state.get(corners_key)

        # ── Bouton détection automatique ──
        if st.button("🔍 Détecter automatiquement", key=f"auto_{prefix}_{sk_local}", use_container_width=True):
            with st.spinner("🔍 Détection du document en cours..."):
                coins_auto = detecter_contour_auto(img_pil)
            if coins_auto:
                st.session_state[corners_key] = coins_auto
                # Forcer réinitialisation des coins du canvas
                ck = f"canvas_coins_json_{prefix}_{sk_local}"
                if ck in st.session_state:
                    del st.session_state[ck]
                st.success("✅ Document détecté ! Ajustez les coins si nécessaire.")
            else:
                st.warning("⚠️ Détection échouée — placez les coins manuellement.")
            st.rerun()

        if coins:
            st.markdown("""<div style="background:rgba(0,230,118,.07);border:1px solid #00e67644;
                border-radius:10px;padding:.55rem 1rem;font-size:.78rem;color:#00e676;
                margin-bottom:.6rem;text-align:center;">
                ✂️ Document détecté — glissez les coins bleus pour ajuster</div>""",
                unsafe_allow_html=True)
        else:
            st.markdown('<div class="tip-box">💡 Cliquez sur "Détecter automatiquement" ou placez les 4 coins manuellement.</div>',
                        unsafe_allow_html=True)

        st.markdown("<div style='font-size:.78rem;color:#7a90b8;margin-bottom:.4rem;'>Mode de rendu :</div>",
                    unsafe_allow_html=True)
        mode = st.radio("Mode", ["🎨 Couleur", "🌫️ Niveaux de gris", "📄 Noir & Blanc"],
                        horizontal=True, key=f"mode_radio_{prefix}_{sk_local}",
                        label_visibility="collapsed")
        mode_map = {"🎨 Couleur": "couleur", "🌫️ Niveaux de gris": "gris", "📄 Noir & Blanc": "nb"}
        st.session_state[mode_key] = mode_map[mode]

        coins_json_key = afficher_canvas(img_pil, coins, prefix, sk_local)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("⏭ Sans recadrage", key=f"skip_{prefix}_{sk_local}", use_container_width=True):
                st.session_state[badge_key]  = "none"
                st.session_state[state_key]  = "result"
                st.rerun()
        with col2:
            if st.button("✅ Recadrer & Générer PDF", key=f"confirm_{prefix}_{sk_local}", use_container_width=True):
                raw = st.session_state.get(coins_json_key, "")
                sx_val = st.session_state.get(f"canvas_sx_{prefix}_{sk_local}", 1.0)
                sy_val = st.session_state.get(f"canvas_sy_{prefix}_{sk_local}", 1.0)
                corners_ok = False
                try:
                    parsed = json.loads(raw) if raw else None
                    if parsed and isinstance(parsed[0], list) and len(parsed) == 4:
                        # Les coords du canvas sont en pixels d'affichage → repasser en pixels originaux
                        corners_orig = [[round(p[0] * sx_val), round(p[1] * sy_val)] for p in parsed]
                        # Sanity check : les coins doivent être dans les dimensions de l'image
                        w_orig, h_orig = img_pil.size
                        valid = all(
                            0 <= c[0] <= w_orig and 0 <= c[1] <= h_orig
                            for c in corners_orig
                        )
                        if valid:
                            st.session_state[corners_key] = corners_orig
                            st.session_state[badge_key] = "manual"
                            corners_ok = True
                except Exception:
                    pass
                if not corners_ok:
                    # Fallback : utiliser les coins auto-détectés (déjà en coords originaux)
                    st.session_state[corners_key] = coins
                    st.session_state[badge_key] = "auto" if coins else "none"
                st.session_state[state_key] = "result"
                st.rerun()

    # ── RÉSULTAT ──
    elif state == "result":
        badge   = st.session_state.get(badge_key, "none")
        corners = st.session_state.get(corners_key)
        mode    = st.session_state.get(mode_key, "couleur")

        if badge == "none" or not corners:
            img_finale = img_pil
        else:
            try:
                img_finale = recadrer_depuis_coins(img_pil, corners, mode)
            except Exception as e:
                img_finale = img_pil
                st.warning(f"Recadrage impossible, image originale utilisée. ({e})")

        afficher_resultat(img_finale, nom_pdf, badge,
                          key_dl=f"dl_{prefix}_{sk_local}",
                          key_btn=f"reset_{prefix}_{sk_local}")


# ══ ONGLETS ═══════════════════════════════════════════════════════════════════
tab_mobile, tab_import = st.tabs(["📷  Caméra", "🖼️  Importer"])

with tab_mobile:
    photo = st.file_uploader(label="photo", type=["jpg","jpeg","png","webp","bmp","heic"],
                              label_visibility="collapsed", key=f"cam_{sk}")
    if photo is None:
        import streamlit.components.v1 as components
        # ✅ FIX MOBILE : hauteur augmentée de 720 → 820 pour afficher le bandeau complet
        components.html("""<!DOCTYPE html><html><head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:transparent;font-family:'DM Sans',sans-serif}
.cam-card{background:rgba(41,121,255,.07);border:1.5px dashed #2979ff88;border-radius:18px;padding:1.3rem 1rem;margin-bottom:.9rem;text-align:center}
.cam-icon{font-size:3.2rem;display:block;margin-bottom:.45rem;animation:pulse 2s infinite}
@keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.08)}}
.cam-title{font-size:1rem;font-weight:700;color:#fff;margin-bottom:.4rem;font-family:'Syne',sans-serif}
.cam-tip{font-size:.78rem;color:#a0b4d0;margin:.2rem 0}
.big-btn{display:block;width:100%;background:linear-gradient(135deg,#2979ff,#1a5cd4);
  color:#fff;border:none;border-radius:16px;padding:1rem;font-size:1.05rem;font-weight:700;
  cursor:pointer;box-shadow:0 4px 24px rgba(41,121,255,.55);font-family:'Syne',sans-serif;
  -webkit-tap-highlight-color:transparent;margin-bottom:.9rem;letter-spacing:.5px}
.sep{border:none;border-top:1px solid rgba(41,121,255,.12);margin:.9rem 0}
.banner{background:linear-gradient(135deg,rgba(15,25,60,.97) 0%,rgba(20,35,80,.97) 100%);border:1px solid rgba(77,138,255,.3);border-radius:20px;padding:1rem .9rem 1.2rem;position:relative;overflow:hidden}
.banner::before{content:'';position:absolute;inset:0;background:radial-gradient(ellipse at top right,rgba(77,138,255,.13) 0%,transparent 65%);pointer-events:none}
.banner-title{font-family:'Syne',sans-serif;font-size:.65rem;font-weight:700;color:rgba(77,138,255,.75);letter-spacing:2.5px;text-transform:uppercase;text-align:center;margin-bottom:.75rem}
.grid{display:flex;flex-direction:column;gap:.6rem}
.card{background:rgba(255,255,255,.04);border:1px solid rgba(77,138,255,.2);border-radius:14px;padding:.8rem .85rem}
.card-top{display:flex;align-items:center;gap:.75rem;margin-bottom:.65rem}
.icon{width:42px;height:42px;border-radius:12px;display:flex;align-items:center;justify-content:center;font-size:1.3rem;flex-shrink:0}
.icon-blue{background:linear-gradient(135deg,#1a3f9f,#2979ff)}
.icon-violet{background:linear-gradient(135deg,#4a1fa8,#7c3aed)}
.body{flex:1;min-width:0}
.name{font-family:'Syne',sans-serif;font-weight:700;font-size:.85rem;color:#e8eeff;display:flex;align-items:center;gap:6px;margin-bottom:.12rem;flex-wrap:wrap}
.badge{font-size:.55rem;font-weight:700;letter-spacing:1px;padding:2px 7px;border-radius:20px;white-space:nowrap}
.badge-green{background:rgba(0,230,118,.1);border:1px solid rgba(0,230,118,.35);color:#00e676}
.badge-violet{background:rgba(124,58,237,.15);border:1px solid rgba(124,58,237,.4);color:#c084fc}
.desc{font-size:.7rem;color:#7a90b8;line-height:1.4}
.btn{display:block;width:100%;padding:.6rem 1rem;border-radius:10px;font-family:'Syne',sans-serif;font-size:.78rem;font-weight:700;letter-spacing:.8px;text-align:center;text-decoration:none;color:#fff;transition:opacity .15s,transform .1s;-webkit-tap-highlight-color:transparent}
.btn:active{transform:scale(.97);opacity:.85}
.btn-green{background:linear-gradient(135deg,#00c853,#00897b);box-shadow:0 3px 12px rgba(0,200,83,.3)}
.btn-violet{background:linear-gradient(135deg,#7c3aed,#4f46e5);box-shadow:0 3px 12px rgba(124,58,237,.3)}
</style></head><body>
<div class="cam-card">
  <span class="cam-icon">📷</span>
  <div class="cam-title">Photographiez votre document</div>
  <div class="cam-tip">💡 Fond contrasté · ☀️ Bonne lumière · 📐 4 coins visibles</div>
</div>
<button class="big-btn" onclick="openCamera()">📷 &nbsp; Ouvrir l'appareil photo</button>
<div class="sep"></div>
<div class="banner">
  <div class="banner-title">✦ Découvrez aussi nos autres apps Nova ✦</div>
  <div class="grid">
    <div class="card">
      <div class="card-top">
        <div class="icon icon-blue">🤖</div>
        <div class="body">
          <div class="name">Nova Platform <span class="badge badge-green">GRATUIT</span></div>
          <div class="desc">Génère tes CV, exposés, rapports et documents scolaires grâce à l'IA — en quelques secondes.</div>
        </div>
      </div>
      <a href="https://dawn-flower-c012.mypublic1309.workers.dev/" target="_blank" class="btn btn-green">🚀 Visiter Nova Platform →</a>
    </div>
    <div class="card">
      <div class="card-top">
        <div class="icon icon-violet">🛠️</div>
        <div class="body">
          <div class="name">Nova Conception <span class="badge badge-violet">GRATUIT</span></div>
          <div class="desc">Crée ton site web ou ton application mobile professionnelle — sans coder, gratuitement.</div>
        </div>
      </div>
      <a href="https://aged-term-0d2e.nova1309ia.workers.dev/" target="_blank" class="btn btn-violet">🌐 Visiter Nova Conception →</a>
    </div>
  </div>
</div>
<script>
function openCamera(){
  try{const inp=window.parent.document.querySelector('input[type="file"]');
    if(inp){inp.setAttribute('capture','environment');inp.setAttribute('accept','image/*');inp.click();return;}}catch(e){}
  const inp=document.createElement('input');inp.type='file';inp.accept='image/*';
  inp.setAttribute('capture','environment');inp.click();
}
</script>
</body></html>""", height=820, scrolling=False)
    else:
        img_mob = corriger_orientation(Image.open(photo))
        flux_image(img_mob, "nova_scan_document.pdf", "mob")

with tab_import:
    import streamlit.components.v1 as components
    # ✅ FIX MOBILE : hauteur augmentée de 430 → 500 pour afficher toutes les features
    components.html("""<!DOCTYPE html><html><head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@400;500;600&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:transparent;font-family:'DM Sans',sans-serif}
.premium-card{
  background:linear-gradient(135deg,rgba(15,25,60,.97) 0%,rgba(25,18,55,.97) 100%);
  border:1.5px solid rgba(124,58,237,.4);
  border-radius:20px;padding:1.4rem 1.1rem 1.4rem;
  position:relative;overflow:hidden;text-align:center;
}
.premium-card::before{
  content:'';position:absolute;inset:0;
  background:radial-gradient(ellipse at top center,rgba(124,58,237,.18) 0%,transparent 65%);
  pointer-events:none;
}
.lock-icon{font-size:2.8rem;display:block;margin-bottom:.6rem;filter:drop-shadow(0 0 14px rgba(124,58,237,.6))}
.premium-title{
  font-family:'Syne',sans-serif;font-size:1.1rem;font-weight:800;
  color:#e8eeff;margin-bottom:.35rem;letter-spacing:.5px;
}
.premium-title span{
  background:linear-gradient(135deg,#c084fc,#7c3aed);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;
}
.premium-desc{font-size:.8rem;color:#8a9cc0;line-height:1.55;margin-bottom:1rem}
.price-box{
  display:inline-flex;align-items:baseline;gap:5px;
  background:rgba(124,58,237,.12);border:1px solid rgba(124,58,237,.35);
  border-radius:40px;padding:.45rem 1.2rem;margin-bottom:1.1rem;
}
.price-amount{font-family:'Syne',sans-serif;font-size:1.6rem;font-weight:800;color:#c084fc}
.price-unit{font-size:.72rem;color:#7a6a9a;font-weight:600}
.features{text-align:left;margin-bottom:1.2rem;display:flex;flex-direction:column;gap:.45rem}
.feat{display:flex;align-items:center;gap:.55rem;font-size:.77rem;color:#a0b0cc}
.feat-icon{font-size:.9rem;flex-shrink:0}
.btn-premium{
  display:block;width:100%;padding:.8rem 1rem;
  background:linear-gradient(135deg,#7c3aed,#4f46e5);
  color:#fff;text-decoration:none;
  border-radius:14px;font-family:'Syne',sans-serif;
  font-size:.92rem;font-weight:700;letter-spacing:.8px;
  box-shadow:0 4px 20px rgba(124,58,237,.5);
  transition:transform .1s,opacity .15s;
  -webkit-tap-highlight-color:transparent;
}
.btn-premium:active{transform:scale(.97);opacity:.85}
</style></head><body>
<div class="premium-card">
  <span class="lock-icon">🔒</span>
  <div class="premium-title">Passe à la version <span>Premium</span></div>
  <div class="premium-desc">L'import d'images depuis ta galerie est réservé aux membres Premium. Débloque cette fonctionnalité et bien plus encore !</div>
  <div class="price-box">
    <span class="price-amount">1 000</span>
    <span class="price-unit">FCFA / mois</span>
  </div>
  <div class="features">
    <div class="feat"><span class="feat-icon">✅</span> Import depuis la galerie (JPG, PNG, WEBP…)</div>
    <div class="feat"><span class="feat-icon">✅</span> Scanner sans limite de documents</div>
    <div class="feat"><span class="feat-icon">✅</span> Accès prioritaire aux nouvelles fonctions</div>
    <div class="feat"><span class="feat-icon">✅</span> Support WhatsApp dédié</div>
  </div>
  <a href="https://wa.me/2250171542505?text=Bonjour%2C+je+veux+passer+à+la+version+Premium+de+Nova+Scan+%281000+FCFA%2Fmois%29" target="_blank" class="btn-premium">💬 Passer à Premium via WhatsApp</a>
</div>
</body></html>""", height=500, scrolling=False)

st.markdown("""<hr class="sep"><div style="text-align:center;font-size:.7rem;color:#2e3f5c;">
Nova Scan · Traitement 100 % en mémoire · Aucun fichier stocké</div>""", unsafe_allow_html=True)
