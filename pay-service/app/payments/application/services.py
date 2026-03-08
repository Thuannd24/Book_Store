from payments.infrastructure.orm_models import Payment


class PaymentService:
    @staticmethod
    def get_payment(payment_id: int):
        try:
            return Payment.objects.get(pk=payment_id)
        except Payment.DoesNotExist:
            return None

    @staticmethod
    def get_by_order(order_id: int):
        return Payment.objects.filter(order_id=order_id)
