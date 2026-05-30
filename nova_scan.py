import streamlit as st
from PIL import Image
import img2pdf
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
    font-weight: 600;
    letter-spacing: 0.5px;
}
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
[data-testid="stCameraInputButton"] {
    background-color: #2979ff !important;
    color: #ffffff !important;
    border: none !important;
    border-radius: 50px !important;
    padding: 0.7rem 2.5rem !important;
    font-size: 1rem !important;
    font-weight: 700 !important;
    letter-spacing: 1px !important;
    cursor: pointer !important;
    box-shadow: 0 0 18px rgba(41, 121, 255, 0.45) !important;
    transition: background 0.2s, box-shadow 0.2s !important;
}
[data-testid="stCameraInputButton"]:hover {
    background-color: #1a5cd4 !important;
    box-shadow: 0 0 28px rgba(41, 121, 255, 0.7) !important;
}
[data-testid="stCameraInputButton"]:active {
    background-color: #0f3fa8 !important;
    transform: scale(0.97) !important;
}
.preview-label {
    font-size: 0.75rem;
    color: #7a90b8;
    text-align: center;
    margin-top: 0.5rem;
    margin-bottom: 0.3rem;
}
.sep { border: none; border-top: 1px solid #0d1e38; margin: 1.5rem 0; }
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

st.markdown('<div class="nova-title">📄 NOVA SCAN</div>', unsafe_allow_html=True)
st.markdown('<div class="nova-subtitle">Numérisation instantanée · Zéro installation</div>', unsafe_allow_html=True)

# Reset propre via key rotation
if st.session_state.get("reset_requested"):
    st.session_state["reset_requested"] = False
    st.session_state["scan_key"] = st.session_state.get("scan_key", 0) + 1

if "scan_key" not in st.session_state:
    st.session_state["scan_key"] = 0

sk = st.session_state["scan_key"]

# ─── ONGLETS ────────────────────────────────────────────────────────────────────
tab_cam, tab_import = st.tabs(["📷  Caméra", "🖼️  Importer une photo"])


def afficher_resultat(image, nom_fichier, key_dl, key_btn):
    """Affiche aperçu + infos + bouton download pour une image PIL."""
    if image.mode in ("RGBA", "P", "LA"):
        image = image.convert("RGB")

    img_buf = io.BytesIO()
    image.save(img_buf, format="JPEG", quality=92, optimize=True)
    pdf_bytes = img2pdf.convert(img_buf.getvalue())

    taille_ko = len(pdf_bytes) / 1024
    taille_str = f"{taille_ko/1024:.1f} Mo" if taille_ko >= 1024 else f"{taille_ko:.0f} Ko"
    w, h = image.size

    st.markdown('<div class="preview-label">APERÇU DU DOCUMENT</div>', unsafe_allow_html=True)
    st.image(image, use_container_width=True)

    st.markdown(f"""
    <div class="pdf-info">
        📄 PDF généré avec succès<br>
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

    st.markdown('<hr class="sep">', unsafe_allow_html=True)

    if st.button("🔄  Recommencer", key=key_btn):
        st.session_state["reset_requested"] = True
        st.rerun()


# ══════════════════════════════════════════════════════
# ONGLET 1 — CAMÉRA
# ══════════════════════════════════════════════════════
with tab_cam:
    photo = st.camera_input(
        label="Prendre la photo",
        label_visibility="collapsed",
        key=f"cam_{sk}",
    )

    if photo is None:
        st.markdown("""
        <div class="steps-row">
            <div class="step-badge step-active">① Cadrer</div>
            <div class="step-badge">② Capturer</div>
            <div class="step-badge">③ Télécharger</div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="tip-box">
            💡 <strong>Conseil :</strong> Place le document sur une surface foncée et assure-toi que les 4 coins sont visibles.
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div class="guide-box">
            <div class="guide-text">📐 ALIGNE TON DOCUMENT DANS CE CADRE AVANT DE PRENDRE LA PHOTO</div>
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

        image_cam = Image.open(io.BytesIO(photo.getvalue()))
        afficher_resultat(image_cam, "nova_scan_document.pdf", "dl_cam", "btn_reset_cam")


# ══════════════════════════════════════════════════════
# ONGLET 2 — IMPORT FICHIER
# ══════════════════════════════════════════════════════
with tab_import:
    st.markdown("""
    <div class="tip-box">
        💡 <strong>Formats acceptés :</strong> JPG, PNG, WEBP, BMP — converti automatiquement en PDF haute qualité.
    </div>
    """, unsafe_allow_html=True)

    fichier = st.file_uploader(
        label="Choisir une image",
        type=["jpg", "jpeg", "png", "webp", "bmp"],
        label_visibility="collapsed",
        key=f"upload_{sk}",
    )

    if fichier is not None:
        image_imp = Image.open(fichier)
        nom_pdf = fichier.name.rsplit(".", 1)[0] + ".pdf"
        afficher_resultat(image_imp, nom_pdf, "dl_import", "btn_reset_import")


# ─── FOOTER ─────────────────────────────────────────────────────────────────────
st.markdown("""
<hr class="sep">
<div style="text-align:center; font-size:0.7rem; color:#2e3f5c;">
    Nova Scan · Module Nova Platform · Traitement 100% en mémoire · Aucun fichier stocké
</div>
""", unsafe_allow_html=True)
