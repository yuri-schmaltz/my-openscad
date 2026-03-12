import bpy


class OpenSCADAddonProperties(bpy.types.PropertyGroup):
  text_block_name: bpy.props.StringProperty(
    name="SCAD Text",
    description="Nome do Text datablock com codigo OpenSCAD",
    default="",
  )

  source_path: bpy.props.StringProperty(
    name="SCAD File",
    subtype="FILE_PATH",
    description="Arquivo .scad para importar",
    default="",
  )

  live_preview: bpy.props.BoolProperty(
    name="Live Preview",
    description="Executa preview automatico ao digitar",
    default=True,
  )

  last_text_hash: bpy.props.StringProperty(
    default="",
  )

  apply_boolean_modifiers: bpy.props.BoolProperty(
    name="Apply Boolean on Render",
    description="Aplica modificadores booleanos no comando Render",
    default=True,
  )

  fallback_segments: bpy.props.IntProperty(
    name="Fallback Segments",
    description="Numero de segmentos para primitivas sem $fn",
    default=32,
    min=8,
    max=256,
  )


def register():
  bpy.utils.register_class(OpenSCADAddonProperties)
  bpy.types.Scene.openscad_bridge = bpy.props.PointerProperty(type=OpenSCADAddonProperties)


def unregister():
  del bpy.types.Scene.openscad_bridge
  bpy.utils.unregister_class(OpenSCADAddonProperties)
