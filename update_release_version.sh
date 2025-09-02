#!/bin/sh

version=$(cat version.txt)

major_minor=$(echo "$version" | cut -d. -f1-2)
patch=$(echo "$version" | awk -F. '{print $NF}')

new_patch=$((patch + 1))

new_version="$major_minor.$new_patch"

echo "$new_version" > version.txt