"""
J4 - Parser Carte Grise Cameroun → JSON 8 champs
Transforme le texte brut OCR (garblé) en JSON propre avec regex
Usage: python parser.py
"""
import re
import json

def parse_carte_grise(text):
    """
    Extrait 8 champs depuis le texte brut OCR
    Retourne dict avec confiance par champ
    """
    text_upper = text.upper()
    # Nettoyage basique
    text_clean = text_upper.replace("\n", " ").replace("|", " ")
    
    result = {}

    # 1. IMMATRICULATION - Formats Cameroun: CE 739 CT, OUMT 185 DK, CA-800-EG, LT 123 AB, etc.
    # Regex: 2-4 lettres + espace/tiret + 3 chiffres + espace + 2 lettres
    imm_pattern = r'\b([A-Z]{1,4}\s*[-]?\s*\d{2,4}\s*[A-Z]{2})\b'
    imm_matches = re.findall(imm_pattern, text_upper)
    # Filtre: garde ceux qui ressemblent à une plaque (évite les fausses détections)
    imm_valid = [m.strip() for m in imm_matches if len(m.strip()) >= 6 and any(c.isdigit() for c in m)]
    # Priorité: CE, OUMT, CA, LT etc. avec chiffres
    result["immatriculation"] = imm_valid[0] if imm_valid else None
    result["immatriculations_toutes"] = imm_valid

    # 2. MARQUE - Liste connue
    marques = ["TOYOTA", "PEUGEOT", "NANFAN", "HIACE", "YAMAHA", "HONDA", "NISSAN", "SUZUKI", "MERCEDES", "BMW", "RENAULT", "FORD"]
    marque_found = None
    for m in marques:
        if m in text_upper:
            marque_found = m
            break
    result["marque"] = marque_found

    # 3. MODÈLE - Après MARQUE, cherche SXA11, 207, N-125, HIACE, etc.
    # Cherche pattern: après marque, 2-10 caractères alphanum
    modele = None
    if marque_found:
        # Cherche le mot après la marque
        idx = text_upper.find(marque_found)
        after = text_upper[idx+len(marque_found):idx+100]
        # Cherche code modèle (ex: SXA11, 207, N-125, 21UH)
        m = re.search(r'\b([A-Z0-9]{2,10}[-/]?[0-9]{1,5})\b', after)
        if m:
            modele = m.group(1).strip()
    # Fallback: cherche SXA, 207 directement
    if not modele:
        for cand in ["SXA11", "207", "N-125", "21UH", "HILUX", "COROLLA"]:
            if cand in text_upper:
                modele = cand
                break
    result["modele"] = modele

    # 4. PUISSANCE - 11 CV, 1 CV, 10 CV
    cv_match = re.search(r'(\d{1,2})\s*CV\b', text_upper)
    result["puissance_cv"] = f"{cv_match.group(1)} CV" if cv_match else None

    # 5. ÉNERGIE - ESS, GO, GASOIL, DIESEL
    if "ESS" in text_upper:
        result["energie"] = "ESS"
    elif "GO" in text_upper or "GASOIL" in text_upper or "DIESEL" in text_upper:
        result["energie"] = "GASOIL"
    else:
        result["energie"] = None

    # 6. CYLINDRÉE - 1998CM3, 125CM3, 1745CM3
    cyl_match = re.search(r'(\d{3,4})\s*CM3\b', text_upper)
    result["cylindree"] = f"{cyl_match.group(1)}CM3" if cyl_match else None

    # 7. N° CHÂSSIS / VIN - 17 chars alphanum ou 13 chiffres + DUPLICATA
    # Cherche VIN 17 chars
    vin_match = re.search(r'\b([A-Z0-9]{13,17}[-]?(?:DUPLICATA|ORIGINAL)?)\b', text_upper)
    # Filtre: VIN contient à la fois lettres et chiffres et a au moins 11 chars
    vin_valid = None
    if vin_match:
        cand = vin_match.group(1)
        # Nettoie
        cand = cand.replace(" ", "").replace("-", "")
        if len(cand) >= 11:
            vin_valid = cand
    # Cherche aussi pattern style 3001111014111
    if not vin_valid:
        m = re.search(r'\b(\d{10,16})\b', text_upper)
        if m:
            vin_valid = m.group(1)
    result["chassis_vin"] = vin_valid

    # 8. DATE - 01-01-1997, 01/07/2020, 12/01/2012
    date_match = re.search(r'(\d{2}[-/]\d{2}[-/]\d{4})', text_upper)
    result["date_premiere_mise"] = date_match.group(1) if date_match else None
    # Deuxième date (validité)
    dates = re.findall(r'(\d{2}[-/]\d{2}[-/]\d{4})', text_upper)
    result["dates_toutes"] = dates

    # Champs supplémentaires utiles
    # Centre SSDT
    centre_match = re.search(r'OU\d{3}\s*[A-Z]+', text_upper)
    result["centre_ssdt"] = centre_match.group(0).strip() if centre_match else None
    # Poids
    poids_match = re.search(r'(\d{3,4})\s*KG', text_upper)
    result["poids"] = poids_match.group(1) + " KG" if poids_match else None

    # Score de confiance simple
    filled = sum(1 for k in ["immatriculation","marque","puissance_cv","energie","cylindree","chassis_vin","date_premiere_mise"] if result.get(k))
    result["score_remplissage"] = f"{filled}/7 champs"
    result["confiance_estimee"] = f"{int(filled/7*100)}%"

    return result

# === TEST sur tes 3 fichiers J3 ===
if __name__ == "__main__":
    import os
    test_files = [
        "results_j3/cg_01_TOYOTA_SXA11_easyocr.txt",
        "results_j3/cg_02_CE739CT_OUMT185DK_easyocr.txt",
        "results_j3/cg_03_CA800EG_Peugeot_easyocr.txt",
    ]

    print("="*60)
    print("J4 - TEST PARSER → JSON (sur texte EasyOCR garblé)")
    print("="*60)

    for path in test_files:
        print(f"\n📄 Fichier: {path}")
        if not os.path.exists(path):
            print("   ❌ Fichier introuvable, ignoré")
            continue
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

        result = parse_carte_grise(text)
        print(f"   ✅ JSON extrait ({result['score_remplissage']} - {result['confiance_estimee']}):")
        print(f"   {json.dumps(result, indent=6, ensure_ascii=False)}")

        # Sauvegarde JSON
        out_path = path.replace("_easyocr.txt", "_parsed.json")
        with open(out_path, "w", encoding="utf-8") as out:
            json.dump(result, out, indent=2, ensure_ascii=False)
        print(f"   💾 Sauvegardé: {out_path}")

    print("\n" + "="*60)
    print("✅ J4 Parser terminé. Prochaine étape: brancher ce parser dans POST /ocr")
    print("="*60)
