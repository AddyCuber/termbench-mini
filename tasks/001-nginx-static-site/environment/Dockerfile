FROM debian:12-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends nginx curl procps \
    && rm -rf /var/lib/apt/lists/* \
    && rm -f /etc/nginx/sites-enabled/default

COPY files/ /

# Worker (www-data) cannot read the homepage; about.html stays readable.
RUN chmod 600 /srv/site/index.html
