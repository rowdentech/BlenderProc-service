""" docstring """
import docker
import connexion
import logging
import collections
import os
collections.Callable = collections.abc.Callable
import shutil
import time
import ast


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

    if os.environ["deployment"] in ["kubernetes"]:
        from kubernetes import client, config
        data = str(connexion.request.get_json())
        data_dict = ast.literal_eval(data)
        num_batches = int(int(data_dict["num_images"])/int(data_dict["batch_size"]))
        config.load_incluster_config()

        api_instance = client.BatchV1Api()
        api_response = api_instance.create_namespaced_job(
            namespace="default",
            body=client.V1Job(
                metadata=client.V1ObjectMeta(name="datagen", labels={"app": "datagen"}),
                spec=client.V1JobSpec(
                    completions=num_batches,
                    completion_mode="Indexed",
                    ttl_seconds_after_finished=60,  # job/pod gets auto deleted after 60s
                    template=client.V1PodTemplateSpec(
                        metadata=client.V1ObjectMeta(name="datagen", labels={"app": "datagen"}),
                        spec=client.V1PodSpec(
                            node_selector={"kubernetes.io/arch": "amd64"},
                            restart_policy="Never",
                            containers=[
                                client.V1Container(
                                name="datagen",
                                image="docker-registry:5000/data-generation",
                                env=[client.V1EnvVar(name="JSON_CONFIG",value=data)],
                                volume_mounts=[client.V1VolumeMount(
                                    name="synth-vol",
                                    mount_path="/data/vol2"
                                )])
                            ],
                            volumes=[client.V1Volume(
                                name="synth-vol",
                                persistent_volume_claim=client.V1PersistentVolumeClaimVolumeSource(
                                    claim_name="synth-pvc"
                                )
                            )]
                        )
                    )
                )
            )
        )
        while True:
            time.sleep(1)
            if api_instance.read_namespaced_job_status(name="datagen", namespace="default").status.active != 1:
                move_files_out_of_temp(request_json)
                return "run OK"
    else:       # os.environ["deployment"] in ["docker"]
        client = docker.from_env()
        for i in range(int(num_batches)):
            client.containers.run("docker-registry:5000/data-generation:latest",
                                  environment={"JSON_CONFIG": request_json},
                                  detach=False,
                                  volumes=[str(request_json["output_dir"])+":/data/vol2"]
                                  )
    move_files_out_of_temp(request_json)
    return 'run OK'
