#!/usr/bin/env python3

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



class VirtualDevice:
    def __init__(self, addr=None, panel=None):
        self.addr = addr if addr else self.default_address()
        self.panel = panel if panel else 0x11
        self.buffer = bytes()
    
    def default_address(self):
        return 0

    def ingest(self, data):
        if data:
            self.buffer = data
            if len(self.buffer) >= 3:
                self.find()

    def find(self):
        try:
            index = self.buffer.index(self.addr)  # skip to first possible start
            self.buffer = self.buffer[index:]
        except ValueError:
            return

        if len(self.buffer) < 3:  # too small for req
            return

        if valid(self.buffer):
            self.handle(self.buffer)

    def handle(self, req):
        print(f"{self.__class__.__name__}({self.addr}): {req.hex(' ')}")


class VirtualEthernet(Device):
    def default_address(self):
        return 0x25 

    def __init__(self, addr=None, panel=None):
        super().__init__(addr, panel)

    def handle(self, req, res):
        if req[1] == 0x00:
            return self.handle_00(req)
        elif req[1] == 0x1A:
            return self.handle_1A(req)

    def reply_ok():
        return bytes([self.panel, 0xEC, 0x03, 0xC0, 0x00, 0x00, 0x00, 0x00, 0x6C])

    def reply_error():
        return bytes([self.panel, 0xEC, 0x03, 0xE0, 0x00, 0x00, 0x00, 0x00, 0x8C])

    # initial device poll
    def handle_00(req):
        return bytes([self.panel, 0xFF, 0x0A, 0x00, 0xDD, 0xA3])

    # device status poll
    def handle_1A(req):
        return reply_ok()

