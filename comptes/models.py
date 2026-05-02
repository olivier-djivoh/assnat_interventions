from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings

class Direction(models.Model):
    """
    Représente une direction (ex: DSI, DQ)
    """
    TYPE_DIRECTION = (
        ('SGA', 'SGA'),
        ('CABINET', 'Cabinet'),
    )
    nom = models.CharField(max_length=100, unique=True)
    type = models.CharField(max_length=20, choices=TYPE_DIRECTION)

    class Meta:
        verbose_name = "Direction"
        verbose_name_plural = "Directions"

    def __str__(self):
        return f"{self.nom} ({self.get_type_display()})"


class Service(models.Model):
    """
    Service appartenant à une direction (ex: Service infrastructures réseaux)
    """
    nom = models.CharField(max_length=100)
    direction = models.ForeignKey(Direction, on_delete=models.CASCADE, related_name='services')

    class Meta:
        verbose_name = "Service"
        verbose_name_plural = "Services"

    def __str__(self):
        return f"{self.nom} - {self.direction.nom}"


class Division(models.Model):
    """
    Division appartenant à un service (ex: Division infrastructures et réseaux)
    """
    nom = models.CharField(max_length=100)
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='divisions')

    class Meta:
        verbose_name = "Division"
        verbose_name_plural = "Divisions"

    def __str__(self):
        return f"{self.nom} - {self.service.nom}"


class Utilisateur(AbstractUser):
    """
    Modèle utilisateur personnalisé, hérite de AbstractUser.
    Ajoute des champs spécifiques à l'Assemblée.
    """
    TYPE_CONTRAT = (
        ('PERMANENT', 'Permanent'),
        ('CONTRACTUEL', 'Contractuel'),
    )

    ROLE_CHOICES = (
        ('personnel', 'Personnel'),
        ('chef_service', 'Chef de service'),
        ('chef_division', 'Chef de division'),
        ('directeur', 'Directeur'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='personnel')

    # Champs supplémentaires
    contact = models.CharField(max_length=20, blank=True)
    type_contrat = models.CharField(max_length=20, choices=TYPE_CONTRAT, blank=True, null=True)
    direction = models.ForeignKey('Direction', on_delete=models.SET_NULL, null=True, blank=True, related_name='utilisateurs')
    service = models.ForeignKey('Service', on_delete=models.SET_NULL, null=True, blank=True, related_name='utilisateurs')
    division = models.ForeignKey('Division', on_delete=models.SET_NULL, null=True, blank=True, related_name='utilisateurs')
    est_valide = models.BooleanField(default=False)
    date_validation = models.DateTimeField(null=True, blank=True)
    notification_preferences = models.JSONField(default=dict, blank=True)
    email_is_invalid = models.BooleanField(default=False, help_text="Indique si l'adresse email a causé un bounce.")

    def __str__(self):
        return f"{self.username} - {self.get_full_name()}"
    
    def get_notif_pref(self, key, default=True):
        """Récupère une préférence, retourne default si absente."""
        return self.notification_preferences.get(key, default)

    @property
    def email_status(self):
        if self.est_valide:
            return "✅ Validé"
        if self.email_is_invalid:
            return "❌ Invalide"
        return "⏳ En attente de délivrance"