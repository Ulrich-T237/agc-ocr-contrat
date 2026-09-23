"""
J3 - Test OCR Tesseract / EasyOCR (offline, gratuit)
Usage: python test_ocr.py
Teste 3 images de dataset/carte_grise et affiche le texte brut + sauvegarde en .txt
"""
import os
import sys

# Try EasyOCR first, fallback to Tesseract
try:
    import easyocr
    USE_EASYOCR = True
    print("✅ EasyOCR disponible")
except ImportError:
    USE_EASYOCR = False
    print("⚠️ EasyOCR non installé, tentative avec pytesseract...")

if not USE_EASYOCR:
    try:
        import pytesseract
        from PIL import Image
        import cv2
        print("✅ pytesseract disponible")
    except ImportError:
        print("❌ Aucun OCR installé. Lance d'abord:")
        print("   pip install easyocr pillow")
        print("   ou: pip install pytesseract pillow opencv-python")
        sys.exit(1)

# Images à tester (prends les 3 premières de ton dataset)
IMAGES = [
    "dataset/carte_grise/cg_01_TOYOTA_SXA11.png",
    "dataset/carte_grise/cg_02_CE739CT_OUMT185DK.png",
    "dataset/carte_grise/cg_03_CA800EG_Peugeot.png",
]

# Dossier de sortie
os.makedirs("results_j3", exist_ok=True)

def ocr_easyocr(image_path):
    """EasyOCR - simple"""
    reader = easyocr.Reader(['fr', 'en'], gpu=False, verbose=False)
    results = reader.readtext(image_path)
    # results = [(bbox, text, confidence), ...]
    text = "\n".join([r[1] for r in results])
    conf_avg = sum([r[2] for r in results]) / len(results) if results else 0
    return text, conf_avg, len(results)

def ocr_tesseract(image_path):
    """Tesseract - fallback"""
    import cv2
    img = cv2.imread(image_path)
    # Prétraitement simple: grayscale + threshold
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
    # OCR
    text = pytesseract.image_to_string(thresh, lang='fra+eng')
    return text, 0.0, 0

print("\n" + "="*60)
print("J3 - TEST OCR V1 (Offline) - AGC Assurances")
print("="*60)

for img_path in IMAGES:
    print(f"\n📸 Image: {img_path}")
    if not os.path.exists(img_path):
        print(f"   ❌ Fichier introuvable, ignoré")
        continue

    print(f"   ⏳ Lecture en cours...")
    try:
        if USE_EASYOCR:
            text, conf, n = ocr_easyocr(img_path)
        else:
            text, conf, n = ocr_tesseract(img_path)
    except Exception as e:
        print(f"   ❌ Erreur OCR: {e}")
        continue

    print(f"   ✅ {n} blocs détectés | Confiance avg: {conf:.2%}" if USE_EASYOCR else "   ✅ Texte extrait")
    print(f"   --- TEXTE BRUT (premières 400 lettres) ---")
    preview = text[:400].replace("\n", " | ")
    print(f"   {preview}...")
    print(f"   -------------------------------------------")

    # Sauvegarde en .txt
    base = os.path.basename(img_path).replace(".png","").replace(".jpg","")
    out_path = f"results_j3/{base}_tesseract.txt" if not USE_EASYOCR else f"results_j3/{base}_easyocr.txt"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"Image: {img_path}\n")
        f.write(f"OCR: {'EasyOCR' if USE_EASYOCR else 'Tesseract'}\n")
        f.write(f"Confiance: {conf:.2%}\n")
        f.write("="*40 + "\n")
        f.write(text)
    print(f"   💾 Sauvegardé: {out_path}")

    # Comptage rapide des champs trouvés (pour ton tableau)
    keywords = ["TOYOTA", "CE ", "OUMT", "PEUGEOT", "CV", "ESS", "199", "2020", "SXA", "CHASSIS", "VIN"]
    found = [k for k in keywords if k in text.upper()]
    print(f"   🔍 Mots-clés trouvés: {found} ({len(found)}/8 champs)")

print("\n" + "="*60)
print("✅ J3 Matin terminé. Vérifie results_j3/")
print("Prochaine étape: Tester Mindee cet après-midi (13h)")
print("="*60)
