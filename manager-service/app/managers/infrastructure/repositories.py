from .orm_models import Manager


class ManagerRepository:
    def get_by_id(self, manager_id: int):
        try:
            return Manager.objects.get(pk=manager_id, is_active=True)
        except Manager.DoesNotExist:
            return None

    def get_by_email(self, email: str):
        try:
            return Manager.objects.get(email__iexact=email, is_active=True)
        except Manager.DoesNotExist:
            return None

    def save(self, manager):
        manager.save()
        return manager
