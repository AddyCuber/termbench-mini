#!/usr/bin/env bash
# Reference fix: three config/permission bugs, then start nginx.
set -euo pipefail

sed -i 's/listen 8080$/listen 8080;/' /etc/nginx/conf.d/site.conf
sed -i 's|root /var/www/site;|root /srv/site;|' /etc/nginx/conf.d/site.conf
chmod 644 /srv/site/index.html
nginx
