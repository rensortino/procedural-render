import bpy
from pathlib import Path
from math import radians
import time
import sys


argv = sys.argv
argv = argv[argv.index("--") + 1:]  # get all args after "--"
slice_idx = int(argv[0])
env_light_dir_name = argv[1]
material_dir_name = argv[2]
slice_size = 1000




def create_material_once(name):
    "Gets a bpy object with the specified name if it exists, otherwise it creates a new instance"
    retrieved = bpy.data.materials.get(name)
    if retrieved is not None:
        return retrieved
    return bpy.data.materials.new(name)

def clear_images():
    for img in bpy.data.images:
        if img.name in ["Diffuse", "Normal", "Roughness", "Specular"]:
            bpy.data.images.remove(img)
            
def create_node_once(nodes, name, location=(0,0)):
    existing = nodes.get(name)
    if existing is not None:
        return existing
    new_node = nodes.new('ShaderNodeTexImage')
    new_node.name = name
    new_node.location = location
    return new_node

def load_map_image(node, img_path, name, colorspace="sRGB"):
    existing = bpy.data.images.get(name)
    if existing is not None:
         bpy.data.images.remove(existing)
    node.image = bpy.data.images.load(img_path)
    node.image.colorspace_settings.name = colorspace
    node.image.name = name
    
def load_hdri_image(img_path, name):
    image = bpy.data.images.get(name)
    if image is None:
        image = bpy.data.images.load(img_path.as_posix())
    image.name = name
    return image
    
def set_env_light(image):
    bpy.data.worlds['World'].node_tree.nodes["Environment Texture"].image = image
    
    

env_light_paths = [
    "abandoned_bakery_4k.exr",
    "burnt_warehouse_4k.exr",
    "je_gray_02_4k.exr",
    "rural_asphalt_road_4k.exr",
    "studio_small_02_4k.exr",
]
# env_light_dir = Path("/home/rsortino/Downloads/DeepMaterialsData/Data_Deschaintre18/env_lights")
env_light_dir = Path(env_light_dir_name)

bpy.context.scene.render.image_settings.file_format = "PNG"

mat_name = f"M_tmp"
material = bpy.data.materials.get(mat_name)

# Set node tree editing
material.use_nodes = True
nodes = material.node_tree.nodes

bsdf_node = nodes.get("Specular BSDF")

start = time.time()

# maps_folder = Path("/home/rsortino/Downloads/DeepMaterialsData/Data_Deschaintre18/train")
material_folders = sorted(list(Path(material_dir_name).iterdir()))
slice_start = slice_idx * slice_size
slice_end = slice_start + slice_size
material_folders = material_folders[slice_start : slice_end]

for material_folder in material_folders:

    print(material_folder)

    if (material_folder / "render").exists():
        if len(list((material_folder / "render").iterdir())) == 20:
            print("Material already rendered, skipping")
            continue
    
    diffuse_image_path = (material_folder / "diffuse.png").as_posix()
    normal_image_path = (material_folder / "normal.png").as_posix()
    roughness_image_path = (material_folder / "roughness.png").as_posix()
    specular_image_path = (material_folder / "specular.png").as_posix()

    # Create a new image texture node for the texture maps
    diffuse_map_node = create_node_once(nodes, "DiffuseNode", location=(-600, 0))
    specular_map_node = create_node_once(nodes, "SpecularNode", location=(-300, 0))
    roughness_map_node = create_node_once(nodes, "RoughnessNode", location=(-300, 300))
    normal_map_node = create_node_once(nodes, "NormalNode", location=(-600, 300))
    normal_shader_node = nodes.new('ShaderNodeNormalMap')
    normal_shader_node.location = (-40, 300)
    
    # Load the texture images 
    load_map_image(diffuse_map_node, diffuse_image_path, name="Diffuse")
    load_map_image(specular_map_node, specular_image_path, name="Specular", colorspace="sRGB")
    load_map_image(roughness_map_node, roughness_image_path, name="Roughness", colorspace="Non-Color")
    load_map_image(normal_map_node, normal_image_path, name="Normal", colorspace="Non-Color")

    # Connect the texture nodes to the Principled BSDF inputs
    #material.node_tree.links.new(diffuse_map_node.outputs['Color'], bsdf_node.inputs['Base Color'])
    #material.node_tree.links.new(normal_map_node.outputs['Color'], normal_shader_node.inputs['Color'])
    #material.node_tree.links.new(normal_shader_node.outputs['Normal'], bsdf_node.inputs['Normal'])
    #material.node_tree.links.new(roughness_map_node.outputs['Color'], bsdf_node.inputs['Roughness'])
    #material.node_tree.links.new(specular_map_node.outputs['Color'], bsdf_node.inputs['Specular'])

    #obj = bpy.context.active_object
    # Remove existing material slots
    #obj.data.materials.clear()
    # Assign the material to the active object
    #obj.data.materials.append(material)
    
    # Render the image
    
    
    for env_path in env_light_paths:
        assert Path(env_light_dir / env_path).exists(), f"Environment light path {env_light_dir / env_path} does not exist"
        env_light_name = env_path.split(".")[0]
        env_light = load_hdri_image(env_light_dir / env_path, env_light_name)
        set_env_light(env_light)
        
        for rotation_angle in [0, 90, 180, 270]:
            dst_path = f'{material_folder}/render/{env_light_name}_rot{rotation_angle}'
            if Path(dst_path).with_suffix(".png").exists():
                print(f"Existing {dst_path}")
                continue
            bpy.data.worlds['World'].node_tree.nodes["Mapping"].inputs[2].default_value[2] = radians(rotation_angle)
            bpy.context.scene.render.filepath = dst_path
            bpy.ops.render.render(animation=False, write_still=True)
print("Elapsed Time: ", time.time() - start)