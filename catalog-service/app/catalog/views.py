from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Category
from .serializers import CategorySerializer


@api_view(['GET'])
def health(request):
    return Response({'status': 'ok', 'service': 'catalog-service'})


class CategoryListCreateView(APIView):
    """
    GET  /api/catalog/categories/
    POST /api/catalog/categories/
    """

    def get(self, request):
        categories = Category.objects.all()
        return Response(CategorySerializer(categories, many=True).data)

    def post(self, request):
        serializer = CategorySerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoryDetailView(APIView):
    """
    GET    /api/catalog/categories/{id}/
    PUT    /api/catalog/categories/{id}/
    DELETE /api/catalog/categories/{id}/
    """

    def _get_category(self, category_id):
        try:
            return Category.objects.get(pk=category_id)
        except Category.DoesNotExist:
            return None

    def get(self, request, category_id):
        category = self._get_category(category_id)
        if category is None:
            return Response({'detail': 'Category not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(CategorySerializer(category).data)

    def put(self, request, category_id):
        category = self._get_category(category_id)
        if category is None:
            return Response({'detail': 'Category not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = CategorySerializer(category, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, category_id):
        category = self._get_category(category_id)
        if category is None:
            return Response({'detail': 'Category not found.'}, status=status.HTTP_404_NOT_FOUND)
        category.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
