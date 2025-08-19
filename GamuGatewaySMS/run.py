#!/usr/bin/env python3
"""
SMS Gammu Gateway - Home Assistant Add-on
REST API SMS Gateway using python-gammu for USB GSM modems

Based on: https://github.com/pajikos/sms-gammu-gateway
Licensed under Apache License 2.0
"""

import os
import json
import logging
from flask import Flask, request
from flask_httpauth import HTTPBasicAuth
from flask_restx import Api, Resource, fields, reqparse

from support import init_state_machine, retrieveAllSms, deleteSms, encodeSms
from mqtt_publisher import MQTTPublisher
from gammu import GSMNetworks

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
mqtt_logger = logging.getLogger('mqtt_publisher')
mqtt_logger.setLevel(logging.INFO)

# Suppress Flask development server warning
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

def load_ha_config():
    """Load Home Assistant add-on configuration"""
    config_path = '/data/options.json'
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return json.load(f)
    else:
        # Default values for testing outside HA
        return {
            'device_path': '/dev/ttyUSB0',
            'pin': '',
            'port': 5000,
            'ssl': False,
            'username': 'admin',
            'password': 'password',
            'mqtt_enabled': False,
            'mqtt_host': 'localhost',
            'mqtt_port': 1883,
            'mqtt_username': '',
            'mqtt_password': '',
            'mqtt_topic_prefix': 'homeassistant/sensor/sms_gateway',
            'sms_monitoring_enabled': True,
            'sms_check_interval': 60
        }

# Load configuration
config = load_ha_config()
pin = config.get('pin') if config.get('pin') else None
ssl = config.get('ssl', False)
port = config.get('port', 5000)
username = config.get('username', 'admin')
password = config.get('password', 'password')
device_path = config.get('device_path', '/dev/ttyUSB0')

# Initialize gammu state machine
machine = init_state_machine(pin, device_path)

# Initialize MQTT publisher
mqtt_publisher = MQTTPublisher(config)

app = Flask(__name__)

# Check if running under Ingress
import os
ingress_path = os.environ.get('INGRESS_PATH', '')

# Define root route BEFORE Flask-RESTX initialization to ensure it takes precedence
@app.route('/')
def home():
    """Root page handler - defined early to ensure it's registered first"""
    from flask import Response
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>SMS Gammu Gateway</title>
        <meta charset="utf-8">
        <style>
            body { 
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                margin: 0;
                padding: 20px;
                background: #f5f5f5;
            }
            .container {
                max-width: 800px;
                margin: 0 auto;
                background: white;
                padding: 30px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
                margin-bottom: 10px;
            }
            .status {
                background: #e8f5e9;
                border-left: 4px solid #4caf50;
                padding: 15px;
                margin: 20px 0;
            }
            .endpoints {
                background: #f5f5f5;
                padding: 20px;
                border-radius: 5px;
                margin: 20px 0;
            }
            .endpoint {
                background: white;
                padding: 10px;
                margin: 10px 0;
                border-radius: 3px;
                font-family: monospace;
            }
            .button {
                display: inline-block;
                padding: 10px 20px;
                background: #2196F3;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                margin: 10px 10px 10px 0;
            }
            .button:hover {
                background: #1976D2;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📱 SMS Gammu Gateway</h1>
            <p>REST API for sending and receiving SMS messages via USB GSM modems</p>
            
            <div class="status">
                <strong>✅ Gateway is running</strong><br>
                Version: 1.1.1
            </div>
            
            <h2>Quick Links</h2>
            <a href="status/signal" class="button">📊 Signal Strength</a>
            <a href="status/network" class="button">🌐 Network Info</a>
            
            <h2>API Endpoints</h2>
            <div class="endpoints">
                <div class="endpoint">
                    <strong>GET /status/signal</strong> - Get signal strength (public)
                </div>
                <div class="endpoint">
                    <strong>GET /status/network</strong> - Get network info (public)
                </div>
                <div class="endpoint">
                    <strong>POST /sms</strong> - Send SMS (requires auth)
                </div>
                <div class="endpoint">
                    <strong>GET /sms</strong> - Get all SMS (requires auth)
                </div>
                <div class="endpoint">
                    <strong>GET /sms/{id}</strong> - Get specific SMS (requires auth)
                </div>
                <div class="endpoint">
                    <strong>DELETE /sms/{id}</strong> - Delete SMS (requires auth)
                </div>
                <div class="endpoint">
                    <strong>GET /getsms</strong> - Get and delete first SMS (requires auth)
                </div>
                <div class="endpoint">
                    <strong>GET /status/reset</strong> - Reset modem (public)
                </div>
            </div>
            
            <h2>Authentication</h2>
            <p>Protected endpoints require HTTP Basic Authentication with your configured username and password.</p>
        </div>
    </body>
    </html>
    '''
    return Response(html, mimetype='text/html', status=200, headers={'Content-Type': 'text/html; charset=utf-8'})

# Swagger UI Configuration  
# Disable Swagger UI to avoid routing conflicts with Ingress
api = Api(
    app, 
    version='1.1.1',
    title='SMS Gammu Gateway API',
    description='REST API for sending and receiving SMS messages via USB GSM modems (SIM800L, Huawei, etc.)',
    doc=False,  # Disable Swagger UI documentation
    prefix=ingress_path,  # Add Ingress prefix if present
    authorizations={
        'basicAuth': {
            'type': 'basic',
            'in': 'header',
            'name': 'Authorization'
        }
    },
    security='basicAuth'
)

auth = HTTPBasicAuth()

@auth.verify_password
def verify(user, pwd):
    if not (user and pwd):
        return False
    return user == username and pwd == password

# API Models for Swagger documentation
sms_model = api.model('SMS', {
    'text': fields.String(required=True, description='SMS message text', example='Hello, how are you?'),
    'number': fields.String(required=True, description='Phone number (international format)', example='+420123456789'),
    'smsc': fields.String(required=False, description='SMS Center number (optional)', example='+420603052000'),
    'unicode': fields.Boolean(required=False, description='Use Unicode encoding', default=False)
})

sms_response = api.model('SMS Response', {
    'Date': fields.String(description='Date and time received', example='2025-01-19 14:30:00'),
    'Number': fields.String(description='Sender phone number', example='+420123456789'),
    'State': fields.String(description='SMS state', example='UnRead'),
    'Text': fields.String(description='SMS message text', example='Hello World!')
})

signal_response = api.model('Signal Quality', {
    'SignalStrength': fields.Integer(description='Signal strength in dBm', example=-75),
    'SignalPercent': fields.Integer(description='Signal strength percentage', example=65),
    'BitErrorRate': fields.Integer(description='Bit error rate', example=-1)
})

network_response = api.model('Network Info', {
    'NetworkName': fields.String(description='Network operator name', example='T-Mobile'),
    'State': fields.String(description='Network registration state', example='HomeNetwork'),
    'NetworkCode': fields.String(description='Network operator code', example='230 01'),
    'CID': fields.String(description='Cell ID', example='0A1B2C3D'),
    'LAC': fields.String(description='Location Area Code', example='1234')
})

send_response = api.model('Send Response', {
    'status': fields.Integer(description='HTTP status code', example=200),
    'message': fields.String(description='Response message', example='[1]')
})

reset_response = api.model('Reset Response', {
    'status': fields.Integer(description='HTTP status code', example=200),
    'message': fields.String(description='Reset message', example='Reset done')
})

# API Namespaces
ns_sms = api.namespace('sms', description='SMS operations (requires authentication)')
ns_status = api.namespace('status', description='Device status and information (public)')

@ns_sms.route('')
@ns_sms.doc('sms_operations')
class SmsCollection(Resource):
    @ns_sms.doc('get_all_sms')
    @ns_sms.marshal_list_with(sms_response)
    @ns_sms.doc(security='basicAuth')
    @auth.login_required
    def get(self):
        """Get all SMS messages from SIM/device memory"""
        allSms = retrieveAllSms(machine)
        list(map(lambda sms: sms.pop("Locations", None), allSms))
        return allSms

    @ns_sms.doc('send_sms')
    @ns_sms.expect(sms_model)
    @ns_sms.marshal_with(send_response)
    @ns_sms.doc(security='basicAuth')
    @auth.login_required
    def post(self):
        """Send SMS message(s)"""
        parser = reqparse.RequestParser()
        parser.add_argument('text', required=True, help='SMS message text')
        parser.add_argument('number', required=True, help='Phone number(s), comma separated')
        parser.add_argument('smsc', required=False, help='SMS Center number (optional)')
        parser.add_argument('unicode', type=bool, required=False, default=False, help='Use Unicode encoding')
        
        args = parser.parse_args()
        
        smsinfo = {
            "Class": -1,
            "Unicode": args.get('unicode', False),
            "Entries": [
                {
                    "ID": "ConcatenatedTextLong",
                    "Buffer": args['text'],
                }
            ],
        }
        messages = []
        for number in args.get("number").split(','):
            for message in encodeSms(smsinfo):
                message["SMSC"] = {'Number': args.get("smsc")} if args.get("smsc") else {'Location': 1}
                message["Number"] = number.strip()
                messages.append(message)
        result = [machine.SendSMS(message) for message in messages]
        return {"status": 200, "message": str(result)}, 200

@ns_sms.route('/<int:id>')
@ns_sms.doc('sms_by_id')
class SmsItem(Resource):
    @ns_sms.doc('get_sms_by_id')
    @ns_sms.marshal_with(sms_response)
    @ns_sms.doc(security='basicAuth')
    @auth.login_required
    def get(self, id):
        """Get specific SMS by ID"""
        allSms = retrieveAllSms(machine)
        if id < 0 or id >= len(allSms):
            api.abort(404, f"SMS with id '{id}' not found")
        sms = allSms[id]
        sms.pop("Locations", None)
        return sms

    @ns_sms.doc('delete_sms_by_id')
    @ns_sms.doc(security='basicAuth')
    @auth.login_required
    def delete(self, id):
        """Delete SMS by ID"""
        allSms = retrieveAllSms(machine)
        if id < 0 or id >= len(allSms):
            api.abort(404, f"SMS with id '{id}' not found")
        deleteSms(machine, allSms[id])
        return '', 204

@ns_sms.route('/getsms')
@ns_sms.doc('get_and_delete_first_sms')
class GetSms(Resource):
    @ns_sms.doc('pop_first_sms')
    @ns_sms.marshal_with(sms_response)
    @ns_sms.doc(security='basicAuth')
    @auth.login_required
    def get(self):
        """Get first SMS and delete it from memory"""
        allSms = retrieveAllSms(machine)
        sms = {"Date": "", "Number": "", "State": "", "Text": ""}
        if len(allSms) > 0:
            sms = allSms[0]
            deleteSms(machine, sms)
            sms.pop("Locations", None)
            # Publish to MQTT if enabled and SMS has content
            if sms.get("Text"):
                mqtt_publisher.publish_sms_received(sms)
        return sms

@ns_status.route('/signal')
@ns_status.doc('get_signal_quality')
class Signal(Resource):
    @ns_status.doc('signal_strength')
    @ns_status.marshal_with(signal_response)
    def get(self):
        """Get GSM signal strength and quality"""
        signal_data = machine.GetSignalQuality()
        # Publish to MQTT if enabled
        mqtt_publisher.publish_signal_strength(signal_data)
        return signal_data

@ns_status.route('/network')
@ns_status.doc('get_network_info')
class Network(Resource):
    @ns_status.doc('network_information')
    @ns_status.marshal_with(network_response)
    def get(self):
        """Get network operator and registration information"""
        network = machine.GetNetworkInfo()
        network["NetworkName"] = GSMNetworks.get(network.get("NetworkCode", ""), 'Unknown')
        # Publish to MQTT if enabled
        mqtt_publisher.publish_network_info(network)
        return network

@ns_status.route('/reset')
@ns_status.doc('reset_modem')
class Reset(Resource):
    @ns_status.doc('modem_reset')
    @ns_status.marshal_with(reset_response)
    def get(self):
        """Reset GSM modem (useful for stuck connections)"""
        machine.Reset(False)
        return {"status": 200, "message": "Reset done"}, 200

if __name__ == '__main__':
    print(f"🚀 SMS Gammu Gateway v1.1.1 started successfully!")
    print(f"📱 Device: {device_path}")
    print(f"🌐 API available on port {port}")
    print(f"🏠 Web UI: http://localhost:{port}/")
    print(f"🔒 SSL: {'Enabled' if ssl else 'Disabled'}")
    
    # MQTT info
    if config.get('mqtt_enabled', False):
        print(f"📡 MQTT: Enabled -> {config.get('mqtt_host')}:{config.get('mqtt_port')}")
        
        # Wait a moment for MQTT connection, then publish initial states
        import time
        time.sleep(2)
        mqtt_publisher.publish_initial_states_with_machine(machine)
        
        # Start periodic MQTT publishing
        mqtt_publisher.publish_status_periodic(machine, interval=300)  # 5 minutes
        
        # Start SMS monitoring if enabled
        if config.get('sms_monitoring_enabled', True):
            check_interval = config.get('sms_check_interval', 60)
            mqtt_publisher.start_sms_monitoring(machine, check_interval=check_interval)
            print(f"📱 SMS Monitoring: Enabled (check every {check_interval}s)")
        else:
            print(f"📱 SMS Monitoring: Disabled")
    else:
        print(f"📡 MQTT: Disabled")
    
    print(f"✅ Ready to send/receive SMS messages")
    
    try:
        if ssl:
            app.run(port=port, host="0.0.0.0", ssl_context=('/ssl/cert.pem', '/ssl/key.pem'),
                    debug=False, use_reloader=False)
        else:
            app.run(port=port, host="0.0.0.0", debug=False, use_reloader=False)
    finally:
        # Cleanup MQTT connection
        mqtt_publisher.disconnect()