import bpy


class OpenSCADAddonPreferences(bpy.types.AddonPreferences):
  bl_idname = __package__

  auto_create_text_block: bpy.props.BoolProperty(
    name="Create Text Block if Missing",
    default=True,
  )

  def draw(self, context):
    layout = self.layout
    layout.label(text="OpenSCAD Bridge Preferences")
    layout.prop(self, "auto_create_text_block")


def register():
  bpy.utils.register_class(OpenSCADAddonPreferences)


def unregister():
  bpy.utils.unregister_class(OpenSCADAddonPreferences)
