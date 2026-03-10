from __future__ import annotations

import bpy
from math import radians

from .ast import Primitive


PREVIEW_COLLECTION_NAME = "OpenSCAD Preview"


def ensure_preview_collection(scene: bpy.types.Scene) -> bpy.types.Collection:
  coll = bpy.data.collections.get(PREVIEW_COLLECTION_NAME)
  if coll is None:
    coll = bpy.data.collections.new(PREVIEW_COLLECTION_NAME)
    scene.collection.children.link(coll)
  return coll


def clear_preview_collection(scene: bpy.types.Scene) -> None:
  coll = bpy.data.collections.get(PREVIEW_COLLECTION_NAME)
  if not coll:
    return

  for obj in list(coll.objects):
    bpy.data.objects.remove(obj, do_unlink=True)


def _apply_transform_chain(obj: bpy.types.Object, chain: list[tuple[str, list[float]]]) -> None:
  for kind, values in chain:
    if kind == "translate" and len(values) >= 3:
      obj.location.x += values[0]
      obj.location.y += values[1]
      obj.location.z += values[2]
    elif kind == "rotate" and len(values) >= 3:
      obj.rotation_euler.x += radians(values[0])
      obj.rotation_euler.y += radians(values[1])
      obj.rotation_euler.z += radians(values[2])
    elif kind == "scale" and len(values) >= 3:
      obj.scale.x *= values[0]
      obj.scale.y *= values[1]
      obj.scale.z *= values[2]


def _apply_color(obj: bpy.types.Object, color: list[float] | None) -> None:
  if not color:
    return
  mat = bpy.data.materials.new(name=f"OpenSCAD_Mat_{obj.name}")
  mat.use_nodes = True
  bsdf = mat.node_tree.nodes.get("Principled BSDF")
  if bsdf:
    bsdf.inputs["Base Color"].default_value = color
  if obj.data and hasattr(obj.data, "materials"):
    if obj.data.materials:
      obj.data.materials[0] = mat
    else:
      obj.data.materials.append(mat)


def _build_primitive(coll: bpy.types.Collection, primitive: Primitive, transform_chain, color):
  kind = primitive.kind
  args = primitive.args

  if kind == "cube":
    size = args.get("size", args.get("arg0", [1.0, 1.0, 1.0]))
    if isinstance(size, (int, float)):
      size = [float(size), float(size), float(size)]
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0))
    obj = bpy.context.active_object
    obj.scale = (float(size[0]) / 2.0, float(size[1]) / 2.0, float(size[2]) / 2.0)
  elif kind == "sphere":
    r = float(args.get("r", args.get("arg0", 1.0)))
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=(0, 0, 0))
    obj = bpy.context.active_object
  elif kind == "cylinder":
    h = float(args.get("h", args.get("arg0", 1.0)))
    r = float(args.get("r", args.get("arg1", 1.0)))
    bpy.ops.mesh.primitive_cylinder_add(radius=r, depth=h, location=(0, 0, h / 2.0))
    obj = bpy.context.active_object
  else:
    return None

  if obj.name in bpy.context.scene.collection.objects:
    bpy.context.scene.collection.objects.unlink(obj)
  coll.objects.link(obj)

  _apply_transform_chain(obj, transform_chain)
  _apply_color(obj, color)
  return obj


def _compose_boolean(base: bpy.types.Object, other: bpy.types.Object, kind: str) -> bpy.types.Object:
  op_map = {
    "union": "UNION",
    "difference": "DIFFERENCE",
    "intersection": "INTERSECT",
    # Fallback aproximado para manter fluxo funcional no Blender.
    "hull": "UNION",
    "minkowski": "UNION",
  }
  mod = base.modifiers.new(name=f"OpenSCAD_{kind}", type="BOOLEAN")
  mod.operation = op_map.get(kind, "UNION")
  mod.object = other
  other.hide_set(True)
  other.hide_render = True
  return base


def _build_eval_item(coll, item):
  if item.node_type == "primitive" and item.primitive:
    return _build_primitive(coll, item.primitive, item.transform_chain, item.color)

  if item.node_type == "group":
    created = None
    for child in item.children:
      child_obj = _build_eval_item(coll, child)
      if created is None:
        created = child_obj
    return created

  if item.node_type == "boolean":
    objs = [o for o in (_build_eval_item(coll, ch) for ch in item.children) if o is not None]
    if not objs:
      return None
    base = objs[0]
    for other in objs[1:]:
      base = _compose_boolean(base, other, item.boolean_kind or "union")
    return base

  return None


def build_scene(scene: bpy.types.Scene, eval_items) -> list[bpy.types.Object]:
  clear_preview_collection(scene)
  coll = ensure_preview_collection(scene)
  created = []
  for item in eval_items:
    obj = _build_eval_item(coll, item)
    if obj is not None:
      created.append(obj)
  return created
