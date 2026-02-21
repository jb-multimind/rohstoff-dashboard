#!/usr/bin/env python3
"""
Simple HTTP Server für Rohstoff-Dashboard
Serviert statische Dateien (HTML + JSON) + API für Crawler-Refresh
"""

from http.server import HTTPServer, SimpleHTTPRequestHandler
import subprocess
import json
import os

class DashboardHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory="/app", **kwargs)
    
    def do_POST(self):
        """Handle POST requests für API endpoints"""
        if self.path == '/api/refresh':
            self.handle_refresh()
        else:
            self.send_error(404)
    
    def handle_refresh(self):
        """Startet den Crawler im Hintergrund"""
        try:
            # Starte Crawler asynchron
            subprocess.Popen(['/usr/local/bin/python3', '/app/crawler.py'],
                           stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = json.dumps({'status': 'ok', 'message': 'Crawler gestartet'})
            self.wfile.write(response.encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = json.dumps({'status': 'error', 'message': str(e)})
            self.wfile.write(response.encode())
    
    def end_headers(self):
        # CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()
    
    def log_message(self, format, *args):
        # Logging reduzieren
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
