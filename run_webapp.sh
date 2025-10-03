#!/bin/bash
# This script can be used to build and run the nutrition app within a Docker container. Content will be stored
# in `database/nutrition.db`
sudo docker buildx build -t nutrition . < Dockerfile
sudo docker run -p 80:80 -it -v database:/database nutrition:latest