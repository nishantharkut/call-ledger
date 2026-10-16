import os

import dj_database_url
from corsheaders.defaults import default_headers

from .settings import *


SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DEBUG = False
ALLOWED_HOSTS = [
    host.strip() for host in os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",")
    if host.strip()
]
render_hostname = os.getenv("RENDER_EXTERNAL_HOSTNAME", "").strip()
if render_hostname:
    ALLOWED_HOSTS.append(render_hostname)

INSTALLED_APPS = [*INSTALLED_APPS, "rest_framework", "reconciliation", "corsheaders"]
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    MIDDLEWARE[0],
    "whitenoise.middleware.WhiteNoiseMiddleware",
    *MIDDLEWARE[1:],
]

DATABASES = {"default": dj_database_url.parse(
    os.environ["DATABASE_URL"], conn_max_age=60, conn_health_checks=True, ssl_require=True,
)}

# Render terminates HTTPS before forwarding requests to Gunicorn.
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 3600
SECURE_HSTS_INCLUDE_SUBDOMAINS = True

frontend_origin = os.getenv("FRONTEND_ORIGIN", "").strip().rstrip("/")
CORS_ALLOWED_ORIGINS = [frontend_origin] if frontend_origin else []
CORS_ALLOW_HEADERS = [*default_headers, "x-organization"]
CORS_ALLOW_METHODS = ["GET", "POST", "OPTIONS"]
CORS_URLS_REGEX = r"^/api/"

STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

AIRTABLE_PAT = os.getenv("AIRTABLE_PAT", "").strip()
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID", "").strip()
AIRTABLE_TABLE_NAME = os.getenv("AIRTABLE_TABLE_NAME", "").strip()
