#!/usr/bin/env python3
"""CSV Logger for Teltonika GPS data"""

import csv
import os
from datetime import datetime
from collections import deque


class CSVLogger:
    def __init__(self, base_dir='/share/teltonika'):
        self.base_dir = base_dir
        self.devices_dir = os.path.join(base_dir, 'devices')
        self.server_log = os.path.join(base_dir, 'server.log')
        self.csv_headers = ['timestamp', 'latitude', 'longitude', 'speed', 
                           'altitude', 'satellites', 'angle', 'io_data']
        
        # Vytvoř základní strukturu
        os.makedirs(self.devices_dir, exist_ok=True)
        os.makedirs(os.path.dirname(self.server_log), exist_ok=True)
    
    def log_server_event(self, message):
        """Zaloguje událost do hlavního server logu"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(self.server_log, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {message}\n")
    
    def log_raw_data(self, client_address, imei, hex_data):
        """Zaloguje RAW hex data do server logu"""
        # Ořež hex data pokud jsou moc dlouhá (zobrazí prvních 200 znaků)
        if len(hex_data) > 200:
            hex_data = hex_data[:200] + '...'
        
        message = f"RAW DATA from {client_address} (IMEI: {imei or 'unknown'}): {hex_data}"
        self.log_server_event(message)
    
    def log_gps_record(self, imei, record):
        """Zaloguje GPS záznam do CSV souboru zařízení"""
        device_dir = os.path.join(self.devices_dir, imei)
        os.makedirs(device_dir, exist_ok=True)
        
        csv_file = os.path.join(device_dir, 'data.csv')
        
        # Zkontroluj jestli soubor existuje
        file_exists = os.path.exists(csv_file)
        
        with open(csv_file, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            
            # Přidej hlavičku pro nový soubor
            if not file_exists:
                writer.writerow(self.csv_headers)
            
            # Připrav data záznamu
            gps = record['gps']
            timestamp = record.get('timestamp', datetime.now())
            if isinstance(timestamp, datetime):
                timestamp = timestamp.strftime('%Y-%m-%d %H:%M:%S')
            
            # Formátuj I/O data jako string
            io_str = ""
            if 'io_data' in record and record['io_data']:
                io_items = []
                for key, value in record['io_data'].items():
                    # Mapování známých I/O klíčů podle Teltonika dokumentace
                    if key == 239:  # Ignition
                        io_items.append(f"ignition={value}")
                    elif key == 66:  # External voltage (mV)
                        io_items.append(f"battery={value/1000:.1f}V")
                    elif key == 21:  # GSM signal strength
                        io_items.append(f"gsm_signal={value}")
                    elif key == 200:  # Sleep mode
                        io_items.append(f"sleep={value}")
                    elif key == 69:  # GPS power
                        io_items.append(f"gps_power={value}")
                    elif key == 1:  # Digital input 1
                        io_items.append(f"din1={value}")
                    else:
                        io_items.append(f"io{key}={value}")
                io_str = ",".join(io_items)
            
            # Vytvoř CSV řádek
            row = [
                timestamp,
                f"{gps['latitude']:.6f}",
                f"{gps['longitude']:.6f}", 
                gps.get('speed', 0),
                gps.get('altitude', 0),
                gps.get('satellites', 0),
                gps.get('angle', 0),
                io_str
            ]
            writer.writerow(row)
    
    def read_last_records(self, imei, count=2000):
        """Načte posledních N záznamů z CSV"""
        csv_file = os.path.join(self.devices_dir, imei, 'data.csv')
        
        if not os.path.exists(csv_file):
            return []
        
        # Použij deque pro efektivní držení posledních N řádků
        last_records = deque(maxlen=count)
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    last_records.append(row)
        except Exception as e:
            print(f"Error reading CSV for {imei}: {e}")
            return []
        
        return list(last_records)
    
    def get_all_devices(self):
        """Vrátí seznam všech IMEI zařízení"""
        devices = []
        try:
            if os.path.exists(self.devices_dir):
                for dirname in os.listdir(self.devices_dir):
                    device_dir = os.path.join(self.devices_dir, dirname)
                    if os.path.isdir(device_dir) and dirname.isdigit():
                        # Zkontroluj jestli má CSV soubor
                        csv_file = os.path.join(device_dir, 'data.csv')
                        if os.path.exists(csv_file):
                            devices.append({
                                'imei': dirname,
                                'last_seen': self._get_last_seen(dirname),
                                'record_count': self._get_record_count(dirname)
                            })
        except Exception as e:
            print(f"Error getting devices: {e}")
        
        return sorted(devices, key=lambda x: x['imei'])
    
    def _get_last_seen(self, imei):
        """Získej čas posledního záznamu"""
        try:
            records = self.read_last_records(imei, 1)
            if records:
                return records[-1]['timestamp']
        except:
            pass
        return "Unknown"
    
    def _get_record_count(self, imei):
        """Spočítej celkový počet záznamů"""
        csv_file = os.path.join(self.devices_dir, imei, 'data.csv')
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                # Počítej řádky kromě hlavičky
                return sum(1 for line in f) - 1
        except:
            return 0
    
    def get_server_log_tail(self, lines=2000):
        """Načte posledních N řádků server logu"""
        if not os.path.exists(self.server_log):
            return "No server log available"
        
        try:
            with open(self.server_log, 'r', encoding='utf-8') as f:
                all_lines = f.readlines()
                # Posledních N řádků
                recent_lines = all_lines[-lines:] if len(all_lines) > lines else all_lines
                return ''.join(recent_lines)
        except Exception as e:
            return f"Error reading server log: {e}"
    
    def create_device_info(self, imei):
        """Vytvoří info.json pro zařízení"""
        device_dir = os.path.join(self.devices_dir, imei)
        os.makedirs(device_dir, exist_ok=True)
        
        info_file = os.path.join(device_dir, 'info.json')
        if not os.path.exists(info_file):
            info = {
                'imei': imei,
                'first_seen': datetime.now().isoformat(),
                'device_name': f"Device {imei}",
                'notes': ""
            }
            
            import json
            with open(info_file, 'w', encoding='utf-8') as f:
                json.dump(info, f, indent=2)