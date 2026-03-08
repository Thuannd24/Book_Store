from .orm_models import Staff


class StaffRepository:
    def get_by_id(self, staff_id: int):
        try:
            return Staff.objects.get(pk=staff_id)
        except Staff.DoesNotExist:
            return None

    def get_by_email(self, email: str, active_only: bool = True):
        try:
            if active_only:
                return Staff.objects.get(email=email, is_active=True)
            return Staff.objects.get(email=email)
        except Staff.DoesNotExist:
            return None

    def get_all(self):
        return Staff.objects.all()

    def save(self, staff):
        staff.save()
        return staff
