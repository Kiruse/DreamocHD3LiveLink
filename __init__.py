import sys
import os
currdir = os.path.abspath(os.path.dirname(__file__))
sys.path.append(currdir)

import bpy
from bpy.props import *
from bpy.types import Panel, Menu, Operator, PropertyGroup, Scene
from bpy.utils import register_class, unregister_class
from mathutils import Euler, Vector, Quaternion
from math import degrees, radians
import numpy as np

from ipc import DisplayerClient

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

displayer = None
cam = None


def render(ctx, props, filepath = None):
    render = ctx.scene.render
    with TempOverride() as ovr:
        ovr.override(ctx.scene, 'camera', cam)
        ovr.override(render, 'resolution_x', props.img_width)
        ovr.override(render, 'resolution_y', props.img_height)
        if filepath is not None: ovr.override(render, 'filepath', filepath)
        ovr.override(render.image_settings, 'file_format', 'PNG')
        ovr.override(ctx.scene.world.node_tree.nodes['Background'].inputs[0], 'default_value', (0, 0, 0, 1))
        
        bpy.ops.render.render(write_still=True)

def acquire_camera(name):
    cameras = bpy.data.cameras
    objects = bpy.data.objects
    scene   = bpy.context.scene
    
    if name in cameras:
        data = cameras[name]
    else:
        data = cameras.new(name)
    
    if name in objects:
        cam  = objects[name]
    else:
        cam  = objects.new(name, data)
    
    if cam not in scene.collection.objects.values():
        scene.collection.objects.link(cam)
    
    return cam

def getObjectQuat(obj):
    mode = obj.rotation_mode
    if mode == 'QUATERNION':
        return obj.rotation_quaternion
    if mode == 'AXIS_ANGLE':
        val = obj.rotation_axis_angle
        return Quaternion((val[0], val[1], val[2]), val[3])
    return obj.rotation_euler.to_quaternion()

def getCameraUpVector(cam, rotation = None):
    if rotation is None:
        rotation = getObjectQuat(cam)
    vec = Vector((0, 1, 0))
    vec.rotate(rotation)
    return vec

def getViewportOffset(region3d):
    offset = Vector((0, 0, region3d.view_distance))
    offset.rotate(region3d.view_rotation)
    return offset

def transformViewportRight(cam, camRotation, pivot, offset):
    _transformViewport(cam, camRotation, pivot, offset, 90)

def transformViewportLeft(cam, camRotation, pivot, offset):
    _transformViewport(cam, camRotation, pivot, offset, -90)

def _transformViewport(cam, camRotation, pivot, offset, rotation_magnitude):
    up = getCameraUpVector(cam, rotation=camRotation)
    rotation = Quaternion(up.to_tuple(), radians(rotation_magnitude))
    
    newOffset = offset.copy()
    newOffset.rotate(rotation)
    
    cam.location = pivot + newOffset
    
    cam.rotation_mode = 'QUATERNION'
    cam.rotation_quaternion = camRotation.copy()
    cam.rotation_quaternion.rotate(rotation)


class TempOverride:
    def __init__(self):
        self.overrides = []
    
    def __enter__(self):
        return self
    
    def __exit__(self, *args, **kwargs):
        for override in self.overrides:
            obj = override['object']
            for attr in override['attrs']:
                setattr(obj, attr, override['attrs'][attr])
    
    def override(self, obj, attr, value):
        ovr = self.getObjectOverride(obj)
        ovr['attrs'][attr] = getattr(obj, attr)
        setattr(obj, attr, value)
    
    def getObjectOverride(self, obj):
        for override in self.overrides:
            if override['object'] == obj:
                return override
        res = {'object': obj, 'attrs': {}}
        self.overrides.append(res)
        return res

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
        default=1280,
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
        layout.operator("dreamochd3.preview_update")
        layout.prop(props, 'display_number')
        layout.prop(props, 'img_width')
        layout.prop(props, 'img_height')

class DreamocHD3LivePreviewUpdateOperator(Operator):
    bl_idname = "dreamochd3.preview_update"
    bl_label  = "Update Dreamoc HD3 Preview"
    
    def execute(self, context):
        global cam
        cam = acquire_camera('DreamocHD3PreviewCamera')
        props = context.scene.dreamocpreviewprops
        
        area = self._getView3DArea(context)
        region = self._getRegion3D(area)
        ctx = {'area': area, 'region': self._getWindowRegion(area)}
        
        oldcam = context.scene.camera
        context.scene.camera = cam
        
        pivot  = Vector(region.view_location)
        offset = getViewportOffset(region)
        
        # Since this is our camera we don't care about resetting it
        cam.rotation_mode = 'QUATERNION'
        
        # Front view
        try: bpy.ops.view3d.camera_to_view(ctx)
        except: pass
        basequat = getObjectQuat(cam).copy() # Original rotation of the viewport camera
        render(context, props, filepath=f'{currdir}/tmp/front')
        
        # Left view
        transformViewportLeft(cam, basequat, pivot, offset)
        render(context, props, filepath=f'{currdir}/tmp/left')
        
        # Right view
        transformViewportRight(cam, basequat, pivot, offset)
        render(context, props, filepath=f'{currdir}/tmp/right')
        
        bpy.ops.view3d.view_camera(ctx)
        
        return {'FINISHED'}
    
    def _getView3DArea(self, ctx):
        for area in ctx.screen.areas:
            if area.type == 'VIEW_3D':
                return area
        return None
    
    def _getWindowRegion(self, area):
        for region in area.regions:
            if region.type == 'WINDOW':
                return region
    
    def _getRegion3D(self, area):
        assert area.type == 'VIEW_3D'
        return area.spaces[0].region_3d



classes = (
    DreamocHD3LivePreviewProps,
    DreamocHD3LivePreviewPanel,
    DreamocHD3LivePreviewUpdateOperator,
)

def register():
    for curr in classes:
        register_class(curr)
    Scene.dreamocpreviewprops = PointerProperty(type=DreamocHD3LivePreviewProps)
    
    global displayer
    # displayer = DisplayerClient()
    # displayer.open()

def unregister():
    for curr in reversed(classes):
        unregister_class(curr)
    # displayer.terminate()
