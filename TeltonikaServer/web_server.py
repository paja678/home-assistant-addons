import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

# Pro vývoj použij lokální složku, pro produkci /data
DATA_DIR = '/data' if os.path.exists('/data') or os.environ.get('HA_ADDON') else './data'
LOG_FILE = os.path.join(DATA_DIR, 'tcp_data.log')

class LogHandler(BaseHTTPRequestHandler):
    """HTTP handler pro zobrazování logů"""
    
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        
        try:
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    # Zobrazit posledních 100 řádků
                    recent_lines = lines[-100:] if len(lines) > 100 else lines
                    log_content = ''.join(recent_lines)
            else:
                log_content = "Log soubor zatím neexistuje."
        except Exception as e:
            log_content = f"Chyba při čtení logu: {e}"
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>Teltonika Server Log</title>
    <meta charset="utf-8">
    <meta http-equiv="refresh" content="5">
    <style>
        body {{ font-family: monospace; margin: 20px; background: #f0f0f0; }}
        .header {{ background: #333; color: white; padding: 10px; margin-bottom: 20px; }}
        .log {{ background: white; padding: 15px; border: 1px solid #ccc; white-space: pre-wrap; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Teltonika Server Log</h1>
        <p>Automatické obnovení každých 5 sekund | Posledních 100 řádků</p>
        <p>Aktualizováno: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    <div class="log">{log_content}</div>
</body>
</html>"""
        
        self.wfile.write(html.encode('utf-8'))

def start_web_server(host='0.0.0.0', port=3031):
    """HTTP server pro zobrazování logů"""
    server = HTTPServer((host, port), LogHandler)
    print(f"Web server listening on {host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Web server shutting down...")
    finally:
        server.shutdown()

if __name__ == "__main__":
    start_web_server()