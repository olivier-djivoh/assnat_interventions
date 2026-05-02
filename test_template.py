# test_template.py
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'assnat_interventions.settings')
django.setup()

from django.template.loader import render_to_string
from comptes.models import Utilisateur

# Récupérez le premier utilisateur (ou l'admin)
user = Utilisateur.objects.first()
lien = "http://127.0.0.1:8000/test-lien/"

# Testez le rendu du template d'activation
html = render_to_string('emails/activation.html', {'user': user, 'lien': lien})
print("=== ACTIVATION HTML ===")
print(html[:500])  # Montre le début

# Testez le rendu du template de relance
from requetes.models import Requete
requete = Requete.objects.first()
url = "http://127.0.0.1:8000/requetes/1/"

html_relance = render_to_string('emails/relance.html', {
    'requete': requete,
    'nom': user.get_full_name(),
    'url': url
})
print("\n=== RELANCE HTML ===")
print(html_relance[:500])