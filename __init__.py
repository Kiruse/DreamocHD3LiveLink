import sys
import os
currdir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(currdir)

import bpy
from bpy.props import *
from bpy.types import Panel, Menu, Operator, PropertyGroup, Scene
from bpy.utils import register_class, unregister_class
from math import degrees, radians
import numpy as np

addon_name = __name__

bl_info = {
    "name": "RealFiction Dreamoc HD3 LiveLink",
    "description": "A live preview of the 3D scene for the RealFiction Dreamoc HD3.2.",
    "author": "Kiruse",
    "version": (0,  0, 1),
    "blender": (2, 80, 0),
    "location": "View3D > Properties > Output",
    "support": "COMMUNITY",
    "category": "View3D",
}

cam = camdat = None


def render(ctx, props):
    render = ctx.scene.render
    oldcam  = ctx.scene.camera
    olddims = (render.resolution_x, render.resolution_y)
    
    ctx.scene.camera = cam
    render.resolution_x, render.resolution_y = props.img_width, props.img_height
    
    bpy.ops.render.render()
    
    ctx.scene.camera = oldcam
    render.resolution_x, render.resolution_y = olddims
    return np.array(bpy.data.images['Viewer Node'].pixels)

def acquire_camera(name):
    cameras = bpy.data.cameras
    objects = bpy.data.objects
    
    if name in cameras:
        data = cameras[name]
    else:
        data = cameras.new(name)
    
    if name in objects:
        cam  = objects[name]
    else:
        cam  = objects.new(name, data)
        collection.objects.link(cam)
    
    return cam, data


class DreamocHD3LivePreviewProps(PropertyGroup):
    display_number : IntProperty(
        name="Display number",
        description="Number of the holographic display as registered with the operating system.",
        default=2,
        min=1,
    )
    
    img_width : IntProperty(
        name="Render width",
        description="Width of each view's rendered image.",
        default=1080,
        min=50,
        max=3840,
    )
    
    img_height : IntProperty(
        name="Render height",
        description="Height of each view's rendered image.",
        default=720,
        min=50,
        max=2160,
    )

class DreamocHD3LivePreviewPanel(Panel):
    bl_idname = "OBJECT_PT_dreamoc_hd3_live_preview"
    bl_label  = "Dreamoc HD3 Live Preview"
    bl_space_type  = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context     = "render"
    
    # DEPRECATED because Blender cannot render nowhere near 30FPS due to the render result being downloaded from GPU.
    # Would require implementing a custom RenderEngine and using bgl calls to render directly to a View3D type area.
    # def draw_header(self, context):
    #     self.layout.prop(context.scene.dreamocpreviewprops, 'enabled', text='')
    
    def draw(self, context):
        layout = self.layout
        props  = context.scene.dreamocpreviewprops
        # layout.enabled = props.enabled
        layout.operator("dreamochd3.update")
        layout.prop(props, 'display_number')
        layout.prop(props, 'img_width')
        layout.prop(props, 'img_height')

class DreamocHD3LivePreviewUpdateOperator(Operator):
    bl_idname = "dreamochd3.update"
    bl_label  = "Dreamoc HD3 Preview Update"
    
    def execute(self, context):
        # TODO: Set camera to viewport and render
        # TODO: Set camera to left & right relative to viewport parameters and render
        return {'FINISHED'}



classes = (
    DreamocHD3LivePreviewProps,
    DreamocHD3LivePreviewPanel,
    DreamocHD3LivePreviewUpdateOperator,
)

def register():
    for curr in classes:
        register_class(curr)
    Scene.dreamocpreviewprops = PointerProperty(type=DreamocHD3LivePreviewProps)

def unregister():
    for curr in reversed(classes):
        unregister_class(curr)
