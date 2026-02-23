#!/usr/bin/env python3
"""Debug: Zeige was auf finanzen.net steht"""

from playwright.sync_api import sync_playwright
import re

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    print("Lade finanzen.net...")
    page.goto('https://www.finanzen.net/rohstoffe/weizenpreis', 
             wait_until='networkidle', 
             timeout=30000)
    
    page.wait_for_timeout(5000)
    
    print("\n=== Seiten-Titel ===")
    print(page.title())
    
    print("\n=== Erste 2000 Zeichen vom Body ===")
    body_text = page.inner_text('body')
    print(body_text[:2000])
    
    print("\n\n=== Suche nach Keywords ===")
    keywords = ['Kurs', 'Aktuell', 'Snapshot', 'EUR', 'Preis', 'Weizen']
    for kw in keywords:
        count = len(re.findall(kw, body_text, re.IGNORECASE))
        print(f"{kw}: {count}x gefunden")
    
    print("\n=== Alle dreistelligen Zahlen (100-500) ===")
    numbers = re.findall(r'\b(\d{3})[,.]?(\d{0,2})\b', body_text)
    found_prices = []
    for match in numbers:
        try:
            if match[1]:
                num = float(f"{match[0]}.{match[1]}")
            else:
                num = float(match[0])
            
            if 100 <= num <= 500:
                found_prices.append(num)
        except:
            pass
    
    print(f"Gefunden: {len(found_prices)} Zahlen zwischen 100-500")
    if found_prices:
        print(f"Erste 10: {found_prices[:10]}")
    else:
        print("KEINE Zahlen zwischen 100-500 gefunden!")
    
    browser.close()
