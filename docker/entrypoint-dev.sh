#!/usr/bin/env sh
# ────────────────────────────────────────────────────────────────────
#  Grief Tracker - dev container entrypoint
#  Runs migrate -> bootstraps admin -> imports Excel (first run only)
#  -> starts the Django dev server.
# ────────────────────────────────────────────────────────────────────
set -e

cd /app

echo ""
echo "==================================================================="
echo " Grief Tracker - dev container starting"
echo "==================================================================="

echo "[1/4] Applying database migrations..."
python manage.py migrate --noinput

echo "[2/4] Ensuring admin user exists..."
python <<'PY'
import os, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()
from django.contrib.auth import get_user_model

User = get_user_model()
admin_email    = os.getenv("DJANGO_ADMIN_EMAIL",    "admin@local")
admin_username = os.getenv("DJANGO_ADMIN_USERNAME", "admin")
admin_password = os.getenv("DJANGO_ADMIN_PASSWORD", "admin")

if not User.objects.filter(is_superuser=True).exists():
    User.objects.create_superuser(
        username=admin_username, email=admin_email, password=admin_password,
    )
    print(f"  Created admin: {admin_email} / {admin_password}  (override with DJANGO_ADMIN_* env vars)")
else:
    print("  Admin user already exists - skipping.")
PY

echo "[3/4] Seeding Excel data if DB is empty..."
# We use `if` so that `set -e` doesn't kill the script when the probe exits 1.
if python - <<'PY'
import os, django, sys
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")
django.setup()
from apps.grief.models import GriefIssue
sys.exit(0 if GriefIssue.objects.exists() else 1)
PY
then
    echo "  GriefIssue table has rows - skipping import."
else
    if [ -f "data/Grief_003.xlsm" ]; then
        echo "  Empty DB - running import_excel data/Grief_003.xlsm ..."
        python manage.py import_excel data/Grief_003.xlsm || echo "  (import returned non-zero; continuing)"
    else
        echo "  No data/Grief_003.xlsm present - skipping import."
    fi
fi

echo "[4/4] Starting dev server on 0.0.0.0:8000 ..."
echo "==================================================================="
echo ""
exec python manage.py runserver 0.0.0.0:8000
