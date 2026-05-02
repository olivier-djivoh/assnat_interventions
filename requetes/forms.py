from django import forms
from .models import Requete, TypeDemande, CompteRendu
from comptes.models import Utilisateur

import os

from django.core.exceptions import ValidationError

class RequeteForm(forms.ModelForm):
    class Meta:
        model = Requete
        fields = ('type_demande', 'description', 'localisation')
        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Décrivez votre problème...'}),
            'localisation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Localisation'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['type_demande'].widget.attrs.update({'class': 'form-control'})

    # Types de fichiers autorisés
ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'pdf', 'doc', 'docx', 'xls', 'xlsx']
ALLOWED_MIME_TYPES = [
    'image/jpeg', 'image/png', 'image/gif',
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'application/vnd.ms-excel',
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
]

def validate_file_size(value):
    """Valide la taille du fichier (max 3 Mo)"""
    filesize = value.size
    if filesize > 3 * 1024 * 1024:
        raise ValidationError(f"Le fichier est trop lourd. La taille maximale est de 3 Mo. Votre fichier fait {filesize / (1024 * 1024):.1f} Mo.")

def validate_file_extension(value):
    """Valide l'extension du fichier"""
    ext = os.path.splitext(value.name)[1].lower().replace('.', '')
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(f"Format de fichier non autorisé. Formats acceptés : {', '.join(ALLOWED_EXTENSIONS)}")

def validate_file_mime_type(value):
    """Valide le type MIME du fichier"""
    from magic import from_buffer  # python-magic
    try:
        file_content = value.read(1024)
        mime_type = from_buffer(file_content, mime=True)
        value.seek(0)  # Revenir au début du fichier
        if mime_type not in ALLOWED_MIME_TYPES:
            raise ValidationError(f"Type de fichier non autorisé.")
    except ImportError:
       
        pass
       
class AttributionForm(forms.Form):
    chef_division = forms.ModelChoiceField(
        queryset=None,
        label="Chef de division",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    commentaire = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        required=False,
        label="Commentaire (optionnel)"
    )

    def __init__(self, *args, **kwargs):
        service = kwargs.pop('service', None)
        super().__init__(*args, **kwargs)
        if service:
            self.fields['chef_division'].queryset = Utilisateur.objects.filter(
                division__service=service,
                is_active=True,
                est_valide=True,
                role='chef_division'
            ).distinct().order_by('last_name', 'first_name')
        else:
            self.fields['chef_division'].queryset = Utilisateur.objects.none()

class CompteRenduForm(forms.ModelForm):
    class Meta:
        model = CompteRendu
        fields = ('contenu', 'intervention_resolue', 'pieces_jointes')
        widgets = {
            'contenu': forms.Textarea(attrs={'rows': 4, 'class': 'form-control', 'placeholder': 'Détaillez votre intervention...'}),
            'pieces_jointes': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'intervention_resolue': "Le problème est-il résolu ?",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
       
        self.fields['intervention_resolue'].widget = forms.RadioSelect(
            choices=[
                (True, '✅ Oui, le problème est résolu'),
                (False, '⏳ Non, en attente'),
            ],
            attrs={'class': 'form-check-input'}
        )



from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, FormView, TemplateView
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Requete, CompteRendu, Attribution
from .forms import RequeteForm, AttributionForm, CompteRenduForm
from comptes.mixins import EstPersonnelMixin, EstChefServiceMixin, EstChefDivisionMixin

class RequeteCreateView(EstPersonnelMixin, CreateView):
    model = Requete
    form_class = RequeteForm
    template_name = 'requetes/creer.html'
    success_url = reverse_lazy('accueil')

    def form_valid(self, form):
        form.instance.demandeur = self.request.user
        # Routage automatique : le service cible est celui du type de demande
        type_demande = form.cleaned_data['type_demande']
        form.instance.service_cible = type_demande.service_cible
        return super().form_valid(form)