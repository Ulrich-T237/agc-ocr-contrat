"""
J5 - Pricing Engine AGC Assurances - 9 Formules Auto
Calcule le prix selon: Puissance (CV), Ville, Valeur vénale, Énergie
Basé sur la grille AGC réelle (simplifiée pour le stage)
Usage: python pricing.py
"""

def calculate_prices(cv, ville="Yaounde", valeur=8000000, energie="ESS"):
    """
    cv: int (ex: 11)
    ville: str (Yaounde, Douala, Bafoussam, Garoua...)
    valeur: int (ex: 8000000 FCFA)
    energie: str (ESS, GASOIL)
    Retourne dict des 9 formules avec prix
    """
    # Base RC obligatoire selon CV (barème CIMA simplifié)
    # Source: tarif RC Cameroun 2024
    if cv <= 2:
        base_rc = 45000
    elif cv <= 6:
        base_rc = 65000
    elif cv <= 9:
        base_rc = 85000
    elif cv <= 12:
        base_rc = 105000
    else:
        base_rc = 130000

    # Majoration ville (Douala/Yaoundé = +10%, Grand Nord = -5%)
    ville = ville.lower()
    if ville in ["douala", "yaounde", "yaoundé"]:
        base_rc = int(base_rc * 1.10)
    elif ville in ["garoua", "maroua", "ngaoundere"]:
        base_rc = int(base_rc * 0.95)

    # Majoration énergie (Gasoil légèrement + cher)
    if energie == "GASOIL":
        base_rc = int(base_rc * 1.05)

    # Les 9 formules AGC (progressives, chaque niveau inclut le précédent)
    formules = {
        "1. RC Obligatoire (Minimum légal CIMA)": base_rc,
        "2. RC + Défense & Recours": int(base_rc * 1.20),
        "3. RC + Défense + Individuelle Pers. Transportées": int(base_rc * 1.38),
        "4. Vol / Vol Partiel + Vol par Braquage": int(base_rc * 1.74),
        "5. Incendie + Bris de Glaces & Blocs Feux": int(base_rc * 1.90),
        "6. Tierce Collision (Recommandée)": int(base_rc * 2.18),
        "7. Dommages Tous Accidents (Recommandée)": int(base_rc * 2.92),
        "8. Assistance Réparation + Assistance Judiciaire": int(base_rc * 3.20),
        "9. Tous Risques + Premiers Risques (Premium Max)": int(base_rc * 4.02),
    }

    # Remise si valeur faible (<5M) : -5%
    if valeur < 5000000:
        for k in formules:
            formules[k] = int(formules[k] * 0.95)

    return formules

if __name__ == "__main__":
    print("="*65)
    print("J5 - PRICING ENGINE AGC - 9 Formules Auto")
    print("="*65)

    # Test 1: Ton image cg_01 TOYOTA 11 CV Yaoundé 8M
    print("\n📊 Test 1: TOYOTA SXA11 - 11 CV - Yaoundé - 8 000 000 FCFA - ESS")
    print("-"*65)
    prices = calculate_prices(cv=11, ville="Yaounde", valeur=8000000, energie="ESS")
    for i, (nom, prix) in enumerate(prices.items(), 1):
        badge = ""
        if "Recommandée" in nom:
            badge = " ⭐ Recommandée"
        elif "Premium" in nom:
            badge = " 👑 Premium"
        elif "Obligatoire" in nom:
            badge = " 🔴 Obligatoire"
        print(f"{i}. {nom:<48} : {prix:>7,} FCFA{badge}".replace(",", " "))

    # Test 2: Petite moto 1 CV Mbouda
    print("\n📊 Test 2: NANFAN N-125 - 1 CV - Mbouda - 500 000 FCFA - ESS")
    print("-"*65)
    prices2 = calculate_prices(cv=1, ville="Mbouda", valeur=500000, energie="ESS")
    for nom, prix in prices2.items():
        print(f"  {nom:<48} : {prix:>7,} FCFA".replace(",", " "))

    # Test 3: HIACE 10 CV Yaoundé
    print("\n📊 Test 3: TOYOTA HIACE - 10 CV - Yaoundé - 12 000 000 FCFA - ESS")
    print("-"*65)
    prices3 = calculate_prices(cv=10, ville="Yaounde", valeur=12000000, energie="ESS")
    for nom, prix in prices3.items():
        print(f"  {nom:<48} : {prix:>7,} FCFA".replace(",", " "))

    # Sauvegarde JSON pour l'API
    import json, os
    os.makedirs("results_j5", exist_ok=True)
    with open("results_j5/pricing_exemple_TOYOTA_11CV.json", "w", encoding="utf-8") as f:
        json.dump({
            "vehicule": "TOYOTA SXA11 - 11 CV - Yaoundé",
            "valeur": 8000000,
            "formules": prices,
            "formule_recommandee": "6. Tierce Collision (Recommandée)",
            "prix_recommande": prices["6. Tierce Collision (Recommandée)"],
            "mensualite_momo": round(prices["6. Tierce Collision (Recommandée)"]/12)
        }, f, indent=2, ensure_ascii=False)
    print("\n💾 Sauvegardé: results_j5/pricing_exemple_TOYOTA_11CV.json")
    print(f"   → Mensualité MoMo recommandée: {round(prices['6. Tierce Collision (Recommandée)']/12):,} FCFA / mois".replace(",", " "))
    print("\n" + "="*65)
    print("✅ J5 Matin terminé. Prochaine étape: Générer le PDF contrat")
    print("="*65)
