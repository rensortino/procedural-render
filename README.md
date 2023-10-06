# procedural-render

Script for procedurally creating renders from SVBRDF material maps. The renders feature different rotations with respect to the environment light and different light sources.

## Usage

```bash
blender scene_for_render.blend --background --python render_maps.py -- {slice_idx} {env_lights_dir} {materials_dir}
```
