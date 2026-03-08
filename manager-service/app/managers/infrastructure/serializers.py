from django.contrib.auth.hashers import check_password, make_password
from rest_framework import serializers

from .orm_models import Manager


class ManagerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Manager
        fields = ['id', 'manager_code', 'full_name', 'email', 'is_active', 'created_at']
        read_only_fields = fields


class ManagerRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = Manager
        fields = ['manager_code', 'full_name', 'email', 'password']

    def validate_email(self, value):
        value_lower = value.lower()
        if Manager.objects.filter(email__iexact=value_lower).exists():
            raise serializers.ValidationError('Email already registered.')
        return value_lower

    def validate_manager_code(self, value):
        if Manager.objects.filter(manager_code=value).exists():
            raise serializers.ValidationError('Manager code already exists.')
        return value

    def create(self, validated_data):
        password = validated_data.pop('password')
        return Manager.objects.create(
            password_hash=make_password(password),
            **validated_data,
        )


class ManagerLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email', '').lower()
        password = attrs.get('password')
        try:
            manager = Manager.objects.get(email__iexact=email, is_active=True)
        except Manager.DoesNotExist:
            raise serializers.ValidationError({'email': 'Invalid credentials.'})

        if not check_password(password, manager.password_hash):
            raise serializers.ValidationError({'password': 'Invalid credentials.'})

        attrs['manager'] = manager
        return attrs
