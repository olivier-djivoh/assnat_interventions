
from django.apps import AppConfig

class RequetesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'requetes'

    def ready(self):
        import requetes.signals