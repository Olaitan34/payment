"""
Django settings for payment_api project.
Suited for Vercel deployment
"""
import os
import dj_database_url
from dotenv import load_dotenv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env if present
load_dotenv(BASE_DIR / ".env")

# Security
# SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", "p22ok35hx1q%ppichdvo_t*)(at1+7dtu+6t=@jf8fw_cnn9c+")

# DEBUG = os.getenv("DEBUG", "False").lower() == "true"

# ✅ Allow Vercel domains and localhost for testing
ALLOWED_HOSTS = ["paymentssss.onrender.com", "localhost", "127.0.0.1"]


# ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "your-vercel-app.vercel.app,localhost,127.0.0.1").split(",")

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',

    # Local apps
    'payments',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",  # must be just after SecurityMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'payment_api.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],  # in case you add frontend templates later
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# ✅ For Vercel, we need ASGI (serverless handler)
WSGI_APPLICATION = 'payment_api.wsgi.application'
ASGI_APPLICATION = 'payment_api.asgi.application'

# Database — for simple Vercel deployments, stick to SQLite
# If you later use Postgres (like Supabase/NeonDB), override with env vars
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
# database_url = os.environ.get("DATABASE_URL")
# DATABASES['default'] = dj_database_url.parse(database_url)

# postgresql://payment_gzin_user:mBg0bVz5DlHPxdAr4Cjtj6yR64aaclT9@dpg-d2kmh53ipnbc73f9s4lg-a.oregon-postgres.render.com/payment_gzinpayment_gzin
# Password validators
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {"NAME": 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {"NAME": 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {"NAME": 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# i18n
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# ✅ Static files — Vercel requires collected static in `/staticfiles`
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Media files (optional if you need uploads)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {"level": "INFO", "class": "logging.StreamHandler"},
    },
    'root': {"handlers": ['console'], "level": "INFO"},
}

# ✅ Paystack
PAYSTACK_SECRET_KEY = os.getenv("PAYSTACK_SECRET_KEY")
PAYSTACK_CALLBACK_URL = os.getenv("PAYSTACK_CALLBACK_URL", "https://your-vercel-app.vercel.app/payment/success")