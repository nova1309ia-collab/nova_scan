import streamlit as st
from PIL import Image
import io
import numpy as np

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

if "scan_key" not in st.session_state:
    st.session_state["scan_key"] = 0
sk = st.session_state["scan_key"]


# ── Détection et recadrage du document ───────────────────────────────────────
def detecter_et_recadrer(img_pil):
    """
    Détecte le document, recadre, redresse et améliore le contraste.
    Retourne (img_result, recadre_bool)
    """
    try:
        import cv2
        img_np = np.array(img_pil.convert("RGB"))
        orig = img_np.copy()
        h, w = img_np.shape[:2]

        # Redimensionner pour traitement rapide
        scale = 800 / max(h, w)
        small = cv2.resize(img_np, (int(w * scale), int(h * scale)))

        # Détection des bords
        gray = cv2.cvtColor(small, cv2.COLOR_RGB2GRAY)
        blur = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blur, 50, 150)
        edges = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=2)

        # Trouver les contours
        contours, _ = cv2.findContours(edges, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:10]

        doc_contour = None
        for c in contours:
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)
            if len(approx) == 4 and cv2.contourArea(c) > (small.shape[0] * small.shape[1] * 0.2):
                doc_contour = approx
                break

        if doc_contour is None:
            return img_pil, False

        # Remettre à l'échelle originale
        pts = (doc_contour.reshape(4, 2) / scale).astype(np.float32)

        # Ordonner les points
        rect = np.zeros((4, 2), dtype=np.float32)
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]

        wA = np.linalg.norm(rect[2] - rect[3])
        wB = np.linalg.norm(rect[1] - rect[0])
        hA = np.linalg.norm(rect[1] - rect[2])
        hB = np.linalg.norm(rect[0] - rect[3])
        maxW = int(max(wA, wB))
        maxH = int(max(hA, hB))

        if maxW < 100 or maxH < 100:
            return img_pil, False

        # Correction de perspective
        dst = np.array([[0, 0], [maxW-1, 0], [maxW-1, maxH-1], [0, maxH-1]], dtype=np.float32)
        M = cv2.getPerspectiveTransform(rect, dst)
        warped = cv2.warpPerspective(orig, M, (maxW, maxH))

        # Amélioration contraste — rendu "scan propre"
        gray2 = cv2.cvtColor(warped, cv2.COLOR_RGB2GRAY)
        clean = cv2.adaptiveThreshold(
            gray2, 255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 21, 10
        )
        result = Image.fromarray(clean).convert("RGB")
        return result, True

    except Exception:
        return img_pil, False


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


# ── Conversion → PDF ──────────────────────────────────────────────────────────
def image_vers_pdf(img):
    img = corriger_orientation(img)
    if img.mode != "RGB":
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="PDF", resolution=150)
    buf.seek(0)
    return buf.getvalue(), img


# ── Affichage résultat ────────────────────────────────────────────────────────
def afficher_resultat(img, nom_fichier, key_dl, key_btn):
    try:
        # Recadrage automatique
        with st.spinner("🔍 Détection du document..."):
            img_traitee, recadree = detecter_et_recadrer(img)

        pdf_bytes, img_rgb = image_vers_pdf(img_traitee)
        w, h = img_rgb.size
        taille_ko = len(pdf_bytes) / 1024
        taille_str = f"{taille_ko/1024:.1f} Mo" if taille_ko >= 1024 else f"{taille_ko:.0f} Ko"

        st.markdown('<div class="steps-row">'
                    '<div class="step-badge">① ✓ Photo prise</div>'
                    '<div class="step-badge">② ✓ PDF généré</div>'
                    '<div class="step-badge step-active">③ Télécharger</div>'
                    '</div>', unsafe_allow_html=True)

        st.markdown('<div class="preview-label">APERÇU DU DOCUMENT</div>', unsafe_allow_html=True)
        st.image(img_rgb, use_container_width=True)

        badge = '<span class="badge-crop">✂️ Recadré automatiquement</span>' if recadree \
                else '<span class="badge-no-crop">⚠️ Recadrage non détecté</span>'

        st.markdown(f"""
        <div class="pdf-info">
            📄 PDF prêt ! {badge}<br>
            Taille : <span>{taille_str}</span> &nbsp;|&nbsp;
            Résolution : <span>{w} × {h} px</span>
        </div>
        """, unsafe_allow_html=True)

        if not recadree:
            st.markdown("""
            <div class="tip-box">
                💡 <strong>Conseil :</strong> Pour un meilleur recadrage, placez le document
                sur un fond contrasté (table sombre ou fond clair) et assurez-vous que
                les 4 coins sont visibles.
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


# ── ONGLETS ───────────────────────────────────────────────────────────────────
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
          * { box-sizing: border-box; margin: 0; padding: 0; }
          body { background: transparent; font-family: 'Segoe UI', sans-serif; }
          .instruction-card {
            background: rgba(41,121,255,0.07);
            border: 1.5px dashed #2979ff88;
            border-radius: 18px;
            padding: 1.4rem 1rem;
            margin-bottom: 1rem;
            text-align: center;
          }
          .instruction-card .icon {
            font-size: 3.5rem;
            display: block;
            margin-bottom: 0.5rem;
            animation: pulse 2s infinite;
          }
          @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.08); }
          }
          .instruction-card .title {
            font-size: 1.05rem;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 0.5rem;
          }
          .tips { text-align: left; display: inline-block; }
          .tip-line {
            font-size: 0.82rem;
            color: #a0b4d0;
            margin: 0.25rem 0;
            display: flex;
            align-items: center;
            gap: 0.4rem;
          }
          .big-btn {
            display: block;
            width: 100%;
            background: linear-gradient(135deg, #2979ff, #1a5cd4);
            color: #fff;
            border: none;
            border-radius: 16px;
            padding: 1.1rem;
            font-size: 1.15rem;
            font-weight: 700;
            letter-spacing: 1px;
            cursor: pointer;
            box-shadow: 0 4px 24px rgba(41,121,255,0.55);
            font-family: 'Segoe UI', sans-serif;
            text-align: center;
            margin-bottom: 0.8rem;
            -webkit-tap-highlight-color: transparent;
            transition: transform 0.1s, opacity 0.1s;
          }
          .big-btn:active { transform: scale(0.97); opacity: 0.9; }
          .auto-badge {
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.4rem;
            background: rgba(0,230,118,0.08);
            border: 1px solid #00e67644;
            border-radius: 10px;
            padding: 0.5rem;
            font-size: 0.75rem;
            color: #00e676;
            margin-bottom: 0.8rem;
          }
          .steps {
            display: flex;
            justify-content: center;
            gap: 0.4rem;
            flex-wrap: wrap;
          }
          .step {
            background: rgba(41,121,255,0.12);
            border: 1px solid #2979ff44;
            border-radius: 20px;
            padding: 4px 12px;
            font-size: 0.7rem;
            color: #7a90b8;
          }
          .step.active {
            background: rgba(41,121,255,0.3);
            border-color: #2979ff;
            color: #fff;
            font-weight: 600;
          }
        </style>

        <div class="instruction-card">
          <span class="icon">📷</span>
          <div class="title">Photographiez votre document</div>
          <div class="tips">
            <div class="tip-line">💡 Posez le document sur un fond contrasté</div>
            <div class="tip-line">☀️ Bonne lumière, sans reflets</div>
            <div class="tip-line">📐 Les 4 coins du document visibles</div>
          </div>
        </div>

        <div class="auto-badge">
          ✂️ Recadrage automatique activé — le document sera détecté et redressé
        </div>

        <button class="big-btn" onclick="openCamera()">
          📷 &nbsp; Ouvrir l'appareil photo
        </button>

        <div class="steps">
          <div class="step active">① Prendre la photo</div>
          <div class="step">② Recadrage auto</div>
          <div class="step">③ Télécharger PDF</div>
        </div>

        <script>
        function openCamera() {
          try {
            const inputs = window.parent.document.querySelectorAll('input[type="file"]');
            for (let inp of inputs) {
              inp.setAttribute('capture', 'environment');
              inp.setAttribute('accept', 'image/*');
              inp.click();
              return;
            }
          } catch(e) {}
          const inp = document.createElement('input');
          inp.type = 'file';
          inp.accept = 'image/*';
          inp.setAttribute('capture', 'environment');
          inp.click();
        }
        </script>
        """, height=370, scrolling=False)

    else:
        img_mob = Image.open(photo)
        afficher_resultat(img_mob, "nova_scan_document.pdf", f"dl_mob_{sk}", f"btn_reset_mob_{sk}")


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
        img_imp = Image.open(fichier)
        nom_pdf = fichier.name.rsplit(".", 1)[0] + ".pdf"
        afficher_resultat(img_imp, nom_pdf, f"dl_import_{sk}", f"btn_reset_import_{sk}")


# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("""
<hr class="sep">
<div style="text-align:center; font-size:0.7rem; color:#2e3f5c;">
    Nova Scan · Module Nova Platform · Traitement 100% en mémoire · Aucun fichier stocké
</div>
""", unsafe_allow_html=True)
