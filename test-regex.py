#!/usr/bin/env python3
"""Test der Kontext-Suche mit simuliertem finanzen.net Text"""

import re

# Simulierter Text von finanzen.net (wie er etwa aussehen könnte)
page_text = """
Weizen Preis
Navigation Menu
Werbung 250,00 EUR
Weitere Rohstoffe
Gold 315,75 EUR
Silber 280,50 EUR

Weizen (Matif)
ISIN: FR0011758151
Kurs
197,00 EUR
Stand: 21.02.2026

Tagesumsatz: 1.250 Kontrakte
Hoch: 199,50
Tief: 195,80

Chart anzeigen
Weitere Informationen
"""

print("=== TEST: Kontext-basierte Suche ===\n")

price_keywords = [
    r'\bKurs\b',
    r'\bAktuell\b',
    r'\bSnapshot\b',
    r'\bRealtime\b',
    r'\bLetzter\s+Kurs\b',
    r'\bBid\b',
    r'\bAsk\b',
]

lines = page_text.split('\n')
candidates = []

for i, line in enumerate(lines):
    # Kontext-Fenster: ±2 Zeilen
    context_window = '\n'.join(lines[max(0, i-2):min(len(lines), i+3)])
    has_keyword = any(re.search(kw, context_window, re.IGNORECASE) for kw in price_keywords)
    
    if has_keyword:
        # Suche Zahlen
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
                        'has_keyword': has_keyword
                    })
                    print(f"Kandidat gefunden: {price} EUR")
                    print(f"  Zeile: {line.strip()}")
                    print(f"  Kontext-Fenster:\n{context_window}\n")
            except:
                pass

print(f"\n=== ERGEBNIS ===")
print(f"Kandidaten gefunden: {len(candidates)}")
if candidates:
    print(f"Erster Kandidat (wird verwendet): {candidates[0]['price']} EUR")
    print(f"Alle Kandidaten: {[c['price'] for c in candidates]}")
    
    # Check: Ist 197 dabei und als erstes?
    prices = [c['price'] for c in candidates]
    if 197.0 in prices:
        if prices[0] == 197.0:
            print("\n✅ SUCCESS: 197 ist der erste Kandidat (korrekt!)")
        else:
            print(f"\n⚠️  WARNING: 197 gefunden, aber Position {prices.index(197.0)+1}, nicht erste!")
    else:
        print("\n❌ FAIL: 197 nicht gefunden!")
else:
    print("❌ Keine Kandidaten gefunden!")
