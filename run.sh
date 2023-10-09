for i in {0..150}
do
    blender scene_for_render.blend --background --python render_maps.py -- $i /path/to/env/lights /path/to/materials
done
