import bpy
from bpy.props import *
from bpy.types import Panel, Menu, Operator, PropertyGroup, Scene
from bpy.utils import register_class, unregister_class

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


collection = None
cam_front_data = cam_left_data = cam_right_data = None
cam_front      = cam_left      = cam_right      = None


def update_enabled(props, context):
    if props.enabled:
        start_preview(props, context)
    else:
        stop_preview(props, context)

def start_preview(props, context):
    acquire_collection()
    acquire_cameras()
    # TODO: Translate & rotate cameras
    # TODO: Render & stitch front, left, right views
    pass

def stop_preview(props, context):
    bpy.data.scenes[0].collection.children.unlink(collection)
    bpy.data.collections.remove(collection)
    
    for cam in [cam_front, cam_left, cam_right]:
        bpy.data.objects.remove(cam)
    for dat in [cam_front_data, cam_left_data, cam_right_data]:
        bpy.data.cameras.remove(dat)

def acquire_collection():
    global collection
    if 'DreamocHD3LiveLink' in bpy.data.collections:
        collection = bpy.data.collections['DreamocHD3LiveLink']
    else:
        collection = bpy.data.collections.new('DreamocHD3LiveLink')
    bpy.data.scenes[0].collection.children.link(collection)

def acquire_cameras():
    global cam_front, cam_front_data, cam_left, cam_left_data, cam_right, cam_right_data
    cam_front, cam_front_data = acquire_camera('DreamocHD3LL_front')
    cam_left,  cam_left_data  = acquire_camera('DreamocHD3LL_left')
    cam_right, cam_right_data = acquire_camera('DreamocHD3LL_right')

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


def update_camera_distance(props, context):
    dist = props.camera_distance
    # TODO: Adjust distance of front, left, right cameras to origin


class DreamocHD3LivePreviewProps(PropertyGroup):
    enabled : BoolProperty(
        name="Enable",
        description="Enable the live preview.",
        default=False,
        update=update_enabled,
    )
    
    display_number : IntProperty(
        name="Display number",
        description="Number of the holographic display as registered with the operating system.",
        default=2,
        min=1,
    )
    
    camera_distance : FloatProperty(
        name="Camera distance",
        description="Distance of all three cameras to the origin.",
        default=500,
        min=0,
        update=update_camera_distance,
    )

class DreamocHD3LivePreviewPanel(Panel):
    bl_idname = "OBJECT_PT_dreamoc_hd3_live_preview"
    bl_label  = "Dreamoc HD3 Live Preview"
    bl_space_type  = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context     = "output"
    
    def draw_header(self, context):
        self.layout.prop(bpy.data.scenes[0].dreamocpreviewprops, 'enabled', text='')
    
    def draw(self, context):
        layout = self.layout
        props  = bpy.data.scenes[0].dreamocpreviewprops
        layout.enabled = props.enabled
        layout.prop(props, 'display_number')
        layout.prop(props, 'camera_distance')



classes = (
    DreamocHD3LivePreviewProps,
    DreamocHD3LivePreviewPanel,
)

def register():
    for curr in classes:
        register_class(curr)
    Scene.dreamocpreviewprops = PointerProperty(type=DreamocHD3LivePreviewProps)
    

def unregister():
    for curr in reversed(classes):
        unregister_class(curr)
