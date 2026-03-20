#!/bin/sh
# Fix permissions on volume-mounted files that celery user needs to write
chown celery:celery /app/history.txt 2>/dev/null || touch /app/history.txt && chown celery:celery /app/history.txt
chown -R celery:celery /app/attachments 2>/dev/null || true


# Drop to celery user and run the command
exec su -s /bin/sh celery -c "$*"
