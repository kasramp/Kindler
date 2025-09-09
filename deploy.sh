#!/bin/bash
IMAGE_VERSION="${1:-latest}"
DOCKERHUB_USERNAME="${2:-$DOCKER_USERNAME}"
DOCKERHUB_PASSWORD="${3:-$DOCKER_PASSWORD}"
export REDIS_URL=localhost
export IMAGE_TAG="$IMAGE_VERSION"
docker login -u "$DOCKERHUB_USERNAME" --password-stdin <<< "$DOCKERHUB_PASSWORD" && \
docker stack deploy --with-registry-auth -c docker-compose-swarm.yml kindler_stack