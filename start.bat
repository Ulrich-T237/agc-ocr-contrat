@echo off
echo Lancement AGC OCR J6...
python -m uvicorn backend.main:app --reload
pause
