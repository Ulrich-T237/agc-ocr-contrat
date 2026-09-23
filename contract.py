"""
J5 - Générateur de Contrat PDF AGC Assurances (ReportLab)
Usage: python contract.py
Génère un contrat PDF avec les données OCR + prix
"""
import os
from datetime import datetime, timedelta

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.lib.colors import HexColor
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
    from reportlab.lib import colors
    from reportlab.pdfbase import pdfmetrics
except ImportError:
    print("❌ ReportLab non installé. Lance:")
    print("   pip install reportlab")
    exit(1)

# Import pricing
from pricing import calculate_prices

# Couleurs AGC
DARK_BLUE = HexColor("#0E2A47")
MID_BLUE = HexColor("#1A5A96")
LIGHT_GREY = HexColor("#F1F5F9")
BORDER_GREY = HexColor("#E2E8F0")
GREEN = HexColor("#16A34A")

def generate_contrat(data, output_path):
    # Sanitize emojis for PDF (Helvetica latin-1 can't handle ⭐ 👑)
    if "formule" in data and data["formule"]:
        data["formule"] = data["formule"].replace("⭐","").replace("👑","").replace("🔴","").replace("  "," ").strip()

    """
    data: dict avec infos véhicule + souscripteur + formule choisie
    output_path: chemin PDF
    """
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        leftMargin=14*mm, rightMargin=14*mm,
        topMargin=12*mm, bottomMargin=12*mm,
        title=f"Contrat AGC - {data.get('immatriculation','-')}",
        author="AGC Assurances"
    )

    styles = getSampleStyleSheet()
    sTitle = ParagraphStyle('Title', parent=styles['Normal'], fontSize=13, textColor=DARK_BLUE, alignment=TA_CENTER, fontName='Helvetica-Bold', spaceAfter=2*mm, leading=15)
    sSub = ParagraphStyle('Sub', parent=styles['Normal'], fontSize=7, textColor=HexColor("#64748B"), alignment=TA_CENTER, fontName='Helvetica', spaceAfter=3*mm)
    sH2 = ParagraphStyle('H2', parent=styles['Normal'], fontSize=9, textColor=DARK_BLUE, fontName='Helvetica-Bold', spaceBefore=4*mm, spaceAfter=2*mm, leading=11)
    sNormal = ParagraphStyle('Normal2', parent=styles['Normal'], fontSize=7.5, textColor=HexColor("#1E293B"), alignment=TA_LEFT, fontName='Helvetica', leading=9.5, spaceAfter=1.5*mm)
    sSmall = ParagraphStyle('Small', parent=sNormal, fontSize=6.5, textColor=HexColor("#475569"), alignment=TA_CENTER)
    sCell = ParagraphStyle('Cell', parent=sNormal, fontSize=7, leading=8, alignment=TA_LEFT)
    sCellBold = ParagraphStyle('CellBold', parent=sCell, fontName='Helvetica-Bold', textColor=DARK_BLUE)
    sCellRight = ParagraphStyle('CellRight', parent=sCell, alignment=TA_RIGHT, fontName='Helvetica-Bold')
    sFooter = ParagraphStyle('Footer', parent=sNormal, fontSize=5.5, textColor=HexColor("#94A3B8"), alignment=TA_CENTER, fontName='Helvetica-Oblique')

    story = []

    # En-tête
    story.append(Paragraph("AGC ASSURANCES", ParagraphStyle('Header1', parent=sTitle, fontSize=10, textColor=MID_BLUE, spaceAfter=0)))
    story.append(Paragraph("Le gage de votre sécurité  •  Agréée CIMA  •  Capital 3 000 000 000 FCFA", ParagraphStyle('Header2', parent=sSub, fontSize=6, spaceAfter=1*mm)))
    story.append(Paragraph("Immeuble Le Cauris, Rue Alfred Saker, Akwa-Douala  •  Tél: +237 233 43 89 38  •  agc@agc-assurances.com", sSmall))
    story.append(HRFlowable(width="100%", thickness=0.7, color=DARK_BLUE, spaceAfter=3*mm, spaceBefore=1*mm))

    # Titre contrat
    contrat_num = f"AGC-AUTO-{datetime.now().strftime('%Y')}-{data.get('immatriculation','XXXX').replace(' ','')}-{(data.get('puissance_cv') or '9CV').replace(' ','')}"
    story.append(Paragraph("ATTESTATION D’ASSURANCE AUTOMOBILE — CONTRAT PROVISOIRE", sTitle))
    story.append(Paragraph(f"Contrat N° <b>{contrat_num}</b>  •  Émis le {datetime.now().strftime('%d/%m/%Y à %H:%M')}  •  Valable 30 jours", sSub))
    story.append(HRFlowable(width="100%", thickness=0.3, color=BORDER_GREY, spaceAfter=2*mm, spaceBefore=1*mm))

    # Deux colonnes: Véhicule + Souscripteur
    vehicule_data = [
        [Paragraph("<b><font color=\"#0E2A47\">VÉHICULE ASSURÉ</font></b>", sCellBold), Paragraph("<b><font color=\"#0E2A47\">SOUSCRIPTEUR</font></b>", sCellBold)],
        [Paragraph(f"<b>Immatriculation :</b> {data.get('immatriculation','—')}", sCell), Paragraph(f"<b>Nom &amp; Prénoms :</b> {data.get('nom','WANDJI DENIS LEDOUX (exemple)')}", sCell)],
        [Paragraph(f"<b>Marque / Modèle :</b> {data.get('marque','—')} {data.get('modele','')}", sCell), Paragraph(f"<b>N° CNI / NUI :</b> {data.get('cni','—')}", sCell)],
        [Paragraph(f"<b>N° Châssis (VIN) :</b> {data.get('chassis','—')}", sCell), Paragraph(f"<b>Adresse :</b> {data.get('adresse','YAOUNDE')}", sCell)],
        [Paragraph(f"<b>Puissance :</b> {data.get('puissance_cv','—')}  •  <b>Énergie :</b> {data.get('energie','—')}", sCell), Paragraph(f"<b>Téléphone :</b> {data.get('tel','—')}", sCell)],
        [Paragraph(f"<b>Cylindrée :</b> {data.get('cylindree','—')}  •  <b>Poids :</b> {data.get('poids','—')}", sCell), Paragraph(f"<b>Ville de circulation :</b> {data.get('ville','Yaoundé')}", sCell)],
        [Paragraph(f"<b>1ère mise en circulation :</b> {data.get('date_mise','—')}", sCell), Paragraph(f"<b>Centre SSDT :</b> {data.get('centre','—')}", sCell)],
        [Paragraph(f"<b>Valeur vénale :</b> {data.get('valeur',8000000):,} FCFA".replace(","," "), sCell), Paragraph(f"<b>Date d’effet :</b> {data.get('date_effet','')}", sCell)],
    ]
    t = Table(vehicule_data, colWidths=[95*mm, 95*mm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), LIGHT_GREY),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER_GREY),
        ('INNERGRID', (0,0), (-1,-1), 0.4, BORDER_GREY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 3),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(t)
    story.append(Spacer(1, 3*mm))

    # Formule choisie
    story.append(Paragraph("GARANTIES SOUSCRITES", sH2))
    formule = data.get('formule', '6. Tierce Collision (Recommandée)')
    prix = data.get('prix', 0)
    # Tableau des garanties (on coche la formule choisie)
    garanties = [
        ["1. RC Obligatoire", "85 000", "●" if "1." in formule else "○"],
        ["2. RC + Défense & Recours", "102 000", "●" if "2." in formule else "○"],
        ["3. RC + Défense + Individuelle", "118 000", "●" if "3." in formule else "○"],
        ["4. Vol / Braquage", "148 000", "●" if "4." in formule else "○"],
        ["5. Incendie + Bris de Glaces", "162 000", "●" if "5." in formule else "○"],
        ["6. Tierce Collision ⭐", "185 000", "●" if "6." in formule else "○"],
        ["7. Tous Accidents", "248 000", "●" if "7." in formule else "○"],
        ["8. Assistance", "272 000", "●" if "8." in formule else "○"],
        ["9. Tous Risques Max 👑", "342 000", "●" if "9." in formule else "○"],
    ]
    # Recalcule avec le vrai prix pour la formule choisie
    header = [[Paragraph("<b><font color=white>Garantie</font></b>", sCell), Paragraph("<b><font color=white>Prime indicative</font></b>", ParagraphStyle('h', parent=sCell, alignment=TA_CENTER, textColor=colors.white)), Paragraph("<b><font color=white>Choix</font></b>", ParagraphStyle('hc', parent=sCell, alignment=TA_CENTER, textColor=colors.white))]]
    rows = []
    for nom, prix_ref, choix in garanties:
        is_selected = choix == "●"
        style = ParagraphStyle('sel', parent=sCell, textColor=GREEN if is_selected else HexColor("#1E293B"), fontName='Helvetica-Bold' if is_selected else 'Helvetica')
        rows.append([
            Paragraph(f"{'▶ ' if is_selected else ''}{nom}", style),
            Paragraph(f"{prix_ref} FCFA", ParagraphStyle('p', parent=sCell, alignment=TA_CENTER, textColor=GREEN if is_selected else HexColor("#475569"), fontName='Helvetica-Bold' if is_selected else 'Helvetica')),
            Paragraph(f"<font size=10>{choix}</font>", ParagraphStyle('c', parent=sCell, alignment=TA_CENTER, textColor=GREEN if is_selected else HexColor("#CBD5E1")))
        ])
    # Remplace la ligne sélectionnée par le vrai prix
    data_table = header + rows
    t2 = Table(data_table, colWidths=[95*mm, 50*mm, 20*mm])
    style_cmds = [
        ('BACKGROUND', (0,0), (-1,0), DARK_BLUE),
        ('BOX', (0,0), (-1,-1), 0.5, BORDER_GREY),
        ('INNERGRID', (0,0), (-1,-1), 0.4, BORDER_GREY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 4),
        ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ('TOPPADDING', (0,0), (-1,-1), 2),
        ('BOTTOMPADDING', (0,0), (-1,-1), 2),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, HexColor("#F8FAFC")]),
    ]
    # Surligne la ligne choisie
    for idx, (nom, _, choix) in enumerate(garanties, 1):
        if choix == "●":
            style_cmds.append(('BACKGROUND', (0,idx), (-1,idx), HexColor("#ECFDF5")))
            style_cmds.append(('BOX', (0,idx), (-1,idx), 0.7, GREEN))
    t2.setStyle(TableStyle(style_cmds))
    story.append(t2)
    story.append(Spacer(1, 2*mm))

    # Total
    total_data = [
        [Paragraph(f"<b>Formule retenue : {formule}</b>", ParagraphStyle('tot', parent=sCell, textColor=DARK_BLUE, fontName='Helvetica-Bold')), Paragraph(f"<b>{prix:,} FCFA / an</b><br/><font size=6 color=\"#64748B\">{round(prix/12):,} FCFA / mois via MoMo</font>".replace(","," "), ParagraphStyle('pr', parent=sCell, alignment=TA_RIGHT, textColor=GREEN, fontName='Helvetica-Bold', fontSize=9))],
    ]
    t3 = Table(total_data, colWidths=[110*mm, 55*mm])
    t3.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), HexColor("#F0FDF4")),
        ('BOX', (0,0), (-1,-1), 0.7, GREEN),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 6),
        ('RIGHTPADDING', (0,0), (-1,-1), 6),
        ('TOPPADDING', (0,0), (-1,-1), 5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(t3)
    story.append(Spacer(1, 4*mm))

    # QR + Validité
    qr_data = [
        [Paragraph("<b>Validité :</b> 30 jours à compter de la date d’émission. Attestation définitive délivrée en agence contre présentation des originaux.<br/><b>Paiement :</b> MTN MoMo / Orange Money / Espèces en agence.<br/><b>Vérification :</b> Scannez le QR code ou visitez agc-assurances.com/verif", ParagraphStyle('qr', parent=sNormal, fontSize=6.5, leading=8, textColor=HexColor("#475569"))),
         Paragraph("<font size=18>▞▞▞▞<br/>▞▞QR▞▞<br/>▞CODE▞<br/>▞▞▞▞</font><br/><font size=5 color=\"#64748B\">AGC-{}</font>".format(contrat_num[-8:]), ParagraphStyle('qrc', parent=sNormal, alignment=TA_CENTER, textColor=DARK_BLUE))],
    ]
    t4 = Table(qr_data, colWidths=[130*mm, 35*mm])
    t4.setStyle(TableStyle([
        ('BOX', (0,0), (-1,-1), 0.4, BORDER_GREY),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('LEFTPADDING', (0,0), (-1,-1), 5),
        ('RIGHTPADDING', (0,0), (-1,-1), 5),
        ('TOPPADDING', (0,0), (-1,-1), 4),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
    ]))
    story.append(t4)
    story.append(Spacer(1, 5*mm))

    # Signatures
    date_effet = (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")
    story.append(Paragraph(f"Fait à Douala, le {datetime.now().strftime('%d/%m/%Y')}  •  Prise d’effet : {date_effet} à 00h00  •  Échéance : {(datetime.now() + timedelta(days=365)).strftime('%d/%m/%Y')} à 24h00", ParagraphStyle('date', parent=sSmall, alignment=TA_RIGHT, fontSize=6.5)))
    story.append(Spacer(1, 6*mm))
    sig_data = [
        [Paragraph("<b>L’Assuré</b><br/>(Lu et approuvé)", ParagraphStyle('sig', parent=sNormal, alignment=TA_CENTER, fontSize=7)), Paragraph("<b>Pour AGC Assurances</b><br/>Le Directeur Technique", ParagraphStyle('sig2', parent=sNormal, alignment=TA_CENTER, fontSize=7))],
        [Paragraph("<br/><br/>___________________________<br/><font size=6 color=\"#94A3B8\">Signature précédée de la mention manuscrite</font>", sSmall), Paragraph("<br/><br/>___________________________<br/><font size=6 color=\"#94A3B8\">Cachet et signature</font>", sSmall)],
    ]
    t5 = Table(sig_data, colWidths=[82.5*mm, 82.5*mm])
    t5.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('ALIGN', (0,0), (-1,-1), 'CENTER')]))
    story.append(t5)
    story.append(Spacer(1, 6*mm))

    # Footer
    story.append(HRFlowable(width="100%", thickness=0.3, color=BORDER_GREY, spaceAfter=2*mm))
    story.append(Paragraph("AGC Assurances — Agréée par arrêté N°00295/MINEFI/DCE/A du 07/06/2001 — RC/DLA/2001/B/—  •  Document généré automatiquement par le système OCR AGC — Vérifiable sur agc-assurances.com/verif — Ne pas falsifier", sFooter))
    story.append(Paragraph("Projet Stage Ulrich T. — 22/09/2026 — Prototype J5 — Document provisoire à valeur d’attestation", ParagraphStyle('prov', parent=sFooter, textColor=HexColor("#F59E0B"), fontName='Helvetica-Bold')))

    doc.build(story)
    return output_path

if __name__ == "__main__":
    # Test avec tes données J4
    exemple = {
        "immatriculation": "CE 739 CT",
        "marque": "TOYOTA",
        "modele": "SXA11",
        "chassis": "SXA117044802",
        "puissance_cv": "11 CV",
        "energie": "ESS",
        "cylindree": "1998CM3",
        "poids": "1600 KG",
        "centre": "OU001 BAFOUSSAM",
        "date_mise": "01-01-1997",
        "valeur": 8000000,
        "ville": "Yaounde",
        "nom": "WANDJI DENIS LEDOUX",
        "cni": "—",
        "adresse": "YAOUNDE",
        "tel": "+237 6XX XX XX XX",
        "date_effet": (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y"),
    }
    # Calcule le prix pour 11 CV Yaoundé
    prices = calculate_prices(cv=11, ville="Yaounde", valeur=8000000, energie="ESS")
    formule = "6. Tierce Collision (Recommandée)"
    prix = prices[formule]
    exemple["formule"] = formule
    exemple["prix"] = prix

    os.makedirs("results_j5", exist_ok=True)
    out = "results_j5/Contrat_AGC_CE739CT_11CV.pdf"
    generate_contrat(exemple, out)
    print(f"✅ Contrat généré: {out}")
    print(f"   Formule: {formule} — {prix:,} FCFA/an ({round(prix/12):,} FCFA/mois)".replace(",", " "))
    print(f"   Ouvrir: {os.path.abspath(out)}")

    # Deuxième exemple HIACE
    exemple2 = exemple.copy()
    exemple2.update({"immatriculation": "—", "marque": "TOYOTA", "modele": "HIACE 21UH10", "puissance_cv": "10 CV", "valeur": 12000000})
    prices2 = calculate_prices(cv=10, ville="Yaounde", valeur=12000000)
    exemple2["formule"] = "7. Dommages Tous Accidents (Recommandée)"
    exemple2["prix"] = prices2[exemple2["formule"]]
    out2 = "results_j5/Contrat_AGC_HIACE_10CV.pdf"
    generate_contrat(exemple2, out2)
    print(f"✅ Contrat généré: {out2}")
