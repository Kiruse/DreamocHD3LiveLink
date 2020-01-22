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


class DreamocHD3LivePreviewProps(PropertyGroup):
    enabled : BoolProperty(
        name="Enable",
        description="Enable the live preview.",
        default=False,
    )
    
    display_number : IntProperty(
        name="Display Number",
        description="Number of the holographic display as registered with the operating system.",
        default=2,
        min=1,
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
