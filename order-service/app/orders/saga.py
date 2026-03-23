import logging
from decimal import Decimal

from django.db import transaction

from orders.infrastructure.orm_models import Order, OrderItem, SagaLog, PromoCode
from orders.infrastructure.repositories import (
    fetch_cart_for_order,
    clear_cart,
    create_payment,
    cancel_payment,
    create_shipment,
    cancel_shipment,
)
from orders.infrastructure.event_publisher import (
    publish_event,
    EXCHANGE_ORDERS,
    EVENT_ORDER_CREATED,
    EVENT_ORDER_CONFIRMED,
    EVENT_ORDER_FAILED,
    EVENT_ORDER_COMPENSATED,
)

logger = logging.getLogger(__name__)

STEP_CREATE_ORDER = 'CREATE_ORDER'
STEP_RESERVE_PAYMENT = 'RESERVE_PAYMENT'
STEP_RESERVE_SHIPPING = 'RESERVE_SHIPPING'
STEP_CONFIRM_ORDER = 'CONFIRM_ORDER'

LOG_STARTED = 'STARTED'
LOG_COMPLETED = 'COMPLETED'
LOG_FAILED = 'FAILED'
LOG_COMPENSATED = 'COMPENSATED'


def _log(order_id, step, status, payload=None):
    SagaLog.objects.create(
        order_id=order_id,
        step=step,
        status=status,
        payload=payload or {},
    )


class OrderSaga:
    """
    Saga orchestrator for order creation.
    Steps:
      1. CREATE_ORDER      – create Order with status PENDING
      2. RESERVE_PAYMENT   – call pay-service POST /internal/payments/
      3. RESERVE_SHIPPING  – call ship-service POST /internal/shipments/
      4. CONFIRM_ORDER     – set status to CONFIRMED

    Compensation:
      - RESERVE_SHIPPING fails  → cancel payment
      - RESERVE_PAYMENT fails   → mark order FAILED
      - CONFIRM_ORDER fails     → cancel both payment and shipment
    """

    def __init__(self, customer_id, payment_method, shipping_method, shipping_address, shipping_fee, promo_code=None):
        self.customer_id = customer_id
        self.payment_method = payment_method
        self.shipping_method = shipping_method
        self.shipping_address = shipping_address
        self.shipping_fee = Decimal(str(shipping_fee))
        if self.shipping_fee < 0:
            raise ValueError("Shipping fee must be non-negative")
        self.order = None
        self.payment_id = None
        self.shipment_id = None
        self.promo_code_str = promo_code or ''
        self.applied_promo = None

    def run(self):
        """Execute the saga. Returns (order, error_message, http_status_code)."""
        # Fetch cart snapshot before starting transaction
        cart_resp = fetch_cart_for_order(self.customer_id)
        if not cart_resp['success']:
            return None, 'Unable to fetch cart.', 502

        cart = cart_resp['data']
        items = cart.get('items', [])
        if not items:
            return None, 'Cart is empty.', 400

        total_amount = Decimal(str(cart['total_amount'])) + self.shipping_fee

        discount_amount = Decimal('0.00')

        # Step 1: CREATE_ORDER
        try:
            with transaction.atomic():
                if self.promo_code_str:
                    try:
                        promo = PromoCode.objects.select_for_update().get(
                            code=self.promo_code_str,
                            customer_id=self.customer_id,
                            status__in=[PromoCode.Status.UNUSED, PromoCode.Status.RETURNED],
                        )
                    except PromoCode.DoesNotExist:
                        return None, 'Invalid or unavailable promo code.', 400

                    self.applied_promo = promo

                    # Basic validity window check if configured
                    from django.utils import timezone

                    now = timezone.now()
                    if promo.valid_from and promo.valid_from > now:
                        return None, 'Promo code is not yet valid.', 400
                    if promo.valid_to and promo.valid_to < now:
                        return None, 'Promo code has expired.', 400

                    percentage = promo.percentage / Decimal('100')
                    raw_discount = (total_amount * percentage).quantize(Decimal('0.01'))
                    max_discount = promo.max_discount_amount
                    discount_amount = min(raw_discount, max_discount)
                    total_amount = (total_amount - discount_amount).quantize(Decimal('0.01'))

                self.order = Order.objects.create(
                    customer_id=self.customer_id,
                    cart_id=cart['id'],
                    status=Order.Status.PENDING,
                    payment_method=self.payment_method,
                    shipping_method=self.shipping_method,
                    shipping_address=self.shipping_address,
                    total_amount=total_amount,
                    payment_status='PENDING',
                    shipping_status='PENDING',
                    promo_code=self.promo_code_str,
                )
                order_items = [
                    OrderItem(
                        order=self.order,
                        book_id=item['book_id'],
                        book_title_snapshot=item['book_title_snapshot'],
                        price_snapshot=Decimal(str(item['price_snapshot'])),
                        quantity=item['quantity'],
                        subtotal=Decimal(str(item['subtotal'])).quantize(Decimal('0.01')),
                    )
                    for item in items
                ]
                OrderItem.objects.bulk_create(order_items)

                if self.applied_promo:
                    self.applied_promo.status = PromoCode.Status.RESERVED
                    self.applied_promo.applied_order_id = self.order.id
                    self.applied_promo.save(update_fields=['status', 'applied_order_id'])
                _log(self.order.id, STEP_CREATE_ORDER, LOG_COMPLETED, {'cart_id': cart['id']})
        except Exception as exc:
            logger.error('CREATE_ORDER failed: %s', exc)
            return None, 'Failed to create order.', 500

        publish_event(EXCHANGE_ORDERS, EVENT_ORDER_CREATED, {'order_id': self.order.id, 'customer_id': self.customer_id})

        # Step 2: RESERVE_PAYMENT
        _log(self.order.id, STEP_RESERVE_PAYMENT, LOG_STARTED)
        pay_resp = create_payment(self.order.id, self.customer_id, self.payment_method, total_amount)
        if not pay_resp['success']:
            _log(self.order.id, STEP_RESERVE_PAYMENT, LOG_FAILED, {'error': pay_resp.get('error')})
            self._mark_failed()
            publish_event(EXCHANGE_ORDERS, EVENT_ORDER_FAILED, {'order_id': self.order.id, 'step': STEP_RESERVE_PAYMENT})
            return self.order, 'Payment reservation failed.', 502

        payment_data = pay_resp.get('payment') or pay_resp.get('data', {})
        self.payment_id = payment_data.get('id')
        self.order.status = Order.Status.PAYMENT_RESERVED
        self.order.payment_status = 'RESERVED'
        self.order.save(update_fields=['status', 'payment_status'])
        _log(self.order.id, STEP_RESERVE_PAYMENT, LOG_COMPLETED, {'payment_id': self.payment_id})

        # Step 3: RESERVE_SHIPPING
        _log(self.order.id, STEP_RESERVE_SHIPPING, LOG_STARTED)
        ship_resp = create_shipment(
            self.order.id, self.customer_id, self.shipping_method, self.shipping_address, self.shipping_fee
        )
        if not ship_resp['success']:
            _log(self.order.id, STEP_RESERVE_SHIPPING, LOG_FAILED, {'error': ship_resp.get('error')})
            self._compensate_payment()
            publish_event(EXCHANGE_ORDERS, EVENT_ORDER_COMPENSATED, {'order_id': self.order.id, 'step': STEP_RESERVE_SHIPPING})
            return self.order, 'Shipment reservation failed; payment cancelled.', 502

        shipment_data = ship_resp.get('shipment') or ship_resp.get('data', {})
        self.shipment_id = shipment_data.get('id')
        self.order.status = Order.Status.SHIPMENT_RESERVED
        self.order.shipping_status = 'RESERVED'
        self.order.save(update_fields=['status', 'shipping_status'])
        _log(self.order.id, STEP_RESERVE_SHIPPING, LOG_COMPLETED, {'shipment_id': self.shipment_id})

        # Step 4: CONFIRM_ORDER
        _log(self.order.id, STEP_CONFIRM_ORDER, LOG_STARTED)
        try:
            self.order.status = Order.Status.CONFIRMED
            self.order.save(update_fields=['status'])
            _log(self.order.id, STEP_CONFIRM_ORDER, LOG_COMPLETED)
        except Exception as exc:
            logger.error('CONFIRM_ORDER failed: %s', exc)
            _log(self.order.id, STEP_CONFIRM_ORDER, LOG_FAILED, {'error': str(exc)})
            self._compensate_payment()
            self._compensate_shipment()
            publish_event(EXCHANGE_ORDERS, EVENT_ORDER_COMPENSATED, {'order_id': self.order.id, 'step': STEP_CONFIRM_ORDER})
            return self.order, 'Order confirmation failed; compensating.', 500

        publish_event(EXCHANGE_ORDERS, EVENT_ORDER_CONFIRMED, {
            'order_id': self.order.id,
            'customer_id': self.customer_id,
            'total_amount': str(total_amount),
            'items': [
                {'book_id': item.book_id, 'quantity': item.quantity}
                for item in self.order.items.all()
            ]
        })

        # Clear cart best-effort
        clear_cart(self.customer_id)

        return self.order, None, 201

    def _mark_failed(self):
        try:
            self.order.status = Order.Status.FAILED
            self.order.save(update_fields=['status'])
            self._refund_promo_if_any()
        except Exception as exc:
            logger.error('Failed to mark order as FAILED: %s', exc)

    def _compensate_payment(self):
        self.order.status = Order.Status.COMPENSATING
        self.order.save(update_fields=['status'])
        if self.payment_id:
            result = cancel_payment(self.payment_id)
            if result['success']:
                _log(self.order.id, STEP_RESERVE_PAYMENT, LOG_COMPENSATED, {'payment_id': self.payment_id})
            else:
                # Compensation failed - log it but still mark as COMPENSATED so the saga can proceed.
                # Manual intervention may be required to cancel the payment out-of-band.
                logger.error('Failed to cancel payment %s: %s', self.payment_id, result.get('error'))
                _log(self.order.id, STEP_RESERVE_PAYMENT, LOG_FAILED, {
                    'payment_id': self.payment_id,
                    'compensation_error': result.get('error'),
                })
        self.order.status = Order.Status.COMPENSATED
        self.order.payment_status = 'CANCELLED'
        self.order.save(update_fields=['status', 'payment_status'])
        self._refund_promo_if_any()

    def _compensate_shipment(self):
        if self.shipment_id:
            result = cancel_shipment(self.shipment_id)
            if result['success']:
                _log(self.order.id, STEP_RESERVE_SHIPPING, LOG_COMPENSATED, {'shipment_id': self.shipment_id})
            else:
                # Compensation failed - log it. Manual intervention may be required.
                logger.error('Failed to cancel shipment %s: %s', self.shipment_id, result.get('error'))
                _log(self.order.id, STEP_RESERVE_SHIPPING, LOG_FAILED, {
                    'shipment_id': self.shipment_id,
                    'compensation_error': result.get('error'),
                })
        self.order.shipping_status = 'CANCELLED'
        self.order.save(update_fields=['shipping_status'])

    def _refund_promo_if_any(self):
        """
        Return promo code to a reusable state if the order never reached DELIVERED.
        """
        if not self.order or not self.order.promo_code:
            return

        try:
            promo = PromoCode.objects.get(
                code=self.order.promo_code,
                customer_id=self.customer_id,
            )
        except PromoCode.DoesNotExist:
            return

        if promo.status in [PromoCode.Status.RESERVED, PromoCode.Status.UNUSED]:
            promo.status = PromoCode.Status.RETURNED
            promo.applied_order_id = None
            promo.save(update_fields=['status', 'applied_order_id'])
