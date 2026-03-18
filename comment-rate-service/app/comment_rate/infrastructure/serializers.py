from rest_framework import serializers


class ReviewSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    book_id = serializers.IntegerField(min_value=1)
    customer_id = serializers.IntegerField(min_value=1)
    rating = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(required=False, allow_blank=True)
    status = serializers.CharField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
