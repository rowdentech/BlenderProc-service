import blenderproc as bproc
import os
import ast
import numpy as np
import datetime
import math
from pathlib import Path
import logging
import sys
import ast
logger = logging.getLogger("Synthetic Image Generation")

bproc.init()
logging.critical(os.environ["JSON_CONFIG"])
request = ast.literal_eval(os.environ["JSON_CONFIG"])
for k, v in request.items():
    os.environ[k] = str(v)

try:
    job_name = os.environ['data_name']
except KeyError as e:
    print('Name of job must be specified in os.environ.info.name')
    raise

# load the scene (.exr)
logging.critical(os.environ['scene_file_path'])
logging.critical(os.path.isfile(os.environ['scene_file_path']))
logging.critical(os.path.splitext(os.environ['scene_file_path'])[-1].lower() == '.exr')
if os.path.isfile(os.environ['scene_file_path']) \
        and os.path.splitext(os.environ['scene_file_path'])[-1].lower() == '.exr':
    logger.critical("Loading background {}".format(os.environ["scene_file_path"]))
    bproc.init(clean_up_scene=True)
    bproc.world.set_world_background_hdr_img(os.environ["scene_file_path"])
else:
    raise TypeError('Scene must be a OpenEXR file (.exr)')

# load object
if os.path.isfile(os.environ['object_file_path']) \
        and os.path.splitext(os.environ['object_file_path'])[-1].lower() == '.obj':
    label = os.environ["object_label"]
    logger.info("Loading object {} ({})".format(os.environ["object_file_path"], label))
    object_3d = bproc.loader.load_obj(os.environ["object_file_path"])
else:
    raise TypeError('Object must be an object file (.obj)')

for j, o in enumerate(object_3d):
    o.set_cp("category_id", j+1)
    o.set_scale([0.001, 0.001, 0.001])
    for mat in o.get_materials():
        mat.map_vertex_color()
poi = bproc.object.compute_poi(object_3d)
unique_job_name = job_name + datetime.datetime.now().strftime('_%Y%m%d%H%M%S%f')[:-3]
out_dir = "/data/vol2"
out_dir_temp = os.path.join(out_dir, "temp")

if not os.path.exists(out_dir_temp):
   os.makedirs(out_dir_temp)

if os.listdir(out_dir_temp):    # check if folder in out_dir_temp. if so append
    out_dir = os.path.join(out_dir_temp, os.listdir(out_dir_temp)[0])
else:   # no folder exists
    out_dir = os.path.join(out_dir_temp, unique_job_name)

images_per_batch=int(os.environ["batch_size"])

i = 0
check = 0
while i < images_per_batch:
    bproc.utility.reset_keyframes()
    print('================')
    print(f'{i}/{images_per_batch}')
    print('================')

    camera_shift_range_xyz = ast.literal_eval(os.environ["camera_shift_range_xyz"])
    shifted_poi = poi - np.random.uniform(
        [camera_shift_range_xyz[0][0],
         camera_shift_range_xyz[0][1],
         camera_shift_range_xyz[0][2]],
        [camera_shift_range_xyz[1][0],
         camera_shift_range_xyz[1][1],
         camera_shift_range_xyz[1][2]]
    )

    camera_location_range_xyz = ast.literal_eval(os.environ["camera_location_range_xyz"])
    location = np.random.uniform(
        [camera_location_range_xyz[0][0],
         camera_location_range_xyz[0][1],
         camera_location_range_xyz[0][2]],
        [camera_location_range_xyz[1][0],
         camera_location_range_xyz[1][1],
         camera_location_range_xyz[1][2]],
    )

    rotation_matrix = bproc.camera.rotation_from_forward_vec(
        shifted_poi - location, inplane_rot=np.random.uniform(-1.0, 1.0)
    )

    bproc.camera.add_camera_pose(
        bproc.math.build_transformation_mat(location, rotation_matrix)
    )

    # render the whole pipeline
    try:
        bproc.renderer.enable_normals_output()
        data = bproc.renderer.render()
        seg_data = bproc.renderer.render_segmap(map_by=["instance", "class", "name"])
        data.update(seg_data)

        altitude = location[2]
        distance_to_target = (np.sqrt(np.sum((location - object_3d[0].get_location()) ** 2, axis=0)))
        elevation_angle = math.degrees(altitude/distance_to_target)

        metadata = {"config_file" : job_name,
                    "scene_file" : os.environ['scene_file_path'],
                    "object_file" : os.environ['object_file_path'],
                    "altitude" : "{:.1f}".format(altitude),
                    "distance_to_target": "{:.1f}".format(distance_to_target),
                    "elevation_angle": "{:.1f}".format(elevation_angle),
                    }

        # Output annotations
        bproc.writer.write_coco_annotations(out_dir,
                                            metadata=metadata,
                                            instance_segmaps=seg_data["instance_segmaps"],
                                            instance_attribute_maps=seg_data["instance_attribute_maps"],
                                            colors=data["colors"],
                                            color_file_format="JPEG",
                                            append_to_existing_output=True
                                            )
        i += 1
    except:
        logging.critical("Error rendering/writing image and annotation to file. Retrying...")
        check += 1
        if check == images_per_batch:
            logging.critical("Repetitive error found when writing images. Aborting.")
            break
        continue
