#!/bin/bash
set -ev

git config --global user.email $EMAIL
git config --global user.name $USERNAME
git symbolic-ref HEAD refs/heads/$(git branch --show-current)
git symbolic-ref HEAD

IMAGE_NAME=kasramp/kindler &&
docker login -u "$DOCKER_USERNAME" --password-stdin <<< "$DOCKER_PASSWORD" &&
docker buildx create --use &&
docker buildx build --platform "$ARCHITECTURE" -t "$IMAGE_NAME":latest -t "$IMAGE_NAME:$TAGGED_VERSION" . --push

if [ "$ARCHITECTURE" = "linux/amd64" ]; then
  git add version.txt &&
  git commit -m "Update version file to $TAGGED_VERSION" &&
  git push origin HEAD:master
fi
echo "Successfully build and pushed Docker $TAGGED_VERSION to Docker Hub"