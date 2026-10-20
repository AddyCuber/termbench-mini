FROM debian:12-slim

RUN apt-get update \
	&& apt-get install -y --no-install-recommends python3 \
	&& rm -rf /var/lib/apt/lists/*

COPY files/ /