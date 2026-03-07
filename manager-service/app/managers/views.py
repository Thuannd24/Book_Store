from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Manager
from .serializers import (
    ManagerLoginSerializer,
    ManagerProfileSerializer,
    ManagerRegisterSerializer,
)
from .services import build_dashboard_summary


@api_view(['GET'])
def health(request):
    return Response({'status': 'ok', 'service': 'manager-service'})


class ManagerRegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ManagerRegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        manager = serializer.save()
        return Response(ManagerProfileSerializer(manager).data, status=status.HTTP_201_CREATED)


class ManagerLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ManagerLoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        manager = serializer.validated_data['manager']
        return Response(ManagerProfileSerializer(manager).data, status=status.HTTP_200_OK)


class ManagerDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, manager_id):
        try:
            manager = Manager.objects.get(pk=manager_id, is_active=True)
        except Manager.DoesNotExist:
            return Response({'detail': 'Manager not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(ManagerProfileSerializer(manager).data)


class DashboardSummaryView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        summary = build_dashboard_summary()
        return Response(summary)
