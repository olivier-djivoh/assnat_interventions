from django.urls import path
from . import views

urlpatterns = [
    path('creer/', views.RequeteCreateView.as_view(), name='creer_requete'),
    path('<int:pk>/', views.RequeteDetailView.as_view(), name='detail_requete'),
    path('<int:pk>/attribuer/', views.AttributionView.as_view(), name='attribuer_requete'),
    path('<int:pk>/compte-rendu/', views.CompteRenduCreateView.as_view(), name='compte_rendu'),
    path('<int:pk>/cloturer/', views.RequeteCloturerView.as_view(), name='cloturer_requete'),
    path('statistiques/', views.statistiques_json, name='statistiques_json'),
    path('a-attribuer/', views.RequetesAAttribuerView.as_view(), name='requetes_a_attribuer'),
    path('mes-interventions/', views.MesInterventionsView.as_view(), name='mes_interventions'),
    path('liste/', views.ListeDemandesView.as_view(), name='liste_demandes'),
    path('api/liste-demandes/', views.api_liste_demandes, name='api_liste_demandes'),
    path('api/accueil/', views.api_accueil, name='api_accueil'),
    path('requetes-attribuees/', views.RequetesAttribueesView.as_view(), name='requetes_attribuees'),
    path('api/requetes-attribuees/', views.api_requetes_attribuees, name='api_requetes_attribuees'),
    path('compte-rendu/<int:pk>/modifier/', views.ModifierCompteRenduView.as_view(), name='modifier_compte_rendu'),
    
]