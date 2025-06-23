import bpy
import os

# -----------------------------------------------------------------------------
# EDIT THESE VALUES
# -----------------------------------------------------------------------------
# 1. The FULL, absolute path to your texture image.
TEXTURE_FILE_PATH = "/home/janga/Downloads/yerba-mate/source/Scaniverse/Scaniverse.jpg"

# 2. The FULL, absolute path where you want to save the final, packed model.
OUTPUT_GLB_PATH = "/home/janga/YOLO/models/yerba_mate_FINAL.glb"
# -----------------------------------------------------------------------------


# --- SCRIPT LOGIC (No need to edit below here) ---

print("Starting command-line texture and export script...")

# Find the first imported MESH object.
# This is more robust than guessing the name.
obj = next((o for o in bpy.data.objects if o.type == 'MESH'), None)

if obj is None:
    print("ERROR: No mesh object found in the file. Quitting.")
    bpy.ops.wm.quit_blender()

print(f"Found object: '{obj.name}'")

# Find the first material on that object.
if not obj.material_slots:
    print(f"ERROR: Object '{obj.name}' has no material slots. Quitting.")
    bpy.ops.wm.quit_blender()

mat = obj.material_slots[0].material
if mat is None:
    print(f"ERROR: No material found in the first slot of '{obj.name}'. Quitting.")
    bpy.ops.wm.quit_blender()

print(f"Found material: '{mat.name}'")

# Ensure the material uses nodes
mat.use_nodes = True
nodes = mat.node_tree.nodes
links = mat.node_tree.links

# Find the main shader node
principled_node = nodes.get("Principled BSDF")
if principled_node is None:
    # Sometimes it's named differently, let's find it by type
    principled_node = next((n for n in nodes if n.type == 'BSDF_PRINCIPLED'), None)

if principled_node is None:
    print("ERROR: Could not find the main 'Principled BSDF' shader node. Quitting.")
    bpy.ops.wm.quit_blender()

# Create an Image Texture node
tex_image_node = nodes.new(type='ShaderNodeTexImage')
tex_image_node.location = principled_node.location - Vector((300, 0))

# Load the image
print(f"Loading texture from: {TEXTURE_FILE_PATH}")
if not os.path.exists(TEXTURE_FILE_PATH):
    print(f"ERROR: Texture file not found at '{TEXTURE_FILE_PATH}'. Check the path.")
    bpy.ops.wm.quit_blender()
    
tex_image_node.image = bpy.data.images.load(TEXTURE_FILE_PATH)

# Link the nodes together
print(f"Connecting '{tex_image_node.name}' to '{principled_node.name}'...")
links.new(tex_image_node.outputs['Color'], principled_node.inputs['Base Color'])

# --- EXPORT THE FINAL MODEL ---
print(f"Exporting packed .glb file to: {OUTPUT_GLB_PATH}")

output_dir = os.path.dirname(OUTPUT_GLB_PATH)
os.makedirs(output_dir, exist_ok=True)

# Select only our target object for export
bpy.ops.object.select_all(action='DESELECT')
obj.select_set(True)

bpy.ops.export_scene.gltf(
    filepath=OUTPUT_GLB_PATH,
    export_format='GLB',
    use_selection=True
)

print("\n✅ DONE. Command-line process complete. 'yerba_mate_FINAL.glb' has been created.")
