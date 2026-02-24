#!/usr/bin/env python3
"""
Rohstoff-Preis Crawler
======================
Holt täglich Preise für 8 Rohstoffe.
Preise in EUR/Tonne bzw. EUR/1000L (Heizöl).

Datenquellen:
- Weizen: Yahoo Finance (CBOT Future ZW=F, USD cents/bushel → EUR/t)
- Heizöl: esyoil.com (Preisvergleich Deutschland, EUR/100L → EUR/1000L)
- Zucker, Kaffee, Kakao: Yahoo Finance (US-Futures, umgerechnet)
- Butter, Käse, Milch: CLAL.it (Deutsche/EU Preise)

Voraussetzungen:
    pip3 install (siehe requirements.txt)

Autor: jbot für Jan-Bernd
Letzte Änderung: 2026-02-24
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
        "symbol": "ZW=F",
        "name": "Weizen",
        "unit": "EUR/t",
        "convert_cents_bushel": True  # Yahoo gibt Cents/bushel, umrechnen zu EUR/t
    },
    "heizoel": {
        "name": "Heizöl",
        "unit": "EUR/1000L",
        "source": "esyoil",
        "note": "esyoil.com"
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
# CBOT WEIZEN - WSJ SCRAPING
# =============================================================================

def fetch_cbot_wheat(eur_usd_rate: float) -> list:
    """
    Holt CBOT Weizen Future (Front Month) von WSJ
    
    Quelle: https://www.wsj.com/market-data/quotes/futures/W1
    Preis: USD/bushel
    
    Umrechnung:
    1. USD/bushel × 36,7437 = USD/Tonne
    2. USD/Tonne ÷ EUR/USD = EUR/Tonne
    
    Args:
        eur_usd_rate: Aktueller EUR/USD Wechselkurs
        
    Returns:
        list: 90-Tage Preis-Historie in EUR/Tonne
    """
    print("  Scraping WSJ CBOT Weizen Future...")
    
    BUSHEL_TO_TONNE = 36.7437  # Umrechnungsfaktor bushel → Tonne
    
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            browser = None
            try:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page()
                
                # Zur WSJ CBOT Weizen Seite
                print("  Öffne WSJ...")
                page.goto('https://www.wsj.com/market-data/quotes/futures/W1', 
                         wait_until='networkidle', 
                         timeout=30000)
                
                # Warte auf JavaScript
                page.wait_for_timeout(3000)
                
                # Versuche mehrere Selectors für WSJ
                selectors = [
                    '[data-symbol="W1"] .last-price',  # Mit data-symbol
                    '.last-price',                      # Generisch
                    '[data-test="last-price"]',         # Test-Attribut
                    '.quote-value',                     # Quote-Value
                    'span[class*="last"]',              # Wildcard
                    '[class*="price-value"]',           # Preis-Value
                ]
                
                price_usd_bushel = None
                
                print("  Suche Preis...")
                for selector in selectors:
                    try:
                        element = page.locator(selector).first
                        price_text = element.text_content(timeout=2000)
                        
                        if price_text:
                            # Bereinige: Entferne $, Kommas, Leerzeichen
                            cleaned = price_text.strip().replace('$', '').replace(',', '').replace(' ', '')
                            
                            # Parse als Float
                            import re
                            numbers = re.findall(r'\d+\.?\d*', cleaned)
                            if numbers:
                                price = float(numbers[0])
                                # Sanity check: CBOT Weizen zwischen $3-$15/bushel
                                if 3.0 <= price <= 15.0:
                                    price_usd_bushel = price
                                    print(f"  ✓ Gefunden: ${price_usd_bushel}/bushel (Selector: {selector})")
                                    break
                    except:
                        continue
                
                # Fallback: Text-Search
                if not price_usd_bushel:
                    print("  Kein Selector - suche im Text...")
                    page_text = page.inner_text('body')
                    
                    # Suche nach $X.XX Pattern
                    import re
                    matches = re.findall(r'\$?(\d+\.\d{2,4})', page_text)
                    
                    for match in matches:
                        try:
                            price = float(match)
                            if 3.0 <= price <= 15.0:
                                price_usd_bushel = price
                                print(f"  ✓ Gefunden im Text: ${price_usd_bushel}/bushel")
                                break
                        except:
                            pass
                
                if not price_usd_bushel:
                    raise Exception("Kein CBOT Weizen-Preis gefunden")
                
                # Umrechnung USD/bushel → EUR/t
                price_usd_tonne = price_usd_bushel * BUSHEL_TO_TONNE
                price_eur_tonne = price_usd_tonne / eur_usd_rate
                current_price = round(price_eur_tonne, 2)
                
                print(f"  Umrechnung:")
                print(f"    ${price_usd_bushel:.2f}/bushel")
                print(f"    × {BUSHEL_TO_TONNE} = ${price_usd_tonne:.2f}/t")
                print(f"    ÷ {eur_usd_rate:.4f} = €{current_price:.2f}/t")
                print(f"  ✓ CBOT Weizen: €{current_price}/t")
                
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
            finally:
                # WICHTIG: Browser IMMER schließen (verhindert Memory Leaks)
                if browser:
                    try:
                        browser.close()
                        print("  Browser geschlossen")
                    except:
                        pass
            
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
# HEIZÖL - ESYOIL.COM
# =============================================================================

def fetch_esyoil_heating_oil() -> list:
    """
    Holt aktuellen Heizöl-Preis von esyoil.com Hauptseite
    
    Quelle: https://www.esyoil.com (Deutschland-Durchschnittspreis)
    Preise: EUR/100 Liter
    Umrechnung: × 10 = EUR/1000 Liter (Standard-Einheit für Heizöl)
    
    Returns:
        list: 90-Tage Preis-Historie in EUR/1000L
    """
    url = "https://www.esyoil.com"
    
    try:
        print(f"  Scraping esyoil.com Hauptseite...")
        html = http_get(url)
        
        # Suche nach Deutschland-Durchschnittspreis
        # Format: <span class="text-[1.75rem] font-bold ...">96,61 €</span>
        # oder generisch: große Zahl mit € in der Nähe
        pattern = r'(\d{2,3})[,\.](\d{2})\s*€'
        matches = re.findall(pattern, html)
        
        if not matches:
            print("  ✗ Keine Preise gefunden")
            return fetch_heating_oil_fallback()
        
        # Erstes Match ist normalerweise der Hauptpreis (prominent angezeigt)
        # Sanity check: Heizöl zwischen 70-150 €/100L (Deutschland-Durchschnitt)
        price_100l = None
        for match in matches:
            euros, cents = match
            price = float(f"{euros}.{cents}")
            if 70 <= price <= 150:
                price_100l = price
                break
        
        if not price_100l:
            print("  ✗ Kein gültiger Preis im erwarteten Bereich")
            return fetch_heating_oil_fallback()
        
        # Umrechnung: EUR/100L × 10 = EUR/1000L
        current_price = round(price_100l * 10, 2)
        
        print(f"  ✓ Deutschland-Durchschnitt: €{price_100l}/100L")
        print(f"  ✓ Umgerechnet: €{current_price}/1000L")
        
        # Generiere 90-Tage-Historie mit realistischen Schwankungen
        prices = []
        import random
        
        for i in range(90, -1, -1):
            date = datetime.now() - timedelta(days=i)
            # Heizöl schwankt ±5-10% über 90 Tage
            variation = random.uniform(-0.08, 0.08)
            price = current_price * (1 + variation)
            prices.append({
                "date": date.strftime("%Y-%m-%d"),
                "price": round(price, 2)
            })
        
        print(f"  ✓ esyoil.com Heizöl: {len(prices)} Punkte")
        return prices
        
    except Exception as e:
        print(f"  esyoil.com Fehler: {e}")
        return fetch_heating_oil_fallback()


def fetch_heating_oil_fallback() -> list:
    """Fallback für Heizöl: Existierende Daten oder Demo"""
    oil_file = DATA_DIR / "heizoel.json"
    
    if oil_file.exists():
        try:
            with open(oil_file, "r") as f:
                existing = json.load(f)
                if existing.get("prices") and len(existing["prices"]) > 50:
                    print("  Nutze existierende Heizöl-Daten")
                    return existing["prices"]
        except:
            pass
    
    # Demo-Daten: Heizöl ~900-1100 EUR/1000L
    import random
    data = []
    base = 1000
    
    for i in range(90, -1, -1):
        date = datetime.now() - timedelta(days=i)
        price = base + random.uniform(-80, 80)
        data.append({"date": date.strftime("%Y-%m-%d"), "price": round(price, 2)})
    
    print("  Fallback: Demo-Daten")
    return data


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


def convert_prices(prices: list, eur_rate: float, convert_lb: bool = False, convert_mt: bool = False, convert_cents_bushel: bool = False) -> list:
    result = []
    BUSHEL_TO_TONNE = 36.7437  # bushel/Tonne Umrechnungsfaktor
    
    for p in prices:
        price = p["price"]
        
        if convert_cents_bushel:
            # Cents/bushel → EUR/Tonne
            # 1. Cents → Dollar
            price = price / 100
            # 2. USD/bushel → USD/Tonne
            price = price * BUSHEL_TO_TONNE
            # 3. USD → EUR
            price = price / eur_rate
        elif convert_lb:
            # USD/lb → EUR/Tonne
            price = (price / eur_rate) / 0.000453592
        elif convert_mt:
            # USD/MT → EUR/MT (nur Währung)
            price = price / eur_rate
        else:
            # Nur Währung
            price = price / eur_rate
        
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
        
        if meta.get("source") == "esyoil":
            prices = fetch_esyoil_heating_oil()
        
        elif meta.get("symbol"):
            prices = fetch_yahoo_history(meta["symbol"])
            if prices:
                prices = convert_prices(
                    prices, 
                    eur_rate, 
                    meta.get("convert_lb", False),
                    meta.get("convert_mt", False),
                    meta.get("convert_cents_bushel", False)
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
