import logging
from anymail.signals import tracking
from django.dispatch import receiver
from django.utils import timezone
from .models import Utilisateur
from django.db.models.signals import pre_save

logger = logging.getLogger(__name__)

@receiver(tracking)
def handle_email_tracking(sender, event, esp_name, **kwargs):
    if event.event_type in ('delivered', 'request'):
        try:
            user = Utilisateur.objects.get(email=event.recipient)
            if not user.est_valide:
                user.est_valide = True
                user.date_validation = timezone.now()
                user.save()
        except Utilisateur.DoesNotExist:
            pass
    elif event.event_type in ('bounced', 'hard_bounce', 'soft_bounce'):
        try:
            user = Utilisateur.objects.get(email=event.recipient)
            user.email_is_invalid = True
            user.save()
        except Utilisateur.DoesNotExist:
            pass

@receiver(pre_save, sender=Utilisateur)
def reset_email_invalid_on_email_change(sender, instance, **kwargs):
    if instance.pk:
        try:
            old = sender.objects.get(pk=instance.pk)
            if old.email != instance.email:
                instance.email_is_invalid = False
        except sender.DoesNotExist:
            pass
