# Copyright (c) Skye Cobile <skye.cobile@outlook.com> 2020, Germany
# SEE LICENSE
# TODO: Automatically terminate if no request in x minutes?
# TODO: Host does not properly handle display change requests

from array import array
from threading import Thread, Lock, Condition
from ipc import DisplayerHost
from OpenGL.GL import *
from glfw.GLFW import *
from PIL import Image
import os

CURRDIR = os.path.abspath(os.path.dirname(__file__))


class Shape:
    def __init__(self, program, verts, uvs, image_filepath):
        self.program = program
        self.vao = 0
        self.vbo_verts = 0
        self.vbo_uvs = 0
        self.tex = 0
        self.verts = array('f', verts)
        self.uvs   = array('f', uvs)
        self.image_filepath = image_filepath
    
    def initialize(self):
        self.vao = glGenVertexArrays(1)
        self.vbo_verts, self.vbo_uvs = glGenBuffers(2)
        self.tex = glGenTextures(1)
        
        glBindVertexArray(self.vao)
        
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_verts)
        glBufferData(GL_ARRAY_BUFFER, 4*len(self.verts), self.verts.tobytes(), GL_STATIC_DRAW)
        glVertexAttribPointer(0, 2, GL_FLOAT, GL_FALSE, 8, ctypes.c_void_p(0))
        glEnableVertexAttribArray(0)
        
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo_uvs)
        glBufferData(GL_ARRAY_BUFFER, 4*len(self.uvs), self.uvs.tobytes(), GL_STATIC_DRAW)
        glVertexAttribPointer(1, 2, GL_FLOAT, GL_FALSE, 8, ctypes.c_void_p(0))
        glEnableVertexAttribArray(1)
        
        glBindTexture(GL_TEXTURE_2D, self.tex)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
        
        return self
    
    def draw(self):
        glBindVertexArray(self.vao)
        glBindTexture(GL_TEXTURE_2D, self.tex)
        glDrawArrays(GL_TRIANGLES, 0, len(self.verts))
    
    def load_texture(self):
        img = Image.open(self.image_filepath).transpose(Image.FLIP_TOP_BOTTOM).transpose(Image.FLIP_LEFT_RIGHT)
        glBindTexture(GL_TEXTURE_2D, self.tex)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, img.size[0], img.size[1], 0, GL_RGBA, GL_UNSIGNED_BYTE, self._get_image_data(img).tobytes())
        glGenerateMipmap(GL_TEXTURE_2D)
    
    def _get_image_data(self, img):
        pixels = array('B')
        for pixel in img.getdata():
            pixels += array('B', pixel)
        return pixels

class Displayer(Thread):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.wants_terminate = False
        self.dirty = False
        
        self.wnd = None
        
        self.monitor = None
        self.wants_monitor = None
        
        self.dimensions = (1280, 720)
        
        # OpenGL resources
        self.shape_front = self.shape_left = self.shape_right = None
        self.program = 0
        
        # Threadsafety
        self.update_cond = Condition()
    
    def run(self):
        assert glfwInit()
        self._init_window()
        self._init_shader()
        
        vf  = self._convert_verts([(-21.5, -14.5), (21.5, -14.5), (-4, 3.5), (21.5, -14.5), (4, 3.5), (-4, 3.5)])
        uvf = self._flatten_vecs( [(-0.279, -0.109), (1.284, -0.109), (0.357, 1.109), (1.284, -0.109), (0.648, 1.109), (0.357, 1.109)])
        vl  = self._convert_verts([(-25.5, -14.5), (-21.5, -14.5), (-25.5, 14.5), (-21.5, -14.5), (-4, 3.5),  (-25.5, 14.5), (-25.5, 14.5), (-4, 3.5),  (-4, 14.5)])
        uvl = self._flatten_vecs( [(1.227, -0.109), (1.227, 0.118), (0.038, -0.109), (1.227, 0.118), (0.489, 1.109), (0.038, -0.109), (0.038, -0.109), (0.489, 1.109), (0.038, 1.109)])
        vr  = self._convert_verts([(21.5, -14.5), (25.5, -14.5), (25.5, 14.5), (21.5, -14.5), (25.5, 14.5), (4, 3.5), (4, 3.5), (25.5, 14.5), (4, 14.5)])
        uvr = self._flatten_vecs( [(-0.226, 0.118), (-0.226, -0.109), (0.962, -0.109), (-0.226, 0.118), (0.962, -0.109), (0.511, 1.109), (0.511, 1.109), (0.962, -0.109), (0.962, 1.109)])
        
        # NOTE: Left view is on the right side of the holographic display and vice versa!
        self.shape_front = Shape(self.program, vf, uvf, f'{CURRDIR}/tmp/front.png').initialize()
        self.shape_left  = Shape(self.program, vl, uvl, f'{CURRDIR}/tmp/right.png').initialize()
        self.shape_right = Shape(self.program, vr, uvr, f'{CURRDIR}/tmp/left.png').initialize()
        
        glClearColor(0, 0, 0, 0)
        
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
    
    def _convert_verts(self, verts):
        device_size = (51/2, 29/2) # approximation; in cm; halved because normalized screen coordinates in [-1;+1]
        return [elem / device_size[idx%2] for idx, elem in enumerate(self._flatten_vecs(verts))]
    
    def _flatten_vecs(self, vecs):
        result = []
        for vec in vecs:
            result += list(vec)
        return result
    
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
    
    def _init_shader(self):
        prog = self.program = glCreateProgram()
        
        vsh = self._load_shader(f'{CURRDIR}/shader_vertex.glsl', GL_VERTEX_SHADER)
        glAttachShader(prog, vsh)
        
        fsh = self._load_shader(f'{CURRDIR}/shader_fragment.glsl', GL_FRAGMENT_SHADER)
        glAttachShader(prog, fsh)
        
        glLinkProgram(prog)
        if not self._get_program_iv(prog, GL_LINK_STATUS):
            raise RuntimeError('Failed to link shader program: ', self._get_program_log(program))
        glDeleteShader(vsh)
        glDeleteShader(fsh)
        glUseProgram(prog)
    
    def _load_shader(self, filename, shadertype):
        glid = glCreateShader(shadertype)
        glShaderSource(glid, [self._read_shader_source(filename)])
        glCompileShader(glid)
        if not self._get_shader_iv(glid, GL_COMPILE_STATUS):
            raise RuntimeError('Failed to compile shader: ', self._get_shader_log(glid))
        return glid
    
    def _read_shader_source(self, filename):
        with open(filename) as f:
            return f.read()
    
    def _get_shader_iv(self, shader, attr):
        tmp = ctypes.c_int(0)
        glGetShaderiv(shader, attr, ctypes.byref(tmp))
        return tmp.value
    
    def _get_shader_log(self, shader):
        return glGetShaderLogInfo(shader)
    
    def _get_program_iv(self, program, attr):
        tmp = ctypes.c_int(0)
        glGetProgramiv(program, attr, ctypes.byref(tmp))
        return tmp.value
    
    def _get_program_log(self, program):
        return glGetProgramInfoLog(program)
    
    def _change_monitor(self, monitorid):
        self.monitor = self._get_monitor(monitorid)
        vidmode = glfwGetVideoMode(self.monitor)
        glfwSetWindowMonitor(self.wnd, self.monitor, 0, 0, vidmode.size.width, vidmode.size.height, vidmode.refresh_rate)
        self.wants_monitor = None
    
    def _get_monitor(self, monitorid):
        monitors = glfwGetMonitors()
        if monitorid < 0 or monitorid >= len(monitors):
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
        self.shape_front.load_texture()
        self.shape_left.load_texture()
        self.shape_right.load_texture()
        
        glClear(GL_COLOR_BUFFER_BIT)
        
        self.shape_front.draw()
        self.shape_left.draw()
        self.shape_right.draw()
        
        glfwSwapBuffers(self.wnd)


def main():
    displayer = Displayer()
    displayer.start()
    host = DisplayerHost(displayer)
    
    while not displayer.wants_terminate:
        host.handle_request()

if __name__ == '__main__':
    main()
