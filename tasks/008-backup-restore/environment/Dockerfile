FROM debian:12-slim

COPY files/ /
RUN chmod +x /usr/local/bin/restore-app.sh
RUN tar -cf /opt/app-backup.tar -C /opt/backup-source app.conf