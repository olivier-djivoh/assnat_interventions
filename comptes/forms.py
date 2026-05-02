from django import forms
from .models import Utilisateur, Direction, Service, Division
from django.core.exceptions import ValidationError

class InscriptionForm(forms.ModelForm):

   # Redéfinition explicite du champ contact avec son propre widget
    contact = forms.CharField(
        max_length=20,
        required=True,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'XX XX XX XX'}),
        label="Contact"
    )

    class Meta:
        model = Utilisateur
        fields = ('username', 'first_name', 'last_name', 'email', 'contact', 'type_contrat', 'direction', 'service', 'division')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['direction'].required = False
        self.fields['service'].required = False
        self.fields['division'].required = False
        self.fields['service'].queryset = Service.objects.none()
        self.fields['division'].queryset = Division.objects.none()
        self.fields['contact'].required = True

        if 'direction' in self.data:
            try:
                direction_id = int(self.data.get('direction'))
                self.fields['service'].queryset = Service.objects.filter(direction_id=direction_id).order_by('nom')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.direction:
            self.fields['service'].queryset = Service.objects.filter(direction=self.instance.direction).order_by('nom')

        if 'service' in self.data:
            try:
                service_id = int(self.data.get('service'))
                self.fields['division'].queryset = Division.objects.filter(service_id=service_id).order_by('nom')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.service:
            self.fields['division'].queryset = Division.objects.filter(service=self.instance.service).order_by('nom')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.est_valide = False
        user.is_active = False
        user.set_unusable_password()
        if commit:
            user.save()
        return user

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Utilisateur.objects.filter(email=email).exists():
            raise ValidationError("Cet email est déjà utilisé. Veuillez en choisir un autre.")
        return email

    def clean_contact(self):
        contact = self.cleaned_data.get('contact', '')
        # Supprimer tous les caractères non numériques
        import re
        chiffres = re.sub(r'\D', '', contact)
        if len(chiffres) != 8:
            raise ValidationError("Le numéro doit contenir exactement 8 chiffres (ex: 12 34 56 78).")
        # Formater le numéro complet avec le préfixe
        return f"+229 01 {chiffres[:2]} {chiffres[2:4]} {chiffres[4:6]} {chiffres[6:8]}"

class NotificationPreferencesForm(forms.Form):
    relance_quotidienne = forms.BooleanField(
        required=False,
        initial=True,
        label="Recevoir les relances quotidiennes"
    )
    attribution = forms.BooleanField(
        required=False,
        initial=True,
        label="Recevoir une notification lors d'une attribution"
    )
    compte_rendu = forms.BooleanField(
        required=False,
        initial=True,
        label="Recevoir une notification lors d'un compte rendu"
    )