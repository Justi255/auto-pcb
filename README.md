# auto-pcb
Automatic PCB (Printed Circuit Board) layout framework




## Docker environment setup

submodule 
```bash
git submodule init
git submodule update
```

Build the docker image with the following command
```bash
## build docker image
docker build -f ./dockerfile -t auto-pcb:cuda .
## or use mirror-site to build docker image
docker build -f ./dockerfile.mirror -t auto-pcb:cuda .
## or build the base image only with no code inside the image
docker build -f ./dockerfile.mirror --target base -t auto-pcb-base:cuda .
```

Run the docker image with the following command
```bash
## run the docker image with gpu support
docker run -it --rm --gpus all auto-pcb:cuda
## if use base image, run the following command to mount the repo-folder
docker run -it --rm --gpus all -v xx:xx  auto-pcb-base:cuda
```
