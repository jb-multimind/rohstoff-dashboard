#!/usr/bin/env python3
"""
Simple HTTP Server für Rohstoff-Dashboard
Serviert statische Dateien (HTML + JSON)
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import os

class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="/app", **kwargs)
    
    def end_headers(self):
        # CORS headers für lokale Entwicklung
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()
    
    def log_message(self, format, *args):
        # Logging (optional reduzieren für Production)
        if not self.path.endswith('.json'):
            super().log_message(format, *args)

def run(server_class=HTTPServer, handler_class=DashboardHandler, port=8080):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Server läuft auf Port {port}...")
    print(f"Dashboard: http://localhost:{port}/dashboard/")
    httpd.serve_forever()

if __name__ == '__main__':
    run()
