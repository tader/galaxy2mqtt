#!/bin/sh

docker run \
	--rm \
	-it \
	-v ./test_data:/data \
	local/galaxy2mqtt-addon

