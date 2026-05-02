# journal/models.py

from django.db import models
from django.conf import settings

class JournalAudit(models.Model):
    """
    Enregistre toutes les actions importantes (création, modification, suppression)
    sur les modèles clés, pour traçabilité.
    """
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    action = models.CharField(max_length=50)                 # Ex: 'CREATION', 'MODIFICATION', 'ATTRIBUTION'
    entite_type = models.CharField(max_length=50)            # Nom du modèle (ex: 'requete', 'utilisateur')
    entite_id = models.IntegerField()                         # ID de l'enregistrement concerné
    anciennes_valeurs = models.JSONField(null=True, blank=True)   # État avant modification (JSON)
    nouvelles_valeurs = models.JSONField(null=True, blank=True)   # État après modification (JSON)
    date_action = models.DateTimeField(auto_now_add=True)
    adresse_ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        verbose_name = "Journal d'audit"
        verbose_name_plural = "Journaux d'audit"
        ordering = ['-date_action']

    def __str__(self):
        return f"{self.date_action} - {self.action} - {self.entite_type}:{self.entite_id}"