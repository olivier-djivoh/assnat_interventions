# requetes/management/commands/relances.py

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from requetes.models import Requete
from comptes.models import Utilisateur
from datetime import timedelta

class Command(BaseCommand):
    help = 'Envoie des relances pour les requêtes en attente avec affichage du délai exact'

    def handle(self, *args, **options):
        seuil = timezone.now() - timedelta(hours=24)
        requetes = Requete.objects.filter(statut='EN_ATTENTE', date_creation__lt=seuil)

        compteur = 0

        for requete in requetes:
            # Calcul du délai écoulé
            delta = timezone.now() - requete.date_creation
            heures = int(delta.total_seconds() // 3600)
            jours = heures // 24
            reste_heures = heures % 24

            if jours > 0:
                if reste_heures == 0:
                    delai_texte = f"{jours} jour{'s' if jours > 1 else ''}"
                else:
                    delai_texte = f"{jours} jour{'s' if jours > 1 else ''} et {reste_heures} heure{'s' if reste_heures > 1 else ''}"
            else:
                delai_texte = f"{heures} heure{'s' if heures > 1 else ''}"

            # 1. Envoi aux chefs de service
            chefs_service = Utilisateur.objects.filter(
                service=requete.service_cible,
                role='chef_service',
                est_valide=True,
                is_active=True
            )

            for chef in chefs_service:
                if chef.get_notif_pref('relance_quotidienne', True):
                    compteur += self.envoyer_relance(chef, requete, delai_texte)

            # 2. Envoi aux chefs de division si attribuée
            if requete.division_attribuee:
                chefs_division = Utilisateur.objects.filter(
                    division=requete.division_attribuee,
                    role='chef_division',
                    est_valide=True,
                    is_active=True
                )

                for chef in chefs_division:
                    if chef.get_notif_pref('relance_quotidienne', True):
                        compteur += self.envoyer_relance(chef, requete, delai_texte)

        self.stdout.write(
            self.style.SUCCESS(f'{compteur} relance(s) envoyée(s) pour {requetes.count()} requête(s).')
        )

    def envoyer_relance(self, destinataire, requete, delai_texte):
        """
        Envoie un email de relance avec le délai exact
        """
        sujet = f"[RELANCE] Requête #{requete.id} : {requete.titre}"

        # URL absolue (à adapter selon ton environnement)
        url = f"http://127.0.0.1:8000/requetes/{requete.id}/"  # dev
        # url = f"https://ton-domaine.com/requetes/{requete.id}/"  # prod

        # Version TEXTE (obligatoire)
        text_message = (
            f"Bonjour {destinataire.get_full_name() or destinataire.username},\n\n"
            f"La requête suivante est toujours en attente depuis **{delai_texte}** :\n\n"
            f"Titre : {requete.titre}\n"
            f"Date de création : {requete.date_creation.strftime('%d/%m/%Y %H:%M')}\n"
            f"Demandeur : {requete.demandeur.get_full_name() or requete.demandeur.username}\n"
            f"Statut : {requete.get_statut_display()}\n"
        )
        if requete.division_attribuee:
            text_message += f"Division attribuée : {requete.division_attribuee.nom}\n"
        text_message += (
            f"\nPour traiter cette requête : {url}\n\n"
            f"Cordialement,\nLe système de gestion des interventions\nAssemblée Nationale"
        )

        # Version HTML (avec template)
        try:
            html_message = render_to_string('emails/relance.html', {
                'destinataire': destinataire,
                'requete': requete,
                'url': url,
                'delai_texte': delai_texte,
            })
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Erreur de template HTML: {e}"))
            html_message = None

        # Envoi
        try:
            email = EmailMultiAlternatives(
                sujet,
                text_message,
                settings.EMAIL_HOST_USER,
                [destinataire.email]
            )
            if html_message:
                email.attach_alternative(html_message, "text/html")
            email.send()
            self.stdout.write(self.style.SUCCESS(f"  → Relance envoyée à {destinataire.email}"))
            return 1
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  → Erreur pour {destinataire.email}: {e}"))
            return 0