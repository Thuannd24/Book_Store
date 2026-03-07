from django.contrib.auth.hashers import check_password
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Staff
from .serializers import StaffSerializer, RegisterSerializer, LoginSerializer


@api_view(['GET'])
def health(request):
    return Response({'status': 'ok', 'service': 'staff-service'})


class RegisterView(APIView):
    """
    POST /api/staff/register/
    """

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            staff = serializer.save()
            return Response(StaffSerializer(staff).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    POST /api/staff/login/
    """

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        try:
            staff = Staff.objects.get(email=email, is_active=True)
        except Staff.DoesNotExist:
            return Response({'detail': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)

        if not check_password(password, staff.password_hash):
            return Response({'detail': 'Invalid credentials.'}, status=status.HTTP_401_UNAUTHORIZED)

        return Response(StaffSerializer(staff).data)


class StaffDetailView(APIView):
    """
    GET /api/staff/{staff_id}/
    """

    def get(self, request, staff_id):
        try:
            staff = Staff.objects.get(pk=staff_id)
        except Staff.DoesNotExist:
            return Response({'detail': 'Staff not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(StaffSerializer(staff).data)


class StaffListView(APIView):
    """
    GET /api/staff/
    """

    def get(self, request):
        staff = Staff.objects.all()
        return Response(StaffSerializer(staff, many=True).data)
