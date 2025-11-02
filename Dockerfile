FROM ghcr.io/home-assistant/home-assistant:stable

RUN apk update && \
    apk add --no-cache \
    build-base \
    geos geos-dev \
    gdal gdal-dev \
    proj proj-dev \
    py3-requests \
    py3-ruamel.yaml \
    py3-jinja2 \
    py3-yaml \
    py3-protobuf \
    py3-numpy \
    py3-pillow \
    py3-matplotlib \
    py3-scipy \
    py3-shapely \
    py3-pandas \
    py3-fiona \
    && pip install --no-cache-dir \
        fitparse \
        pyproj \
        geopandas \
        contextily \
    && \
    apk del build-base

LABEL org.opencontainers.image.source=https://github.com/watsona4/hass-config