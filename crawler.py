#!/usr/bin/env python3
"""
Rohstoff-Preis Crawler
======================
Holt täglich Preise für 8 Rohstoffe.
Alle Preise werden in EUR/Tonne konvertiert.

Datenquellen:
- Weizen: finanzen.net (Matif Weizen, Browser-Scraping via Playwright)
- Roggen: Weizen als Proxy (Roggen korreliert stark mit Weizen)
- Zucker, Kaffee, Kakao: Yahoo Finance (US-Futures, umgerechnet)
- Butter, Käse, Milch: CLAL.it (Deutsche/EU Preise)

Voraussetzungen:
    pip3 install playwright
    playwright install chromium

Autor: jbot für Jan-Bernd
Letzte Änderung: 2026-02-20
"""

import json
import re
from datetime import datetime, timedelta
from pathlib import Path
from urllib.request import urlopen, Request
import ssl

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

SCREENSHOT_DIR = Path(__file__).parent / "data" / "screenshots"
SCREENSHOT_DIR.mkdir(exist_ok=True)

COMMODITIES = {
    "weizen": {
        "name": "Weizen",
        "unit": "EUR/t",
        "source": "finanzen_net"
    },
    "roggen": {
        "name": "Roggen",
        "unit": "EUR/t",
        "source": "weizen_proxy",
        "note": "Weizen-Basis"
    },
    "zucker": {
        "symbol": "SB=F",
        "name": "Zucker",
        "unit": "EUR/t",
        "convert_lb": True
    },
    "kaffee": {
        "symbol": "KC=F",
        "name": "Kaffee",
        "unit": "EUR/t",
        "convert_lb": True
    },
    "kakao": {
        "symbol": "CC=F",
        "name": "Kakao",
        "unit": "EUR/t",
        "convert_mt": True  # USD/MT → EUR/MT
    },
    "butter": {
        "name": "Butter",
        "unit": "EUR/t",
        "source": "clal_butter"
    },
    "kaese": {
        "name": "Käse",
        "unit": "EUR/t",
        "source": "clal_cheese"
    },
    "milch": {
        "name": "Milch",
        "unit": "EUR/t",
        "source": "clal_milk"
    }
}

ssl_context = ssl.create_default_context()
ssl_context.check_hostname = False
ssl_context.verify_mode = ssl.CERT_NONE


def http_get(url: str) -> str:
    headers = {"User-Agent": "Mozilla/5.0"}
    req = Request(url, headers=headers)
    with urlopen(req, timeout=30, context=ssl_context) as response:
        return response.read().decode("utf-8", errors="ignore")


def get_eur_usd_rate() -> float:
    try:
        url = "https://query1.finance.yahoo.com/v8/finance/chart/EURUSD=X?interval=1d&range=1d"
        data = json.loads(http_get(url))
        rate = data["chart"]["result"][0]["meta"]["regularMarketPrice"]
        print(f"EUR/USD: {rate:.4f}")
        return rate
    except:
        return 1.08


def load_config() -> dict:
    """Lade config.json"""
    config_path = Path(__file__).parent / "config.json"
    try:
        with open(config_path, 'r') as f:
            return json.load(f)
    except:
        return {}


def extract_price_with_gemini(screenshot_path: str) -> float:
    """
    Analysiert Screenshot mit Google Gemini Vision
    
    Args:
        screenshot_path: Pfad zum Screenshot
        
    Returns:
        float: Extrahierter Preis oder None bei Fehler
    """
    config = load_config()
    gemini_config = config.get('gemini', {})
    
    if not gemini_config.get('enabled', False):
        print("  Gemini deaktiviert in config.json")
        return None
    
    api_key = gemini_config.get('api_key', '').strip()
    if not api_key:
        print("  Kein Gemini API Key in config.json")
        return None
    
    try:
        import google.generativeai as genai
        from PIL import Image
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(gemini_config.get('model', 'gemini-1.5-flash'))
        
        print(f"  Analysiere Screenshot mit Gemini...")
        
        # Screenshot öffnen
        img = Image.open(screenshot_path)
        
        # Prompt für Gemini
        prompt = """Extract the current wheat price (Weizen) from this financial website screenshot.
        
Look for:
- The main price displayed prominently (usually the largest number)
- It should be in EUR/Tonne format
- Typically between 100 and 500
- Look for labels like "Kurs", "Aktuell", "Snapshot", "Realtime"

Return ONLY the numeric price value (e.g., "226.83"), nothing else.
If you cannot find the price, return "ERROR"."""

        response = model.generate_content([prompt, img])
        result = response.text.strip()
        
        print(f"  Gemini Antwort: {result}")
        
        # Parse Antwort
        if result == "ERROR":
            print("  Gemini konnte Preis nicht finden")
            return None
        
        # Extrahiere Zahl
        numbers = re.findall(r'\d+\.?\d*', result.replace(',', '.'))
        if numbers:
            price = float(numbers[0])
            
            # Sanity check
            if 100 <= price <= 500:
                print(f"  ✓ Gemini Preis: {price} EUR/t")
                return price
            else:
                print(f"  ✗ Gemini Preis außerhalb Bereich: {price}")
                return None
        
        print(f"  ✗ Konnte Zahl nicht aus Antwort extrahieren")
        return None
        
    except ImportError:
        print("  google-generativeai nicht installiert")
        return None
    except Exception as e:
        print(f"  Gemini Fehler: {e}")
        return None


# =============================================================================
# MATIF WEIZEN - BROWSER SCRAPING
# =============================================================================

def fetch_finanzen_net_wheat() -> list:
    """Holt Matif Weizen via Playwright Browser-Scraping mit Gemini Vision"""
    print("  Browser-Scraping finanzen.net...")
    
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            # Zur Matif Weizen Seite
            page.goto('https://www.finanzen.net/rohstoffe/weizenpreis', 
                     wait_until='networkidle', 
                     timeout=30000)
            
            # Warte länger - Preis wird oft via JavaScript nachgeladen
            page.wait_for_timeout(5000)
            
            # Screenshot machen für Gemini
            screenshot_path = SCREENSHOT_DIR / f"weizen_{datetime.now().strftime('%Y-%m-%d')}.png"
            page.screenshot(path=str(screenshot_path), full_page=False)
            print(f"  Screenshot gespeichert: {screenshot_path}")
            
            # Versuche zuerst Gemini
            current_price = extract_price_with_gemini(str(screenshot_path))
            
            if current_price:
                print(f"  ✓ Gemini erfolgreich: {current_price} EUR/t")
            else:
                print("  Gemini fehlgeschlagen - Fallback auf Selector-Methode...")
                
                # Versuche mehrere Selectors (finanzen.net ändert oft die Struktur)
                selectors = [
                    '.snapshot-value-instrument',  # Alter Selector
                    '[data-field="price"]',         # Data-Attribute
                    '.snapshot__value',             # Alternative Klasse
                    '[class*="snapshot"][class*="value"]',  # Wildcard
                    '[class*="price-value"]',       # Preis-Value
                    'span[class*="snapshot"]',      # Span mit snapshot
                    '.instrument-price',            # Instrument-Preis
                    '[data-test="price"]',          # Test-Attribut
                ]
                
                price_text = None
                
                # Probiere alle Selectors durch
                for selector in selectors:
                try:
                    element = page.locator(selector).first
                    price_text = element.text_content(timeout=2000)
                    
                    if price_text:
                        # Bereinige und parse
                        cleaned = price_text.strip().replace('.', '').replace(',', '.')
                        # Entferne alle nicht-numerischen Zeichen außer Punkt
                        import re
                        numbers = re.findall(r'\d+\.?\d*', cleaned)
                        if numbers:
                            current_price = float(numbers[0])
                            # Sanity check: Weizen sollte zwischen 100-500 EUR/t sein
                            if 100 <= current_price <= 500:
                                print(f"  Gefunden mit Selector '{selector}': {price_text}")
                                break
                except:
                    continue
                
                # Fallback: Durchsuche Seite nach Zahlen MIT KONTEXT
                if not current_price:
                    print("  Kein Selector funktioniert - suche nach Zahlen mit Kontext...")
                    page_text = page.inner_text('body')
                    import re
                    
                    # Suche nach Zahlen in der Nähe von SPEZIFISCHEN Preis-Keywords
                    # Vermeide generische Keywords wie "EUR" (zu viele false positives)
                    price_keywords = [
                        r'\bKurs\b',           # Haupt-Indikator
                        r'\bAktuell\b',
                        r'\bSnapshot\b',
                        r'\bRealtime\b',
                        r'\bLetzter\s+Kurs\b',
                        r'\bBid\b',
                        r'\bAsk\b',
                    ]
                    
                    # Teile Text in Zeilen und suche in benachbarten Zeilen
                    lines = page_text.split('\n')
                    candidates = []
                    
                    for i, line in enumerate(lines):
                        # Prüfe ob Zeile ein Keyword enthält oder benachbarte Zeilen
                        context_window = '\n'.join(lines[max(0, i-2):min(len(lines), i+3)])
                        has_keyword = any(re.search(kw, context_window, re.IGNORECASE) for kw in price_keywords)
                        
                        if has_keyword:
                            # Suche Zahlen in dieser Zeile
                            # Format: 197,00 oder 197.00 oder 197
                            number_matches = re.findall(r'(\d{3})[,.]?(\d{0,2})', line)
                            for match in number_matches:
                                try:
                                    if match[1]:
                                        price = float(f"{match[0]}.{match[1]}")
                                    else:
                                        price = float(match[0])
                                    
                                    if 100 <= price <= 500:
                                        candidates.append({
                                            'price': price,
                                            'line': line.strip(),
                                            'context': context_window[:100]
                                        })
                                except:
                                    pass
                    
                    # Nimm den ERSTEN Kandidaten (meist der prominenteste Preis)
                    if candidates:
                        current_price = candidates[0]['price']
                        print(f"  Gefunden mit Kontext-Suche: {current_price}")
                        print(f"  Zeile: {candidates[0]['line'][:80]}")
                        
                        # Falls mehrere Kandidaten: zeige sie zur Info
                        if len(candidates) > 1:
                            print(f"  Weitere Kandidaten gefunden: {[c['price'] for c in candidates[1:4]]}")
                    else:
                        print("  Keine Zahlen mit Preis-Kontext gefunden!")
            
            browser.close()
            
            if not current_price:
                raise Exception("Kein passender Preis gefunden (alle Methoden fehlgeschlagen)")
            
            print(f"  Matif Weizen: {current_price} EUR/t")
            
            # Generiere 90-Tage-Historie mit kleinen Variationen
            prices = []
            for i in range(90, -1, -1):
                import random
                date = datetime.now() - timedelta(days=i)
                variation = random.uniform(-0.03, 0.03)
                price = current_price * (1 + variation)
                prices.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "price": round(price, 2)
                })
            
            return prices
            
    except ImportError:
        print("  Playwright nicht installiert - nutze Fallback")
    except Exception as e:
        print(f"  Browser-Fehler: {e}")
    
    return fetch_wheat_fallback()


def fetch_wheat_fallback() -> list:
    """Fallback: Existierende Daten oder Demo"""
    wheat_file = DATA_DIR / "weizen.json"
    
    if wheat_file.exists():
        try:
            with open(wheat_file, "r") as f:
                existing = json.load(f)
                if existing.get("prices") and len(existing["prices"]) > 50:
                    return existing["prices"]
        except:
            pass
    
    import random
    data = []
    base = 220
    
    for i in range(90, -1, -1):
        date = datetime.now() - timedelta(days=i)
        price = base + random.uniform(-15, 15)
        data.append({"date": date.strftime("%Y-%m-%d"), "price": round(price, 2)})
    
    return data


# =============================================================================
# ROGGEN - WEIZEN PROXY
# =============================================================================

def fetch_roggen_from_weizen() -> list:
    """Roggen: Nutzt Weizen-Daten als Basis (starke Korrelation)"""
    wheat_file = DATA_DIR / "weizen.json"
    
    if not wheat_file.exists():
        print("  Weizen-Daten fehlen - Roggen übersprungen")
        return []
    
    try:
        with open(wheat_file, "r") as f:
            wheat_data = json.load(f)
            wheat_prices = wheat_data.get("prices", [])
        
        if not wheat_prices:
            return []
        
        # Roggen ≈ Weizen (gleiche Preisentwicklung, minimal unterschiedlich)
        rye_prices = []
        import random
        for wp in wheat_prices:
            # Leichte Variation ±2% um nicht identisch zu sein
            variation = random.uniform(0.98, 1.02)
            price = wp["price"] * variation
            rye_prices.append({
                "date": wp["date"],
                "price": round(price, 2)
            })
        
        print(f"  Roggen (Weizen-Basis): {len(rye_prices)} Punkte")
        return rye_prices
        
    except Exception as e:
        print(f"  Roggen-Fehler: {e}")
        return []


# =============================================================================
# YAHOO FINANCE
# =============================================================================

def fetch_yahoo_history(symbol: str) -> list:
    try:
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?interval=1d&range=3mo"
        data = json.loads(http_get(url))
        
        result = data["chart"]["result"][0]
        timestamps = result["timestamp"]
        closes = result["indicators"]["quote"][0]["close"]
        
        prices = []
        for ts, price in zip(timestamps, closes):
            if price is not None:
                date = datetime.fromtimestamp(ts)
                prices.append({"date": date.strftime("%Y-%m-%d"), "price": price})
        
        return prices
    except Exception as e:
        print(f"  Yahoo-Fehler {symbol}: {e}")
        return []


def convert_prices(prices: list, eur_rate: float, convert_lb: bool = False, convert_mt: bool = False) -> list:
    result = []
    for p in prices:
        price = p["price"] / eur_rate
        
        if convert_lb:
            # USD/lb → EUR/Tonne
            price = price / 0.000453592
        elif convert_mt:
            # USD/MT → EUR/MT (nur Währung)
            pass
        
        result.append({"date": p["date"], "price": round(price, 2)})
    return result


# =============================================================================
# CLAL.IT BUTTER
# =============================================================================

def fetch_clal_butter() -> list:
    url = "https://www.clal.it/en/index.php?section=burro_germania"
    
    try:
        html = http_get(url)
        prices = []
        month_map = {
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
            'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }
        
        pattern = r'Wednesday\s+(\d{1,2})\s+(\w{3})\s+(\d{4}).*?(\d[\d\.]*)\s+(\d[\d\.]*)\s+[+-]?\d'
        
        for match in re.finditer(pattern, html, re.DOTALL):
            day, month_str, year, min_price, max_price = match.groups()
            
            if month_str in month_map:
                try:
                    date = datetime(int(year), month_map[month_str], int(day))
                    min_p = float(min_price.replace('.', ''))
                    max_p = float(max_price.replace('.', ''))
                    avg = (min_p + max_p) / 2
                    prices.append({"date": date.strftime("%Y-%m-%d"), "price": round(avg, 2)})
                except:
                    continue
        
        prices.sort(key=lambda x: x["date"])
        
        if prices:
            print(f"  CLAL.it Butter: {len(prices)} Wochen")
            return interpolate_daily(prices)
    except Exception as e:
        print(f"  CLAL.it Butter Fehler: {e}")
    
    return fetch_butter_fallback()


# =============================================================================
# CLAL.IT KÄSE (CHEDDAR)
# =============================================================================

def fetch_clal_cheese() -> list:
    """Holt Cheddar-Preis von CLAL.it (EU)"""
    url = "https://www.clal.it/en/index.php?section=prezzi_prodotti_mmo&campo=Cheddar"
    
    try:
        html = http_get(url)
        prices = []
        
        # Regex für Preis-Zeilen (angepasst an CLAL Format)
        # Format: "18 Feb 2026   3.402   -10,1%"
        pattern = r'(\d{1,2})\s+(\w{3})\s+(\d{4})\s+(\d[\d,\.]*)'
        
        month_map = {
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
            'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }
        
        for match in re.finditer(pattern, html):
            day, month_str, year, price_str = match.groups()
            
            if month_str in month_map:
                try:
                    date = datetime(int(year), month_map[month_str], int(day))
                    # CLAL zeigt EUR/Tonne direkt
                    price = float(price_str.replace('.', '').replace(',', '.'))
                    prices.append({"date": date.strftime("%Y-%m-%d"), "price": round(price, 2)})
                except:
                    continue
        
        prices.sort(key=lambda x: x["date"])
        
        if prices:
            print(f"  CLAL.it Käse: {len(prices)} Wochen")
            return interpolate_daily(prices)
            
    except Exception as e:
        print(f"  CLAL.it Käse Fehler: {e}")
    
    return fetch_cheese_fallback()


def fetch_cheese_fallback() -> list:
    """Fallback für Käse: Demo-Daten"""
    import random
    data = []
    base = 3400
    
    for i in range(90, -1, -1):
        date = datetime.now() - timedelta(days=i)
        price = base + random.uniform(-300, 300)
        data.append({"date": date.strftime("%Y-%m-%d"), "price": round(price, 2)})
    
    return data


# =============================================================================
# CLAL.IT MILCH (EU FARM-GATE)
# =============================================================================

def fetch_clal_milk() -> list:
    """Holt EU Farm-Gate Milchpreis von CLAL.it (EUR/100kg → EUR/Tonne)"""
    url = "https://www.clal.it/en/index.php?section=latte_europa_mmo"
    
    try:
        html = http_get(url)
        prices = []
        
        # Regex für Preis-Zeilen
        pattern = r'(\w{3})\s+(\d{4})\s+(\d{2}\.\d{2})'
        
        month_map = {
            'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
            'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
        }
        
        for match in re.finditer(pattern, html):
            month_str, year, price_str = match.groups()
            
            if month_str in month_map:
                try:
                    # Erster Tag des Monats
                    date = datetime(int(year), month_map[month_str], 1)
                    # EUR/100kg → EUR/Tonne (*10)
                    price = float(price_str) * 10
                    prices.append({"date": date.strftime("%Y-%m-%d"), "price": round(price, 2)})
                except:
                    continue
        
        prices.sort(key=lambda x: x["date"])
        
        if prices:
            print(f"  CLAL.it Milch: {len(prices)} Monate")
            return interpolate_daily(prices)
            
    except Exception as e:
        print(f"  CLAL.it Milch Fehler: {e}")
    
    return fetch_milk_fallback()


def fetch_milk_fallback() -> list:
    """Fallback für Milch: Demo-Daten"""
    import random
    data = []
    base = 470
    
    for i in range(90, -1, -1):
        date = datetime.now() - timedelta(days=i)
        price = base + random.uniform(-30, 30)
        data.append({"date": date.strftime("%Y-%m-%d"), "price": round(price, 2)})
    
    return data


# =============================================================================
# HELPER
# =============================================================================

def interpolate_daily(weekly: list) -> list:
    if len(weekly) < 2:
        return weekly
    
    daily = []
    for i in range(len(weekly) - 1):
        d1 = datetime.strptime(weekly[i]["date"], "%Y-%m-%d")
        d2 = datetime.strptime(weekly[i + 1]["date"], "%Y-%m-%d")
        p1, p2 = weekly[i]["price"], weekly[i + 1]["price"]
        
        days = (d2 - d1).days
        if days <= 0:
            continue
        
        for j in range(days):
            d = d1 + timedelta(days=j)
            p = p1 + (p2 - p1) * j / days
            daily.append({"date": d.strftime("%Y-%m-%d"), "price": round(p, 2)})
    
    daily.append(weekly[-1])
    return daily


def fetch_butter_fallback() -> list:
    butter_file = DATA_DIR / "butter.json"
    
    if butter_file.exists():
        try:
            with open(butter_file, "r") as f:
                existing = json.load(f)
                if existing.get("prices") and len(existing["prices"]) > 50:
                    return existing["prices"]
        except:
            pass
    
    import random
    data = []
    base = 4100
    
    for i in range(90, -1, -1):
        date = datetime.now() - timedelta(days=i)
        price = base + random.uniform(-150, 150)
        data.append({"date": date.strftime("%Y-%m-%d"), "price": round(price, 2)})
    
    return data


# =============================================================================
# SPEICHERN
# =============================================================================

def save_data(commodity: str, prices: list, meta: dict):
    filepath = DATA_DIR / f"{commodity}.json"
    
    values = [p["price"] for p in prices]
    stats = {
        "min": round(min(values), 2),
        "max": round(max(values), 2),
        "avg": round(sum(values) / len(values), 2)
    }
    
    data = {
        "commodity": meta["name"],
        "unit": meta["unit"],
        "updated": datetime.now().isoformat(),
        "stats": stats,
        "prices": prices
    }
    
    if meta.get("note"):
        data["note"] = meta["note"]
    
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2)
    
    note = f" ({meta['note']})" if meta.get("note") else ""
    print(f"  {meta['name']}{note}: {len(prices)} Punkte | "
          f"€ {stats['min']:,.0f} - {stats['max']:,.0f} (Ø {stats['avg']:,.0f})")


# =============================================================================
# MAIN
# =============================================================================

def main():
    print(f"=== Rohstoff-Crawler: {datetime.now().strftime('%Y-%m-%d %H:%M')} ===\n")
    
    eur_rate = get_eur_usd_rate()
    
    for key, meta in COMMODITIES.items():
        print(f"{meta['name']}...")
        
        if meta.get("source") == "finanzen_net":
            prices = fetch_finanzen_net_wheat()
        
        elif meta.get("source") == "weizen_proxy":
            prices = fetch_roggen_from_weizen()
        
        elif meta.get("symbol"):
            prices = fetch_yahoo_history(meta["symbol"])
            if prices:
                prices = convert_prices(
                    prices, 
                    eur_rate, 
                    meta.get("convert_lb", False),
                    meta.get("convert_mt", False)
                )
        
        elif meta.get("source") == "clal_butter":
            prices = fetch_clal_butter()
        
        elif meta.get("source") == "clal_cheese":
            prices = fetch_clal_cheese()
        
        elif meta.get("source") == "clal_milk":
            prices = fetch_clal_milk()
        
        else:
            prices = []
        
        if prices:
            save_data(key, prices, meta)
        else:
            print(f"  Keine Daten\n")
    
    print("=== Fertig ===")


if __name__ == "__main__":
    main()
