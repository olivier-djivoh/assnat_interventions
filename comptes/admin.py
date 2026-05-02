from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings
from .models import Direction, Service, Division, Utilisateur
from django.core.mail import EmailMultiAlternatives
from django import forms



from validate_email import validate_email
from django.conf import settings

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.conf import settings

@admin.action(description="Envoyer le lien d'activation (validation après délivrance)")
def valider_utilisateurs_action(self, request, queryset):
    success_count = 0
    for user in queryset:
        if user.est_valide:
            self.message_user(request, f"⚠️ L'utilisateur {user.email} est déjà validé.", level='WARNING')
            continue

        # Génération du token et du lien
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        lien = request.build_absolute_uri(f'/comptes/activer/{uid}/{token}/')
        sujet = "Activation de votre compte - Assemblée Nationale"
        nom = user.get_full_name() or user.username
        text_message = f"Bonjour {nom},\n\nVotre compte a été validé. Pour l'activer, cliquez ici :\n{lien}\n\nCe lien est valable 3 jours.\n\nCordialement,\nL'équipe technique"

        try:
            html_message = render_to_string('emails/activation.html', {'user': user, 'lien': lien})
        except Exception as e:
            html_message = None
            self.message_user(request, f"Erreur template pour {user.email} : {e}", level='ERROR')

        # Envoi de l'email (sans metadata)
        try:
            email = EmailMultiAlternatives(
                sujet,
                text_message,
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                # metadata={"user_id": user.id},   ← à supprimer
            )
            if html_message:
                email.attach_alternative(html_message, "text/html")
            email.send(fail_silently=False)
        except Exception as e:
            contact_info = user.contact if user.contact else "aucun numéro"
            self.message_user(
                request,
                f"❌ Échec d'envoi à {user.email} pour {user.get_full_name()}. "
                f"Contactez-le via {contact_info}. Erreur : {str(e)}",
                level='ERROR'
            )
            continue

        # Ne pas valider ici – on attend le webhook 'delivered'
        success_count += 1
        self.message_user(
    request,
    f"📧 Email d'activation envoyé à {user.email}. "
    "Si l'adresse est invalide, un rebond sera détecté et le compte sera marqué 'email_invalide' dans quelques minutes.",
    level='INFO'
)


class UtilisateurAdmin(UserAdmin):
    list_display = ('username', 'email', 'last_name', 'first_name', 'role', 'type_contrat', 'direction', 'service', 'division', 'contact', 'est_valide','email_is_invalid', 'is_active')
    list_filter = ('email_is_invalid','est_valide', 'role', 'type_contrat', 'direction', 'service', 'division')
    fieldsets = UserAdmin.fieldsets + (
        ('Informations complémentaires', {
            'fields': ('contact', 'type_contrat', 'direction', 'service', 'division', 'role', 'est_valide', 'date_validation')
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informations complémentaires', {
            'fields': ('contact', 'type_contrat', 'direction', 'service', 'division', 'role')
        }),
    )
    actions = [valider_utilisateurs_action]
    class Media:
        js = ('admin/js/jquery.init.js', 'js/admin_direct.js',)  # Notre fichier JavaScript


class UtilisateurForm(forms.ModelForm):
    class Meta:
        model = Utilisateur
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Initialiser les querysets vides
        self.fields['service'].queryset = Service.objects.none()
        self.fields['division'].queryset = Division.objects.none()

        # Si une direction est sélectionnée, charger ses services
        if 'direction' in self.data:
            try:
                direction_id = int(self.data.get('direction'))
                self.fields['service'].queryset = Service.objects.filter(direction_id=direction_id).order_by('nom')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.direction:
            self.fields['service'].queryset = Service.objects.filter(direction=self.instance.direction).order_by('nom')

        # Si un service est sélectionné, charger ses divisions
        if 'service' in self.data:
            try:
                service_id = int(self.data.get('service'))
                self.fields['division'].queryset = Division.objects.filter(service_id=service_id).order_by('nom')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.service:
            self.fields['division'].queryset = Division.objects.filter(service=self.instance.service).order_by('nom')


    

    # 👇 AJOUTEZ CES MÉTHODES POUR FILTRER LES LISTES DÉROULANTES
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "service":
            # Filtrer les services en fonction de la direction sélectionnée
            if request._obj_:
                direction_id = request._obj_.direction_id
                kwargs["queryset"] = Service.objects.filter(direction_id=direction_id)
            else:
                kwargs["queryset"] = Service.objects.none()
        elif db_field.name == "division":
            # Filtrer les divisions en fonction du service sélectionné
            if request._obj_:
                service_id = request._obj_.service_id
                kwargs["queryset"] = Division.objects.filter(service_id=service_id)
            else:
                kwargs["queryset"] = Division.objects.none()
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def get_form(self, request, obj=None, **kwargs):
        # Sauvegarder l'objet en cours pour l'utiliser dans formfield_for_foreignkey
        request._obj_ = obj
        return super().get_form(request, obj, **kwargs)

admin.site.register(Direction)
admin.site.register(Service)
admin.site.register(Division)
admin.site.register(Utilisateur, UtilisateurAdmin)