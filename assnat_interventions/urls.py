from django.contrib import admin
from django.urls import path, include
from requetes.views import AccueilView   # Import de la vue personnalisée
from django.conf import settings
from django.conf.urls.static import static
from requetes.views import LandingPageView  # à importer
from comptes.auth_views import (
    CustomPasswordResetView, CustomPasswordResetDoneView,
    CustomPasswordResetConfirmView, CustomPasswordResetCompleteView
)
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', LandingPageView.as_view(), name='landing'),  # page publique
    path('accueil/', AccueilView.as_view(), name='accueil'),
    path('comptes/', include('comptes.urls')),
    path('requetes/', include('requetes.urls')),
    path('password-reset/', CustomPasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', CustomPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/', CustomPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset/complete/', CustomPasswordResetCompleteView.as_view(), name='password_reset_complete'),
    path('anymail/', include('anymail.urls')),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += staticfiles_urlpatterns()