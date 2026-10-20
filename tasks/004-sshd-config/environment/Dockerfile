FROM debian:12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends openssh-server \
    && rm -rf /var/lib/apt/lists/* \
    && ssh-keygen -A \
    && mkdir -p /run/sshd

COPY files/ /