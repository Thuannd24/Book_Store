from rest_framework import serializers

from .models import Review


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = [
            'id',
            'book_id',
            'customer_id',
            'rating',
            'comment',
            'status',
            'created_at',
        ]
        read_only_fields = ['id', 'status', 'created_at']

    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError('rating must be between 1 and 5')
        return value
