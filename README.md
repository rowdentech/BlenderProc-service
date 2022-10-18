# A dockerised service for Bounding Box and Segementation data generation using Blenderproc

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

<img src="./images/datagen-montage.png" alt="Labelled generated data" width="1000">

## Requirements:
- Linux 20.04
- Python 3.5.2+
- Docker

# Setup
## Prepare objects/scenes
Objects/scenes are available across the web. A couple of good free sites:
- Objects: [Free3d](https://free3d.com/)
- Scenes: [PolyHaven](https://polyhaven.com/)

## Prepare output folder structure
The microservice by default outputs data to /data/nfs1/synth, using /data/nfs1/synth/temp during creation. 
Before commencing, create this directory structure and set permissions to -rwxrwsrwx using:
````bash
chmod -R 2777 /data/nfs1
````

## Data Generation 
Run:
````bash
make all_docker
````
This will:
 - Use [Swagger CodeGen](https://swagger.io/tools/swagger-codegen/) to generate server code
 - Build the [BlenderProc](https://hub.docker.com/r/blenderproc/blenderproc) docker
 - Build and deploy the data generation microservice
 - Send a data generation request after a small wait to test the service end to end
 - Further requests can be sent by modifying the request.json and running:
````bash
make curl_docker
````

Data Generation requests are specified in request.json.
