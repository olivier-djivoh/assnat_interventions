# comptes/apps.py
from django.apps import AppConfig

class ComptesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'comptes'

    def ready(self):
        import comptes.signals  