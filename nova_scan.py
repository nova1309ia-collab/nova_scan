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
html,body,[data-testid="stAppViewContainer"]{background-color:#050d1a;color:#e0e8ff;font-family:'Segoe UI',sans-serif}
[data-testid="stHeader"]{display:none}
[data-testid="stFileUploader"]{display:none!important}
.nova-title{text-align:center;font-size:2rem;font-weight:700;color:#2979ff;margin-bottom:.2rem;letter-spacing:2px}
.nova-subtitle{text-align:center;font-size:.85rem;color:#7a90b8;margin-bottom:1.8rem;letter-spacing:1px;text-transform:uppercase}
.pdf-info{background:rgba(0,229,255,.06);border:1px solid rgba(0,229,255,.2);border-radius:10px;padding:1rem 1.2rem;margin:1rem 0;font-size:.85rem}
.pdf-info span{color:#00e5ff;font-weight:600}
.badge-crop{display:inline-block;background:rgba(0,230,118,.12);border:1px solid #00e676;border-radius:20px;padding:3px 12px;font-size:.72rem;color:#00e676;margin-left:8px}
.badge-manual{display:inline-block;background:rgba(41,121,255,.15);border:1px solid #2979ff;border-radius:20px;padding:3px 12px;font-size:.72rem;color:#82b1ff;margin-left:8px}
.badge-no-crop{display:inline-block;background:rgba(255,193,7,.12);border:1px solid #ffc107;border-radius:20px;padding:3px 12px;font-size:.72rem;color:#ffc107;margin-left:8px}
[data-testid="stDownloadButton"]>button{background-color:#2979ff!important;color:white!important;border:none!important;border-radius:14px!important;font-weight:700!important;font-size:1.1rem!important;padding:.9rem 2rem!important;width:100%!important;letter-spacing:1px!important;box-shadow:0 4px 20px rgba(41,121,255,.4)!important}
[data-testid="stButton"]>button{background:transparent!important;border:1px solid #2979ff55!important;color:#7a90b8!important;border-radius:8px!important;width:100%!important;margin-top:.5rem!important}
.preview-label{font-size:.75rem;color:#7a90b8;text-align:center;margin-bottom:.3rem}
.sep{border:none;border-top:1px solid #0d1e38;margin:1.5rem 0}
.tip-box{background:rgba(255,193,7,.06);border-left:3px solid #ffc107;border-radius:0 8px 8px 0;padding:.7rem 1rem;font-size:.78rem;color:#c9a227;margin-bottom:1rem}
.steps-row{display:flex;justify-content:center;gap:.5rem;margin-bottom:1.2rem;flex-wrap:wrap}
.step-badge{background:rgba(41,121,255,.12);border:1px solid #2979ff44;border-radius:20px;padding:4px 14px;font-size:.72rem;color:#7a90b8;white-space:nowrap}
.step-active{background:rgba(41,121,255,.3);border-color:#2979ff;color:#fff;font-weight:600}
div[data-testid="stTextInput"]{display:none!important}
/* Mode selector */
.mode-row{display:flex;gap:8px;margin-bottom:1rem}
.mode-btn{flex:1;padding:10px 6px;border-radius:12px;font-size:.8rem;font-weight:600;cursor:pointer;
  border:1.5px solid #2979ff44;background:rgba(41,121,255,.07);color:#7a90b8;
  font-family:'Segoe UI',sans-serif;transition:all .15s;text-align:center}
.mode-btn.active{background:rgba(41,121,255,.25);border-color:#2979ff;color:#fff}
[data-testid="stRadio"]>div{display:flex;gap:8px;flex-direction:row!important}
[data-testid="stRadio"] label{flex:1;background:rgba(41,121,255,.07);border:1.5px solid #2979ff44;
  border-radius:12px;padding:10px 6px;text-align:center;cursor:pointer;font-size:.8rem;
  font-weight:600;color:#7a90b8;transition:all .15s}
[data-testid="stRadio"] label:has(input:checked){background:rgba(41,121,255,.25);border-color:#2979ff;color:#fff}
[data-testid="stRadio"] input{display:none}
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
        edges = cv2.Canny(blur,50,150)
        edges = cv2.dilate(edges,np.ones((3,3),np.uint8),iterations=2)
        cnts,_ = cv2.findContours(edges,cv2.RETR_LIST,cv2.CHAIN_APPROX_SIMPLE)
        cnts = sorted(cnts,key=cv2.contourArea,reverse=True)[:10]
        for c in cnts:
            peri = cv2.arcLength(c,True)
            approx = cv2.approxPolyDP(c,0.02*peri,True)
            if len(approx)==4 and cv2.contourArea(c)>(small.shape[0]*small.shape[1]*0.2):
                pts = (approx.reshape(4,2)/sc).astype(np.float32)
                s=pts.sum(axis=1); diff=np.diff(pts,axis=1)
                o=np.zeros((4,2),dtype=np.float32)
                o[0]=pts[np.argmin(s)]; o[1]=pts[np.argmin(diff)]
                o[2]=pts[np.argmax(s)]; o[3]=pts[np.argmax(diff)]
                return o.tolist()
        return None
    except:
        return None

def recadrer_depuis_coins(img_pil, coins, mode="couleur"):
    """
    Recadre la perspective et applique le traitement selon le mode :
    - 'couleur'  : image couleur recadrée, légèrement améliorée
    - 'gris'     : niveaux de gris, contraste amélioré
    - 'nb'       : noir & blanc (binarisation adaptative) pour documents texte
    """
    import cv2
    img_np = np.array(img_pil.convert("RGB"))
    pts = np.array(coins, dtype=np.float32)
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
        # Améliore le contraste
        pil_gray = Image.fromarray(gray)
        pil_gray = ImageEnhance.Contrast(pil_gray).enhance(1.4)
        return pil_gray.convert("RGB")
    else:  # couleur
        pil_color = Image.fromarray(warped)
        # Légère amélioration couleur
        pil_color = ImageEnhance.Contrast(pil_color).enhance(1.2)
        pil_color = ImageEnhance.Sharpness(pil_color).enhance(1.3)
        return pil_color

def image_vers_pdf(img):
    """Convertit en PDF — PAS de correction EXIF ici (déjà faite à l'ouverture)."""
    if img.mode != "RGB":
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="PDF", resolution=150)
    buf.seek(0)
    return buf.getvalue(), img


# ── Canvas interactif ─────────────────────────────────────────────────────────
def canvas_et_relay(img_pil, coins_initiales, relay_key, prefix):
    import streamlit.components.v1 as components

    max_dim = 1200
    img_d = img_pil.copy()
    w_o, h_o = img_d.size
    if max(w_o,h_o) > max_dim:
        sc = max_dim/max(w_o,h_o)
        img_d = img_d.resize((int(w_o*sc),int(h_o*sc)), Image.LANCZOS)

    wd, hd = img_d.size
    sx, sy = w_o/wd, h_o/hd

    buf = io.BytesIO()
    img_d.save(buf, format="JPEG", quality=80)
    b64 = base64.b64encode(buf.getvalue()).decode()

    if coins_initiales:
        cd = [[c[0]/sx, c[1]/sy] for c in coins_initiales]
    else:
        mx,my = wd*.08, hd*.08
        cd = [[mx,my],[wd-mx,my],[wd-mx,hd-my],[mx,hd-my]]

    relay_val = st.text_input("_relay_", key=relay_key, label_visibility="collapsed")

    html = f"""<!DOCTYPE html><html><head>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:#050d1a;font-family:'Segoe UI',sans-serif;padding:2px}}
#wrap{{width:100%;max-width:600px;margin:0 auto}}
canvas{{display:block;width:100%;border-radius:10px;touch-action:none;cursor:crosshair}}
.toolbar{{display:flex;gap:8px;margin-top:10px}}
.btn{{flex:1;padding:14px 8px;border-radius:14px;font-size:.95rem;font-weight:700;
      cursor:pointer;border:none;font-family:'Segoe UI',sans-serif;
      -webkit-tap-highlight-color:transparent;transition:transform .1s,opacity .1s}}
.btn:active{{transform:scale(.97);opacity:.85}}
.btn-ok{{background:linear-gradient(135deg,#2979ff,#1565c0);color:#fff;box-shadow:0 4px 18px rgba(41,121,255,.5)}}
.btn-skip{{background:rgba(255,255,255,.06);border:1px solid #2979ff44!important;color:#7a90b8}}
.hint{{text-align:center;font-size:.75rem;color:#4a6080;margin-top:7px}}
#status{{text-align:center;font-size:.82rem;color:#00e676;margin-top:6px;min-height:1.4em;font-weight:600}}
</style></head><body>
<div id="wrap">
  <canvas id="cv"></canvas>
  <div class="toolbar">
    <button class="btn btn-skip" onclick="doSkip()">⏭ Sans recadrage</button>
    <button class="btn btn-ok"   onclick="doConfirm()">✓ Confirmer</button>
  </div>
  <div class="hint">Glissez les 4 coins 🔵 sur les bords du document</div>
  <div id="status"></div>
</div>
<script>
const IW={wd},IH={hd},SX={sx},SY={sy};
const COINS_INIT={json.dumps(cd)};
const cv=document.getElementById('cv');
const ctx=cv.getContext('2d');
cv.width=IW; cv.height=IH;
const img=new Image(); img.src='data:image/jpeg;base64,{b64}';
let coins=COINS_INIT.map(c=>({{x:c[0],y:c[1]}}));
let drag=null;
const R=Math.max(20,Math.min(IW,IH)*.042);
img.onload=()=>draw();

function draw(){{
  ctx.clearRect(0,0,IW,IH); ctx.drawImage(img,0,0);
  const off=new OffscreenCanvas(IW,IH),oc=off.getContext('2d');
  oc.fillStyle='rgba(0,0,0,.55)'; oc.fillRect(0,0,IW,IH);
  oc.globalCompositeOperation='destination-out';
  oc.beginPath(); oc.moveTo(coins[0].x,coins[0].y);
  coins.forEach((c,i)=>{{if(i)oc.lineTo(c.x,c.y)}}); oc.closePath();
  oc.fillStyle='rgba(0,0,0,1)'; oc.fill();
  ctx.drawImage(off,0,0);
  ctx.beginPath(); ctx.moveTo(coins[0].x,coins[0].y);
  coins.forEach((c,i)=>{{if(i)ctx.lineTo(c.x,c.y)}}); ctx.closePath();
  ctx.strokeStyle='#2979ff'; ctx.lineWidth=Math.max(2.5,R*.12); ctx.stroke();
  const lbl=['↖','↗','↘','↙'];
  coins.forEach((c,i)=>{{
    ctx.beginPath(); ctx.arc(c.x,c.y,R+6,0,Math.PI*2);
    ctx.fillStyle='rgba(0,0,0,.25)'; ctx.fill();
    ctx.beginPath(); ctx.arc(c.x,c.y,R,0,Math.PI*2);
    ctx.fillStyle=drag===i?'#82b1ff':'#2979ff'; ctx.fill();
    ctx.strokeStyle='#fff'; ctx.lineWidth=Math.max(2,R*.1); ctx.stroke();
    const s=R*.38;
    ctx.strokeStyle='rgba(255,255,255,.85)'; ctx.lineWidth=Math.max(1.5,R*.08);
    ctx.beginPath(); ctx.moveTo(c.x-s,c.y); ctx.lineTo(c.x+s,c.y); ctx.stroke();
    ctx.beginPath(); ctx.moveTo(c.x,c.y-s); ctx.lineTo(c.x,c.y+s); ctx.stroke();
    ctx.fillStyle='rgba(255,255,255,.7)';
    ctx.font=`bold ${{Math.max(11,R*.45)}}px Segoe UI`;
    ctx.textAlign='center'; ctx.textBaseline='middle';
    ctx.fillText(lbl[i],c.x,c.y);
  }});
}}
function gp(e){{
  const r=cv.getBoundingClientRect(),sx2=IW/r.width,sy2=IH/r.height;
  const s=e.touches?e.touches[0]:e;
  return{{x:Math.max(0,Math.min(IW,(s.clientX-r.left)*sx2)),
          y:Math.max(0,Math.min(IH,(s.clientY-r.top)*sy2))}};
}}
function hit(p){{
  for(let i=0;i<4;i++){{const dx=p.x-coins[i].x,dy=p.y-coins[i].y;if(Math.sqrt(dx*dx+dy*dy)<R*2.2)return i;}}
  return null;
}}
cv.addEventListener('mousedown',e=>{{e.preventDefault();drag=hit(gp(e));draw();}});
cv.addEventListener('touchstart',e=>{{e.preventDefault();drag=hit(gp(e));draw();}},{{passive:false}});
cv.addEventListener('mousemove',e=>{{if(drag===null)return;coins[drag]=gp(e);draw();}});
cv.addEventListener('touchmove',e=>{{e.preventDefault();if(drag===null)return;coins[drag]=gp(e);draw();}},{{passive:false}});
cv.addEventListener('mouseup',()=>{{drag=null;draw();}});
cv.addEventListener('touchend',()=>{{drag=null;draw();}});

function sendRelay(value){{
  document.getElementById('status').textContent='⏳ Traitement en cours...';
  try{{
    const doc=window.parent.document;
    let inp=null;
    for(const el of doc.querySelectorAll('input[type="text"]')){{
      if(el.getAttribute('aria-label')==='_relay_'){{inp=el;break;}}
    }}
    if(!inp){{
      const all=[...doc.querySelectorAll('input[type="text"]')];
      inp=all[all.length-1];
    }}
    if(!inp){{document.getElementById('status').textContent='⚠ Champ introuvable';return;}}
    const setter=Object.getOwnPropertyDescriptor(window.parent.HTMLInputElement.prototype,'value').set;
    setter.call(inp,value);
    inp.dispatchEvent(new Event('input',{{bubbles:true}}));
    inp.dispatchEvent(new KeyboardEvent('keydown',{{key:'Enter',code:'Enter',keyCode:13,which:13,bubbles:true}}));
    inp.dispatchEvent(new KeyboardEvent('keypress',{{key:'Enter',code:'Enter',keyCode:13,which:13,bubbles:true}}));
    inp.dispatchEvent(new KeyboardEvent('keyup',{{key:'Enter',code:'Enter',keyCode:13,which:13,bubbles:true}}));
  }}catch(err){{
    document.getElementById('status').textContent='Erreur: '+err.message;
  }}
}}
function doConfirm(){{
  const result=coins.map(c=>[Math.round(c.x*SX),Math.round(c.y*SY)]);
  sendRelay('CONFIRM:'+JSON.stringify(result));
}}
function doSkip(){{sendRelay('SKIP');}}
</script></body></html>"""

    components.html(html, height=680, scrolling=False)
    return relay_val


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

    # Persister l'image UNE SEULE FOIS en PNG lossless
    if img_b64_key not in st.session_state:
        st.session_state[img_b64_key] = img_to_b64(img_pil)
        st.session_state[nom_key] = nom_pdf

    if state_key not in st.session_state:
        st.session_state[state_key] = "detecting"

    # Recharger depuis la session (résiste aux reruns)
    img_pil = b64_to_img(st.session_state[img_b64_key])
    nom_pdf = st.session_state[nom_key]
    state   = st.session_state[state_key]

    # ── DÉTECTION ──
    if state == "detecting":
        with st.spinner("🔍 Détection du document..."):
            coins = detecter_contour_auto(img_pil)
        st.session_state[corners_key] = coins
        st.session_state[state_key]   = "canvas"
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
                ✂️ Document détecté — ajustez les coins si besoin</div>""", unsafe_allow_html=True)
        else:
            st.markdown('<div class="tip-box">💡 Document non détecté. Placez les coins manuellement.</div>',
                        unsafe_allow_html=True)

        # Choix du mode de rendu
        st.markdown("<div style='font-size:.78rem;color:#7a90b8;margin-bottom:.4rem;'>Mode de rendu :</div>",
                    unsafe_allow_html=True)
        mode = st.radio("Mode", ["🎨 Couleur", "🌫️ Niveaux de gris", "📄 Noir & Blanc"],
                        horizontal=True, key=f"mode_radio_{prefix}_{sk_local}",
                        label_visibility="collapsed")
        mode_map = {"🎨 Couleur": "couleur", "🌫️ Niveaux de gris": "gris", "📄 Noir & Blanc": "nb"}
        st.session_state[mode_key] = mode_map[mode]

        relay_val = canvas_et_relay(img_pil, coins, relay_key, prefix)

        if relay_val:
            if relay_val.startswith("CONFIRM:"):
                try:
                    corners_js = json.loads(relay_val[8:])
                    st.session_state[corners_key] = corners_js
                    st.session_state[badge_key]   = "manual"
                    st.session_state[state_key]   = "result"
                    st.rerun()
                except Exception as e:
                    st.error(f"Erreur recadrage : {e}")
            elif relay_val == "SKIP":
                st.session_state[badge_key] = "none"
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
        components.html("""<style>
        *{box-sizing:border-box;margin:0;padding:0}
        body{background:transparent;font-family:'Segoe UI',sans-serif}
        .card{background:rgba(41,121,255,.07);border:1.5px dashed #2979ff88;border-radius:18px;padding:1.4rem 1rem;margin-bottom:1rem;text-align:center}
        .icon{font-size:3.5rem;display:block;margin-bottom:.5rem;animation:pulse 2s infinite}
        @keyframes pulse{0%,100%{transform:scale(1)}50%{transform:scale(1.08)}}
        .title{font-size:1.05rem;font-weight:700;color:#fff;margin-bottom:.5rem}
        .tip{font-size:.82rem;color:#a0b4d0;margin:.25rem 0}
        .big-btn{display:block;width:100%;background:linear-gradient(135deg,#2979ff,#1a5cd4);
          color:#fff;border:none;border-radius:16px;padding:1.1rem;font-size:1.15rem;font-weight:700;
          cursor:pointer;box-shadow:0 4px 24px rgba(41,121,255,.55);font-family:'Segoe UI',sans-serif;
          -webkit-tap-highlight-color:transparent;margin-bottom:.8rem}
        </style>
        <div class="card">
          <span class="icon">📷</span>
          <div class="title">Photographiez votre document</div>
          <div class="tip">💡 Fond contrasté · ☀️ Bonne lumière · 📐 4 coins visibles</div>
        </div>
        <button class="big-btn" onclick="openCamera()">📷 &nbsp; Ouvrir l'appareil photo</button>
        <script>
        function openCamera(){
          try{const inp=window.parent.document.querySelector('input[type="file"]');
            if(inp){inp.setAttribute('capture','environment');inp.setAttribute('accept','image/*');inp.click();return;}}catch(e){}
          const inp=document.createElement('input');inp.type='file';inp.accept='image/*';
          inp.setAttribute('capture','environment');inp.click();
        }
        </script>""", height=300, scrolling=False)
    else:
        img_mob = corriger_orientation(Image.open(photo))
        flux_image(img_mob, "nova_scan_document.pdf", "mob")

with tab_import:
    st.markdown('<div class="tip-box">💡 <strong>Formats :</strong> JPG, PNG, WEBP, BMP</div>', unsafe_allow_html=True)
    fichier = st.file_uploader(label="Choisir une image", type=["jpg","jpeg","png","webp","bmp"],
                                label_visibility="collapsed", key=f"upload_{sk}")
    if fichier is not None:
        img_imp = corriger_orientation(Image.open(fichier))
        flux_image(img_imp, fichier.name.rsplit(".",1)[0]+".pdf", "imp")

st.markdown("""<hr class="sep"><div style="text-align:center;font-size:.7rem;color:#2e3f5c;">
Nova Scan · Traitement 100 % en mémoire · Aucun fichier stocké</div>""", unsafe_allow_html=True)
