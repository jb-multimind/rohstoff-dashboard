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
    
    def do_GET(self):
        """Handle GET requests - nur /dashboard/ und /data/ erlauben"""
        # Root redirect zu /dashboard/
        if self.path == '/' or self.path == '':
            self.send_response(301)
            self.send_header('Location', '/dashboard/')
            self.end_headers()
            return
        
        # API endpoints
        if self.path == '/api/settings':
            self.handle_settings_get()
            return
        
        # Nur bestimmte Pfade erlauben
        allowed_paths = ['/dashboard/', '/data/', '/config.json']
        if not any(self.path.startswith(p) for p in allowed_paths):
            self.send_error(403, "Forbidden")
            return
        
        # Standard GET handler
        super().do_GET()
    
    def do_POST(self):
        """Handle POST requests für API endpoints"""
        if self.path == '/api/refresh':
            self.handle_refresh()
        elif self.path == '/api/settings':
            self.handle_settings_post()
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
    
    def handle_settings_get(self):
        """Gibt aktuelle Einstellungen zurück (ohne API Key)"""
        try:
            with open('/app/config.json', 'r') as f:
                config = json.load(f)
            
            # API Key nicht zurückgeben (Sicherheit)
            gemini_config = config.get('gemini', {})
            has_key = bool(gemini_config.get('api_key', '').strip())
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = json.dumps({
                'gemini': {
                    'enabled': gemini_config.get('enabled', False),
                    'has_key': has_key,
                    'model': gemini_config.get('model', 'gemini-1.5-flash')
                }
            })
            self.wfile.write(response.encode())
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = json.dumps({'status': 'error', 'message': str(e)})
            self.wfile.write(response.encode())
    
    def handle_settings_post(self):
        """Speichert neue Einstellungen"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            # Lade aktuelle Config
            with open('/app/config.json', 'r') as f:
                config = json.load(f)
            
            # Update Gemini-Settings
            if 'gemini' in data:
                if 'gemini' not in config:
                    config['gemini'] = {}
                
                if 'enabled' in data['gemini']:
                    config['gemini']['enabled'] = data['gemini']['enabled']
                
                if 'api_key' in data['gemini']:
                    # Nur übernehmen wenn nicht leer
                    key = data['gemini']['api_key'].strip()
                    if key:
                        config['gemini']['api_key'] = key
                
                if 'model' in data['gemini']:
                    config['gemini']['model'] = data['gemini']['model']
            
            # Speichere Config
            with open('/app/config.json', 'w') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            response = json.dumps({'status': 'ok', 'message': 'Einstellungen gespeichert'})
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
