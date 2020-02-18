from ipc import RequestIds, DisplayerHost
from OpenGL import GL
from glfw import GLFW
from PIL import Image


class Displayer():
    def __init__(self):
        pass
    
    def use_display(self, display):
        raise RuntimeError("Not yet implemented")
    
    def set_dimensions(self, width, height):
        raise RuntimeError("Not yet implemented")
    
    def update(self):
        raise RuntimeError("Not yet implemented")


def main():
    displayer = Displayer()
    host = DisplayerHost(displayer)
    
    while not host.terminate:
        host.handle_request()

if __name__ == '__main__':
    main()
