from .orm_models import Customer


class CustomerRepository:
    def get_by_id(self, customer_id: int):
        try:
            return Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            return None

    def get_active_by_id(self, customer_id: int):
        try:
            return Customer.objects.get(pk=customer_id, is_active=True)
        except Customer.DoesNotExist:
            return None

    def get_by_email(self, email: str):
        try:
            return Customer.objects.get(email=email)
        except Customer.DoesNotExist:
            return None

    def get_all_active(self):
        return Customer.objects.filter(is_active=True)

    def save(self, customer):
        customer.save()
        return customer
