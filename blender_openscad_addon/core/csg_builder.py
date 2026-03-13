from __future__ import annotations

import math
import bmesh  # type: ignore
import bpy  # type: ignore
from math import radians, pi, cos, sin

from .ast import Primitive  # type: ignore


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
      import mathutils  # type: ignore
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


def _get_fragments(r: float, args: dict) -> int:
  fn = int(float(args.get("$fn", 0)))
  if fn > 0:
      return fn
  
  fa = float(args.get("$fa", 12.0))
  fs = float(args.get("$fs", 2.0))
  
  # Minimum angle formula
  fragments_angle = int(math.ceil(360.0 / fa)) if fa > 0 else 5
  
  # Minimum size formula
  fragments_size = int(math.ceil(2 * math.pi * r / fs)) if fs > 0 else 5
  
  frag = max(fragments_angle, fragments_size)
  # OpenSCAD min fragments is 5 by default
  return max(5, frag)

def _build_primitive(coll: bpy.types.Collection, primitive: Primitive, transform_chain, color):
  kind = primitive.kind
  args = primitive.args

  if kind == "cube":
    size = args.get("size", args.get("arg0", [1.0, 1.0, 1.0]))
    center = args.get("center", False)
    if isinstance(size, (int, float)):
      size = [float(size), float(size), float(size)]
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0, 0, 0))
    obj = bpy.context.active_object
    obj.scale = (float(size[0]) / 2.0, float(size[1]) / 2.0, float(size[2]) / 2.0)
    
    if not center:
      # If center=false, OpenSCAD aligns the cube's corner at 0,0,0
      obj.location = (obj.scale.x, obj.scale.y, obj.scale.z)
  elif kind == "sphere":
    r = float(args.get("r", args.get("arg0", 1.0)))
    fn = _get_fragments(r, args)
    segments = max(4, fn)
    rings = max(4, fn // 2)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, segments=segments, ring_count=rings, location=(0, 0, 0))
    obj = bpy.context.active_object
  elif kind == "cylinder":
    h = float(args.get("h", args.get("arg0", 1.0)))
    r1 = float(args.get("r1", args.get("r", args.get("arg1", 1.0))))
    # OpenSCAD can also specify r2, fallback to r1 if missing
    r2 = float(args.get("r2", r1))
    center = args.get("center", False)
    
    fn = _get_fragments(max(r1, r2), args)
    segments = max(3, fn)
    
    # Cylinder in Blender requires building from cone to support r1/r2
    z_offset = 0 if center else h / 2.0
    bpy.ops.mesh.primitive_cone_add(vertices=segments, radius1=r1, radius2=r2, depth=h, location=(0, 0, z_offset))
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
    fn = _get_fragments(r, args)
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
          i = int(idx)  # type: ignore
          if 0 <= i < len(verts):
            face_verts.append(verts[i])  # type: ignore
        if len(face_verts) >= 3:
          try:
            bm.faces.new(face_verts)
          except ValueError:
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
  if kind == "hull" or kind == "minkowski":
    depsgraph = bpy.context.evaluated_depsgraph_get()
    
    base_eval = base.evaluated_get(depsgraph)
    me_a = bpy.data.meshes.new_from_object(base_eval)
    other_eval = other.evaluated_get(depsgraph)
    me_b = bpy.data.meshes.new_from_object(other_eval)
    
    bm_a = bmesh.new()
    bm_a.from_mesh(me_a)
    bmesh.ops.transform(bm_a, matrix=base.matrix_world, verts=bm_a.verts)
    
    bm_b = bmesh.new()
    bm_b.from_mesh(me_b)
    bmesh.ops.transform(bm_b, matrix=other.matrix_world, verts=bm_b.verts)
    
    bm_result = bmesh.new()
    
    if kind == "hull":
      for v in bm_a.verts:
        bm_result.verts.new(v.co)
      for v in bm_b.verts:
        bm_result.verts.new(v.co)
    else:
      # Minkowski Sum: For each vertex in A, add each vertex in B
      # Then convex hull the result
      # Note: This is a convex minkowski sum approximation which is standard
      # for polyhedron-polyhedron minkowski where they are convex. 
      # Full non-convex minkowski is extremely complex CSG.
      for va in bm_a.verts:
        for vb in bm_b.verts:
          bm_result.verts.new(va.co + vb.co)

    bmesh.ops.convex_hull(bm_result, kdop_margin=0.0)
    
    # Mapear de volta a matriz do base
    bmesh.ops.transform(bm_result, matrix=base.matrix_world.inverted(), verts=bm_result.verts)
    
    bm_result.to_mesh(base.data)
    
    bm_a.free()
    bm_b.free()
    bm_result.free()
    bpy.data.meshes.remove(me_a)
    bpy.data.meshes.remove(me_b)
    
    for mod in base.modifiers:
        base.modifiers.remove(mod)

    other.hide_set(True)
    other.hide_render = True
    return base

  op_map = {
    "union": "UNION",
    "difference": "DIFFERENCE",
    "intersection": "INTERSECT",
  }
  mod = base.modifiers.new(name=f"OSCAD_{kind}_{other.name}", type="BOOLEAN")
  mod.operation = op_map.get(kind, "UNION")
  mod.object = other
  # Ensure the modifier runs exactly where the other object is
  mod.solver = 'EXACT'
  other.hide_set(True)
  other.hide_render = True
  return base


def _build_eval_item(coll, item):
  if item.node_type == "primitive" and item.primitive:
    obj = _build_primitive(coll, item.primitive, item.transform_chain, item.color)
    return [obj] if obj else []
  if item.node_type == "polygon" and item.primitive:
    obj = _build_primitive(coll, item.primitive, item.transform_chain, item.color)
    return [obj] if obj else []

  if item.node_type == "extrude" and item.primitive:
    kind = item.primitive.args.get("kind", item.primitive.kind)
    args = item.primitive.args
    child_objs = []
    for ch in item.children:
      res = _build_eval_item(coll, ch)
      if res:
        child_objs.extend(res)
    
    if not child_objs:
      return []
    
    # In OpenSCAD, extrude often unions its children if multiple
    base = child_objs[0]
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
      
      # In OpenSCAD, rotate_extrude spins a 2D XY shape around the Y axis (or Z depending on view).
      # The distance from the Y axis becomes the radius.
      # If the node has child transforms (like translate), we must apply them *first* 
      # to the mesh vertices before spinning, so the origin remains at 0,0,0.
      _apply_transform_chain(base, item.transform_chain)
      # Clear the chain so we don't apply it again at the end of _build_eval_item
      item.transform_chain = []
      
      # Apply the transformation to the mesh data itself, leaving object origin at global 0,0,0
      bpy.context.view_layer.objects.active = base
      bpy.ops.object.select_all(action='DESELECT')
      base.select_set(True)
      bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
      
      # Now we forcefully rotate the mesh vertices by 90 degrees on X
      # so that the 2D plane (XY) aligns with XZ, making the Screw around Z work properly.
      import bmesh
      import mathutils
      bm = bmesh.new()
      bm.from_mesh(base.data)
      rx90 = mathutils.Matrix.Rotation(math.radians(90.0), 4, 'X')
      bmesh.ops.transform(bm, matrix=rx90, verts=bm.verts)
      bm.to_mesh(base.data)
      bm.free()
      
      # Now apply the screw modifier around the Z axis
      screw_mod = base.modifiers.new("OpenSCAD_RotExtrude", type="SCREW")
      screw_mod.angle = math.radians(angle)
      screw_mod.steps = steps
      screw_mod.iterations = 1
      screw_mod.axis = 'Z'
    if item.transform_chain:
      _apply_transform_chain(base, item.transform_chain)
    _apply_color(base, item.color)
    return [base]

  if item.node_type == "offset" and item.primitive:
    child_objs = []
    for ch in item.children:
      res = _build_eval_item(coll, ch)
      if res:
        child_objs.extend(res)
        
    if not child_objs:
      return []
    
    base = child_objs[0]
    # Rest of offset logic... (treating first child as base for now)
    r = float(item.primitive.args.get("r", 0.0))
    if r != 0.0:
      sol = base.modifiers.new("OpenSCAD_Offset", type="SOLIDIFY")
      sol.thickness = r
      sol.offset = 1.0
    
    if item.transform_chain:
      _apply_transform_chain(base, item.transform_chain)
    _apply_color(base, item.color)
    return [base]

  if item.node_type == "projection":
    child_objs = []
    for ch in item.children:
      res = _build_eval_item(coll, ch)
      if res:
        child_objs.extend(res)
        
    if not child_objs:
      return []
    
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
          return [obj]
      except Exception:
        pass
    return []


  if item.node_type == "group":
    created = []
    for child in item.children:
      res = _build_eval_item(coll, child)
      if res:
        created.extend(res)
    return created

  if item.node_type == "boolean":
    objs = []
    for ch in item.children:
      res = _build_eval_item(coll, ch)
      if res:
        objs.extend(res)
        
    if not objs:
      return []
      
    base = objs[0]
    kind = item.boolean_kind or "union"
    others = objs[1:]
    
    # In OpenSCAD, union combines all. Difference subtracts ALL following objects from the first.
    # Intersection intersects ALL objects.
    if kind == "union" and len(objs) > 1:
      # If it's a union, we can just apply boolean union to the base sequentially
      for other in others:
        base = _compose_boolean(base, other, "union")
    elif kind == "difference" and len(objs) > 1:
      # Difference subtracts all subsequent objects from the first one
      for other in others:
        base = _compose_boolean(base, other, "difference")
    elif kind == "intersection" and len(objs) > 1:
      for other in others:
        base = _compose_boolean(base, other, "intersection")
        
    return [base]

  return []


def build_scene(scene: bpy.types.Scene, eval_items) -> list[bpy.types.Object]:
  clear_preview_collection(scene)
  coll = ensure_preview_collection(scene)
  created = []
  for item in eval_items:
    res = _build_eval_item(coll, item)
    if res:
      created.extend(res)
  return created
