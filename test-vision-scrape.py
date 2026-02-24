#!/usr/bin/env python3
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    page.goto('https://www.finanzen.net/rohstoffe/weizenpreis', wait_until='networkidle', timeout=30000)
    page.wait_for_timeout(5000)
    page.screenshot(path='/tmp/wheat-finanzen.png', full_page=False)
    browser.close()
    print("/tmp/wheat-finanzen.png")
