import streamlit as st
from PIL import Image
import img2pdf
import io

# ─── CONFIG PAGE ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Nova Scan",
    page_icon="📄",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ─── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* Globals */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #050d1a;
    color: #e0e8ff;
    font-family: 'Segoe UI', sans-serif;
}

/* Cacher le header Streamlit */
[data-testid="stHeader"] { display: none; }

/* Titre principal */
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

/* Zone caméra */
.guide-box {
    border: 2px dashed #2979ff;
    border-radius: 12px;
    padding: 1rem;
    margin-bottom: 1rem;
    background: rgba(41, 121, 255, 0.04);
}
.guide-text {
    text-align: center;
    font-size: 0.8rem;
    color: #2979ff;
    margin-bottom: 0.6rem;
    font-weight: 600;
    letter-spacing: 0.5px;
}

/* Étapes */
.steps-row {
    display: flex;
    justify-content: center;
    gap: 0.5rem;
    margin-bottom: 1.5rem;
    flex-wrap: wrap;
}
.step-badge {
    background: rgba(41, 121, 255, 0.12);
    border: 1px solid #2979ff44;
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 0.72rem;
    color: #00e5ff;
    white-space: nowrap;
}
.step-active {
    background: rgba(41, 121, 255, 0.3);
    border-color: #2979ff;
    color: #ffffff;
    font-weight: 600;
}

/* Infos PDF */
.pdf-info {
    background: rgba(0, 229, 255, 0.06);
    border: 1px solid rgba(0, 229, 255, 0.2);
    border-radius: 10px;
    padding: 1rem 1.2rem;
    margin: 1rem 0;
    font-size: 0.85rem;
}
.pdf-info span { color: #00e5ff; font-weight: 600; }

/* Bouton download override */
[data-testid="stDownloadButton"] > button {
    background-color: #2979ff !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    padding: 0.75rem 2rem !important;
    width: 100% !important;
    letter-spacing: 1px !important;
}
[data-testid="stDownloadButton"] > button:hover {
    background-color: #1a5cd4 !important;
}

/* Bouton reset */
[data-testid="stButton"] > button {
    background: transparent !important;
    border: 1px solid #2979ff55 !important;
    color: #7a90b8 !important;
    border-radius: 8px !important;
    width: 100% !important;
    margin-top: 0.5rem !important;
}
[data-testid="stButton"] > button:hover {
    border-color: #2979ff !important;
    color: #2979ff !important;
}

/* Aperçu image */
.preview-label {
    font-size: 0.75rem;
    color: #7a90b8;
    text-align: center;
    margin-top: 0.5rem;
    margin-bottom: 0.3rem;
}

/* Séparateur */
.sep {
    border: none;
    border-top: 1px solid #0d1e38;
    margin: 1.5rem 0;
}

/* Tips */
.tip-box {
    background: rgba(255, 193, 7, 0.06);
    border-left: 3px solid #ffc107;
    border-radius: 0 8px 8px 0;
    padding: 0.7rem 1rem;
    font-size: 0.78rem;
    color: #c9a227;
    margin-bottom: 1rem;
}
</style>
""", unsafe_allow_html=True)

# ─── EN-TÊTE ────────────────────────────────────────────────────────────────────
st.markdown('<div class="nova-title">📄 NOVA SCAN</div>', unsafe_allow_html=True)
st.markdown('<div class="nova-subtitle">Numérisation instantanée · Zéro installation</div>', unsafe_allow_html=True)

# ─── ÉTAPES ─────────────────────────────────────────────────────────────────────
photo_prise = "captured_image" in st.session_state and st.session_state["captured_image"] is not None

if not photo_prise:
    st.markdown("""
    <div class="steps-row">
        <div class="step-badge step-active">① Cadrer</div>
        <div class="step-badge">② Capturer</div>
        <div class="step-badge">③ Télécharger</div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="steps-row">
        <div class="step-badge">① Cadré ✓</div>
        <div class="step-badge">② Capturé ✓</div>
        <div class="step-badge step-active">③ Télécharger</div>
    </div>
    """, unsafe_allow_html=True)

# ─── PHASE 1 : CAPTURE ──────────────────────────────────────────────────────────
if not photo_prise:

    st.markdown("""
    <div class="tip-box">
        💡 <strong>Conseil :</strong> Place le document sur une surface foncée et assure-toi que les 4 coins sont visibles dans le cadre.
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="guide-box">
        <div class="guide-text">📐 ALIGNE TON DOCUMENT DANS CE CADRE AVANT DE PRENDRE LA PHOTO</div>
    </div>
    """, unsafe_allow_html=True)

    photo = st.camera_input(
        label="Prendre la photo",
        label_visibility="collapsed",
    )

    if photo is not None:
        st.session_state["captured_image"] = photo
        st.rerun()

# ─── PHASE 2 : CONVERSION + TÉLÉCHARGEMENT ─────────────────────────────────────
else:
    photo = st.session_state["captured_image"]

    # Lecture image
    img_bytes = photo.getvalue()
    image = Image.open(io.BytesIO(img_bytes))

    # Conversion RGB obligatoire (img2pdf n'accepte pas RGBA)
    if image.mode in ("RGBA", "P", "LA"):
        image = image.convert("RGB")

    # Sauvegarder en JPEG en mémoire (qualité 92 = bon équilibre qualité/poids)
    img_buffer = io.BytesIO()
    image.save(img_buffer, format="JPEG", quality=92, optimize=True)
    img_buffer.seek(0)
    jpeg_bytes = img_buffer.read()

    # Conversion PDF en mémoire (zero-disk)
    pdf_bytes = img2pdf.convert(jpeg_bytes)

    # Taille PDF
    taille_ko = len(pdf_bytes) / 1024
    if taille_ko >= 1024:
        taille_str = f"{taille_ko/1024:.1f} Mo"
    else:
        taille_str = f"{taille_ko:.0f} Ko"

    # Dimensions
    largeur_px, hauteur_px = image.size
    dim_str = f"{largeur_px} × {hauteur_px} px"

    # ── Aperçu ────────────────────────────────────────────────────────────────
    st.markdown('<div class="preview-label">APERÇU DU DOCUMENT CAPTURÉ</div>', unsafe_allow_html=True)
    st.image(image, use_container_width=True)

    # ── Infos PDF ─────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="pdf-info">
        📄 PDF généré avec succès<br>
        Taille : <span>{taille_str}</span> &nbsp;|&nbsp;
        Résolution : <span>{dim_str}</span> &nbsp;|&nbsp;
        Format : <span>JPEG → PDF sans perte</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Bouton téléchargement ─────────────────────────────────────────────────
    st.download_button(
        label="⬇️  TÉLÉCHARGER LE PDF",
        data=pdf_bytes,
        file_name="nova_scan_document.pdf",
        mime="application/pdf",
    )

    st.markdown('<hr class="sep">', unsafe_allow_html=True)

    # ── Reset ─────────────────────────────────────────────────────────────────
    if st.button("📷  Scanner un autre document"):
        del st.session_state["captured_image"]
        st.rerun()

# ─── FOOTER ─────────────────────────────────────────────────────────────────────
st.markdown("""
<hr class="sep">
<div style="text-align:center; font-size:0.7rem; color:#2e3f5c;">
    Nova Scan · Module Nova Platform · Traitement 100% en mémoire · Aucun fichier stocké
</div>
""", unsafe_allow_html=True)
