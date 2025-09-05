#!/usr/bin/env python3
"""
Teltonika AVL Protocol Implementation
Supports Codec8 and Codec8 Extended protocols
"""

import struct
import binascii
from datetime import datetime
from typing import Tuple, Optional, Dict, List, Any

def parse_imei(data: bytes) -> Optional[str]:
    """
    Parsuje IMEI handshake packet
    Format: [IMEI Length][IMEI]
    Příklad: 000F333536333037303432343431303133
    """
    try:
        if len(data) < 2:
            return None
            
        # Prvních 2 bytes = délka IMEI
        imei_length = struct.unpack('>H', data[:2])[0]
        
        if len(data) != 2 + imei_length:
            return None
            
        # IMEI jako ASCII string
        imei = data[2:2+imei_length].decode('ascii')
        return imei
    except Exception:
        return None

def calculate_crc16(data: bytes) -> int:
    """Vypočítá CRC16 pro AVL packet"""
    crc = 0
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF
    return crc

def parse_avl_record(data: bytes, offset: int) -> Tuple[Dict[str, Any], int]:
    """
    Parsuje jednotlivý AVL record
    Returns: (record_dict, new_offset)
    """
    record = {}
    
    # Timestamp (8 bytes) - Unix timestamp v ms
    timestamp_ms = struct.unpack('>Q', data[offset:offset+8])[0]
    try:
        # Teltonika timestamp je Unix timestamp v milisekundách od 1.1.1970
        # Validace rozsahu: roky 2000-2100 (946684800000 - 4102444800000 ms)
        if 946684800000 <= timestamp_ms <= 4102444800000:
            record['timestamp'] = datetime.fromtimestamp(timestamp_ms / 1000.0)
        else:
            # Neplatný timestamp - použij současný čas
            from datetime import datetime as dt
            ts = dt.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"[{ts}] Invalid timestamp {timestamp_ms}, using current time", flush=True)
            record['timestamp'] = datetime.now()
    except (ValueError, OSError) as e:
        from datetime import datetime as dt
        ts = dt.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{ts}] Error parsing timestamp {timestamp_ms}: {e}, using current time", flush=True)
        record['timestamp'] = datetime.now()
    offset += 8
    
    # Priority (1 byte)
    record['priority'] = struct.unpack('>B', data[offset:offset+1])[0]
    offset += 1
    
    # GPS Data (15 bytes)
    if offset + 15 > len(data):
        print(f"Not enough data for GPS at offset {offset}, need 15 bytes, have {len(data) - offset}")
        return None, offset
    gps_data = struct.unpack('>iiHHBH', data[offset:offset+15])  # Changed last part to BH instead of Hbb
    record['gps'] = {
        'longitude': gps_data[0] / 10000000.0,  # Degrees * 10^7
        'latitude': gps_data[1] / 10000000.0,   # Degrees * 10^7
        'altitude': gps_data[2],                # Meters
        'angle': gps_data[3],                   # Degrees
        'satellites': gps_data[4],              # Count
        'speed': gps_data[5]                    # km/h
    }
    offset += 15
    
    # I/O Data
    io_event_id = struct.unpack('>B', data[offset:offset+1])[0]
    record['io_event'] = io_event_id
    offset += 1
    
    # Total I/O elements
    io_elements = struct.unpack('>B', data[offset:offset+1])[0]
    record['io_count'] = io_elements
    offset += 1
    
    record['io_data'] = {}
    
    # 1-byte I/O elements
    if offset < len(data):
        count_1b = struct.unpack('>B', data[offset:offset+1])[0]
        offset += 1
        for _ in range(count_1b):
            if offset + 2 <= len(data):
                io_id = struct.unpack('>B', data[offset:offset+1])[0]
                io_value = struct.unpack('>B', data[offset+1:offset+2])[0]
                record['io_data'][io_id] = io_value
                offset += 2
    
    # 2-byte I/O elements
    if offset < len(data):
        count_2b = struct.unpack('>B', data[offset:offset+1])[0]
        offset += 1
        for _ in range(count_2b):
            if offset + 3 <= len(data):
                io_id = struct.unpack('>B', data[offset:offset+1])[0]
                io_value = struct.unpack('>H', data[offset+1:offset+3])[0]
                record['io_data'][io_id] = io_value
                offset += 3
    
    # 4-byte I/O elements
    if offset < len(data):
        count_4b = struct.unpack('>B', data[offset:offset+1])[0]
        offset += 1
        for _ in range(count_4b):
            if offset + 5 <= len(data):
                io_id = struct.unpack('>B', data[offset:offset+1])[0]
                io_value = struct.unpack('>I', data[offset+1:offset+5])[0]
                record['io_data'][io_id] = io_value
                offset += 5
    
    # 8-byte I/O elements  
    if offset < len(data):
        count_8b = struct.unpack('>B', data[offset:offset+1])[0]
        offset += 1
        for _ in range(count_8b):
            if offset + 9 <= len(data):
                io_id = struct.unpack('>B', data[offset:offset+1])[0]
                io_value = struct.unpack('>Q', data[offset+1:offset+9])[0]
                record['io_data'][io_id] = io_value
                offset += 9
    
    return record, offset

def parse_avl_packet_with_length(data: bytes) -> Tuple[Optional[List[Dict[str, Any]]], int, str, int]:
    """
    Parsuje AVL packet a vrací i jeho celkovou délku
    Returns: (records_list, record_count, codec_type, packet_length)
    """
    try:
        if len(data) < 16:
            return None, 0, "unknown", 0
        
        # Standardní Teltonika AVL packet struktura
        # Preamble (4 bytes) - měly by být nuly
        if data[0:4] != b'\x00\x00\x00\x00':
            return None, 0, "unknown", 0
            
        # Data field length (4 bytes)
        data_length = struct.unpack('>I', data[4:8])[0]
        
        # Validace délky
        if data_length < 10 or data_length > 10000:
            return None, 0, "unknown", 0
            
        # Celková délka packetu: preamble(4) + length(4) + data + CRC(4)
        total_packet_length = 8 + data_length + 4
        
        # Kontrola zda máme dostatek dat
        if len(data) < total_packet_length:
            print(f"Incomplete packet: need {total_packet_length} bytes, have {len(data)}")
            return None, 0, "unknown", 0
        
        # Codec ID (1 byte)
        codec_id = data[8]
        codec_type = "codec8" if codec_id == 0x08 else "codec8_extended" if codec_id == 0x8E else f"unknown_{codec_id}"
        
        # Number of records (1 byte)
        record_count = data[9]
        
        if codec_id not in [0x08, 0x8E] or record_count == 0:
            return None, 0, codec_type, 0
            
        # Parse records
        records = []
        offset = 10  # After header
        
        for i in range(record_count):
            if offset + 34 > len(data):  # Minimum record size
                break
                
            try:
                record, new_offset = parse_avl_record(data, offset)
                if record:
                    records.append(record)
                    offset = new_offset
                else:
                    break
            except Exception as e:
                from datetime import datetime as dt
                ts = dt.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"[{ts}] Error parsing record {i}: {e}", flush=True)
                break
        
        return records, len(records), codec_type, total_packet_length
        
    except Exception as e:
        print(f"Error in parse_avl_packet_with_length: {e}")
        return None, 0, "error", 0

def parse_avl_packet(data: bytes) -> Tuple[Optional[List[Dict[str, Any]]], int, str]:
    """
    Parsuje celý AVL packet s robustním hledáním struktury
    Returns: (records_list, record_count, codec_type)
    """
    try:
        if len(data) < 16:
            return None, 0, "unknown"
        
        # Zkus najít správnou AVL strukturu na různých pozicích
        for start_offset in [0, 4, 8, 16]:
            if start_offset + 16 > len(data):
                continue
                
            try:
                # Zkus parsovat jako standardní AVL packet
                preamble = struct.unpack('>I', data[start_offset:start_offset+4])[0]
                data_length = struct.unpack('>I', data[start_offset+4:start_offset+8])[0]
                codec_id = struct.unpack('>B', data[start_offset+8:start_offset+9])[0]
                record_count = struct.unpack('>B', data[start_offset+9:start_offset+10])[0]
                
                # Validace
                if (codec_id in [0x08, 0x8E] and 
                    record_count > 0 and record_count < 100 and
                    data_length > 0 and data_length < 100000):
                    
                    codec_type = "codec8" if codec_id == 0x08 else "codec8_extended"
                    print(f"Found valid AVL structure at offset {start_offset}: codec={codec_id:02X}, count={record_count}")
                    
                    if record_count == 0:
                        return [], 0, codec_type
                    
                    # Parse records starting after header
                    records = []
                    offset = start_offset + 10
                    
                    for i in range(record_count):
                        if offset + 34 > len(data):
                            break
                            
                        try:
                            record, new_offset = parse_avl_record(data, offset)
                            if record:
                                records.append(record)
                                offset = new_offset
                            else:
                                break
                        except Exception as e:
                            print(f"Error parsing record {i} at offset {offset}: {e}")
                            break
                    
                    return records, len(records), codec_type
                    
            except Exception as e:
                continue
        
        # Pokud nenajdeme validní strukturu, vrátíme chybu
        print(f"No valid AVL structure found in {len(data)} bytes")
        return None, 0, "unknown"
        
    except Exception as e:
        print(f"Chyba při parsování AVL packet: {e}")
        return None, 0, "error"

def format_record_for_log(record: Dict[str, Any], imei: str = "") -> str:
    """Zformátuje AVL record pro log soubor"""
    timestamp = record['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
    gps = record['gps']
    
    log_entry = f"IMEI: {imei} | "
    log_entry += f"Time: {timestamp} | "
    log_entry += f"GPS: {gps['latitude']:.6f},{gps['longitude']:.6f} | "
    log_entry += f"Speed: {gps['speed']}km/h | "
    log_entry += f"Altitude: {gps['altitude']}m | "
    log_entry += f"Angle: {gps['angle']}° | "
    log_entry += f"Sats: {gps['satellites']} | "
    log_entry += f"Priority: {record['priority']} | "
    log_entry += f"IO: {len(record['io_data'])} elements"
    
    if record['io_data']:
        io_str = ", ".join([f"{k}={v}" for k, v in record['io_data'].items()])
        log_entry += f" [{io_str}]"
    
    return log_entry

def get_io_description(io_id: int) -> str:
    """Vrátí popis I/O elementu podle ID"""
    descriptions = {
        1: "Digital Input 1",
        9: "Analog Input 1", 
        11: "iButton ID",
        66: "External Voltage",
        67: "Battery Voltage",
        68: "Battery Current",
        69: "Fuel Level 1",
        181: "GSM Signal",
        182: "Sleep Mode",
        200: "Deep Sleep",
        239: "Ignition",
        240: "Movement Sensor",
        241: "Active GSM Operator",
        # Přidej další podle potřeby
    }
    return descriptions.get(io_id, f"Unknown IO {io_id}")