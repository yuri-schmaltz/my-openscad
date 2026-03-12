import bpy

class OPENSCAD_OT_quick_insert(bpy.types.Operator):
  bl_idname = "openscad_bridge.quick_insert"
  bl_label = "Quick Edit SCAD Script"
  bl_description = "Abre uma janela flutuante nativa com o editor de texto completo"

  def execute(self, context):
    props = context.scene.openscad_bridge
    
    # Check if we have a valid text block, otherwise create one
    text_name = props.text_block_name
    text = bpy.data.texts.get(text_name) if text_name else None
    
    if not text:
      text = bpy.data.texts.new("OpenSCAD_Script.scad")
      props.text_block_name = text.name
      
    # Identify existing windows to find the new one later
    old_windows = set(context.window_manager.windows)
    
    # Duplicate current area into a floating OS window
    bpy.ops.screen.area_dupli('INVOKE_DEFAULT')
    
    # Find the newly created window
    new_windows = set(context.window_manager.windows) - old_windows
    if new_windows:
      new_window = list(new_windows)[0]
      for area in new_window.screen.areas:
        area.type = 'TEXT_EDITOR'
        area.spaces.active.text = text
        break
        
    return {"FINISHED"}

  def invoke(self, context, event):
    return self.execute(context)


def register():
  bpy.utils.register_class(OPENSCAD_OT_quick_insert)

def unregister():
  bpy.utils.unregister_class(OPENSCAD_OT_quick_insert)
