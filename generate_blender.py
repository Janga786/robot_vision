"""
generate_blender.py — Synthetic data generator for a single‑class YOLO dataset
-----------------------------------------------------------------------------
[VERSION 3.0 - FINAL]
• Loads one or more 3‑D models of objects (OBJ / GLB / GLTF)
• Randomises camera position, zoom, object scale / pose / location and lighting
• Composites rendered objects onto random real-world background images
• Renders PNGs plus YOLO‑formatted labels   (class 0  cx  cy  w  h)
• Compatible with Blender ≥ 2.80 (tested 3.x)

HOW TO RUN (headless):
  blender --background --python generate_blender.py

Edit the *CONFIG* section below to point at your model paths and output dir.
"""

# ────────────────────────────────────────────────────────────────────────────
# CONFIG — set these paths to match your system
# ───────────────────────────────────────────────────────────────────────────
MODELS = [
    # Use the new, ready-to-go .glb file
    "/home/janga/YOLO/models/yerba_mate_final.glb",
]

BACKGROUNDS_DIR = "/home/janga/YOLO/backgrounds"

NUM_IMAGES  = 1000
OUTPUT_DIR  = "/home/janga/YOLO/output_blender"
IMAGE_RES   = (640, 640)
CLASS_ID    = 0

# --- RANDOMIZATION SETTINGS ---

# ✅ ADJUSTED: Camera is now closer to the object on average
CAM_RAD_MIN, CAM_RAD_MAX = 0.6, 1.2  # Camera distance from origin (metres)
CAM_ELEV_MIN, CAM_ELEV_MAX = 10, 50  # Camera elevation (degrees)

# ✅ NEW: Camera Focal Length (Zoom). Higher number = more zoomed in.
FOCAL_MIN, FOCAL_MAX = 40, 80        # In millimeters

# ✅ ADJUSTED: Object scale is slightly larger for more presence
SCALE_MIN, SCALE_MAX = 1.2, 1.8

# Random object placement range (X, Y) in metres from the center
POS_X_MIN, POS_X_MAX = -0.2, 0.2
POS_Y_MIN, POS_Y_MAX = -0.2, 0.2

# Random light power
LIGHT_PWR_MIN, LIGHT_PWR_MAX = 800, 1500

# ----------------------------------------------------------------------------
import bpy
import os
import random
import math
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view

# ────────────────────────────────────────────────────────────────────────────
# Utility helpers
# ────────────────────────────────────────────────────────────────────────────

def clean_scene():
    """Delete everything except cameras and lights."""
    for obj in [o for o in bpy.data.objects if o.type not in {'CAMERA', 'LIGHT'}]:
        bpy.data.objects.remove(obj, do_unlink=True)


def setup_renderer():
    """Configure renderer settings for performance and output."""
    scn = bpy.context.scene
    scn.render.engine = 'CYCLES'
    scn.cycles.device = 'GPU'
    scn.render.film_transparent = True
    scn.render.image_settings.file_format = 'PNG'
    scn.render.resolution_x, scn.render.resolution_y = IMAGE_RES
    scn.cycles.samples = 128


def setup_compositor():
    """Set up compositor nodes to overlay render on a background image."""
    scn = bpy.context.scene
    scn.use_nodes = True
    tree = scn.node_tree
    
    for node in tree.nodes:
        tree.nodes.remove(node)

    render_layers = tree.nodes.new(type='CompositorNodeRLayers')
    alpha_over = tree.nodes.new(type='CompositorNodeAlphaOver')
    scale_node = tree.nodes.new(type='CompositorNodeScale')
    image_node = tree.nodes.new(type='CompositorNodeImage')
    composite_node = tree.nodes.new(type='CompositorNodeComposite')

    scale_node.space = 'RENDER_SIZE'

    tree.links.new(image_node.outputs['Image'], scale_node.inputs['Image'])
    tree.links.new(scale_node.outputs['Image'], alpha_over.inputs[1])
    tree.links.new(render_layers.outputs['Image'], alpha_over.inputs[2])
    tree.links.new(alpha_over.outputs['Image'], composite_node.inputs['Image'])
    
    return image_node


def ensure_camera():
    """Create a camera if none exists and return it."""
    cams = [o for o in bpy.data.objects if o.type == 'CAMERA']
    if cams:
        return cams[0]
    cam_data = bpy.data.cameras.new('Camera')
    cam_obj = bpy.data.objects.new('Camera', cam_data)
    bpy.context.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj
    return cam_obj


def ensure_light():
    """Ensure at least one sun and a random fill light exist."""
    for obj in [o for o in bpy.data.objects if o.type == 'LIGHT' and 'Fill' in o.name]:
        bpy.data.objects.remove(obj, do_unlink=True)

    if not [o for o in bpy.data.objects if o.type == 'LIGHT' and o.name == 'Sun']:
        sun_data = bpy.data.lights.new('Sun', 'SUN')
        sun_data.energy = random.uniform(2, 5)
        sun = bpy.data.objects.new('Sun', sun_data)
        bpy.context.collection.objects.link(sun)
        sun.location = (5, -5, 5)
        sun.rotation_euler = (0.7, 0.2, -0.7)

    fill_data = bpy.data.lights.new(name='Fill', type='POINT')
    fill = bpy.data.objects.new('Fill', fill_data)
    bpy.context.collection.objects.link(fill)
    fill.data.energy = random.uniform(LIGHT_PWR_MIN, LIGHT_PWR_MAX)
    fill.location = (random.uniform(-4, 4), random.uniform(-4, 4), random.uniform(1, 4))


def import_model(path):
    """Import a model from the given path."""
    ext = os.path.splitext(path)[1].lower()
    if ext in {'.glb', '.gltf'}:
        bpy.ops.import_scene.gltf(filepath=path)
    else:
        raise RuntimeError(f'Unsupported model format: {path}')
    return bpy.context.selected_objects


def randomise_object(obj):
    """Randomize object scale, rotation, and position."""
    obj.scale = (random.uniform(SCALE_MIN, SCALE_MAX),) * 3
    obj.rotation_euler = (random.uniform(0, 2 * math.pi),) * 3
    obj.location = (
        random.uniform(POS_X_MIN, POS_X_MAX),
        random.uniform(POS_Y_MIN, POS_Y_MAX),
        0
    )


def randomise_camera(cam_obj):
    """✅ UPDATED: Randomize camera position, rotation, and now zoom."""
    # Set camera zoom (focal length)
    cam_obj.data.lens = random.uniform(FOCAL_MIN, FOCAL_MAX)

    # Set camera position using spherical coordinates
    r = random.uniform(CAM_RAD_MIN, CAM_RAD_MAX)
    elev = math.radians(random.uniform(CAM_ELEV_MIN, CAM_ELEV_MAX))
    azim = random.uniform(0, 2 * math.pi)
    
    cam_obj.location = (
        r * math.cos(azim) * math.cos(elev),
        r * math.sin(azim) * math.cos(elev),
        r * math.sin(elev)
    )

    # Point camera towards the center of the random object placement area
    target_pos = Vector((
        random.uniform(POS_X_MIN, POS_X_MAX) / 2,
        random.uniform(POS_Y_MIN, POS_Y_MAX) / 2,
        0
    ))
    direction = target_pos - cam_obj.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam_obj.rotation_euler = rot_quat.to_euler()


def calc_yolo_bbox(obj, cam):
    """Calculate the YOLO-formatted bounding box of an object."""
    scene = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    evaluated_obj = obj.evaluated_get(dg)

    mesh = evaluated_obj.to_mesh()
    if not mesh.vertices:
        evaluated_obj.to_mesh_clear()
        return None

    coords_3d = [evaluated_obj.matrix_world @ v.co for v in mesh.vertices]
    coords_2d = [world_to_camera_view(scene, cam, p) for p in coords_3d]
    evaluated_obj.to_mesh_clear()

    visible_coords = [c for c in coords_2d if 0.0 <= c.x <= 1.0 and 0.0 <= c.y <= 1.0 and c.z > 0]
    if not visible_coords:
        return None

    xs, ys = zip(*[(c.x, c.y) for c in visible_coords])
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)

    cx = (xmin + xmax) / 2
    cy = 1 - ((ymin + ymax) / 2)
    w = xmax - xmin
    h = ymax - ymin
    
    bbox_vals = [cx, cy, w, h]
    for i in range(len(bbox_vals)):
        bbox_vals[i] = min(max(bbox_vals[i], 0.0), 1.0)

    return f"{CLASS_ID} {bbox_vals[0]:.6f} {bbox_vals[1]:.6f} {bbox_vals[2]:.6f} {bbox_vals[3]:.6f}"
# ────────────────────────────────────────────────────────────────────────────
# Main generation loop
# ────────────────────────────────────────────────────────────────────────────

def main():
    if not MODELS:
        raise RuntimeError('MODELS list is empty. Set valid paths at top of script.')
    
    background_files = [os.path.join(BACKGROUNDS_DIR, f) for f in os.listdir(BACKGROUNDS_DIR) 
                        if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    if not background_files:
        raise RuntimeError(f'No background images found in {BACKGROUNDS_DIR}.')

    img_dir = os.path.join(OUTPUT_DIR, 'images')
    lbl_dir = os.path.join(OUTPUT_DIR, 'labels')
    os.makedirs(img_dir, exist_ok=True)
    os.makedirs(lbl_dir, exist_ok=True)

    setup_renderer()
    cam = ensure_camera()
    bg_image_node = setup_compositor()

    rendered = 0
    frame_num = 0
    while rendered < NUM_IMAGES:
        clean_scene()
        
        imported_objs = import_model(random.choice(MODELS))
        
        # ✅ FIXED: Find the actual MESH object from the import, not just the first object.
        # This handles cases where the glb/gltf has a parent "Empty" object.
        obj = None
        for o in imported_objs:
            if o.type == 'MESH':
                obj = o
                break # Found it, stop looking
        
        # If no mesh was found in the imported file, skip this iteration.
        if obj is None:
            frame_num += 1
            print(f"ERROR: No MESH object found in the imported model. Skipping frame {frame_num}.")
            continue

        # Now, proceed with the correctly identified mesh object
        randomise_object(obj)
        randomise_camera(cam)
        ensure_light()
        
        bg_image_node.image = bpy.data.images.load(random.choice(background_files))
        bpy.context.view_layer.update()

        bbox = calc_yolo_bbox(obj, cam)
        if bbox is None:
            frame_num += 1
            print(f'Object not visible in frame {frame_num}, trying new randomisation.')
            bpy.data.images.remove(bg_image_node.image)
            continue

        base_filename = f'synth_{frame_num:05d}'
        bpy.context.scene.render.filepath = os.path.join(img_dir, f'{base_filename}.png')
        bpy.ops.render.render(write_still=True)

        with open(os.path.join(lbl_dir, f'{base_filename}.txt'), 'w') as f:
            f.write(bbox + '\n')
            
        bpy.data.images.remove(bg_image_node.image)

        rendered += 1
        frame_num += 1
        print(f'Rendered {rendered}/{NUM_IMAGES} -> {base_filename}.png')

    print(f'\n✅ DONE — Synthetic dataset with {NUM_IMAGES} images stored in {OUTPUT_DIR}')


if __name__ == '__main__':
    main()
