bl_info = {
  "name": "OpenSCAD Bridge for Blender",
  "author": "Copilot",
  "version": (0, 1, 1),
  "blender": (5, 0, 0),
  "location": "View3D > Sidebar > OpenSCAD",
  "description": "Bridge OpenSCAD-like workflow inside Blender",
  "category": "Import-Export",
}

from . import properties
from .ui import panels, syntax_highlighter
from .operators import import_scad, export_scad, preview_scad, render_scad

import bpy

classes = (
    properties.OpenSCADBridgeProperties,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.openscad_bridge = bpy.props.PointerProperty(type=properties.OpenSCADBridgeProperties)
    
    panels.register()
    syntax_highlighter.register()
    import_scad.register()
    export_scad.register()
    preview_scad.register()
    render_scad.register()

def unregister():
    render_scad.unregister()
    preview_scad.unregister()
    export_scad.unregister()
    import_scad.unregister()
    syntax_highlighter.unregister()
    panels.unregister()
    
    del bpy.types.Scene.openscad_bridge
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
