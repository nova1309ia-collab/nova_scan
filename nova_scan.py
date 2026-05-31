import streamlit as st
from PIL import Image
import io

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
[data-testid="stFileUploader"] {
    display: none !important;
}
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

# ── Reset ────────────────────────────────────────────────────────────────────
if st.session_state.get("reset_requested"):
    st.session_state["reset_requested"] = False
    st.session_state["scan_key"] = st.session_state.get("scan_key", 0) + 1

if "scan_key" not in st.session_state:
    st.session_state["scan_key"] = 0
sk = st.session_state["scan_key"]


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


def image_vers_pdf(img):
    img = corriger_orientation(img)
    if img.mode != "RGB":
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="PDF", resolution=150)
    buf.seek(0)
    return buf.getvalue(), img


def afficher_resultat(img, nom_fichier, key_dl, key_btn):
    try:
        pdf_bytes, img_rgb = image_vers_pdf(img)
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

        st.markdown(f"""
        <div class="pdf-info">
            📄 PDF prêt !&nbsp;&nbsp;
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


# ── ONGLETS ───────────────────────────────────────────────────────────────────
tab_mobile, tab_import = st.tabs(["📷  Caméra", "🖼️  Importer"])


# ══════════════════════════════════
# ONGLET 1 — CAMÉRA MOBILE
# ══════════════════════════════════
with tab_mobile:

    photo = st.file_uploader(
        label="photo",
        type=["jpg", "jpeg", "png", "webp", "bmp", "heic"],
        label_visibility="collapsed",
        key=f"cam_{sk}",
    )

    if photo is None:
        # Gros bouton HTML qui trigger directement le file input caché de Streamlit
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
            margin-bottom: 0.3rem;
          }
          .instruction-card .sub {
            font-size: 0.8rem;
            color: #7a90b8;
            line-height: 1.5;
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

          .steps {
            display: flex;
            justify-content: center;
            gap: 0.4rem;
            flex-wrap: wrap;
            margin-top: 0.6rem;
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
          <div class="title">Prenez en photo votre document</div>
          <div class="sub">
            Pointez votre caméra vers le document<br>
            Assurez-vous d'avoir une bonne lumière<br>
            Cadrez bien le document entier
          </div>
        </div>

        <button class="big-btn" onclick="openCamera()">
          📷 &nbsp; Ouvrir l'appareil photo
        </button>

        <div class="steps">
          <div class="step active">① Prendre la photo</div>
          <div class="step">② PDF généré auto</div>
          <div class="step">③ Télécharger</div>
        </div>

        <script>
        function openCamera() {
          // Trouve le vrai input[type=file] de Streamlit dans le parent
          try {
            const inputs = window.parent.document.querySelectorAll('input[type="file"]');
            for (let inp of inputs) {
              inp.setAttribute('capture', 'environment');
              inp.setAttribute('accept', 'image/*');
              inp.click();
              return;
            }
          } catch(e) {}
          // Fallback si cross-origin bloqué : créer un input local
          const inp = document.createElement('input');
          inp.type = 'file';
          inp.accept = 'image/*';
          inp.setAttribute('capture', 'environment');
          inp.onchange = function() {
            alert("Photo prise ! Utilisez le bouton 'Upload' ci-dessus pour l'envoyer.");
          };
          inp.click();
        }
        </script>
        """, height=320, scrolling=False)

    else:
        img_mob = Image.open(photo)
        afficher_resultat(img_mob, "nova_scan_document.pdf", f"dl_mob_{sk}", f"btn_reset_mob_{sk}")


# ══════════════════════════════════
# ONGLET 2 — IMPORT FICHIER
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


st.markdown("""
<hr class="sep">
<div style="text-align:center; font-size:0.7rem; color:#2e3f5c;">
    Nova Scan · Module Nova Platform · Traitement 100% en mémoire · Aucun fichier stocké
</div>
""", unsafe_allow_html=True)
