class OrderNotFoundError(Exception):
    pass


class CartEmptyError(Exception):
    pass


class PaymentReservationError(Exception):
    pass


class ShipmentReservationError(Exception):
    pass


class OrderConfirmationError(Exception):
    pass
