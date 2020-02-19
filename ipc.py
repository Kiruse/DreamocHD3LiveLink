from subprocess import Popen, PIPE, TimeoutExpired
from sys import stdin
from enum import IntEnum
import os

TERMINATE_TIMEOUT = 5 # seconds

class RequestIds(IntEnum):
    TERMINATE      = 0
    KEEPALIVE      = 1
    USE_DISPLAY    = 2
    SET_DIMS       = 3
    RELOAD_RENDERS = 4


class DisplayerClient:
    def __init__(self):
        self.proc = None
        self.initialized = False
    
    def open(self):
        if self.proc is None:
            currdir = os.path.abspath(os.path.dirname(__file__))
            self.proc = Popen([f'{currdir}/venv/Scripts/python', f'{currdir}/displayer.py'], stdin=PIPE, bufsize=0)
            self.initialized = False
    
    def initialize(self, display = 2, width = 1280, height = 720):
        self.set_display(display)
        self.set_dimensions(width, height)
        self.initialized = True
    
    def terminate(self):
        self.write_int(RequestIds.TERMINATE)
        try:
            self.proc.wait(TERMINATE_TIMEOUT)
        except TimeoutExpired:
            self.proc.kill()
        self.proc = None
    
    def write_int(self, num, bytes = 4, byteorder = 'big'):
        buff = num.to_bytes(bytes, byteorder)
        self.proc.stdin.write(buff)
    
    def keepalive(self):
        self.write_int(RequestIds.KEEPALIVE)
    
    def notify(self):
        self.write_int(RequestIds.RELOAD_RENDERS)
    
    def set_display(self, display):
        self.write_int(RequestIds.USE_DISPLAY)
        self.write_int(display)
    
    def set_dimensions(self, width, height):
        self.write_int(RequestIds.SET_DIMS)
        self.write_int(width)
        self.write_int(height)


class DisplayerHost:
    def __init__(self, delegate):
        self.terminate = False
        self.delegate  = delegate
    
    def handle_request(self):
        reqid = self.read_int()
        
        if reqid == RequestIds.TERMINATE:
            self.delegate.terminate()
        
        elif reqid == RequestIds.USE_DISPLAY:
            self.delegate.use_display(self.read_int())
        
        elif reqid == RequestIds.SET_DIMS:
            self.delegate.set_dimensions(self.read_int(), self.read_int())
        
        elif reqid == RequestIds.RELOAD_RENDERS:
            self.delegate.update()
        
        return reqid
    
    def read_int(self, bytes = 4, byteorder = 'big', signed = False):
        buff = stdin.buffer.read(bytes)
        return int.from_bytes(buff, byteorder, signed=signed)
