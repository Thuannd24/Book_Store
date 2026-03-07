from rest_framework import serializers

from .models import Book


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = [
            'id',
            'title',
            'isbn',
            'author',
            'publisher',
            'price',
            'stock',
            'description',
            'image_url',
            'category_id',
            'category_name_snapshot',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_stock(self, value):
        if value < 0:
            raise serializers.ValidationError('stock must be non-negative.')
        return value

    def validate(self, attrs):
        stock = attrs.get('stock', getattr(self.instance, 'stock', 0))
        status = attrs.get('status', getattr(self.instance, 'status', Book.Status.ACTIVE))
        if stock == 0 and status == Book.Status.ACTIVE:
            attrs['status'] = Book.Status.OUT_OF_STOCK
        return attrs


class InternalBookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = [
            'id',
            'title',
            'price',
            'stock',
            'status',
            'category_id',
            'category_name_snapshot',
        ]
