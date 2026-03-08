from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Customer
from .serializers import (
    CustomerRegisterSerializer,
    CustomerLoginSerializer,
    CustomerProfileSerializer,
    CustomerUpdateSerializer,
    CustomerInternalSerializer,
)
from .services import create_cart_for_customer


# ── Health ────────────────────────────────────────────────────────────────────

@api_view(['GET'])
def health(request):
    db_ok = True
    try:
        from django.db import connection
        connection.ensure_connection()
    except Exception:
        db_ok = False
    return Response({
        'status': 'ok' if db_ok else 'degraded',
        'service': 'customer-service',
        'db': 'ok' if db_ok else 'error',
        'version': '2.0.0',
    }, status=200 if db_ok else 503)

class CustomerListView(APIView):
    """
    GET /api/customers/

    Returns active customers; used by manager dashboard totals.
    """

    def get(self, request):
        customers = Customer.objects.filter(is_active=True)
        return Response(CustomerProfileSerializer(customers, many=True).data)


# ── Public API ────────────────────────────────────────────────────────────────

class RegisterView(APIView):
    """
    POST /api/customers/register/

    Register a new customer.
    On success, also calls cart-service to auto-create an empty cart.
    Customer is always saved even if cart creation fails.
    """

    def post(self, request):
        serializer = CustomerRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        customer = serializer.save()

        # Call cart-service; do NOT rollback on failure
        cart_result = create_cart_for_customer(customer.id)
        cart_created = cart_result['success']

        response_data = CustomerProfileSerializer(customer).data
        response_data['cart_created'] = cart_created
        if not cart_created:
            response_data['warning'] = (
                f"Customer registered but cart creation failed: {cart_result.get('error', 'unknown error')}"
            )

        return Response(response_data, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """
    POST /api/customers/login/

    Authenticate a customer with email + password.
    Returns customer profile on success.
    (Token / JWT auth is handled by the API gateway — not this service.)
    """

    def post(self, request):
        serializer = CustomerLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        customer = serializer.validated_data['customer']
        return Response(CustomerProfileSerializer(customer).data, status=status.HTTP_200_OK)


class CustomerDetailView(APIView):
    """
    GET  /api/customers/{customer_id}/  — retrieve profile
    PUT  /api/customers/{customer_id}/  — update profile (full_name, phone, address)
    """

    def _get_customer(self, customer_id):
        try:
            return Customer.objects.get(pk=customer_id, is_active=True)
        except Customer.DoesNotExist:
            return None

    def get(self, request, customer_id):
        customer = self._get_customer(customer_id)
        if customer is None:
            return Response(
                {'detail': 'Customer not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(CustomerProfileSerializer(customer).data)

    def put(self, request, customer_id):
        customer = self._get_customer(customer_id)
        if customer is None:
            return Response(
                {'detail': 'Customer not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = CustomerUpdateSerializer(customer, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response(CustomerProfileSerializer(customer).data)


# ── Internal API (called by other services) ───────────────────────────────────

class InternalCustomerDetailView(APIView):
    """
    GET /internal/customers/{customer_id}/

    Lightweight endpoint consumed by other services (e.g. comment-rate-service).
    Returns only the fields needed to validate a customer exists.
    """

    def get(self, request, customer_id):
        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            return Response(
                {'detail': 'Customer not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(CustomerInternalSerializer(customer).data)
