from django.utils.text import slugify
from rest_framework import serializers

from .orm_models import Category


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = [
            'id',
            'name',
            'slug',
            'description',
            'is_active',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def validate_slug(self, value):
        if value == '':
            return value
        return slugify(value)

    def validate(self, attrs):
        name = attrs.get('name') or getattr(self.instance, 'name', None)
        slug = attrs.get('slug')
        if not slug and name:
            attrs['slug'] = slugify(name)
        return attrs
