import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]
DEBUG = False
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv(
        "DJANGO_ALLOWED_HOSTS",
        "localhost,127.0.0.1,backend,testserver"
    ).split(",")
    if host.strip()
]
CSRF_TRUSTED_ORIGINS = os.getenv("CSRF_TRUSTED_ORIGINS", "http://localhost:8080,http://127.0.0.1:8080").split(",")
ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"
INSTALLED_APPS = ["django.contrib.auth", "django.contrib.contenttypes", "django.contrib.sessions", "tramites"]
MIDDLEWARE = ["django.middleware.security.SecurityMiddleware", "django.contrib.sessions.middleware.SessionMiddleware", "django.middleware.common.CommonMiddleware", "django.middleware.csrf.CsrfViewMiddleware", "django.contrib.auth.middleware.AuthenticationMiddleware"]
DATABASES = {"default": {"ENGINE": "django.db.backends.postgresql", "HOST": os.environ["POSTGRES_HOST"], "PORT": "5432", "NAME": "sitrah", "USER": "sitrah", "PASSWORD": os.environ["POSTGRES_PASSWORD"]}} if os.getenv("POSTGRES_HOST") else {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "local.sqlite3"}}
LANGUAGE_CODE = "es-cl"
if os.getenv("POSTGRES_HOST"):
    DATABASES["default"].update(CONN_MAX_AGE=60, CONN_HEALTH_CHECKS=True,
        OPTIONS={"connect_timeout": 10})
TIME_ZONE = "America/Santiago"
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
MEDIA_ROOT = Path(os.getenv("SITRAH_MEDIA_ROOT", BASE_DIR / "media"))
FILE_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024
DATA_UPLOAD_MAX_MEMORY_SIZE = 1024 * 1024
DATA_UPLOAD_MAX_NUMBER_FILES = 8
SESSION_COOKIE_HTTPONLY = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SITRAH_DEMO = os.getenv("SITRAH_DEMO") == "1"
if os.getenv("DJANGO_HTTPS", "0") == "1":
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
