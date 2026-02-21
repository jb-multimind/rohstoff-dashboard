#!/usr/bin/env python3
"""Debug: Zeige ALLE Zahlen mit Kontext von finanzen.net"""

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
    
    print("\n=== ALLE dreistelligen Zahlen mit Kontext ===\n")
    
    # Hole alle Text-Nodes
    all_text = page.inner_text('body')
    
    # Finde alle Zahlen mit Kontext (50 Zeichen vorher und nachher)
    lines = all_text.split('\n')
    
    for i, line in enumerate(lines):
        # Suche nach dreistelligen Zahlen
        matches = re.finditer(r'\b(\d{3})[,.]?(\d{0,2})\b', line)
        for match in matches:
            full_number = match.group(0)
            try:
                num = float(full_number.replace(',', '.'))
                if 100 <= num <= 500:  # Weizen-Bereich
                    # Zeige Kontext: vorherige und nächste Zeile
                    context_before = lines[i-1] if i > 0 else ""
                    context_after = lines[i+1] if i < len(lines)-1 else ""
                    
                    print(f"--- Zahl: {full_number} ({num}) ---")
                    if context_before.strip():
                        print(f"  Vorher:  {context_before.strip()}")
                    print(f"  Zeile:   {line.strip()}")
                    if context_after.strip():
                        print(f"  Nachher: {context_after.strip()}")
                    print()
            except:
                pass
    
    browser.close()
