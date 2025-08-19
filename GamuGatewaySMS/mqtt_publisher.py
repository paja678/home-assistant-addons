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
        
        if config.get('mqtt_enabled', False):
            self._setup_client()
    
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
        else:
            logger.error(f"Failed to connect to MQTT broker: {rc}")
    
    def _on_disconnect(self, client, userdata, rc):
        """Callback for MQTT disconnection"""
        self.connected = False
        logger.warning("Disconnected from MQTT broker")
    
    def _on_publish(self, client, userdata, mid):
        """Callback for published messages"""
        pass
    
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
        
        # Publish discovery configs
        discoveries = [
            ("homeassistant/sensor/sms_gateway_signal/config", signal_config),
            ("homeassistant/sensor/sms_gateway_network/config", network_config),
            ("homeassistant/sensor/sms_gateway_last_sms/config", sms_config)
        ]
        
        for topic, config in discoveries:
            self.client.publish(topic, json.dumps(config), retain=True)
        
        logger.info("Published MQTT discovery configurations")
        
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