from django.contrib import admin
from .models import JournalAudit

@admin.register(JournalAudit)
class JournalAuditAdmin(admin.ModelAdmin):
    list_display = ('date_action', 'message_audit', 'utilisateur', 'adresse_ip')
    list_filter = ('action', 'entite_type', 'date_action')
    search_fields = ('utilisateur__username', 'message_audit')
    readonly_fields = ('utilisateur', 'action', 'entite_type', 'entite_id', 
                       'anciennes_valeurs', 'nouvelles_valeurs', 'date_action', 
                       'adresse_ip', 'message_audit')
    fieldsets = (
        ('Informations générales', {
            'fields': ('date_action', 'utilisateur', 'adresse_ip', 'action', 'entite_type')
        }),
        ('Message détaillé', {
            'fields': ('message_audit',)
        }),
        ('Données techniques (JSON)', {
            'fields': ('entite_id', 'anciennes_valeurs', 'nouvelles_valeurs'),
            'classes': ('collapse',)
        }),
    )

    def message_audit(self, obj):
        """Génère un message lisible en français"""
        user = obj.utilisateur
        if user:
            nom_utilisateur = user.get_full_name() or user.username
            if user.is_superuser:
                role = "Administrateur"
            elif hasattr(user, 'role') and user.role == 'chef_service':
                role = "Chef de service"
            elif hasattr(user, 'role') and user.role == 'chef_division':
                role = "Chef de division"
            elif hasattr(user, 'role') and user.role == 'directeur':
                role = "Directeur"
            else:
                role = "Personnel"
            affichage_user = f"{nom_utilisateur} ({role})"
        else:
            affichage_user = "Système"

        date_str = obj.date_action.strftime("%d/%m/%Y à %H:%M:%S")

        # Actions spécifiques (connexion, déconnexion)
        if obj.action == 'CONNEXION':
            return f"{affichage_user} s'est connecté(e) le {date_str} depuis l'IP {obj.adresse_ip or 'inconnue'}."
        if obj.action == 'DECONNEXION':
            return f"{affichage_user} s'est déconnecté(e) le {date_str}."

        # Actions CRUD
        if obj.action == 'CREATION':
            verbe = "a créé"
        elif obj.action == 'MODIFICATION':
            verbe = "a modifié"
        elif obj.action == 'SUPPRESSION':
            verbe = "a supprimé"
        else:
            verbe = f"a effectué l'action '{obj.action}'"

        entite_fr = {
            'utilisateur': "l'utilisateur",
            'requete': "la requête",
            'attribution': "l'attribution",
            'compte_rendu': "le compte rendu",
            'authentification': "l'événement de connexion",
        }.get(obj.entite_type, f"l'entité '{obj.entite_type}'")

        libelle = ""
        if obj.entite_type == 'requete' and obj.nouvelles_valeurs:
            titre = obj.nouvelles_valeurs.get('titre')
            if titre:
                libelle = f" « {titre} »"
        elif obj.entite_type == 'utilisateur' and obj.nouvelles_valeurs:
            prenom = obj.nouvelles_valeurs.get('first_name', '')
            nom = obj.nouvelles_valeurs.get('last_name', '')
            if prenom or nom:
                libelle = f" {prenom} {nom}".strip()
            else:
                libelle = f" {obj.nouvelles_valeurs.get('username', '')}"
        elif obj.entite_type == 'compte_rendu' and obj.entite_id:
            try:
                from requetes.models import CompteRendu
                cr = CompteRendu.objects.get(pk=obj.entite_id)
                titre_req = cr.requete.titre
                libelle = f" de la requête « {titre_req} »"
            except:
                pass

        id_entite = f" #{obj.entite_id}" if obj.entite_id else ""
        details = ""
        if obj.action == 'MODIFICATION' and obj.nouvelles_valeurs and obj.anciennes_valeurs:
            champs_modifies = set(obj.nouvelles_valeurs.keys()) & set(obj.anciennes_valeurs.keys())
            if champs_modifies:
                details = f" (champs modifiés : {', '.join(champs_modifies)})"

        return f"{affichage_user} {verbe} {entite_fr}{id_entite}{libelle} le {date_str}{details}."

    message_audit.short_description = "Action détaillée"