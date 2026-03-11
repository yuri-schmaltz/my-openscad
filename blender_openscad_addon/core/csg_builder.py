from __future__ import annotations

import math
import bmesh
import bpy
from math import radians, pi, cos, sin

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
    elif kind == "mirror" and len(values) >= 3:
      mx, my, mz = values[0], values[1], values[2]
      mod = obj.modifiers.new(name="OpenSCAD_Mirror", type="MIRROR")
      mod.use_axis[0] = abs(mx) > 0.5
      mod.use_axis[1] = abs(my) > 0.5
      mod.use_axis[2] = abs(mz) > 0.5
    elif kind == "resize" and len(values) >= 3:
      obj.scale.x = values[0] if values[0] != 0 else obj.scale.x
      obj.scale.y = values[1] if values[1] != 0 else obj.scale.y
      obj.scale.z = values[2] if values[2] != 0 else obj.scale.z
    elif kind == "multmatrix" and isinstance(values, list) and len(values) >= 4:
      import mathutils
      rows = values
      m = mathutils.Matrix([
        [float(rows[0][0]), float(rows[0][1]), float(rows[0][2]), float(rows[0][3])],
        [float(rows[1][0]), float(rows[1][1]), float(rows[1][2]), float(rows[1][3])],
        [float(rows[2][0]), float(rows[2][1]), float(rows[2][2]), float(rows[2][3])],
        [0.0,               0.0,               0.0,               1.0            ],
      ])
      obj.matrix_world = m @ obj.matrix_world


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
    fn = int(float(args.get("$fn", 32))) or 32
    # OpenSCAD subdivide spheres evenly, minimal 3 segments.
    segments = max(4, fn)
    rings = max(4, fn // 2)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=segments, ring_count=rings, location=(0, 0, 0))
    obj = bpy.context.active_object
  elif kind == "cylinder":
    h = float(args.get("h", args.get("arg0", 1.0)))
    r = float(args.get("r", args.get("arg1", 1.0)))
    fn = int(float(args.get("$fn", 32))) or 32
    segments = max(3, fn)
    bpy.ops.mesh.primitive_cylinder_add(vertices=segments, radius=r, depth=h, location=(0, 0, h / 2.0))
    obj = bpy.context.active_object
  elif kind == "polygon":
    pts = args.get("points", [])
    if not pts or not isinstance(pts, list):
      return None
    bm = bmesh.new()
    verts = []
    for pt in pts:
      if isinstance(pt, (list, tuple)) and len(pt) >= 2:
        verts.append(bm.verts.new((float(pt[0]), float(pt[1]), 0.0)))
    if len(verts) >= 3:
      bm.faces.new(verts)
    me = bpy.data.meshes.new("OpenSCAD_Polygon")
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new("OpenSCAD_Polygon", me)
  elif kind == "circle":
    r = float(args.get("r", args.get("arg0", 1.0)))
    fn = int(float(args.get("$fn", 32))) or 32
    bm = bmesh.new()
    verts = [bm.verts.new((r * cos(2 * pi * i / fn), r * sin(2 * pi * i / fn), 0.0)) for i in range(fn)]
    bm.faces.new(verts)
    me = bpy.data.meshes.new("OpenSCAD_Circle")
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new("OpenSCAD_Circle", me)
  elif kind == "square":
    size = args.get("size", args.get("arg0", [1.0, 1.0]))
    if isinstance(size, (int, float)):
      size = [float(size), float(size)]
    w, h = float(size[0]), float(size[1])
    center = bool(args.get("center", False))
    ox = -w / 2 if center else 0.0
    oy = -h / 2 if center else 0.0
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=1.0)
    for v in bm.verts:
      v.co.x = v.co.x * w / 2 + ox + w / 2
      v.co.y = v.co.y * h / 2 + oy + h / 2
    me = bpy.data.meshes.new("OpenSCAD_Square")
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new("OpenSCAD_Square", me)
  elif kind == "polyhedron":
    points = args.get("points", [])
    faces = args.get("faces", [])
    if not points or not faces or not isinstance(points, list) or not isinstance(faces, list):
      return None
    bm = bmesh.new()
    verts = []
    for pt in points:
      if isinstance(pt, (list, tuple)) and len(pt) >= 3:
        verts.append(bm.verts.new((float(pt[0]), float(pt[1]), float(pt[2]))))
    
    for face_indices in faces:
      if isinstance(face_indices, (list, tuple)) and len(face_indices) >= 3:
        face_verts = []
        for idx in face_indices:
          i = int(idx)
          if 0 <= i < len(verts):
            face_verts.append(verts[i])
        if len(face_verts) >= 3:
          try:
            bm.faces.new(face_verts)
          except Exception:
            pass  # Ignora self-intersecting faces repetidas

    # Limpar qualquer ponta solta para garantir validade    
    bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=0.0001)
    bm.normal_update()

    me = bpy.data.meshes.new("OpenSCAD_Polyhedron")
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new("OpenSCAD_Polyhedron", me)
  elif kind == "text":
    text_val = str(args.get("text", args.get("arg0", "")))
    size_val = float(args.get("size", 10.0))
    font_val = args.get("font", None)
    curve_data = bpy.data.curves.new(name="OpenSCAD_Text", type="FONT")
    curve_data.body = text_val
    curve_data.size = size_val
    if font_val and isinstance(font_val, str):
      try:
        curve_data.font = bpy.data.fonts.load(font_val)
      except Exception:
        pass
    curve_data.extrude = 0.0
    obj = bpy.data.objects.new("OpenSCAD_Text", curve_data)
  else:
    return None

  if obj.name in bpy.context.scene.collection.objects:
    bpy.context.scene.collection.objects.unlink(obj)
  coll.objects.link(obj)

  _apply_transform_chain(obj, transform_chain)
  _apply_color(obj, color)
  return obj


def _compose_boolean(base: bpy.types.Object, other: bpy.types.Object, kind: str) -> bpy.types.Object:
  if kind == "hull":
    # 1. Copia o obj base + target pra Meshes temporarios aplicando os modifiers  
    depsgraph = bpy.context.evaluated_depsgraph_get()
    
    base_eval = base.evaluated_get(depsgraph)
    me_a = bpy.data.meshes.new_from_object(base_eval)
    other_eval = other.evaluated_get(depsgraph)
    me_b = bpy.data.meshes.new_from_object(other_eval)
    
    # 2. Fundir vertices no espaco global numa base limpa
    bm = bmesh.new()
    bm.from_mesh(me_a)
    bmesh.ops.transform(bm, matrix=base.matrix_world, verts=bm.verts)
    
    bm_b = bmesh.new()
    bm_b.from_mesh(me_b)
    bmesh.ops.transform(bm_b, matrix=other.matrix_world, verts=bm_b.verts)
    
    for v in bm_b.verts:
      bm.verts.new(v.co)
    bm_b.free()
    
    # 3. Criar Convex Hull
    bmesh.ops.convex_hull(bm, kdop_margin=0.0)
    
    # Mapear de volta matriz de origem
    bmesh.ops.transform(bm, matrix=base.matrix_world.inverted(), verts=bm.verts)
    bm.to_mesh(base.data)
    bm.free()
    bpy.data.meshes.remove(me_a)
    bpy.data.meshes.remove(me_b)
    
    # Limpar modifiers se existirem (agora é poligonal purista)
    for mod in base.modifiers:
        base.modifiers.remove(mod)

    other.hide_set(True)
    other.hide_render = True
    return base

  op_map = {
    "union": "UNION",
    "difference": "DIFFERENCE",
    "intersection": "INTERSECT",
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
  if item.node_type == "polygon" and item.primitive:
    return _build_primitive(coll, item.primitive, item.transform_chain, item.color)

  if item.node_type == "extrude" and item.primitive:
    kind = item.primitive.args.get("kind", item.primitive.kind)
    args = item.primitive.args
    child_objs = [o for o in (_build_eval_item(coll, ch) for ch in item.children) if o is not None]
    if not child_objs:
      return None
    base = child_objs[0] if len(child_objs) == 1 else child_objs[0]
    # Join children if multiple
    if len(child_objs) > 1:
      bpy.ops.object.select_all(action='DESELECT')
      for o in child_objs:
        o.select_set(True)
      bpy.context.view_layer.objects.active = child_objs[0]
      bpy.ops.object.join()
      base = bpy.context.active_object
    if "linear_extrude" in kind or kind == "linear_extrude":
      height = float(args.get("height", args.get("arg0", 1.0)))
      bpy.ops.object.select_all(action='DESELECT')
      base.select_set(True)
      bpy.context.view_layer.objects.active = base
      bpy.ops.object.mode_set(mode='EDIT')
      bpy.ops.mesh.select_all(action='SELECT')
      bpy.ops.mesh.extrude_region_move(
        TRANSFORM_OT_translate={"value": (0, 0, height)}
      )
      bpy.ops.object.mode_set(mode='OBJECT')
    elif "rotate_extrude" in kind or kind == "rotate_extrude":
      angle = float(args.get("angle", 360.0))
      steps = int(float(args.get("$fn", 32))) or 32
      bpy.ops.object.select_all(action='DESELECT')
      base.select_set(True)
      bpy.context.view_layer.objects.active = base
      screw_mod = base.modifiers.new("OpenSCAD_RotExtrude", type="SCREW")
      screw_mod.angle = math.radians(angle)
      screw_mod.steps = steps
      screw_mod.iterations = 1
      screw_mod.axis = 'Y'
    _apply_transform_chain(base, item.transform_chain)
    _apply_color(base, item.color)
    return base

  if item.node_type == "offset" and item.primitive:
    child_objs = [o for o in (_build_eval_item(coll, ch) for ch in item.children) if o is not None]
    if not child_objs:
      return None
    base = child_objs[0]
    r = float(item.primitive.args.get("r", 0.0))
    if r != 0.0:
      sol = base.modifiers.new("OpenSCAD_Offset", type="SOLIDIFY")
      sol.thickness = r
      sol.offset = 1.0
    _apply_transform_chain(base, item.transform_chain)
    _apply_color(base, item.color)
    return base

  if item.node_type == "projection":
    child_objs = [o for o in (_build_eval_item(coll, ch) for ch in item.children) if o is not None]
    if not child_objs:
      return None
    base = child_objs[0]
    _apply_transform_chain(base, item.transform_chain)
    _apply_color(base, item.color)
    return base

  if item.node_type == "import" and item.primitive:
    path = item.primitive.args.get("path", "")
    if path and isinstance(path, str):
      path_lower = path.lower()
      try:
        if path_lower.endswith(".stl"):
          bpy.ops.import_mesh.stl(filepath=path)
        elif path_lower.endswith(".obj"):
          bpy.ops.wm.obj_import(filepath=path)
        elif path_lower.endswith(".3mf"):
          bpy.ops.import_mesh.threemf(filepath=path)
        elif path_lower.endswith(".svg"):
          # SVG carrega colecoes de curvas ao inves de uma variavel obj_import fixa.
          # Vamos isolar para retornar o primeiro mesh convertido.
          bpy.ops.object.select_all(action='DESELECT')
          bpy.ops.import_curve.svg(filepath=path)
          imported_curves = bpy.context.selected_objects
          if imported_curves:
            bpy.context.view_layer.objects.active = imported_curves[0]
            bpy.ops.object.convert(target='MESH')
            if len(imported_curves) > 1:
              bpy.ops.object.join()
        else:
          return None
        obj = bpy.context.active_object
        if obj:
          if obj.name in bpy.context.scene.collection.objects:
            bpy.context.scene.collection.objects.unlink(obj)
          coll.objects.link(obj)
          _apply_transform_chain(obj, item.transform_chain)
          _apply_color(obj, item.color)
          return obj
      except Exception:
        pass
    return None


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
