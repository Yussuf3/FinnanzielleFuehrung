"""
data_loader.py - Modul zum Abrufen und Aufbereiten von Finanzdaten über die öffentliche Yahoo Finance API.
Berechnet die Kennzahlen des "Magischen Dreiecks" nach den Vorgaben der HSG-Vorlesung 'Finanzielle Führung'.
"""

import yfinance as yf
import pandas as pd
import numpy as np

def safe_get(df, row_keys, col_idx=0):
    """Sucht in einem Financial DataFrame (Balance Sheet, Financials, Cashflow) sicher nach Werten."""
    if df is None or df.empty:
        return None
    for key in row_keys:
        if key in df.index:
            try:
                val = df.loc[key].iloc[col_idx]
                if pd.notna(val) and not np.isnan(val):
                    return float(val)
            except Exception:
                continue
    return None

def fetch_company_data(ticker_symbol: str) -> dict:
    """Ruft Bilanz-, GuV- und Cashflow-Daten sowie Marktkennzahlen über die Yahoo Finance API ab."""
    ticker_symbol = ticker_symbol.strip().upper()
    ticker = yf.Ticker(ticker_symbol)
    
    try:
        info = ticker.info or {}
    except Exception:
        info = {}
        
    try:
        bs = ticker.balance_sheet
    except Exception:
        bs = pd.DataFrame()
        
    try:
        fin = ticker.financials
    except Exception:
        fin = pd.DataFrame()
        
    try:
        cf = ticker.cashflow
    except Exception:
        cf = pd.DataFrame()
        
    # Basisdaten
    name = info.get('shortName') or info.get('longName') or ticker_symbol
    currency = info.get('currency') or 'USD'
    sector = info.get('sector') or 'N/A'
    industry = info.get('industry') or 'N/A'
    country = info.get('country') or 'N/A'
    summary = info.get('longBusinessSummary') or 'Keine Beschreibung verfügbar.'
    market_cap = info.get('marketCap')
    current_price = info.get('currentPrice') or info.get('regularMarketPrice')
    
    # 1. Bilanzpositionen (Aktuellste Periode col_idx=0)
    current_assets = safe_get(bs, ['Current Assets', 'Total Current Assets'])
    current_liabilities = safe_get(bs, ['Current Liabilities', 'Total Current Liabilities'])
    cash = safe_get(bs, ['Cash And Cash Equivalents', 'Cash Cash Equivalents And Short Term Investments', 'Cash'])
    receivables = safe_get(bs, ['Receivables', 'Accounts Receivable', 'Gross Accounts Receivable'])
    inventory = safe_get(bs, ['Inventory', 'Inventories'])
    stockholders_equity = safe_get(bs, ['Stockholders Equity', 'Total Equity Gross Minority Interest', 'Common Stock Equity'])
    total_assets = safe_get(bs, ['Total Assets'])
    total_liabilities = safe_get(bs, ['Total Liabilities Net Minority Interest', 'Total Liabilities'])
    total_debt = safe_get(bs, ['Total Debt'])
    net_debt = safe_get(bs, ['Net Debt'])
    non_current_assets = safe_get(bs, ['Non Current Assets', 'Total Non Current Assets', 'Net PPE'])
    long_term_debt = safe_get(bs, ['Long Term Debt', 'Long Term Debt And Capital Lease Obligation'])
    
    # Vorperiode (col_idx=1) für Durchschnittswerte (falls vorhanden)
    equity_prev = safe_get(bs, ['Stockholders Equity', 'Total Equity Gross Minority Interest'], col_idx=1)
    assets_prev = safe_get(bs, ['Total Assets'], col_idx=1)
    
    # Durchschnittliches Eigen- & Gesamtkapital nach HSG-Standard: Ø EK = (EK_t + EK_t-1) / 2
    avg_equity = (stockholders_equity + equity_prev) / 2 if (stockholders_equity and equity_prev) else stockholders_equity
    avg_assets = (total_assets + assets_prev) / 2 if (total_assets and assets_prev) else total_assets
    
    # 2. Erfolgsrechnung / GuV
    revenue = safe_get(fin, ['Total Revenue', 'Operating Revenue'])
    gross_profit = safe_get(fin, ['Gross Profit'])
    ebit = safe_get(fin, ['EBIT', 'Operating Income'])
    ebitda = safe_get(fin, ['EBITDA', 'Normalized EBITDA'])
    net_income = safe_get(fin, ['Net Income', 'Net Income Common Stockholders', 'Net Income From Continuing Operation Net Minority Interest'])
    interest_expense = safe_get(fin, ['Interest Expense', 'Interest Expense Non Operating'])
    tax_rate = safe_get(fin, ['Tax Rate For Calcs']) or 0.20
    
    # 3. Geldflussrechnung (Cashflow)
    operating_cf = safe_get(cf, ['Operating Cash Flow', 'Cash Flowsfromusedin Operating Activities'])
    capex = safe_get(cf, ['Capital Expenditure'])
    free_cash_flow = safe_get(cf, ['Free Cash Flow'])
    if free_cash_flow is None and operating_cf is not None and capex is not None:
        free_cash_flow = operating_cf - abs(capex)
        
    # --- BERECHNUNG DER KENNZAHLEN (HSG VORLESUNG 7 DR. TINNER) ---
    
    # A. LIQUIDITÄTSKENNZAHLEN
    # Liquiditätsgrad I (Cash Ratio) = Flüssige Mittel / kurzfristiges Fremdkapital
    cash_ratio = (cash / current_liabilities * 100) if (cash and current_liabilities) else None
    
    # Liquiditätsgrad II (Quick Ratio) = (Flüssige Mittel + Forderungen) / kurzfristiges Fremdkapital
    quick_ratio = ((cash + (receivables or 0)) / current_liabilities * 100) if (cash and current_liabilities) else None
    
    # Liquiditätsgrad III (Current Ratio) = Umlaufvermögen / kurzfristiges Fremdkapital
    current_ratio = (current_assets / current_liabilities * 100) if (current_assets and current_liabilities) else None
    
    # Cashflow Ratio = Cashflow aus Geschäftstätigkeit / kurzfristige Verbindlichkeiten
    cashflow_ratio = (operating_cf / current_liabilities * 100) if (operating_cf and current_liabilities) else None
    
    # B. SICHERHEITSKENNZAHLEN (RISIKO / KAPITALSTRUKTUR)
    # Eigenkapitalquote (Eigenfinanzierungsgrad) = Eigenkapital / Gesamtkapital
    equity_ratio = (stockholders_equity / total_assets * 100) if (stockholders_equity and total_assets) else None
    
    # Fremdkapitalquote = Fremdkapital / Gesamtkapital
    debt_ratio = (total_liabilities / total_assets * 100) if (total_liabilities and total_assets) else None
    
    # Debt-to-Equity (Verschuldungsgrad) = Fremdkapital / Eigenkapital
    # Alternativ Total Debt / Equity
    debt_to_equity = (total_debt / stockholders_equity * 100) if (total_debt and stockholders_equity and stockholders_equity > 0) else None
    
    # Gearing (Net Debt to Equity) = Nettoverschuldung / Eigenkapital
    gearing = (net_debt / stockholders_equity * 100) if (net_debt is not None and stockholders_equity and stockholders_equity > 0) else None
    
    # Net Debt / EBITDA (Verschuldungsfaktor / Tilgungsdauer)
    net_debt_ebitda = (net_debt / ebitda) if (net_debt is not None and ebitda and ebitda > 0) else None
    
    # Zinsdeckungsgrad (Interest Coverage) = EBIT / Zinsaufwand
    interest_coverage = (ebit / abs(interest_expense)) if (ebit and interest_expense and interest_expense != 0) else None
    
    # Anlagedeckungsgrad II = (Eigenkapital + langfr. Fremdkapital) / Anlagevermögen
    # Goldene Finanzierungsregel: Zielwert >= 100%
    if non_current_assets and non_current_assets > 0 and stockholders_equity is not None:
        lt_debt = long_term_debt if long_term_debt else (total_liabilities - (current_liabilities or 0)) if total_liabilities else 0
        asset_coverage_2 = ((stockholders_equity + max(0, lt_debt)) / non_current_assets * 100)
    else:
        asset_coverage_2 = None
        
    # C. RENTABILITÄTSKENNZAHLEN (RENDITE)
    # Eigenkapitalrendite (ROE) = Jahresgewinn / Ø Eigenkapital
    roe = (net_income / avg_equity * 100) if (net_income and avg_equity and avg_equity > 0) else None
    
    # Gesamtkapitalrendite (ROA) = (Jahresgewinn + Zinsaufwand) / Ø Gesamtkapital
    if net_income is not None and avg_assets and avg_assets > 0:
        int_exp_add = abs(interest_expense) if interest_expense else 0
        roa = ((net_income + int_exp_add) / avg_assets * 100)
    else:
        roa = None
        
    # Reingewinnmarge (ROS / Net Profit Margin) = Jahresgewinn / Nettoumsatz
    ros = (net_income / revenue * 100) if (net_income and revenue and revenue > 0) else None
    
    # EBIT-Marge = EBIT / Nettoumsatz
    ebit_margin = (ebit / revenue * 100) if (ebit and revenue and revenue > 0) else None
    
    # EBITDA-Marge = EBITDA / Nettoumsatz
    ebitda_margin = (ebitda / revenue * 100) if (ebitda and revenue and revenue > 0) else None
    
    # Bruttogewinnmarge = Bruttogewinn / Nettoumsatz
    gross_margin = (gross_profit / revenue * 100) if (gross_profit and revenue and revenue > 0) else None
    
    # Return on Invested Capital (ROIC) = NOPAT / Invested Capital
    invested_capital = safe_get(bs, ['Invested Capital'])
    if not invested_capital and stockholders_equity and total_debt:
        invested_capital = stockholders_equity + total_debt - (cash or 0)
    if ebit and invested_capital and invested_capital > 0:
        nopat = ebit * (1 - tax_rate)
        roic = (nopat / invested_capital * 100)
    else:
        roic = None

    # D. DUPONT-ZERLEGUNG DES ROE (Folie 34)
    # ROE = Reingewinnmarge (ROS) * Kapitalumschlag (CTO) * Verschuldungshebel (Equity Multiplier)
    # CTO = Nettoumsatz / Total Assets
    capital_turnover = (revenue / total_assets) if (revenue and total_assets and total_assets > 0) else None
    # Equity Multiplier = Total Assets / Stockholders Equity
    equity_multiplier = (total_assets / stockholders_equity) if (total_assets and stockholders_equity and stockholders_equity > 0) else None
    
    # E. MARKT- & BEWERTUNGSKENNZAHLEN (FÜR WEALTH MANAGER)
    pe_trailing = info.get('trailingPE')
    pe_forward = info.get('forwardPE')
    ps_ratio = info.get('priceToSalesTrailing12Months') or ((market_cap / revenue) if market_cap and revenue else None)
    pb_ratio = info.get('priceToBook') or ((market_cap / stockholders_equity) if market_cap and stockholders_equity else None)
    ev_ebitda = info.get('enterpriseToEbitda')
    
    # Dividendenrendite (in %): Yahoo liefert dividendYield bereits als Prozentwert (z.B. 8.65 für 8.65%)
    raw_dy = info.get('dividendYield')
    div_rate = info.get('dividendRate')
    price = current_price
    if div_rate and price and price > 0:
        dividend_yield = round(float(div_rate / price * 100), 2)
    elif raw_dy is not None:
        dividend_yield = round(float(raw_dy), 2)
    else:
        dividend_yield = None
        
    payout_ratio = (info.get('payoutRatio') * 100) if info.get('payoutRatio') else None
    beta = info.get('beta')
    fcf_yield = ((free_cash_flow / market_cap) * 100) if (free_cash_flow and market_cap and market_cap > 0) else None

    # Historische Zeitreihen (Umsatz, Reingewinn, Cashflow)
    history_dict = {}
    try:
        years = [str(col.year) for col in fin.columns[:4]]
        rev_hist = [float(fin.loc[k, col]) if k in fin.index and pd.notna(fin.loc[k, col]) else 0 for col in fin.columns[:4] for k in ['Total Revenue'] if k in fin.index]
        net_inc_hist = [float(fin.loc[k, col]) if k in fin.index and pd.notna(fin.loc[k, col]) else 0 for col in fin.columns[:4] for k in ['Net Income'] if k in fin.index]
        history_dict = {
            'years': years[::-1],
            'revenue': rev_hist[::-1],
            'net_income': net_inc_hist[::-1]
        }
    except Exception:
        history_dict = {'years': [], 'revenue': [], 'net_income': []}

    return {
        'symbol': ticker_symbol,
        'name': name,
        'currency': currency,
        'sector': sector,
        'industry': industry,
        'country': country,
        'summary': summary,
        'current_price': current_price,
        'market_cap': market_cap,
        # Rohdaten
        'revenue': revenue,
        'net_income': net_income,
        'ebit': ebit,
        'ebitda': ebitda,
        'total_assets': total_assets,
        'stockholders_equity': stockholders_equity,
        'operating_cf': operating_cf,
        'free_cash_flow': free_cash_flow,
        'current_assets': current_assets,
        'current_liabilities': current_liabilities,
        'cash': cash,
        # Magisches Dreieck Kennzahlen
        'liquidity': {
            'cash_ratio': cash_ratio,           # Liquiditätsgrad I (Ziel: ~20-30%)
            'quick_ratio': quick_ratio,         # Liquiditätsgrad II (Ziel: ~100%)
            'current_ratio': current_ratio,     # Liquiditätsgrad III (Ziel: >150-200%)
            'cashflow_ratio': cashflow_ratio,   # Cashflow Ratio
            'free_cash_flow': free_cash_flow    # FCF
        },
        'safety': {
            'equity_ratio': equity_ratio,       # Eigenkapitalquote (Ziel: >30-40%)
            'debt_ratio': debt_ratio,           # Fremdkapitalquote
            'debt_to_equity': debt_to_equity,   # Verschuldungsgrad D/E
            'gearing': gearing,                 # Gearing
            'net_debt_ebitda': net_debt_ebitda, # Verschuldungsfaktor (< 2.5-3x)
            'interest_coverage': interest_coverage, # Zinsdeckung (> 4-5x)
            'asset_coverage_2': asset_coverage_2    # Anlagedeckungsgrad II (Ziel: >= 100%)
        },
        'profitability': {
            'roe': roe,                         # Eigenkapitalrendite (Ziel: > 12-15%)
            'roa': roa,                         # Gesamtkapitalrendite (Ziel: > 6-8%)
            'roic': roic,                       # ROIC (Ziel: > WACC / 8-10%)
            'ros': ros,                         # Reingewinnmarge
            'ebit_margin': ebit_margin,         # EBIT-Marge
            'ebitda_margin': ebitda_margin,     # EBITDA-Marge
            'gross_margin': gross_margin        # Bruttomarge
        },
        'dupont': {
            'roe': roe,
            'ros': ros,
            'capital_turnover': capital_turnover,
            'equity_multiplier': equity_multiplier
        },
        'valuation': {
            'pe_trailing': pe_trailing,
            'pe_forward': pe_forward,
            'ps_ratio': ps_ratio,
            'pb_ratio': pb_ratio,
            'ev_ebitda': ev_ebitda,
            'dividend_yield': dividend_yield,
            'payout_ratio': payout_ratio,
            'beta': beta,
            'fcf_yield': fcf_yield
        },
        'history': history_dict
    }

def get_multiple_companies(tickers: list[str]) -> list[dict]:
    """Lädt Daten für eine Liste von Ticker-Symbolen."""
    results = []
    for t in tickers:
        try:
            data = fetch_company_data(t)
            results.append(data)
        except Exception as e:
            print(f"Fehler beim Laden von {t}: {e}")
    return results

def smart_search_company(query: str):
    """
    Intelligente Symbol-Auflösung:
    Ermöglicht es dem Nutzer, Firmennamen oder Ticker ohne Börsenkürzel einzugeben (z.B. 'BMW', 'Adidas', 'Lindt', 'Ferrari').
    Sucht über die Yahoo Finance Search API nach dem passenden Börsenkürzel mit Bilanzdaten.
    """
    import requests
    query = query.strip()
    if not query:
        return None, None
        
    # 1. Wenn bereits ein Börsenkürzel mit Punkt vorliegt (z.B. BMW.DE, NESN.SW)
    if '.' in query:
        try:
            res = fetch_company_data(query)
            if res.get('revenue') or res.get('total_assets'):
                return res, res.get('symbol')
        except Exception:
            pass

    # 2. Yahoo Finance Search API abfragen
    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={query}&quotesCount=10"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    candidates = []
    try:
        r = requests.get(url, headers=headers, timeout=5).json()
        quotes = r.get('quotes', [])
        # Nur Aktien (EQUITY) berücksichtigen
        equities = [q for q in quotes if q.get('quoteType') == 'EQUITY']
        candidates = [q.get('symbol') for q in equities if q.get('symbol')]
    except Exception as e:
        candidates = []

    # Direkter Uppercase Ticker als Fallback-Kandidat
    up_sym = query.upper()
    if up_sym not in candidates:
        candidates.insert(0, up_sym)

    # 3. Kandidaten durchgehen und prüfen, wer vollständige Bilanzdaten liefert
    for sym in candidates:
        try:
            res = fetch_company_data(sym)
            if res.get('revenue') or res.get('total_assets'):
                return res, sym
        except Exception:
            continue

    return None, None

