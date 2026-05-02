

from django.db import models
from django.conf import settings
from comptes.models import Service, Division

class TypeDemande(models.Model):
    """
    Catégorie de demande, associée au service qui doit la traiter (routage automatique).
    """
    nom = models.CharField(max_length=100)                        
    service_cible = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='types_demande')
    description = models.TextField(blank=True)                

    class Meta:
        verbose_name = "Type de demande"
        verbose_name_plural = "Types de demande"
        ordering = ['nom']

    def __str__(self):
        return self.nom


class Requete(models.Model):
    STATUT_CHOICES = (
        ('EN_ATTENTE', 'En attente'),
        ('RESOLU', 'Résolu'),
    )
    
    STATUT_COMPTE_RENDU_CHOICES = (
        ('AUCUN', 'Aucun compte rendu'),
        ('EN_COURS', 'Compte rendu en cours'),
        ('MODIFIE', 'Compte rendu modifié'),
        ('RESOLU', 'Compte rendu résolu'),
    )

    titre = models.CharField(max_length=200)
    description = models.TextField()
    type_demande = models.ForeignKey(TypeDemande, on_delete=models.PROTECT, related_name='requetes')
    # PROTECT empêche la suppression d'un type tant que des requêtes y sont liées
    localisation = models.CharField(max_length=200, blank=True)   # Ex: "Bureau 203, Bâtiment A"
    date_creation = models.DateTimeField(auto_now_add=True)       # Date de création automatique
    statut = models.CharField(max_length=20,choices=STATUT_CHOICES, default='EN_ATTENTE')
    demandeur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='requetes_emises')
    service_cible = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='requetes_recues')

    # service_cible est déterminé automatiquement lors de la création à partir du type_demande
    division_attribuee = models.ForeignKey(Division, on_delete=models.SET_NULL, null=True, blank=True, related_name='requetes')
    date_attribution = models.DateTimeField(null=True, blank=True)  # Date à laquelle la requête a été attribuée à une division
    date_resolution = models.DateTimeField(null=True, blank=True)   # Date de passage à "Résolu"
    statut_compte_rendu = models.CharField( max_length=20, choices=STATUT_COMPTE_RENDU_CHOICES, default='AUCUN')

    class Meta:
        verbose_name = "Requête"
        verbose_name_plural = "Requêtes"
        ordering = ['-date_creation']  # Les plus récentes en premier

    def __str__(self):
        return f"{self.titre} - {self.demandeur}"


class Attribution(models.Model):
    """
    Trace chaque attribution d'une requête à un chef de division.
    Permet un historique complet.
    """
    requete = models.ForeignKey(Requete, on_delete=models.CASCADE, related_name='attributions')
    chef_service = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='attributions_effectuees')
    chef_division = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='attributions_recues')
    date_attribution = models.DateTimeField(auto_now_add=True)
    commentaire = models.TextField(blank=True)
 
    class Meta:
        verbose_name = "Attribution"
        verbose_name_plural = "Attributions"

    def __str__(self):
        return f"Attribution {self.requete.id} à {self.chef_division}"


class CompteRendu(models.Model):
    """
    Compte rendu d'intervention rédigé par le chef de division après l'intervention.
    """
    requete = models.ForeignKey(Requete, on_delete=models.CASCADE, related_name='comptes_rendus')
    chef_division = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    date = models.DateTimeField(auto_now_add=True)
    contenu = models.TextField()
    intervention_resolue = models.BooleanField(default=False)  # Le problème est-il résolu selon le chef division ?
    pieces_jointes = models.FileField(upload_to='comptes_rendus/', blank=True, null=True)
    date_derniere_modification = models.DateTimeField(auto_now=True, null=True, blank=True)

    class Meta:
        verbose_name = "Compte rendu"
        verbose_name_plural = "Comptes rendus"
        ordering = ['-date']

    def __str__(self):
        return f"CR {self.requete.id} - {self.date}"