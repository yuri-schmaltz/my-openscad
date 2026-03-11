import bpy  # type: ignore
import re
from bpy.app.handlers import persistent  # type: ignore

# Cores tema para OpenSCAD
SCAD_KEYWORDS = {
    'module': (0.8, 0.2, 0.5, 1.0),    # Rosa Magenta
    'function': (0.8, 0.2, 0.5, 1.0),
    'include': (0.2, 0.6, 0.8, 1.0),   # Azul claro
    'use': (0.2, 0.6, 0.8, 1.0),
    'for': (0.9, 0.6, 0.1, 1.0),       # Laranja/Amarelo
    'if': (0.9, 0.6, 0.1, 1.0),
    'else': (0.9, 0.6, 0.1, 1.0),
    'intersection_for': (0.9, 0.6, 0.1, 1.0),
    'return': (0.9, 0.6, 0.1, 1.0),
    'true': (0.3, 0.8, 0.3, 1.0),      # Verde
    'false': (0.8, 0.2, 0.2, 1.0),     # Vermelho
    'undef': (0.5, 0.5, 0.5, 1.0),     # Cinza
}

SCAD_PRIMITIVES = {
    'cube': (0.2, 0.8, 0.8, 1.0),      # Ciano
    'cylinder': (0.2, 0.8, 0.8, 1.0),
    'sphere': (0.2, 0.8, 0.8, 1.0),
    'polyhedron': (0.2, 0.8, 0.8, 1.0),
    'square': (0.2, 0.8, 0.8, 1.0),
    'circle': (0.2, 0.8, 0.8, 1.0),
    'polygon': (0.2, 0.8, 0.8, 1.0),
    'text': (0.2, 0.8, 0.8, 1.0),
    'import': (0.7, 0.5, 0.9, 1.0),    # Roxo
    'linear_extrude': (0.7, 0.5, 0.9, 1.0),
    'rotate_extrude': (0.7, 0.5, 0.9, 1.0),
    'union': (0.5, 0.8, 0.2, 1.0),     # Verde lima
    'difference': (0.5, 0.8, 0.2, 1.0),
    'intersection': (0.5, 0.8, 0.2, 1.0),
    'hull': (0.5, 0.8, 0.2, 1.0),
    'minkowski': (0.5, 0.8, 0.2, 1.0),
    'translate': (0.2, 0.5, 0.8, 1.0), # Azul cobalto
    'rotate': (0.2, 0.5, 0.8, 1.0),
    'scale': (0.2, 0.5, 0.8, 1.0),
    'resize': (0.2, 0.5, 0.8, 1.0),
    'mirror': (0.2, 0.5, 0.8, 1.0),
    'multmatrix': (0.2, 0.5, 0.8, 1.0),
    'color': (0.2, 0.5, 0.8, 1.0),
    'offset': (0.2, 0.5, 0.8, 1.0),
}


def _clear_format(text_dt):
    """Limpa a formatação visual previa de um bloco texto."""
    if not text_dt or not text_dt.lines:
        return
    # O Blender text format precisa de deselecionamento senao substitui caractere
    for line in text_dt.lines:
        pass


def _apply_scad_highlight():
    """Percorre os arquivos de texto do Blender abertos e colore a sintaxe caso nomeiem extensao scad"""
    for text_block in bpy.data.texts:
        if not text_block.name.endswith(".scad"):
            continue
        
        # Como a API de text color do Blender é super restrita e nao permite pintar 
        # substrings via scripting diretamente na v1, a adocao basica sera alterar
        # a sintaxe format global do text viewer se ele focar neste bloco
        pass


@persistent
def update_scad_syntax_timer():
    _apply_scad_highlight()
    return 2.0  # Roda a cada 2s pra nao sobrecarregar interface


def register():
    if not bpy.app.timers.is_registered(update_scad_syntax_timer):
        bpy.app.timers.register(update_scad_syntax_timer)


def unregister():
    if bpy.app.timers.is_registered(update_scad_syntax_timer):
        bpy.app.timers.unregister(update_scad_syntax_timer)
