# create_superuser.py
import os
import django
from django.contrib.auth import get_user_model

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "paymentss.settings")  # <-- change to your project name

django.setup()

User = get_user_model()

username = os.environ.get("DJANGO_SUPERUSER_USERNAME", "Olaitan34")
email = os.environ.get("DJANGO_SUPERUSER_EMAIL", "admin@gmail.com")
password = os.environ.get("DJANGO_SUPERUSER_PASSWORD", "12345678")

if not User.objects.filter(username=username).exists():
    User.objects.create_superuser(username=username, email=email, password=password)
    print("Superuser created ✅")
else:
    print("Superuser already exists 🚀")