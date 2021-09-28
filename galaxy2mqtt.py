#!/usr/bin/env python3

# pip install pyserial paho-mqtt

import sys
import serial
from paho.mqtt import client as mqtt_client
import random
import json
import yaml
import time
import http.server
import socketserver
import urllib
import threading
import jinja2

from state_model import StateStore


def merge(source, destination):
    """
    run me with nosetests --with-doctest file.py

    >>> a = { 'first' : { 'all_rows' : { 'pass' : 'dog', 'number' : '1' } } }
    >>> b = { 'first' : { 'all_rows' : { 'fail' : 'cat', 'number' : '5' } } }
    >>> merge(b, a) == { 'first' : { 'all_rows' : { 'pass' : 'dog', 'fail' : 'cat', 'number' : '5' } } }
    True
    """
    for key, value in source.items():
        if isinstance(value, dict):
            # get node or create one
            node = destination.setdefault(key, {})
            merge(value, node)
        else:
            destination[key] = value

    return destination


print("Honywell Galaxy G2-20 RS-485 to MQTT")

DEFAULTS = {
  'mqtt': {
    'base_discovery_topic': 'homeassistant',
    'base_topic': 'galaxy2mqtt',
    'server': 'core-mosquitto',
    'port': 1883,
    'user': 'homeassistant',
    'password': None,
    'timeout': 0.1,
  },
  'serial': {
      'port': None,
      'baudrate': 9600,
      'timeout': 0.1,
  },
  'web': {
      'host': '',
      'port': 8099,
  },
  'availability': {
      'expire_after': 60 * 20,
      'publish_interval': 60,
  },
  'devices': [
  ],
}

with open('/data/options.json', 'r') as fp:
    config_file = json.load(fp)

config = merge(DEFAULTS, {})
config = merge(config_file, config)
print(config)


allow_joining = False

state_store = StateStore()
state_store.load()


s = serial.Serial(config['serial']['port'], config['serial']['baudrate'], timeout=config['serial']['timeout'])


jinja = jinja2.Environment(
    loader=jinja2.FileSystemLoader('templates'),
    autoescape=jinja2.select_autoescape(),
)


class MyServer(http.server.BaseHTTPRequestHandler):
    def do(self):
        if self.client_address[0] != '172.30.32.2':
            self.send_response(304)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(f"<h1>Honywell Galaxy 2 MQTT</h1><p>Access Denied</p>".encode())
            return

        self.url = urllib.parse.urlparse(self.path)
        self.query = urllib.parse.parse_qs(self.url.query)
        self.base_url = self.headers.get('X-Ingress-Path', '')

        try:
            self.route = self.url.path.split('/')[1]
        except:
            self.route = ''

        try:
            self.subroute = '/'.join(self.url.path.split('/')[1:])
        except:
            self.subroute = ''

        handler = getattr(self, f'do_{self.command}_{self.route}', None)
        if callable(handler):
            handler()
        else:
            self.send_response(404)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(f"{self.command} <pre>{self.route}</pre> not found".encode())

    def do_GET(self):
        self.do()

    def do_PUT(self):
        self.do()

    def do_POST(self):
        self.do()

    def do_DELETE(self):
        self.do()

    def get_path(self, path):
        return self.headers.get('X-Ingress-Path', '') + '/' + path

    def redirect(self, path):
        target = self.get_path(path)
        self.send_response(301)
        self.send_header("Content-Type", "text/html")
        self.send_header("Location", target)
        self.end_headers()
        self.wfile.write(f'Moved to <a href="{target}">{target}</a>'.encode())

    def send_json(self, data):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data, indent=4).encode())

    def send_file(self, filename):
        with open(filename, 'rb') as fp:
            self.send_response(200)
            self.send_header('Content-Type', 'application/octetstream')
            self.send_header('Cache-Control', f'max-age={60*60*24}')
            self.end_headers()
            self.wfile.write(fp.read())

    def do_GET_(self):
        self.redirect('devices')

    def do_GET_dashboard(self):
        self.redirect('devices')

    def do_GET_devices(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.end_headers()
        self.wfile.write(jinja.get_template('devices.html.j2').render(handler=self, allow_joining=allow_joining, state=state_store.state, devices=devices, now=time.time()).encode())

    def do_POST_device(self):
        device_type = next(iter(self.query.get('type', [])), None)
        device_address = next(iter(self.query.get('address', [])), None)
        device_state = state_store.get(device_type, device_address)

        if device_state:
            new_name = next(iter(self.query.get('name', [])), None)
            if new_name:
                device_state['name'] = new_name
                state_store.set(device_type, device_address, device_state)

            if device_state.get('joined'):
                publish_state(device_state)
            self.send_json(device_state)
        else:
            self.send_json({'error': 'Device not joined or not found'})

    def do_PUT_device(self):
        device_type = next(iter(self.query.get('type', [])), None)
        device_address = next(iter(self.query.get('address', [])), None)
        device_state = state_store.get(device_type, device_address)

        if device_state:
            publish_state(device_state)
            device_state['joined'] = True
            state_store.set(device_type, device_address, device_state)
            self.send_json(device_state)
        else:
            self.send_json({'error': 'Device not joined or not found'})

    def do_DELETE_device(self):
        device_type = next(iter(self.query.get('type', [])), None)
        device_address = next(iter(self.query.get('address', [])), None)
        device_state = state_store.get(device_type, device_address)

        if device_state:
            name = f"{device_type}X{device_address}"
            discovery_topic = f"{config['mqtt']['base_discovery_topic']}/binary_sensor/{name}/binary_sensor/config"
            publish(discovery_topic, '')
            device_state['joined'] = False
            state_store.set(device_type, device_address, device_state)
            self.send_json(device_state)
        else:
            self.send_json({'error': 'Device not joined or not found'})

    def do_POST_joining(self):
        global allow_joining
        allow_joining = next(iter(self.query.get('allowed', [])), None) in ['true']
        if not allow_joining:
            purge_not_joined()
        self.send_json({'allow_joining': allow_joining})

    def do_GET_static(self):
        self.send_file(self.subroute)



def purge_not_joined():
    deleted = []
    for name, data in state_store.state.items():
        if not data.get('joined'):
            deleted.append(name)
    for name in deleted:
        del state_store.state[name]
    state_store.flush()
    return deleted


socketserver.TCPServer.allow_reuse_address = True
httpd = socketserver.TCPServer((config['web']['host'], config['web']['port']), MyServer)
httpd.timeout = 0.001

def connect_mqtt():
    def on_connect(client, userdata, flags, rc):
        print("MQTT Connection Status")
        if rc == 0:
            print("Connected to MQTT!")
        else:
            print(f"Failed connect MQTT :( {rc}")

    client_id = f'python-mqtt-{random.randint(0, 10000)}'
    client = mqtt_client.Client(client_id)
    client.username_pw_set(config['mqtt']['user'], config['mqtt']['password'])
    client.on_connect = on_connect
    client.connect(config['mqtt']['server'], config['mqtt']['port'])
    return client


client = connect_mqtt()


def publish(topic, data):
    print(f"MQTT [{topic}]: {data}")
    client.publish(topic, data)
    client.loop(timeout=0)


def online(availability_topic):
    publish(availability_topic, 'online')


last_publish_offline = time.time()
def publish_offline():
    global last_publish_offline
    now = time.time()

    if last_publish_offline + config['availability']['publish_interval'] <= now:
        for name, data in state_store.not_seen_for(config['availability']['expire_after']):
            if data.get('joined'):
                name = f"{data['type']}X{data['address']}"
                availability_topic = f"{config['mqtt']['base_topic']}/binary_sensor/{name}/availability"
                publish(availability_topic, 'offline')

        last_publish_offline = now


def publish_state(device):
    device_type = device.get('type')
    device_address = device.get('address')
    attributes = device.get('attributes', {})

    device_class = {'02': 'door', '0d': 'motion'}.get(device_type)
    name = f"{device_type}X{device_address}"
    custom_name = device.get('name', name)

    state_topic = f"{config['mqtt']['base_topic']}/binary_sensor/{name}"
    availability_topic = f"{config['mqtt']['base_topic']}/binary_sensor/{name}/availability"
    attributes_topic = f"{config['mqtt']['base_topic']}/binary_sensor/{name}/attributes"
    discovery_topic = f"{config['mqtt']['base_discovery_topic']}/binary_sensor/{name}/binary_sensor/config"

    discovery = {
        'name': custom_name,
        'unique_id': f'galaxyrs485_{name}',
        'device_class': device_class,
        'state_topic': state_topic,
        'json_attributes_topic': attributes_topic,
        'availability': [
            {
                'topic': availability_topic,
            },
        ],
        "device": {
          "identifiers": [f"honeywell_{name}"],
          "manufacturer": "Honeywell",
          "model": f"Honeywell Galaxy Sensor ({device_type})",
          "name": custom_name,
          "sw_version": "galaxy2mqtt 0.0.0",
        },
    }
    if device_class == 'motion':
        discovery['off_delay'] = 300

    txt_state = 'ON' if attributes.get('alarm') else 'OFF'

    publish(discovery_topic, json.dumps(discovery))
    online(availability_topic)
    if device_class != 'motion' or txt_state == 'ON':
        publish(state_topic, txt_state)

    publish(attributes_topic, json.dumps(attributes))


def calculate_checksum(data):
    return sum((0xaa + sum(data)).to_bytes(10, byteorder='big')) & 0xFF

def validate_checksum(data):
    if len(data) < 3:
        return False
    checksum = calculate_checksum(data[:-1])
    return data[-1] == checksum

def valid(data):
    return validate_checksum(data)

def output(buffer):
    valid = '+' if validate_checksum(buffer) else '-'
    print(f' {valid} [{buffer.hex(" ")}] [{buffer}]')



class Device:
    def __init__(self, addr=None, panel=None):
        self.addr = addr if addr else self.default_address()
        self.panel = panel if panel else 0x11
        self.buffer = bytes()
    
    def default_address(self):
        return 0

    def ingest(self, data):
        if data:
            self.buffer += data
            if len(self.buffer) >= 6:
                self.find()
            self.buffer = self.buffer[-60:]

    def find(self):
        try:
            index = self.buffer.index(self.addr)  # skip to first possible start
            self.buffer = self.buffer[index:]
        except ValueError:
            self.buffer = bytes()
            return

        if len(self.buffer) < 6:  # too small for req and res
            return

        for i, x in enumerate(self.buffer):
            if x == self.panel:
                message = self.buffer[:i]
                for r in range(len(message), len(self.buffer)):
                    response = self.buffer[i:r]

                    if valid(message) and valid(response):
                        self.handle(message, response)
                        self.buffer = self.buffer[r:]
                        return

    def handle(self, req, res):
        print(f"{self.__class__.__name__}({self.addr}): {req.hex(' ')}  -->  {res.hex(' ')}")
        print(f"--- [{req[2:-1]}]  -->  [{res[2:-1]}]")


class Keypad(Device):
    def default_address(self):
        return 0x10

    def __init__(self, addr=None, panel=None):
        super().__init__(addr, panel)
        self.screen = bytearray([0x20] * 32)
        self.old_screen = bytearray([0x20] * 32)
        self.cursor = 0

    def handle(self, req, res):
        if req[:2] == bytes([self.addr, 0x07]):
            update = req[3:-1]
            next_byte_cursor_pos = False
            for byte in update:
                if next_byte_cursor_pos:
                    self.cursor = byte
                    next_byte_cursor_pos = False
                    continue

                if byte == 1:  # cursor beginning first line
                    self.cursor = 0
                elif byte == 2:  # cursor beginning second line
                    self.cursor = 16
                elif byte == 3:  # set cursor pos to next byte
                    next_byte_cursor_pos = True
                elif byte == 4:  # scroll left
                    pass
                elif byte == 5:  # scroll right
                    pass
                elif byte >= 6 and byte <= 11:  # cursor style stuff
                    pass
                elif byte == 14:  # backspace
                    if self.cursor > 0:
                        self.cursor -= 1
                        self.screen[self.cursor] = 0x20
                elif byte == 15:  # cursor left
                    self.cursor = max(self.cursor - 1, 0)
                elif byte == 16:  # cursor right
                    self.cursor = min(self.cursor + 1, 31)
                elif byte == 17:  # clear screen
                    self.screen = bytearray([0x20]  * 32)
                    self.cursor = 0
                elif byte >= 19 and byte <= 19:  # (stop) flashing
                    pass
                else:
                    self.screen[self.cursor] = byte
                    self.cursor = min(self.cursor + 1, 31)

            if self.screen != self.old_screen:
                print("." + "-" * 16 + ".")
                print("|" + self.screen[:16].decode('ascii') + "|")
                print("|" + self.screen[16:].decode('ascii') + "|")
                print("'" + "-" * 16 + "'")
                self.old_screen[:] = self.screen



class RFPortal(Device):
    def default_address(self):
        return 0x85

    def find(self):
        while len(self.buffer) >= 13:
            try:
                index = self.buffer.index(self.panel)
                self.buffer = self.buffer[index:]
            except ValueError:
                self.buffer = bytes()

            if len(self.buffer) >= 13:
                if self.buffer[:2] != bytes([self.panel, 0xfd]):
                    self.buffer = self.buffer[1:]
                    continue
                    
                response = self.buffer[:13]

                if valid(response):
                    self.buffer = self.buffer[1:]
                    self.handle(None, response)
                    continue
                else:
                    self.buffer = self.buffer[1:]
                    continue


    def handle(self, req, res):
        if len(res) != 13:
            return

        if res[:2] == bytes([self.panel, 0xfd]):
            device_type = bytes([res[10]]).hex()
            device_address = bytes(res[2:6]).hex()

            alarm = res[7] & 0x40 != 0
            tamper = res[7] & 0x20 != 0
            device_class = {0x02: 'door', 0x0d: 'motion'}.get(res[10])
            signal = int(res[11] * 10)
            battery = int(res[6] / 2.56)
            counter = int(res[8])

            if device_class:
                print(f"Sensor {bytes([res[10]]).hex()} X {bytes(res[2:6]).hex(' ')}:")
                print(f"  > {res.hex(' ')}")
                print(f"  Signal:  {signal}%")
                if res[6] > 0:
                    print(f"  Battery: {battery}%")
                if res[8] > 0:
                    print(f"  Counter: {counter}")
                print(f"  Alarm:   {res[7] & 0x40 != 0}")
                print(f"  Tamper:  {res[7] & 0x20 != 0}")

                attributes = {
                    'linkquality': signal,
                    'battery': battery,
                    'counter': counter,
                    'timestamp': int(time.time()),
                    'alarm': alarm,
                    'tamper': tamper,
                }
    
                device_state = state_store.upsert(device_type, device_address, attributes, allow_joining)
                if device_state.get('joined'):
                    publish_state(device_state)


class JustLog(Device):
    def ingest(self, data):
        print(f'{self.__class__.__name__}({self.addr}): {data.hex(" ")}')


devices = [
    globals()[device['type']](device.get('address'))
    for device in config['devices']
]

while True:
    httpd.handle_request()
    client.loop(timeout=0.1)
    publish_offline()
    data = s.read(1024)
    if data:
        for device in devices:
            device.ingest(data)

    sys.stdout.flush()
