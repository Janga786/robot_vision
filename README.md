# Robot Vision: Synthetic Data Generation for Object Detection

A Blender-based pipeline that generates fully labeled synthetic training data for object detection, plus the configuration to train an Ultralytics YOLO model on the result. It was built to train perception models for robotic manipulation and inspection tasks (Sawyer/Baxter platforms), where collecting and hand-labeling thousands of real images per object is impractical. Instead, a single photogrammetry scan of the target object is rendered under randomized cameras, poses, and lighting, composited onto real-world background photos, and exported with pixel-accurate YOLO bounding-box labels — no manual annotation required. The repository includes a complete worked example using a scanned beverage can as the target object.

## Pipeline

```
3D scan of object
      │
      ▼
apply_texture.py ──── bakes the scan texture onto the mesh and exports a
      │               packed .glb (models/yerba_mate_final.glb)
      ▼
background_generator.py ── downloads real-world photos into backgrounds/
      │
      ▼
generate_blender.py ── headless Blender (Cycles) renders the object with
      │                randomized camera distance, focal length, elevation,
      │                object scale/pose/position, and lighting; composites
      │                each render onto a random background; computes the
      │                2D bounding box by projecting mesh vertices through
      │                the camera; writes PNG + YOLO label pairs
      ▼
output_blender/{images,labels}
      │
      ▼
Ultralytics YOLO training (dataset.yaml, single class)
```

Key details of the generator (`generate_blender.py`):

- Renders with Cycles (GPU, 128 samples) at 640 x 640 with a transparent film, then uses Blender's compositor (Alpha Over) to place the render on a randomly chosen background image.
- Domain randomization per frame: camera radius 0.6–1.2 m, elevation 10–50 degrees, focal length 40–80 mm, object scale 1.2–1.8x, random rotation and XY placement, and a randomized sun plus point fill light (800–1500 W).
- Labels are computed analytically: every mesh vertex is projected into camera space and the axis-aligned extent of the visible vertices becomes the normalized YOLO box (`class cx cy w h`). Frames where the object falls outside the view are discarded and re-randomized.
- All ranges and paths are constants in the CONFIG section at the top of the script.

## Repository layout

```
.
├── apply_texture.py          # Asset prep: bake texture onto scan, export packed .glb
├── background_generator.py   # Download background photos for compositing
├── generate_blender.py       # Main synthetic dataset generator (run inside Blender)
├── dataset.yaml              # Ultralytics YOLO dataset config (single class: can)
├── requirements.txt          # Python dependencies
├── assets/
│   └── sample_can_model/     # Raw photogrammetry textures for the sample can
├── backgrounds/              # Sample background images used for compositing
├── models/                   # Processed 3D assets (.glb / .obj) used by the generator
└── yolo_model/
    └── train/                # Example training artifacts: args.yaml and batch
                              # visualizations from a YOLO11s training run
```

## Requirements

- [Blender](https://www.blender.org/) 2.80 or newer (developed and tested with 3.x). The generator scripts run inside Blender's bundled Python, so `bpy` does not need to be installed separately.
- Python 3.8+ for the helper script and training:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

A GPU is recommended: the generator sets Cycles to GPU rendering, and YOLO training is significantly faster with CUDA.

## Usage

### 1. Prepare the 3D asset (optional — a ready model is included)

`models/yerba_mate_final.glb` is already packed and ready. To rebuild it from a raw scan, open the scan in Blender and run the texture-baking script headlessly:

```bash
blender your_scan.blend --background --python apply_texture.py
```

Edit `TEXTURE_FILE_PATH` and `OUTPUT_GLB_PATH` at the top of `apply_texture.py` to point at your own scan texture and output location.

### 2. Collect background images (optional — samples are included)

`backgrounds/` ships with ten sample photos. To fetch your own set, add image URLs to the list in `background_generator.py` and run:

```bash
python background_generator.py
```

### 3. Generate the synthetic dataset

From the repository root:

```bash
blender --background --python generate_blender.py
```

This renders `NUM_IMAGES` (default 1000) labeled images into `output_blender/`:

```
output_blender/
├── images/
│   ├── synth_00000.png
│   ├── synth_00001.png
│   └── ...
└── labels/
    ├── synth_00000.txt   # e.g. "0 0.512345 0.498765 0.213456 0.401234"
    └── ...
```

Each label file contains one line per object in standard YOLO format: class id followed by the normalized center x, center y, width, and height of the bounding box.

### 4. Train the detector

```bash
yolo detect train data=dataset.yaml model=yolo11s.pt epochs=20 imgsz=640 batch=16
```

`yolo_model/train/` contains example artifacts from such a run (the full `args.yaml` plus label-distribution and training-batch visualizations). The training-batch images show the synthetic composites as the network sees them: the rendered can at varied scales and poses over real backgrounds, with the generated boxes overlaid.

Note that `dataset.yaml` validates on the training images for demonstration purposes; hold out a separate split (or real photos of the object) for meaningful evaluation.

## Extending to new objects

1. Scan the new object (e.g. with a phone photogrammetry app) and export the mesh and texture.
2. Bake and pack it with `apply_texture.py`.
3. Add the resulting `.glb` to the `MODELS` list in `generate_blender.py`. Multiple models can be listed; one is chosen at random per frame.
4. Update `nc`/`names` in `dataset.yaml` (and `CLASS_ID` in the generator) if training on more than one class.

## License

MIT — see [LICENSE](LICENSE).
