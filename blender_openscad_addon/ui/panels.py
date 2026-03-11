from __future__ import annotations

import bpy


class OPENSCAD_PT_bridge_panel(bpy.types.Panel):
  bl_label = "OpenSCAD Bridge"
  bl_idname = "OPENSCAD_PT_bridge_panel"
  bl_space_type = "VIEW_3D"
  bl_region_type = "UI"
  bl_category = "OpenSCAD"

  def draw(self, context):
    layout = self.layout
    props = context.scene.openscad_bridge

    # I/O Box
    box = layout.box()
    box.label(text="I/O Settings", icon='FILE_FOLDER')
    
    col = box.column(align=True)
    row = col.row(align=True)
    row.prop(props, "text_block_name", icon='TEXT')
    row.operator("openscad_bridge.quick_insert", text="", icon='GREASEPENCIL')
    
    col.prop(props, "source_path", icon='FILE_SCRIPT')
    
    # Build Settings Box
    box = layout.box()
    box.label(text="Build Settings", icon='MODIFIER')
    col = box.column(align=True)
    col.prop(props, "live_preview", icon='RESTRICT_VIEW_OFF')
    col.prop(props, "apply_boolean_modifiers", icon='MOD_BOOLEAN')
    col.prop(props, "fallback_segments", icon='MESH_CIRCLE')

    # Actions Box
    box = layout.box()
    box.label(text="Actions", icon='PLAY')
    row = box.row(align=True)
    row.operator("openscad_bridge.import_file", text="Import SCAD", icon='IMPORT')
    row.operator("openscad_bridge.export_selected", text="Export SCAD", icon='EXPORT')
    
    row = box.row(align=True)
    row.operator("openscad_bridge.preview", text="Preview", icon='FILE_REFRESH')
    row.operator("openscad_bridge.render", text="Render", icon='RENDER_STILL')


class OPENSCAD_PT_bridge_text_editor_panel(bpy.types.Panel):
  bl_label = "OpenSCAD Bridge"
  bl_idname = "OPENSCAD_PT_bridge_text_editor_panel"
  bl_space_type = "TEXT_EDITOR"
  bl_region_type = "UI"
  bl_category = "OpenSCAD"

  def draw(self, context):
    layout = self.layout
    props = context.scene.openscad_bridge

    if context.space_data.text:
      props.text_block_name = context.space_data.text.name

    box = layout.box()
    box.label(text="Quick Preview", icon='RESTRICT_VIEW_OFF')
    box.prop(props, "text_block_name", text="", icon='TEXT')
    box.prop(props, "live_preview", icon='TIME')
    box.operator("openscad_bridge.preview", text="Force Preview", icon='FILE_REFRESH')


def register():
  bpy.utils.register_class(OPENSCAD_PT_bridge_panel)
  bpy.utils.register_class(OPENSCAD_PT_bridge_text_editor_panel)


def unregister():
  bpy.utils.unregister_class(OPENSCAD_PT_bridge_text_editor_panel)
  bpy.utils.unregister_class(OPENSCAD_PT_bridge_panel)
