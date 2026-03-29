"""
CODE2
Serveur Flask - API pour les Agents de Compression d'Images
Système Multi-Agents Intelligent
Lance avec: python server_groq.py
"""

from flask import Flask, request, jsonify
import numpy as np
from PIL import Image
import io
import base64
import os
import logging
from skimage.metrics import structural_similarity as ssim
from skimage.metrics import peak_signal_noise_ratio as psnr
import json
import requests as req
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime
from scipy import ndimage
from scipy.ndimage import convolve
import pytesseract
from pathlib import Path

pytesseract.pytesseract.tesseract_cmd = os.getenv("TESSERACT_PATH", "tesseract")
# ── Import formats POUR AGENT EXECUTEUR ──
try:
    import pillow_heif
    pillow_heif.register_heif_opener()
    HEIF_SUPPORTED = True
except ImportError:
    HEIF_SUPPORTED = False

AVIF_SUPPORTED     = True
JPEG2000_SUPPORTED = True

# ── Logging ──
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

#POUR RAPPORT
BASE_DIR = Path(__file__).resolve().parent

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB


# ============================================================
# UTILITAIRES COMMUNS — utilisées par Agent 5 Rapporteur
# ============================================================

def calculate_mse(original_np, compressed_np):
    return float(np.mean((original_np.astype(np.float64) - compressed_np.astype(np.float64)) ** 2))


def calculate_compression_rate(original_size, compressed_size):
    return round((1 - compressed_size / original_size) * 100, 2)


def quality_ratio(ssim_val, compression_rate):
    return round((ssim_val * 0.6) + (min(compression_rate, 100) / 100 * 0.4), 4)


# ── FIX 1 : interpreter_metrique — gain séparé, libellés plus explicites ──
def interpreter_metrique(psnr_v, ssim_v, mse_v, taux):
    """
    Interprétation textuelle des 4 métriques clés.
    Le 'gain' reflète l'efficacité de compression (indépendant de la qualité visuelle).
    """
    if taux > 50:
        gain_label = "Excellent (>50%)"
    elif taux > 30:
        gain_label = "Bon (30–50%)"
    elif taux > 15:
        gain_label = "Modéré (15–30%) — envisager qualité plus basse"
    else:
        gain_label = "⚠️ Faible (<15%) — format ou qualité à revoir"

    return {
        "psnr": "Très bonne qualité" if psnr_v > 30 else "Qualité moyenne" if psnr_v > 20 else "Faible qualité",
        "ssim": "Structure préservée" if ssim_v > 0.95 else "Légère dégradation" if ssim_v > 0.85 else "Dégradation visible",
        "mse" : "Faible erreur"      if mse_v  < 50  else "Erreur modérée"  if mse_v  < 200 else "Erreur élevée",
        "gain": gain_label
    }


def evaluate_quality(ssim_val: float) -> str:
    """Évalue la qualité visuelle uniquement (basée sur SSIM)."""
    if ssim_val >= 0.95: return "Excellent"
    if ssim_val >= 0.90: return "Bon"
    if ssim_val >= 0.80: return "Acceptable"
    return "Dégradé"


# ── FIX 2 : evaluate_compression_efficiency — nouvel indicateur séparé ──
def evaluate_compression_efficiency(taux: float) -> str:
    """Évalue l'efficacité du gain de compression (indépendant de la qualité visuelle)."""
    if taux > 50:  return "Excellent"
    if taux > 30:  return "Bon"
    if taux > 15:  return "Modéré"
    return "Faible"


def calculate_all_metrics(original_pil, compressed_bytes, original_size):
    """Calcule toutes les métriques de qualité."""
    compressed_size = len(compressed_bytes)
    original_np     = np.array(original_pil.convert('RGB'))
    compressed_pil  = Image.open(io.BytesIO(compressed_bytes)).convert('RGB')
    compressed_np   = np.array(compressed_pil)

    if original_np.shape != compressed_np.shape:
        compressed_np = np.array(
            compressed_pil.resize((original_np.shape[1], original_np.shape[0]))
        )

    psnr_val = float(psnr(original_np, compressed_np))
    ssim_val = float(ssim(original_np, compressed_np, channel_axis=2))
    mse_val  = calculate_mse(original_np, compressed_np)
    tau      = calculate_compression_rate(original_size, compressed_size)
    ratio_qs = quality_ratio(ssim_val, tau)

    return {
        "psnr_db"                    : round(psnr_val, 2),
        "ssim"                       : round(ssim_val, 4),
        "mse"                        : round(mse_val, 4),
        "taux_compression_pct"       : tau,
        "ratio_qualite_taille"       : ratio_qs,
        "original_size_kb"           : round(original_size / 1024, 2),
        "compressed_size_kb"         : round(compressed_size / 1024, 2),
        "compression_ratio"          : round(original_size / compressed_size, 2),
        "space_saved_percent"        : round((1 - compressed_size / original_size) * 100, 1),
        # FIX 3 : deux évaluations distinctes dans les métriques
        "evaluation_qualite"         : evaluate_quality(ssim_val),
        "evaluation_compression"     : evaluate_compression_efficiency(tau),
    }


# ============================================================
# AGENT 1 : ANALYSTE — Sara
# ============================================================

def rgb2gray(I):
    r, g, b = I[:,:,0], I[:,:,1], I[:,:,2]
    return 0.2989 * r + 0.5870 * g + 0.1140 * b

def variance(image):
    m = np.mean(image)
    l, c = image.shape
    return (1/(l*c)) * np.sum((image-m)**2)

def energy(image):
    return float(np.sum(image**2))

def entropy(image):
    hist, _ = np.histogram(image.flatten(), bins=256, range=(0, 256))
    probs = hist / image.size
    probs = probs[probs > 0]
    return round(float(-np.sum(probs * np.log2(probs))), 4)

def contrast(image):
    l, c = image.shape
    cont = 0
    for i in range(l):
        for j in range(c):
            cont += ((i-j)**2) * image[i][j]
    return cont

def homogenity(image):
    l, c = image.shape
    moment = 0
    for i in range(l):
        for j in range(c):
            moment += image[i][j] / (1 + np.abs(i-j))
    return moment

def avg_color(matrice):
    return float(np.mean(matrice))

def hist_rgb(image, bins=256):
    resultats = {}
    canaux = ['rouge', 'vert', 'bleu']
    for i, canal in enumerate(canaux):
        valeurs = image[:,:,i].flatten()
        resultats[canal] = {
            'moyenne':    round(float(np.mean(valeurs)), 2),
            'ecart_type': round(float(np.std(valeurs)), 2),
            'min':        int(np.min(valeurs)),
            'max':        int(np.max(valeurs))
        }
    return resultats

def extraire_metadonnees(chemin, image):
    largeur, hauteur = image.size
    taille_kb = os.path.getsize(chemin) / 1024
    ext = os.path.splitext(chemin)[1].lower()
    format_map = {'.jpg': 'JPEG', '.jpeg': 'JPEG', '.png': 'PNG', '.webp': 'WEBP'}
    return {
        'nom_fichier':   os.path.basename(chemin),
        'largeur':       largeur,
        'hauteur':       hauteur,
        'format':        format_map.get(ext, str(image.format)),
        'extension':     ext,
        'mode':          image.mode,
        'taille_kb':     round(taille_kb, 2),
        'nombre_pixels': largeur * hauteur
    }

def detecter_contours(chemin_image):
    img = Image.open(chemin_image).convert('L')
    img_array = np.array(img, dtype=np.float64)
    sobel_x = np.array([[-1,0,1],[-2,0,2],[-1,0,1]])
    sobel_y = np.array([[-1,-2,-1],[0,0,0],[1,2,1]])
    grad_x = convolve(img_array, sobel_x)
    grad_y = convolve(img_array, sobel_y)
    magnitude = np.sqrt(grad_x**2 + grad_y**2)
    laplacien = np.array([[0,1,0],[1,-4,1],[0,1,0]])
    lap = convolve(img_array, laplacien)
    return {
        'nombre_contours': int(np.sum(magnitude > 100)),
        'nettete':         round(float(np.var(lap)), 2)
    }

def analyser_morphologie(chemin_image):
    img = Image.open(chemin_image).convert('L')
    img_bin = (np.array(img) > 128).astype(np.uint8)
    elem_struct = np.array([[0,1,0],[0,1,1],[0,1,0]], dtype=np.uint8)
    dilatee = ndimage.binary_dilation(img_bin, structure=elem_struct).astype(np.uint8)
    erodee  = ndimage.binary_erosion(img_bin, structure=elem_struct).astype(np.uint8)
    contours_morpho = dilatee - erodee
    pixels_blancs   = int(np.sum(img_bin))
    pixels_contours = int(np.sum(contours_morpho))
    return {
        'pixels_contours_morpho': pixels_contours,
        'ratio_complexite':       round(pixels_contours / (pixels_blancs + 1), 4)
    }

def co_occurence_0(image, level=256):
    co = np.zeros((level, level))
    rows, cols = image.shape
    for i in range(rows):
        for j in range(cols - 1):
            row_val = int(image[i, j])
            col_val = int(image[i, j + 1])
            co[row_val, col_val] += 1
    if np.sum(co) != 0:
        co = co / np.sum(co)
    return co

def co_occurence_90(image, level=256):
    co = np.zeros((level, level), dtype=float)
    l, c = image.shape
    for i in range(1, l):
        for j in range(c):
            rows = int(image[i, j])
            cols = int(image[i-1, j])
            co[rows, cols] += 1
    if np.sum(co) != 0:
        co = co / np.sum(co)
    return co

def glcm_features(glcm):
    i_idx, j_idx = np.meshgrid(
        np.arange(glcm.shape[0]),
        np.arange(glcm.shape[1]),
        indexing='ij'
    )
    contrast_val    = float(np.sum(glcm * (i_idx - j_idx)**2))
    homogeneity_val = float(np.sum(glcm / (1 + np.abs(i_idx - j_idx))))
    energy_val      = float(np.sum(glcm**2))
    g = glcm[glcm > 0]
    entropy_val     = float(-np.sum(g * np.log2(g)))
    return {
        'contrast':    round(contrast_val, 4),
        'homogeneity': round(homogeneity_val, 4),
        'energy':      round(energy_val, 6),
        'entropy':     round(entropy_val, 4)
    }

def analyser_glcm(image_gray):
    img_small = np.clip(image_gray[:80, :80], 0, 255).astype(int)
    if np.std(img_small) < 1:
        return {
            'glcm_0deg':  {'contrast': 0, 'homogeneity': 1, 'energy': 1, 'entropy': 0},
            'glcm_90deg': {'contrast': 0, 'homogeneity': 1, 'energy': 1, 'entropy': 0},
            'note': 'image uniforme'
        }
    glcm_0  = co_occurence_0(img_small, level=256)
    glcm_90 = co_occurence_90(img_small, level=256)
    return {
        'glcm_0deg':  glcm_features(glcm_0),
        'glcm_90deg': glcm_features(glcm_90)
    }

def detecter_type_image(features, histogramme):
    entropy_val = features['entropy']
    couleur_moy = histogramme['couleur_moyenne']
    r, g, b = couleur_moy[0], couleur_moy[1], couleur_moy[2]
    diff_couleurs = abs(r-g) + abs(g-b) + abs(r-b)
    if entropy_val > 6.0 and diff_couleurs > 30:
        return 'photo'
    elif entropy_val < 3.0 and diff_couleurs < 20:
        return 'document'
    elif entropy_val < 4.0 and diff_couleurs > 20:
        return 'graphique'
    else:
        return 'screenshot'

def analyser_ocr(chemin_image):
    try:
        img = Image.open(chemin_image).convert('L')
        texte = pytesseract.image_to_string(img, lang='fra+eng')
        texte = texte.strip()
        mots = [m for m in texte.split() if len(m) > 1]
        return {
            'contient_texte': len(mots) > 5,
            'nombre_mots':    len(mots),
            'texte_extrait':  texte[:200] if texte else ''
        }
    except Exception as e:
        return {
            'contient_texte': False,
            'nombre_mots':    0,
            'texte_extrait':  f'Erreur OCR: {str(e)}'
        }

def agent_analyste(chemin_image):
    image     = Image.open(chemin_image)
    image_rgb = image.convert('RGB')
    img_array = np.array(image_rgb)
    img_gray  = rgb2gray(img_array)
    img_small = img_gray[:50, :50]
    metadonnees = extraire_metadonnees(chemin_image, image)
    features = {
        'variance':   round(float(variance(img_gray)), 4),
        'energy':     round(float(energy(img_gray)), 4),
        'entropy':    round(float(entropy(img_gray)), 4),
        'contrast':   round(float(contrast(img_small)), 4),
        'homogenity': round(float(homogenity(img_small)), 4)
    }
    histogramme = hist_rgb(img_array)
    histogramme['couleur_moyenne'] = [
        round(avg_color(img_array[:,:,0]), 2),
        round(avg_color(img_array[:,:,1]), 2),
        round(avg_color(img_array[:,:,2]), 2)
    ]
    contours    = detecter_contours(chemin_image)
    morphologie = analyser_morphologie(chemin_image)
    glcm        = analyser_glcm(img_gray)
    type_image  = detecter_type_image(features, histogramme)
    ocr         = analyser_ocr(chemin_image)
    return {
        'image':                 chemin_image,
        'type_image':            type_image,
        'metadonnees':           metadonnees,
        'features_statistiques': features,
        'histogramme_rgb':       histogramme,
        'contours':              contours,
        'morphologie':           morphologie,
        'glcm':                  glcm,
        'ocr':                   ocr
    }


@app.route('/agent/analyste', methods=['POST'])
def route_analyste():
    try:
        data = request.json
        if 'image_path' in data:
            chemin_image = data['image_path']
        elif 'image_base64' in data:
            import tempfile
            img_bytes = base64.b64decode(data['image_base64'])
            img_pil_tmp = Image.open(io.BytesIO(img_bytes))
            suffix = '.' + (img_pil_tmp.format or 'PNG').lower()
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                tmp.write(img_bytes)
                chemin_image = tmp.name
        else:
            return jsonify({"error": "Fournir image_path ou image_base64"}), 400

        resultat = agent_analyste(chemin_image)
        return jsonify({"status": "success", "agent": "Analyste", "features": resultat})

    except Exception as e:
        logger.error(f"[Analyste] {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================
# AGENT 4 : EXÉCUTEUR — Zayneb
# ============================================================
import base64
import io
from PIL import Image, ImageOps
def agent_executeur(chemin_source, format_cible, qualite=70):
    try:
        if not os.path.exists(chemin_source):
            return {"statut": "erreur", "message": "Fichier source introuvable"}

        img = Image.open(chemin_source)
        dossier_sortie = BASE_DIR / "output_images"
        dossier_sortie.mkdir(exist_ok=True)


        if not os.path.exists(dossier_sortie):
            os.makedirs(dossier_sortie)

        nom_base     = os.path.splitext(os.path.basename(chemin_source))[0]
        ext          = format_cible.lower()
        chemin_final = dossier_sortie / f"{nom_base}_compresse.{ext}"
        fmt_upper    = format_cible.upper()

        if fmt_upper == "JPEG":
            img.convert("RGB").save(chemin_final, "JPEG", quality=qualite, optimize=True)
        elif fmt_upper == "PNG":
            img.save(chemin_final, "PNG", optimize=True)
        elif fmt_upper == "WEBP":
            img.save(chemin_final, "WEBP", quality=qualite)
        elif fmt_upper == "AVIF":
            img.save(chemin_final, "AVIF", quality=qualite)
        elif fmt_upper == "HEIF":
            img.save(chemin_final, "HEIF", quality=qualite)
        else:
            return {"statut": "erreur", "message": f"Format {format_cible} non supporté"}

        return {
            "statut"         : "success",
            "format_utilise" : fmt_upper,
            "chemin_resultat": os.path.abspath(chemin_final),
            "taille_ko"      : round(os.path.getsize(chemin_final) / 1024, 2)
        }

    except Exception as e:
        return {"statut": "erreur", "message": str(e)}


@app.route('/agent/executeur', methods=['POST'])
def route_executeur():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Body JSON vide"}), 400

        if 'image_base64' in data and data['image_base64']:
            # ✅ base64 prioritaire
            img_bytes = base64.b64decode(data['image_base64'])
            img = Image.open(io.BytesIO(img_bytes))
            img = ImageOps.exif_transpose(img)
            img = img.convert("RGB")
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
                tmp_path = tmp.name
            img.save(tmp_path)
            chemin_source = tmp_path

        elif 'image_path' in data and data['image_path']:
            # ✅ path seulement si non vide
            chemin_source = data['image_path']
            if not os.path.exists(chemin_source):
                return jsonify({"error": f"Fichier introuvable : {chemin_source}"}), 400

        else:
            return jsonify({"error": "Fournir image_base64 (non vide) ou image_path (non vide)"}), 400

        format_cible = data.get('format', 'WEBP')
        qualite      = int(data.get('quality', 85))

        resultat = agent_executeur(chemin_source, format_cible, qualite)

        if resultat.get("statut") != "success":
            return jsonify({"error": resultat.get("message")}), 500

        chemin_final = resultat["chemin_resultat"]

        with open(chemin_final, 'rb') as f:
            comp_bytes = f.read()

        with open(chemin_source, 'rb') as f:
            orig_bytes = f.read()

        return jsonify({
            "status": "success",
            "agent": "Exécuteur — Zayneb",
            "compressed_image_base64": base64.b64encode(comp_bytes).decode('utf-8'),
            "original_image_base64": base64.b64encode(orig_bytes).decode('utf-8'),
            "chemin_resultat": chemin_final,
            "original_size_kb": round(os.path.getsize(chemin_source) / 1024, 2),
            "compressed_size_kb": resultat["taille_ko"],
            "format_used": resultat["format_utilise"],
            "quality_used": qualite,
            "retry_count": 0,
            "quality_adjusted": False,
            "note_metriques": "SSIM, PSNR et MSE sont calculés par l'Agent Rapporteur"
        })

    except Exception as e:
        logger.error(f"[Exécuteur] {e}")
        return jsonify({"error": str(e)}), 500


# ============================================================
# AGENT 5 : RAPPORTEUR — Ghaouta Bassma
# ============================================================

from pathlib import Path

BASSMA_RAPPORTS_DIR = BASE_DIR / "rapports"
BASSMA_RAPPORTS_DIR.mkdir(parents=True, exist_ok=True)


@app.route('/agent/rapporteur', methods=['POST'])
def agent_rapporteur():
    try:
        bassma_data = request.json
        if not bassma_data:
            return jsonify({"error": "Body JSON vide"}), 400

        bassma_features   = bassma_data.get('features', {})
        bassma_decision   = bassma_data.get('llm_decision', {})
        bassma_strategies = bassma_data.get('strategies', {})
        bassma_nom_image  = bassma_data.get('nom_image', f"image_{datetime.now().strftime('%H%M%S')}")

        bassma_compressed_b64 = bassma_data.get('compressed_b64', '')
        bassma_original_b64   = bassma_data.get('original_b64', '')
        bassma_format_used    = bassma_data.get('format_used', bassma_decision.get('format_choisi', 'WEBP'))
        bassma_quality_used   = bassma_data.get('quality_used', 85)
        bassma_retry_count    = bassma_data.get('retry_count', 0)
        bassma_quality_adj    = bassma_data.get('quality_adjusted', False)

        # FIX 5 : C'est ICI que SSIM, PSNR, MSE sont calculés (pas dans l'exécuteur)
        if bassma_compressed_b64 and bassma_original_b64:
            orig_bytes     = base64.b64decode(bassma_original_b64)
            comp_bytes     = base64.b64decode(bassma_compressed_b64)
            orig_pil       = Image.open(io.BytesIO(orig_bytes))
            orig_size      = len(orig_bytes)
            bassma_metrics = calculate_all_metrics(orig_pil, comp_bytes, orig_size)
            bassma_metrics['format_used']      = bassma_format_used
            bassma_metrics['quality_used']     = bassma_quality_used
            bassma_metrics['retry_count']      = bassma_retry_count
            bassma_metrics['quality_adjusted'] = bassma_quality_adj
        else:
            bassma_metrics = bassma_data.get('metrics', {})

        bassma_ssim_val = float(bassma_metrics.get('ssim', 0))
        bassma_psnr_val = float(bassma_metrics.get('psnr_db', 0))
        bassma_mse_val  = float(bassma_metrics.get('mse', 0))
        bassma_tau      = float(bassma_metrics.get('taux_compression_pct', 0))
        bassma_ratio_qs = float(bassma_metrics.get('ratio_qualite_taille', 0))

        # FIX 6 : Deux évaluations distinctes — qualité visuelle ET efficacité compression
        bassma_evaluation_qualite      = evaluate_quality(bassma_ssim_val)
        bassma_evaluation_compression  = evaluate_compression_efficiency(bassma_tau)

        # Couleur basée sur la qualité visuelle (SSIM)
        if bassma_ssim_val >= 0.95:   bassma_color = "#2ecc71"
        elif bassma_ssim_val >= 0.90: bassma_color = "#27ae60"
        elif bassma_ssim_val >= 0.80: bassma_color = "#f39c12"
        else:                         bassma_color = "#e74c3c"

        bassma_image_type    = bassma_features.get('type_image', bassma_features.get('image_type', ''))
        bassma_format_choisi = bassma_decision.get('format_choisi', bassma_decision.get('format', '')).upper()

        bassma_regles = {
            'document_texte'     : ['PNG'],
            'image_simple_logo'  : ['PNG', 'WEBP'],
            'photo_complexe'     : ['JPEG', 'WEBP'],
            'photo_standard'     : ['JPEG', 'WEBP'],
            'photo'              : ['JPEG', 'WEBP'],
            'graphique_diagramme': ['PNG', 'WEBP'],
            'graphique'          : ['PNG', 'WEBP'],
            'screenshot'         : ['PNG', 'WEBP'],
            'document'           : ['PNG'],
        }
        bassma_ia_pertinente = bassma_format_choisi in bassma_regles.get(bassma_image_type, [])

        bassma_resolution = {
            "width" : bassma_features.get('metadonnees', {}).get('largeur', 0),
            "height": bassma_features.get('metadonnees', {}).get('hauteur', 0)
        }
        bassma_recommandations = {
            'document_texte'   : 'PNG sans perte (préserve le texte)',
            'screenshot'       : 'PNG ou WebP sans perte (conserve les détails)',
            'photo'            : 'JPEG qualité 85-90 (bon compromis)',
            'graphique'        : 'PNG ou WebP (préserve les lignes)',
            'photo_complexe'   : 'JPEG qualité 85 (bon pour paysages)',
            'photo_standard'   : 'WebP qualité 85 (moderne)',
            'image_simple_logo': 'PNG (sans perte)'
        }
        bassma_reco              = bassma_recommandations.get(bassma_image_type, 'WebP qualité 85')
        bassma_pertinence_niveau = "Élevée" if bassma_ia_pertinente else "Moyenne" if bassma_format_choisi in ['WEBP','JPEG'] else "Faible"

        bassma_stem       = Path(bassma_nom_image).stem
        bassma_ts         = datetime.now().strftime("%Y%m%d_%H%M%S")
        bassma_report_dir = BASSMA_RAPPORTS_DIR / f"{bassma_stem}_{bassma_ts}"
        bassma_report_dir.mkdir(parents=True, exist_ok=True)
        bassma_paths = {}

        # ── Graphique SSIM + Taux compression ──
        bassma_valides = {k: v for k, v in bassma_strategies.items()
                          if 'error' not in v} if bassma_strategies else {}
        if bassma_valides:
            bassma_labels = list(bassma_valides.keys())
            bassma_ssims  = [bassma_valides[k].get('ssim', 0)                 for k in bassma_labels]
            bassma_taux   = [bassma_valides[k].get('taux_compression_pct', 0) for k in bassma_labels]
        else:
            bassma_labels = [bassma_metrics.get('format_used', 'Résultat')]
            bassma_ssims  = [bassma_ssim_val]
            bassma_taux   = [bassma_tau]

        bassma_colors_bars = []
        for bassma_s in bassma_ssims:
            if bassma_s >= 0.95:   bassma_colors_bars.append("#2ecc71")
            elif bassma_s >= 0.90: bassma_colors_bars.append("#27ae60")
            elif bassma_s >= 0.80: bassma_colors_bars.append("#f39c12")
            else:                  bassma_colors_bars.append("#e74c3c")

        bassma_fig_chart, bassma_axes_chart = plt.subplots(1, 2, figsize=(9, 3.4), facecolor="#0d1117")
        bassma_fig_chart.suptitle("Comparaison des stratégies", color="white", fontsize=11)

        bassma_ax1 = bassma_axes_chart[0]
        bassma_ax1.set_facecolor("#161b22")
        bassma_bars1 = bassma_ax1.bar(bassma_labels, bassma_ssims,
                                      color=bassma_colors_bars, width=0.5, edgecolor="#0d1117")
        bassma_ax1.set_ylim(0, 1.05)
        bassma_ax1.axhline(0.95, color="#2ecc71", linestyle="--", linewidth=0.8, alpha=0.6)
        bassma_ax1.axhline(0.90, color="#f39c12", linestyle="--", linewidth=0.8, alpha=0.6)
        bassma_ax1.set_title("SSIM (Qualité visuelle)", color="white", fontsize=9)
        bassma_ax1.tick_params(colors="#8892a4", labelsize=7)
        for bassma_spine in bassma_ax1.spines.values():
            bassma_spine.set_edgecolor("#2c3e50")
        for bassma_bar, bassma_v in zip(bassma_bars1, bassma_ssims):
            bassma_ax1.text(bassma_bar.get_x() + bassma_bar.get_width() / 2,
                            bassma_bar.get_height() + 0.01,
                            f"{bassma_v:.3f}", ha='center', fontsize=7, color="white")
        bassma_ax1.set_xticklabels(bassma_labels, rotation=25, ha='right')

        bassma_ax2 = bassma_axes_chart[1]
        bassma_ax2.set_facecolor("#161b22")
        bassma_bars2 = bassma_ax2.bar(bassma_labels, bassma_taux,
                                      color="#3498db", width=0.5, edgecolor="#0d1117")
        bassma_ax2.set_ylim(0, max(bassma_taux) * 1.3 + 5 if bassma_taux else 100)
        bassma_ax2.set_title("Taux de compression τ (%)", color="white", fontsize=9)
        bassma_ax2.tick_params(colors="#8892a4", labelsize=7)
        for bassma_spine in bassma_ax2.spines.values():
            bassma_spine.set_edgecolor("#2c3e50")
        for bassma_bar, bassma_v in zip(bassma_bars2, bassma_taux):
            bassma_ax2.text(bassma_bar.get_x() + bassma_bar.get_width() / 2,
                            bassma_bar.get_height() + 0.4,
                            f"{bassma_v:.1f}%", ha='center', fontsize=7, color="white")
        bassma_ax2.set_xticklabels(bassma_labels, rotation=25, ha='right')

        bassma_fig_chart.patch.set_facecolor("#0d1117")
        bassma_fig_chart.tight_layout(pad=0.8)
        bassma_chart_path = bassma_report_dir / "metrics_chart.png"
        bassma_fig_chart.savefig(bassma_chart_path, dpi=120, bbox_inches='tight',
                                 facecolor="#0d1117", edgecolor='none')
        plt.close(bassma_fig_chart)
        bassma_paths['metrics_chart'] = str(bassma_chart_path)

        if bassma_compressed_b64:
            bassma_ext_map = {"JPEG":"jpg","PNG":"png","WEBP":"webp","AVIF":"avif","HEIF":"heif","JPEG2000":"jp2"}
            bassma_ext     = bassma_ext_map.get(bassma_format_used.upper(), "webp")
            bassma_img_out = bassma_report_dir / f"{bassma_stem}_compressed.{bassma_ext}"
            bassma_img_out.write_bytes(base64.b64decode(bassma_compressed_b64))
            bassma_paths['compressed_image'] = str(bassma_img_out)

        # FIX 7 : Rapport JSON — deux champs évaluation distincts
        bassma_rapport = {
            "rapport_compression": {
                "image_originale": {
                    "nom_image"       : bassma_nom_image,
                    "resolution"      : f"{bassma_resolution['width']}x{bassma_resolution['height']}",
                    "taille_ko"       : bassma_features.get('metadonnees', {}).get('taille_kb', 0),
                    "type_detecte"    : bassma_image_type,
                    "format_original" : bassma_features.get('metadonnees', {}).get('format', 'inconnu'),
                    "entropie"        : bassma_features.get('features_statistiques', {}).get('entropy', 0),
                    "densite_contours": bassma_features.get('contours', {}).get('nombre_contours', 0),
                    "contient_texte"  : bassma_features.get('ocr', {}).get('contient_texte', False)
                },
                "decision_ia": {
                    "format_choisi"      : bassma_format_choisi,
                    "qualite_choisie"    : bassma_decision.get('qualite', bassma_decision.get('quality', 'N/A')),
                    "justification"      : bassma_decision.get('raison', bassma_decision.get('justification', '—')),
                    "source"             : bassma_decision.get('methode_selection', bassma_decision.get('source', '—')),
                    "decision_pertinente": bassma_ia_pertinente,
                    "niveau_pertinence"  : bassma_pertinence_niveau
                },
                "metriques_qualite": {
                    "1_psnr_db"                  : round(bassma_psnr_val, 2),
                    "2_ssim"                      : round(bassma_ssim_val, 4),
                    "3_mse"                       : round(bassma_mse_val, 4),
                    "4_taux_compression_pct"      : round(bassma_tau, 2),
                    "5_ratio_qualite_taille"      : round(bassma_ratio_qs, 4),
                    # FIX : deux évaluations séparées
                    "evaluation_qualite_visuelle" : bassma_evaluation_qualite,
                    "evaluation_efficacite_compression": bassma_evaluation_compression,
                    "interpretation"              : interpreter_metrique(
                        bassma_psnr_val, bassma_ssim_val, bassma_mse_val, bassma_tau
                    )
                },
                "compression_appliquee": {
                    "taille_originale_ko" : bassma_metrics.get('original_size_kb', 0),
                    "taille_compressee_ko": bassma_metrics.get('compressed_size_kb', 0),
                    "ratio_compression"   : bassma_metrics.get('compression_ratio', 0),
                    "gain_pourcentage"    : round(bassma_tau, 2),
                    "format_utilise"      : bassma_format_used,
                    "qualite_utilisee"    : bassma_quality_used,
                    "qualite_ajustee"     : bassma_quality_adj,
                    "nb_retries"          : bassma_retry_count
                },
                "analyse_categorie": {
                    "type"                    : bassma_image_type,
                    "recommandation_theorique": bassma_reco,
                    "recommandation_appliquee": f"{bassma_format_choisi} q={bassma_decision.get('qualite', bassma_decision.get('quality', 'N/A'))}",
                    "pertinence"              : bassma_pertinence_niveau,
                    "respecte_recommandation" : bassma_ia_pertinente
                },
                "fichiers_generes": bassma_paths,
                # FIX 8 : Conclusion distingue qualité visuelle ET gain de compression
                "conclusion": (
                    f"Qualité visuelle : {bassma_evaluation_qualite} (SSIM={bassma_ssim_val:.4f}, PSNR={bassma_psnr_val:.2f} dB, MSE={bassma_mse_val:.2f}). "
                    f"Efficacité compression : {bassma_evaluation_compression} — {bassma_tau:.1f}% économisé"
                    + (" ⚠️ Gain faible : envisager une qualité plus basse pour améliorer la réduction." if bassma_tau < 20 else ".")
                    + f" Décision IA {bassma_pertinence_niveau.lower()} — {'✓ pertinente' if bassma_ia_pertinente else '✗ à revoir'}."
                    + (f" Qualité ajustée après {bassma_retry_count} retry(s)." if bassma_quality_adj else "")
                ),
                "date_analyse": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        }

        bassma_json_path = bassma_report_dir / f"{bassma_stem}_rapport.json"
        with open(bassma_json_path, "w", encoding="utf-8") as bassma_f:
            json.dump(bassma_rapport, bassma_f, indent=2, ensure_ascii=False)
        bassma_paths['rapport_json'] = str(bassma_json_path)

        logger.info(
            f"[Rapporteur — Bassma] Qualité={bassma_evaluation_qualite} "
            f"Compression={bassma_evaluation_compression} "
            f"τ={bassma_tau:.1f}% SSIM={bassma_ssim_val:.4f}"
        )

        return jsonify({
            "status"     : "success",
            "agent"      : "Rapporteur — Ghaouta Bassma",
            "rapport"    : bassma_rapport,
            "fichiers"   : bassma_paths,
            "rapport_dir": str(bassma_report_dir),
            "metrics"    : bassma_metrics
        })

    except Exception as bassma_err:
        logger.error(f"[Rapporteur — Bassma] {bassma_err}")
        return jsonify({"error": str(bassma_err)}), 500


# ============================================================
# HEALTH CHECK
# ============================================================
@app.route('/health', methods=['GET'])
def health():
    return jsonify({
        "status"           : "running",
        "formats_supportes": ["JPEG", "PNG", "WEBP", "AVIF", "JPEG2000"] + (["HEIF"] if HEIF_SUPPORTED else []),
        "metriques"        : ["PSNR", "SSIM", "MSE", "Taux_compression", "Ratio_qualite_taille"],
        "endpoints": {
            "analyste"   : "POST /agent/analyste",
            "decideur"   : "POST /agent/decideur",
            "comparateur": "POST /agent/comparateur",
            "executeur"  : "POST /agent/executeur",
            "rapporteur" : "POST /agent/rapporteur",
            "pipeline"   : "POST /run-all",
            "statut"     : "GET  /run-all/status",
            "liste"      : "GET  /run-all/list"
        }
    })


# ============================================================
# ROUTE PIPELINE COMPLET
# ============================================================
import threading
import glob

pipeline_status = {"running": False, "total": 0, "done": 0, "resultats": []}


@app.route('/run-all', methods=['POST'])
def run_all_images():
    if pipeline_status["running"]:
        return jsonify({"status": "already_running", "done": pipeline_status["done"], "total": pipeline_status["total"]})
    data    = request.json or {}
    dossier = str(BASE_DIR / "database-projet")
    thread  = threading.Thread(target=_run_pipeline_thread, args=(dossier,))
    thread.daemon = True
    thread.start()
    return jsonify({"status": "started", "message": "Pipeline lancé sur toutes les images"})


@app.route('/run-all/status', methods=['GET'])
def run_all_status():
    return jsonify(pipeline_status)


@app.route('/run-all/list', methods=['GET'])
def list_images():
    dossier = str(BASE_DIR / "database-projet")
    extensions = ['jpg','jpeg','png','bmp','webp','tiff']
    images     = []
    for ext in extensions:
        images += glob.glob(os.path.join(dossier, '**', f'*.{ext}'), recursive=True)
        images += glob.glob(os.path.join(dossier, '**', f'*.{ext.upper()}'), recursive=True)
    return jsonify({
        "total" : len(images),
        "images": [{"image_path": p, "nom": os.path.basename(p),
                    "categorie": os.path.basename(os.path.dirname(p))} for p in images]
    })


def _run_pipeline_thread(dossier):
    import time

    pipeline_status["running"]   = True
    pipeline_status["done"]      = 0
    pipeline_status["resultats"] = []

    extensions = ['jpg','jpeg','png','bmp','webp','tiff']
    images = []
    for ext in extensions:
        images += glob.glob(os.path.join(dossier, '**', f'*.{ext}'), recursive=True)
        images += glob.glob(os.path.join(dossier, '**', f'*.{ext.upper()}'), recursive=True)

    pipeline_status["total"] = len(images)
    logger.info(f"[run-all] {len(images)} images trouvées")

    BASE = "http://127.0.0.1:5000"
    RAPPORTS_DIR = BASE_DIR / "rapports"
    RAPPORTS_DIR.mkdir(parents=True, exist_ok=True)

    def call(endpoint, payload, timeout=120):
        try:
            r = req.post(f"{BASE}/{endpoint}", json=payload, timeout=timeout)
            return r.json()
        except Exception as e:
            return {"error": str(e)}

    for img_path in images:
        nom       = os.path.basename(img_path)
        categorie = os.path.basename(os.path.dirname(img_path))
        logger.info(f"[run-all] Traitement : {nom}")

        try:
            # Étape 1 : Analyste
            r1 = call("agent/analyste", {"image_path": img_path})
            if "error" in r1:
                raise Exception(r1["error"])
            features = r1.get("features", {})

            # Étape 2 : Décideur
            r2 = call("agent/decideur", {"features": features})
            if "erreur" in r2:
                raise Exception(r2["erreur"])
            decision = r2

            # Étape 3 : Comparateur
            rc = call("agent/comparateur", {"features": features}, timeout=180)
            if "erreur" not in rc and rc.get("decision_finale"):
                decision_finale  = rc["decision_finale"]
                decision_changee = (decision_finale.get("format_choisi") != decision.get("format_choisi"))
            else:
                decision_finale  = decision
                decision_changee = False

            fmt  = decision_finale.get("format_choisi", "WEBP").upper()
            qual = int(decision_finale.get("qualite", 85))

            # Étape 4 : Exécuteur
            r3 = call("agent/executeur", {
                "image_path": img_path,
                "format"    : fmt,
                "quality"   : qual
            }, timeout=180)
            if "error" in r3:
                raise Exception(r3["error"])

            # Étape 5 : Rapporteur — calcule SSIM/PSNR/MSE ici
            r4 = call("agent/rapporteur", {
                "features"        : features,
                "llm_decision"    : decision_finale,
                "compressed_b64"  : r3.get("compressed_image_base64", ""),
                "original_b64"    : r3.get("original_image_base64", ""),
                "format_used"     : r3.get("format_used", fmt),
                "quality_used"    : r3.get("quality_used", qual),
                "retry_count"     : r3.get("retry_count", 0),
                "quality_adjusted": r3.get("quality_adjusted", False),
                "nom_image"       : nom,
                "categorie"       : categorie
            })

            # FIX 9 : Métriques viennent du Rapporteur, pas de l'Exécuteur
            metrics = r4.get("metrics", {})

            resultat = {
                "image"            : nom,
                "categorie"        : categorie,
                "type_detecte"     : features.get("type_image", "?"),
                "decision_initiale": decision.get("format_choisi", "?"),
                "decision_finale"  : fmt,
                "decision_changee" : decision_changee,
                "source_decision"  : decision_finale.get("methode_selection", "?"),
                "ssim"             : metrics.get("ssim", "?"),
                "psnr_db"          : metrics.get("psnr_db", "?"),
                "mse"              : metrics.get("mse", "?"),
                "tau"              : metrics.get("taux_compression_pct", "?"),
                # FIX : deux évaluations dans le résumé global
                "evaluation_qualite"     : metrics.get("evaluation_qualite", "?"),
                "evaluation_compression" : metrics.get("evaluation_compression", "?"),
                "statut"           : "✅"
            }

            path_r = RAPPORTS_DIR / f"{nom}_rapport.json"
            with open(path_r, 'w', encoding='utf-8') as f:
                json.dump({
                    "image"    : nom,
                    "analyse"  : features,
                    "decision" : decision_finale,
                    "metriques": metrics,
                    "rapport"  : r4.get("rapport", {})
                }, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"[run-all] Erreur {nom}: {e}")
            resultat = {"image": nom, "categorie": categorie, "statut": "❌", "erreur": str(e)}

        pipeline_status["resultats"].append(resultat)
        pipeline_status["done"] += 1

        resume = {
            "total"    : pipeline_status["total"],
            "succes"   : sum(1 for r in pipeline_status["resultats"] if r.get("statut") == "✅"),
            "erreurs"  : sum(1 for r in pipeline_status["resultats"] if r.get("statut") == "❌"),
            "resultats": pipeline_status["resultats"]
        }
        with open(os.path.join(RAPPORTS_DIR, "resume_global.json"), 'w', encoding='utf-8') as f:
            json.dump(resume, f, indent=2, ensure_ascii=False)

        time.sleep(0.2)

    pipeline_status["running"] = False
    logger.info(f"[run-all] Terminé — {pipeline_status['done']} images traitées")


# ============================================================
# DÉMARRAGE
# ============================================================
if __name__ == '__main__':
    print("=" * 60)
    print("  Serveur Multi-Agents - Compression d'Images")
    print(f"  HEIF     : {'✅' if HEIF_SUPPORTED else '❌ (pip install pillow-heif)'}")
    print(f"  AVIF     : ✅")
    print(f"  JPEG2000 : ✅")
    print("  URL      : http://localhost:5000")
    print("  Test     : http://localhost:5000/health")
    print("=" * 60)
    app.run(host='0.0.0.0', port=5000, debug=True)