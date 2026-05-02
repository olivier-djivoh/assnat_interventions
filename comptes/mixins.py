from django.contrib.auth.mixins import UserPassesTestMixin

class EstPersonnelMixin(UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and user.est_valide and user.is_active

class EstChefServiceMixin(UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and user.est_valide and user.is_active and user.role == 'chef_service'

class EstChefDivisionMixin(UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and user.est_valide and user.is_active and user.role == 'chef_division'

class EstDirecteurMixin(UserPassesTestMixin):
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and user.est_valide and user.is_active and user.role == 'directeur'