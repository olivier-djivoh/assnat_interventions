from django.db.models.signals import post_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .models import Requete
from comptes.models import Utilisateur

@receiver(post_save, sender=Requete)
def notify_new_requete(sender, instance, created, **kwargs):
    if created:
        # Notifier les chefs de service concernés
        chefs_service = Utilisateur.objects.filter(
            service=instance.service_cible,
            role='chef_service',
            est_valide=True,
            is_active=True
        )
        channel_layer = get_channel_layer()
        for chef in chefs_service:
            async_to_sync(channel_layer.group_send)(
                f'user_{chef.id}',
                {
                    'type': 'send_notification',
                    'message': f'Nouvelle requête dans votre service : {instance.titre}',
                    'url': f'/requetes/{instance.id}/',
                }
            )

@receiver(post_save, sender=Requete)
def notify_attribution(sender, instance, **kwargs):
    # Si la division a changé (attribution)
    if instance.division_attribuee and instance.date_attribution:
        # Notifier le chef de division concerné
        chefs_division = Utilisateur.objects.filter(
            division=instance.division_attribuee,
            role='chef_division',
            est_valide=True,
            is_active=True
        )
        channel_layer = get_channel_layer()
        for chef in chefs_division:
            async_to_sync(channel_layer.group_send)(
                f'user_{chef.id}',
                {
                    'type': 'send_notification',
                    'message': f'Une requête vous a été attribuée : {instance.titre}',
                    'url': f'/requetes/{instance.id}/',
                }
            )