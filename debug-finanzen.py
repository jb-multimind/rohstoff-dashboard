#!/usr/bin/env python3
"""
Debug Script für finanzen.net HTML-Struktur
"""

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    print("Lade finanzen.net...")
    page.goto('https://www.finanzen.net/rohstoffe/weizenpreis', 
             wait_until='networkidle', 
             timeout=30000)
    
    page.wait_for_timeout(3000)
    
    print("\n=== Alle Klassen mit 'snapshot' ===")
    snapshot_elements = page.query_selector_all('[class*="snapshot"]')
    for i, el in enumerate(snapshot_elements[:10]):
        print(f"{i}. {el.get_attribute('class')}: {el.text_content()[:50]}")
    
    print("\n=== Alle Klassen mit 'value' ===")
    value_elements = page.query_selector_all('[class*="value"]')
    for i, el in enumerate(value_elements[:10]):
        print(f"{i}. {el.get_attribute('class')}: {el.text_content()[:50]}")
    
    print("\n=== Alle Klassen mit 'price' oder 'kurs' ===")
    price_elements = page.query_selector_all('[class*="price"], [class*="kurs"], [class*="Price"], [class*="Kurs"]')
    for i, el in enumerate(price_elements[:10]):
        print(f"{i}. {el.get_attribute('class')}: {el.text_content()[:50]}")
    
    print("\n=== Großer Text (wahrscheinlich Preis) ===")
    big_text = page.query_selector_all('span, div')
    for el in big_text:
        text = el.text_content().strip()
        # Suche nach Zahlen mit Komma (deutscher Preis-Format)
        if ',' in text and len(text) < 20:
            try:
                # Könnte ein Preis sein
                num = float(text.replace('.', '').replace(',', '.'))
                if 100 < num < 300:  # Weizen-Preis Bereich
                    print(f"Möglicher Preis: {text} | Klasse: {el.get_attribute('class')}")
            except:
                pass
    
    browser.close()
