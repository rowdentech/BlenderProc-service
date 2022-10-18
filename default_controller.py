""" docstring """
import docker
import connexion
import logging
import collections
import os
collections.Callable = collections.abc.Callable
import shutil


def move_files_out_of_temp(req_json):
    # move completed folder up one level out of "temp" dir
    source = os.path.join(req_json["output_dir"], "temp")
    dest = req_json["output_dir"]
    files_list = os.listdir(source)
    for files in files_list:
        files_path = os.path.join(source, files)
        shutil.move(files_path, dest)


def generate_synthetic_data(configuration):  # noqa: E501
    """Generates synthetic data

    Generates the synthetic data using config json provided # noqa: E501

    :param configuration: Synthetic Data configuration json
    :type configuration: dict | bytes

    :rtype: None
    """
    request_json = connexion.request.get_json()
    num_batches = int(request_json["num_images"]) / int(request_json["batch_size"])
    client = docker.from_env()
    print(connexion.request.get_json())
    for i in range(int(num_batches)):
        client.containers.run("docker-registry:5000/data-generation:latest",
                              environment={"JSON_CONFIG": request_json},
                              detach=False,
                              volumes=[str(request_json["output_dir"])+":/data/vol2"]
                              )
    move_files_out_of_temp(request_json)
    return 'run OK'
