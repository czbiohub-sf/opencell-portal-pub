#!/bin/bash
set -e

# run gunicorn using supervisor
# supervisord -c /opencell/deploy/local/supervisord.conf

# run gunicorn directly
gunicorn -w 4 -b 0.0.0.0:5000 "opencell.api.app:create_app()"

exec "$@"
