from django.urls import path
from . import views

urlpatterns = [
    path('inscription/', views.InscriptionView.as_view(), name='inscription'),
    path('inscription/done/', views.InscriptionDoneView.as_view(), name='inscription_done'),
    path('connexion/', views.ConnexionView.as_view(), name='connexion'),
    path('deconnexion/', views.deconnexion_view, name='deconnexion'),
    path('activer/<uidb64>/<token>/', views.ActivationView.as_view(), name='activation'),
    path('api/services/', views.api_services, name='api_services'),
    path('api/divisions/', views.api_divisions, name='api_divisions'),
    path('gestion-utilisateurs/', views.GestionUtilisateursView.as_view(), name='gestion_utilisateurs'),
    path('modifier-utilisateur/<int:pk>/', views.ModifierUtilisateurView.as_view(), name='modifier_utilisateur'),
    path('profil/', views.ProfilView.as_view(), name='profil'),
    path('changer-mot-de-passe/', views.ChangerMotDePasseView.as_view(), name='changer_mdp'),
    path('detail-utilisateur/<int:pk>/', views.DetailUtilisateurView.as_view(), name='detail_utilisateur'),
    path('preferences-notifications/', views.NotificationPreferencesView.as_view(), name='notification_prefs'),
    path('ajouter-utilisateur/', views.AjouterUtilisateurView.as_view(), name='ajouter_utilisateur'),
]