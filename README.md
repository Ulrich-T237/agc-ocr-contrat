# AGC Assurances - OCR Carte Grise → Contrat PDF

Stage Ulrich T. — AGC Assurances — 22 Sept → 05 Oct 2026 (2 semaines Sprint IA)

## Lancer l'app
```bash
pip install fastapi uvicorn reportlab pillow easyocr
python -m uvicorn backend.main:app --reload
# Puis ouvrir http://127.0.0.1:8000/app
```

## Structure
- backend/main.py → API POST /ocr + POST /contract
- frontend/index.html → App 2 panneaux
- dataset/carte_grise/ + dataset/cni/ + verite_terrain.xlsx
- parser.py → Regex 8 champs
- pricing.py → 9 formules AGC
- contract.py → Générateur PDF

## GitHub
https://github.com/Ulrich-T237/agc-ocr-contrat
