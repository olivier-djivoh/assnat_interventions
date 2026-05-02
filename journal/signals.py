from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.admin.models import ADDITION, CHANGE, DELETION
from .models import JournalAudit
from requetes.models import Requete, Attribution, CompteRendu
from comptes.models import Utilisateur
from .middleware import get_current_request

def get_client_ip(request):
    if request:
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    return None

@receiver(post_save)
def audit_post_save(sender, **kwargs):
    if sender in [Requete, Utilisateur, Attribution, CompteRendu]:
        instance = kwargs['instance']
        created = kwargs['created']
        action = ADDITION if created else CHANGE
        request = get_current_request()
        user = request.user if request and request.user.is_authenticated else None
        ip = get_client_ip(request)

        nouvelles = {}
        for field in instance._meta.fields:
            if field.name not in ['password', 'last_login']:
                valeur = getattr(instance, field.name)
                if valeur and hasattr(valeur, 'pk'):
                    nouvelles[field.name] = valeur.pk
                else:
                    nouvelles[field.name] = str(valeur) if valeur is not None else None

        JournalAudit.objects.create(
            utilisateur=user,
            action=action,
            entite_type=instance._meta.model_name,
            entite_id=instance.pk,
            anciennes_valeurs=None,
            nouvelles_valeurs=nouvelles,
            adresse_ip=ip
        )

@receiver(post_delete)
def audit_post_delete(sender, **kwargs):
    if sender in [Requete, Utilisateur, Attribution, CompteRendu]:
        instance = kwargs['instance']
        request = get_current_request()
        user = request.user if request and request.user.is_authenticated else None
        ip = get_client_ip(request)

        JournalAudit.objects.create(
            utilisateur=user,
            action=DELETION,
            entite_type=instance._meta.model_name,
            entite_id=instance.pk,
            anciennes_valeurs=None,
            nouvelles_valeurs=None,
            adresse_ip=ip
        )