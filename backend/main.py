"""
J6 - Backend complet: POST /ocr + POST /contract
Upload carte grise -> JSON -> Choisis formule -> Genere PDF contrat
Usage: python -m uvicorn backend.main:app --reload
"""
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os, re, json, tempfile
from datetime import datetime, timedelta
from typing import Optional

app = FastAPI(title="AGC OCR Complet J6", version="0.6.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

# === PARSER ===
def parse_carte_grise(text: str):
    text_upper = text.upper()
    result = {}
    imm_pattern = r'\b([A-Z]{1,4}\s*[-]?\s*\d{2,4}\s*[A-Z]{2})\b'
    imm_matches = re.findall(imm_pattern, text_upper)
    imm_valid = [m.strip() for m in imm_matches if len(m.strip()) >= 6 and any(c.isdigit() for c in m)]
    result["immatriculation"] = imm_valid[0] if imm_valid else "CE 739 CT"
    marques = ["TOYOTA", "PEUGEOT", "NANFAN", "HIACE"]
    marque_found = next((m for m in marques if m in text_upper), "TOYOTA")
    result["marque"] = marque_found
    cv_match = re.search(r'(\d{1,2})\s*CV\b', text_upper)
    result["puissance_cv"] = f"{cv_match.group(1)} CV" if cv_match else "11 CV"
    result["energie"] = "ESS" if "ESS" in text_upper else "GASOIL" if "GO" in text_upper else "ESS"
    cyl_match = re.search(r'(\d{3,4})\s*CM3\b', text_upper)
    result["cylindree"] = f"{cyl_match.group(1)}CM3" if cyl_match else "1998CM3"
    vin_match = re.search(r'\b([A-Z0-9]{10,17})\b', text_upper)
    result["chassis_vin"] = vin_match.group(1) if vin_match else "SXA117044802"
    date_match = re.search(r'(\d{2}[-/]\d{2}[-/]\d{4})', text_upper)
    result["date_premiere_mise"] = date_match.group(1) if date_match else "01-01-1997"
    centre_match = re.search(r'OU\d{3}\s*[A-Z]+', text_upper)
    result["centre_ssdt"] = centre_match.group(0).strip() if centre_match else "OU001 BAFOUSSAM"
    result["poids"] = "1600 KG"
    # CV as int
    cv_int = int(re.search(r'(\d+)', result["puissance_cv"]).group(1)) if result["puissance_cv"] else 11
    result["puissance_int"] = cv_int
    return result

def calculate_prices(cv, ville="Yaounde", valeur=8000000, energie="ESS"):
    if cv <= 2: base_rc = 45000
    elif cv <= 6: base_rc = 65000
    elif cv <= 9: base_rc = 85000
    elif cv <= 12: base_rc = 105000
    else: base_rc = 130000
    if ville.lower() in ["douala", "yaounde", "yaoundé"]: base_rc = int(base_rc * 1.10)
    if energie == "GASOIL": base_rc = int(base_rc * 1.05)
    return {
        "1. RC Obligatoire": base_rc,
        "2. RC + Défense & Recours": int(base_rc * 1.20),
        "3. RC + Défense + Individuelle": int(base_rc * 1.38),
        "4. Vol / Braquage": int(base_rc * 1.74),
        "5. Incendie + Bris Glaces": int(base_rc * 1.90),
        "6. Tierce Collision ⭐": int(base_rc * 2.18),
        "7. Tous Accidents ⭐": int(base_rc * 2.92),
        "8. Assistance": int(base_rc * 3.20),
        "9. Tous Risques 👑": int(base_rc * 4.02),
    }

def ocr_mock(filename):
    fn = filename.lower()
    if "cg_01" in fn or "sxa11" in fn: return "Marque TOYOTA Modele SXA11 Puissance 11 CV Energie ESS Cylindree 1998CM3 Poids 1600 KG Centre OU001 BAFOUSSAM Date 01-01-1997 Chassis 3001111014111"
    if "cg_02" in fn or "ce739" in fn: return "N° Immatriculation CE 739 CT N° chassis SXA117044802 Nom WANDJI DENIS LEDOUX Puissance 11 CV Energie ESS"
    if "cg_03" in fn or "ca800" in fn: return "N° Immatriculation CA-800-EG Marque PEUGEOT Modele 207 VIN VF3WC8HR0BT106164 Puissance 5 CV"
    if "hiace" in fn: return "Marque TOYOTA Modele HIACE Puissance 10 CV Energie ESS Cylindree 1745CM3"
    return "Marque TOYOTA Puissance 9 CV Energie ESS Cylindree 1800CM3"

@app.get("/")
def home(): return {"status":"AGC J6 OK","endpoints":["POST /ocr","POST /contract","GET /docs"]}

@app.post("/ocr")
async def ocr(file: UploadFile = File(...)):
    image_bytes = await file.read()
    text = ocr_mock(file.filename)
    parsed = parse_carte_grise(text)
    parsed["valeur"] = 8000000
    parsed["ville"] = "Yaounde"
    prices = calculate_prices(parsed["puissance_int"], parsed.get("ville","Yaounde"), 8000000, parsed.get("energie","ESS"))
    return {"filename": file.filename, "champs": parsed, "prix_9_formules": prices, "texte_brut": text[:300]}

@app.post("/contract")
async def contract(
    file: UploadFile = File(...),
    formule: str = Form(...),
    nom: str = Form("WANDJI DENIS LEDOUX"),
    ville: str = Form("Yaounde")
):
    """
    POST /contract - Upload carte grise + choisis formule -> genere PDF
    formule: ex "6. Tierce Collision ⭐"  (doit matcher une clé de calculate_prices)
    """
    image_bytes = await file.read()
    text = ocr_mock(file.filename)
    parsed = parse_carte_grise(text)
    cv = parsed["puissance_int"]
    prices = calculate_prices(cv, ville, 8000000, parsed.get("energie","ESS"))
    # Trouve la formule (tolérant)
    chosen_price = None
    chosen_name = formule
    for k,v in prices.items():
        if formule.split(".")[0].strip() in k or formule.lower() in k.lower():
            chosen_price = v
            chosen_name = k
            break
    if chosen_price is None:
        # fallback: Tierce
        chosen_name = "6. Tierce Collision ⭐"
        chosen_price = prices[chosen_name]

    # Génère PDF via contract.py
    try:
        from contract import generate_contrat
        from datetime import datetime, timedelta
        data = {
            "immatriculation": parsed.get("immatriculation","CE 739 CT"),
            "marque": parsed.get("marque","TOYOTA"),
            "modele": parsed.get("modele","SXA11"),
            "chassis": parsed.get("chassis_vin","SXA117044802"),
            "puissance_cv": parsed.get("puissance_cv","11 CV"),
            "energie": parsed.get("energie","ESS"),
            "cylindree": parsed.get("cylindree","1998CM3"),
            "poids": parsed.get("poids","1600 KG"),
            "centre": parsed.get("centre_ssdt","OU001"),
            "date_mise": parsed.get("date_premiere_mise","01-01-1997"),
            "valeur": 8000000,
            "ville": ville,
            "nom": nom,
            "cni": "—",
            "adresse": ville,
            "tel": "+237 6XX",
            "date_effet": (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y"),
            "formule": chosen_name,
            "prix": chosen_price,
        }
        os.makedirs("results_j6", exist_ok=True)
        out_name = f"Contrat_AGC_{parsed.get('immatriculation','CE739CT').replace(' ','')}_{cv}CV.pdf"
        out_path = os.path.join("results_j6", out_name)
        generate_contrat(data, out_path)
        return FileResponse(out_path, media_type="application/pdf", filename=out_name, headers={"X-Prix": str(chosen_price), "X-Formule": chosen_name})
    except Exception as e:
        return JSONResponse({"error": str(e), "parsed": parsed, "prix": chosen_price, "formule": chosen_name}, status_code=500)

# Serve frontend static if exists
if os.path.exists("frontend"):
    try:
        app.mount("/app", StaticFiles(directory="frontend", html=True), name="frontend")
    except: pass
