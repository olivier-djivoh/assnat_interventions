from django.contrib.auth.views import (
    PasswordResetView, PasswordResetDoneView, 
    PasswordResetConfirmView, PasswordResetCompleteView
)

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.auth.views import PasswordResetView
from django.urls import reverse_lazy
from django.conf import settings

import os
from email.mime.image import MIMEImage
from django.contrib.auth.views import PasswordResetView
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.conf import settings
from django.contrib.staticfiles import finders

class CustomPasswordResetView(PasswordResetView):
    template_name = 'registration/password_reset_form.html'
    email_template_name = 'registration/password_reset_email.txt'
    html_email_template_name = 'registration/password_reset_email.html'
    subject_template_name = 'registration/password_reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['hide_sidebar'] = True
        return context

    def send_mail(self, subject_template_name, email_template_name,
                  context, from_email, to_email,
                  html_email_template_name=None):
        """
        Envoie l'email de réinitialisation avec le logo attaché (CID)
        """
        # Sujet
        subject = render_to_string(subject_template_name, context).strip()
        # Corps texte
        body = render_to_string(email_template_name, context)
        # Corps HTML
        html_body = render_to_string(self.html_email_template_name, context)
        
        # Créer l'email
        email = EmailMultiAlternatives(subject, body, from_email, [to_email])
        email.attach_alternative(html_body, "text/html")
        
        # --- Attacher le logo en CID ---
        # Chercher le fichier 'an.png' dans les dossiers static
        logo_path = finders.find('images/an.png')
        if not logo_path:
            # Chemin absolu alternatif
            logo_path = os.path.join(settings.BASE_DIR, 'static', 'images', 'an.png')
        
        print(f"Chemin du logo : {logo_path}")  # Debug
        print(f"Existe ? {os.path.exists(logo_path)}")  # Debug
        
        if os.path.exists(logo_path):
            with open(logo_path, 'rb') as f:
                logo_data = f.read()
                logo = MIMEImage(logo_data)
                logo.add_header('Content-ID', '<logo>')
                logo.add_header('Content-Disposition', 'inline', filename='logo.png')
                email.attach(logo)
                print("✅ Logo attaché avec succès")
        else:
            print("❌ Logo non trouvé – vérifiez le chemin")
        
        # Envoyer l'email
        email.send()

class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'registration/password_reset_done.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['hide_sidebar'] = True
        return context

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'registration/password_reset_confirm.html'
    success_url = reverse_lazy('password_reset_complete')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['hide_sidebar'] = True
        return context

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'registration/password_reset_complete.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['hide_sidebar'] = True
        return context