import json
import os
import sys
from data_loader import fetch_company_data

UNIVERSE = [
    # 🇨🇭 Schweiz (SMI & SPI Bluechips)
    'GEBN.SW', 'NESN.SW', 'NOVN.SW', 'UBSG.SW', 'SIKA.SW', 
    'ABBN.SW', 'ZURN.SW', 'LONN.SW', 'HOLN.SW', 'SCMN.SW',
    'GIVN.SW', 'SREN.SW', 'LOGN.SW', 'STMN.SW',
    
    # 🇪🇺 Europa (DAX, EuroStoxx, Euronext)
    'SAP.DE', 'SIE.DE', 'ALV.DE', 'BMW.DE', 'MBG.DE',
    'MC.PA', 'OR.PA', 'ASML.AS', 'AIR.PA',
    
    # 🇺🇸 USA & Global Leaders (S&P 500 / Nasdaq)
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 
    'META', 'TSLA', 'JNJ', 'JPM', 'V', 'KO', 'PG', 'LLY'
]

def load_or_update_cache(force_refresh=False):
    cache_file = os.path.join(os.path.dirname(__file__), 'companies_cache.json')
    if not force_refresh and os.path.exists(cache_file):
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if len(data) >= 30:
                    return data
        except Exception as e:
            print(f"Cache-Fehler: {e}, lade neu von API...")

    print(f"Verbinde direkt mit Yahoo Finance API fuer {len(UNIVERSE)} Unternehmen...")
    results = []
    for sym in UNIVERSE:
        try:
            c_data = fetch_company_data(sym)
            results.append(c_data)
            print(f"Geladen: {sym} ({c_data.get('name')})")
        except Exception as e:
            print(f"Fehler bei {sym}: {e}")

    try:
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        print(f"Erfolgreich {len(results)} Unternehmen im Cache gespeichert.")
    except Exception as e:
        print(f"Fehler beim Schreiben des Caches: {e}")

    return results

if __name__ == '__main__':
    load_or_update_cache(force_refresh=True)
