from .orm_models import Payment


class PaymentRepository:
    def get_by_id(self, payment_id: int):
        try:
            return Payment.objects.get(pk=payment_id)
        except Payment.DoesNotExist:
            return None

    def get_by_order(self, order_id: int):
        return Payment.objects.filter(order_id=order_id)

    def save(self, payment):
        payment.save()
        return payment
