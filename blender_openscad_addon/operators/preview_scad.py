from __future__ import annotations

import bpy

from ..core.parser import parse_scad
from ..core.evaluator import evaluate_program
from ..core.csg_builder import build_scene


class OPENSCAD_OT_preview(bpy.types.Operator):
  bl_idname = "openscad_bridge.preview"
  bl_label = "Preview"
  bl_description = "Gera preview da cena OpenSCAD no Blender"

  def execute(self, context):
    props = context.scene.openscad_bridge
    if not props.text_block_name:
      self.report({"ERROR"}, "Defina um bloco de texto SCAD")
      return {"CANCELLED"}

    text = bpy.data.texts.get(props.text_block_name)
    if text is None:
      self.report({"ERROR"}, "Text datablock nao encontrado")
      return {"CANCELLED"}

    source = text.as_string()
    try:
      program = parse_scad(source)
      source_path = props.source_path or None
      eval_items = evaluate_program(program, source_path=source_path)
      objects = build_scene(context.scene, eval_items)
    except Exception as ex:
      self.report({"ERROR"}, f"Erro de parse/execucao: {ex}")
      return {"CANCELLED"}

    self.report({"INFO"}, f"Preview concluido: {len(objects)} objeto(s)")
    return {"FINISHED"}


def register():
  bpy.utils.register_class(OPENSCAD_OT_preview)


def unregister():
  bpy.utils.unregister_class(OPENSCAD_OT_preview)
