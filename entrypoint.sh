#!/bin/sh
set -e

echo "waiting for postgres..."
python - <<'PY'
import os
import sys
import time

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.db import connections

for attempt in range(30):
    try:
        connections["default"].ensure_connection()
        break
    except Exception:
        time.sleep(2)
else:
    sys.exit("postgres is not reachable")
PY

python manage.py migrate --noinput

exec "$@"
