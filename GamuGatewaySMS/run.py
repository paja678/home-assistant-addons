#!/usr/bin/env python3
"""
SMS Gammu Gateway - Home Assistant Add-on
REST API SMS Gateway using python-gammu for USB GSM modems

Based on: https://github.com/pajikos/sms-gammu-gateway
Licensed under Apache License 2.0
"""

import os
import json
from flask import Flask, request
from flask_httpauth import HTTPBasicAuth
from flask_restful import reqparse, Api, Resource, abort

from support import init_state_machine, retrieveAllSms, deleteSms, encodeSms
from gammu import GSMNetworks

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
            'password': 'password'
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
app = Flask(__name__)
api = Api(app)
auth = HTTPBasicAuth()


@auth.verify_password
def verify(user, pwd):
    if not (user and pwd):
        return False
    return user == username and pwd == password


class Sms(Resource):
    def __init__(self, sm):
        self.parser = reqparse.RequestParser()
        self.parser.add_argument('text')
        self.parser.add_argument('number')
        self.parser.add_argument('smsc')
        self.parser.add_argument('unicode')
        self.machine = sm

    @auth.login_required
    def get(self):
        allSms = retrieveAllSms(machine)
        list(map(lambda sms: sms.pop("Locations"), allSms))
        return allSms

    @auth.login_required
    def post(self):
        args = self.parser.parse_args()
        if args['text'] is None or args['number'] is None:
            abort(404, message="Parameters 'text' and 'number' are required.")
        smsinfo = {
            "Class": -1,
            "Unicode": args.get('unicode') if args.get('unicode') else False,
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
                message["Number"] = number
                messages.append(message)
        result = [machine.SendSMS(message) for message in messages]
        return {"status": 200, "message": str(result)}, 200


class Signal(Resource):
    def __init__(self, sm):
        self.machine = sm

    def get(self):
        return machine.GetSignalQuality()


class Reset(Resource):
    def __init__(self, sm):
        self.machine = sm

    def get(self):
        machine.Reset(False)
        return {"status": 200, "message": "Reset done"}, 200


class Network(Resource):
    def __init__(self, sm):
        self.machine = sm

    def get(self):
        network = machine.GetNetworkInfo()
        network["NetworkName"] = GSMNetworks.get(network["NetworkCode"], 'Unknown')
        return network


class GetSms(Resource):
    def __init__(self, sm):
        self.machine = sm

    @auth.login_required
    def get(self):
        allSms = retrieveAllSms(machine)
        sms = {"Date": "", "Number": "", "State": "", "Text": ""}
        if len(allSms) > 0:
            sms = allSms[0]
            deleteSms(machine, sms)
            sms.pop("Locations")

        return sms


class SmsById(Resource):
    def __init__(self, sm):
        self.machine = sm

    @auth.login_required
    def get(self, id):
        allSms = retrieveAllSms(machine)
        self.abort_if_id_doesnt_exist(id, allSms)
        sms = allSms[id]
        sms.pop("Locations")
        return sms

    @auth.login_required
    def delete(self, id):
        allSms = retrieveAllSms(machine)
        self.abort_if_id_doesnt_exist(id, allSms)
        deleteSms(machine, allSms[id])
        return '', 204

    def abort_if_id_doesnt_exist(self, id, allSms):
        if id < 0 or id >= len(allSms):
            abort(404, message="Sms with id '{}' not found".format(id))


# Add API routes
api.add_resource(Sms, '/sms', resource_class_args=[machine])
api.add_resource(SmsById, '/sms/<int:id>', resource_class_args=[machine])
api.add_resource(Signal, '/signal', resource_class_args=[machine])
api.add_resource(Network, '/network', resource_class_args=[machine])
api.add_resource(GetSms, '/getsms', resource_class_args=[machine])
api.add_resource(Reset, '/reset', resource_class_args=[machine])

if __name__ == '__main__':
    print(f"Starting SMS Gammu Gateway on port {port}")
    print(f"Device path: {device_path}")
    print(f"SSL enabled: {ssl}")
    
    if ssl:
        app.run(port=port, host="0.0.0.0", ssl_context=('/ssl/cert.pem', '/ssl/key.pem'))
    else:
        app.run(port=port, host="0.0.0.0")