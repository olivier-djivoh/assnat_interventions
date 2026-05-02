# test_send.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'assnat_interventions.settings')
django.setup()

from django.core.mail import send_mail
from django.conf import settings

send_mail(
    "Test HTML",
    "Ceci est la version texte",
    settings.EMAIL_HOST_USER,
    ["olivierdjivoh2@gmail.com"],  # Mettez votre email ici
    html_message="<h1>Test HTML</h1><p style='color:blue'>Ceci est un test</p>"
)
print("Email envoyé !")