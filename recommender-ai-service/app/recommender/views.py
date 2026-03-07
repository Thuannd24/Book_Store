from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from .services import ServiceError, compute_recommendations


@api_view(['GET'])
def health(request):
    return Response({'status': 'ok', 'service': 'recommender-ai-service'})


class RecommendationView(APIView):
    """
    GET /api/recommendations/customer/{customer_id}/
    """

    def get(self, request, customer_id):
        try:
            top_n = int(request.query_params.get('limit', 5) or 5)
        except (TypeError, ValueError):
            top_n = 5
        try:
            recommendations = compute_recommendations(customer_id, top_n=top_n)
        except ServiceError as exc:
            return Response(
                {'success': False, 'customer_id': customer_id, 'error': str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        return Response(
            {'success': True, 'customer_id': customer_id, 'recommendations': recommendations},
            status=status.HTTP_200_OK,
        )
