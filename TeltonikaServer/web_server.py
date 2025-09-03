import os
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
from tcp_server import get_all_log_files

# Pro vývoj použij lokální složku, pro produkci /data
DATA_DIR = '/data' if os.path.exists('/data') or os.environ.get('HA_ADDON') else './data'
LOG_FILE = os.path.join(DATA_DIR, 'tcp_data.log')

class LogHandler(BaseHTTPRequestHandler):
    """HTTP handler pro zobrazování logů"""
    
    def do_GET(self):
        try:
            self.send_response(200)
            self.send_header('Content-type', 'text/html; charset=utf-8')
            self.end_headers()
            
            # Zobrazit pouze logy
            content = self._get_logs_content()
            html = self._get_html_template(content)
            self.wfile.write(html.encode('utf-8'))
        except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError) as e:
            # Klient se odpojil předčasně - toto je normální a můžeme to ignorovat
            pass
        except Exception as e:
            # Jiné chyby logujeme
            print(f"Chyba ve web serveru: {e}")
    
    def _get_logs_content(self):
        """Vrátí obsah logů"""
        try:
            log_files = get_all_log_files()
            if log_files:
                all_lines = []
                file_info = []
                
                # Načti posledních 500 řádků ze všech log souborů
                for log_file in log_files:
                    if os.path.exists(log_file):
                        with open(log_file, 'r', encoding='utf-8') as f:
                            lines = f.readlines()
                            filename = os.path.basename(log_file)
                            file_info.append(f"=== {filename} ({len(lines)} řádků) ===\n")
                            all_lines.extend(file_info[-1:])
                            all_lines.extend(lines)
                            all_lines.append("\n")
                
                # Zobrazit posledních 500 řádků celkově
                recent_lines = all_lines[-500:] if len(all_lines) > 500 else all_lines
                log_content = ''.join(recent_lines)
                
                # Přidej info o souborech nahoře
                file_summary = f"Celkem {len(log_files)} log souborů:\n"
                for log_file in log_files:
                    filename = os.path.basename(log_file)
                    file_summary += f"• {filename}\n"
                content = file_summary + "\n" + "="*50 + "\n\n" + log_content
                return content
            else:
                return "Žádné log soubory zatím neexistují."
        except Exception as e:
            return f"Chyba při čtení logů: {e}"

    def _get_html_template(self, content):
        """Vrátí jednoduchý HTML template pouze pro logy"""
        return f"""<!DOCTYPE html>
<html>
<head>
    <title>Teltonika Server Logs</title>
    <meta charset="utf-8">
    <meta http-equiv="refresh" content="10">
    <style>
        body {{ font-family: monospace; margin: 20px; background: #f0f0f0; }}
        .header {{ background: #333; color: white; padding: 10px; margin-bottom: 20px; }}
        .content {{ background: white; padding: 15px; border: 1px solid #ccc; white-space: pre-wrap; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Teltonika Server Logs</h1>
        <p>Automatické obnovení každých 10 sekund | Posledních 500 řádků</p>
        <p>Aktualizováno: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    <div class="content">{content}</div>
</body>
</html>"""

    def log_message(self, format, *args):
        """Přepíšeme log_message aby se nelogovala normální HTTP requests"""
        # Nelogujeme normální GET requests, pouze chyby
        if not (args and len(args) > 1 and args[1] == '200'):
            print(f"Web server: {format % args}")

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