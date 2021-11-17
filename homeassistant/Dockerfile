ARG BUILD_FROM
FROM $BUILD_FROM

ENV LANG C.UTF-8

# Setup base
RUN \
    apk add --no-cache \
        py3-pip \
    \
    && pip3 install \
        pyserial \
        paho-mqtt \
        pyyaml \
	Jinja2

# Copy data
COPY rootfs /

