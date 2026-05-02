from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView, ListView, UpdateView, DetailView, FormView
from django.views import View
from django.http import JsonResponse
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin
from django.contrib.admin.views.decorators import staff_member_required
from django.utils.decorators import method_decorator
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django import forms
from django.core.mail import EmailMultiAlternatives  # ← IMPORTANT !
from .forms import InscriptionForm, NotificationPreferencesForm
from .models import Utilisateur, Service, Division
from requetes.models import Requete
from django.utils import timezone  # ← IMPORT MANQUANT
from validate_email import validate_email


# Vue de déconnexion

from django.contrib import messages

def deconnexion_view(request):
    # Vider tous les messages avant la déconnexion
    storage = messages.get_messages(request)
    storage.used = True  # Marque tous les messages comme lus
    
    logout(request)
    messages.success(request, "Vous avez été déconnecté avec succès.")
    return redirect('connexion')


# Inscription

class InscriptionView(UserPassesTestMixin, CreateView):
    model = Utilisateur
    form_class = InscriptionForm
    template_name = 'comptes/inscription.html'
    success_url = reverse_lazy('inscription_done')

    def test_func(self):
        return not self.request.user.is_authenticated

    def handle_no_permission(self):
        return redirect('accueil')

    def form_valid(self, form):
        response = super().form_valid(form)
        messages.success(self.request, "Votre compte a été créé. Il sera activé par l'administrateur. Vous recevrez un email pour définir votre mot de passe.")
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['hide_sidebar'] = True
        return context

class InscriptionDoneView(TemplateView):
    template_name = 'comptes/inscription_done.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['hide_sidebar'] = True
        return context


# Connexion

class ConnexionView(LoginView):
    template_name = 'comptes/connexion.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['hide_sidebar'] = True
        context['hide_sweet_alert'] = True
        return context
    
    def form_valid(self, form):
        """Gère la case "Se souvenir de moi" """
        remember_me = self.request.POST.get('remember_me')
        
        if not remember_me:
            # Si "Se souvenir de moi" n'est pas coché, la session expire à la fermeture du navigateur
            self.request.session.set_expiry(0)
        else:
            # Si coché, la session dure 2 semaines
            self.request.session.set_expiry(1209600)
            
        return super().form_valid(form)

# Activation de compte

class ActivationForm(forms.Form):
    password1 = forms.CharField(label="Mot de passe", widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(label="Confirmation", widget=forms.PasswordInput(attrs={'class': 'form-control'}))

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get("password1")
        p2 = cleaned_data.get("password2")
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Les mots de passe ne correspondent pas.")
        return cleaned_data

class ActivationView(View):
    template_name = 'comptes/activation.html'

    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = Utilisateur.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, Utilisateur.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            form = ActivationForm()
            return render(request, self.template_name, {
                'form': form,
                'uidb64': uidb64,
                'token': token,
                'validlink': True,
                'hide_sidebar': True,
            })
        else:
            return render(request, self.template_name, {'validlink': False})

    def post(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = Utilisateur.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, Utilisateur.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            form = ActivationForm(request.POST)
            if form.is_valid():
                user.set_password(form.cleaned_data['password1'])
                user.is_active = True
                user.est_valide = True
                user.save()
                messages.success(request, "Votre mot de passe a été défini. Vous pouvez maintenant vous connecter.")
                return redirect('connexion')
            else:
                return render(request, self.template_name, {
                    'form': form,
                    'uidb64': uidb64,
                    'token': token,
                    'validlink': True,
                    'hide_sidebar': True,
                })
        else:
            return render(request, self.template_name, {'validlink': False})


# API pour listes déroulantes

def api_services(request):
    direction_id = request.GET.get('direction')
    if not direction_id:
        return JsonResponse([], safe=False)
    services = Service.objects.filter(direction_id=direction_id).values('id', 'nom')
    return JsonResponse(list(services), safe=False)

def api_divisions(request):
    service_id = request.GET.get('service')
    if not service_id:
        return JsonResponse([], safe=False)
    divisions = Division.objects.filter(service_id=service_id).values('id', 'nom')
    return JsonResponse(list(divisions), safe=False)

# Gestion des utilisateurs (admin)

@method_decorator(staff_member_required, name='dispatch')
class GestionUtilisateursView(ListView):
    model = Utilisateur
    template_name = 'comptes/gestion_utilisateurs.html'
    context_object_name = 'utilisateurs'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        filtre = self.request.GET.get('filtre')
        if filtre == 'en_attente':
            queryset = queryset.filter(est_valide=False)
        elif filtre == 'valides':
            queryset = queryset.filter(est_valide=True)
        return queryset.order_by('-date_joined')

    def post(self, request, *args, **kwargs):
        if 'valider' in request.POST:
            ids = request.POST.getlist('selected_users')
            utilisateurs = Utilisateur.objects.filter(id__in=ids, est_valide=False)
            success_count = 0
            import time
            for user in utilisateurs:
                # Réinitialiser le flag email invalide (utile après correction d'email)
                user.email_is_invalid = False

                # Génération du token et du lien d'activation
                token = default_token_generator.make_token(user)
                uid = urlsafe_base64_encode(force_bytes(user.pk))
                lien = request.build_absolute_uri(f'/comptes/activer/{uid}/{token}/')
                sujet = "Activation de votre compte - Assemblée Nationale"

                nom = user.get_full_name() or user.username
                text_message = f"Bonjour {nom},\n\n"
                text_message += f"Votre compte a été validé. Pour l'activer, cliquez ici :\n{lien}\n\n"
                text_message += "Ce lien est valable 3 jours.\n\nCordialement,\nL'équipe technique"

                # Version HTML
                try:
                    html_message = render_to_string('emails/activation.html', {
                        'user': user,
                        'lien': lien
                    })
                except Exception as e:
                    html_message = None
                    print(f"Erreur template: {e}")

                # Envoi de l'email
                from django.core.mail import EmailMultiAlternatives
                try:
                    email = EmailMultiAlternatives(
                        sujet,
                        text_message,
                        settings.DEFAULT_FROM_EMAIL,
                        [user.email],
                    )
                    if html_message:
                        email.attach_alternative(html_message, "text/html")
                    email.send(fail_silently=False)
                    time.sleep(2)  # 2 secondes entre chaque email
                except Exception as e:
                    contact_info = user.contact if user.contact else "aucun numéro renseigné"
                    messages.error(
                        request,
                        f"❌ Échec d'envoi à {user.email} pour {user.get_full_name()}. "
                        f"Contactez-le via {contact_info} pour lui demander de fournir un email valide. Erreur: {str(e)}"
                    )
                    continue

                # Sauvegarde du flag réinitialisé (et du reste si nécessaire)
                user.save(update_fields=['email_is_invalid'])
                success_count += 1
                messages.info(
                    request,
                    f"📧 Email d'activation envoyé à {user.email}. "
                    "Si l'adresse est valide, le compte sera automatiquement validé après délivrance. "
                    "Sinon, il sera marqué comme 'email invalide'."
                )

            if success_count > 0:
                messages.success(
                    request,
                    f"{success_count} email(s) d'activation envoyé(s) au serveur. "
                    "⚠️ Attention : 'envoyé' ne signifie pas 'délivré'. "
                    "Si une adresse est invalide, le compte ne sera jamais validé et sera marqué 'email_invalide' après quelques minutes."
                )

        elif 'supprimer' in request.POST:
            ids = request.POST.getlist('selected_users')
            if request.user.id in ids:
                messages.error(request, "Vous ne pouvez pas supprimer votre propre compte.")
            else:
                utilisateurs = Utilisateur.objects.filter(id__in=ids)
                count = utilisateurs.count()
                utilisateurs.delete()
                messages.success(request, f"{count} utilisateur(s) supprimé(s).")

        return redirect('gestion_utilisateurs')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tous = Utilisateur.objects.all()
        context['stats'] = {
            'total': tous.count(),
            'en_attente': tous.filter(est_valide=False).count(),
            'valides': tous.filter(est_valide=True).count(),
            'actifs': tous.filter(is_active=True).count(),
        }
        context['filtre_actuel'] = self.request.GET.get('filtre', 'tous')
        return context
@method_decorator(staff_member_required, name='dispatch')
class ModifierUtilisateurView(UpdateView):
    model = Utilisateur
    fields = ['first_name', 'last_name', 'email', 'contact', 'role', 'direction', 'service', 'division', 'est_valide', 'is_active']
    template_name = 'comptes/modifier_utilisateur.html'
    success_url = reverse_lazy('gestion_utilisateurs')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['hide_sidebar'] = False
        return context

@method_decorator(staff_member_required, name='dispatch')
class DetailUtilisateurView(DetailView):
    model = Utilisateur
    template_name = 'comptes/detail_utilisateur.html'
    context_object_name = 'user_detail'

# Profil utilisateur

class ProfilView(LoginRequiredMixin, UpdateView):
    model = Utilisateur
    fields = ['first_name', 'last_name', 'email', 'contact']
    template_name = 'comptes/profil.html'
    success_url = reverse_lazy('profil')

    def get_object(self, queryset=None):
        return self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['nb_requetes_crees'] = Requete.objects.filter(demandeur=user).count()
        if user.role == 'chef_service':
            context['nb_requetes_attribuees'] = Requete.objects.filter(
                service_cible=user.service,
                division_attribuee__isnull=False
            ).count()
        else:
            context['nb_requetes_attribuees'] = None
        context['membre_depuis'] = user.date_joined.strftime('%d/%m/%Y')
        context['role_display'] = self.get_role_display(user)
        return context

    def get_role_display(self, user):
        if user.is_superuser:
            return 'Admin'
        elif user.role == 'chef_service':
            return 'Chef de service'
        elif user.role == 'chef_division':
            return 'Chef de division'
        elif user.role == 'directeur':
            return 'Directeur'
        else:
            return 'Personnel'

class ChangerMotDePasseView(PasswordChangeView):
    template_name = 'comptes/changer_mdp.html'
    success_url = reverse_lazy('profil')

    def form_valid(self, form):
        messages.success(self.request, "Votre mot de passe a été changé avec succès.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['hide_sidebar'] = False
        return context

class NotificationPreferencesView(LoginRequiredMixin, FormView):
    template_name = 'comptes/notification_prefs.html'
    form_class = NotificationPreferencesForm
    success_url = reverse_lazy('notification_prefs')

    def get_initial(self):
        prefs = self.request.user.notification_preferences
        return {
            'relance_quotidienne': prefs.get('relance_quotidienne', True),
            'attribution': prefs.get('attribution', True),
            'compte_rendu': prefs.get('compte_rendu', True),
        }

    def form_valid(self, form):
        user = self.request.user
        user.notification_preferences = {
            'relance_quotidienne': form.cleaned_data['relance_quotidienne'],
            'attribution': form.cleaned_data['attribution'],
            'compte_rendu': form.cleaned_data['compte_rendu'],
        }
        user.save(update_fields=['notification_preferences'])
        return super().form_valid(form)



from django.views.generic.edit import CreateView
from django.urls import reverse_lazy
from .models import Utilisateur
from .forms import InscriptionForm  

class AjouterUtilisateurView(CreateView):
    model = Utilisateur
    form_class = InscriptionForm
    template_name = 'comptes/ajouter_utilisateur.html'
    success_url = reverse_lazy('gestion_utilisateurs')
    
    def form_valid(self, form):
        user = form.save(commit=False)
        user.est_valide = True  # Validé directement par l'admin
        user.is_active = False   # Sera activé quand l'utilisateur définira son mot de passe
        user.save()
        
        # Envoyer l'email d'activation
        from django.contrib.auth.tokens import default_token_generator
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        from django.core.mail import EmailMultiAlternatives
        from django.template.loader import render_to_string
        from django.conf import settings
        
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        lien = self.request.build_absolute_uri(f'/comptes/activer/{uid}/{token}/')
        
        # Version texte
        text_message = f"Bonjour {user.get_full_name() or user.username},\n\n"
        text_message += f"Votre compte a été créé par l'administrateur. Pour l'activer :\n{lien}"
        
        # Version HTML
        html_message = render_to_string('emails/activation.html', {
            'user': user,
            'lien': lien
        })
        
        email = EmailMultiAlternatives(
            "Activation de votre compte",
            text_message,
            settings.EMAIL_HOST_USER,
            [user.email]
        )
        email.attach_alternative(html_message, "text/html")
        email.send()
        
        return super().form_valid(form)


