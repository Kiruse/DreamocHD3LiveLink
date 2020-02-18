from threading import Thread, Lock, Condition
from ipc import DisplayerHost
from OpenGL import GL
from glfw.GLFW import *
from PIL import Image


class Displayer(Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.wants_terminate = False
        self.dirty = False
        
        self.wnd = None
        
        self.monitor = None
        self.wants_monitor = None
        
        self.dimensions = (1280, 720)
        
        self.update_cond = Condition()
    
    def run(self):
        assert glfwInit()
        self._init_window()
        
        while not self.wants_terminate:
            with self.update_cond:
                self.update_cond.wait_for(lambda: self.wants_terminate or self.dirty)
                
                if not self.wants_terminate:
                    if self.wants_monitor is not None:
                        self._change_monitor(self.wants_monitor)
                    self.do_update()
                    self.dirty = False
        
        glfwTerminate()
    
    def terminate(self):
        with self.update_cond:
            self.wants_terminate = True
            self.update_cond.notify()
    
    def _init_window(self):
        if self.wnd is not None:
            glfwDestroyWindow(self.wnd)
        
        self.monitor = self._get_monitor(-1)
        vidmode = glfwGetVideoMode(self.monitor)
        
        glfwWindowHint(GLFW_RED_BITS,     vidmode.bits.red)
        glfwWindowHint(GLFW_GREEN_BITS,   vidmode.bits.green)
        glfwWindowHint(GLFW_BLUE_BITS,    vidmode.bits.blue)
        glfwWindowHint(GLFW_REFRESH_RATE, vidmode.refresh_rate)
        self.wnd = glfwCreateWindow(vidmode.size.width, vidmode.size.height, "Dreamoc HD3 Blender Preview", self.monitor, None)
        glfwMakeContextCurrent(self.wnd)
    
    def _change_monitor(self, monitorid):
        self.monitor = self._get_monitor(monitorid)
        vidmode = glfwGetVideoMode(self.monitor)
        glfwSetWindowMonitor(self.wnd, self.monitor, 0, 0, vidmode.width, vidmode.height, vidmode.refresh_rate)
        self.wants_monitor = None
    
    def _get_monitor(self, monitorid):
        monitors = glfwGetMonitors()
        if monitorid < 0 or monitorid > len(monitors):
            monitorid = len(monitors) - 1
        return monitors[monitorid]
    
    def use_display(self, display):
        with self.update_cond:
            self.wants_monitor = display
            self.dirty = True
            self.update_cond.notify()
    
    def set_dimensions(self, width, height):
        # Dimensions only take effect with the next update. They do not trigger an update themselves.
        self.dimensions = (width, height)
    
    def update(self):
        with self.update_cond:
            self.dirty = True
            self.update_cond.notify()
    
    def do_update(self):
        pass


def main():
    displayer = Displayer()
    displayer.start()
    host = DisplayerHost(displayer)
    
    while not displayer.wants_terminate:
        host.handle_request()

if __name__ == '__main__':
    main()
