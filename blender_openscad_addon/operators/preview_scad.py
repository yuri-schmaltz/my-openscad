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
    text_name = props.text_block_name

    source = ""
    if text_name:
      text = bpy.data.texts.get(text_name)
      if text:
        source = text.as_string()
      else:
        self.report({"WARNING"}, f"Text datablock '{text_name}' nao encontrado.")
    
    if not source and props.source_path:
      try:
        with open(props.source_path, "r", encoding="utf-8") as f:
          source = f.read()
      except Exception as e:
        self.report({"ERROR"}, f"Falha ao ler o arquivo: {e}")
        return {"CANCELLED"}
        
    if not source:
      self.report({"WARNING"}, "Nenhum arquivo/texto valido para gerar OpenSCAD.")
      return {"CANCELLED"}

    source = text.as_string()
    try:
      program = parse_scad(source)
      source_path = props.source_path or None
      eval_items = evaluate_program(program, source_path=source_path)
      objects = build_scene(context.scene, eval_items)
    except Exception as ex:
      def draw_error(self, context):
        self.layout.label(text="Falha no Parsing SCAD:")
        for line in str(ex).split('\n'):
          self.layout.label(text=line)
      bpy.context.window_manager.popup_menu(draw_error, title="OpenSCAD Error", icon='ERROR')
      self.report({"ERROR"}, f"Erro de parse/execucao: {ex}")
      return {"CANCELLED"}

    self.report({"INFO"}, f"Preview concluido: {len(objects)} objeto(s)")
    return {"FINISHED"}


def _check_live_preview():
  context = bpy.context
  if not hasattr(context, "scene") or not hasattr(context.scene, "openscad_bridge"):
    return 1.0
    
  props = context.scene.openscad_bridge
  if not props.live_preview or not props.text_block_name:
    return 1.0

  text = bpy.data.texts.get(props.text_block_name)
  if not text:
    return 1.0
    
  current_text = text.as_string()
  import hashlib
  current_hash = hashlib.md5(current_text.encode('utf-8')).hexdigest()
  
  if current_hash != props.last_text_hash:
    props.last_text_hash = current_hash
    # Update on change
    try:
      bpy.ops.openscad_bridge.preview('INVOKE_DEFAULT')
    except Exception:
      pass

  return 1.0


def register():
  bpy.utils.register_class(OPENSCAD_OT_preview)
  if not bpy.app.timers.is_registered(_check_live_preview):
    bpy.app.timers.register(_check_live_preview)


def unregister():
  if bpy.app.timers.is_registered(_check_live_preview):
    bpy.app.timers.unregister(_check_live_preview)
  bpy.utils.unregister_class(OPENSCAD_OT_preview)
