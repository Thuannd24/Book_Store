from staffs.infrastructure.orm_models import Staff


class StaffService:
    @staticmethod
    def get_staff(staff_id: int):
        try:
            return Staff.objects.get(pk=staff_id)
        except Staff.DoesNotExist:
            return None

    @staticmethod
    def get_all():
        return Staff.objects.all()
