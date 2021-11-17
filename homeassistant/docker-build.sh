#!/bin/sh

docker build \
	--build-arg BUILD_FROM="homeassistant/armhf-base:latest" \
	-t local/galaxy2mqtt-addon \
	.

