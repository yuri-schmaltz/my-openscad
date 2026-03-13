import bpy
import time
import sys
import os

addon_dir = "/home/yurix/Documentos/my-openscad/blender_openscad_addon"
sys.path.append(addon_dir)

import core.parser as parser
import core.evaluator as evaluator
import core.csg_builder as csg_builder

print("\n\n========================================================")
print("--- Starting 1000 Object Exhaustive Test ---")
scad_file = "/home/yurix/Documentos/my-openscad/test_1000_objects.scad"

with open(scad_file, "r") as f:
    source = f.read()

start_time = time.time()

try:
    print("1. Parsing SCAD AST...")
    program = parser.parse_scad(source)
    parse_time = time.time()
    print(f"   AST Parsed in {parse_time - start_time:.4f} seconds")

    print("2. Evaluating Program Context...")
    eval_items = evaluator.evaluate_program(program)
    eval_time = time.time()
    print(f"   Evaluation finished in {eval_time - parse_time:.4f} seconds")

    print("3. Building CSG Scene inside Blender (BMesh operations)...")
    
    # Needs a mock scene properly set up for context when headless
    scene = bpy.context.scene
    
    objects = csg_builder.build_scene(scene, eval_items)
    build_time = time.time()
    
    print(f"   CSG Builder finished in {build_time - eval_time:.4f} seconds")
    
    print("4. Verifying Precision (Applying CSG Modifiers & Counting Geometry)...")
    total_verts = 0
    total_faces = 0
    
    # Apply all modifiers to get the final "baked" CSG meshes and count precision
    depsgraph = bpy.context.evaluated_depsgraph_get()
    for obj in objects:
        if obj.type == 'MESH':
            eval_obj = obj.evaluated_get(depsgraph)
            mesh = eval_obj.to_mesh()
            total_verts += len(mesh.vertices)
            total_faces += len(mesh.polygons)
            eval_obj.to_mesh_clear()
            
    verify_time = time.time()
    print(f"   Geometry Verification finished in {verify_time - build_time:.4f} seconds")
    
    print("========================================================")
    print("--- Test completed successfully ---")
    print(f"Total Top-Level Objects Created: {len(objects)}")
    print(f"Total True CSG Vertices Generated: {total_verts:,}")
    print(f"Total True CSG Faces Generated: {total_faces:,}")
    print(f"Total Time Elapsed: {verify_time - start_time:.4f} seconds")
    print("========================================================\n\n")
except Exception as e:
    import traceback
    traceback.print_exc()
    print("TEST FAILED")
    sys.exit(1)

sys.exit(0)
