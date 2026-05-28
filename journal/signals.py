from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in, user_logged_out
from .models import JournalAudit
from .middleware import get_current_request, get_client_ip
from comptes.models import Utilisateur
from requetes.models import Requete, Attribution, CompteRendu

# ---------------------------
# Actions CRUD
# ---------------------------
@receiver(post_save)
def audit_post_save(sender, **kwargs):
    if sender in [Utilisateur, Requete, Attribution, CompteRendu]:
        instance = kwargs['instance']
        created = kwargs['created']
        request = get_current_request()
        user = request.user if request and request.user.is_authenticated else None
        ip = get_client_ip(request)

        nouvelles = {}
        for field in instance._meta.fields:
            value = getattr(instance, field.name)
            if value and hasattr(value, 'pk'):
                nouvelles[field.name] = value.pk
            else:
                nouvelles[field.name] = str(value) if value is not None else None

        JournalAudit.objects.create(
            utilisateur=user,
            action='CREATION' if created else 'MODIFICATION',
            entite_type=instance._meta.model_name,
            entite_id=instance.pk,
            anciennes_valeurs=None,
            nouvelles_valeurs=nouvelles,
            adresse_ip=ip
        )

@receiver(post_delete)
def audit_post_delete(sender, **kwargs):
    if sender in [Utilisateur, Requete, Attribution, CompteRendu]:
        instance = kwargs['instance']
        request = get_current_request()
        user = request.user if request and request.user.is_authenticated else None
        ip = get_client_ip(request)

        JournalAudit.objects.create(
            utilisateur=user,
            action='SUPPRESSION',
            entite_type=instance._meta.model_name,
            entite_id=instance.pk,
            anciennes_valeurs=None,
            nouvelles_valeurs=None,
            adresse_ip=ip
        )


# ---------------------------
# Connexion / Déconnexion
# ---------------------------
@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    ip = get_client_ip(request)
    JournalAudit.objects.create(
        utilisateur=user,
        action='CONNEXION',
        entite_type='authentification',
        entite_id=user.id,
        anciennes_valeurs=None,
        nouvelles_valeurs=None,
        adresse_ip=ip
    )

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    ip = get_client_ip(request)
    JournalAudit.objects.create(
        utilisateur=user,
        action='DECONNEXION',
        entite_type='authentification',
        entite_id=user.id,
        anciennes_valeurs=None,
        nouvelles_valeurs=None,
        adresse_ip=ip
    )