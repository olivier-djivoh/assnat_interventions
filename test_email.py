# test_email.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'assnat_interventions.settings')
django.setup()

from django.template.loader import render_to_string
from comptes.models import Utilisateur

# Récupérez un utilisateur existant
user = Utilisateur.objects.first()
lien = "http://test.com/lien"

# Testez le rendu HTML
html = render_to_string('emails/activation.html', {'user': user, 'lien': lien})
print("=== RENDU HTML ===")
print(html[:500])  # Affiche les 500 premiers caractères

# Testez le rendu texte
text = render_to_string('emails/activation.txt', {'user': user, 'lien': lien})
print("\n=== RENDU TEXTE ===")
print(text)