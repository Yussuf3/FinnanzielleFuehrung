"""
hsg_engine.py - HSG Kennzahlensystem & Wealth Management Decision Engine.
Basiert auf der Vorlesung 'Finanzielle Führung' (HSG, Dr. Daniel Tinner):
- Magisches Dreieck (Rendite, Risiko/Sicherheit, Liquidität)
- DuPont-Zerlegung
- Automatisierte Investment-Klassifikation & Kundengesprächs-Pitch für Wealth Manager
"""

import numpy as np

def score_dimension(metrics: dict, dimension_type: str) -> float:
    """Berechnet einen normalisierten Score (0-100) für eine Dimension des Magischen Dreiecks."""
    score = 50.0  # Basiswert
    
    if dimension_type == 'profitability':
        # Rendite: ROE, EBIT-Marge, ROIC, ROS
        roe = metrics.get('roe')
        ebit_m = metrics.get('ebit_margin')
        ros = metrics.get('ros')
        
        sub_scores = []
        if roe is not None:
            # ROE Benchmark: <0% -> 10, 0-10% -> 40, 10-15% -> 65, 15-25% -> 85, >25% -> 100
            s = np.clip((roe / 25.0) * 85.0, 0, 100)
            sub_scores.append(s)
        if ebit_m is not None:
            # EBIT-Marge: <5% -> 30, 10% -> 60, >20% -> 90+
            s = np.clip((ebit_m / 20.0) * 85.0, 0, 100)
            sub_scores.append(s)
        if ros is not None:
            s = np.clip((ros / 15.0) * 80.0, 0, 100)
            sub_scores.append(s)
            
        if sub_scores:
            score = float(np.mean(sub_scores))
            
    elif dimension_type == 'safety':
        # Sicherheit / Risiko: Eigenkapitalquote, Debt-to-Equity, Net Debt/EBITDA, Anlagedeckung II
        eq_ratio = metrics.get('equity_ratio')
        de = metrics.get('debt_to_equity')
        nd_ebitda = metrics.get('net_debt_ebitda')
        cov2 = metrics.get('asset_coverage_2')
        
        sub_scores = []
        if eq_ratio is not None:
            # EK-Quote Benchmark: >50% hervorragend (90-100), 30-50% solide (60-80), <20% kritisch (<40)
            s = np.clip((eq_ratio / 50.0) * 85.0, 0, 100)
            sub_scores.append(s)
        if de is not None:
            # D/E: <50% hervorragend (95), 100% (70), >200% (<40)
            s = np.clip(100 - (de / 200.0) * 60.0, 10, 100)
            sub_scores.append(s)
        if nd_ebitda is not None:
            # Net Debt / EBITDA: <1.5x top (90), 2.5x neutral (60), >4x schwach (20)
            if nd_ebitda <= 0:
                s = 95.0 # Netto Cash Position!
            else:
                s = np.clip(100.0 - (nd_ebitda / 4.0) * 70.0, 10, 100)
            sub_scores.append(s)
        if cov2 is not None:
            # Anlagedeckungsgrad II: Ziel >= 100% (Goldene Finanzierungsregel)
            s = 85.0 if cov2 >= 100 else np.clip((cov2 / 100.0) * 60.0, 10, 80)
            sub_scores.append(s)
            
        if sub_scores:
            score = float(np.mean(sub_scores))
            
    elif dimension_type == 'liquidity':
        # Liquidität: Current Ratio (L3), Quick Ratio (L2), Cash Ratio (L1), Cashflow Ratio
        cr = metrics.get('current_ratio')
        qr = metrics.get('quick_ratio')
        cfr = metrics.get('cashflow_ratio')
        
        sub_scores = []
        if cr is not None:
            # Current Ratio: >150-200% super (85-100), 100-150% okay (60-80), <100% Liquiditätsrisiko (<40)
            if cr >= 150:
                s = np.clip(75 + (cr - 150) / 100 * 25, 75, 100)
            elif cr >= 100:
                s = 50 + (cr - 100) / 50 * 25
            else:
                s = (cr / 100) * 50
            sub_scores.append(s)
        if qr is not None:
            # Quick Ratio: Ziel ~100%
            s = np.clip((qr / 100.0) * 80.0, 0, 100)
            sub_scores.append(s)
        if cfr is not None:
            # Cashflow Ratio: >100% hervorragend (Geberit Sanitec Vorlesung)
            s = np.clip((cfr / 100.0) * 80.0, 0, 100)
            sub_scores.append(s)
            
        if sub_scores:
            score = float(np.mean(sub_scores))
            
    return round(float(np.clip(score, 5, 98)), 1)

def evaluate_company(comp: dict) -> dict:
    """Evaluiert ein Unternehmen anhand des Magischen Dreiecks und erstellt eine Wealth Management Einstufung."""
    liq_score = score_dimension(comp['liquidity'], 'liquidity')
    safe_score = score_dimension(comp['safety'], 'safety')
    prof_score = score_dimension(comp['profitability'], 'profitability')
    
    # Gesamtscore (Gewichtetes harmonisches/arithmetisches Mittel)
    overall_score = round(0.40 * prof_score + 0.35 * safe_score + 0.25 * liq_score, 1)
    
    # Wealth Management Klassifikation & Empfehlung
    div_yield = comp['valuation'].get('dividend_yield') or 0
    pe = comp['valuation'].get('pe_trailing')
    roe = comp['profitability'].get('roe') or 0
    eq_ratio = comp['safety'].get('equity_ratio') or 0
    cr = comp['liquidity'].get('current_ratio') or 0
    
    recommendation_type = "Ausgewogen (Solide Qualität)"
    suitable_for = "Ausgewogene Anleger mit mittelfristigem Horizont"
    badge_color = "#2E7D32" # Grün
    pitch_points = []
    
    if safe_score >= 70 and liq_score >= 65 and div_yield >= 2.0:
        recommendation_type = "Defensiver Qualitäts- & Dividendentitel"
        suitable_for = "Sicherheitsorientierte Kunden, Stiftungen, Pensionskassen & Dividendenjäger"
        badge_color = "#1565C0" # Blau
        pitch_points.append(f"Hohe Bilanzsicherheit (Eigenkapitalquote: {eq_ratio:.1f}%) und robuste Liquidität schützen in Krisen.")
        pitch_points.append(f"Attraktive Ausschüttung: Dividendenrendite von {div_yield:.2f}% bietet stetigen Ertrag.")
        pitch_points.append("Entspricht voll der 'Goldenen Finanzierungsregel'.")
        
    elif prof_score >= 75 and roe >= 18:
        recommendation_type = "Wachstum & Hohe Rentabilität"
        suitable_for = "Renditeorientierte Kunden mit dynamischem Wachstumsprofil"
        badge_color = "#6A1B9A" # Violett
        pitch_points.append(f"Exzellente Kapitalverzinsung: Eigenkapitalrendite von {roe:.1f}% demonstriert überlegene Preissetzungsmacht.")
        pitch_points.append("Starke Margen stärken die Generierung des freien Cashflows (Free Cash Flow).")
        pitch_points.append("Hervorragende Spitzenkennzahl im Branchenvergleich.")
        
    elif pe is not None and 0 < pe < 16 and overall_score >= 50:
        recommendation_type = "Unterbewertete Substanz (Value)"
        suitable_for = "Wertorientierte Anleger auf der Suche nach Unterbewertungen"
        badge_color = "#E65100" # Orange
        pitch_points.append(f"Günstige Bewertung mit einem Kurs-Gewinn-Verhältnis (KGV) von {pe:.1f}x bei soliden Fundamentaldaten.")
        pitch_points.append("Gutes Chance-Risiko-Verhältnis durch Bewertungsabschlag zum Gesamtmarkt.")
        
    elif overall_score < 45 or cr < 90 or eq_ratio < 20:
        recommendation_type = "Spekulativ / Restrukturierungspotenzial"
        suitable_for = "Nur für hochspekulative Anleger; für konservative Kunden nicht geeignet"
        badge_color = "#C62828" # Rot
        pitch_points.append("Erhöhte Verschuldung oder angespannte Liquidität erfordern engmaschiges Monitoring.")
        pitch_points.append("Eventueller Sanierungs- oder Refinanzierungsbedarf (siehe Air Berlin Fallbeispiel).")
    else:
        pitch_points.append(f"Ausgewogenes Profil über alle drei Dimensionen des Zieldreiecks.")
        pitch_points.append(f"Solide Eigenkapitalquote von {eq_ratio:.1f}% bei gesundem ROE von {roe:.1f}%.")
        
    return {
        'scores': {
            'profitability': prof_score,
            'safety': safe_score,
            'liquidity': liq_score,
            'overall': overall_score
        },
        'profile': {
            'type': recommendation_type,
            'target_client': suitable_for,
            'color': badge_color,
            'pitch_points': pitch_points
        }
    }

def format_metric_value(val, unit="%", decimals=1):
    """Formatiert Kennzahlenwerte lesbar für Kundenberichte."""
    if val is None or np.isnan(val):
        return "–"
    if unit == "%":
        return f"{val:.{decimals}f}%"
    elif unit == "x":
        return f"{val:.{decimals}f}x"
    elif unit == "CHF" or unit == "$":
        if abs(val) >= 1e9:
            return f"{val/1e9:.2f} Mrd."
        elif abs(val) >= 1e6:
            return f"{val/1e6:.2f} Mio."
        else:
            return f"{val:,.0f}"
    return f"{val:.{decimals}f}"
