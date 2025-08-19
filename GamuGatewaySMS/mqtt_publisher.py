"""
MQTT Publisher for SMS Gammu Gateway
Publishes SMS and device status to MQTT broker with Home Assistant auto-discovery
"""

import json
import time
import logging
import threading
from typing import Optional, Dict, Any
import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)

class MQTTPublisher:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client: Optional[mqtt.Client] = None
        self.connected = False
        self.topic_prefix = config.get('mqtt_topic_prefix', 'homeassistant/sensor/sms_gateway')
        self.gammu_machine = None  # Will be set externally
        
        if config.get('mqtt_enabled', False):
            self._setup_client()
    
    def set_gammu_machine(self, machine):
        """Set gammu machine for SMS sending"""
        self.gammu_machine = machine
        logger.info("Gammu machine set for MQTT SMS sending")
    
    def _setup_client(self):
        """Setup MQTT client with configuration"""
        try:
            self.client = mqtt.Client()
            
            # Set credentials if provided
            username = self.config.get('mqtt_username')
            password = self.config.get('mqtt_password')
            if username:
                self.client.username_pw_set(username, password)
            
            # Set callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_publish = self._on_publish
            self.client.on_message = self._on_message
            
            # Connect to broker
            host = self.config.get('mqtt_host', 'core-mosquitto')
            port = self.config.get('mqtt_port', 1883)
            
            logger.info(f"Connecting to MQTT broker: {host}:{port}")
            self.client.connect(host, port, 60)
            self.client.loop_start()
            
        except Exception as e:
            logger.error(f"Failed to setup MQTT client: {e}")
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback for MQTT connection"""
        if rc == 0:
            self.connected = True
            logger.info("Connected to MQTT broker")
            self._publish_discovery_configs()
            # Subscribe to SMS send command topic
            send_topic = f"{self.topic_prefix}/send"
            client.subscribe(send_topic)
            logger.info(f"Subscribed to SMS send topic: {send_topic}")
            
            # Subscribe to SMS button topic
            button_topic = f"{self.topic_prefix}/send_button"
            client.subscribe(button_topic)
            logger.info(f"Subscribed to SMS button topic: {button_topic}")
        else:
            logger.error(f"Failed to connect to MQTT broker: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for MQTT disconnection"""
        self.connected = False
        logger.warning("Disconnected from MQTT broker")
    
    def _on_publish(self, client, userdata, mid):
        """Callback for published messages"""
        pass
    
    def _on_message(self, client, userdata, msg):
        """Callback for received MQTT messages"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            logger.info(f"Received MQTT message on topic {topic}: {payload}")
            
            # Check if it's SMS send command
            send_topic = f"{self.topic_prefix}/send"
            button_topic = f"{self.topic_prefix}/send_button"
            
            if topic == send_topic:
                self._handle_sms_send_command(payload)
            elif topic == button_topic and payload == "PRESS":
                # Button pressed - for now just show notification
                # In a real implementation, you'd want to open a dialog or use HA service
                logger.info("SMS Send button pressed - use MQTT topic or service to send SMS")
                self._publish_button_press_notification()
                
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
    
    def _handle_sms_send_command(self, payload):
        """Handle SMS send command from MQTT"""
        try:
            # Parse JSON payload
            data = json.loads(payload)
            number = data.get('number')
            text = data.get('text')
            
            if not number or not text:
                logger.error("SMS send command missing required fields: number or text")
                return
            
            logger.info(f"Processing SMS send command: {number} -> {text}")
            
            # Send SMS via gammu machine (will be set externally)
            if hasattr(self, 'gammu_machine') and self.gammu_machine:
                self._send_sms_via_gammu(number, text)
            else:
                logger.error("Gammu machine not available for SMS sending")
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in SMS send command: {e}")
        except Exception as e:
            logger.error(f"Error handling SMS send command: {e}")
    
    def _send_sms_via_gammu(self, number, text):
        """Send SMS using gammu machine"""
        try:
            # Import gammu and support functions
            from support import encodeSms
            
            # Prepare SMS info
            smsinfo = {
                "Class": -1,
                "Unicode": False,
                "Entries": [
                    {
                        "ID": "ConcatenatedTextLong",
                        "Buffer": text,
                    }
                ],
            }
            
            # Encode and send SMS
            messages = encodeSms(smsinfo)
            for message in messages:
                message["SMSC"] = {'Location': 1}
                message["Number"] = number
                result = self.gammu_machine.SendSMS(message)
                logger.info(f"SMS sent successfully: {result}")
                
            # Publish confirmation
            if self.connected:
                status_topic = f"{self.topic_prefix}/send_status"
                status_data = {
                    "status": "success",
                    "number": number,
                    "text": text,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                self.client.publish(status_topic, json.dumps(status_data), retain=False)
                
        except Exception as e:
            logger.error(f"Failed to send SMS via gammu: {e}")
            # Publish error status
            if self.connected:
                status_topic = f"{self.topic_prefix}/send_status"
                status_data = {
                    "status": "error",
                    "error": str(e),
                    "number": number,
                    "text": text,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                }
                self.client.publish(status_topic, json.dumps(status_data), retain=False)
    
    def _publish_button_press_notification(self):
        """Publish notification when SMS send button is pressed"""
        if self.connected:
            status_topic = f"{self.topic_prefix}/send_status"
            status_data = {
                "status": "button_pressed",
                "message": "Use MQTT topic or Home Assistant service to send SMS",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            self.client.publish(status_topic, json.dumps(status_data), retain=False)
            logger.info("Published button press notification")
    
    def _publish_discovery_configs(self):
        """Publish Home Assistant auto-discovery configurations"""
        if not self.connected:
            return
            
        # Signal strength sensor
        signal_config = {
            "name": "GSM Signal Strength",
            "unique_id": "sms_gateway_signal",
            "state_topic": f"{self.topic_prefix}/signal/state",
            "value_template": "{{ value_json.SignalPercent }}",
            "unit_of_measurement": "%",
            "device_class": "signal_strength",
            "icon": "mdi:signal-cellular-3",
            "device": {
                "identifiers": ["sms_gateway"],
                "name": "SMS Gateway",
                "model": "GSM Modem",
                "manufacturer": "Gammu Gateway"
            }
        }
        
        # Network info sensor
        network_config = {
            "name": "GSM Network",
            "unique_id": "sms_gateway_network",
            "state_topic": f"{self.topic_prefix}/network/state",
            "value_template": "{{ value_json.NetworkName }}",
            "icon": "mdi:network",
            "device": {
                "identifiers": ["sms_gateway"],
                "name": "SMS Gateway",
                "model": "GSM Modem", 
                "manufacturer": "Gammu Gateway"
            }
        }
        
        # Last SMS sensor
        sms_config = {
            "name": "Last SMS Received",
            "unique_id": "sms_gateway_last_sms",
            "state_topic": f"{self.topic_prefix}/sms/state",
            "value_template": "{{ value_json.Text }}",
            "json_attributes_topic": f"{self.topic_prefix}/sms/state",
            "icon": "mdi:message-text",
            "device": {
                "identifiers": ["sms_gateway"],
                "name": "SMS Gateway",
                "model": "GSM Modem",
                "manufacturer": "Gammu Gateway"
            }
        }
        
        # SMS send status sensor
        send_status_config = {
            "name": "SMS Send Status",
            "unique_id": "sms_gateway_send_status",
            "state_topic": f"{self.topic_prefix}/send_status",
            "value_template": "{{ value_json.status }}",
            "json_attributes_topic": f"{self.topic_prefix}/send_status",
            "icon": "mdi:send",
            "device": {
                "identifiers": ["sms_gateway"],
                "name": "SMS Gateway",
                "model": "GSM Modem",
                "manufacturer": "Gammu Gateway"
            }
        }
        
        # SMS send button
        button_config = {
            "name": "Send SMS",
            "unique_id": "sms_gateway_send_button",
            "command_topic": f"{self.topic_prefix}/send_button",
            "payload_press": "PRESS",
            "icon": "mdi:message-plus",
            "device": {
                "identifiers": ["sms_gateway"],
                "name": "SMS Gateway",
                "model": "GSM Modem",
                "manufacturer": "Gammu Gateway"
            }
        }
        
        # Publish discovery configs
        discoveries = [
            ("homeassistant/sensor/sms_gateway_signal/config", signal_config),
            ("homeassistant/sensor/sms_gateway_network/config", network_config),
            ("homeassistant/sensor/sms_gateway_last_sms/config", sms_config),
            ("homeassistant/sensor/sms_gateway_send_status/config", send_status_config),
            ("homeassistant/button/sms_gateway_send_button/config", button_config)
        ]
        
        for topic, config in discoveries:
            self.client.publish(topic, json.dumps(config), retain=True)
        
        logger.info("Published MQTT discovery configurations including SMS send button")
        
        # Publish initial states immediately after discovery
        self._publish_initial_states()
    
    def publish_signal_strength(self, signal_data: Dict[str, Any]):
        """Publish signal strength data"""
        if not self.connected:
            return
            
        topic = f"{self.topic_prefix}/signal/state"
        self.client.publish(topic, json.dumps(signal_data), retain=True)
        logger.info(f"📡 Published signal strength to MQTT: {signal_data.get('SignalPercent', 'N/A')}%")
    
    def publish_network_info(self, network_data: Dict[str, Any]):
        """Publish network information"""
        if not self.connected:
            return
            
        topic = f"{self.topic_prefix}/network/state"
        self.client.publish(topic, json.dumps(network_data), retain=True)
        logger.info(f"📡 Published network info to MQTT: {network_data.get('NetworkName', 'Unknown')}")
    
    def publish_sms_received(self, sms_data: Dict[str, Any]):
        """Publish received SMS data"""
        if not self.connected:
            return
            
        # Add timestamp
        sms_data['timestamp'] = time.strftime('%Y-%m-%d %H:%M:%S')
        
        topic = f"{self.topic_prefix}/sms/state"
        self.client.publish(topic, json.dumps(sms_data))
        
        logger.info(f"📡 Published SMS to MQTT: {sms_data.get('Number', 'Unknown')} -> {sms_data.get('Text', '')[:50]}...")
    
    def _publish_initial_states(self):
        """Publish initial sensor states on startup"""
        # This will be called from the main thread with access to gammu machine
        pass
    
    def publish_initial_states_with_machine(self, gammu_machine):
        """Publish initial states with gammu machine access"""
        if not self.connected:
            logger.info("📡 MQTT not connected, skipping initial state publish")
            return
            
        try:
            from gammu import GSMNetworks
            
            # Publish initial signal strength
            signal = gammu_machine.GetSignalQuality()
            self.publish_signal_strength(signal)
            
            # Publish initial network info
            network = gammu_machine.GetNetworkInfo()
            network["NetworkName"] = GSMNetworks.get(network.get("NetworkCode", ""), 'Unknown')
            self.publish_network_info(network)
            
            # Publish empty SMS state initially
            empty_sms = {"Date": "", "Number": "", "State": "", "Text": "", "timestamp": ""}
            topic = f"{self.topic_prefix}/sms/state"
            self.client.publish(topic, json.dumps(empty_sms), retain=True)
            
            logger.info("📡 Published initial states to MQTT")
            
        except Exception as e:
            logger.error(f"Error publishing initial states: {e}")
    
    def start_sms_monitoring(self, gammu_machine, check_interval=30):
        """Start SMS monitoring in background thread"""
        if not self.connected:
            return
            
        def _sms_monitor_loop():
            logger.info(f"📱 Started SMS monitoring (check every {check_interval}s)")
            last_sms_count = 0
            
            while self.connected:
                try:
                    from support import retrieveAllSms, deleteSms
                    
                    # Check for new SMS
                    all_sms = retrieveAllSms(gammu_machine)
                    current_count = len(all_sms)
                    
                    # If there are new SMS since last check
                    if current_count > last_sms_count:
                        logger.info(f"📱 Detected {current_count - last_sms_count} new SMS messages")
                        
                        # Process new SMS (from the end, newest first)
                        for i in range(last_sms_count, current_count):
                            if i < len(all_sms):
                                sms = all_sms[i].copy()
                                sms.pop("Locations", None)
                                
                                # Publish to MQTT
                                self.publish_sms_received(sms)
                                
                                # Optionally delete after processing
                                # deleteSms(gammu_machine, all_sms[i])
                    
                    last_sms_count = current_count
                    
                except Exception as e:
                    logger.error(f"Error monitoring SMS: {e}")
                
                time.sleep(check_interval)
        
        # Only start if both MQTT and SMS monitoring are enabled  
        if (self.config.get('mqtt_enabled', False) and 
            self.config.get('sms_monitoring_enabled', True)):
            thread = threading.Thread(target=_sms_monitor_loop, daemon=True)
            thread.start()
    
    def publish_status_periodic(self, gammu_machine, interval=60):
        """Publish status data periodically in background thread"""
        if not self.connected:
            return
            
        def _publish_loop():
            while self.connected:
                try:
                    # Publish signal strength
                    signal = gammu_machine.GetSignalQuality()
                    self.publish_signal_strength(signal)
                    
                    # Publish network info
                    from gammu import GSMNetworks
                    network = gammu_machine.GetNetworkInfo()
                    network["NetworkName"] = GSMNetworks.get(network.get("NetworkCode", ""), 'Unknown')
                    self.publish_network_info(network)
                    
                except Exception as e:
                    logger.error(f"Error publishing periodic status: {e}")
                
                time.sleep(interval)
        
        if self.config.get('mqtt_enabled', False):
            thread = threading.Thread(target=_publish_loop, daemon=True)
            thread.start()
            logger.info(f"Started MQTT periodic publishing (interval: {interval}s)")
    
    def disconnect(self):
        """Disconnect from MQTT broker"""
        if self.client and self.connected:
            self.client.loop_stop()
            self.client.disconnect()
            logger.info("Disconnected from MQTT broker")