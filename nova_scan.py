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
    border-radius: 10px !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    padding: 0.75rem 2rem !important;
    width: 100% !important;
    letter-spacing: 1px !important;
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
    box-shadow: 0 0 18px rgba(41,121,255,0.45) !important;
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
    margin-bottom: 1.5rem;
    flex-wrap: wrap;
}
.step-badge {
    background: rgba(41,121,255,0.12);
    border: 1px solid #2979ff44;
    border-radius: 20px;
    padding: 4px 14px;
    font-size: 0.72rem;
    color: #00e5ff;
    white-space: nowrap;
}
.step-active {
    background: rgba(41,121,255,0.3);
    border-color: #2979ff;
    color: #fff;
    font-weight: 600;
}
.guide-box {
    border: 2px dashed #2979ff;
    border-radius: 12px;
    padding: 1rem;
    margin-bottom: 1rem;
    background: rgba(41,121,255,0.04);
}
.guide-text {
    text-align: center;
    font-size: 0.8rem;
    color: #2979ff;
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


# ── Correction orientation EXIF (photos mobile) ──────────────────────────────
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


# ── Conversion image → PDF bytes (100% Pillow, zéro dépendance externe) ──────
def image_vers_pdf(img):
    """
    Pillow peut sauvegarder directement en PDF depuis la version 2.x.
    C'est la méthode la plus fiable sur Streamlit Cloud.
    img2pdf est évité car il rejette certains JPEG mobiles (profil ICC, DPI, etc.)
    """
    img = corriger_orientation(img)
    # Forcer RGB — PDF Pillow n'accepte pas RGBA/P/LA
    if img.mode != "RGB":
        img = img.convert("RGB")
    buf = io.BytesIO()
    img.save(buf, format="PDF", resolution=150)
    buf.seek(0)
    return buf.getvalue(), img


# ── Affichage résultat ────────────────────────────────────────────────────────
def afficher_resultat(raw_file_or_image, nom_fichier, key_dl, key_btn, is_pil=False):
    try:
        if is_pil:
            img = raw_file_or_image
        else:
            img = Image.open(raw_file_or_image)

        pdf_bytes, img_rgb = image_vers_pdf(img)
        w, h = img_rgb.size
        taille_ko = len(pdf_bytes) / 1024
        taille_str = f"{taille_ko/1024:.1f} Mo" if taille_ko >= 1024 else f"{taille_ko:.0f} Ko"

        st.markdown('<div class="steps-row">'
                    '<div class="step-badge">① ✓</div>'
                    '<div class="step-badge">② ✓</div>'
                    '<div class="step-badge step-active">③ Télécharger</div>'
                    '</div>', unsafe_allow_html=True)

        st.markdown('<div class="preview-label">APERÇU DU DOCUMENT</div>', unsafe_allow_html=True)
        st.image(img_rgb, use_container_width=True)

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

    except Exception as e:
        st.error(f"Erreur lors de la génération du PDF : {e}")

    st.markdown('<hr class="sep">', unsafe_allow_html=True)
    if st.button("🔄  Recommencer", key=key_btn):
        st.session_state["reset_requested"] = True
        st.rerun()


# ── ONGLETS ───────────────────────────────────────────────────────────────────
tab_cam, tab_mobile, tab_import = st.tabs([
    "🖥️ Caméra PC",
    "📱 Mobile",
    "🖼️ Importer"
])


# ══════════════════════════════════
# ONGLET 1 — st.camera_input (PC)
# ══════════════════════════════════
with tab_cam:
    st.markdown("""
    <div class="tip-box">
        💡 Cet onglet utilise la webcam. <strong>Sur PC uniquement.</strong>
        Sur mobile, utilise l'onglet <strong>📱 Mobile</strong>.
    </div>
    """, unsafe_allow_html=True)

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
        <div class="guide-box">
            <div class="guide-text">📐 ALIGNE TON DOCUMENT DANS CE CADRE</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        img_cam = Image.open(io.BytesIO(photo.getvalue()))
        afficher_resultat(img_cam, "nova_scan_document.pdf", "dl_cam", "btn_reset_cam", is_pil=True)


# ══════════════════════════════════
# ONGLET 2 — MOBILE (input natif)
# ══════════════════════════════════
with tab_mobile:
    st.markdown("""
    <div class="tip-box">
        💡 Appuie sur <strong>Parcourir</strong> puis choisis
        <strong>Appareil photo</strong> pour scanner,
        ou sélectionne une photo déjà prise.
    </div>
    """, unsafe_allow_html=True)

    # Sur Android, type="image/*" + pas de list → propose caméra ET galerie
    mob_file = st.file_uploader(
        label="📷  Ouvrir l'appareil photo ou la galerie",
        type=["jpg", "jpeg", "png", "webp", "bmp", "heic", "heif"],
        key=f"mob_{sk}",
    )

    if mob_file is None:
        st.markdown("""
        <div class="steps-row">
            <div class="step-badge step-active">① Prendre / choisir</div>
            <div class="step-badge">② Générer</div>
            <div class="step-badge">③ Télécharger</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        img_mob = Image.open(mob_file)
        afficher_resultat(img_mob, "nova_scan_mobile.pdf", "dl_mob", "btn_reset_mob", is_pil=True)


# ══════════════════════════════════
# ONGLET 3 — IMPORT FICHIER
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
        afficher_resultat(img_imp, nom_pdf, "dl_import", "btn_reset_import", is_pil=True)


# ── FOOTER ────────────────────────────────────────────────────────────────────
st.markdown("""
<hr class="sep">
<div style="text-align:center; font-size:0.7rem; color:#2e3f5c;">
    Nova Scan · Module Nova Platform · Traitement 100% en mémoire · Aucun fichier stocké
</div>
""", unsafe_allow_html=True)
