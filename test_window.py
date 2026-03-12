import bpy

def open_text_editor(text_name):
    # Get or create text
    text = bpy.data.texts.get(text_name)
    if not text:
        text = bpy.data.texts.new(text_name)
        
    # Duplicate current area into a new window? 
    # Actually, bpy.ops.wm.window_new() might work.
    
    # Let's just print available operators
    print(dir(bpy.ops.wm))
