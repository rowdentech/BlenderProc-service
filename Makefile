all_kube: k8s_prereq gen_swagger build_datagen build_sds deploy_kube test_curl
all_nosudo: k8s_prereq_nosudo gen_swagger build deploy_nosudo test_curl
all_docker: gen_swagger build deploy_docker sleep curl_docker

# Configure Ingress, Persistent Volumes (check server: IP) and clusterRole
# add sds.sml.io to your IP address in /etc/hosts
k8s_prereq:
	sudo kubectl apply -f ./kube/
k8s_prereq_nosudo:
	kubectl apply -f ./kube/

gen_swagger:
	docker run -v $(shell pwd):/sds -w /sds swaggerapi/swagger-codegen-cli:v2.3.1 generate -l python-flask -o /sds -i /sds/sds-api.yaml -D packageName=sds

build_datagen:
	docker build data_generation/ -t data-generation --no-cache
	docker tag data-generation docker-registry:5000/data-generation
	docker push docker-registry:5000/data-generation
build_sds:
	docker build . -t sds --no-cache
	docker tag sds docker-registry:5000/sds
	docker push docker-registry:5000/sds
build: build_datagen build_sds

# k3s requires sudo
deploy_kube:
	sudo kubectl delete svc sds --ignore-not-found
	sudo kubectl delete pod sds --ignore-not-found
	sleep 1
	sudo kubectl apply -f sds-pod.yaml

# local laptop dev using docker destop doesn't require sudo
deploy_nosudo:
	kubectl delete svc sds --ignore-not-found
	kubectl delete pod sds --ignore-not-found
	sleep 1
	kubectl apply -f sds-pod.yaml

# deploy using python-docker
deploy_docker:
	docker stop sds #2>/dev/null || true
	docker rm sds #2>/dev/null || true
	docker run -d -p 8080:8080 -v /var/run/docker.sock:/var/run/docker.sock -v /data:/data -e "deployment=docker" --name sds sds

curl_docker:
	curl -X PUT --header 'Content-Type: application/json' --header 'Accept: application/json' -d @request.json 'http://127.0.0.1:8080/v1/synth/generate'
curl_local: curl_docker

sleep:
	sleep 10

test_curl: sleep curl

