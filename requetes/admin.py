# requetes/admin.py

from django.contrib import admin
from .models import TypeDemande, Requete, Attribution, CompteRendu

admin.site.register(TypeDemande)
admin.site.register(Requete)
admin.site.register(Attribution)
admin.site.register(CompteRendu)