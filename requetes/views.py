from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, TemplateView, FormView, ListView, UpdateView
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.http import JsonResponse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import Requete, CompteRendu, Attribution
from .forms import RequeteForm, AttributionForm, CompteRenduForm
from comptes.mixins import EstPersonnelMixin, EstChefServiceMixin, EstChefDivisionMixin
from comptes.models import Service, Utilisateur

class AccueilView(LoginRequiredMixin, TemplateView):
    template_name = 'accueil.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Récupération des requêtes selon le rôle
        if user.is_superuser:
            requetes = Requete.objects.all()
        elif user.role == 'chef_division':
            requetes = Requete.objects.filter(division_attribuee=user.division)
        elif user.role == 'chef_service':
            requetes = Requete.objects.filter(service_cible=user.service)
        elif user.role == 'directeur':
            requetes = Requete.objects.filter(service_cible__direction=user.direction)
        else:
            requetes = Requete.objects.filter(demandeur=user)

        # Gestion du tri
        order = self.request.GET.get('order', '-date_creation')
        allowed_fields = ['date_creation', 'titre', 'statut','-date_creation', '-titre', '-statut']
        if order in allowed_fields:
            requetes = requetes.order_by(order)
        else:
            requetes = requetes.order_by('-date_creation')

        # Statistiques
        context['requetes'] = requetes  # ici on garde le tri déjà appliqué
        context['total_requetes'] = requetes.count()
        context['nouvelles'] = requetes.filter(statut='EN_ATTENTE').count()
        context['resolues'] = requetes.filter(statut='RESOLU').count()
        context['order'] = order
        return context
    


from django.views.generic import CreateView
from .models import Requete, TypeDemande



from django.shortcuts import get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, TemplateView, FormView, ListView
from django.views import View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count
from django.http import JsonResponse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import Requete, CompteRendu, Attribution, TypeDemande
from .forms import RequeteForm, AttributionForm, CompteRenduForm
from comptes.mixins import EstPersonnelMixin, EstChefServiceMixin, EstChefDivisionMixin



from comptes.models import Service

# ===== DICTIONNAIRE DES MOTS-CLÉS =====
ROUTING_KEYWORDS = {
    'Service infrastructures réseaux et maintenance': [
        'réseau', 'wifi', 'internet', 'connexion', 'déconnexion', 'câble', 'prise réseau',
        'ethernet', 'fibre', 'routeur', 'switch', 'modem', 'box', 'vpn',
        'panne réseau', 'coupure internet', 'plus de réseau', 'pas de wifi', 'réseau lent',
        'connexion instable', 'carte réseau', 'antenne wifi', 'borne wifi'
    ],
    'Service développement, applications et e-services': [
        'logiciel', 'application', 'programme', 'installation', 'mise à jour', 'bug', 'erreur',
        'crash', 'plantage', 'word', 'excel', 'powerpoint', 'outlook', 'office',
        'email', 'courriel', 'messagerie', 'impression', 'imprimante', 'scanner', 'scan',
        'windows', 'linux', 'serveur', 'site web', 'intranet', 'téléchargement'
    ],
    'Service du patrimoine non financier et de l\'entretien': [
        'plomberie', 'fuite', 'eau', 'robinet', 'évier', 'wc', 'toilette', 'chasse eau',
        'débouchage', 'tuyau', 'chauffe eau', 'électricité', 'panne de courant',
        'coupure', 'disjoncteur', 'prise', 'interrupteur', 'ampoule', 'lumière','lampe',
        'chauffage', 'radiateur', 'chaudière', 'climatisation', 'clim', 'ventilation',
        'ventilateur', 'porte', 'fenêtre', 'volet', 'serrure', 'vitre', 'peinture',
        'mur', 'plafond', 'sol', 'carrelage', 'fissure', 'infiltration', 'gouttière'
    ],
    'Service des archives et de la gestion des savoirs': [
        'archivage', 'archives', 'document', 'dossier', 'classeur', 'carton', 'rangement',
        'classement', 'inventaire', 'consultation', 'numérisation', 'scan', 'copie numérique',
        'pdf', 'documentation', 'bibliothèque', 'notice', 'mode d emploi', 'procédure',
        'tutoriel', 'guide', 'catalogue', 'recherche'
    ],
}

# Définir la priorité des services
SERVICE_PRIORITE = {
    'Service du patrimoine non financier et de l\'entretien': 1,  # Urgence (fuite, électricité)
    'Service infrastructures réseaux et maintenance': 2,          # Panne réseau
    'Service développement, applications et e-services': 3,       # Logiciel
    'Service des archives et de la gestion des savoirs': 4,       # Archivage
}

def trouver_service_par_mots_cles(texte):
    """
    Trouve le service le plus pertinent selon :
    1. Le nombre de mots-clés correspondants
    2. La priorité du service en cas d'égalité
    """
    texte = texte.lower()
    
    # Compter les correspondances par service
    comptage = {}
    for service_nom, mots_cles in ROUTING_KEYWORDS.items():
        compteur = 0
        for mot in mots_cles:
            if mot in texte:
                compteur += 1
        if compteur > 0:
            comptage[service_nom] = compteur
    
    if not comptage:
        return None
    
    # Trouver le score maximum
    max_score = max(comptage.values())
    
    # Récupérer les services avec le score maximum
    gagnants = [nom for nom, score in comptage.items() if score == max_score]
    
    if len(gagnants) == 1:
        return Service.objects.filter(nom__icontains=gagnants[0]).first()
    
    # En cas d'égalité, appliquer la priorité
    gagnants.sort(key=lambda s: SERVICE_PRIORITE.get(s, 99))
    return Service.objects.filter(nom__icontains=gagnants[0]).first()


def obtenir_service_par_defaut():
    """Retourne le service par défaut pour les requêtes non routées"""
    service = Service.objects.filter(nom__icontains="Service d'Accueil").first()
    if not service:
        service = Service.objects.first()
    return service




class RequeteCreateView(EstPersonnelMixin, CreateView):
    model = Requete
    form_class = RequeteForm
    template_name = 'requetes/creer.html'
    # Pas de success_url, on utilise get_success_url

    def get_success_url(self):
        return reverse_lazy('detail_requete', kwargs={'pk': self.object.pk})
    def form_valid(self, form):
        # Vérifier que l'utilisateur est authentifié
        if not self.request.user.is_authenticated:
            messages.error(self.request, "Vous devez être connecté.")
            return redirect('connexion')
        

        form.instance.demandeur = self.request.user
        
        # Récupérer le type de demande
        type_demande_obj = form.cleaned_data.get('type_demande')
        
        # Si c'est "Autre", on applique le routage par mots-clés
        if type_demande_obj and type_demande_obj.nom == "Autre":
            description = form.cleaned_data.get('description', '')
            texte_complet = f" {description}"
            
            service_trouve = trouver_service_par_mots_cles(texte_complet)
            
            if service_trouve:
                form.instance.service_cible = service_trouve
                messages.info(self.request, f"✅ Votre demande a été dirigée vers {service_trouve.nom}.")
            else:
                form.instance.service_cible = type_demande_obj.service_cible
                messages.info(self.request, "Votre demande a été envoyée au service par défaut.")
        else:
            # Routage normal
            form.instance.service_cible = type_demande_obj.service_cible
        
        return super().form_valid(form)
class RequeteDetailView(LoginRequiredMixin, DetailView):
    model = Requete
    template_name = 'requetes/detail.html'
    context_object_name = 'requete'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        requete = self.object
        user = self.request.user
        compte_rendu = requete.comptes_rendus.first()

        if not (user == requete.demandeur or user.service == requete.service_cible or user.division == requete.division_attribuee or user.is_superuser):
            messages.error(self.request, "Vous n'êtes pas autorisé à voir cette requête.")
            context['non_autorise'] = True
            return context

        compte_rendu = requete.comptes_rendus.first()

        context['peut_attribuer'] = (
            user.role == 'chef_service' and
            requete.statut == 'EN_ATTENTE' and
            not requete.division_attribuee
        )
        
        context['peut_rendre_compte'] = (
            user.role == 'chef_division' and
            user.division == requete.division_attribuee and
            requete.statut == 'EN_ATTENTE' and
            not compte_rendu  # Pas encore de compte rendu
        )
        
        context['peut_cloturer'] = (
            user.role == 'chef_service' and
            requete.statut == 'EN_ATTENTE' and
            requete.division_attribuee is not None
        )
        
        context['peut_modifier_compte_rendu'] = (
            compte_rendu and
            user.role == 'chef_division' and
            compte_rendu.chef_division == user and
            requete.statut == 'EN_ATTENTE' and
            not compte_rendu.intervention_resolue  # Seulement si non résolu
        )
        
        # Ajouter les informations sur le statut du compte rendu
        context['compte_rendu'] = compte_rendu
        context['statut_compte_rendu_display'] = requete.get_statut_compte_rendu_display()
        context['statut_compte_rendu_code'] = requete.statut_compte_rendu
        
        return context

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

class AttributionView(EstChefServiceMixin, FormView):
    template_name = 'requetes/attribution.html'
    form_class = AttributionForm
    success_url = reverse_lazy('accueil')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['service'] = self.request.user.service
        return kwargs

    def form_valid(self, form):
        requete_id = self.kwargs.get('pk')
        requete = get_object_or_404(Requete, pk=requete_id)
        
        if requete.service_cible != self.request.user.service:
            messages.error(self.request, "Cette requête ne dépend pas de votre service.")
            return redirect('accueil')

        chef_division = form.cleaned_data['chef_division']
        commentaire = form.cleaned_data['commentaire']

        requete.division_attribuee = chef_division.division
        requete.date_attribution = timezone.now()
        requete.save()

        Attribution.objects.create(
            requete=requete,
            chef_service=self.request.user,
            chef_division=chef_division,
            commentaire=commentaire
        )

        # ✅ NOTIFICATION EN TEMPS RÉEL (déplacée après la définition des variables)
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        if hasattr(chef_division, 'notif_prefs') and chef_division.notif_prefs.attribution:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f'user_{chef_division.id}',
                {
                    'type': 'send_notification',
                    'message': f'Requête attribuée : {requete.titre}',
                    'url': f'/requetes/{requete.id}/'
                }
            )

        messages.success(self.request, f"Requête attribuée à {chef_division.get_full_name()}.")
        return redirect('detail_requete', pk=requete_id)

class CompteRenduCreateView(EstChefDivisionMixin, CreateView):
    model = CompteRendu
    form_class = CompteRenduForm
    template_name = 'requetes/compte_rendu.html'

    def dispatch(self, request, *args, **kwargs):
        requete_id = self.kwargs.get('pk')
        self.requete = get_object_or_404(Requete, pk=requete_id)
        
        if self.requete.division_attribuee != request.user.division:
            messages.error(request, "Cette requête n'est pas attribuée à votre division.")
            return redirect('accueil')
        
        if self.requete.comptes_rendus.exists():
            messages.error(request, "Un compte rendu existe déjà pour cette requête.")
            return redirect('detail_requete', pk=self.requete.pk)
        
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('detail_requete', kwargs={'pk': self.requete.pk})

    def form_valid(self, form):
        form.instance.requete = self.requete
        form.instance.chef_division = self.request.user
        
        if form.cleaned_data['intervention_resolue']:
            self.requete.statut_compte_rendu = 'RESOLU'
        else:
            self.requete.statut_compte_rendu = 'EN_COURS'
        self.requete.save()
        
        messages.success(self.request, "✅ Compte rendu enregistré avec succès !")
        return super().form_valid(form)
class RequeteCloturerView(EstChefServiceMixin, View):
    def post(self, request, pk):
        requete = get_object_or_404(Requete, pk=pk)
        if requete.service_cible != request.user.service:
            messages.error(request, "Vous n'êtes pas autorisé à clôturer cette requête.")
            return redirect('accueil')

        requete.statut = 'RESOLU'
        requete.date_resolution = timezone.now()
        requete.save()
        
        messages.success(request, f"✅ La requête #{requete.id} a été clôturée avec succès.")
        return redirect('detail_requete', pk=pk)



from django.http import JsonResponse
from django.db.models import Count, Q
from django.utils import timezone

def statistiques_json(request):
    user = request.user
    if not user.is_authenticated or not user.est_valide:
        return JsonResponse({'error': 'Non autorisé'}, status=403)

    # Superuser voit toutes les requêtes
    if user.is_superuser:
        requetes = Requete.objects.all()
    elif user.role == 'chef_service':
        if not user.service:
            return JsonResponse({'error': 'Utilisateur sans service'}, status=400)
        requetes = Requete.objects.filter(service_cible=user.service)
    elif user.role == 'directeur':
        if not user.direction:
            return JsonResponse({'error': 'Utilisateur sans direction'}, status=400)
        requetes = Requete.objects.filter(service_cible__direction=user.direction)
    else:
        return JsonResponse({'error': 'Accès réservé'}, status=403)

    total = requetes.count()
    en_attente = requetes.filter(statut='EN_ATTENTE').count()
    resolues = requetes.filter(statut='RESOLU').count()

    # Répartition par type de demande
    types = requetes.values('type_demande__nom').annotate(count=Count('id')).order_by('-count')
    types_labels = [t['type_demande__nom'] for t in types]
    types_data = [t['count'] for t in types]

    # Délai moyen de résolution (en jours)
    resolved = requetes.filter(statut='RESOLU', date_resolution__isnull=False)
    total_delai = 0
    count_delai = resolved.count()
    for r in resolved:
        delta = r.date_resolution - r.date_creation
        total_delai += delta.total_seconds() / 86400  # en jours
    delai_moyen = round(total_delai / count_delai, 1) if count_delai > 0 else 0

    data = {
        'total': total,
        'en_attente': en_attente,
        'resolues': resolues,
        'types_labels': types_labels,
        'types_data': types_data,
        'delai_moyen': delai_moyen,
    }
    return JsonResponse(data)


from asgiref.sync import async_to_sync
from comptes.models import Utilisateur

class RequetesAAttribuerView(EstChefServiceMixin, ListView):
    model = Requete
    template_name = 'requetes/requetes_a_attribuer.html'
    context_object_name = 'requetes'

    def get_queryset(self):
        return Requete.objects.filter(
            service_cible=self.request.user.service,
            statut='EN_ATTENTE',
            division_attribuee__isnull=True
        ).order_by('-date_creation')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Ajouter la liste des chefs de division du service
        context['chefs_division'] = Utilisateur.objects.filter(
            division__service=self.request.user.service,
            role='chef_division',
            est_valide=True,
            is_active=True
        ).distinct().order_by('last_name', 'first_name')
        return context
    
class MesInterventionsView(EstChefDivisionMixin, ListView):
    model = Requete
    template_name = 'requetes/mes_interventions.html'
    context_object_name = 'requetes'

    def get_queryset(self):
        # Filtrer les requêtes attribuées à la division du chef connecté
        return Requete.objects.filter(
            division_attribuee=self.request.user.division
        ).order_by('-date_creation')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Pour chaque requête, ajouter une information sur l'existence d'un compte rendu
        requetes = context['requetes']
        for requete in requetes:
            requete.a_un_compte_rendu = requete.comptes_rendus.exists()
        
        return context


from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Requete
from comptes.models import Service

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

class ListeDemandesView(LoginRequiredMixin, ListView):
    model = Requete
    template_name = 'requetes/liste.html'
    context_object_name = 'requetes'
    paginate_by = 10  # Nombre d'éléments par page

    def test_func(self):
        user = self.request.user
        return user.is_superuser or user.role in ['chef_service', 'directeur']

    def get_queryset(self):
        user = self.request.user
        queryset = Requete.objects.all().order_by('-date_creation')

        if user.is_superuser:
            queryset = Requete.objects.all()
        elif user.role == 'chef_service':
            queryset = Requete.objects.filter(service_cible=user.service)
        elif user.role == 'directeur':
            queryset = Requete.objects.filter(service_cible__direction=user.direction)
        else:
            queryset = Requete.objects.filter(demandeur=user)

        # Filtres via GET
        statut = self.request.GET.get('statut')
        if statut and statut != 'tous':
            queryset = queryset.filter(statut=statut)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Récupérer la page courante
        page = self.request.GET.get('page', 1)
        
        # Pagination
        paginator = Paginator(self.get_queryset(), self.paginate_by)
        
        try:
            requetes_page = paginator.page(page)
        except PageNotAnInteger:
            requetes_page = paginator.page(1)
        except EmptyPage:
            requetes_page = paginator.page(paginator.num_pages)
        
        context['requetes'] = requetes_page
        context['paginator'] = paginator
        context['page_obj'] = requetes_page
        context['statut_actuel'] = self.request.GET.get('statut', 'tous')
        
        return context

from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from datetime import datetime
from .models import Requete

def api_liste_demandes(request):
    """
    API pour la liste des demandes avec filtres avancés
    """
    user = request.user
    
    if not user.is_authenticated:
        return JsonResponse({'error': 'Non autorisé'}, status=403)
    
    # Récupérer les requêtes selon le rôle
    if user.is_superuser:
        queryset = Requete.objects.all()
    elif user.role == 'chef_service':
        if not user.service:
            return JsonResponse({'error': 'Service non défini'}, status=400)
        queryset = Requete.objects.filter(service_cible=user.service)
    elif user.role == 'directeur':
        if not user.direction:
            return JsonResponse({'error': 'Direction non définie'}, status=400)
        queryset = Requete.objects.filter(service_cible__direction=user.direction)
    else:
        queryset = Requete.objects.filter(demandeur=user)
    
    # Filtre par statut
    statut = request.GET.get('statut', 'tous')
    if statut != 'tous':
        queryset = queryset.filter(statut=statut)
    
    # Filtre par recherche (description, demandeur, type, localisation)
    search = request.GET.get('search', '').strip()
    if search:
        queryset = queryset.filter(
            Q(description__icontains=search) |
            Q(demandeur__first_name__icontains=search) |
            Q(demandeur__last_name__icontains=search) |
            Q(demandeur__username__icontains=search) |
            Q(type_demande__nom__icontains=search) |
            Q(localisation__icontains=search)
        )  # ← SUPPRIMER Q(titre__icontains=search)
    
    # Filtre par intervalle de dates
    date_debut = request.GET.get('date_debut', '')
    date_fin = request.GET.get('date_fin', '')
    
    if date_debut:
        try:
            debut = datetime.strptime(date_debut, '%Y-%m-%d')
            queryset = queryset.filter(date_creation__date__gte=debut.date())
        except ValueError:
            pass
    
    if date_fin:
        try:
            fin = datetime.strptime(date_fin, '%Y-%m-%d')
            queryset = queryset.filter(date_creation__date__lte=fin.date())
        except ValueError:
            pass
    
    # Trier par date décroissante
    queryset = queryset.order_by('-date_creation')
    
    # Pagination
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 10)
    
    paginator = Paginator(queryset, per_page)
    
    try:
        current_page = paginator.page(page)
    except:
        current_page = paginator.page(1)
    
    # Construction de la réponse
    data = {
        'total': paginator.count,
        'total_pages': paginator.num_pages,
        'current_page': current_page.number,
        'has_next': current_page.has_next(),
        'has_previous': current_page.has_previous(),
        'requetes': []
    }
    
    for req in current_page:
        date_locale = req.date_creation.astimezone()
        demandeur = req.demandeur.get_full_name()
        if not demandeur:
            demandeur = req.demandeur.username if req.demandeur else 'Utilisateur inconnu'
        
        data['requetes'].append({
            'id': req.id,
            'date_creation': date_locale.strftime('%d/%m/%Y %H:%M'),
            'date': date_locale.strftime('%d/%m/%Y'),
            'heure': date_locale.strftime('%H:%M'),
            'statut': req.get_statut_display(),
            'statut_code': req.statut,
            'demandeur': demandeur,
            'type_demande': req.type_demande.nom if req.type_demande else 'Non défini',
            'url': f'/requetes/{req.id}/'
        })
    
    return JsonResponse(data)      






from django.views.generic import TemplateView

class LandingPageView(TemplateView):
    template_name = 'landing.html'



def api_accueil(request):
    """API pour le tableau de bord avec filtres"""
    user = request.user
    
    if not user.is_authenticated:
        return JsonResponse({'error': 'Non autorisé'}, status=403)
    
    # Récupérer les requêtes selon le rôle
    if user.is_superuser:
        queryset = Requete.objects.all()
    elif user.role == 'chef_division':
        if not user.division:
            return JsonResponse({'error': 'Division non définie'}, status=400)
        queryset = Requete.objects.filter(division_attribuee=user.division)
    elif user.role == 'chef_service':
        if not user.service:
            return JsonResponse({'error': 'Service non défini'}, status=400)
        queryset = Requete.objects.filter(service_cible=user.service)
    elif user.role == 'directeur':
        if not user.direction:
            return JsonResponse({'error': 'Direction non définie'}, status=400)
        queryset = Requete.objects.filter(service_cible__direction=user.direction)
    else:
        queryset = Requete.objects.filter(demandeur=user)
    
    # Filtre par statut
    statut = request.GET.get('statut', 'tous')
    if statut != 'tous':
        queryset = queryset.filter(statut=statut)
    
    # Filtre par recherche
    search = request.GET.get('search', '').strip()
    if search:
        queryset = queryset.filter(
            Q(description__icontains=search) |
            Q(demandeur__first_name__icontains=search) |
            Q(demandeur__last_name__icontains=search) |
            Q(demandeur__username__icontains=search) |
            Q(type_demande__nom__icontains=search)
        )
    
    queryset = queryset.order_by('-date_creation')
    
    # Pagination
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 10)
    
    paginator = Paginator(queryset, per_page)
    
    try:
        current_page = paginator.page(page)
    except:
        current_page = paginator.page(1)
    
    data = {
        'total': paginator.count,
        'total_pages': paginator.num_pages,
        'current_page': current_page.number,
        'requetes': []
    }
    
    for req in current_page:
        date_locale = req.date_creation.astimezone()
        
        data['requetes'].append({
            'id': req.id,
            'date_creation': date_locale.strftime('%d/%m/%Y %H:%M'),
            'date': date_locale.strftime('%d/%m/%Y'),
            'heure': date_locale.strftime('%H:%M'),
            'statut': req.get_statut_display(),
            'statut_code': req.statut,
            'statut_compte_rendu': req.get_statut_compte_rendu_display(),
            'statut_compte_rendu_code': req.statut_compte_rendu,
            'url': f'/requetes/{req.id}/'
        })
    
    return JsonResponse(data)


from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.db.models import Q
from .models import Requete
from comptes.models import Utilisateur, Division

class RequetesAttribueesView(LoginRequiredMixin, ListView):
    model = Requete
    template_name = 'requetes/requetes_attribuees.html'
    context_object_name = 'requetes'
    paginate_by = 10

    def get_queryset(self):
        user = self.request.user
        
        # Filtrer selon le rôle
        if user.role == 'chef_service':
            # Voir les requêtes attribuées dans son service
            return Requete.objects.filter(
                service_cible=user.service,
                division_attribuee__isnull=False
            ).order_by('-date_creation')
        elif user.role == 'directeur':
            # Voir les requêtes attribuées dans sa direction
            return Requete.objects.filter(
                service_cible__direction=user.direction,
                division_attribuee__isnull=False
            ).order_by('-date_creation')
        elif user.is_superuser:
            # Voir toutes les requêtes attribuées
            return Requete.objects.filter(
                division_attribuee__isnull=False
            ).order_by('-date_creation')
        else:
            # Personnel - voir ses propres requêtes attribuées
            return Requete.objects.filter(
                demandeur=user,
                division_attribuee__isnull=False
            ).order_by('-date_creation')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Ajouter la liste des divisions pour le filtre
        user = self.request.user
        if user.role == 'chef_service':
            context['divisions'] = Division.objects.filter(service=user.service)
        elif user.role == 'directeur':
            context['divisions'] = Division.objects.filter(service__direction=user.direction)
        elif user.is_superuser:
            context['divisions'] = Division.objects.all()
        else:
            context['divisions'] = Division.objects.none()
        return context


def api_requetes_attribuees(request):
    """API pour la liste des requêtes attribuées avec filtres"""
    user = request.user
    
    if not user.is_authenticated:
        return JsonResponse({'error': 'Non autorisé'}, status=403)
    
    # Récupérer les requêtes selon le rôle
    if user.role == 'chef_service':
        queryset = Requete.objects.filter(
            service_cible=user.service,
            division_attribuee__isnull=False
        )
    elif user.role == 'directeur':
        queryset = Requete.objects.filter(
            service_cible__direction=user.direction,
            division_attribuee__isnull=False
        )
    elif user.is_superuser:
        queryset = Requete.objects.filter(division_attribuee__isnull=False)
    else:
        queryset = Requete.objects.filter(
            demandeur=user,
            division_attribuee__isnull=False
        )
    
    # Filtre par division
    division_id = request.GET.get('division')
    if division_id and division_id != 'tous':
        queryset = queryset.filter(division_attribuee_id=division_id)
    
    # Filtre par statut
    statut = request.GET.get('statut', 'tous')
    if statut != 'tous':
        queryset = queryset.filter(statut=statut)
    
    # Filtre par recherche
    search = request.GET.get('search', '').strip()
    if search:
        queryset = queryset.filter(
            Q(description__icontains=search) |
            Q(demandeur__first_name__icontains=search) |
            Q(demandeur__last_name__icontains=search) |
            Q(type_demande__nom__icontains=search) |
            Q(division_attribuee__nom__icontains=search)
        )
    
    queryset = queryset.order_by('-date_creation')
    
    # Pagination
    page = request.GET.get('page', 1)
    per_page = request.GET.get('per_page', 10)
    paginator = Paginator(queryset, per_page)
    
    try:
        current_page = paginator.page(page)
    except:
        current_page = paginator.page(1)
    
    data = {
        'total': paginator.count,
        'total_pages': paginator.num_pages,
        'current_page': current_page.number,
        'requetes': []
    }
    
    for req in current_page:
        date_locale = req.date_creation.astimezone()
        data['requetes'].append({
            'id': req.id,
            'date_creation': date_locale.strftime('%d/%m/%Y %H:%M'),
            'date': date_locale.strftime('%d/%m/%Y'),
            'heure': date_locale.strftime('%H:%M'),
            'statut': req.get_statut_display(),
            'statut_code': req.statut,
            'demandeur': req.demandeur.get_full_name(),
            'type_demande': req.type_demande.nom if req.type_demande else 'Non défini',
            'division': req.division_attribuee.nom if req.division_attribuee else 'Non attribuée',
            'chef_division': req.attributions.last().chef_division.get_full_name() if req.attributions.last() and req.attributions.last().chef_division else 'Non défini',
            'url': f'/requetes/{req.id}/'
        })
    
    return JsonResponse(data)


# requetes/views.py - Ajouter une vue d'édition

class ModifierCompteRenduView(EstChefDivisionMixin, UpdateView):
    model = CompteRendu
    form_class = CompteRenduForm
    template_name = 'requetes/modifier_compte_rendu.html'
    
    def get_success_url(self):
        return reverse_lazy('detail_requete', kwargs={'pk': self.object.requete_id})
    
    def form_valid(self, form):
        compte_rendu = self.object
        requete = compte_rendu.requete
        
        # Mettre à jour la date de dernière modification
        compte_rendu.date_derniere_modification = timezone.now()
        
        if form.cleaned_data['intervention_resolue']:
            requete.statut_compte_rendu = 'RESOLU'
        else:
            # Le statut reste "MODIFIE" (ou "EN_COURS" si première modification)
            if requete.statut_compte_rendu == 'AUCUN':
                requete.statut_compte_rendu = 'EN_COURS'
            else:
                requete.statut_compte_rendu = 'MODIFIE'
        
        requete.save()
        response = super().form_valid(form)
        messages.success(self.request, "✅ Compte rendu modifié avec succès.")
        return response